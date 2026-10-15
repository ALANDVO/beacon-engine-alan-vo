from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "beacon-engine"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True

    database_url: str = "sqlite+aiosqlite:///./data/beacon.db"
    database_echo: bool = False

    api_prefix: str = "/api/v1"

    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Demo mode for local development (no OIDC)
    demo_mode: bool = True
    demo_user_id: str = "demo-user"
    demo_user_roles: list[str] = ["admin", "operator", "viewer"]

    # OIDC settings (used when demo_mode=false)
    oidc_issuer_url: str = ""
    oidc_client_id: str = ""
    oidc_client_secret: str = ""
    oidc_redirect_uri: str = ""
    oidc_scopes: list[str] = ["openid", "profile", "email", "roles"]

    # LLM settings (optional)
    llm_api_key: str = ""
    llm_provider: str = "openai-compatible"
    llm_model: str = ""
    llm_base_url: str = ""

    # Build settings
    build_workspace: str = "./data/builds"
    max_concurrent_builds: int = 2


@lru_cache
def get_settings() -> Settings:
    return Settings()