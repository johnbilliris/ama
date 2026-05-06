# Spec-035 — Web Application Capstone Closure

## Specification (top-level brief — feed this to `speckit.specify` and to all agent panels)

The previous specification (spec 034) **validated** the AMA web application against the capstone objectives by authoring a 111-spec Playwright suite, a depth-profile contract, a coverage trace, and a gap register. That validation found that the web application is structurally present (routes load, audit plumbing emits) but **lacks the workflow depth required to satisfy the capstone outcomes** for many personas, jurisdictions, and cross-sector scenarios. The Playwright suite is now wired correctly; the next gate is the **web application itself**.

The KEY REQUIREMENT for this specification is to **close the gaps in the web application** at `apps/web/` so that, when the spec-034 web-coverage suite is executed end-to-end, every capstone outcome assertion (SC-001..SC-011) passes against real UI state changes — not against bailing stubs or seed-only echo. Out of scope: changing the validation suite itself, changing the constitution, expanding to Asia-Pacific personas (deferred to spec-028 follow-on).

## Hard inputs (gap source-of-truth)

The spec-035 specification MUST be derived from the following spec-034 artefacts:

1. `specs/034-webapp-capstone-coverage/spec.md` — FR-002, FR-009..FR-018, FR-028, FR-029, FR-030, SC-001..SC-012
2. `specs/034-webapp-capstone-coverage/contracts/outcome-evaluator.contract.md` — FR-028 evaluator surface (currently dev/test-only)
3. `tests/e2e/web-coverage/_lib/depth-profiles/_schema.json` + the 68 `{persona-id}.depth.yaml` files — defines the workflow depth each persona needs the UI to support
4. `<session>/files/agent-review/consolidated-review.md` — the parent-validated 85-agent merit register
5. The 13 cycle-1 net-new specs (T187..T199) — each one names a capstone behaviour the UI does not yet support
6. `apps/web/src/` — the current authoritative source of UI capability; spec-035 must enumerate the **delta** between it and (3)

## Acceptance bar

The spec-035 specification is complete when:
- Every `test.fail()` candidate that was retired by spec-034 cycle-1 is **green** against the production UI (not via dev/test-only routes)
- The coverage trace at `tests/e2e/web-coverage/_artifacts/coverage-trace.json` shows ≥ 95 % of persona × outcome × hazard tuples in `pass` state when run against `https://app-ama-zo6bb5.azurewebsites.net/` (production endpoint)
- The gap register at `specs/034-webapp-capstone-coverage/gap-register.json` contains zero `Open` entries with severity ≥ HIGH and no entry has `iteration_count` > spec-034's FR-024 limit
- The capstone evaluator endpoints (`/api/outcomes/sc-{001..005}/evaluate`) and audit-list endpoint (`/api/audit/list`) are reachable in production, not just in dev/test, with appropriate RBAC + auth (Q25/Q29 supersede)

## Workflow

The user will run all 9 steps from the original capstone-validation prompt against this spec, including the all-agent review loop. Each panel's brief is provided in this folder:

- `operational-brief.md` (10 operational agents)
- `sector-eastern-brief.md` (NSW + VIC + QLD agents)
- `sector-southwest-brief.md` (SA + WA + TAS agents)
- `sector-tc-brief.md` (ACT + NT + Commonwealth + cross-sector agents)
- `technical-brief.md` (17 technical agents)

## Constraints

- **Azure-only**: no third-party hosted services. New AI capabilities go through Microsoft Foundry. Identity stays on Microsoft Entra ID. AU data sovereignty (australiaeast) holds for all new resources.
- **AVM-first**: all new infrastructure goes through Azure Verified Modules (Bicep) — no hand-rolled `Microsoft.*` resources unless an AVM does not yet exist for the type.
- **No regression of spec-034**: the validation suite at `tests/e2e/web-coverage/` is read-only for spec-035 implementers. If a depth-profile assertion is wrong, the fix is to amend the spec-034 depth-profile YAML, not to weaken the spec-035 implementation.
- **Constitution v1.2.0 binds**: NN-1..NN-5 (sovereignty, append-only audit, accessibility, multilingual, offline-capable) and QG-1..QG-3 (TDD, evidence-bound, immutable evidence) are non-negotiable.
- **Out-of-scope** (mirrors spec-034 OOS): no new persona inventory beyond the 68 already in FR-002; no Asia personas; no rewrite of the Playwright harness; no changes to the seed-data shape (additive only).
