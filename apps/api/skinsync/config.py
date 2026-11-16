"""Settings from environment variables (12-factor). Prod refuses weak defaults."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEV_SECRET = "dev-only-insecure-secret-change-me-0000000000"
DEV_ENC_KEY = "ZGV2LW9ubHkta2V5LTMyLWJ5dGVzLWxvY2FsLXVzZSE="  # base64 of a 32-byte DEV-ONLY key; prod refuses it


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SKINSYNC_", env_file=".env", extra="ignore")

    env: str = Field(default="dev", pattern="^(dev|test|staging|prod)$")
    app_name: str = "SkinSync"
    database_url: str = "postgresql+psycopg://postgres@localhost:5432/skinsync"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = DEV_SECRET
    image_encryption_key: str = DEV_ENC_KEY  # base64, 32 bytes, AES-256-GCM
    cors_origins: list[str] = ["http://localhost:3000"]
    public_base_url: str = "http://localhost:3000"
    cookie_secure: bool = False  # True behind HTTPS (staging/prod)

    access_token_minutes: int = 15
    refresh_token_days: int = 14
    policy_version: str = "2026-11-01"

    storage_backend: str = Field(default="local", pattern="^(local|s3)$")
    storage_dir: str = "./var/storage"
    s3_endpoint: str | None = None
    s3_bucket: str = "skinsync-private"
    s3_access_key: str | None = None
    s3_secret_key: str | None = None

    skin_model_adapter: str = "heuristic"  # "heuristic" (experimental, labelled) | "mock" (labelled demo) | "none"
    skin_image_retention_hours: int = 24
    knowledge_dir: str = "../../knowledge"
    demo_mode: bool = False             # allows the labelled fictional demo knowledge version
    obf_user_agent: str = "SkinSync/0.1 (student project; contact via repository)"
    rate_limit_enabled: bool = True

    @model_validator(mode="after")
    def _prod_guard(self):
        if self.env in ("staging", "prod"):
            if self.secret_key == DEV_SECRET or len(self.secret_key) < 32:
                raise ValueError("SKINSYNC_SECRET_KEY must be set to a strong value outside dev")
            if self.image_encryption_key == DEV_ENC_KEY:
                raise ValueError("SKINSYNC_IMAGE_ENCRYPTION_KEY must be set outside dev")
            if not self.cookie_secure:
                raise ValueError("SKINSYNC_COOKIE_SECURE must be true outside dev")
            if self.demo_mode and self.env == "prod":
                raise ValueError("demo_mode is not allowed in prod")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
