"""Custom exception hierarchy for the engine."""

from __future__ import annotations


class EngineError(Exception):
    """Base exception for all engine errors."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class RecipeResolutionError(EngineError):
    """Raised when recipe resolution fails."""


class AgentExecutionError(EngineError):
    """Raised when the Claude Agent SDK execution fails."""


class ToolExecutionError(EngineError):
    """Raised when a custom tool execution fails."""


class StreamError(EngineError):
    """Raised when streaming encounters an error."""


class MCPError(EngineError):
    """Raised when MCP server management fails."""


class ConfigurationError(EngineError):
    """Raised when configuration is invalid or missing."""
