"""Search agent: Ollama LLM + a DuckDuckGo tool (LangChain 1.x create_agent).

Runs when the sufficiency judge decides the supplied content is not enough. It researches the
topic on the web and returns a factual summary that augments the content, plus the search
queries it issued (used as lightweight "sources").
"""

from __future__ import annotations

import logging

from langchain.agents import create_agent
from langchain_community.tools import DuckDuckGoSearchRun

from ..config import get_settings
from ..llm import make_llm
from ..prompts import SEARCH_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


def _collect_queries(messages: list) -> list[str]:
    """Pull the search queries the agent issued from its tool-call history."""
    queries: list[str] = []
    for msg in messages:
        for call in getattr(msg, "tool_calls", None) or []:
            args = call.get("args", {}) if isinstance(call, dict) else {}
            query = args.get("query") or args.get("__arg1")
            if query:
                queries.append(str(query))
    return list(dict.fromkeys(queries))  # de-duplicate, preserve order


def enrich(topic: str, content: str | None) -> tuple[str, list[str]]:
    """Research the topic and return (enriched_content, sources).

    On any failure, degrades to the original content (or a minimal note) so the pipeline can
    still produce a post.
    """
    try:
        settings = get_settings()
        llm = make_llm(temperature=settings.fact_temperature)
        search_tool = DuckDuckGoSearchRun()
        agent = create_agent(model=llm, tools=[search_tool], system_prompt=SEARCH_SYSTEM_PROMPT)

        user_msg = f"TOPIC: {topic}\n\nExisting notes (may be empty): {content or ''}"
        result = agent.invoke({"messages": [{"role": "user", "content": user_msg}]})
        messages = result.get("messages", [])

        summary = (messages[-1].content if messages else "").strip()
        if not summary:
            raise ValueError("Search agent returned empty output.")

        enriched = summary if not content else f"{content.strip()}\n\n{summary}"
        return enriched, _collect_queries(messages)
    except Exception as exc:  # noqa: BLE001 - graceful degradation
        logger.warning("Search agent failed (%s); falling back to original content.", exc)
        return (content or f"General knowledge about: {topic}"), []
