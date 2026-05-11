"""Spec-039 T015: tests for resolve_seed() precedence (CL-8, FR-051)."""

from __future__ import annotations

import warnings

import pytest

from scripts.generators._seed_contract import UINT64_MAX, resolve_seed


def test_fn_arg_wins_over_all():
    assert (
        resolve_seed(fn_arg=10, cli_arg=20, env={"AMA_TEST_SEED": "30"}, default=40)
        == 10
    )


def test_cli_arg_wins_over_env_and_default():
    assert resolve_seed(cli_arg=20, env={"AMA_TEST_SEED": "30"}, default=40) == 20


def test_env_wins_over_default():
    assert resolve_seed(env={"AMA_TEST_SEED": "30"}, default=40) == 30


def test_default_used_when_nothing_else():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        assert resolve_seed(env={}, default=7) == 7
    assert any(issubclass(w.category, UserWarning) for w in caught)


def test_default_zero_warns_by_default():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        assert resolve_seed(env={}) == 0
    assert any("default seed 0" in str(w.message) for w in caught)


def test_env_var_name_is_configurable():
    assert resolve_seed(env={"X": "5", "AMA_TEST_SEED": "9"}, env_var_name="X") == 5


def test_overflow_rejected():
    with pytest.raises(ValueError):
        resolve_seed(fn_arg=UINT64_MAX + 1)


def test_negative_rejected():
    with pytest.raises(ValueError):
        resolve_seed(fn_arg=-1)


def test_non_integer_rejected():
    with pytest.raises(ValueError):
        resolve_seed(env={"AMA_TEST_SEED": "not-a-number"})
