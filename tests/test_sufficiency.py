"""Sufficiency judge: short-circuit behavior + LLM path."""

from __future__ import annotations

import pytest
from langchain_core.runnables import RunnableLambda

from post_generator.agents import sufficiency
from post_generator.schemas import Sufficiency


@pytest.mark.parametrize("content", [None, "", "   ", "too short"])
def test_blank_or_short_content_is_insufficient_without_llm(content, monkeypatch):
    # If the LLM factory is touched, fail loudly - short content must short-circuit.
    monkeypatch.setattr(
        sufficiency, "make_llm", lambda *a, **k: pytest.fail("LLM should not be called")
    )
    verdict = sufficiency.judge("Some topic", content)
    assert verdict.enough is False
    assert verdict.reason


def test_long_content_invokes_llm(monkeypatch):
    class _FakeLLM:
        def with_structured_output(self, _schema):
            # Chain is PROMPT | structured; return a Runnable that yields a verdict.
            return RunnableLambda(lambda _pv: Sufficiency(enough=True, reason="looks good"))

    monkeypatch.setattr(sufficiency, "make_llm", lambda *a, **k: _FakeLLM())

    verdict = sufficiency.judge("Topic", "x" * 500)
    assert verdict.enough is True
    assert verdict.reason == "looks good"
