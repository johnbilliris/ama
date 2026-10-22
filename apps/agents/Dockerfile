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
COPY apps/agents/pyproject.toml ./apps/agents/
COPY scripts/install_pyproject_dependencies.py ./scripts/
RUN pip install --no-cache-dir --upgrade pip && \
    python ./scripts/install_pyproject_dependencies.py ./apps/agents/pyproject.toml
COPY apps/agents/common/ ./apps/agents/common/
COPY apps/agents/dispatcher/ ./apps/agents/dispatcher/
COPY apps/agents/maf_runtime/ ./apps/agents/maf_runtime/
COPY apps/agents/monitoring/ ./apps/agents/monitoring/
COPY apps/agents/risk_assessment/ ./apps/agents/risk_assessment/
COPY apps/agents/evacuation/ ./apps/agents/evacuation/
COPY apps/agents/resource_allocation/ ./apps/agents/resource_allocation/
COPY apps/agents/communication/ ./apps/agents/communication/
COPY data/alert-templates/ ./data/alert-templates/
COPY data/road-networks/ ./data/road-networks/
COPY data/population/ ./data/population/
COPY packages/ ./packages/
RUN pip install --no-cache-dir --no-deps ./apps/agents && \
    pip check

FROM python:3.15-slim AS runtime-base

LABEL com.azure.containerizationassist.createdby="containerization-assist"

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 10001 appuser && \
    mkdir -p /app/var/evacuation-agent && \
    chown -R appuser:appuser /app/var
WORKDIR /app
COPY --from=builder /usr/local /usr/local
COPY apps/agents/common/ ./common/
COPY apps/agents/dispatcher/ ./dispatcher/
COPY apps/agents/maf_runtime/ ./maf_runtime/
COPY apps/agents/monitoring/ ./monitoring/
COPY apps/agents/risk_assessment/ ./risk_assessment/
COPY apps/agents/evacuation/ ./evacuation/
COPY apps/agents/resource_allocation/ ./resource_allocation/
COPY apps/agents/communication/ ./communication/
COPY data/alert-templates/ ./data/alert-templates/
COPY data/road-networks/ ./data/road-networks/
COPY data/population/ ./data/population/
COPY packages/ ./packages/
COPY apps/__init__.py ./apps/__init__.py
COPY apps/console_logging.py ./apps/console_logging.py
COPY apps/api/app/__init__.py ./app/__init__.py
COPY apps/api/app/validators/ ./app/validators/
COPY apps/api/app/services/simulation/ ./app/services/simulation/
COPY apps/api/app/config/ ./app/config/

ENV PYTHONPATH="/app:/app/packages/domain/src"
ENV AUDIT_BUFFER_FILE_PATH="/app/var/evacuation-agent/audit-buffer.jsonl"

RUN python -m uvicorn --version && \
    python -c "import agent_framework.observability, dispatcher.agent, evacuation.runtime; from agent_framework import Agent, InMemoryCheckpointStorage, MCPStreamableHTTPTool; from agent_framework_openai import OpenAIChatClient; from agent_framework_azure_cosmos import CosmosCheckpointStorage"

USER appuser

FROM runtime-base AS dispatcher-runtime

ENV AMA_AGENTS_RUNTIME=dispatcher
ENV PORT=8080

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 CMD curl -fsS http://localhost:8080/health/liveness || exit 1

CMD ["python", "-m", "dispatcher"]

FROM runtime-base AS evacuation-runtime

ENV AMA_AGENTS_RUNTIME=evacuation
ENV PORT=8082

EXPOSE 8082
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 CMD curl -fsS http://localhost:8082/live || exit 1

CMD ["python", "-m", "evacuation"]

FROM runtime-base AS runtime

EXPOSE 8080 8082 8084
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 CMD sh -c 'case "${AMA_AGENTS_RUNTIME:-dispatcher}" in evacuation) curl -fsS "http://localhost:${PORT:-8082}/ready" ;; dispatcher) curl -fsS "http://localhost:${PORT:-8080}/health/liveness" ;; *) curl -fsS "http://localhost:${PORT:-8080}/health" ;; esac' || exit 1

CMD ["sh", "-c", "case \"${AMA_AGENTS_RUNTIME:-dispatcher}\" in maf_runtime) exec python -m maf_runtime.workflow.builder ${MAF_INCIDENT_FIXTURE:+--incident-fixture \"$MAF_INCIDENT_FIXTURE\"} ;; communication) exec python -m communication ;; evacuation) exec python -m evacuation ;; dispatcher) exec python -m dispatcher ;; *) echo \"Unsupported AMA_AGENTS_RUNTIME: $AMA_AGENTS_RUNTIME\" >&2; exit 64 ;; esac"]
