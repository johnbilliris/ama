# Spec 036 T101 — WAVE + screen-reader pre-GA accessibility audit checklist

> **Status:** code is in place (`<CitationCard />`, `<DegradedModeBadge />`).
> The full WAVE + NVDA + JAWS audit lands as a gate before T130 (GA cutover).
> This checklist is the script the audit will follow.

## Audit targets

1. `packages/ui/src/components/citation/citation-card.tsx`
2. `packages/ui/src/components/citation/degraded-mode-badge.tsx`
3. `apps/web/src/components/recommendations/recommendation-card.tsx`
4. The Simulation chat panel (turn.delta + citation event rendering)

## WAVE checks (browser extension)

| # | Check | Expected |
|---|-------|----------|
| 1 | No empty buttons / links | 0 errors |
| 2 | Adequate contrast (4.5:1 for normal, 3:1 for large) | 0 errors |
| 3 | Adequate alt text on icons | 0 errors |
| 4 | ARIA roles match the visual semantics | 0 errors |
| 5 | Heading order is logical | 0 errors |

## Screen-reader checks (NVDA + JAWS)

| Element | Expected announcement |
|---------|------------------------|
| Citation card region | "Region: Sources cited by Risk Assessment Agent" |
| Jurisdiction badge | "Jurisdiction: New South Wales" (full name, not "NSW") |
| Confidence badge | "Status: High (84 percent)" — never colour-only |
| "Show quote" button | "Show quote, button, collapsed" / "expanded" |
| Source PDF link | "Source PDF (opens in new tab), link" |
| Degraded-mode banner | "Alert: Operating in degraded mode. Showing cached corpus content (12 minutes old, since 14:32)…" |
| Empty-result note | "Status: no corpus match — recommend operator verification" |

## Keyboard navigation

* Tab order: header → handbook link → PDF link → show-quote button → next card.
* Enter / Space activates the show-quote button.
* No keyboard trap.
* Focus ring visible on every interactive element (browser default OK).

## Mobile / responsive

* Citation card collapses to single column ≤ 480 px width.
* Banner remains readable at 200% zoom.

## Acceptance gate

Phase E (T130) MUST NOT cut to GA until:

1. WAVE returns 0 errors on each component preview page.
2. NVDA + JAWS produce the expected announcements.
3. Keyboard nav passes.
4. The accessibility memo §45–69 is updated to reference this audit.

## Where the audit logs land

* `tests/accessibility/spec_036/<date>-wave.html` — WAVE export.
* `tests/accessibility/spec_036/<date>-screenreader.md` — manual transcript.
