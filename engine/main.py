"""FastAPI app factory, lifespan, and middleware.

This is the entry point for the engine. It wires all components together:
- Recipe resolver
- Agent executor
- MCP manager
- LiteLLM proxy configuration
- Tool registration
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from engine import __version__
from engine.agent.executor import AgentExecutor
from engine.agent.session import SessionManager
from engine.api.router import api_router
from engine.config import get_settings
from engine.litellm.client import LiteLLMClient
from engine.litellm.proxy import configure_litellm_proxy
from engine.mcp import MCPManager
from engine.recipes import PlaceholderRecipeResolver
from engine.tools.recipe_tool import configure_recipe_tool
from engine.tools.registry import registry
from engine.utils.logging import get_logger, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan — startup and shutdown logic."""
    settings = get_settings()
    setup_logging(settings.log_level)
    logger = get_logger("engine.main")
    logger.info("engine_starting", version=__version__)

    # 1. Configure LiteLLM proxy (must happen before SDK clients are created)
    configure_litellm_proxy()

    # 2. Initialize recipe resolver
    recipe_resolver = PlaceholderRecipeResolver()

    # 3. Initialize LiteLLM client (for direct calls in Recipe-as-Tool)
    litellm_client = LiteLLMClient(default_model=settings.default_model)

    # 4. Wire the recipe tool with its dependencies
    configure_recipe_tool(recipe_resolver, litellm_client)

    # 5. Auto-discover and register custom tools
    registry.auto_discover()

    # 6. Initialize MCP manager and load config
    mcp_manager = MCPManager()
    mcp_manager.load_config()

    # 7. Initialize session manager
    session_manager = SessionManager()

    # 8. Build the agent executor
    executor = AgentExecutor(
        recipe_resolver=recipe_resolver,
        mcp_manager=mcp_manager,
        session_manager=session_manager,
        workspace_path=settings.workspace_path,
        default_model=settings.default_model,
        default_max_turns=settings.default_max_turns,
        default_permission_mode=settings.default_permission_mode,
    )

    # Store components on app state for route access
    app.state.executor = executor
    app.state.recipe_resolver = recipe_resolver
    app.state.mcp_manager = mcp_manager
    app.state.session_manager = session_manager
    app.state.litellm_client = litellm_client
    app.state.active_tasks = set()

    logger.info(
        "engine_ready",
        workspace=settings.workspace_path,
        default_model=settings.default_model,
        tools=registry.get_names(),
    )

    yield

    # Shutdown
    logger.info("engine_shutting_down")

    # Cancel any active tasks
    for task in list(app.state.active_tasks):
        task.cancel()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="AI Matrx Agent Engine",
        description="Bridges the AI Matrx Recipe system with the Claude Agent SDK and LiteLLM",
        version=__version__,
        lifespan=lifespan,
    )

    # CORS middleware — permissive for dev, tighten in production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount API routes
    app.include_router(api_router)

    return app


# The app instance — imported by uvicorn as engine.main:app
app = create_app()
