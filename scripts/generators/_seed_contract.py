"""Spec-039 T015: deterministic-seed contract for generators (FR-051, CL-8).

Resolves the 64-bit unsigned random seed for a generator according to the
documented precedence rule:

    1. Explicit ``fn_arg`` (highest)
    2. CLI ``--seed`` argument (``cli_arg``)
    3. Env var (default ``AMA_TEST_SEED``)
    4. Hard default 0 (lowest) — emits a UserWarning per CL-8.

The chosen seed is returned as a Python ``int`` in the closed interval
[0, 2**64 - 1]. Out-of-range values raise ``ValueError``.
"""

from __future__ import annotations

import os
import warnings
from typing import Final

UINT64_MAX: Final[int] = (1 << 64) - 1


def _coerce(name: str, value: object) -> int | None:
    if value is None or value == "":
        return None
    try:
        n = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name}: not an integer: {value!r}") from exc
    if n < 0 or n > UINT64_MAX:
        raise ValueError(
            f"{name}: seed {n} is outside 64-bit unsigned range [0, 2**64-1]"
        )
    return n


def resolve_seed(
    *,
    fn_arg: int | None = None,
    cli_arg: int | None = None,
    env_var_name: str = "AMA_TEST_SEED",
    default: int = 0,
    env: dict[str, str] | None = None,
) -> int:
    """Return the seed selected by the documented precedence (CL-8).

    Args:
        fn_arg: explicit programmatic seed (highest precedence).
        cli_arg: parsed ``--seed`` CLI value.
        env_var_name: environment variable name to consult.
        default: fallback when nothing else is set; using this triggers a
            ``UserWarning`` per CL-8 so non-deterministic test runs are loud.
        env: optional env mapping (for tests); defaults to ``os.environ``.
    """
    fn = _coerce("fn_arg", fn_arg)
    if fn is not None:
        return fn

    cli = _coerce("cli_arg", cli_arg)
    if cli is not None:
        return cli

    env_map = env if env is not None else os.environ
    env_val = _coerce(env_var_name, env_map.get(env_var_name))
    if env_val is not None:
        return env_val

    d = _coerce("default", default)
    if d is None:  # pragma: no cover — default of None is illegal
        raise ValueError("default seed must be an integer in 64-bit unsigned range")
    warnings.warn(
        f"resolve_seed: falling back to default seed {d}; "
        f"set --seed or {env_var_name} for reproducibility (CL-8)",
        UserWarning,
        stacklevel=2,
    )
    return d


__all__ = ["UINT64_MAX", "resolve_seed"]
