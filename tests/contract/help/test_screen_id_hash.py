"""spec-038 T-AA188 — screen_id_hash determinism (FR-010a)."""

from __future__ import annotations

from ama_domain import Callout
from ama_domain.screen_id_hash import compute_screen_id_hash


def _c(number: int, anchor: str) -> Callout:
    return Callout(number=number, anchor_dom_path=anchor, alt_text=f"alt {number}")


def test_hash_stable_for_same_inputs() -> None:
    a = [_c(1, "#a"), _c(2, "#b"), _c(3, "#c")]
    assert compute_screen_id_hash("route-x", a) == compute_screen_id_hash("route-x", a)


def test_hash_changes_when_callout_added() -> None:
    h1 = compute_screen_id_hash("route-x", [_c(1, "#a"), _c(2, "#b")])
    h2 = compute_screen_id_hash("route-x", [_c(1, "#a"), _c(2, "#b"), _c(3, "#c")])
    assert h1 != h2


def test_hash_changes_when_route_changes() -> None:
    assert compute_screen_id_hash("route-x", [_c(1, "#a")]) != compute_screen_id_hash("route-y", [_c(1, "#a")])


def test_hash_ordered_by_callout_number_not_lexical() -> None:
    # Reordering callout numbers must change the hash even with same anchors.
    h_norm = compute_screen_id_hash("r", [_c(1, "#a"), _c(2, "#b")])
    h_swap = compute_screen_id_hash("r", [_c(1, "#b"), _c(2, "#a")])
    assert h_norm != h_swap
