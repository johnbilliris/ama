"""spec-038 T-AA061 — deprecation resolver (FR-011d / FR-011d-AMEND)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class DeprecationOutcome:
    kind: Literal["current", "current_replacement", "withdrawn_no_replacement"]
    current_slug: str | None
    replacement_slug: str | None
    handoff_destination: str | None


def resolve_deprecation(
    *,
    deep_link_slug: str,
    snapshot_id: str,
    deprecation_map: dict[str, dict[str, str | None]] | None = None,
    tenant_handoff_destination: str | None = None,
) -> DeprecationOutcome:
    """Look up the deprecation map for ``deep_link_slug``.

    ``deprecation_map`` shape::

        {
          "old-slug": {"replacement": "new-slug" | None, "snapshot_id": "..."},
          ...
        }
    """
    if not deprecation_map or deep_link_slug not in deprecation_map:
        return DeprecationOutcome(
            kind="current",
            current_slug=deep_link_slug,
            replacement_slug=None,
            handoff_destination=None,
        )
    row = deprecation_map[deep_link_slug]
    replacement = row.get("replacement")
    if replacement:
        return DeprecationOutcome(
            kind="current_replacement",
            current_slug=deep_link_slug,
            replacement_slug=replacement,
            handoff_destination=None,
        )
    return DeprecationOutcome(
        kind="withdrawn_no_replacement",
        current_slug=deep_link_slug,
        replacement_slug=None,
        handoff_destination=tenant_handoff_destination,
    )


__all__ = ["DeprecationOutcome", "resolve_deprecation"]
