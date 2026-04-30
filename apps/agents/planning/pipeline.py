"""Emergency plan assembly pipeline.

Input validation → 27-section content assembly → 8-principle completeness
check → output formatting. Target: ≤15s (NFR-001).

FRs: FR-001–004 | Research: R-007
"""

from packages.domain.src.domain.models.emergency_plan import PLAN_SECTION_SLUGS, PLANNING_PRINCIPLES


def compute_completeness(plan_doc: dict) -> dict:
    """Compute section and principle completeness for a plan.

    Returns completeness metrics including missing sections and unchecked principles.
    """
    sections = plan_doc.get("plan_sections", {})
    completed_sections = sum(1 for s in sections.values() if isinstance(s, dict) and s.get("is_complete", False))
    total_sections = len(PLAN_SECTION_SLUGS)

    principles = plan_doc.get("planning_principles_checklist", {})
    checked_principles = sum(1 for v in principles.values() if v is True)
    total_principles = len(PLANNING_PRINCIPLES)

    missing_sections = [
        slug
        for slug in PLAN_SECTION_SLUGS
        if slug not in sections or not sections.get(slug, {}).get("is_complete", False)
    ]
    unchecked_principles = [p for p in PLANNING_PRINCIPLES if not principles.get(p, False)]

    return {
        "section_completeness": completed_sections / total_sections if total_sections > 0 else 0.0,
        "principles_completeness": checked_principles / total_principles if total_principles > 0 else 0.0,
        "total_sections": total_sections,
        "completed_sections": completed_sections,
        "total_principles": total_principles,
        "checked_principles": checked_principles,
        "missing_sections": missing_sections,
        "unchecked_principles": unchecked_principles,
    }


def validate_plan_for_endorsement(plan_doc: dict) -> tuple[bool, list[str]]:
    """Check if a plan meets minimum requirements for endorsement.

    Returns (is_ready, list_of_issues).
    """
    issues = []
    completeness = compute_completeness(plan_doc)

    if completeness["section_completeness"] < 0.5:
        done = completeness["completed_sections"]
        total = completeness["total_sections"]
        issues.append(f"Only {done}/{total} sections complete (need ≥50%)")

    if completeness["principles_completeness"] < 1.0:
        issues.append(f"Not all planning principles checked: missing {completeness['unchecked_principles']}")

    if not plan_doc.get("hazard_types"):
        issues.append("No hazard types specified")

    if not plan_doc.get("authority"):
        issues.append("No issuing authority specified")

    return len(issues) == 0, issues
