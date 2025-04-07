# syntax=docker/dockerfile:1.9

FROM ghcr.io/astral-sh/uv:0.6.12-python3.13-bookworm-slim AS builder

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

ENV UV_PROJECT_ENVIRONMENT=/opt/venv

RUN --mount=type=cache,target=/root/.cache \
    uv sync --locked --no-dev --no-install-project

FROM python:3.13-slim AS server

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY src/ ./src

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app/src"

EXPOSE 4200

CMD ["prefect", "server", "start"]

FROM python:3.13-slim AS task

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY src/ ./src

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app/src"

CMD ["python", "-m", "foo.task"]

FROM python:3.13-slim AS api

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY src/ ./src

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app/src"

EXPOSE 8000

CMD ["uvicorn", "foo.api:app", "--host", "0.0.0.0", "--port", "8000"]