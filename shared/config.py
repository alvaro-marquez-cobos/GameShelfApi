"""Application settings loaded from environment variables.

Uses pydantic-settings to validate and parse configuration from .env files
and environment variables, providing typed access to all service credentials
and runtime parameters.
"""

from functools import lru_cache
from typing import cast

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized configuration for the GameShelf API.

    All fields map to environment variables (case-insensitive).
    Secrets and service URLs are loaded from .env in development.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Firebase
    firebase_project_id: str = ""
    firebase_private_key: str = ""
    firebase_client_email: str = ""

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_env: str = "development"
    cors_origins: list[str] = ["http://localhost:8081", "exp://localhost:8081"]

    # Rate limits
    steam_max_concurrent: int = 3
    psn_rate_limit: int = 300

    # External APIs
    steam_api_key: str = ""
    itad_api_key: str = ""
    epic_client_id: str = ""
    epic_client_secret: str = ""
    gog_client_id: str = ""
    gog_client_secret: str = ""

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: object) -> list[str]:
        if isinstance(v, str):
            import json

            return cast(list[str], json.loads(v))
        return cast(list[str], v)

    @property
    def is_testing(self) -> bool:
        return self.api_env == "testing"


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings singleton."""
    return Settings()
