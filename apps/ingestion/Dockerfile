FROM python:3.12-slim AS builder
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
COPY pyproject.toml ./pyproject.toml
COPY apps/ingestion/pyproject.toml ./apps/ingestion/
COPY apps/ingestion/ ./apps/ingestion/
COPY apps/api/pyproject.toml ./apps/api/
COPY apps/api/app/ ./apps/api/app/
COPY apps/agents/ ./apps/agents/
COPY apps/__init__.py ./apps/__init__.py
COPY apps/console_logging.py ./apps/console_logging.py
COPY packages/ ./packages/
RUN pip install --no-cache-dir --upgrade pip "uv==0.11.21" && \
    python -c "import tomllib; from pathlib import Path; overrides=tomllib.loads(Path('pyproject.toml').read_text())['tool']['uv']['override-dependencies']; Path('/tmp/uv-overrides.txt').write_text('\n'.join(overrides) + '\n')" && \
    uv --no-config pip install --system --no-cache \
      --default-index "$UV_DEFAULT_INDEX" \
      --overrides /tmp/uv-overrides.txt \
      ./packages/eval-core ./apps/api ./apps/ingestion && \
    pip uninstall --yes uv && \
    rm /tmp/uv-overrides.txt

FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:/app/apps/api:/app/apps/agents

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 10001 appuser
WORKDIR /app
COPY --from=builder /usr/local /usr/local
COPY apps/ingestion/ ./apps/ingestion/
COPY apps/agents/ ./apps/agents/
COPY packages/ ./packages/
COPY apps/api/app/ ./apps/api/app/

USER appuser
EXPOSE 8081
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 CMD curl -f http://localhost:8081/health || exit 1

CMD ["python", "-m", "apps.ingestion.worker"]
