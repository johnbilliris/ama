---
purpose: Documents the Incident Commander's journey through the ops dashboard with WCAG 2.2 AA touchpoint annotations, enabling UX and PO review of accessibility obligations per step.
personas:
  - Technical-Experience
diagrams:
  - EXP-01
specs:
  - spec-020
---

# EXP-01 — Ops Dashboard User Journey

[→ Architecture index](../README.md)

![EXP-01: Ops Dashboard User Journey](ops-dashboard-user-journey.png)

<!-- spec-cross-ref: spec-020 -->

This view documents the Incident Commander's journey through the ops dashboard with WCAG 2.2 AA touchpoint annotations, enabling UX and PO review of accessibility obligations per step.

## Journey Steps

| Step | Cognitive phase | WCAG 2.2 Criterion | Component/Endpoint mapping | Implementation note | Status |
| --- | --- | --- | --- | --- | --- |
| Sign-in | Perception | SC 1.3.1 Info and Relationships | Web auth screen -> Entra OAuth session | Labeled controls and structured form groups | IMPLEMENTED |
| Situational awareness | Comprehension | SC 2.4.6 Headings and Labels | Workspace panels, map summaries, and incident context | Panel headings and section labels identify current incident context | IMPLEMENTED |
| Review recommendation | Comprehension | SC 1.4.3 Contrast | Recommendation details and supporting evidence | Evidence presentation requires browser-level accessibility verification | UNVERIFIED |
| Approve recommendation | Action | SC 4.1.2 Name, Role, Value | Approval card action control -> recommendation approval endpoint | Action uses an explicit button click (`type=button`) with disabled state while submitting | IMPLEMENTED |
| Publication confirmation | Comprehension | SC 4.1.3 Status Messages | Alert publication response state | Publication success/failure messaging should be surfaced without forced focus movement | UNVERIFIED |
| Audit receipt | Comprehension | SC 1.3.1 + SC 4.1.3 | Audit retrieval panel and provenance display | Audit row visibility and status announcements require scenario verification in browser testing | UNVERIFIED |

> **👤 Human Approval Gate (FR-009)**: The "Approve Recommendation" step is a mandatory human decision point. The platform must not auto-publish recommendations; the Incident Commander explicitly approves before actuation.

## FR Notes

- **FR-026**: Ops-dashboard user journey documented with per-step WCAG 2.2 AA annotations; the seven-step sequence matches the EXP-01 source diagram.
- **FR-009**: Human approval gate is marked on the diagram and documented in the Journey Steps table.

WCAG status notes in this page reflect repository evidence only. Any criterion marked `UNVERIFIED` requires independent accessibility test execution and captured receipts.

## Related Pages

- [Architecture index](../README.md)
- [WCAG Coverage Map](wcag-coverage.md)
- [QUAL-01 — Test Pyramid](../quality/test-pyramid.md)
