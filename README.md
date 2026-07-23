# LinkedIn Post Generator (multi-agent)

A small multi-agent system that turns a **topic** (and optional **content**) into a
ready-to-publish **LinkedIn post** plus a **generated image**.

Built with **Python + uv + LangChain (LCEL) + Ollama**. When the supplied content is missing or
insufficient, a **search agent** (Ollama bound to a DuckDuckGo tool) researches the topic first.
Two generators then run **in parallel**: a content writer and an image generator (free,
key-less [Pollinations](https://pollinations.ai) image API).

All prompts instruct the model to be **logical, fact-based, and avoid hallucination**, with
**medium creativity** (`temperature 0.5`); the judge and search steps run deterministically
(`temperature 0`).

## Flow

```
topic, content?
   -> sufficiency judge (LLM)
      -> if NOT enough: search agent (Ollama + DuckDuckGo) enriches content
      -> if enough:     pass content through
   -> parallel: [ content generator ] + [ image generator ]
   -> assembled response (post + image + sources + metadata)
```

See [`docs/spec.md`](docs/spec.md) for the full specification.

## Prerequisites

- [uv](https://docs.astral.sh/uv/)
- [Ollama](https://ollama.com/) running locally with a **tool-capable** model:
  ```bash
  ollama pull llama3.1:8b
  ```

## Setup

```bash
uv sync
cp .env.example .env   # then edit if needed
```

## Run

**CLI:**
```bash
uv run post-generator --topic "AI in healthcare"
uv run post-generator --topic "AI in healthcare" --content "..." --json
```

**HTTP API:**
```bash
uv run uvicorn post_generator.api:app --reload
# then:
curl -X POST localhost:8000/generate \
  -H 'content-type: application/json' \
  -d '{"topic":"AI in healthcare","content":null}'
```

- `GET /health` -> `{"status":"ok"}`
- `POST /generate` -> `{ linkedin_post, image_prompt, image_url, image_path, sources,
  used_search, sufficiency_reason }`

Generated images are saved under `OUTPUT_DIR` (default `./output`).

## Tests

Tests run fully offline (LLM, search and image calls are stubbed):
```bash
uv run pytest
```

## Docker

```bash
docker compose up --build
# one-time model pull into the ollama container:
docker compose exec ollama ollama pull llama3.1:8b
# the API is now on http://localhost:8000
```

The compose stack runs two services: `ollama` (model server) and `app` (this API), wired via
`OLLAMA_BASE_URL=http://ollama:11434`.

## Configuration

Environment variables (see `.env.example`): `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `GEN_TEMPERATURE`,
`FACT_TEMPERATURE`, `IMAGE_API_BASE`, `OUTPUT_DIR`, `SEARCH_MAX_RESULTS`, `MIN_CONTENT_CHARS`,
`REQUEST_TIMEOUT`.
