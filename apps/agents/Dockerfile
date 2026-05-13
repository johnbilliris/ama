FROM python:3.12-slim AS builder

WORKDIR /app
COPY apps/agents/pyproject.toml ./apps/agents/
COPY apps/agents/common/ ./apps/agents/common/
COPY apps/agents/dispatcher/ ./apps/agents/dispatcher/
COPY apps/agents/monitoring/ ./apps/agents/monitoring/
COPY apps/agents/risk_assessment/ ./apps/agents/risk_assessment/
COPY apps/agents/evacuation/ ./apps/agents/evacuation/
COPY apps/agents/resource_allocation/ ./apps/agents/resource_allocation/
COPY apps/agents/communication/ ./apps/agents/communication/
COPY packages/ ./packages/
RUN pip install --no-cache-dir --upgrade pip && \
    cd apps/agents && pip install --no-cache-dir .

FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 10001 appuser
WORKDIR /app
COPY --from=builder /usr/local /usr/local
COPY apps/agents/common/ ./common/
COPY apps/agents/dispatcher/ ./dispatcher/
COPY apps/agents/monitoring/ ./monitoring/
COPY apps/agents/risk_assessment/ ./risk_assessment/
COPY apps/agents/evacuation/ ./evacuation/
COPY apps/agents/resource_allocation/ ./resource_allocation/
COPY apps/agents/communication/ ./communication/
COPY packages/ ./packages/
COPY apps/api/app/__init__.py ./app/__init__.py
COPY apps/api/app/validators/ ./app/validators/
COPY apps/api/app/services/simulation/ ./app/services/simulation/
COPY apps/api/app/config/ ./app/config/

ENV PYTHONPATH="/app:/app/packages/domain/src:${PYTHONPATH}"

USER appuser
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 CMD curl -f http://localhost:8080/health || exit 1

CMD ["python", "-m", "dispatcher"]
