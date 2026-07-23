"""Content-sufficiency judge.

Decides whether the caller-supplied content is rich and relevant enough to write a grounded
LinkedIn post, or whether we must run the search agent first.
"""

from __future__ import annotations

from ..config import get_settings
from ..llm import make_llm
from ..prompts import SUFFICIENCY_PROMPT
from ..schemas import Sufficiency


def judge(topic: str, content: str | None) -> Sufficiency:
    """Return a Sufficiency verdict for (topic, content).

    Null / blank / very short content is judged insufficient without an LLM call. Otherwise an
    LLM (deterministic) classifies sufficiency using structured output.
    """
    settings = get_settings()
    text = (content or "").strip()
    if len(text) < settings.min_content_chars:
        return Sufficiency(
            enough=False,
            reason=f"Content is empty or shorter than {settings.min_content_chars} characters.",
        )

    llm = make_llm(temperature=settings.fact_temperature)
    structured = llm.with_structured_output(Sufficiency)
    chain = SUFFICIENCY_PROMPT | structured
    return chain.invoke({"topic": topic, "content": text})
