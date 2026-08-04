"""Pipeline conditional branch: search runs only when content is insufficient."""

from __future__ import annotations

from post_generator import pipeline
from post_generator.agents import search as search_agent
from post_generator.agents import sufficiency as sufficiency_agent
from post_generator.schemas import GenerateRequest, Sufficiency


def _track_search(monkeypatch):
    """Patch the search agent to record whether it ran."""
    calls = {"n": 0}

    async def _fake_enrich(topic, content):
        calls["n"] += 1
        return f"ENRICHED::{topic}", ["https://example.com/q"]

    monkeypatch.setattr(search_agent, "enrich", _fake_enrich)
    return calls


async def test_sufficient_content_skips_search(monkeypatch, stub_generators):
    
    async def fake_judge(t, c):
        return Sufficiency(enough=True, reason="ok")
    
    monkeypatch.setattr(
        sufficiency_agent, "judge", fake_judge)
    
    calls =  _track_search(monkeypatch)

    result = await pipeline.generate(GenerateRequest(topic="AI", content="x" * 500))

    assert calls["n"] == 0
    assert result.used_search is False
    assert result.sources == []
    assert result.linkedin_post.startswith("POST[AI]")
    assert result.image_prompt == "IMG[AI]"


async def test_insufficient_content_triggers_search(monkeypatch, stub_generators):
    
    async def fake_judge(t, c):
        return Sufficiency(enough=False, reason="thin")
    
    monkeypatch.setattr(
        sufficiency_agent, "judge", fake_judge)
    
    calls =  _track_search(monkeypatch)

    result = await pipeline.generate(GenerateRequest(topic="Quantum", content=None))

    assert calls["n"] == 1
    assert result.used_search is True
    assert result.sources == ["https://example.com/q"]
    # Enriched content must reach the content generator.
    assert "ENRICHED::Quantum"[:20] in result.linkedin_post
    assert result.sufficiency_reason == "thin"
