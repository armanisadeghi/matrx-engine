"""AgentExecutor — runs the Claude Agent SDK with resolved recipe config.

This is the heart of the engine. It takes a request, resolves the recipe,
builds SDK options, runs the agent loop, and streams events back.
"""

from __future__ import annotations

import os
from typing import Any

from claude_agent_sdk import (
    ClaudeAgentOptions,
    query,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    ToolResultBlock,
)

from engine.agent.hooks import post_execution_hook, pre_execution_hook
from engine.agent.permissions import resolve_permission_mode
from engine.agent.session import AgentSession, SessionManager
from engine.api.schemas.requests import AgentExecuteRequest
from engine.mcp import MCPManager
from engine.recipes.interfaces import RecipeResolverInterface, RecipeResult
from engine.streaming import StreamEmitter
from engine.utils.logging import get_logger

logger = get_logger(__name__)


class AgentExecutor:
    """Executes agent sessions using the Claude Agent SDK.

    Wires the recipe resolver output into SDK options, manages the agent
    lifecycle, and streams events through the emitter.
    """

    def __init__(
        self,
        recipe_resolver: RecipeResolverInterface,
        mcp_manager: MCPManager,
        session_manager: SessionManager,
        workspace_path: str = "/workspace",
        default_model: str | None = None,
        default_max_turns: int = 50,
        default_permission_mode: str = "bypassPermissions",
    ) -> None:
        self._resolver = recipe_resolver
        self._mcp = mcp_manager
        self._sessions = session_manager
        self._workspace = workspace_path
        self._default_model = default_model
        self._default_max_turns = default_max_turns
        self._default_permission_mode = default_permission_mode

    async def execute(self, request: AgentExecuteRequest, emitter: StreamEmitter) -> None:
        """Execute an agent request end-to-end.

        1. Resolve the recipe
        2. Build SDK options
        3. Run the agent loop
        4. Stream events

        Always closes the emitter when done, regardless of outcome.
        """
        session = self._sessions.create_session(
            agent_id=request.id,
            conversation_id=request.conversation_id,
        )

        user_input = request.user_input
        if isinstance(user_input, list):
            # If user_input is a list of message dicts, extract text
            user_input = " ".join(
                item.get("text", str(item)) if isinstance(item, dict) else str(item) for item in user_input
            )

        try:
            # Step 1: Resolve recipe
            await emitter.emit_status("resolving_recipe", agent_id=request.id)

            recipe_result = await self._resolver.resolve(
                agent_id=request.id,
                user_input=user_input,
                variables=request.variables,
                config_overrides=request.config_overrides,
            )

            if not recipe_result.success:
                await emitter.emit_error(
                    recipe_result.error or "Recipe resolution failed",
                    details={"agent_id": request.id},
                )
                return

            await emitter.emit_debug({"recipe_result": recipe_result.model_dump()})

            # Step 2: Build SDK options
            await emitter.emit_status("building_agent")

            options = self._build_options(recipe_result, session)

            # Step 3: Determine the prompt
            prompt = recipe_result.compiled_prompt or user_input or ""
            if not prompt:
                await emitter.emit_error("No prompt available — user_input and compiled_prompt are both empty")
                return

            # Step 4: Run pre-execution hook
            await pre_execution_hook(
                agent_id=request.id,
                prompt=prompt,
                emitter=emitter,
                metadata=recipe_result.metadata,
            )

            # Step 5: Run the agent loop and stream events
            await emitter.emit_status("executing")
            await self._run_agent(prompt, options, emitter, request.debug)

            # Step 6: Post-execution
            self._sessions.end_session(session.session_id)

        except Exception as exc:
            logger.error("agent_execution_failed", agent_id=request.id, error=str(exc), exc_info=True)
            await emitter.emit_error(f"Agent execution failed: {exc}")
            await post_execution_hook(
                agent_id=request.id,
                result=None,
                emitter=emitter,
                error=str(exc),
            )
        finally:
            await emitter.close()

    def _build_options(self, recipe: RecipeResult, session: AgentSession) -> ClaudeAgentOptions:
        """Build ClaudeAgentOptions from a resolved recipe."""
        # Build MCP servers dict
        mcp_servers: dict[str, Any] = {}

        # Add our custom tools MCP server
        tools_server = self._mcp.build_tools_mcp_server()
        mcp_servers["matrx_tools"] = tools_server

        permission_mode = resolve_permission_mode(
            recipe.permission_mode,
            default=self._default_permission_mode,
        )

        # Ensure workspace exists
        os.makedirs(self._workspace, exist_ok=True)

        options = ClaudeAgentOptions(
            system_prompt=recipe.system_prompt,
            permission_mode=permission_mode,
            max_turns=recipe.max_turns or self._default_max_turns,
            cwd=self._workspace,
            mcp_servers=mcp_servers,
        )

        # Set model if specified
        if recipe.model or self._default_model:
            options.model = recipe.model or self._default_model

        # Set allowed tools if specified
        if recipe.allowed_tools:
            options.allowed_tools = recipe.allowed_tools

        return options

    async def _run_agent(
        self,
        prompt: str,
        options: ClaudeAgentOptions,
        emitter: StreamEmitter,
        debug: bool = False,
    ) -> None:
        """Run the Claude Agent SDK loop and stream events."""
        final_result: str | None = None
        total_usage: dict[str, Any] = {
            "input_tokens": 0,
            "output_tokens": 0,
        }

        try:
            async for message in query(prompt=prompt, options=options):
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            await emitter.emit_content(block.text)
                        elif isinstance(block, ToolUseBlock):
                            await emitter.emit_tool_use(
                                tool_name=block.name,
                                tool_input=block.input if isinstance(block.input, dict) else {},
                            )
                        elif isinstance(block, ToolResultBlock):
                            content_text = ""
                            if isinstance(block.content, str):
                                content_text = block.content
                            elif isinstance(block.content, list):
                                for item in block.content:
                                    if isinstance(item, dict) and item.get("type") == "text":
                                        content_text += item.get("text", "")
                            await emitter.emit_tool_result(
                                tool_name=getattr(block, "tool_use_id", "unknown"),
                                result=content_text[:5000],
                            )

                elif isinstance(message, ResultMessage):
                    final_result = getattr(message, "text", None) or str(message)
                    # Capture usage if available
                    if hasattr(message, "usage"):
                        msg_usage = message.usage
                        if hasattr(msg_usage, "input_tokens"):
                            total_usage["input_tokens"] = msg_usage.input_tokens
                        if hasattr(msg_usage, "output_tokens"):
                            total_usage["output_tokens"] = msg_usage.output_tokens

            await emitter.emit_done(result=final_result, usage=total_usage)

            await post_execution_hook(
                agent_id="",
                result=final_result,
                emitter=emitter,
                usage=total_usage,
            )

        except Exception as exc:
            logger.error("agent_loop_error", error=str(exc), exc_info=True)
            await emitter.emit_error(f"Agent SDK error: {exc}")
            await emitter.emit_done(result=None, usage=total_usage)
