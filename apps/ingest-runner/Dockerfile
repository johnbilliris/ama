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

ARG INGEST_BUILD_TAG=2026-05-10-v4-direct-copy

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN pip install --no-cache-dir uv==0.5.14

COPY apps/ingest-runner/pyproject.toml /app/
COPY apps/ingest-runner/src /app/src
# Install dependencies-only via uv (do NOT install our own package — we'll
# expose it via PYTHONPATH so source edits land deterministically and we
# bypass any layer/wheel cache mismatch.).
RUN echo "build_tag=${INGEST_BUILD_TAG}" > /app/.build-tag && \
    uv pip install --system --no-cache --force-reinstall \
      "azure-identity>=1.19,<2" \
      "azure-search-documents>=11.5.2,<12" \
      "azure-storage-blob>=12.24,<13" \
      "azure-servicebus>=7.13,<8" \
      "azure-monitor-opentelemetry>=1.6,<2" \
      "azure-ai-inference>=1.0.0b9" \
      "azure-core>=1.30,<2" \
      "openai>=1.59.0" \
      "pydantic>=2.10,<3" \
      "pyyaml>=6.0,<7" \
      "tenacity>=9.0,<10" \
      "tiktoken>=0.8,<1" \
      "cryptography>=46.0,<47"

# Verify our source actually made it (debug aid for ACR cache issues).
RUN echo "=== SRC LISTING ===" && ls -la /app/src/ama_ingest/ && \
    echo "=== live_clients.py SHA ===" && sha256sum /app/src/ama_ingest/live_clients.py && \
    echo "=== safe_key/VERSION lines ===" && grep -n -E "safe_key|LIVE_CLIENTS_VERSION|BATCH_SIZE" /app/src/ama_ingest/live_clients.py | head -10

ENV PYTHONPATH=/app/src

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
