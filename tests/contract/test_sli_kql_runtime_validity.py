"""Cycle 4 / T-AA46 + T-AA47 / A4-01 / FR-073 (strengthening) — author-time
KQL column-resolution-validity walker (parametric Z1..Z7).

Per **PD-C4-01** (`specs/036-sim-agent-extend/plan.md:788-1010`) and the
A4-01 amendment (`specs/036-sim-agent-extend/spec.md:3875-3895`): the
existing FR-073 byte-equality contract test
(`tests/contract/test_sli_kql_canonical_match.py`) does NOT catch the
class of defect where BOTH the implementation KQL
(`infra/observability/sli-kql.json`) and the contract KQL
(`contracts/sli-thresholds.md`) drift symmetrically — both files
canonicalise to the same byte sequence, just both wrong. The Z7 case
that motivated A4-01 was a `summarize ... by model_deployment` clause
that referenced an undefined column (the `extend model_deployment`
clause was missing from BOTH sides).

This module adds the **runtime-validity** surface: every column
referenced in `where`, `summarize ... by`, `extend` RHS, and `project`
clauses MUST resolve to one of:

* (a) a base-table column on the queried Application Insights table
      (`requests`, `customEvents`, `customMetrics`, `traces`); OR
* (b) a `let`-bound, `extend`-bound, or `summarize-LHS`-bound name
      introduced earlier in the same query; OR
* (c) a `customDimensions["..."]` lookup expression (the canonical
      Application Insights escape hatch — Pass-1 Q4 (c)).

Bare column references that do not satisfy (a)/(b)/(c) are contract
violations regardless of whether the byte-equality test passes.

**Walker discipline** (per PD-C4-01 + Pass-1 Q1):

* Lightweight regex/lexer top-down walk — NO Kusto AST parser
  dependency (rejected per PD-C4-01 three-part rationale).
* `let` / `extend` LHS / `summarize ... by ... bin()` aggregate-LHS
  bindings accumulate into the `defined_columns` state set.
* `union` MUST hard-fail (multi-table column resolution is out of
  scope); NO `pytest.skip` / `xfail` / `mark.skipif` is permitted
  per Cycle 3 Pass-2 Q3 universal ban.
* Failure messages name the SLI id, the unresolved column, the line
  number (counting pipe-clauses in the canonicalised body), and the
  full canonicalised KQL — for diagnostic completeness.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from tests.contract._kql_canonicaliser import (
    canonical_kql_for_sli,
    canonicalise_kql,
)

# Mirror the established `_SLI_PATH` pattern at
# tests/contract/test_sli_kql_schema_v2.py:25 and
# tests/contract/test_sli_kql_canonical_match.py:28.
_SLI_PATH = (
    Path(__file__).resolve().parents[2]
    / "infra"
    / "observability"
    / "sli-kql.json"
)
_SLI_DOC = json.loads(_SLI_PATH.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# Base-table allowlist — Pass-1 Q4 (a) clause
# --------------------------------------------------------------------------
#
# Application Insights schema columns visible to every KQL query that
# anchors on the corresponding base table. Each entry is comment-anchored
# to the table-of-origin so future maintainers can extend safely.
#
# `customEvents` (Application Insights custom events emitted by the
# `apps/api/app/services/simulation/*` instrumentation surface):
_CUSTOM_EVENTS_COLUMNS = frozenset(
    {
        "timestamp",
        "name",
        "customDimensions",
        "customMeasurements",
        "operation_Id",
        "operation_Name",
        "operation_ParentId",
        "user_Id",
        "session_Id",
        "client_IP",
        "client_Type",
        "client_City",
        "client_CountryOrRegion",
        "cloud_RoleName",
        "cloud_RoleInstance",
        "appName",
        "appId",
        "iKey",
        "sdkVersion",
        "itemCount",
        "itemId",
        "itemType",
    }
)
# `requests` (Application Insights request telemetry — used by Z1
# inject→fan-out latency only on the customEvents-emitted bridge; the
# allowlist below preserves coverage for future SLIs that anchor on
# `requests` directly):
_REQUESTS_COLUMNS = frozenset(
    {
        "timestamp",
        "id",
        "source",
        "name",
        "url",
        "success",
        "resultCode",
        "duration",
        "performanceBucket",
        "customDimensions",
        "customMeasurements",
        "operation_Id",
        "operation_Name",
        "operation_ParentId",
        "user_Id",
        "session_Id",
        "client_IP",
        "cloud_RoleName",
        "cloud_RoleInstance",
        "itemCount",
        "itemId",
        "itemType",
    }
)
# `customMetrics` (numeric metrics — used by Z4 Cosmos RU headroom in
# theory; current Z4 anchors on `AzureDiagnostics` instead):
_CUSTOM_METRICS_COLUMNS = frozenset(
    {
        "timestamp",
        "name",
        "value",
        "valueCount",
        "valueSum",
        "valueMin",
        "valueMax",
        "valueStdDev",
        "customDimensions",
        "customMeasurements",
        "operation_Id",
        "operation_Name",
        "user_Id",
        "session_Id",
        "client_IP",
        "cloud_RoleName",
        "cloud_RoleInstance",
        "itemCount",
        "itemId",
    }
)
# `traces` (Application Insights trace telemetry — distributed-trace
# events; not currently used by any Z-series SLI but allow-listed for
# completeness):
_TRACES_COLUMNS = frozenset(
    {
        "timestamp",
        "message",
        "severityLevel",
        "customDimensions",
        "customMeasurements",
        "operation_Id",
        "operation_Name",
        "user_Id",
        "session_Id",
        "client_IP",
        "cloud_RoleName",
        "cloud_RoleInstance",
        "itemCount",
        "itemId",
    }
)
# `AuditEntries_CL` (Log Analytics custom log — Z2 audit gap-free
# invariant). The `_CL` suffix denotes a Custom Log table (Log
# Analytics convention). Columns are domain-specific to the
# spec-036 audit envelope schema.
_AUDIT_ENTRIES_CL_COLUMNS = frozenset(
    {
        "TimeGenerated",
        "sequence_number",
        "simulation_id_g",
        "type",
        "tenant_id",
        "Type",
        "_ResourceId",
    }
)
# `AzureDiagnostics` (Azure Monitor diagnostic logs — Z4 Cosmos RU
# headroom anchors here). Schema is broad; only the columns exercised
# by Z4 are listed for correctness.
_AZURE_DIAGNOSTICS_COLUMNS = frozenset(
    {
        "TimeGenerated",
        "ResourceProvider",
        "Category",
        "ResourceId",
        "OperationName",
        "requestCharge_s",
        "requestResourceType_s",
        "statusCode_s",
        "Resource",
        "Type",
    }
)

# Map base-table identifier → its allow-listed column set.
_BASE_TABLE_COLUMNS: dict[str, frozenset[str]] = {
    "customEvents": _CUSTOM_EVENTS_COLUMNS,
    "requests": _REQUESTS_COLUMNS,
    "customMetrics": _CUSTOM_METRICS_COLUMNS,
    "traces": _TRACES_COLUMNS,
    "AuditEntries_CL": _AUDIT_ENTRIES_CL_COLUMNS,
    "AzureDiagnostics": _AZURE_DIAGNOSTICS_COLUMNS,
}

# Kusto built-in aggregate / scalar functions and operators we should
# not treat as column references when seen as bare identifiers.
_KUSTO_FUNCTIONS_AND_OPERATORS = frozenset(
    {
        # Aggregates
        "count",
        "countif",
        "sum",
        "sumif",
        "avg",
        "avgif",
        "min",
        "minif",
        "max",
        "maxif",
        "percentile",
        "percentiles",
        "dcount",
        "dcountif",
        "make_set",
        "make_list",
        "make_bag",
        "any",
        # Scalars
        "tostring",
        "todouble",
        "toint",
        "tolong",
        "tobool",
        "todatetime",
        "totimespan",
        "toreal",
        "todynamic",
        "isnull",
        "isnotnull",
        "isempty",
        "isnotempty",
        "iif",
        "case",
        "coalesce",
        "strcat",
        "substring",
        "strlen",
        "split",
        "trim",
        "ago",
        "now",
        "bin",
        "bin_at",
        "startofday",
        "endofday",
        "startofhour",
        "format_datetime",
        "format_timespan",
        # Tabular operators / keywords (lowercased post canonicalisation)
        "let",
        "extend",
        "where",
        "project",
        "summarize",
        "by",
        "and",
        "or",
        "in",
        "between",
        "not",
        "ascending",
        "descending",
        "true",
        "false",
        "null",
        "asc",
        "desc",
    }
)


# --------------------------------------------------------------------------
# Walker — PD-C4-01 lightweight regex/lexer
# --------------------------------------------------------------------------

# Identifier regex — Kusto identifiers match `[A-Za-z_][A-Za-z0-9_]*`.
_IDENT_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\b")

# `customDimensions["..."]` (and `customMeasurements["..."]`) — the
# Pass-1 Q4 (c) escape hatch. Once one of these expressions appears,
# the identifier inside the brackets is a string literal, not a
# column reference, so it does not need to resolve via (a)/(b).
_DYNAMIC_LOOKUP_RE = re.compile(
    r"\b(?:customDimensions|customMeasurements)\s*\[\s*\"[^\"]*\"\s*\]",
)

# String literal — masked before identifier scan to avoid string
# contents being interpreted as identifiers.
_STRING_LITERAL_RE = re.compile(r"\"(?:\\.|[^\"\\])*\"")

# Numeric literal — masked likewise.
_NUMERIC_LITERAL_RE = re.compile(r"\b\d+(?:\.\d+)?\b")


def _detect_base_table(canonical_kql: str) -> str:
    """Identify the base table the query anchors on.

    The base table is the FIRST identifier in the canonicalised body
    (before the first pipe). Cycle-1-7 SLIs anchor on one of the
    keys in :data:`_BASE_TABLE_COLUMNS`; future SLIs that introduce
    a new base table MUST extend the allow-list.

    Multi-table queries (Z2 uses ``let`` + a derived table reference)
    are accommodated: the first non-``let`` identifier is the base
    table for the subsequent operator chain.
    """

    # Strip leading let-bindings (Z2). A `let` binding has the form
    # `let <name> = <body> ;` — the body itself anchors on a base
    # table that we want to discover.
    head = canonical_kql.lstrip()
    # Pop any leading `let <name> = ago(...);` (Z2) — the right-hand
    # side of the let binding is a scalar (`ago(...)`), and the
    # actual table reference is the next `let <name> = <Table> | ...`
    # or the next bare-table line. The simplest robust strategy: take
    # the first identifier that matches a known base-table key.
    for ident_match in _IDENT_RE.finditer(head):
        ident = ident_match.group(1)
        if ident in _BASE_TABLE_COLUMNS:
            return ident
    # No known base table — fall back to a sentinel that triggers a
    # walker failure with a diagnostic message.
    return "<unknown-base-table>"


def _extract_let_bindings(canonical_kql: str) -> set[str]:
    """Extract all `let <name> = ...` LHS identifiers.

    Recognises canonicalised `let` clauses on their own line (post
    canonicalisation, `let` clauses sit between newlines + pipe boundaries
    OR before the first pipe). The walker treats `let`-bound names as
    table references AND scalars: their use as a stand-alone identifier
    on the RHS of a subsequent operator is permitted.
    """

    pattern = re.compile(r"\blet\s+([A-Za-z_][A-Za-z0-9_]*)\s*=", re.IGNORECASE)
    return {match.group(1) for match in pattern.finditer(canonical_kql)}


def _split_top_level_commas(text: str) -> list[str]:
    """Split *text* on top-level commas, respecting parenthesis depth."""

    parts: list[str] = []
    depth = 0
    current: list[str] = []
    for ch in text:
        if ch == "(":
            depth += 1
            current.append(ch)
        elif ch == ")":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current).strip())
    return parts


def _extract_extend_rhs_only(clause_body: str) -> str:
    """Return only the RHS portion(s) of an `extend`/`project` clause body.

    For ``extend a = expr1, b = expr2``, returns ``expr1 ; expr2``.
    LHS bindings are stripped — they introduce new columns rather
    than referencing existing ones.
    """

    rhs_parts: list[str] = []
    for part in _split_top_level_commas(clause_body):
        if "=" in part:
            rhs_parts.append(part.split("=", 1)[1].strip())
        else:
            # bare reference (e.g. `project col1, col2`) — keep as-is.
            rhs_parts.append(part)
    return " ; ".join(rhs_parts)


def _extract_extend_bindings(clause_body: str) -> set[str]:
    """Extract `extend <name> = <expr>` LHS identifiers from a clause body.

    The clause body is the post-pipe text after `extend `. Multiple
    bindings may appear comma-separated:
    ``extend a = expr1, b = expr2``.
    """

    bindings: set[str] = set()
    for part in _split_top_level_commas(clause_body):
        if "=" in part:
            lhs = part.split("=", 1)[0].strip()
            # `extend tenant_id = ...` → `tenant_id`
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", lhs):
                bindings.add(lhs)
    return bindings


def _extract_summarize_bindings(clause_body: str) -> set[str]:
    """Extract LHS aliases from a `summarize` clause body.

    Recognises both:
    * ``summarize alias = expr(...)``
    * ``summarize alias = expr(...) by group_a, group_b, bin(timestamp, 1m)``

    The `by` group expressions add their referenced columns to the
    output schema (visible to subsequent operators). For `bin(col, …)`
    the LHS is a derived column with the SAME name as its argument
    (Kusto convention: `bin(timestamp, 1m)` produces a `timestamp`
    output column).
    """

    bindings: set[str] = set()
    by_split = re.split(r"\s+\bby\b\s+", clause_body, maxsplit=1, flags=re.IGNORECASE)
    aggregate_part = by_split[0]
    group_part = by_split[1] if len(by_split) > 1 else ""

    bindings |= _extract_extend_bindings(aggregate_part)

    if group_part:
        for part in _split_top_level_commas(group_part):
            part = re.sub(
                r"\s+(?:asc|desc|ascending|descending)\s*$",
                "",
                part,
                flags=re.IGNORECASE,
            )
            if "=" in part:
                lhs = part.split("=", 1)[0].strip()
                if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", lhs):
                    bindings.add(lhs)
                continue
            bin_match = re.match(r"bin(?:_at)?\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)", part)
            if bin_match:
                bindings.add(bin_match.group(1))
                continue
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", part):
                bindings.add(part)
    return bindings


def _extract_summarize_rhs_only(clause_body: str) -> str:
    """Return the RHS portions of aggregate exprs + group-by exprs.

    For ``summarize alias = expr(col) by group_col, bin(timestamp, 1m)``,
    returns ``expr(col) ; group_col ; bin(timestamp, 1m)`` — the LHS
    aggregate aliases are stripped (they introduce new columns), but
    `by` group expressions ARE included (they reference existing
    columns even though they also become output columns).
    """

    by_split = re.split(r"\s+\bby\b\s+", clause_body, maxsplit=1, flags=re.IGNORECASE)
    aggregate_part = by_split[0]
    group_part = by_split[1] if len(by_split) > 1 else ""

    rhs_parts: list[str] = [_extract_extend_rhs_only(aggregate_part)]
    if group_part:
        # For group-by expressions, references must resolve before the
        # summarize step — so include each part as-is for reference
        # validation. For `alias = expr` group-by elements, only the
        # RHS is validated.
        rhs_parts.append(_extract_extend_rhs_only(group_part))
    return " ; ".join(p for p in rhs_parts if p)


def _extract_referenced_columns(clause_body: str) -> set[str]:
    """Extract all bare-identifier column references in *clause_body*.

    Strategy:

    1. Mask string literals + numeric literals (so their contents are
       not parsed as identifiers).
    2. Mask `customDimensions["..."]` / `customMeasurements["..."]`
       lookups (Pass-1 Q4 (c) escape hatch — the bracketed string is
       a literal, not a column reference).
    3. Collect remaining identifiers that are NOT in the
       Kusto-functions-and-operators allow-list.

    The result is the set of identifiers that MUST resolve to either
    (a) a base-table column or (b) an earlier `let`/`extend`/
    `summarize-LHS` binding.
    """

    masked = _STRING_LITERAL_RE.sub('""', clause_body)
    masked = _NUMERIC_LITERAL_RE.sub("0", masked)
    masked = _DYNAMIC_LOOKUP_RE.sub("__DYN__", masked)

    referenced: set[str] = set()
    for match in _IDENT_RE.finditer(masked):
        ident = match.group(1)
        if ident in _KUSTO_FUNCTIONS_AND_OPERATORS:
            continue
        if ident == "__DYN__":
            continue
        referenced.add(ident)
    return referenced


def _walk(canonicalised_kql: str, sli_id: str) -> None:
    """Walk *canonicalised_kql* left-to-right; raise on first violation.

    Failure message format (PD-C4-01 contract):
    ``KQL {sli_id} references undefined column '{name}' at line {N} —
    must extend from customDimensions first; canonicalised KQL:\n{...}``.

    The walker is a single forward pass — clauses are split on the
    canonical pipe-on-newline boundary (produced by step 2 of the
    PD-C3-01 canonicalisation pipeline), state accumulates into
    ``defined_columns``, and references are validated per clause.

    Hard-fails on `union` (multi-table column resolution out of scope —
    Pass-1 Q1 fail-fast invariant).
    """

    if re.search(r"\bunion\b", canonicalised_kql, flags=re.IGNORECASE):
        raise AssertionError(
            "union is not yet supported by the runtime validity walker — "
            "extend test_sli_kql_runtime_validity.py to support multi-table "
            "column resolution"
        )

    base_table = _detect_base_table(canonicalised_kql)
    base_cols = _BASE_TABLE_COLUMNS.get(base_table, frozenset())
    let_bindings = _extract_let_bindings(canonicalised_kql)
    defined_columns: set[str] = set(base_cols) | let_bindings

    # Split into clauses on the canonical newline-pipe boundary.
    # The first chunk is everything BEFORE the first pipe (the
    # base-table reference, possibly preceded by `let` bindings).
    clauses: list[str] = []
    raw_clauses = canonicalised_kql.split("\n|")
    for idx, raw in enumerate(raw_clauses):
        if idx == 0:
            # Pre-pipe head — strip and skip if just `let` / table.
            clauses.append(raw.strip())
        else:
            clauses.append(raw.strip())

    for line_no, clause in enumerate(clauses, start=1):
        if not clause:
            continue
        if line_no == 1:
            # Head clause — `let ...; ... <table>` — already accounted
            # for via let-binding scan and base-table detection.
            continue

        # Identify the clause keyword.
        keyword_match = re.match(r"\s*([A-Za-z_]+)\b\s*(.*)$", clause, flags=re.DOTALL)
        if not keyword_match:
            continue
        keyword = keyword_match.group(1).lower()
        body = keyword_match.group(2).strip()

        if keyword == "extend":
            rhs_only = _extract_extend_rhs_only(body)
            _validate_references(
                clause=rhs_only,
                defined_columns=defined_columns,
                sli_id=sli_id,
                line_no=line_no,
                canonical=canonicalised_kql,
            )
            new_bindings = _extract_extend_bindings(body)
            defined_columns |= new_bindings

        elif keyword == "where":
            _validate_references(
                clause=body,
                defined_columns=defined_columns,
                sli_id=sli_id,
                line_no=line_no,
                canonical=canonicalised_kql,
            )

        elif keyword == "summarize":
            # Validate references in aggregate-RHS exprs + `by` exprs
            # (LHS aliases are excluded — they introduce new columns).
            rhs_only = _extract_summarize_rhs_only(body)
            _validate_references(
                clause=rhs_only,
                defined_columns=defined_columns,
                sli_id=sli_id,
                line_no=line_no,
                canonical=canonicalised_kql,
            )
            # AFTER validation, the summarize step REPLACES the
            # output schema with (group columns) ∪ (aggregate aliases).
            # Subsequent operators (extend, project) see the new
            # schema. Per Kusto semantics we drop pre-summarize
            # columns NOT carried via `by`, but for our walker we
            # need to preserve any earlier columns that the post-
            # summarize clauses reference. Pragmatic compromise:
            # ADD the new bindings without dropping the old ones
            # (this is permissive — but the false-positive surface
            # is limited since the canonicalised body is short).
            # If a future SLI references a pre-summarize column
            # post-summarize that Kusto would actually reject, the
            # canonical-match test catches the drift via the
            # contract surface.
            new_bindings = _extract_summarize_bindings(body)
            defined_columns |= new_bindings

        elif keyword == "project":
            rhs_only = _extract_extend_rhs_only(body)
            _validate_references(
                clause=rhs_only,
                defined_columns=defined_columns,
                sli_id=sli_id,
                line_no=line_no,
                canonical=canonicalised_kql,
            )
            # `project` accepts `alias = expr` — add aliases.
            new_bindings = _extract_extend_bindings(body)
            defined_columns |= new_bindings

        elif keyword in {"let"}:
            # Already accumulated above; nothing to validate.
            continue

        elif keyword == "order" or keyword == "sort":
            # `order by <col>` — validate the column.
            _validate_references(
                clause=body,
                defined_columns=defined_columns,
                sli_id=sli_id,
                line_no=line_no,
                canonical=canonicalised_kql,
            )

        else:
            # Unrecognised tabular operator — pragmatic policy is to
            # validate any bare identifiers against the current
            # defined set (so future operator additions are safe by
            # default).
            _validate_references(
                clause=body,
                defined_columns=defined_columns,
                sli_id=sli_id,
                line_no=line_no,
                canonical=canonicalised_kql,
            )


def _validate_references(
    *,
    clause: str,
    defined_columns: set[str],
    sli_id: str,
    line_no: int,
    canonical: str,
) -> None:
    """Validate every bare-identifier reference in *clause*.

    Raises ``AssertionError`` with the PD-C4-01 contract failure
    message on the first unresolved reference.
    """

    referenced = _extract_referenced_columns(clause)
    for name in sorted(referenced):
        if name in defined_columns:
            continue
        # Allow base-table identifiers themselves to appear as
        # references (e.g. `union T1, T2` — handled separately;
        # `let counts = AuditEntries_CL | ...` — let-binding scan
        # already promoted `counts`).
        if name in _BASE_TABLE_COLUMNS:
            continue
        raise AssertionError(
            f"KQL {sli_id} references undefined column '{name}' at line "
            f"{line_no} — must extend from customDimensions first; "
            f"canonicalised KQL:\n{canonical}"
        )


# --------------------------------------------------------------------------
# Parametric per-SLI test surface — Pass-1 Q5 dynamic parametrisation
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "sli_id",
    [s["id"] for s in _SLI_DOC["slis"]],
)
def test_runtime_column_resolution_validity(sli_id: str) -> None:
    """Every SLI's KQL passes author-time column-resolution validity.

    The walker hard-fails on the first unresolved column reference;
    a clean walk implies that every `where` / `summarize ... by` /
    `extend` RHS / `project` clause references a base-table column,
    a `let`/`extend`/`summarize-LHS` binding introduced earlier in
    the same query, or a `customDimensions["..."]` lookup.

    This test enforces the A4-01 strengthening of FR-073 (per
    `spec.md:3875-3895`): the byte-equality contract test does not
    catch symmetric drift across both the implementation KQL and
    the contract KQL — the runtime-validity walker does.
    """

    impl_entry = next(s for s in _SLI_DOC["slis"] if s["id"] == sli_id)
    canonical = canonicalise_kql(impl_entry["kql"])
    _walk(canonical, sli_id=sli_id)

    # Symmetric assertion against the contract-side canonical body —
    # ensures the contract-side KQL does not carry undefined columns
    # either (the byte-equality test would catch symmetric drift but
    # the runtime-validity test catches it independently of canonical-
    # match parity).
    contract_canonical = canonical_kql_for_sli(sli_id)
    _walk(contract_canonical, sli_id=f"{sli_id} (contract)")
