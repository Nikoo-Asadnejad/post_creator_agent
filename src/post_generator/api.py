"""FastAPI HTTP interface."""

from __future__ import annotations

from fastapi import FastAPI

from .pipeline import generate
from .schemas import GenerateRequest, GenerateResponse

app = FastAPI(title="LinkedIn Post Generator", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@app.post("/generate", response_model=GenerateResponse)
def generate_endpoint(request: GenerateRequest) -> GenerateResponse:
    """Generate a LinkedIn post + image for a topic (+ optional content)."""
    return generate(request)
