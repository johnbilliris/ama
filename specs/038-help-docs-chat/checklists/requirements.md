# Specification Quality Checklist: In-Product Help Documentation & Grounded Chat Assistant

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-05-11
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain — Pass 1 (2026-05-11) auto-resolved both prior markers (Help UI localisation; chat grounding freshness); Pass 2 (2026-05-11) auto-resolved 8 residual ambiguities (snapshot publication mechanics, stale-screenshot governance, per-tenant support handoff + SLA, persona-context resolution, conversation persistence + retention, negative-feedback closure, degraded-mode cache scope + TTL, accessibility lang-attribute hygiene) and confirmed Observer-Auditor read-only enforcement was already clear. See spec "Clarifications" section.
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Persona Coverage (feature-specific)

- [x] All 10 operational personas listed with help needs
- [x] All 6 sector clusters listed with help needs
- [x] Read-only role (Observer-Auditor) explicitly handled in chat/help guidance
- [x] PIO multilingual & accessibility needs addressed

## Chat Safety (feature-specific)

- [x] Grounding sources explicitly enumerated (Help, `docs/corpus/**`, `docs/aidr/**`, `specs/**`)
- [x] Out-of-scope refusal behaviour specified
- [x] Citation requirement on every factual claim
- [x] Tenant isolation by design
- [x] PII redaction at gateway (per spec-036 pattern)
- [x] Australian data residency
- [x] Append-only audit log of chat interactions
- [x] Degraded-connectivity behaviour defined

## Notes

- Pass 1 (2026-05-11) auto-resolved both retained `[NEEDS CLARIFICATION]` markers using the constitution + `docs/corpus/**` + `docs/aidr/**` + prior specs (001–037) authority hierarchy:
  1. **Help UI localisation** → English-only at launch (Constitution V applies to public-facing warnings, not internal operator UI; spec already lists Help-UI localisation as out-of-scope).
  2. **Chat grounding freshness** → Help-approved snapshot only (Constitution I + V-B.3 + Quality Gates require trusted/reviewed sources for safety-relevant answers; aligned with spec-005 governance and spec-036 curated RAG model).
- Pass 2 (2026-05-11) re-read the spec end-to-end and auto-resolved 8 residual material ambiguities introduced during Pass 1 / left unspecified by the original draft, plus confirmed 1 area was already clear:
  1. **Snapshot publication mechanics** → dual sign-off (Help-content owner + safety/governance lead), immutable snapshots, rollback by re-publishing previous snapshot id within spec-029 5-minute SLO, explicit deprecation notice on superseded deep links (FR-011b/c/d).
  2. **Stale-screenshot governance** → deterministic `screen_id_hash` (route id + ordered DOM-element fingerprints of callout anchors); grace period = 1 release cycle; never auto-removed (FR-010a/b).
  3. **Per-tenant support handoff** → required record fields (channel, address, hours, incident-mode override); SLA = 5 min during NEMA-Level-3, 4 business-hours otherwise; SLA breach emits audit event (FR-023a/b).
  4. **Persona-context resolution** → IdP role claim default + persona switcher override; multi-role users see union of tiles ordered by authority rank (spec-021 FR-025 pattern); chat uses only the *active* persona (FR-027/028).
  5. **Conversation persistence** → Cosmos DB AU East per-tenant; 30-day transcript retention (operational class — strict spec-001 NFR-002 cap); 7-year audit-log retention (APP 11 + spec-001 NFR-012); auto-purge (FR-029/029a).
  6. **Negative-feedback closure** → queued in tenant-scoped content-review backlog; ≥3 in 30 days auto-promotes to "needs review"; never auto-disables answers (Constitution Principle I no-silencing) (FR-022a).
  7. **Degraded-mode cache** → previously-viewed articles + glossary + curated FAQ; 14-day TTL; ≤500 MB shared with spec-036 FR-RAG-LS-02; chat / uncached search / corpus retrieval all unavailable; reconnect emits audit-logged refresh (FR-026a/b).
  8. **Accessibility lang-attribute hygiene** → embedded non-English fragments (Aboriginal & Torres Strait Islander language, place names, AIIMS-adjacent terms) MUST carry `lang` attribute per WCAG 2.2 SC 3.1.2 (FR-009a).
  9. **Observer-Auditor read-only enforcement** → confirmed already clear; FR-025 sufficient (observers may query freely; restriction is on instructed *actions*, not *questions*).
- All resolutions and citations are recorded in the spec's `## Clarifications` section under `### Session 2026-05-11` (Pass 1) and `### Session 2026-05-11 (Pass 2 — residual ambiguities, auto-resolved)`.
- Spec is ready for `/speckit.plan`.
