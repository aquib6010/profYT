from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = Field(default="sqlite+aiosqlite:///./profitly.db")

    session_secret: str = Field(default="dev-only-change-me")
    token_encryption_key: str = Field(default="")

    google_client_id: str = Field(default="")
    google_client_secret: str = Field(default="")
    oauth_redirect_uri: str = Field(default="http://localhost:8000/auth/google/callback")

    frontend_origin: str = Field(default="http://localhost:5173")

    # Session cookie. Local dev is same-site over http, so lax/insecure works.
    # In production the frontend (Vercel) and backend (Render) are cross-site, so
    # the cookie must be SameSite=None + Secure or the browser drops it.
    # Set COOKIE_SAMESITE=none and COOKIE_SECURE=true in the prod environment.
    cookie_samesite: str = Field(default="lax")
    cookie_secure: bool = Field(default=False)

    hf_home: str = Field(default="./.cache/huggingface")
    log_level: str = Field(default="INFO")


@lru_cache
def get_settings() -> Settings:
    return Settings()
