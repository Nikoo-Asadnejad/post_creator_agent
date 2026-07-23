"""Shared test fixtures. All tests run fully offline by stubbing the agents/LLM/HTTP."""

from __future__ import annotations

import pytest

from post_generator.schemas import Image


@pytest.fixture
def stub_generators(monkeypatch):
    """Replace the two heavy generator agents with deterministic fakes."""
    from post_generator.agents import content as content_agent
    from post_generator.agents import image as image_agent

    monkeypatch.setattr(
        content_agent, "generate_post", lambda topic, content: f"POST[{topic}]::{content[:20]}"
    )
    monkeypatch.setattr(
        image_agent,
        "generate",
        lambda topic, content: Image(prompt=f"IMG[{topic}]", url=None, local_path=None),
    )
