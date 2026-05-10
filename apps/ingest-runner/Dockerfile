# Spec 036 — corpus ingest Container Apps Job (FR-RAG-IDX-01..05; R-08).
# Scaffolded by T002. Used by infra/main.bicep Container Apps Job wiring (T050)
# and the corpus-ingest workflow (T053).
#
# Build context **must be the repository root** (not apps/ingest-runner/) so that
# COPY can pick up:
#   - apps/ingest-runner/pyproject.toml + src (the runner package)
#   - docs/corpus/                            (FR-RAG-IDX-01 source-of-truth)
#   - infra/parameters/foundry-carveout.yaml  (FR-RAG-CV-01 fail-closed registry)
#
# Build command:
#   az acr build --registry <acr> --image ama/ingest-runner:<tag> \
#     --file apps/ingest-runner/Dockerfile .
FROM python:3.13-slim AS base

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Use uv for fast deterministic installs (matches rest of monorepo).
RUN pip install --no-cache-dir uv==0.5.14

COPY apps/ingest-runner/pyproject.toml /app/
COPY apps/ingest-runner/src /app/src
RUN uv pip install --system --no-cache .

# FR-RAG-IDX-01 — bake the corpus into the image so the runner has a known
# tree to walk (rebuild image when corpus changes; ``corpus_build_sha``
# captured by the runner is the git ls-tree hash of docs/corpus/).
COPY docs/corpus /app/docs/corpus

# FR-RAG-CV-01 — bake the carve-out registry alongside so preflight can read it.
COPY infra/parameters/foundry-carveout.yaml /app/infra/parameters/foundry-carveout.yaml

# Default entrypoint — overridden by Container Apps Job spec; explicit form for
# `docker run ama-ingest-runner --dry-run` smoke tests.
ENTRYPOINT ["python", "-m", "ama_ingest"]
CMD ["--incremental"]
