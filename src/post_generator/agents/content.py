"""Content generator: summarizes the (enriched) content into a LinkedIn post."""

from __future__ import annotations

from langchain_core.output_parsers import StrOutputParser

from ..config import get_settings
from ..llm import make_llm
from ..prompts import CONTENT_PROMPT


def generate_post(topic: str, content: str) -> str:
    """Return a LinkedIn-ready post string grounded in `content`."""
    settings = get_settings()
    llm = make_llm(temperature=settings.gen_temperature)
    chain = CONTENT_PROMPT | llm | StrOutputParser()
    return chain.invoke({"topic": topic, "content": content}).strip()
