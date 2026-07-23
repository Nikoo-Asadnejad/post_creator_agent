"""Pydantic models shared across the pipeline, API and CLI."""

from __future__ import annotations

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    """Input to the pipeline."""

    topic: str = Field(..., min_length=1, description="What the post is about.")
    content: str | None = Field(
        default=None, description="Optional source material. If missing/insufficient, we search."
    )


class Sufficiency(BaseModel):
    """Verdict from the content-sufficiency judge."""

    enough: bool = Field(..., description="True if the content is sufficient to write the post.")
    reason: str = Field(default="", description="Short justification for the verdict.")


class Image(BaseModel):
    """Result of the image generator."""

    prompt: str = Field(..., description="The image-generation prompt produced by the LLM.")
    url: str | None = Field(default=None, description="Remote URL of the generated image.")
    local_path: str | None = Field(default=None, description="Local path to the saved PNG.")


class GenerateResponse(BaseModel):
    """Final assembled output."""

    linkedin_post: str
    image_prompt: str
    image_url: str | None = None
    image_path: str | None = None
    sources: list[str] = Field(default_factory=list)
    used_search: bool = False
    sufficiency_reason: str = ""
