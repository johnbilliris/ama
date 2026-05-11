"""Unit tests for the activation-mutex lifespan invariant (spec-035 T014)."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi import FastAPI


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.delenv("ACTIVATION_SIMULATION", raising=False)
    monkeypatch.delenv("ACTIVATION_PRODUCTION", raising=False)
    yield


def test_no_guards_ok():
    from app.middleware.activation_mutex import assert_activation_mutex

    assert_activation_mutex()


@pytest.mark.parametrize("var", ["ACTIVATION_SIMULATION", "ACTIVATION_PRODUCTION"])
def test_single_guard_ok(monkeypatch: pytest.MonkeyPatch, var: str):
    from app.middleware.activation_mutex import assert_activation_mutex

    monkeypatch.setenv(var, "1")
    assert_activation_mutex()


@pytest.mark.parametrize(
    ("sim", "prod"),
    [("1", "1"), ("true", "TRUE"), ("yes", "on"), ("y", "true")],
)
def test_both_guards_raise(monkeypatch: pytest.MonkeyPatch, sim: str, prod: str):
    from app.middleware.activation_mutex import (
        ActivationMutexViolation,
        assert_activation_mutex,
    )

    monkeypatch.setenv("ACTIVATION_SIMULATION", sim)
    monkeypatch.setenv("ACTIVATION_PRODUCTION", prod)
    with pytest.raises(ActivationMutexViolation):
        assert_activation_mutex()


def test_falsy_values_are_ignored(monkeypatch: pytest.MonkeyPatch):
    from app.middleware.activation_mutex import assert_activation_mutex

    monkeypatch.setenv("ACTIVATION_SIMULATION", "0")
    monkeypatch.setenv("ACTIVATION_PRODUCTION", "false")
    assert_activation_mutex()


@pytest.mark.asyncio
async def test_lifespan_yields_when_clean():
    from app.middleware.activation_mutex import activation_mutex_lifespan

    app = FastAPI()
    async with activation_mutex_lifespan(app):
        assert True


@pytest.mark.asyncio
async def test_lifespan_raises_when_both_guards_set(monkeypatch: pytest.MonkeyPatch):
    from app.middleware.activation_mutex import (
        ActivationMutexViolation,
        activation_mutex_lifespan,
    )

    monkeypatch.setenv("ACTIVATION_SIMULATION", "true")
    monkeypatch.setenv("ACTIVATION_PRODUCTION", "true")
    app = FastAPI()
    with pytest.raises(ActivationMutexViolation):
        async with activation_mutex_lifespan(app):
            pass
