---
purpose: WCAG 2.2 success-criteria coverage table mapping each criterion to implementation status per component.
personas:
  - Technical-Experience
diagrams: []
specs:
  - spec-020
---

# WCAG 2.2 Coverage Map

[→ Architecture index](../README.md)

<!-- spec-cross-ref: spec-020 -->

Full independent WCAG audit is deferred. See known-gaps entry WCAG-AUDIT-FULL.

| Criterion | Description | Component | Status | Notes |
| --- | --- | --- | --- | --- |
| 1.1.1 | Non-text Content | CitationCard | IMPLEMENTED | Alt text patterns present in component-level tests |
| 1.3.1 | Info and Relationships | AlertBanner | IMPLEMENTED | Structured headings/labels documented in UI components |
| 1.4.3 | Contrast (Minimum) | Dashboard views | UNVERIFIED | Global contrast verification evidence not checked in for every view/state |
| 2.1.1 | Keyboard | Dashboard | UNVERIFIED | End-to-end keyboard traversal receipts are not currently attached |
| 2.4.1 | Bypass Blocks | Web Dashboard | IMPLEMENTED | Skip-navigation behavior is part of UI baseline expectations |
| 3.1.1 | Language of Page | Web shell | IMPLEMENTED | `lang` attribute is expected by web runtime scaffolding |
| 4.1.2 | Name, Role, Value | Form and action controls | PARTIAL | Control semantics vary by component; scenario-level verification pending |
| 2.5.3 | Label in Name | Buttons | UNVERIFIED | Requires assistive-tech validation beyond static component assertions |
