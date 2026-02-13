# AI Matrx Agent Engine

FastAPI-based Python backend that bridges the AI Matrx Recipe system with the Claude Agent SDK, LiteLLM, and containerized execution environments.

## Quick Start

```bash
# Clone and enter repo
git clone https://github.com/armanisadeghi/matrx-engine.git
cd matrx-engine

# Copy environment template and add your API keys
cp .env.example .env

# Install dependencies
uv sync

# Start LiteLLM proxy (optional, in separate terminal)
docker-compose up litellm

# Run the API server
uv run uvicorn engine.main:app --reload --port 8000
```

## Test the API

```bash
# Health check
curl http://localhost:8000/health

# Execute an agent
curl -X POST http://localhost:8000/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "id": "9f3c2e7a-6d4b-4e5a-9a8b-2f7c1d0e8b21",
    "user_input": "List all Python files in the current directory",
    "variables": {},
    "config_overrides": {}
  }'

# List available tools
curl http://localhost:8000/tools
```

## Running Tests

```bash
uv run pytest tests/ -v
```

## Architecture

See [AGENT_ENGINE_SPEC.md](AGENT_ENGINE_SPEC.md) for the full specification.
