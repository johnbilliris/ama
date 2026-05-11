"""Cycle 3 / T-AA30 / A3-05 / FR-073 — KQL canonicalisation pipeline (PD-C3-01).

Public surface (Cycle 3 Pass-2 Q2 — `spec.md:1388-1483`):

* :func:`canonicalise_kql` — public entry point applying the six-step
  canonicalisation pipeline to a single KQL string.
* :func:`canonical_kql_for_sli` — extracts and canonicalises the
  ``contracts/sli-thresholds.md`` fenced KQL block for *sli_id*.

Algorithm (`contracts/sli-thresholds.md` §10.1, plan.md PD-C3-01):

1. Strip line comments (``// …`` to end-of-line) + block comments
   (``/* … */``).
2. Collapse runs of ASCII whitespace to a single space, preserving
   exactly one ``\\n`` before each pipe (``|``).
3. Lowercase Kusto reserved keywords (``extend``, ``where``,
   ``summarize``, ``by``, ``project``, ``let``, ``and``, ``or``,
   ``in``, ``between``, ``ascending``, ``descending``).
4. Sort each ``by`` clause's column list lexicographically.
5. Sort each ``summarize`` aggregate-expression list by left-hand-side
   alias lexicographically.
6. Strip redundant outer parentheses around ``extend`` target
   expressions.

Invariants (PD-C3-01):

* Idempotence — ``canonicalise_kql(canonicalise_kql(x)) == canonicalise_kql(x)``.
* Determinism — same input produces same byte-sequence across hash-randomisation
  seeds and Python interpreter restarts (no set-of-strings sort path participates).
* Stability under semantic-no-op rewrites (whitespace, comments, parenthesis,
  ``by``/``summarize`` re-ordering).

The leading underscore on the module file name signals private scope to
the contract-test surface; the module exports its public API via
``__all__``.
"""

from __future__ import annotations

import re
from pathlib import Path

__all__ = ["canonicalise_kql", "canonical_kql_for_sli"]

# Resolves to <repo>/specs/036-sim-agent-extend/contracts/sli-thresholds.md.
# Mirrors the established `_SLI_PATH` pattern at
# tests/contract/test_sli_kql_schema_v2.py:25.
_THRESHOLDS_PATH = (
    Path(__file__).resolve().parents[2]
    / "specs"
    / "036-sim-agent-extend"
    / "contracts"
    / "sli-thresholds.md"
)

# Kusto reserved keywords lowered in step 3. We deliberately limit the
# set to operators and connectives the SLI bodies use (PD-C3-01); the
# canonicaliser is not a full Kusto AST — strict-string equivalence
# is the contract surface.
_KUSTO_KEYWORDS = (
    "extend",
    "where",
    "summarize",
    "by",
    "project",
    "let",
    "and",
    "or",
    "in",
    "between",
    "ascending",
    "descending",
)


# --------------------------------------------------------------------------
# Step 1 — strip comments
# --------------------------------------------------------------------------

_LINE_COMMENT_RE = re.compile(r"//[^\n]*")
_BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", flags=re.DOTALL)


def _strip_comments(text: str) -> str:
    """Step 1 — remove line and block comments."""

    text = _BLOCK_COMMENT_RE.sub("", text)
    text = _LINE_COMMENT_RE.sub("", text)
    return text


# --------------------------------------------------------------------------
# Step 2 — whitespace collapse with pipe-newline preservation
# --------------------------------------------------------------------------


def _collapse_whitespace_pipe_newline(text: str) -> str:
    """Step 2 — collapse whitespace; ensure exactly one ``\\n`` before each ``|``."""

    # First pass — collapse all runs of whitespace (including newlines) to
    # a single space.
    collapsed = re.sub(r"\s+", " ", text).strip()
    # Second pass — restore a single newline immediately before each pipe
    # so the canonical form is line-oriented per-clause (and so subsequent
    # regexes can use ``\n`` as a clause boundary).
    collapsed = re.sub(r"\s*\|\s*", "\n| ", collapsed)
    # Strip any leading whitespace that re-entered before the first clause.
    return collapsed.lstrip()


# --------------------------------------------------------------------------
# Step 3 — lowercase Kusto reserved keywords
# --------------------------------------------------------------------------

# Build a single regex that matches any keyword as a whole word (case-
# insensitively); the substitution lowercases the matched span. We use
# word boundaries so identifiers containing the keyword as a substring
# (e.g. ``where_clause`` if it ever appears as a column name) are
# unaffected.
_KEYWORD_RE = re.compile(
    r"\b(" + "|".join(_KUSTO_KEYWORDS) + r")\b",
    flags=re.IGNORECASE,
)


def _lowercase_keywords(text: str) -> str:
    """Step 3 — lowercase Kusto reserved keywords."""

    return _KEYWORD_RE.sub(lambda m: m.group(0).lower(), text)


# --------------------------------------------------------------------------
# Step 4 — sort `by` clause column lists lexicographically
# --------------------------------------------------------------------------

# Match `by <columns>` where `<columns>` is a comma-separated list of
# bare identifiers. Stop at end-of-line (canonical form is line-oriented
# after step 2) so we do not consume a following pipe.
_BY_CLAUSE_RE = re.compile(
    r"\bby\s+([A-Za-z_][A-Za-z0-9_]*(?:\s*,\s*[A-Za-z_][A-Za-z0-9_]*)*)\b",
)


def _sort_by_clauses(text: str) -> str:
    """Step 4 — sort each ``by`` column list lexicographically."""

    def _sort(match: re.Match[str]) -> str:
        columns = [c.strip() for c in match.group(1).split(",")]
        columns.sort()
        return "by " + ", ".join(columns)

    return _BY_CLAUSE_RE.sub(_sort, text)


# --------------------------------------------------------------------------
# Step 5 — sort `summarize` alias-expression list by alias lexicographically
# --------------------------------------------------------------------------


def _split_top_level_comma(text: str) -> list[str]:
    """Split *text* on top-level ``,`` (ignoring commas inside parentheses).

    Used for ``summarize alias = expr(...), alias2 = expr2(...)`` decomposition.
    """

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


def _sort_summarize_clauses(text: str) -> str:
    """Step 5 — sort ``summarize`` alias-expression pairs by alias lex.

    Recognises ``summarize <alias> = <expr>(, <alias_n> = <expr_n>)*`` up to
    a clause-terminating ``by`` keyword OR a clause-terminating newline-pipe.
    Pairs are reassembled in alias-sorted order.
    """

    # Match `summarize <body>` up to (a) ` by ` clause-boundary, or (b) end of
    # canonical line (the sole-pipe-on-newline form produced by step 2).
    pattern = re.compile(
        r"\bsummarize\s+(?P<body>[^\n]*?)(?P<tail>\s+by\b|$)",
        flags=re.MULTILINE,
    )

    def _sort(match: re.Match[str]) -> str:
        body = match.group("body").strip()
        tail = match.group("tail")
        pairs = _split_top_level_comma(body)
        if not pairs:
            return match.group(0)

        # Each pair must be `alias = expr` (the canonical Kusto summarize
        # form for the SLIs in scope). Decompose by the first `=`.
        decomposed: list[tuple[str, str]] = []
        for pair in pairs:
            if "=" in pair:
                alias, _, expr = pair.partition("=")
                decomposed.append((alias.strip(), pair.strip()))
            else:
                # Non-alias forms (e.g. `summarize count() by ...`) are
                # left as-is — sort would be a no-op single-element list.
                decomposed.append((pair.strip(), pair.strip()))

        decomposed.sort(key=lambda p: p[0])
        sorted_body = ", ".join(p[1] for p in decomposed)
        return f"summarize {sorted_body}{tail}"

    return pattern.sub(_sort, text)


# --------------------------------------------------------------------------
# Step 6 — strip redundant outer parentheses around `extend` target exprs
# --------------------------------------------------------------------------

# Match `extend <name> = (<expr>)` where the parens are the OUTERMOST around
# the target — i.e. the open-paren immediately follows the `=` (with optional
# whitespace) and the matching close-paren is the last character of the
# extend target (terminating at newline or comma).
_EXTEND_PAREN_RE = re.compile(
    r"\bextend\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\((?P<inner>[^()]*(?:\([^()]*\)[^()]*)*)\)(?=\s*(?:\n|,|$))",
)


def _strip_redundant_extend_parens(text: str) -> str:
    """Step 6 — strip redundant outer parentheses on ``extend`` target exprs."""

    def _strip(match: re.Match[str]) -> str:
        name = match.group(1)
        inner = match.group("inner").strip()
        return f"extend {name} = {inner}"

    return _EXTEND_PAREN_RE.sub(_strip, text)


# --------------------------------------------------------------------------
# Public entry-points
# --------------------------------------------------------------------------


def _canonicalise_kql_string(raw: str) -> str:
    """Apply the six-step canonicalisation pipeline to *raw*.

    Private helper (no leading underscore export). Used by both
    :func:`canonicalise_kql` (public surface) and :func:`canonical_kql_for_sli`.
    """

    text = _strip_comments(raw)
    text = _collapse_whitespace_pipe_newline(text)
    text = _lowercase_keywords(text)
    text = _sort_by_clauses(text)
    text = _sort_summarize_clauses(text)
    text = _strip_redundant_extend_parens(text)
    # Trailing whitespace clean-up — a final strip ensures the byte-sequence
    # is normalised regardless of input trailing newlines.
    return text.strip()


def canonicalise_kql(text: str) -> str:
    """Canonicalise *text* (a KQL string) per the six-step PD-C3-01 pipeline.

    Idempotent: ``canonicalise_kql(canonicalise_kql(x)) == canonicalise_kql(x)``.
    Deterministic: same input → same byte-sequence across runs.

    Raises ``TypeError`` if *text* is not a string.
    """

    if not isinstance(text, str):
        raise TypeError(
            f"canonicalise_kql expected str, got {type(text).__name__!r}"
        )
    return _canonicalise_kql_string(text)


def canonical_kql_for_sli(
    sli_id: str,
    *,
    thresholds_path: Path | None = None,
) -> str:
    """Return canonical KQL for *sli_id* from the contracts file.

    Parses the matching ```` ```kql ... ``` ```` fenced block out of
    *thresholds_path* (defaults to :data:`_THRESHOLDS_PATH`); returns its
    canonicalised form.

    Block discovery: the contract file contains one or more SLI sections
    with ``## ... <sli_id> ...`` headings preceding a single ` ```kql ` fence
    block. Cycle 3 introduced a §10 KQL-canonicalisation contract subsection
    that contains an explanatory ` ```python ` fence — the discovery is
    therefore ``kql``-language-fenced AND positioned within the SLI's section
    (bounded above by the section heading carrying *sli_id*, bounded below by
    the next ``## ``-prefixed heading).

    Recognised SLI ids: ``SLI-Z1`` … ``SLI-Z7``. ``SLI-Z1`` and
    ``SLI-Z2`` are anchored on the Cycle 1 numeric-stem headings
    (``## 2. SLI-1 — …`` and ``## 3. SLI-2 — …``); ``SLI-Z3`` /
    ``SLI-Z4`` / ``SLI-Z5`` are anchored on the Cycle 3-added headings
    (``## 6c. SLI-Z3 — …``, ``## 6d. SLI-Z4 — …``, ``## 6e. SLI-Z5 — …``)
    promoted by T-AA34 alignment audit; ``SLI-Z6`` / ``SLI-Z7`` are
    anchored on the Cycle 2 headings (``## 6a. SLI-Z6 — …`` and
    ``## 6b. SLI-Z7 — …``).

    Raises ``KeyError`` if *sli_id* has no matching block; raises
    ``ValueError`` if the contracts file is malformed (no fence-close, etc.).
    """

    path = thresholds_path if thresholds_path is not None else _THRESHOLDS_PATH
    if not path.is_file():
        raise ValueError(
            f"Failed to extract canonical KQL for {sli_id!r}: "
            f"thresholds file not found at {path!s}"
        )
    text = path.read_text(encoding="utf-8")

    # Map Cycle 1 SLI ids whose contract heading uses an unprefixed
    # numeric stem (SLI-1, SLI-2) to that stem; Cycle 1 SLIs Z3 / Z4 / Z5
    # use the literal SLI-Z3 / SLI-Z4 / SLI-Z5 anchor (their contract
    # headings are at §6c / §6d / §6e — added in Cycle 3 / T-AA34 per
    # Pass-1 Q5 dynamic parametrisation requirement); Cycle 2 ids
    # (SLI-Z6, SLI-Z7) likewise use the literal anchor (§6a / §6b).
    if sli_id in {"SLI-Z1", "SLI-Z2"}:
        # Map Z1 → 1, Z2 → 2 so the section heading "## 2. SLI-1 — …"
        # matches the ``SLI-Z1`` lookup. The numeric stem in the heading
        # is the (Z<N>) → (N) digit substitution.
        n = sli_id[len("SLI-Z"):]
        section_anchors = (f"SLI-{n}",)
    else:
        section_anchors = (sli_id,)

    # Find the section: a heading line like "## <prefix> <anchor> ..." (we
    # accept both numbered and `6a` / `6b` forms — anything that includes
    # the anchor string as a whole token following a ``## `` prefix).
    section_start: int | None = None
    section_end: int = len(text)
    lines = text.splitlines(keepends=True)
    line_offsets: list[int] = [0]
    for ln in lines:
        line_offsets.append(line_offsets[-1] + len(ln))

    for idx, line in enumerate(lines):
        if not line.startswith("## "):
            continue
        if section_start is not None:
            # End of the chosen section — first subsequent ``## ``-heading.
            section_end = line_offsets[idx]
            break
        for anchor in section_anchors:
            # Use whole-token match so ``SLI-1`` does not match ``SLI-10``
            # if a future SLI is added.
            if re.search(rf"\b{re.escape(anchor)}\b", line):
                section_start = line_offsets[idx]
                break

    if section_start is None:
        raise KeyError(f"{sli_id} not found in {path!s}")

    section = text[section_start:section_end]

    # Extract the FIRST ``` ```kql ``` ``` fenced block in the section.
    fence_match = re.search(r"```kql\s*\n(?P<body>.*?)```", section, flags=re.DOTALL)
    if fence_match is None:
        raise ValueError(
            f"Failed to extract canonical KQL for {sli_id!r}: "
            "no ```kql fenced block in matched section"
        )

    return _canonicalise_kql_string(fence_match.group("body"))
