"""All settings come from environment variables (or a local .env file)."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from taxdost.db.url import to_asyncpg_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "taxdost"
    # No defaults on purpose: if these are missing, the app refuses to start (fail fast).
    app_env: Literal["local", "ci", "production"]
    database_url: str
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    data_file: Path = Path("data/sample_records.json")
    db_pool_size: int = 5
    db_max_overflow: int = 5
    # The commit this image was built from. CI sets it (Dockerfile ARG GIT_SHA); locally "dev".
    git_sha: str = "dev"

    # LLM gateway (Day 8)
    gemini_api_key: str = ""
    groq_api_key: str = ""
    llm_primary_model: str = "gemini-3.5-flash-lite"
    llm_fallback_model: str = "openai/gpt-oss-20b"

    llm_primary_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai"
    llm_fallback_base_url: str = "https://api.groq.com/openai/v1"

    llm_timeout_seconds: float = 30.0
    usd_inr: float = 95.0
    prompts_dir: Path = Path("prompts")

    @field_validator("database_url")
    @classmethod
    def _asyncpg(cls, value: str) -> str:
        return to_asyncpg_url(value)


@lru_cache
def get_settings() -> Settings:
    """Build the settings once and reuse them."""
    return Settings()
