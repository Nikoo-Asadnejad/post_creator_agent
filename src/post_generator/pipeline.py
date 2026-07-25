"""LCEL orchestration.

    judge  ->  RunnableBranch(enough?)  ->  RunnableParallel(content, image)  ->  assemble

The state is a dict threaded through the runnables. Agent functions are called via their
modules so tests can monkeypatch them.
"""

from __future__ import annotations

from langchain_core.runnables import (
    Runnable,
    RunnableBranch,
    RunnableLambda,
    RunnableParallel,
    RunnablePassthrough,
)

from .agents import content as content_agent
from .agents import image as image_agent
from .agents import search as search_agent
from .agents import sufficiency as sufficiency_agent
from .schemas import GenerateRequest, GenerateResponse, Sufficiency


async def _judge_node(state: dict) -> dict:
    """Attach a sufficiency verdict to the state."""
    verdict: Sufficiency = await sufficiency_agent.judge(state["topic"], state.get("content"))
    return {**state, "sufficiency": verdict, "sources": [], "used_search": False}


async def _search_node(state: dict) -> dict:
    """Enrich content via the search agent (only reached when content is insufficient)."""
    enriched, sources = await search_agent.enrich(state["topic"], state.get("content"))
    return {**state, "content": enriched, "sources": sources, "used_search": True}


def _assemble(bundle: dict) -> GenerateResponse:
    """Combine parallel generator outputs and carried state into the response."""
    state = bundle["state"]
    image = bundle["image"]
    verdict: Sufficiency = state["sufficiency"]
    return GenerateResponse(
        linkedin_post=bundle["content"],
        image_prompt=image.prompt,
        image_url=image.url,
        image_path=image.local_path,
        sources=state.get("sources", []),
        used_search=state.get("used_search", False),
        sufficiency_reason=verdict.reason,
    )

async def generate_content(s):
    return await content_agent.generate_post(s["topic"], s["content"])

async def generate_image(s):
    return await image_agent.generate(s["topic"], s["content"])
    

def build_pipeline() -> Runnable:
    """Assemble and return the full LCEL pipeline (dict -> GenerateResponse)."""
    judge = RunnableLambda(_judge_node)

    branch = RunnableBranch(
        (lambda s: not s["sufficiency"].enough, RunnableLambda(_search_node)),
        RunnablePassthrough(),  # content is sufficient -> keep as is
    )

    generators = RunnableParallel(
        content=RunnableLambda(generate_content),
        image=RunnableLambda(generate_image),
        state=RunnablePassthrough(), 
    )

    return judge | branch | generators | RunnableLambda(_assemble)


async def generate(request: GenerateRequest) -> GenerateResponse:
    """Convenience entry point: run the pipeline for a request."""
    pipeline = build_pipeline()
    return await pipeline.ainvoke({"topic": request.topic, "content": request.content})
