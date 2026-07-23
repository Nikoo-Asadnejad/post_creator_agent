# syntax=docker/dockerfile:1
FROM python:3.12-slim

# uv (copied from the official image)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (better layer caching).
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH" \
    OUTPUT_DIR=/app/output

EXPOSE 8000

CMD ["uvicorn", "post_generator.api:app", "--host", "0.0.0.0", "--port", "8000"]
