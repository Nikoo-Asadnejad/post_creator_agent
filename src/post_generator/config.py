"""Environment-driven configuration."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings, populated from environment / .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:3b"

    gen_temperature: float = 0.5  # medium creativity for generators
    fact_temperature: float = 0.0  # deterministic for judge / search

    image_api_base: str = "https://image.pollinations.ai/prompt"
    output_dir: str = "./output"

    search_max_results: int = 5
    min_content_chars: int = 200
    request_timeout: int = 60


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
