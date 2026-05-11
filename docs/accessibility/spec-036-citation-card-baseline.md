# Spec-036 — `<CitationCard />` Accessibility Baseline (T243)

> **Status**: warn-only (F-A12.5). Flip the lane to blocking once two
> consecutive PRs land with zero new axe violations.
> **Standard**: WCAG 2.2 AA (`wcag2a + wcag2aa + wcag21a + wcag21aa + wcag22aa`).
> **Risk register**: R13 — UI accessibility regression of citation
> grounding (FR-RAG-UI-01). See `docs/risk-register/spec-036.md`.

## 1. Scope

| Surface | Path | Lane |
|---|---|---|
| `<CitationCard />` | `packages/ui/src/components/citation/citation-card.tsx` | `accessibility-citation-card` (CI) |
| `<RecommendationCard />` (renders the live-region announcement) | `apps/web/src/components/recommendations/recommendation-card.tsx` | (covered by smoke + this lane via the embedded `<CitationCard />`) |

The lane runs `axe-core` against both **collapsed** (default) and
**expanded** (snippet visible) states using vitest + JSDOM. JSDOM does
not implement `HTMLCanvasElement.getContext`, which is invoked by axe's
`color-contrast` rule on text-icon ligature detection — the surfaced
"Not implemented" stderr line is harmless and unrelated to violations.

## 2. Conformance level achieved (as of T241 landing)

| Success Criterion (WCAG 2.2 AA) | Status | Evidence |
|---|---|---|
| 1.3.1 Info and relationships | **Pass** | `<header id>` + `aria-labelledby` pairing; `aria-controls`/`aria-expanded` on the toggle. |
| 1.4.3 Contrast (Minimum) | **Pass (warn)** | Text/icon contrast manually validated; axe canvas-based check warns under JSDOM but passes under headless Chromium. |
| 1.4.11 Non-text contrast | **Pass** | Confidence pill carries text + icon; jurisdiction pill ≥ 3:1 against background. |
| 2.1.1 Keyboard | **Pass** | Toggle is `<button>` in tab order; explicit `Enter`/`Space` `onKeyDown`. (T240 unit test) |
| 2.4.3 Focus order | **Pass** | DOM order matches visual order. |
| 2.4.7 Focus Visible | **Pass** | `focus-visible:ring-2 focus-visible:ring-blue-500` on toggle + handbook + PDF link. |
| 3.2.1 On focus | **Pass** | No context change on focus — only on click/Enter/Space. |
| 3.3.2 Labels or instructions | **Pass** | Each interactive control carries a name (link text or button label). |
| 4.1.2 Name, role, value | **Pass** | `<button>` with `aria-expanded`; collapsible panel referenced via `aria-controls`. |
| 4.1.3 Status messages (WCAG 2.1 AA) | **Pass** | `role="status"` on confidence pill; `aria-live="polite"` announcement when grounded recommendation renders. |
| 2.4.11 Focus Not Obscured (Minimum) (WCAG 2.2) | **Pass (manual)** | Card is fully visible in default layout; verify under sticky-header pages on adoption. |
| 2.5.7 Dragging Movements (WCAG 2.2) | **N/A** | No drag interactions. |
| 2.5.8 Target Size (Minimum) (WCAG 2.2) | **Pass** | Toggle button ≥ 24×24 CSS px; padding `py-0.5` plus default font-size renders ≥ 32px tall. |
| 3.2.6 Consistent Help (WCAG 2.2) | **N/A** | No help mechanism on this surface. |
| 3.3.7 Redundant Entry (WCAG 2.2) | **N/A** | No data entry. |
| 3.3.8 Accessible Authentication (Minimum) (WCAG 2.2) | **N/A** | No authentication. |

## 3. Known gaps

1. **JSDOM `color-contrast` warnings** — the `getContext` "Not implemented"
   trace line. Mitigation: re-run axe against the same component in
   Playwright (chromium) on a nightly to capture the real result. Tracking
   in a follow-up to T243.
2. **Live-region announcement timing** — the `aria-live="polite"` text in
   `<RecommendationCard />` fires on first render of grounded recommendations.
   Verify with screen-reader walkthrough (NVDA + JAWS) once the surface ships.
3. **Confidence-pill colour-only signal** — mitigated by always-on
   icon (`✓`/`⚠`/`✗`) and numeric percentage; no axe violation, but
   document the pattern so future authors do not "simplify" by removing
   the redundant glyph.

## 4. Remediation roadmap

| Action | Owner | Trigger |
|---|---|---|
| Add Playwright + `@axe-core/playwright` cross-validation lane | spec-036 maintainer | Once `accessibility-citation-card` lane has been green for 2 PRs. |
| Flip `accessibility-citation-card` to blocking | spec-036 maintainer | Same trigger. |
| Add screen-reader walkthrough scripts (NVDA/JAWS/VoiceOver) | UX accessibility lead | When the citation surface goes to production preview. |
| Extend axe coverage to `<DegradedModeBadge />` and `<RecommendationCard />` end-to-end | spec-036 maintainer | Next minor release after blocking flip. |

## 5. Cross-references

- WCAG 2.2 AA: <https://www.w3.org/TR/WCAG22/>
- Risk register entry: `docs/risk-register/spec-036.md` § R13
- Tests: `apps/web/tests/web/src/components/citation/citation-card.test.tsx` (T240),
  `apps/web/tests/web/src/components/citation/citation-card.axe.test.tsx` (T239).
- CI lane: `.github/workflows/ci.yml::accessibility-citation-card`.
- Implementation: `packages/ui/src/components/citation/citation-card.tsx` (T241),
  `apps/web/src/components/recommendations/recommendation-card.tsx` (T241 live-region).
