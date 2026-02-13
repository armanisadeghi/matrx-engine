"""Pydantic Settings — env-based configuration for the engine."""

from __future__ import annotations

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Engine-wide configuration loaded from environment variables."""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    # --- API Keys ---
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")

    # --- LiteLLM ---
    litellm_proxy_url: str = Field(default="http://localhost:4000", alias="LITELLM_PROXY_URL")
    litellm_master_key: str = Field(default="", alias="LITELLM_MASTER_KEY")
    use_litellm_proxy: bool = Field(default=False, alias="USE_LITELLM_PROXY")

    # --- Engine ---
    workspace_path: str = Field(default="/workspace", alias="WORKSPACE_PATH")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    default_model: str = Field(default="claude-sonnet-4-5", alias="DEFAULT_MODEL")
    default_max_turns: int = Field(default=50, alias="DEFAULT_MAX_TURNS")
    default_permission_mode: str = Field(default="bypassPermissions", alias="DEFAULT_PERMISSION_MODE")

    # --- Auth ---
    auth_enabled: bool = Field(default=False, alias="AUTH_ENABLED")
    auth_secret: str = Field(default="", alias="AUTH_SECRET")


def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
