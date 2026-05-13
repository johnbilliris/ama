FROM python:3.12-slim AS builder

WORKDIR /app
COPY apps/api/pyproject.toml ./apps/api/
COPY apps/api/app/ ./apps/api/app/
COPY packages/ ./packages/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir ./packages/eval-core && \
    cd apps/api && pip install --no-cache-dir .

FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 10001 appuser
WORKDIR /app
COPY --from=builder /usr/local /usr/local
COPY apps/api/app/ ./app/
COPY packages/ ./packages/
COPY apps/__init__.py ./apps/
COPY apps/agents/__init__.py ./apps/agents/
COPY apps/agents/common/ ./apps/agents/common/
COPY apps/agents/communication/ ./apps/agents/communication/
COPY apps/agents/evacuation/ ./apps/agents/evacuation/
COPY apps/agents/help_assistant/ ./apps/agents/help_assistant/
# Spec-037 — bundle the 5 evidence-pack artefact JSON files for the read-only
# /governance/evidence-pack/* routes (FR-021). The runtime cache in Cosmos +
# immutable archive in Blob (PD-037-04) is a Step-9-deferred enhancement.
COPY docs/risk-register/ ./docs/risk-register/
COPY docs/governance-hub/adoption-roadmap/ ./docs/governance-hub/adoption-roadmap/
COPY docs/governance-hub/executive-kpi/ ./docs/governance-hub/executive-kpi/
COPY docs/governance-hub/rai-register/ ./docs/governance-hub/rai-register/
COPY specs/shared/ ./specs/shared/

ENV PYTHONPATH="/app/apps/agents:/app/packages/domain/src"

USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
