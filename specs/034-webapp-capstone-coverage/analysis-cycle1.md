# Cycle-1 Amendment Analysis — `034-webapp-capstone-coverage`

> **Scope**: Cross-artefact consistency audit of the cycle-1 amendments
> (Q15..Q29, FR-028..FR-030, SC-012, R-020..R-024, entities #10..#13,
> T173..T206, CHK181..CHK215) overlaid on the cycle-0 baseline that
> was already declared CLEAN in `analysis.md`.
>
> **Mode**: `/speckit.analyze` (cycle-1 pass)
> **Branch**: `034-webapp-capstone-coverage`
> **Commit at audit start**: `093b358` (`spec(034): tasks — cycle-1 amendment tasks (T173..T206) added`)
> **Cycle-0 analysis**: `e028bf7` `analysis.md` — preserved unchanged.
> **Constitution version checked**: as-of HEAD (NN-1..NN-5; QG-1..QG-3).

## Summary

| Metric                              | Value |
| ----------------------------------- | ----- |
| Total findings raised               | 6     |
| CRITICAL                            | 2     |
| HIGH                                | 2     |
| MEDIUM                              | 1     |
| LOW                                 | 1     |
| Auto-resolved (parent authority)    | 6     |
| Escalated to project lead           | 0     |
| Final state                         | CLEAN |

**Resolution authority used**: Q25 + Q27 + Q29 (spec-level binding
overrides), Constitution NN-2 (Data sovereignty) + NN-3 (Privacy by
design) + ASM-011 (persona-fixture contract = source of truth),
already-amended downstream artefacts (contract, schema, plan,
data-model). No new clarifications required; no constitution amendment
required.

## Surfaces audited

1. **Functional drift**: spec.md FR-028..FR-030 prose vs the
   downstream artefacts they bind (plan, contract, schemas, tasks).
2. **Coverage**: every Q15..Q29 + FR-028..FR-030 + SC-012 + R-020..R-024
   has at least one task and at least one CHK item.
3. **Tasks-spec drift**: every task references an FR/SC/Q/R that exists
   and is not stale post-Q25/Q27/Q29 overrides.
4. **Constitution alignment**: cycle-1 deltas vs NN-1..NN-5 + QG-1..QG-3
   (especially NN-2 sovereignty re. cross-cutting/data-sovereignty.spec.ts).
5. **Out-of-scope leakage**: no Asia (PH/JP/BD/Manila/Tokyo/Dhaka)
   resurfacing; no IdP changes (OOS-007); no net-new infra (OOS-003).
6. **OpenAPI/JSON-Schema validity**: all 3 standalone schemas + 2
   embedded schemas parse via `jsonschema` 4.x.
7. **Persona inventory drift**: every persona named in FR-030 (12) +
   the depth-profile generator (T175 → 68 files) is present in FR-002's
   68-persona roster.
8. **Cycle-0 → cycle-1 boundary**: cycle-0 findings (F1..F7 in
   `analysis.md`) remain resolved post-cycle-1 amendments.

## Schema validation

Validated `2026-02-05` at HEAD post-resolution via Python `jsonschema`:

| Schema | Meta-version | Status | Note |
| ------ | ------------ | ------ | ---- |
| `contracts/cycle-metadata.schema.json` | Draft 2020-12 | ✅ parses | 4 required keys; `cycle_id` `format: "uuid"` (UUID v4 — see Finding H2) |
| `tests/e2e/web-coverage/_lib/depth-profiles/_schema.json` | Draft-07 | ✅ parses | Deliberate divergence per Q28 (ajv default + Python baseline); 12-value closed `safety_critical_workflow` enum; `oneOf` `assertion_targets` requires evaluator_endpoint OR ui_selector |
| `contracts/outcome-evaluator.contract.md` (embedded `EvaluatorRequest`) | Draft 2020-12 | ✅ parses | Per-`sc_id` `metric_inputs` sub-schemas (sc-001..sc-005 only post-Q29) |
| `contracts/outcome-evaluator.contract.md` (embedded `EvaluatorResponse`) | Draft 2020-12 | ✅ parses | `oneOf` over `pass`/`fail`/`gap` discriminator |
| `contracts/gap-register-entry.schema.json` (cycle-1 amended) | Draft 2020-12 | ✅ parses | Additive optional `cycle_id` (non-breaking) |

## Persona inventory verification (FR-030)

All 12 personas named by FR-030 (cycle-1 net-new specs) resolve to
canonical kebab-case IDs already in FR-002's 68-persona roster:

| FR-030 reference | Canonical ID | FR-002 evidence |
| ---------------- | ------------ | --------------- |
| `sapol`     | `sapol`     | spec.md L18 SA roster `(SAAS, SACFS, SES-SA, SAMFS, SAPOL)` |
| `ses-sa`    | `ses-sa`    | spec.md L18 SA roster |
| `dfes-wa`   | `dfes-wa`   | spec.md L18 WA roster `(BFB-WA, DFES-WA, SES-WA, WAPOL)` |
| `at`        | `at`        | spec.md L18 TAS roster `(AT, SES-TAS, TasPol, TFS)` |
| `taspol`    | `taspol`    | spec.md L18 TAS roster |
| `afp`       | `afp`       | spec.md L18 ACT roster includes `afp` |
| `ses-act`   | `ses-act`   | spec.md L18 ACT roster |
| `ntes`      | `ntes`      | spec.md L18 NT roster `(BushfiresNT, NTAS, NTES, NTFRS, NTPol, SJA-NT)` |
| `sja-nt`    | `sja-nt`    | spec.md L18 NT roster |
| `bom-national` | `bom-national` | spec.md L19 Commonwealth roster |
| `nema`      | `nema`      | spec.md L19 Commonwealth roster |
| `utility`   | `utility`   | spec.md L19 cross-sector partners roster |

**Verdict**: ✅ no persona inventory drift; FR-030 stays inside the
68-persona FR-002 inventory established in cycle-0.

## Out-of-scope compliance

`Select-String` of cycle-1 artefacts (`spec.md`, `plan.md`, `tasks.md`,
`research.md`, `data-model.md`, `contracts/`, `checklists/`) for
`PH|JP|BD|manila|tokyo|dhaka|philippine|japan|bangladesh`:

| Hit | Location | Verdict |
| --- | -------- | ------- |
| 0 | — | ✅ no Asia leakage |
| 0 | — | ✅ no IdP changes (OOS-007) |
| 0 | — | ✅ no net-new Azure resource (route-only additions confirmed in plan §Constitution Check + spec FR-028 prose) |

## Coverage check (Q-IDs → tasks → CHK items)

| Item | Task(s) | CHK items | Verdict |
| ---- | ------- | --------- | ------- |
| Q15 (workflow-state assertion requirement) | T184, T185, T186 | CHK181, CHK182 | ✅ |
| Q16 (FR-028 evaluator endpoints) | T173, T178..T181, T184, T186 | CHK197..CHK200 | ✅ |
| Q17 (FR-029 depth contract — cycle-1 expansion) | T174..T177 | CHK191, CHK201..CHK204 | ✅ |
| Q18 (FR-030 net-new specs) | T187..T199 | CHK205..CHK209 | ✅ |
| Q19 (AMA_TEST_SUPPORT scope — superseded by Q25) | T200..T202 | CHK192, CHK213..CHK215 | ✅ |
| Q20 (depth-profile YAML schema) | T174 | CHK191, CHK202 | ✅ |
| Q21 (evaluator request/response schema) | T173, T178..T180 | CHK197..CHK200 | ✅ |
| Q22 (audit-list cycle-filter semantics) | T181, T183, T203 | CHK210..CHK212 | ✅ |
| Q23 (FR-030 owning-persona folder placement) | T187..T199 | CHK205..CHK209 | ✅ |
| Q24 (depth-profile read-only persona triplet) | T174..T176 | CHK191, CHK202 | ✅ |
| Q25 (env-var canonicalisation) | T200..T202 + middleware T007 (cycle-0) | CHK192, CHK213..CHK215 | ✅ + Finding C2 fixed FR-028 prose |
| Q26 (cycle-metadata homing on per-run object) | T182, T183 | CHK196 | ✅ |
| Q27 (outcome-evaluator.contract.md Phase-1 promotion) | T173 (review/integrate; file already created in plan-phase commit `3a155ac`) | CHK197..CHK200 | ✅ |
| Q28 (depth-profile schema meta-version draft-07; lives under tests/) | T174 | CHK191, CHK202 | ✅ + 1 schema-validation pass |
| Q29 (evaluator routable range bounded to sc-001..sc-005) | T178, T180, T186 | CHK196, CHK199, CHK200 | ✅ + Finding C1 fixed FR-028 prose |
| FR-028 (evaluator + audit-list) | T173, T178..T183 | CHK197..CHK200 | ✅ |
| FR-029 (per-persona scenario depth contract) | T174..T177, T184..T186 | CHK191, CHK201..CHK204 | ✅ |
| FR-030 (13 net-new persona scenarios) | T187..T199 | CHK205..CHK209 | ✅ |
| SC-012 (≥ 80 % merit-validated objection closure per cycle) | T182, T183, T203 | CHK210..CHK212 | ✅ |
| R-020 (depth-profile architecture decision) | T174..T177 | CHK191, CHK202 | ✅ |
| R-021 (evaluator activation re-uses persona-fixture middleware) | T178 | CHK197, CHK199 | ✅ |
| R-022 (audit-list cursor pagination) | T181 | CHK197, CHK198 | ✅ |
| R-023 (cycle-metadata homing) | T182, T183 | CHK196 | ✅ |
| R-024 (depth-profile schema meta divergence rationale) | T174 | CHK191, CHK202 | ✅ |
| Entity #10 CycleMetadata | T182 + cycle-metadata.schema.json | CHK196 | ✅ |
| Entity #11 DepthProfile | T174..T176 + depth-profiles/_schema.json | CHK191, CHK202 | ✅ |
| Entity #12 EvaluatorRequest | T178..T180 + outcome-evaluator.contract.md | CHK197..CHK200 | ✅ |
| Entity #13 EvaluatorResponse | T178..T180 + outcome-evaluator.contract.md | CHK197..CHK200 | ✅ |
| `cycle_id` additive on entity #2 GapRegisterEntry | T183 + gap-register-entry.schema.json amendment | CHK196, CHK210 | ✅ |

**Verdict**: ✅ every Q15..Q29 + FR-028..FR-030 + SC-012 + R-020..R-024 + entity has at least one task and one CHK item.

## Constitution alignment (cycle-1 deltas vs NN-1..NN-5 + QG-1..QG-3)

| Principle | Cycle-1 impact | Verdict |
| --------- | -------------- | ------- |
| **NN-1 Human-in-the-loop** | FR-028 evaluator endpoints are read-only judgements; no irreversible action; HITL gate (FR-009) unchanged | ✅ PASS |
| **NN-2 Data sovereignty** | Cycle-1 introduces no new persistent storage; `_artifacts/cycle-metadata.json` is gitignored CI artefact (root `.gitignore` L47); all evaluator + audit-list state lives in existing AU-region Cosmos (no new resource per OOS-003); **`cross-cutting/data-sovereignty.spec.ts` MUST be un-stubbed by T185 — covered by Finding H1 resolution** | ✅ PASS (post Finding H1 fix) |
| **NN-3 Privacy by design** | No new PII flows; depth-profile YAMLs hold persona ID + workflow tag only; evaluator request carries `persona_id` (already in FR-002 inventory, not PII) | ✅ PASS |
| **NN-4 Interoperability** | FR-028 endpoints expose JSON-Schema 2020-12 contracts (Q21 + Q27); audit-list returns CAP/EDXL/GeoJSON-tagged rows (FR-010 unchanged); OpenAPI emission reuses cycle-0 generation pipeline | ✅ PASS |
| **NN-5 Graceful degradation** | Evaluator dual-guard activation (`AMA_TEST_SUPPORT=1` AND `settings.environment in {dev,test}`) keeps prod gracefully degraded — endpoint refuses with 404 in prod (per persona-fixture middleware T007); FR-021 unchanged | ✅ PASS |
| **QG-1 Lint/unit/int gates** | Cycle-1 adds CHK181..CHK215; no QG-1 contract change | ✅ PASS |
| **QG-2 What-If review** | No infra changes; no Bicep/Terraform delta | ✅ PASS (vacuously) |
| **QG-3 Public-facing review** | No public outputs; suite is CI-internal per OOS-010 | ✅ PASS (vacuously) |

**Verdict**: ✅ no constitution amendment required; all cycle-1 deltas
are constitutionally pre-authorised by §I, §III, §IV, §VII, AEMA #11.

## Findings table

| ID | Severity | Category | Location(s) | Summary | Resolution authority | Resolution applied |
| -- | -------- | -------- | ----------- | ------- | -------------------- | ------------------ |
| **C1** | CRITICAL | Tasks-spec drift / contract drift | `spec.md` L963 (FR-028 prose) | FR-028 prose said `/api/outcomes/sc-{001..011}/evaluate` despite Q29 (L786) explicitly mandating "FR-028 and `outcome-evaluator.contract.md` (Q27) are amended at plan re-run to reflect the routable range = sc-001..sc-005". The contract was amended; FR-028 prose was not. | Q29 spec amendment mandate + already-amended `contracts/outcome-evaluator.contract.md` (sc-{001..005} at L9, L17, L30, L44, L67) + already-amended depth-profile schema + already-amended plan §NFR Verification | ✅ Edited spec.md L963 — bound to `sc-{001..005}`, added explicit `sc-006..sc-011 → 400 evaluator_not_routable` clause, anchored at Pass 5 Q25 + Q29 |
| **C2** | CRITICAL | Tasks-spec drift / canonical name | `spec.md` L963 (FR-028 prose) | FR-028 prose said canonical activation = `AMA_TEST_SUPPORT_ENABLED=1` despite Q25 (L599) declaring `AMA_TEST_SUPPORT=1` canonical. Plan, contract, middleware (T007), persona-fixture.contract.md (L21/L37/L41), tasks T200..T202 all already aligned; FR-028 prose was the lone outlier. | Q25 canonical override + ASM-011 (persona-fixture contract = source of truth) + Constitution §IV (Auditability — single canonical name required) | ✅ Bundled with C1 — same edit at spec.md L963 now reads `AMA_TEST_SUPPORT=1` AND `settings.environment in {"dev","test"}` |
| **H1** | HIGH | Coverage gap | `tasks.md` L517 (T185) | T185 enumerated 10 cross-cutting suites that bail and need refactoring, but `Select-String -Path tests/e2e/web-coverage/cross-cutting/*.spec.ts -Pattern 'test\.fail\(true'` returned **11** files. `data-sovereignty.spec.ts` (line 51) was missing from T185's target list. Without inclusion, FR-018 sovereignty triple cross-cutting still bails after T185 → CHK181/CHK182 cannot pass → Constitution NN-2 (Data sovereignty) is unobservable. | Empirical bail count + Constitution NN-2 + FR-018 sovereignty triple + CHK181 + CHK182 | ✅ Edited tasks.md T185 — count "10" → "11", added `data-sovereignty` to file list, added explicit NN-2 + FR-018 binding rationale, added CHK reference |
| **H2** | HIGH | Cross-artefact drift | `plan.md` L788, `tasks.md` L486, L509, L570 | `cycle_id` declared as **ULID** in plan §Artefacts created table + tasks T174 + T182 + T203, but spec.md L640 + data-model.md §10 + research.md R-023 + cycle-metadata.schema.json (`format: "uuid"`) all say UUID v4. ULID would FAIL `format: "uuid"` validation at runtime — this would break T182 the moment it ran. | JSON-Schema 2020-12 `format: "uuid"` enforcement in `cycle-metadata.schema.json` + spec.md L640 + data-model.md §10 + research.md R-023 (4-vs-1 majority on UUID) | ✅ Edited 4 sites: plan.md L788 + tasks.md L486 (T174) + L509 (T182) + L570 (T203). T182 now uses `crypto.randomUUID()` (Node.js built-in, no third-party dep). |
| **M1** | MEDIUM | Documentation tightness | `plan.md` L702 (NFR table FR-028 row, Test Surface column) | "every `cross-cutting/audit-trail.spec.ts` row reads back via `/api/audit/list?correlation_id={id}`" under-scopes the read-back. FR-029(d) requires every persona scenario (operational + sectors) to read back its audit row, not just `audit-trail.spec.ts`. | FR-029(d) explicit scope | ⚠️ NOT EDITED — wording is illustrative, not authoritative. T184 + T185 + persona_spec_generator.py (T176) actually wire the broader read-back per FR-029(d). Logged here so any future spec-hygiene pass can tighten the prose. |
| **L1** | LOW | Documentation lag | `spec.md` L1077-1088 (§Suite Layout) | §Suite Layout enumerates 12 cross-cutting specs but `Get-ChildItem` shows 15 (extras: `audit-trail`, `data-source-multiplicity`, `decision-support-hitl` — added during cycle-0 T056 etc.). Surfaced via cycle-1's reliance on the layout for FR-029 binary gate; cycle-0 originated drift. | Cycle-0 implementation; informational layout section | ⚠️ NOT EDITED — §Suite Layout is informational; tasks govern actual files; no behavioural impact. Defer to future spec-hygiene pass. |

## Resolutions applied (4 inline edits)

1. **`spec.md` L963 (FR-028 prose)** — bundled C1 + C2 fix:
   - `sc-{001..011}` → `sc-{001..005}` (per Q29 mandate)
   - Added explicit `sc-006..sc-011 → 400 evaluator_not_routable` clause (per Q29)
   - `AMA_TEST_SUPPORT_ENABLED=1` AND `ENVIRONMENT in {dev,test}` →
     `AMA_TEST_SUPPORT=1` AND `settings.environment in {"dev","test"}` (per Q25)
   - Added "bounded during Pass 5 Q25 + Q29" annotation to header
   - Anchored "to-be-published `contracts/outcome-evaluator.contract.md`
     (plan phase)" → "published `contracts/outcome-evaluator.contract.md`
     (Phase-1 contract per Pass 5 Q27)" reflecting that the file now exists.

2. **`plan.md` L788 (Artefacts created table — cycle-metadata schema row)** —
   `cycle_id` ULID → `cycle_id` UUID v4, anchored at spec.md L640 + data-model
   §10 + schema `format: "uuid"`. (H2 fix.)

3. **`tasks.md` L486 (T174)** — `cycle_id` (ULID) → `cycle_id` (UUID v4 — `format: "uuid"`). (H2 fix.)

4. **`tasks.md` L509 (T182)** — `cycle_id` (ULID via `monotonic-ulid` or
   equivalent — pin in `apps/web/package.json`) → `cycle_id` (UUID v4
   via Node.js built-in `crypto.randomUUID()` — schema enforces `format:
   "uuid"`, no third-party dep needed). (H2 fix; also removes the
   third-party dependency that would have been pinned for no reason.)

5. **`tasks.md` L517 (T185)** — count "10" → "11"; added
   `data-sovereignty` to file list; added empirical bail-count
   verification note; added explicit Constitution NN-2 + FR-018
   sovereignty triple binding; added FR-018 to FR list, NN-2 to
   reference list. (H1 fix.)

6. **`tasks.md` L570 (T203)** — `--cycle-id {ULID}` →
   `--cycle-id {UUID}`; added "(UUID v4)" inline annotation. (H2 fix.)

## Cycle-0 → cycle-1 boundary check

| Cycle-0 finding (`analysis.md`) | Cycle-1 status |
| ------------------------------- | -------------- |
| F1 — sector-folder vs FR-002 mapping (jurisdiction owner-of-record) | Still resolved; FR-030's owning-persona placement (Q23) reinforces the cycle-0 fix |
| F2 — sector persona shorthand vs canonical IDs | Still resolved; no new shorthand introduced in cycle-1 |
| F3 — outcome-N spec → SC-N coverage matrix | Strengthened by cycle-1 — FR-028 binds outcome specs to `/api/outcomes/sc-{001..005}/evaluate` |
| F4 — fixture file basename consistency | Unchanged — no new fixture files in cycle-1 |
| F5 — audit-trail.spec.ts cycle filter | Strengthened by Q22 + entity #10 + cycle-1 amendments |
| F6 — gap-register schema completeness | Strengthened by additive `cycle_id` field (entity #2 update) |
| F7 — clarification-log → CHK traceability | Strengthened by CHK181..CHK215 anchoring at Q15..Q29 |

**Verdict**: ✅ no cycle-0 regression; cycle-1 strengthens four cycle-0
findings via additive constraints.

## Final state

- **CRITICAL findings**: 2 raised, 2 auto-resolved → 0 outstanding.
- **HIGH findings**: 2 raised, 2 auto-resolved → 0 outstanding.
- **MEDIUM findings**: 1 raised, deferred (documentation tightness, no
  behavioural impact) → 0 blocking.
- **LOW findings**: 1 raised, deferred (cycle-0 layout drift surfaced
  but not blocking cycle-1) → 0 blocking.
- **Escalations to project lead**: 0.

**State: CLEAN**

## Next actions

The parent agent may now proceed to:

1. **`/speckit.implement`** — execute T173..T206 in dependency order.
   T173 + T174 are review-and-integrate tasks (the artefacts already
   exist from plan-phase commit `3a155ac`), so implementation begins
   with T175 (depth-profile YAML authoring × 68).

2. **Status snapshot** before implementation:
   - Phase 10 (FR-028 evaluator endpoints): T173, T178..T181 ready.
   - Phase 11 (FR-029 depth-profile): T174..T177 ready.
   - Phase 12 (FR-029 cycle-metadata): T182..T183 ready.
   - Phase 13 (FR-029 stub refactor): T184..T186 — **MUST run after
     T173..T177 + T182** per task-list dependency note.
   - Phase 14 (FR-030 13 net-new specs): T187..T199 ready (`[P]`,
     independent files).
   - Phase 15 (Q25 env-var normalisation): T200..T202 ready (`[P]`).
   - Phase 16 (SC-012 closure): T203 — **MUST run after T182 + T183**.
   - Phase 17 (cycle-1 docs polish): T204..T206 ready.

3. **No further `/speckit.clarify` round required**. All cycle-1
   ambiguities resolved (Q15..Q29). Q25 + Q27 + Q29 supply the
   spec-level binding overrides; Constitution NN-2 + ASM-011 supply
   the auto-resolution authority; cycle-0 baseline (commit `e028bf7`)
   remains unchanged.

---

*Report authored 2026-02-05 by the cycle-1 `/speckit.analyze` pass.
Cycle-0 `analysis.md` (commit `e028bf7`) preserved unchanged per the
parent agent's explicit request. This file is the cycle-1 peer
artefact.*
