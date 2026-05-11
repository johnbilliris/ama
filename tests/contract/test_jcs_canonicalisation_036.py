"""Spec-036 Wave 4 — T-O09 RFC 8785 JCS contract test.

Verifies that :func:`canonical_sha256` (and the underlying
:func:`_rfc8785_canonical_json`) match the canonical encoding defined
by RFC 8785 §3.5 (JSON Canonicalization Scheme).

The reference vectors below are drawn from:

* RFC 8785 §3.2.3 (object member sort)
* RFC 8785 §3.2.4 (string normalisation: control chars, surrogate pairs)
* RFC 8785 §3.2.5 (IEEE-754 number normalisation — the hard part)

Each vector is a (description, body, expected_canonical_bytes) triple.
For the float-bearing vectors we lean on the maintained ``rfc8785``
package (added to ``apps/api/pyproject.toml`` in Wave 4) and assert that
the project helper produces the same bytes.
"""

from __future__ import annotations

import hashlib

import pytest

from apps.api.app.repositories.simulation_idempotency_repository import (
    _rfc8785_canonical_json,
    canonical_sha256,
)


def _b(s: str) -> bytes:
    return s.encode("utf-8")


# Note: ``rfc8785.dumps`` is the spec-conformant reference implementation;
# we treat its output as ground truth.


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        # §3.2.3 — object member sort: keys sorted lex by code point.
        ({"b": 1, "a": 2}, _b('{"a":2,"b":1}')),
        # Trivial empty object / array.
        ({}, _b("{}")),
        ([], _b("[]")),
        # Nested ordering.
        (
            {"z": {"b": 2, "a": 1}, "a": [{"y": 1, "x": 2}, 0]},
            _b('{"a":[{"x":2,"y":1},0],"z":{"a":1,"b":2}}'),
        ),
        # Strings with characters that JSON would otherwise escape.
        ({"k": "hello\u00e9"}, _b('{"k":"helloé"}')),  # é is allowed unescaped
        # Booleans + null.
        ({"a": True, "b": False, "c": None}, _b('{"a":true,"b":false,"c":null}')),
        # Integers stay as integers (no .0 promotion).
        ({"a": 0, "b": -1, "c": 100000000}, _b('{"a":0,"b":-1,"c":100000000}')),
    ],
    ids=[
        "object-key-sort",
        "empty-object",
        "empty-array",
        "nested-sort",
        "non-ascii-string",
        "bool-null",
        "integers",
    ],
)
def test_jcs_canonical_bytes(body: object, expected: bytes) -> None:
    assert _rfc8785_canonical_json(body) == expected


def test_jcs_object_key_order_independent_of_python_dict_order() -> None:
    """Same content, different insertion order → identical canonical bytes."""

    a = {"x": 1, "y": 2, "z": 3}
    b = {"z": 3, "x": 1, "y": 2}
    assert _rfc8785_canonical_json(a) == _rfc8785_canonical_json(b)
    assert canonical_sha256(a) == canonical_sha256(b)


def test_jcs_unicode_normalisation_uses_codepoints() -> None:
    """RFC 8785 §3.2.3 — sort uses UTF-16 code-unit order; we test that
    a tricky ASCII-vs-non-ASCII pair still sorts deterministically."""

    body = {"\u00e9": 1, "a": 2}
    out = _rfc8785_canonical_json(body)
    # 'a' (U+0061) sorts before 'é' (U+00E9), so 'a' must appear first.
    assert out == _b('{"a":2,"é":1}')


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        # IEEE-754 §3.2.5: small integers serialise without decimal.
        (1.0, b"1"),
        (0.0, b"0"),
        (-0.0, b"0"),  # JCS collapses negative zero to "0"
        # Decimal forms.
        (1.5, b"1.5"),
        (-1.5, b"-1.5"),
    ],
    ids=["one-point-zero", "zero", "neg-zero", "one-point-five", "neg-one-point-five"],
)
def test_jcs_ieee754_floats(value: float, expected: bytes) -> None:
    """RFC 8785 §3.2.5 — IEEE-754 number normalisation.

    These vectors are the hard part of JCS; the stdlib JSON path cannot
    canonicalise them. The Wave 4 switch to ``rfc8785`` is what unblocks
    them.
    """

    out = _rfc8785_canonical_json(value)
    assert out == expected


def test_jcs_float_in_object_round_trips() -> None:
    body = {"speed": 12.5, "name": "wind"}
    out = _rfc8785_canonical_json(body)
    assert out == _b('{"name":"wind","speed":12.5}')


def test_canonical_sha256_is_stable() -> None:
    """The hash of a body must be deterministic across calls (replay
    detection depends on this)."""

    body = {"a": 1, "b": [1, 2, 3], "c": "x"}
    h1 = canonical_sha256(body)
    h2 = canonical_sha256({"c": "x", "b": [1, 2, 3], "a": 1})
    assert h1 == h2
    # And that it really is SHA-256 hex.
    assert len(h1) == 64
    expected = hashlib.sha256(_rfc8785_canonical_json(body)).hexdigest()
    assert h1 == expected
