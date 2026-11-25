# syntax=docker/dockerfile:1.9

FROM ghcr.io/astral-sh/uv:0.13.9-python3.13-trixie-slim AS builder

WORKDIR /app

COPY pyproject.toml uv.lock ./

ENV UV_PROJECT_ENVIRONMENT=/opt/venv

RUN --mount=type=cache,target=/root/.cache \
    uv sync --locked --no-dev --no-install-project

FROM python:3.13-slim AS runtime

# New named volumes copy the ownership of the directory they are mounted on, so
# the mount points must exist and belong to `app`. `docker compose watch` also
# needs write access to /app.
RUN useradd --create-home --uid 1000 app \
    && install -d -o app -g app /app /task-storage /home/app/.prefect

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=app:app src/ ./src

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app/src"

FROM runtime AS server

# The default is inside /opt/venv, which `app` cannot write to.
ENV PREFECT_UI_STATIC_DIRECTORY=/home/app/prefect-ui

USER app

EXPOSE 4200

CMD ["prefect", "server", "start"]

FROM runtime AS task

USER app

CMD ["python", "-m", "foo.task"]

FROM runtime AS api

USER app

EXPOSE 8000

CMD ["uvicorn", "foo.api:app", "--host", "0.0.0.0", "--port", "8000"]
