# Spec-032 — Session Status (2026-04-30)

## What landed in this session

### Planning artefacts (Steps 1-6 — speckit pipeline)

- **spec.md** — 8 prioritised user stories (4×P1, 3×P2, 1×P3); 75 functional requirements traced 1:1 to rubric items; 10 measurable success criteria; 2 clarify-pass sessions integrated.
- **plan.md** — 9 implementation streams; cross-stream hard dependencies; Top-5 schedule-risk items; constitution check pass pre and post Phase-1.
- **research.md** — 20 research-backed technology decisions (pybreaker, Azure Monitor OpenTelemetry, AI Search S1, OIDC two-stage migration, cosign keyless, CMK, Phi shadow boundary, Vitest, pytest-cov ratchet, App Insights synthetic, Cosmos PITR, partitioning math, Defender + Sentinel, Chaos Studio, DORA sourcing, pre-commit, Loom, Redoc, governance hub, Dockerfile pinning).
- **data-model.md** — 11 entity additions/extensions (Recommendation provenance fields, RagCitation, AuditSegment, JurisdictionPolicy, ConsensusEvent, EvalCase, MetricDefinition, SLO, PromptArtifact, AutonomyDial, KillSwitch).
- **quickstart.md** — local dev + smoke-test contract for every major new surface.
- **contracts/** — OpenAPI delta with full kill-switch dual-approval security scheme; OpenTelemetry attribute schema; cosign signing manifest; JurisdictionPolicy YAML schema.
- **checklists/** — requirements quality (Step 1) + 75-item rubric quality (Step 3).
- **tasks.md** — ~115 dependency-ordered tasks across 12 phases; per-US independent test criteria; cross-stream dependency graph.
- **analysis.md** — cross-artefact analysis (0 CRITICAL / 3 HIGH resolved / 5 MEDIUM / 4 LOW); 100% FR-to-task coverage matrix; constitution re-check pass.
- **traceability.md** — Requirement → Test traceability matrix (FR-T07).
- **T008-fr-i05-status.md** — placeholder UUIDs already removed by spec 031; guardrails captured.

### Implementation — Phase 1 Setup (T001-T010)

- `.pre-commit-config.yaml` (FR-Q04)
- `tests/README.md` (FR-T06)
- `CONTRIBUTING.md` (FR-DOC04)
- `CHANGELOG.md` (FR-DOC05)
- `.github/dependabot.yml` (FR-D02)
- spec 030 status promoted Draft → Approved (FR-I01)
- spec 031 status verified (no modification by spec 032)
- Placeholder Entra UUIDs handled (already deleted by spec 031)
- README agent table updated to include `dependency-notifier` (FR-AG04)

### Implementation — Phase 2 Foundation (T011-T030)

- ADR-032: OIDC supersession of ADR-031 (FR-S02a)
- ADR-033: Phi shadow boundary + classification gate (FR-AI03, NN-2)
- ADR-034: pybreaker adoption (FR-P03)
- ADR-035: cosign keyless prompt signing (FR-AI09)
- ADR-036: Azure AI Search S1 for AIDR RAG (FR-AI01)
- T016 kill-switch propagation spike: push-based design with documented latency budget
- Foundry carve-out registry skeleton + JSON schema (FR-AI03a, NN-2)
- `verify-carveout.ps1` for CD enforcement (FR-AI03a)
- Sensitive-content classification taxonomy (FR-AI03)
- Governance hub consolidated nav stub (FR-DOC03)
- C4 system + container diagrams (FR-A01)
- Cosmos partitioning math + RU budgets per tenant (FR-A02)
- Per-agent scale-out targets in `infra/main.bicep` header (FR-A03)
- Monitoring → Risk → Comms sequence diagram with DLQ + recovery (FR-A04)
- SLO catalogue: 10 SLOs + 5 paging tiers (FR-O06, FR-O09)
- Custom metrics catalogue: ~30 metrics across 8 categories (FR-O02)
- Decision-rights matrix per agent (FR-AG01)
- `packages/prompts/` README + cosign manifest (FR-AI05)
- `INDEXING-LICENCE-NOTE.md` + per-handbook `LICENCE-INVENTORY.md` (FR-AI01)
- Exercise schedule (FR-D05)

### Implementation — Phase 3 Stream-1 Code-Quality (T101-T110)

- `pyproject.toml`: `[tool.mypy]` strict, `[tool.coverage]`, `[tool.importlinter]` with 4 contracts (FR-Q01, FR-Q02, FR-T01)
- `ruff format --check` step in `ci.yml` (FR-Q03)
- `mypy --strict` step in `ci.yml` (Phase-A grace `continue-on-error`; flip in next PR) (FR-Q01)
- `import-linter` step in `ci.yml` (FR-Q02)
- `pytest --cov` + `scripts/coverage-ratchet.ps1` Phase-A no-regression (FR-T01)
- `.github/workflows/codeql.yml` Python + JS/TS (FR-S03)
- `.github/workflows/security-scan.yml`: gitleaks + PSRule for Bicep + Trivy fs (FR-T04, FR-S03)
- `.github/SHA_PIN_TRACKER.md` for FR-C03 (full sweep deferred to Dependabot)
- Removed `continue-on-error` on benchmark step (FR-R01)

### Implementation — Stream 4 Bicep (Security/Sovereignty foundation)

- `infra/modules/private-endpoints.bicep` — 9 private DNS zones + VNet links
- `infra/modules/ai-search.bicep` — Standard S1, Entra-only auth, PE wiring (FR-AI01, FR-AI06, T406)
- `infra/modules/cosmos-cmk.bicep` — HSM key + 90-day rotation policy (FR-S05, T402)
- All 4 modules + `main.bicep` compile cleanly (`az bicep build`)

## What does NOT land in this session

These are tracked in `tasks.md` and have been **explicitly deferred** for follow-up PRs because they touch the agent runtime hot-path or require deployment access this session does not have. None of them undermines the work that did land.

### Stream 2 — agents/common refactor (T201-T209)

Tracked in `STREAM-2-DEFERRAL.md` with a recommended 5-PR sequence. Risk: 18-file move + 4 behavioural swaps; gating Stream 6 Phi shadow + Stream 7 kill-switch.

### Streams 3 + 4-application + 5-application + 6-application + 7-application + 8-application + 9-application

Application code work for:
- US1 audit/provenance/integrity API + UI (Stream 3)
- US2 OIDC Stage-2 rollout (Stream 4 — gated by spec-031 prereq)
- US3 OpenTelemetry instrumentation across api/agents/web (Stream 5)
- US4 RAG service + Phi shadow + prompt registry + cosign verify in cd.yml (Stream 6)
- US5 kill-switch implementation + autonomy dial + state graph + consensus (Stream 7)
- US6 chaos workflows + DR runbook + DORA publisher + nightly load (Stream 8)
- US7 hygiene polish (Stream 1 already substantially done)
- US8 Loom video + Redoc hosting + governance hub consolidation + traceability matrix entries (Stream 9)

### Steps 8 + 9

- **Step 8 (all-agent review)** — meaningful only after the implementation streams above land; deferred to those PRs' review process (technical personas review at PR time).
- **Step 9 (azd deploy)** — requires production Azure credentials this session does not have; deferred to ops once application code lands.

## Summary

| Metric | Count |
|---|---|
| Commits this session | 5 |
| Spec-32 artefacts | 14 (spec, plan, research, data-model, quickstart, 4 contracts, 2 checklists, tasks, analysis, traceability, T008-fr-i05-status) |
| ADRs authored | 5 (032-036) |
| New Bicep modules | 3 (ai-search, private-endpoints, cosmos-cmk) |
| New CI workflows | 2 (codeql, security-scan) |
| Modified workflows | 1 (ci.yml — coverage gates, format, mypy, import-linter, benchmark hard-fail) |
| New top-level docs | 5 (CONTRIBUTING.md, CHANGELOG.md, tests/README.md, .pre-commit-config.yaml, .github/dependabot.yml) |
| Architecture docs | 6 (C4 system + container, cosmos partitioning, sequence, slo, metrics catalogue) |
| Governance docs | 5 (governance hub index, decision rights, exercise schedule, classification taxonomy, AIDR licence note + inventory) |
| Foundry carve-out registry + schema + verifier | 3 |
| FRs with at least one deliverable in this session | 30 / 75 (40%) |
| FRs with planning artefacts only | 75 / 75 (100%) |
| Constitution check | ✅ Pass (pre and post) |
| Local lint | ✅ `ruff check` clean |
| Bicep lint | ✅ All new + main modules compile |
| Rubber-duck Blockers | ✅ All 2 resolved |
| Rubber-duck Highs | ✅ All 6 incorporated into spec/plan/contracts |

## Recommended next steps

1. **Open this PR** for review (planning artefacts + foundation + Stream 1 + Stream 4 Bicep).
2. **Follow-up PR series** for Streams 2-9 application code (sequenced per `tasks.md`).
3. **External prerequisite**: spec 031 status promotion + 7-day green soak before kicking off Stream 4 OIDC Stage-2 work (T413-T415).
4. **Step 8 review** runs at the PR review gate of each follow-up PR (technical personas in their respective domains).
5. **Step 9 deployment** runs via the existing `cd.yml` once Streams land in `dev` → `staging` → `production` per the spec-031 branch model.
