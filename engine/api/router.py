"""Main API router — mounts all sub-routers."""

from __future__ import annotations

from fastapi import APIRouter

from engine.api.routes import agent, health, tools

api_router = APIRouter()

# Mount sub-routers
api_router.include_router(health.router)
api_router.include_router(agent.router)
api_router.include_router(tools.router)
