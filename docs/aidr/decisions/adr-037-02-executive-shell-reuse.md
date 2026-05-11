# ADR-037-02 — Executive shell reuse (no new chart libraries)

**Date**: 2026-05-11
**Status**: Accepted
**Spec**: [`specs/037-capstone-evidence-pack/`](../../../specs/037-capstone-evidence-pack/) — PD-037-02, SC-009

## Context

Spec-037's Clarification 3 asks where the read-only Executive KPI page should live and how richly it should render. The options ranged from a fully bespoke standalone micro-frontend (with charting libraries) to embedding the surface inside an existing dashboard sub-route.

## Decision

A **new top-level Next.js route** at `apps/web/src/app/governance/executive/`, **sibling to the existing `/governance/dashboard/{audit,compliance,readiness,recovery,risk}` routes** delivered by spec-035. The page is a **Server Component composed entirely from the spec-035 `PersonaWorkspace` and audit-row read primitives**. Three small local components (`ManualRowRatioStrip`, `KpiLadder`, `StaleTelemetryBanner`) are composition-only — **no new chart libraries, no net-new UI primitives, no new design tokens**.

## Rationale

- Honours this spec's Clarification 3 verbatim.
- Preserves SC-009 ("zero net-new dashboards, chart libraries, or infrastructure components").
- Reuses the existing JWT/AppRole middleware (10 AIIMS roles + system-administrator from spec-035 Q1) — nothing new to authenticate.
- Composition-only keeps the page easy to test (Vitest + Playwright + axe-core) and easy to retire.

## Alternatives Considered

- **Standalone micro-frontend with Recharts/Visx** — rejected: violates SC-009; doubles auth surface.
- **Embed in an existing dashboard sub-route** — rejected: breaks the executive's "single page" mental model (FR-021, SC-008) and crowds the spec-035 dashboard tiles.
- **Pure Markdown rendering with no React state** — rejected: the live `manual_row_ratio` strip needs an `aria-live="polite"` region (NN-3) which requires a client component.

## Consequences

- Future evidence-pack additions extend the existing components rather than introduce new chart libraries.
- The KPI ladder is text-first; future visualisation work must justify the dependency cost against SC-009.
