# Phase 0 Research — Capstone Evidence Pack

**Spec**: [`spec.md`](./spec.md) · **Plan**: [`plan.md`](./plan.md) · **Date**: 2026-05-11

This document records the five research notes that resolve every non-trivial decision in the implementation plan. Each note follows the **Decision / Rationale / Alternatives** format and cites the synthesised 17-persona technical-cohort input (`<session>/files/step4-tech-synthesis.md`) where applicable.

All four spec-level `Clarifications` (FR-021, FR-024, FR-037, FR-037+FR-038) were resolved at spec-time; **no `NEEDS CLARIFICATION` markers remain**.

---

## RES-01 — Schema strategy

**Decision**: Express each artefact as a **JSON Schema draft 2020-12** document under `packages/schemas/spec_037/`, with a corresponding **Pydantic v2** model under `packages/domain/src/domain/models/`. Extend the existing `signal-envelope.schema.*` governance pattern (the same dual-export contract used by `packages/schemas/spec_035/` and `packages/schemas/spec_036/`).

**Rationale**:

- AI/ML Engineer persona requires structured JSON with confidence/provenance/timestamps and machine-readable fallback templates — JSON Schema + Pydantic v2 gives this directly.
- Data Engineer persona explicitly requested extending the `signal-envelope.schema.json` governance pattern, partitioning artefact rows by `organisation_id` / `jurisdiction_id` where applicable, and contract-testing every schema change.
- API Architect persona requires contract-first specs with RFC7807 error envelopes and provenance metadata in responses — JSON Schema generates these consistently.
- Aligns with how spec-035 and spec-036 were shipped: contract tests under `tests/contract/spec_03X/test_schemas.py`, Pydantic codegen via `make schemas`, no tooling change required.

**Alternatives considered**:

- **OpenAPI as the primary contract** — rejected: the artefacts themselves are the contract, not their HTTP wire format; OpenAPI for the read API is a thin layer on top of the JSON Schemas (`contracts/openapi.evidence-pack.yaml`).
- **YAML-only artefacts** — rejected: harder to validate at scale, harder for the executive page to consume, breaks parity with the spec-035/spec-036 pattern.
- **Bespoke per-artefact schema flavours** — rejected: increases contract drift surface; mirroring the established `spec_03X/` layout costs nothing and reuses tooling.

---

## RES-02 — Governance-Hub information architecture

**Decision**: Use a **flat-per-artefact directory layout** under `docs/governance-hub/<artefact>/{name}.{md,json}`, with the existing `docs/governance-hub/index.md` extended to link the five artefacts. Risk Register stays under `docs/risk-register/` (preserving the existing `RISK-AOAI-001.md` path so prior back-citations remain valid). Feature-Value Ledger stays under `specs/shared/` so the inverse relationship to `capstone-metric-trace.md` is co-located.

```text
docs/risk-register/                                  # PRESERVED location
├── index.md                                         # NEW roll-up
├── schema.json
├── RISK-AOAI-001.md                                 # PRESERVED file
└── RISK-*.md

docs/governance-hub/
├── index.md                                         # EXTENDED with 5 links
├── adoption-roadmap/{roadmap.md, roadmap.json}
├── executive-kpi/{surface.md, surface.json}
├── rai-register/{responsible-ai-register.md, responsible-ai-register.json}
└── feature-value-ledger/tradeoff-log.md             # ADR log

specs/shared/
├── capstone-metric-trace.md                         # EXTENDED with self-flag row
└── feature-value-ledger.{md,json}                   # NEW (inverse of capstone-metric-trace.md)
```

**Rationale**:

- UX Designer persona: scannable, severity-distinct, degraded-mode aware — flat layout means each artefact's URL is predictable and linkable from emails/PDFs.
- Compliance Auditor persona: regulator-facing — auditors prefer "one folder per artefact, both human-readable and machine-readable" over deeply nested structures.
- Preserves the existing `docs/risk-register/RISK-AOAI-001.md` path (FR-012) so all prior citations remain valid.
- The Feature-Value Ledger sits alongside `capstone-metric-trace.md` because they are **inverses of each other** (FR-034); co-location keeps the cross-link single-hop.

**Alternatives considered**:

- **Nested under `docs/governance-hub/evidence-pack/<artefact>/`** — rejected: adds a layer with no semantic benefit; lengthens every URL and breaks the established `governance-hub/<topic>/` pattern.
- **Move the existing risk register under `governance-hub/`** — rejected: would invalidate prior back-citations and forces an unnecessary migration.
- **Single mega-document** — rejected: violates UX scannability and breaks per-artefact schema validation.

---

## RES-03 — Web-shell composition for the Executive KPI page

**Decision**: Implement `apps/web/src/app/governance/executive/page.tsx` as a **Next.js 15 Server Component** that composes the existing `PersonaWorkspace` and audit-row read primitives delivered by spec-035 (`apps/web/src/app/governance/dashboard/{audit,compliance,readiness,recovery,risk}/`). Two new local components — `_components/ManualRowRatioStrip.tsx` (live-region accessible) and `_components/KpiLadder.tsx` — are **composition-only**: no new chart libraries, no new global UI primitives, no new design tokens.

**Rationale**:

- This spec's Clarification 3 explicitly locks the route as a sibling of `/governance/dashboard/{audit,compliance,readiness,recovery,risk}` and forbids net-new UI primitives.
- Spec-035 Q1 locks the AppRole inventory; the executive page reuses the same JWT/AppRole middleware and the spec-035 `PersonaWorkspace` shell — there is nothing new to authenticate.
- UX Designer + Software Developer personas: composition-only keeps the page easy to test (Vitest snapshot + Playwright smoke) and easy to retire if priorities shift.
- Accessibility Tester persona: the live-region pattern (`aria-live="polite"`) on the `manual_row_ratio` strip is the established pattern from spec-035's stale-telemetry banner; reusing it guarantees axe-core parity.
- SC-009 ("zero net-new dashboards, chart libraries, or infrastructure components") is preserved by construction.

**Alternatives considered**:

- **Standalone micro-frontend** — rejected: violates SC-009, doubles the auth surface.
- **Embed in an existing dashboard sub-route** — rejected: breaks the executive-leader's "single page" mental model (FR-021, SC-008) and crowds the spec-035 dashboard tiles.
- **Charting library (e.g., Recharts, Visx)** — rejected: explicitly forbidden by SC-009 and Clarification 3; KPI cards + textual ladders are sufficient for the executive surface.

---

## RES-04 — CI publication-gate strategy

**Decision**: Add a single new GitHub Actions job `evidence-pack-publication-gate` to `.github/workflows/ci.yml`, running on `ubuntu-latest` after the existing `quality` job. The job runs four checks **in this order, fail-fast**:

1. **Schema validation** — every `*.json` sidecar under `docs/risk-register/`, `docs/governance-hub/{adoption-roadmap,executive-kpi,rai-register}/`, and `specs/shared/feature-value-ledger.json` validates against its `packages/schemas/spec_037/*.schema.json`.
2. **Link check** — every back-citation in every artefact `*.md` resolves to an existing file/heading (extends the existing markdown link-checker); broken links fail the build (FR-008).
3. **`manual_row_ratio` recomputation + cap** — the gate parses each JSON sidecar, recomputes `manual_row_count / total_row_count`, asserts it equals the value declared in metadata, and asserts `≤ 0.5` (FR-038 cap).
4. **`auditor_signoff` completeness** — for any artefact with `manual_row_ratio > 0.5`, the gate asserts a complete `{name, role, signoff_date_utc, basis}` block exists (FR-038 override path); incomplete blocks fail the build.

The gate is implemented as a single Python module under `scripts/evidence_pack_gate/` (importable for local dry-run) and invoked from CI via `python -m evidence_pack_gate`. Honours [`.github/instructions/governance-discovery.instructions.md`](../../.github/instructions/governance-discovery.instructions.md): the gate's own constraint description is added to the governance discovery index in the same PR that introduces it.

**Rationale**:

- Infrastructure/DevOps persona: extends existing pipeline, no net-new runners, pnpm + uv tooling already in CI.
- QA/Test Engineer persona: contract + integration test boundary — the gate is the integration test for the publication contract; per-FR contract tests live alongside in `apps/api/tests/contract/spec_037/`.
- Compliance Auditor persona: a single named CI job is auditor-friendly ("show me where the cap is enforced" → "this job, this commit").
- SRE persona: gate failure rate emits as a custom App Insights metric (`evidence_pack.publication_gate.failure_rate`); alert fires if rate > 5% over a 24-hour window.

**Alternatives considered**:

- **Pre-commit hook only** — rejected: bypassable; auditors require a CI-side gate.
- **Four separate jobs** — rejected: increases CI minutes and obscures the single "is the pack publishable?" question.
- **Run inside the existing `quality` job** — rejected: `quality` is broad and slow; isolating the gate gives clearer signal and shorter feedback when only artefact files change.

---

## RES-05 — `manual_row_ratio` measurement strategy

**Decision**: Compute `manual_row_ratio` **server-side at publish time** by walking the JSON sidecar's `rows[]` array and counting entries where `provenance.tag == "manual"`. The ratio is written to the artefact's metadata block (`{ manual_row_count, total_row_count, manual_row_ratio }`) and emitted as the App Insights custom metric `evidence_pack.manual_row_ratio` with dimensions `{ artefact_id, publication_id, environment }`. Client UIs (the executive page, the read-only API consumers) **never recompute** the ratio — they read the metadata block and trust it because the publication-gate has already validated it.

**Rationale**:

- SRE persona: a single server-side computation eliminates "client and server disagree" failure modes and gives one number that powers both UI display and alerting.
- Compliance Auditor persona: the metadata block is part of the artefact's tamper-evident snapshot in Blob (PD-037-04); the computed value, the input rows, and the auditor sign-off (if any) all live in the same immutable snapshot.
- AI/ML Engineer + API Architect personas: the ratio is part of the response provenance envelope (`provenance.metrics.manual_row_ratio`), consistent with the spec-036 RAG-citation envelope pattern.
- Honours FR-037 ("`manual_row_count`, `total_row_count`, and `manual_row_ratio` (= `manual_row_count / total_row_count`, range 0..1)") and FR-038 (cap + override) by ensuring the same number drives both UI and CI gate.

**Alternatives considered**:

- **Client-side computation** — rejected: clients could disagree with the gate; ratio shown to the executive could differ from ratio used by the cap; auditability suffers.
- **Compute lazily on every API read** — rejected: wastes compute; allows drift between metadata block and runtime value; the source rows are immutable per publish, so one-time computation is correct.
- **Track manual rows via a side database table** — rejected: violates "evidence in git" principle (PD-037-01); creates a non-tamper-evident second source of truth.

---

## Summary of inputs honoured

The five research notes above directly honour the synthesised 17-persona technical-cohort input (`<session>/files/step4-tech-synthesis.md`):

- **AI/ML Engineer** → RES-01, RES-05
- **Data Engineer** → RES-01, RES-02
- **API Architect** → RES-01, RES-05
- **Solution Architect** → RES-01 (CQRS-lite + append-only audit preserved), PD-037-04
- **Security Engineer** → entire plan (AU-only, RBAC, no PII in logs)
- **Compliance Auditor** → RES-02, RES-04, RES-05
- **UX Designer** → RES-02, RES-03
- **Accessibility Tester** → RES-03
- **QA / Test Engineer** → RES-04
- **Chaos Engineer** → degraded-publication and degraded-retrieval validation in `tests/contract/spec_037/test_publication_gate.py` and `tests/e2e/web-coverage/governance-executive.spec.ts`
- **SRE Engineer** → RES-04, RES-05 (publication SLO + executive page latency)
- **Infrastructure / DevOps** → RES-04 (no net-new resources; CI extension only)
- **Azure Principal Architect** → confirmed AU-East availability for all reused resources; no carve-out required
- **Docker & Container Engineer** → no container changes needed; existing `ca-api-ama` revision serves the new routes
- **Software Developer** → RES-01, RES-03
- **Principal Engineer** → entire plan kept lean; no unnecessary abstraction; meaningful test coverage; trade-offs documented in the four ADRs PD-037-01..PD-037-04
- **Product Owner / BA** → measurable success metrics (SC-001..SC-011) + BDD traceability via `_traceability.csv` files
