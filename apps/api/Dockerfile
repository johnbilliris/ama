FROM python:3.15-slim AS builder
ENV PIP_CONFIG_FILE=/dev/null \
    PIP_INDEX_URL=https://packagefeedproxy.microsoft.io/pypi/simple \
    PIP_EXTRA_INDEX_URL= \
    PIP_FIND_LINKS= \
    UV_DEFAULT_INDEX=https://packagefeedproxy.microsoft.io/pypi/simple \
    UV_INDEX= \
    UV_EXTRA_INDEX_URL= \
    UV_FIND_LINKS= \
    UV_NO_CONFIG=1

WORKDIR /app
COPY apps/api/pyproject.toml ./apps/api/
COPY scripts/install_pyproject_dependencies.py ./scripts/
RUN pip install --no-cache-dir --upgrade pip && \
    python ./scripts/install_pyproject_dependencies.py ./apps/api/pyproject.toml
COPY packages/eval-core/ ./packages/eval-core/
RUN pip install --no-cache-dir ./packages/eval-core
COPY apps/api/app/ ./apps/api/app/
COPY packages/ ./packages/
RUN pip install --no-cache-dir --no-deps ./apps/api

FROM python:3.15-slim AS runtime

LABEL com.azure.containerizationassist.createdby="containerization-assist"

ENV PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/* && \
    useradd -m -u 10001 appuser
WORKDIR /app
COPY --from=builder /usr/local /usr/local
COPY apps/api/app/ ./apps/api/app/
COPY packages/ ./packages/
COPY apps/__init__.py ./apps/
COPY apps/agents/ ./apps/agents/
COPY apps/ingestion/ ./apps/ingestion/
COPY apps/console_logging.py ./apps/console_logging.py
COPY scripts/seed_loader.py ./scripts/seed_loader.py
COPY scripts/_pii_detector.py ./scripts/_pii_detector.py
COPY apps/web/src/content/help/ ./apps/web/src/content/help/
# Spec-037 — bundle the 5 evidence-pack artefact JSON files for the read-only
# /governance/evidence-pack/* routes (FR-021). The runtime cache in Cosmos +
# immutable archive in Blob (PD-037-04) is a Step-9-deferred enhancement.
COPY docs/risk-register/ ./docs/risk-register/
COPY docs/governance-hub/adoption-roadmap/ ./docs/governance-hub/adoption-roadmap/
COPY docs/governance-hub/executive-kpi/ ./docs/governance-hub/executive-kpi/
COPY docs/governance-hub/rai-register/ ./docs/governance-hub/rai-register/
COPY specs/shared/ ./specs/shared/

ENV PYTHONPATH="/app/apps/api:/app/apps/agents:/app/packages/domain/src:/app"

RUN python -m uvicorn --version && \
    AMA_ENVIRONMENT=dev python -c "import app.main"

USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 CMD curl -f http://localhost:8000/api/health/liveness || exit 1

CMD ["uvicorn", "app.main:app", "--app-dir", "/app/apps/api", "--host", "0.0.0.0", "--port", "8000"]
