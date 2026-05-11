"""Cycle 3 / T-AA31 / FR-073 — unit tests for the KQL canonicaliser.

Validates each step of the six-step pipeline in
``tests/contract/_kql_canonicaliser.py`` independently, then idempotence
and a 10× determinism rerun.
"""

from __future__ import annotations

import pytest

from tests.contract._kql_canonicaliser import (
    _canonicalise_kql_string,
    canonicalise_kql,
)

# --------------------------------------------------------------------------
# Step 1 — strip line + block comments
# --------------------------------------------------------------------------


def test_step_1_strips_line_and_block_comments() -> None:
    raw = """
    AppMetrics
    | where TimeGenerated >= ago(7d) // last week's window
    /* block comment
       across lines */
    | summarize p99 = percentile(latency_ms, 99) by sub_agent
    """
    result = canonicalise_kql(raw)
    assert "//" not in result
    assert "/*" not in result and "*/" not in result
    # The semantic content survives.
    assert "AppMetrics" in result
    assert "summarize" in result
    assert "percentile(latency_ms, 99)" in result


# --------------------------------------------------------------------------
# Step 2 — whitespace collapse with newline-before-pipe
# --------------------------------------------------------------------------


def test_step_2_collapses_whitespace_and_preserves_pipe_newline() -> None:
    raw = "AppMetrics    |   where    a == b   |   project a"
    result = canonicalise_kql(raw)
    # Each pipe is on its own line.
    pipes_on_newline = [ln for ln in result.split("\n") if ln.lstrip().startswith("|")]
    assert len(pipes_on_newline) == 2, (
        f"expected 2 pipe-prefixed clause lines, got {pipes_on_newline!r}"
    )
    # No double-space runs survive within a clause.
    assert "  " not in result


def test_step_2_no_trailing_or_leading_whitespace() -> None:
    raw = "   AppMetrics | where a == b   "
    result = canonicalise_kql(raw)
    assert result == result.strip()


# --------------------------------------------------------------------------
# Step 3 — lowercase Kusto reserved keywords
# --------------------------------------------------------------------------


def test_step_3_lowercases_reserved_keywords() -> None:
    raw = "AppMetrics | WHERE x == 1 | SUMMARIZE p99 = percentile(y, 99) BY sub_agent"
    result = canonicalise_kql(raw)
    assert "WHERE" not in result
    assert "SUMMARIZE" not in result
    assert " BY " not in result and "BY sub_agent" not in result
    assert "where" in result
    assert "summarize" in result
    assert "by sub_agent" in result


def test_step_3_does_not_lowercase_identifiers() -> None:
    # An identifier whose name happens to start with a keyword prefix should
    # not be lowercased (e.g. ``WhereClause`` is a hypothetical column).
    raw = "AppMetrics | extend WhereClause = 1"
    result = canonicalise_kql(raw)
    # ``WhereClause`` survives — only the standalone keyword `WHERE` would
    # be lowered. Note ``extend`` IS a keyword and IS lowered.
    assert "WhereClause" in result
    assert "extend WhereClause" in result


# --------------------------------------------------------------------------
# Step 4 — sort by-clause column lists lexicographically
# --------------------------------------------------------------------------


def test_step_4_sorts_by_clause_columns() -> None:
    raw = "AppMetrics | summarize p99 = percentile(x, 99) by model_deployment, sub_agent"
    result = canonicalise_kql(raw)
    # Expect alphabetical: model_deployment < sub_agent (m < s).
    assert "by model_deployment, sub_agent" in result

    raw_reordered = "AppMetrics | summarize p99 = percentile(x, 99) by sub_agent, model_deployment"
    result_reordered = canonicalise_kql(raw_reordered)
    assert result == result_reordered, (
        "canonicalisation must produce identical bytes regardless of input by-clause order"
    )


# --------------------------------------------------------------------------
# Step 5 — sort summarize alias-expression list by alias lex
# --------------------------------------------------------------------------


def test_step_5_sorts_summarize_aliases() -> None:
    raw = (
        "AppMetrics | summarize p99 = percentile(x, 99), avg_x = avg(x), "
        "p50 = percentile(x, 50) by sub_agent"
    )
    result = canonicalise_kql(raw)
    # Aliases sorted: avg_x < p50 < p99 (a < p, then numeric).
    assert (
        "summarize avg_x = avg(x), p50 = percentile(x, 50), p99 = percentile(x, 99) by sub_agent"
        in result
    )


def test_step_5_summarize_sort_is_stable_across_input_orderings() -> None:
    # All three permutations should canonicalise to the same string.
    raws = [
        "T | summarize a = f(x), b = g(y), c = h(z)",
        "T | summarize c = h(z), a = f(x), b = g(y)",
        "T | summarize b = g(y), a = f(x), c = h(z)",
    ]
    canonicals = {canonicalise_kql(r) for r in raws}
    assert len(canonicals) == 1, f"expected 1 canonical form, got {canonicals!r}"


# --------------------------------------------------------------------------
# Step 6 — strip redundant outer parentheses on extend target exprs
# --------------------------------------------------------------------------


def test_step_6_strips_redundant_extend_parens() -> None:
    raw = "T | extend latency = (server_emit_ms - client_received_ms)"
    result = canonicalise_kql(raw)
    assert "extend latency = server_emit_ms - client_received_ms" in result
    assert "(server_emit_ms" not in result


def test_step_6_preserves_function_call_parens() -> None:
    # The extend rhs is an inner function call, not a redundant outer paren —
    # the parens belong to the function call and must NOT be stripped.
    raw = "T | extend p = percentile(x, 99)"
    result = canonicalise_kql(raw)
    assert "extend p = percentile(x, 99)" in result


# --------------------------------------------------------------------------
# Idempotence — applying the canonicaliser twice yields the same bytes
# --------------------------------------------------------------------------


def test_canonicalise_kql_is_idempotent() -> None:
    raw = """
    AppMetrics
    /* descriptive comment */
    | where TimeGenerated >= ago(7d) // weekly window
    | summarize p99 = percentile(latency_ms, 99), avg_lat = avg(latency_ms)
                by model_deployment, sub_agent
    | extend gap = (p99 - avg_lat)
    """
    once = canonicalise_kql(raw)
    twice = canonicalise_kql(once)
    assert once == twice, (
        "canonicalise_kql must be idempotent (PD-C3-01 invariant)"
    )


# --------------------------------------------------------------------------
# Determinism — 10× same input → same byte-sequence
# --------------------------------------------------------------------------


def test_canonicalise_kql_is_deterministic_across_10_runs() -> None:
    raw = (
        "T | where x == 1 | summarize "
        "z = sum(z), a = avg(a), m = max(m) "
        "by gamma, alpha, beta"
    )
    results = {canonicalise_kql(raw) for _ in range(10)}
    assert len(results) == 1, (
        f"canonicalise_kql must be deterministic; got {len(results)} distinct results"
    )


# --------------------------------------------------------------------------
# Type validation
# --------------------------------------------------------------------------


def test_canonicalise_kql_rejects_non_string() -> None:
    with pytest.raises(TypeError):
        canonicalise_kql(123)  # type: ignore[arg-type]


def test_internal_helper_accepts_string_only() -> None:
    # `_canonicalise_kql_string` is a module-private helper — exercise it
    # to ensure each step composes without raising.
    raw = "T | where x == 1"
    assert _canonicalise_kql_string(raw) == "T\n| where x == 1"
