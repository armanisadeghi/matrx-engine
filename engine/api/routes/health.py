"""Health and readiness endpoints."""

from __future__ import annotations

import os

from fastapi import APIRouter

from engine import __version__

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    """Basic health check — returns OK if the server is running."""
    return {"status": "healthy", "version": __version__}


@router.get("/ready")
async def ready() -> dict:
    """Readiness check — verifies critical dependencies are available."""
    checks: dict[str, bool] = {}

    # Check that ANTHROPIC_API_KEY is set
    checks["anthropic_key"] = bool(os.getenv("ANTHROPIC_API_KEY"))

    # Check workspace directory exists
    workspace = os.getenv("WORKSPACE_PATH", "/workspace")
    checks["workspace"] = os.path.isdir(workspace)

    all_ready = all(checks.values())

    return {"ready": all_ready, "checks": checks}
