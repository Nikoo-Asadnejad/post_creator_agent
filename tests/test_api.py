"""API surface: health + generate (pipeline stubbed)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from post_generator import api
from post_generator.schemas import GenerateResponse


def test_health():
    client = TestClient(api.app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_generate_returns_assembled_schema(monkeypatch):
    async def _fake_generate(request):
        return GenerateResponse(
            linkedin_post="hello post",
            image_prompt="an image",
            image_url="http://img/x.png",
            image_path="/out/x.png",
            sources=["http://s/1"],
            used_search=True,
            sufficiency_reason="thin",
        )

    monkeypatch.setattr(api, "generate", _fake_generate)

    client = TestClient(api.app)
    resp = client.post("/generate", json={"topic": "AI", "content": None})
    assert resp.status_code == 200
    body = resp.json()
    assert body["linkedin_post"] == "hello post"
    assert body["used_search"] is True
    assert body["sources"] == ["http://s/1"]
