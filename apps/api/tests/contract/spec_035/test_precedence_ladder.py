"""T018 — precedence ladder for the spec-035 extension envelope.

When two error conditions stack, the higher-precedence code wins per
[ERROR_PRECEDENCE](../../../app/domain/extension_envelope.py):

    evaluator_not_routable > sovereignty_denied > unauthorized > forbidden
    > rate_limited > schema_invalid|seed_not_ready
"""

from __future__ import annotations

from app.domain.extension_envelope import ERROR_PRECEDENCE, ExtensionErrorCode


def _index(code: ExtensionErrorCode) -> int:
    return ERROR_PRECEDENCE.index(code)


def test_evaluator_not_routable_beats_sovereignty_denied() -> None:
    assert _index(ExtensionErrorCode.EVALUATOR_NOT_ROUTABLE) < _index(ExtensionErrorCode.SOVEREIGNTY_DENIED)


def test_sovereignty_denied_beats_unauthorized() -> None:
    assert _index(ExtensionErrorCode.SOVEREIGNTY_DENIED) < _index(ExtensionErrorCode.UNAUTHORIZED)


def test_unauthorized_beats_forbidden() -> None:
    assert _index(ExtensionErrorCode.UNAUTHORIZED) < _index(ExtensionErrorCode.FORBIDDEN)


def test_forbidden_beats_rate_limited() -> None:
    assert _index(ExtensionErrorCode.FORBIDDEN) < _index(ExtensionErrorCode.RATE_LIMITED)


def test_rate_limited_beats_schema_invalid() -> None:
    assert _index(ExtensionErrorCode.RATE_LIMITED) < _index(ExtensionErrorCode.SCHEMA_INVALID)


def test_rate_limited_beats_seed_not_ready() -> None:
    assert _index(ExtensionErrorCode.RATE_LIMITED) < _index(ExtensionErrorCode.SEED_NOT_READY)


def test_evaluator_not_routable_is_top_of_ladder() -> None:
    assert ERROR_PRECEDENCE[0] is ExtensionErrorCode.EVALUATOR_NOT_ROUTABLE


def test_precedence_full_chain_is_total_order() -> None:
    chain = [
        ExtensionErrorCode.EVALUATOR_NOT_ROUTABLE,
        ExtensionErrorCode.SOVEREIGNTY_DENIED,
        ExtensionErrorCode.UNAUTHORIZED,
        ExtensionErrorCode.FORBIDDEN,
        ExtensionErrorCode.RATE_LIMITED,
    ]
    indices = [_index(c) for c in chain]
    assert indices == sorted(indices), (
        f"precedence must be evaluator_not_routable→sovereignty→unauth→forbidden→rate_limited; got indices {indices}"
    )
