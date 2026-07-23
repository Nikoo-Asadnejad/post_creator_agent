"""ChatOllama factory."""

from __future__ import annotations

from langchain_ollama import ChatOllama

from .config import get_settings


def make_llm(temperature: float | None = None) -> ChatOllama:
    """Build a ChatOllama client.

    Args:
        temperature: Sampling temperature. Defaults to the configured generation temperature.
    """
    settings = get_settings()
    return ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=settings.gen_temperature if temperature is None else temperature,
    )
