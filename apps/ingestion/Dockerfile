FROM python:3.14-slim AS builder

WORKDIR /app
COPY apps/ingestion/pyproject.toml ./apps/ingestion/
COPY apps/ingestion/ ./apps/ingestion/
COPY packages/ ./packages/
COPY apps/api/app/services/ingestion/ ./apps/api/app/services/ingestion/
COPY apps/api/app/repositories/ ./apps/api/app/repositories/
COPY apps/api/app/core/ ./apps/api/app/core/
COPY apps/api/app/services/state_store.py ./apps/api/app/services/state_store.py
COPY apps/api/app/validators/ ./apps/api/app/validators/
RUN pip install --no-cache-dir --upgrade pip && \
    cd apps/ingestion && pip install --no-cache-dir .

FROM python:3.14-slim AS runtime

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 10001 appuser
WORKDIR /app
COPY --from=builder /usr/local /usr/local
COPY apps/ingestion/ ./apps/ingestion/
COPY packages/ ./packages/
COPY apps/api/app/services/ingestion/ ./apps/api/app/services/ingestion/
COPY apps/api/app/repositories/ ./apps/api/app/repositories/
COPY apps/api/app/core/ ./apps/api/app/core/
COPY apps/api/app/services/state_store.py ./apps/api/app/services/state_store.py
COPY apps/api/app/validators/ ./apps/api/app/validators/

USER appuser
EXPOSE 8081
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 CMD curl -f http://localhost:8081/health || exit 1

CMD ["python", "-m", "apps.ingestion.worker"]
