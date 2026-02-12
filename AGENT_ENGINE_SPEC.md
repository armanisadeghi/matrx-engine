# AI Matrx Agent Engine — Repository Specification (Matrx Engine)

> **Purpose**: This document is the single source of truth for setting up the AI Matrx Agent Engine — a Python-based system that bridges the AI Matrx Recipe system with the Claude Agent SDK, LiteLLM, and a containerized execution environment. Read this entire document before writing any code.

---

## 1. What This Repo Is

This is a **FastAPI-based Python backend** that:

1. Accepts agent execution requests via API (not CLI — this runs headless in containers)
2. Resolves the request through the **AI Matrx Recipe system** (a black box that returns LLM configs)
3. Executes the resolved agent through the **Claude Agent SDK** with **LiteLLM** as the model router
4. Streams results back to the caller via NDJSON Server-Sent Events
5. Supports Recipes at three integration layers: as the **outer agent wrapper**, as **sub-agents**, and as **custom tools**

Claude Code (via the Agent SDK) has **full filesystem and shell access** inside its container. This is by design. Every instance runs in an isolated, pre-provisioned container.

---

## 2. Tech Stack

| Component | Technology | Purpose |
|---|---|---|
| Framework | FastAPI + Uvicorn | HTTP API, streaming, WebSocket support |
| Agent Runtime | `claude-agent-sdk` (Python) | Claude Code's agent loop, tools, context management |
| Model Router | LiteLLM (proxy mode) | Route to any LLM provider (Anthropic, OpenAI, Gemini, local, etc.) |
| Task Queue | (Pluggable — Redis/Celery placeholder) | Future: distributed task management |
| Container | Docker | Isolated execution environment per agent instance |
| Python | 3.11+ | Runtime |
| Node.js | 18+ | Required by Claude Code CLI (bundled with SDK) |

---

## 3. Project Structure

```
matrx-agent-engine/
├── README.md
├── AGENT_ENGINE_SPEC.md          # This file
├── pyproject.toml                # Project config + dependencies
├── Dockerfile                    # Container image for agent instances
├── docker-compose.yml            # Local dev: FastAPI + LiteLLM proxy
├── litellm_config.yaml           # LiteLLM model routing configuration
├── .env.example                  # Required environment variables template
│
├── engine/                       # Core application package
│   ├── __init__.py
│   ├── main.py                   # FastAPI app factory, lifespan, middleware
│   ├── config.py                 # Pydantic Settings (env-based config)
│   │
│   ├── api/                      # HTTP API layer
│   │   ├── __init__.py
│   │   ├── router.py             # Main API router (mounts all sub-routers)
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── agent.py          # POST /agent/execute — primary endpoint
│   │   │   ├── health.py         # GET /health, GET /ready
│   │   │   └── tools.py          # GET /tools — list available tools/MCPs
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   └── auth.py           # Auth verification (verify_user dependency)
│   │   └── schemas/
│   │       ├── __init__.py
│   │       ├── requests.py       # AgentExecuteRequest and related models
│   │       └── responses.py      # Streaming event schemas
│   │
│   ├── recipes/                  # Recipe system integration (BLACK BOX)
│   │   ├── __init__.py
│   │   ├── interfaces.py         # Abstract interface + RecipeResult model
│   │   ├── resolver.py           # RecipeResolver — placeholder implementation
│   │   └── README.md             # Instructions for Arman's recipe integration
│   │
│   ├── agent/                    # Claude Agent SDK integration
│   │   ├── __init__.py
│   │   ├── executor.py           # AgentExecutor — runs the SDK with resolved config
│   │   ├── session.py            # Session management, conversation continuity
│   │   ├── permissions.py        # Permission mode configuration
│   │   └── hooks.py              # Pre/post execution hooks
│   │
│   ├── tools/                    # Custom tools registered with Claude
│   │   ├── __init__.py
│   │   ├── registry.py           # ToolRegistry — discovers and registers all tools
│   │   ├── recipe_tool.py        # THE KEY TOOL: executes a Recipe as a tool call
│   │   ├── database_tool.py      # Placeholder: query databases
│   │   ├── http_tool.py          # Placeholder: make HTTP requests to external APIs
│   │   └── README.md             # How to add new custom tools
│   │
│   ├── mcp/                      # MCP server configurations
│   │   ├── __init__.py
│   │   ├── manager.py            # MCP lifecycle management
│   │   ├── servers/              # Individual MCP server configs
│   │   │   ├── __init__.py
│   │   │   └── README.md         # How to add new MCP servers
│   │   └── config.json           # MCP server registry (auto-loaded)
│   │
│   ├── litellm/                  # LiteLLM integration
│   │   ├── __init__.py
│   │   ├── client.py             # Direct LiteLLM client for Recipe-as-Tool calls
│   │   └── proxy.py              # LiteLLM proxy management utilities
│   │
│   ├── streaming/                # Response streaming infrastructure
│   │   ├── __init__.py
│   │   ├── emitter.py            # StreamEmitter — NDJSON event streaming
│   │   └── events.py             # Event type definitions
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logging.py            # Structured logging setup
│       └── errors.py             # Custom exception hierarchy
│
├── .claude/                      # Claude Code filesystem config (loaded by SDK)
│   ├── settings.json             # Hooks, permission rules, output style
│   ├── agents/                   # Sub-agent definitions (Markdown + YAML frontmatter)
│   │   └── README.md
│   └── skills/                   # Skill definitions
│       └── README.md
│
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_agent_executor.py
    ├── test_recipe_resolver.py
    ├── test_streaming.py
    └── test_tools.py
```

---

## 4. The Request Flow

Every request starts with an agent ID and follows this exact pipeline:

```
Client Request (AgentExecuteRequest)
    │
    ▼
┌─────────────────────────────────────────────┐
│  1. API Layer (engine/api/routes/agent.py)   │
│     - Validate request                       │
│     - Open NDJSON stream                     │
│     - Create StreamEmitter                   │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  2. Recipe Resolver (engine/recipes/)        │
│     INPUT:  agent_id + variables + overrides │
│     OUTPUT: RecipeResult (config object)     │
│     *** THIS IS A BLACK BOX ***              │
│     Returns: system_prompt, model, tools,    │
│     temperature, max_tokens, etc.            │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  3. Agent Executor (engine/agent/)           │
│     - Builds ClaudeAgentOptions from config  │
│     - Registers custom tools (incl. Recipe   │
│       Tool) via ClaudeSDKClient              │
│     - Attaches MCP servers                   │
│     - Runs the agent loop                    │
│     - Streams events back via emitter        │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  4. Stream Response                          │
│     NDJSON events: status, content, tool_use,│
│     tool_result, error, done                 │
└─────────────────────────────────────────────┘
```

---

## 5. Request & Response Schemas

### 5.1 Input: AgentExecuteRequest

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Union
import uuid

class AgentExecuteRequest(BaseModel):
    """Every request to execute an agent starts here."""

    # REQUIRED: The agent/recipe UUID. This is THE key that unlocks everything.
    id: str = Field(..., description="Agent/Recipe UUID. The recipe system resolves this into a full config.")

    # User's message (optional — some agents are fully autonomous)
    user_input: Optional[Union[str, List[Dict[str, Any]]]] = None

    # Variables to inject into the recipe template
    variables: Optional[Dict[str, Any]] = Field(default_factory=dict)

    # Override specific config values (temperature, max_tokens, model, etc.)
    config_overrides: Optional[Dict[str, Any]] = Field(default_factory=dict)

    # Session tracking
    conversation_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))

    # Execution flags
    stream: bool = True
    debug: bool = False
```

### 5.2 Output: RecipeResult (What the black box returns)

```python
class RecipeResult(BaseModel):
    """The Recipe system ALWAYS returns this shape. No exceptions."""

    # Success or failure
    success: bool
    error: Optional[str] = None  # If success=False, this explains why

    # LLM Configuration
    system_prompt: str = ""
    model: Optional[str] = None  # e.g., "claude-sonnet-4-5-20250929", "gpt-4o", etc.
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    max_turns: Optional[int] = None

    # Tool configuration
    allowed_tools: Optional[List[str]] = None  # e.g., ["Bash", "Read", "Write", "recipe_tool"]
    custom_tools: Optional[List[Dict[str, Any]]] = None  # Additional tool definitions
    mcp_servers: Optional[List[Dict[str, Any]]] = None  # MCP servers to attach

    # Permission mode for Claude Agent SDK
    permission_mode: Optional[str] = "bypassPermissions"  # Default for container execution

    # The actual user-facing prompt (recipe may transform user_input)
    compiled_prompt: Optional[str] = None

    # Arbitrary metadata the recipe wants to pass through
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
```

### 5.3 Streaming Events

All responses stream as NDJSON (newline-delimited JSON). Each line is one event:

```python
class StreamEvent(BaseModel):
    event: str  # Event type
    data: Dict[str, Any]

# Event types:
# "status"       — Connection state, processing state
# "content"      — Text content from the agent (streamable)
# "tool_use"     — Agent is invoking a tool (name + input)
# "tool_result"  — Tool execution result
# "recipe_call"  — A Recipe-as-Tool is being executed (sub-agent visibility)
# "error"        — Error occurred
# "done"         — Agent execution complete, final result
# "debug"        — Debug info (only when debug=True)
```

---

## 6. The Three Recipe Integration Layers

This is the core architectural concept. Recipes integrate at three distinct layers:

### 6.1 Layer 1: Recipe as Agent (Outer Wrapper)

This is the **entry point** for every request. The Recipe system resolves the agent ID into a full configuration that drives the entire Claude Agent SDK session.

```python
# In engine/agent/executor.py

async def execute(self, request: AgentExecuteRequest, emitter: StreamEmitter):
    # Step 1: Resolve recipe
    recipe_result = await self.recipe_resolver.resolve(
        agent_id=request.id,
        user_input=request.user_input,
        variables=request.variables,
        config_overrides=request.config_overrides,
    )

    if not recipe_result.success:
        await emitter.emit_error(recipe_result.error)
        return

    # Step 2: Build SDK options from recipe config
    options = ClaudeAgentOptions(
        system_prompt=recipe_result.system_prompt,
        model=recipe_result.model,
        allowed_tools=recipe_result.allowed_tools or self.default_tools,
        permission_mode=recipe_result.permission_mode,
        max_turns=recipe_result.max_turns or 50,
        cwd=self.workspace_path,
    )

    # Step 3: Run agent with compiled prompt
    prompt = recipe_result.compiled_prompt or request.user_input or ""
    async with ClaudeSDKClient(options=options) as client:
        # ... execute and stream
```

### 6.2 Layer 2: Recipe as Sub-Agent

When Claude needs to delegate a specialized sub-task, it can invoke a sub-agent that is itself backed by a Recipe. This uses the Claude Agent SDK's native subagent support.

Sub-agent definitions live in `.claude/agents/` as Markdown files. The Recipe system can dynamically generate these, or they can be pre-configured.

```markdown
# .claude/agents/research-specialist.md
---
name: research-specialist
description: Deep research on a specific topic using a specialized recipe
tools:
  - WebSearch
  - WebFetch
  - Read
  - Write
---

You are a research specialist. Your job is to thoroughly research
the assigned topic and produce a structured report.

{{system_prompt_from_recipe}}
```

For **dynamic sub-agents** (where the Recipe system generates the sub-agent config at runtime), use the SDK's programmatic subagent API rather than filesystem-based agents.

### 6.3 Layer 3: Recipe as Tool (The Big One)

This is the most powerful integration. Claude sees a tool called `execute_recipe` in its available tools. When Claude calls it, **a completely separate LLM call happens under the hood via LiteLLM** — Claude doesn't know it's talking to another AI. It just gets results back.

```python
# In engine/tools/recipe_tool.py

from claude_agent_sdk import tool

@tool
def execute_recipe(
    recipe_id: str,
    task_description: str,
    variables: dict = {},
    config_overrides: dict = {},
) -> str:
    """
    Execute a specialized AI recipe for a specific task. Use this when you need
    expert-level processing for a sub-task such as: content generation, analysis,
    translation, code review, data extraction, summarization, or any task that
    benefits from a specialized, pre-configured AI agent.

    Args:
        recipe_id: The UUID of the recipe to execute.
        task_description: What you need this recipe to do. Be specific.
        variables: Key-value pairs of variables the recipe needs.
        config_overrides: Optional overrides (temperature, model, max_tokens).

    Returns:
        The recipe's output as a string.
    """
    # 1. Resolve recipe config (same black box)
    recipe_result = recipe_resolver.resolve_sync(
        agent_id=recipe_id,
        user_input=task_description,
        variables=variables,
        config_overrides=config_overrides,
    )

    if not recipe_result.success:
        return f"Error: Recipe resolution failed — {recipe_result.error}"

    # 2. Make LLM call directly through LiteLLM (NOT through Claude Agent SDK)
    from litellm import completion

    response = completion(
        model=recipe_result.model or "claude-sonnet-4-5-20250929",
        messages=[
            {"role": "system", "content": recipe_result.system_prompt},
            {"role": "user", "content": recipe_result.compiled_prompt or task_description},
        ],
        temperature=recipe_result.temperature,
        max_tokens=recipe_result.max_tokens,
    )

    return response.choices[0].message.content
```

**Why this matters**: Claude's agent loop is orchestrating. When it hits a task it knows a Recipe handles better, it calls `execute_recipe`. Under the hood, that might call GPT-4o for cheap summarization, Gemini for long-context analysis, or Claude Opus for complex reasoning — whatever the Recipe specifies. The outer Claude agent just sees the result come back as a string.

---

## 7. LiteLLM Setup

### 7.1 LiteLLM Config (litellm_config.yaml)

```yaml
model_list:
  # Anthropic Direct
  - model_name: claude-sonnet-4-5
    litellm_params:
      model: anthropic/claude-sonnet-4-5-20250929
      api_key: os.environ/ANTHROPIC_API_KEY

  - model_name: claude-opus-4-5
    litellm_params:
      model: anthropic/claude-opus-4-5-20251101
      api_key: os.environ/ANTHROPIC_API_KEY

  # OpenAI
  - model_name: gpt-4o
    litellm_params:
      model: openai/gpt-4o
      api_key: os.environ/OPENAI_API_KEY

  - model_name: gpt-4o-mini
    litellm_params:
      model: openai/gpt-4o-mini
      api_key: os.environ/OPENAI_API_KEY

  # Google Gemini
  - model_name: gemini-2.5-flash
    litellm_params:
      model: gemini/gemini-2.5-flash-preview
      api_key: os.environ/GEMINI_API_KEY

  # AWS Bedrock (if needed)
  # - model_name: bedrock-claude-sonnet
  #   litellm_params:
  #     model: bedrock/us.anthropic.claude-sonnet-4-5-20250929-v1:0
  #     aws_region_name: us-east-1

litellm_settings:
  drop_params: true
  set_verbose: false
```

### 7.2 The LiteLLM Proxy Hack (For Agent SDK)

The Claude Agent SDK natively only talks to the Anthropic API. To route it through LiteLLM (enabling any model), override the base URL:

```python
# In engine/agent/executor.py — set BEFORE creating the SDK client

import os

def configure_litellm_proxy():
    """
    Point the Claude Agent SDK at LiteLLM proxy instead of Anthropic directly.
    This enables using any model provider through the SDK's agent loop.
    """
    litellm_proxy_url = os.getenv("LITELLM_PROXY_URL", "http://localhost:4000")

    os.environ["ANTHROPIC_BASE_URL"] = litellm_proxy_url
    # The API key here is your LiteLLM master key, not an Anthropic key
    os.environ["ANTHROPIC_API_KEY"] = os.getenv("LITELLM_MASTER_KEY", "")
```

**Important**: This proxy hack is specifically for **Layer 1 (Recipe as Agent)** when you want the outer Claude Agent SDK loop to use a non-Anthropic model. For **Layer 3 (Recipe as Tool)**, LiteLLM is called directly via `litellm.completion()` — no proxy needed.

### 7.3 docker-compose.yml

```yaml
version: "3.9"

services:
  litellm:
    image: ghcr.io/berriai/litellm:main-latest
    ports:
      - "4000:4000"
    volumes:
      - ./litellm_config.yaml:/app/config.yaml
    environment:
      - LITELLM_MASTER_KEY=${LITELLM_MASTER_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    command: ["--config", "/app/config.yaml", "--port", "4000"]

  engine:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./workspace:/workspace  # Agent working directory
      - ./.claude:/app/.claude  # Claude Code config
    environment:
      - LITELLM_PROXY_URL=http://litellm:4000
      - LITELLM_MASTER_KEY=${LITELLM_MASTER_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - WORKSPACE_PATH=/workspace
    depends_on:
      - litellm
```

---

## 8. Environment Variables (.env.example)

```bash
# === Required ===
ANTHROPIC_API_KEY=sk-ant-...          # Direct Anthropic access (also used if no LiteLLM)
LITELLM_MASTER_KEY=sk-matrx-...      # Master key for LiteLLM proxy auth
LITELLM_PROXY_URL=http://localhost:4000

# === Optional Provider Keys (add as needed) ===
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
# AWS_ACCESS_KEY_ID=...
# AWS_SECRET_ACCESS_KEY=...
# AWS_DEFAULT_REGION=us-east-1

# === Engine Configuration ===
WORKSPACE_PATH=/workspace
LOG_LEVEL=INFO
DEFAULT_MODEL=claude-sonnet-4-5
DEFAULT_MAX_TURNS=50
DEFAULT_PERMISSION_MODE=bypassPermissions

# === API Auth (implement your own) ===
AUTH_ENABLED=true
# AUTH_SECRET=...
```

---

## 9. Custom Tools Architecture

### 9.1 Tool Registry

Every tool in `engine/tools/` is auto-discovered and registered with the Claude Agent SDK client.

```python
# engine/tools/registry.py

from typing import List, Callable
from claude_agent_sdk import tool

class ToolRegistry:
    """Discovers and manages all custom tools available to agents."""

    def __init__(self):
        self._tools: List[Callable] = []

    def register(self, fn: Callable):
        """Register a tool function."""
        self._tools.append(fn)

    def get_all(self) -> List[Callable]:
        """Return all registered tool functions."""
        return self._tools

    def get_by_names(self, names: List[str]) -> List[Callable]:
        """Return tools matching the given names."""
        return [t for t in self._tools if t.__name__ in names]

# Global registry instance
registry = ToolRegistry()
```

### 9.2 Adding a New Custom Tool

Create a new file in `engine/tools/`. Use the `@tool` decorator from `claude_agent_sdk`. Register it in the module's `__init__.py`.

```python
# engine/tools/my_new_tool.py

from claude_agent_sdk import tool
from engine.tools.registry import registry

@tool
def my_new_tool(param1: str, param2: int = 10) -> str:
    """
    Clear description of what this tool does.
    Claude reads this docstring to decide when to use the tool.

    Args:
        param1: What this parameter is for.
        param2: What this parameter is for. Defaults to 10.

    Returns:
        Description of the return value.
    """
    # Your implementation
    result = do_something(param1, param2)
    return str(result)

# Auto-register
registry.register(my_new_tool)
```

### 9.3 Built-In Custom Tools to Implement

These are the custom tools that should be created beyond Claude's default toolset (Bash, Read, Write, Edit, Glob, Grep, WebSearch, WebFetch):

| Tool | File | Purpose |
|---|---|---|
| `execute_recipe` | `recipe_tool.py` | **THE core tool.** Executes a Recipe via LiteLLM. See Section 6.3. |
| `query_database` | `database_tool.py` | Query Supabase/Postgres. Accepts SQL or structured query. |
| `call_api` | `http_tool.py` | Make authenticated HTTP requests to external services. |

Add more as needed. The pattern is always the same: `@tool` decorator, clear docstring, register in the registry.

---

## 10. MCP Server Configuration

MCP servers extend Claude's capabilities with external integrations. They're configured in `engine/mcp/config.json` and loaded at agent startup.

```json
{
  "servers": [
    {
      "name": "playwright-browser",
      "enabled": false,
      "transport": "stdio",
      "command": "npx",
      "args": ["@anthropic-ai/playwright-mcp"]
    },
    {
      "name": "github",
      "enabled": false,
      "transport": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  ]
}
```

The MCP manager loads this config and attaches enabled servers to the SDK client at runtime. Recipes can also specify additional MCP servers in their `mcp_servers` field.

---

## 11. The Recipe System Black Box

**Developers: Read this carefully.**

The Recipe system is Arman's proprietary system. It will be integrated after the core engine is built. Your job is to build everything around it using the `RecipeResolver` interface.

### 11.1 The Interface (DO NOT CHANGE)

```python
# engine/recipes/interfaces.py

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class RecipeResult(BaseModel):
    """
    The output of recipe resolution. This is the contract.
    The Recipe system ALWAYS returns this shape.
    If it fails, success=False and error is populated.
    If it succeeds, all relevant fields are populated.
    """
    success: bool
    error: Optional[str] = None

    # LLM config
    system_prompt: str = ""
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    max_turns: Optional[int] = None

    # Tool config
    allowed_tools: Optional[List[str]] = None
    custom_tools: Optional[List[Dict[str, Any]]] = None
    mcp_servers: Optional[List[Dict[str, Any]]] = None

    # Execution config
    permission_mode: Optional[str] = "bypassPermissions"
    compiled_prompt: Optional[str] = None

    # Pass-through
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class RecipeResolverInterface(ABC):
    """
    Abstract interface for the Recipe system.
    Developers: implement the placeholder. Arman will replace it.
    """

    @abstractmethod
    async def resolve(
        self,
        agent_id: str,
        user_input: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        config_overrides: Optional[Dict[str, Any]] = None,
    ) -> RecipeResult:
        """
        Resolve an agent_id into a full execution config.

        Args:
            agent_id: UUID of the agent/recipe.
            user_input: The user's message (may be empty).
            variables: Template variables to inject.
            config_overrides: Override specific config values.

        Returns:
            RecipeResult with full LLM configuration.
        """
        ...

    def resolve_sync(
        self,
        agent_id: str,
        user_input: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        config_overrides: Optional[Dict[str, Any]] = None,
    ) -> RecipeResult:
        """
        Synchronous version for use inside @tool functions
        (which cannot be async in the current SDK).
        """
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(
                    asyncio.run,
                    self.resolve(agent_id, user_input, variables, config_overrides)
                ).result()
        return asyncio.run(self.resolve(agent_id, user_input, variables, config_overrides))
```

### 11.2 The Placeholder Implementation

```python
# engine/recipes/resolver.py

from engine.recipes.interfaces import RecipeResolverInterface, RecipeResult
from typing import Optional, Dict, Any


class PlaceholderRecipeResolver(RecipeResolverInterface):
    """
    PLACEHOLDER: Returns a sensible default config for any agent_id.
    Arman will replace this with the real Recipe system.

    For now, this allows the entire engine to be tested end-to-end
    without the Recipe system being connected.
    """

    async def resolve(
        self,
        agent_id: str,
        user_input: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        config_overrides: Optional[Dict[str, Any]] = None,
    ) -> RecipeResult:
        overrides = config_overrides or {}

        return RecipeResult(
            success=True,
            system_prompt=overrides.get(
                "system_prompt",
                "You are a helpful AI assistant with full access to the local "
                "filesystem and shell. You can read, write, and execute code. "
                "Be thorough and precise."
            ),
            model=overrides.get("model", None),  # None = use SDK default
            temperature=overrides.get("temperature", None),
            max_tokens=overrides.get("max_tokens", None),
            max_turns=overrides.get("max_turns", 30),
            allowed_tools=overrides.get("allowed_tools", [
                "Bash", "Read", "Write", "Edit", "Glob", "Grep",
                "WebSearch", "WebFetch",
                "execute_recipe",  # Always include Recipe-as-Tool
            ]),
            permission_mode="bypassPermissions",
            compiled_prompt=user_input,
            metadata={"agent_id": agent_id, "variables": variables or {}},
        )
```

---

## 12. Dockerfile

```dockerfile
FROM python:3.11-slim

# Install Node.js (required by Claude Code CLI bundled with SDK)
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]"

# Copy application code
COPY . .

# Create workspace directory for agent execution
RUN mkdir -p /workspace

# Expose API port
EXPOSE 8000

# Run the API server
CMD ["uvicorn", "engine.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 13. Key Implementation Notes

### 13.1 The Agent SDK is a subprocess wrapper

The Claude Agent SDK spawns the Claude Code CLI as a child process. This means:
- Each `ClaudeSDKClient` instance = one CLI process
- The CLI maintains shell state, file context, and conversation history
- Multiple clients can run in the same container (for parallel sub-tasks)
- The CLI auto-bundles with `pip install claude-agent-sdk` — no separate install needed

### 13.2 Streaming is non-negotiable

Every agent execution MUST stream. The `StreamEmitter` wraps FastAPI's `StreamingResponse` and emits NDJSON events. Do not buffer and return — always stream.

### 13.3 Permission mode in containers

Since agents run in isolated containers with intentional full access, use `permission_mode="bypassPermissions"`. This skips interactive permission prompts that would block headless execution.

On first run in a new container, the CLI needs `--dangerously-skip-permissions` to be set. The SDK handles this via the permission_mode option.

### 13.4 LiteLLM serves two purposes

1. **As a proxy** (for the Agent SDK): Override `ANTHROPIC_BASE_URL` to point at LiteLLM, enabling the SDK's agent loop to use any model.
2. **As a direct client** (for Recipe-as-Tool): Import `litellm` and call `completion()` directly when the `execute_recipe` tool fires. No proxy needed for this path.

Both should be supported simultaneously.

### 13.5 Error handling

Every layer must handle errors gracefully and surface them through the stream:
- Recipe resolution failure → emit `error` event, stop
- SDK process crash → emit `error` event with exit code
- Tool execution failure → let Claude see the error (it will retry or adapt)
- Stream disconnect → cancel the background task, clean up

### 13.6 Cost tracking

The Agent SDK supports cost tracking. Implement the `on_usage` callback to capture token counts and costs per execution. This data flows back through the stream as `usage` events and should be stored for billing.

---

## 14. Development Setup (For the Developer)

```bash
# 1. Clone and enter repo
git clone <repo-url>
cd matrx-agent-engine

# 2. Copy environment template
cp .env.example .env
# Edit .env with your API keys

# 3. Install dependencies
pip install -e ".[dev]"

# 4. Start LiteLLM proxy (in a separate terminal or via docker-compose)
docker-compose up litellm

# 5. Run the API server
uvicorn engine.main:app --reload --port 8000

# 6. Test with curl
curl -X POST http://localhost:8000/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "id": "9f3c2e7a-6d4b-4e5a-9a8b-2f7c1d0e8b21",
    "user_input": "List all Python files in the current directory",
    "variables": {},
    "config_overrides": {}
  }'

# 7. Run tests
pytest tests/ -v
```

---

## 15. What Arman Will Add Later

The following are explicitly out of scope for the initial build. Build the interfaces and placeholders, but do not implement:

1. **The real Recipe system** — replaces `PlaceholderRecipeResolver`
2. **Database integration** — Supabase connection for recipe storage, conversation history, usage tracking
3. **Authentication** — Real auth middleware (placeholder should accept any request in dev)
4. **Multi-container orchestration** — Kubernetes/Docker Swarm configs for running N agent instances
5. **Additional custom tools** — Domain-specific tools for AI Matrx applications
6. **Additional MCP servers** — Per-project MCP configurations
7. **Conversation persistence** — Storing and resuming agent sessions across requests

---

## 16. Success Criteria

The repo is considered complete when:

- [ ] `POST /agent/execute` accepts the request schema and streams NDJSON events
- [ ] The placeholder recipe resolver returns a valid config for any agent ID
- [ ] The Claude Agent SDK executes successfully with the resolved config
- [ ] Claude can use Bash, Read, Write, Edit, and other built-in tools
- [ ] The `execute_recipe` custom tool is registered and callable by Claude
- [ ] The `execute_recipe` tool makes a real LLM call through LiteLLM
- [ ] LiteLLM proxy is running and the SDK can be routed through it
- [ ] MCP server configuration is loadable (even if no servers are enabled)
- [ ] The tool registry auto-discovers tools from `engine/tools/`
- [ ] Streaming works end-to-end (status → content → tool_use → done)
- [ ] Errors at any layer surface cleanly through the stream
- [ ] Docker build succeeds and the container runs the full stack
- [ ] `GET /health` and `GET /ready` return appropriate status
- [ ] Basic tests pass for executor, resolver, streaming, and tools
