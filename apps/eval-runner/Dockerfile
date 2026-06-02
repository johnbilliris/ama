# syntax=docker/dockerfile:1.7
FROM python:3.14-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN groupadd --gid 10001 evalrunner \
 && useradd --uid 10001 --gid evalrunner --shell /usr/sbin/nologin --create-home evalrunner

WORKDIR /workspace

COPY packages/eval-core/pyproject.toml packages/eval-core/pyproject.toml
COPY packages/eval-core/src packages/eval-core/src
COPY apps/eval-runner/pyproject.toml apps/eval-runner/pyproject.toml
COPY apps/eval-runner/src apps/eval-runner/src
COPY apps/__init__.py apps/__init__.py
COPY apps/api/__init__.py apps/api/__init__.py
COPY apps/api/app/__init__.py apps/api/app/__init__.py
COPY apps/api/app/repositories/__init__.py apps/api/app/repositories/__init__.py
COPY apps/api/app/repositories/eval apps/api/app/repositories/eval

RUN pip install --upgrade pip \
 && pip install ./packages/eval-core ./apps/eval-runner

ENV PYTHONPATH="/workspace:${PYTHONPATH}"

USER evalrunner

ENTRYPOINT ["python", "-m", "ama_eval.runner"]
