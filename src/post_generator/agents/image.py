"""Image generator.

The LLM writes a literal image prompt; we then fetch a real PNG from the free, key-less
Pollinations image API and save it locally. Network failures degrade gracefully to
"prompt only" (url/local_path = None).
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from urllib.parse import quote

import httpx
from langchain_core.output_parsers import StrOutputParser

from ..config import get_settings
from ..llm import make_llm
from ..prompts import IMAGE_PROMPT
from ..schemas import Image

logger = logging.getLogger(__name__)


def _slug(topic: str) -> str:
    """Filesystem-safe short slug from a topic."""
    s = re.sub(r"[^a-zA-Z0-9]+", "-", topic.strip().lower()).strip("-")
    return (s[:40] or "image")


def build_prompt(topic: str, content: str) -> str:
    """Use the LLM to produce a detailed image-generation prompt."""
    settings = get_settings()
    llm = make_llm(temperature=settings.gen_temperature)
    chain = IMAGE_PROMPT | llm | StrOutputParser()
    return chain.invoke({"topic": topic, "content": content}).strip()


def fetch_image(prompt: str, topic: str) -> tuple[str | None, str | None]:
    """Fetch a PNG for `prompt` from Pollinations and save it. Returns (url, local_path)."""
    settings = get_settings()
    url = f"{settings.image_api_base}/{quote(prompt)}"
    try:
        resp = httpx.get(url, timeout=settings.request_timeout, follow_redirects=True)
        resp.raise_for_status()
        out_dir = Path(settings.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        local_path = out_dir / f"{_slug(topic)}.png"
        local_path.write_bytes(resp.content)
        return url, str(local_path)
    except Exception as exc:  # noqa: BLE001 - graceful degradation
        logger.warning("Image fetch failed (%s); returning prompt only.", exc)
        return None, None


def generate(topic: str, content: str) -> Image:
    """Produce an image prompt and (best-effort) a saved PNG."""
    prompt = build_prompt(topic, content)
    url, local_path = fetch_image(prompt, topic)
    return Image(prompt=prompt, url=url, local_path=local_path)
