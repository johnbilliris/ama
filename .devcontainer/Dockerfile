# syntax=docker/dockerfile:1.7

FROM node:24-bookworm-slim AS node

FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm AS development

ARG UV_VERSION=0.11.21

LABEL com.azure.containerizationassist.createdby="containerization-assist"

ENV PATH="/opt/venv/bin:/opt/node/bin:${PATH}" \
    VIRTUAL_ENV="/opt/venv" \
    PLAYWRIGHT_BROWSERS_PATH="/opt/ms-playwright" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_CONFIG_FILE=/dev/null \
    PIP_INDEX_URL=https://packagefeedproxy.microsoft.io/pypi/simple \
    PIP_EXTRA_INDEX_URL= \
    PIP_FIND_LINKS= \
    UV_DEFAULT_INDEX=https://packagefeedproxy.microsoft.io/pypi/simple \
    UV_INDEX= \
    UV_EXTRA_INDEX_URL= \
    UV_FIND_LINKS= \
    UV_NO_CONFIG=1 \
    UV_LINK_MODE=copy \
    NPM_CONFIG_REGISTRY="https://packagefeedproxy.microsoft.io/npm/" \
    PNPM_HOME="/home/vscode/.local/share/pnpm"

COPY --from=node /usr/local /opt/node

RUN python -m pip install --no-cache-dir "uv==${UV_VERSION}" && \
    npm install --global --prefix /opt/node pnpm@10.6.3 && \
    mkdir -p /opt/venv /opt/ms-playwright /home/vscode/.cache/uv "${PNPM_HOME}" && \
    chown -R vscode:vscode /opt/venv /opt/ms-playwright /home/vscode/.cache/uv "${PNPM_HOME}"

WORKDIR /workspace

COPY --chown=vscode:vscode pyproject.toml ./
COPY --chown=vscode:vscode apps/api/pyproject.toml apps/api/pyproject.toml
COPY --chown=vscode:vscode apps/agents/pyproject.toml apps/agents/pyproject.toml
COPY --chown=vscode:vscode apps/ingestion/pyproject.toml apps/ingestion/pyproject.toml
COPY --chown=vscode:vscode apps/eval-runner/pyproject.toml apps/eval-runner/pyproject.toml
COPY --chown=vscode:vscode apps/ingest-runner/pyproject.toml apps/ingest-runner/pyproject.toml
COPY --chown=vscode:vscode packages/eval-core/pyproject.toml packages/eval-core/pyproject.toml
COPY --chown=vscode:vscode packages/eval-dataset/pyproject.toml packages/eval-dataset/pyproject.toml
COPY --chown=vscode:vscode tools/routing_mcp_server/pyproject.toml tools/routing_mcp_server/pyproject.toml
COPY --chown=vscode:vscode .devcontainer/install-python-dependencies.py .devcontainer/install-python-dependencies.py

COPY --chown=vscode:vscode package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY --chown=vscode:vscode apps/web/package.json apps/web/package.json
COPY --chown=vscode:vscode packages/domain/package.json packages/domain/package.json
COPY --chown=vscode:vscode packages/ui/package.json packages/ui/package.json

RUN chown vscode:vscode /workspace

USER vscode

RUN python -m venv "${VIRTUAL_ENV}" && \
    python .devcontainer/install-python-dependencies.py \
      --python "${VIRTUAL_ENV}/bin/python" \
      --mode dependencies

RUN pnpm install --frozen-lockfile && \
    pnpm --filter @ama/web exec playwright install chromium

USER root

RUN rm -f /etc/apt/sources.list.d/yarn.list && \
    pnpm --filter @ama/web exec playwright install-deps chromium

RUN printf '%s\n' 'export PATH="/opt/venv/bin:/opt/node/bin:$PATH"' > /etc/profile.d/ama-toolchain.sh && \
    mkdir -p /workspace/apps/web/.next && \
    chown vscode:vscode /workspace/apps/web/.next

USER vscode

CMD ["sleep", "infinity"]
