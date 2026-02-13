"""Auth verification — stub that passes all requests in dev mode.

Real authentication will be implemented by Arman. For now, this
allows any request through when AUTH_ENABLED is false (default).
"""

from __future__ import annotations

import os

from fastapi import HTTPException, Request


async def verify_user(request: Request) -> dict[str, str]:
    """Dependency that verifies the requesting user.

    In dev mode (AUTH_ENABLED=false), returns a placeholder user.
    When auth is enabled, validates the Authorization header.

    Returns:
        A dict with user information.
    """
    auth_enabled = os.getenv("AUTH_ENABLED", "false").lower() in ("true", "1", "yes")

    if not auth_enabled:
        return {"user_id": "dev-user", "role": "admin"}

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Empty token")

    # Placeholder: accept any non-empty token in this stub
    # Real implementation will validate JWTs or API keys
    return {"user_id": "authenticated-user", "role": "user", "token": token}
