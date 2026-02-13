"""Permission mode configuration for the Claude Agent SDK.

Since agents run in isolated containers with intentional full access,
the default is bypassPermissions. This skips interactive permission
prompts that would block headless execution.
"""

from __future__ import annotations

from enum import Enum


class PermissionMode(str, Enum):
    """Valid permission modes for the Claude Agent SDK."""

    PROMPT = "prompt"
    ACCEPT_EDITS = "acceptEdits"
    BYPASS = "bypassPermissions"


def resolve_permission_mode(mode: str | None, default: str = "bypassPermissions") -> str:
    """Resolve a permission mode string to a valid SDK value.

    Args:
        mode: The requested permission mode.
        default: Fallback if mode is None or invalid.

    Returns:
        A valid permission mode string.
    """
    if mode is None:
        return default
    try:
        return PermissionMode(mode).value
    except ValueError:
        return default
