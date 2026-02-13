"""Shared fixtures for the test suite."""

from __future__ import annotations

import os
from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

# Ensure auth is disabled for tests
os.environ.setdefault("AUTH_ENABLED", "false")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("WORKSPACE_PATH", "/tmp/matrx-test-workspace")

from engine.main import app  # noqa: E402
from engine.recipes import PlaceholderRecipeResolver  # noqa: E402
from engine.streaming import StreamEmitter  # noqa: E402


@pytest.fixture
def recipe_resolver() -> PlaceholderRecipeResolver:
    return PlaceholderRecipeResolver()


@pytest.fixture
def emitter() -> StreamEmitter:
    return StreamEmitter(debug=True)


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
