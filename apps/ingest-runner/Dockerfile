# Spec 036 — corpus ingest Container Apps Job (FR-RAG-IDX-01..05; R-08).
# Scaffolded by T002. Used by infra/main.bicep Container Apps Job wiring (T050)
# and the corpus-ingest workflow (T053).
FROM python:3.13-slim AS base

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Use uv for fast deterministic installs (matches rest of monorepo).
RUN pip install --no-cache-dir uv==0.5.14

COPY pyproject.toml /app/
COPY src /app/src
RUN uv pip install --system --no-cache .

# Default entrypoint — overridden by Container Apps Job spec; explicit form for
# `docker run ama-ingest-runner --dry-run` smoke tests.
ENTRYPOINT ["python", "-m", "ama_ingest"]
CMD ["--incremental"]
