# Spec: Multi-Agent LinkedIn Post Generator

## 1. Goal

Given a **topic** and an **optional content** blob, produce a ready-to-publish **LinkedIn post**
plus a **generated image**. When the supplied content is missing or insufficient, the system
autonomously researches the topic on the web before writing.

The system is a small **multi-agent** pipeline built with **LangChain (LCEL Runnables)** on top
of a local **Ollama** model, packaged as both a **FastAPI service** and a **CLI**, and shipped
with Docker + docker-compose.

## 2. Non-goals

- No user accounts, persistence, or scheduling.
- No direct posting to LinkedIn (output is text + image, ready to paste).
- No fine-tuning; we only prompt a general Ollama model.
- No paid/authenticated APIs. The only external call is the free, key-less Pollinations image API.

## 3. Architecture

```
                 ┌─────────────────────────────────────────────────────────┐
 topic, content? │                       PIPELINE (LCEL)                    │
────────────────►│                                                          │
                 │  1) Sufficiency judge (LLM, temp=0)                       │
                 │        │                                                  │
                 │        ▼   RunnableBranch(enough?)                        │
                 │   ┌──────────────┐        ┌──────────────────────────┐   │
                 │   │ enough=False │        │ enough=True (passthrough)│   │
                 │   │ Search agent │        └──────────────────────────┘   │
                 │   │ (Ollama +    │                    │                  │
                 │   │  DuckDuckGo) │                    │                  │
                 │   └──────┬───────┘                    │                  │
                 │          └──────────────┬─────────────┘                  │
                 │                          ▼                                │
                 │            RunnableParallel                               │
                 │        ┌───────────────┬────────────────┐                │
                 │        ▼               ▼                                  │
                 │  Content generator   Image generator                     │
                 │  (LLM, temp=0.5)     (LLM prompt + Pollinations)          │
                 │        └───────────────┴────────────────┐                │
                 │                          ▼                                │
                 │                     Assemble response                     │
                 └─────────────────────────────────────────────────────────┘
                                            │
                                            ▼
                        GenerateResponse (post + image + metadata)
```

The pipeline state is a dict threaded through the runnables:
`{"topic", "content", "sufficiency", "sources", "used_search"}`.

## 4. Agents & contracts

### 4.1 Sufficiency judge — `agents/sufficiency.py`
- **Input:** `topic: str`, `content: str | None`
- **Output:** `Sufficiency{ enough: bool, reason: str }`
- **Behavior:** If content is null/blank/very short → `enough=False` without an LLM call
  (short-circuit). Otherwise an LLM (temp=0) judges whether the content is relevant and rich
  enough to write a grounded post about the topic. Structured output via `with_structured_output`.

### 4.2 Search agent — `agents/search.py`
- **Input:** `topic`, `content` (may be null)
- **Output:** enriched `content: str` + `sources: list[str]`
- **Behavior:** `ChatOllama` (temp=0) `.bind_tools([DuckDuckGoSearchRun()])` driven by an
  `AgentExecutor` (tool-calling agent). It searches for facts about the topic, then returns a
  concise, factual research summary that becomes the new `content`. Query URLs / result snippets
  are captured as `sources`. Tool-capable model required (default `llama3.1:8b`).

### 4.3 Content generator — `agents/content.py`
- **Input:** `topic`, `content`
- **Output:** `linkedin_post: str`
- **Behavior:** LLM (temp=0.5) summarizes the content and writes a LinkedIn post: a strong hook
  line, 2–4 short paragraphs, 3–5 relevant hashtags, optional CTA. Plain text, ready to paste.

### 4.4 Image generator — `agents/image.py`
- **Input:** `topic`, `content`
- **Output:** `Image{ prompt: str, url: str | None, local_path: str | None }`
- **Behavior:** LLM (temp=0.5) writes a detailed, literal image prompt (subject, setting, style,
  composition; explicitly no text rendered in the image). The prompt is URL-encoded and fetched
  from `https://image.pollinations.ai/prompt/<prompt>`; the PNG is saved to `OUTPUT_DIR` and its
  URL returned. On network failure, returns the prompt with `url=None` (graceful degradation).

## 5. Prompt principles

Every generative prompt carries a shared system preamble:

> "You are a precise assistant. Be logical and rely only on the provided facts and the topic. Do
> not invent facts, statistics, names, or events. If you are unsure, stay general rather than
> fabricate. Creativity level: medium."

- Judge & search agent run at **temperature 0** (deterministic, factual).
- Content generator & image-prompt generator run at **temperature 0.5** (medium creativity).

## 6. Configuration (env)

| Var | Default | Meaning |
|-----|---------|---------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama endpoint (`http://ollama:11434` in compose) |
| `OLLAMA_MODEL` | `llama3.1:8b` | Tool-capable chat model |
| `GEN_TEMPERATURE` | `0.5` | Medium creativity for generators |
| `FACT_TEMPERATURE` | `0.0` | Deterministic for judge/search |
| `IMAGE_API_BASE` | `https://image.pollinations.ai/prompt` | Free image API base |
| `OUTPUT_DIR` | `./output` | Where generated PNGs are saved |
| `SEARCH_MAX_RESULTS` | `5` | Max DuckDuckGo results |
| `MIN_CONTENT_CHARS` | `200` | Below this, content is auto-insufficient |
| `REQUEST_TIMEOUT` | `60` | HTTP timeout (s) for image fetch |

## 7. Interfaces

### HTTP (FastAPI) — `api.py`
- `GET /health` → `{"status": "ok"}`
- `POST /generate` body `GenerateRequest{ topic: str, content: str | None }`
  → `GenerateResponse{ linkedin_post, image_prompt, image_url, image_path, sources,
  used_search, sufficiency_reason }`

### CLI (typer) — `cli.py`
- `post-generator --topic "..." [--content "..."] [--json]`
  prints the LinkedIn post + image info (or full JSON with `--json`).

## 8. Docker

- **Dockerfile:** `python:3.12-slim`, install `uv`, `uv sync --frozen`, run
  `uvicorn post_generator.api:app` on `:8000`.
- **docker-compose.yml:** `ollama` service (`ollama/ollama`, volume for models, healthcheck) +
  `app` service (build ., `OLLAMA_BASE_URL=http://ollama:11434`, port 8000, mounts `./output`).
- One-time model pull documented: `docker compose exec ollama ollama pull llama3.1:8b`.

## 9. Testing

Offline tests monkeypatch the LLM factory, the search agent, and the Pollinations HTTP call:
- **Sufficiency:** null/blank/short ⇒ not-enough with no LLM call.
- **Pipeline branch:** enough ⇒ search skipped; not-enough ⇒ search runs and its output reaches
  both generators; parallel generators both populate the response.
- **API:** `/health` ok; `/generate` returns the full assembled schema with a stubbed pipeline.
