"""Spec-037 evidence-pack publication gate.

Single Python module (importable for local dry-run) that runs four checks
in fail-fast order over every evidence-pack JSON sidecar + Markdown:

  1. Schema validation       (FR-009)
  2. Markdown link check     (FR-008)
  3. manual_row_ratio recompute + cap   (FR-037 + FR-038)
  4. auditor_signoff completeness when over cap (FR-038)

Citations: RES-04, FR-008, FR-009, FR-037, FR-038, SC-002, SC-011.
"""

from .gate import check_links, enforce_cap, recompute_manual_row_ratio  # noqa: F401
