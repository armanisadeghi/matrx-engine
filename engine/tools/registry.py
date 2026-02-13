"""ToolRegistry — discovers and manages all custom tools available to agents."""

from __future__ import annotations

import importlib
import pkgutil
from typing import Any, Callable

from engine.utils.logging import get_logger

logger = get_logger(__name__)


class ToolRegistry:
    """Discovers and manages all custom tools available to agents.

    Tools are callables decorated with @tool from claude_agent_sdk.
    They are collected here so the agent executor can build an MCP server
    containing all registered tools.
    """

    def __init__(self) -> None:
        self._tools: list[Callable[..., Any]] = []
        self._tool_map: dict[str, Callable[..., Any]] = {}

    def register(self, fn: Callable[..., Any]) -> None:
        """Register a tool function."""
        name = getattr(fn, "_tool_name", fn.__name__)
        if name in self._tool_map:
            logger.warning("tool_already_registered", name=name)
            return
        self._tools.append(fn)
        self._tool_map[name] = fn
        logger.info("tool_registered", name=name)

    def get_all(self) -> list[Callable[..., Any]]:
        """Return all registered tool functions."""
        return list(self._tools)

    def get_by_names(self, names: list[str]) -> list[Callable[..., Any]]:
        """Return tools matching the given names."""
        return [self._tool_map[n] for n in names if n in self._tool_map]

    def get_names(self) -> list[str]:
        """Return all registered tool names."""
        return list(self._tool_map.keys())

    def auto_discover(self) -> None:
        """Auto-discover tool modules in the engine.tools package.

        Imports every submodule of engine.tools. Each submodule is expected
        to register its tools with the global registry at import time.
        """
        import engine.tools as tools_pkg

        for importer, modname, ispkg in pkgutil.iter_modules(tools_pkg.__path__):
            if modname in ("registry", "__init__"):
                continue
            full_name = f"engine.tools.{modname}"
            try:
                importlib.import_module(full_name)
                logger.info("tool_module_loaded", module=full_name)
            except Exception as exc:
                logger.error("tool_module_load_failed", module=full_name, error=str(exc))


# Global registry instance
registry = ToolRegistry()
