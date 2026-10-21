# Spec 037 Static Implementation Audit

## Review Metadata

- Review date: 2026-09-14.
- Expected and observed HEAD: `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a` (read-only `git rev-parse HEAD`).
- Scope: only spec 037 Capstone Evidence Pack and the implementation, tests, artefacts, and gates needed to assess its obligations.
- Writable boundary: this report only. No delegation, implementation changes, original checkbox changes, evidence changes, index updates, branches, or commits.
- Method: fresh source inspection plus read-only text parsing, inventory, report-integrity checks, and editor diagnostics. No verification scripts, product tests, builds, imports, models, browsers, servers, cloud operations, installs, runtime inspection, or external approvals were executed.
- Baseline: tracked worktree clean; pre-existing untracked audit files were left untouched and their report contents were not read.
- Contract: [Review Contract](../001-spec-implementation-audit/README.md#L11); [review instructions](../../.github/instructions/code-review.instructions.md#L1).
- Evidence statuses describe source support only. Measurements, deployment state, historical test execution, reviewer decisions, and current runtime success remain UNVERIFIED.

## Prioritised Findings

| Priority | Finding and exact controlling evidence | Follow-up |
| --- | --- | --- |
| CRITICAL | Evidence-pack is outside the [Entra protected-prefix set](../../apps/api/app/middleware/entra_auth.py#L38) and [RBAC set](../../apps/api/app/middleware/rbac_check.py#L32); legacy auth permits anonymous defaults and GETs have no read audit. | AUD-037-002 |
| CRITICAL | [Publisher callbacks are optional](../../apps/api/app/services/governance/evidence_pack_writer.py#L36), validation is absent, and the only caller is a test; [history reads](../../apps/api/app/api/routes/governance/evidence_pack.py#L174) serve only the current sidecar. | AUD-037-003 |
| IMPORTANT | [Discovery](../../scripts/evidence_pack_gate/gate.py#L200) can pass an empty/incomplete pack; [link checking](../../scripts/evidence_pack_gate/gate.py#L97) ignores JSON references, headings, and the tradeoff-log directory. | AUD-037-001, AUD-037-004 |
| IMPORTANT | [Schema/model contract](./contracts/publication-gate-metadata.schema.json#L32) misses exact-boundary and semantic rules; typed validators are detached and ledger metadata excludes 15 tradeoffs. | AUD-037-005 |
| IMPORTANT | [Generation](../../scripts/evidence_pack_gate/generate_artefacts.py#L27) writes its own approval/validation labels and overwrites the same publication IDs. | AUD-037-006 |
| IMPORTANT | [Missing-data stubs](../../apps/api/app/api/routes/governance/evidence_pack.py#L120) return 200 and current timestamps; [page error handling](../../apps/web/src/app/governance/executive/page.tsx#L24) suppresses outage warnings. | AUD-037-007 |
| IMPORTANT | [Executive ladder](../../apps/web/src/app/governance/executive/_components/KpiLadder.tsx#L29) lacks source links, thresholds/status and existing shell composition; current JSON has no observations. | AUD-037-008 |
| IMPORTANT | [Risk renderer](../../scripts/evidence_pack_gate/generate_artefacts.py#L836) freezes its date; 19 overdue risks are unflagged and legacy Markdown is not schema-migrated. | AUD-037-009 |
| IMPORTANT | [Roadmap](../../docs/governance-hub/adoption-roadmap/roadmap.md#L10) omits utilities/transport and the lessons feedback loop; Commonwealth sequencing and per-pilot rollback are incomplete. | AUD-037-010 |
| IMPORTANT | [RAI claims](../../docs/governance-hub/rai-register/responsible-ai-register.md#L18) overstate cell counts and cite specifications instead of evaluation outputs; no new-agent row gate exists. | AUD-037-011 |
| IMPORTANT | [Hard-coded ledger inventory](../../scripts/evidence_pack_gate/generate_artefacts.py#L650) has one missing/one invented spec; the [log](../../docs/governance-hub/feature-value-ledger/tradeoff-log.md#L11) misattributes the 036 ADRs and omits a required tension. | AUD-037-012 |
| IMPORTANT | [Vitest](../../apps/web/vitest.config.ts#L19) and [Playwright](../../apps/web/playwright.config.cts#L4) do not discover the spec-037 suites; CSV mappings and branch-protection intent do not enforce the advertised coverage. | AUD-037-013 |
| IMPORTANT | [CI metrics](../../.github/workflows/ci.yml#L430) remain an echo; duration is logged rather than instrumented and failure rate is not emitted. | AUD-037-014 |
| IMPORTANT | [Storage additions](../../infra/main.bicep#L763) bypass the promised AVM composition; retention has no lower bound or demonstrated lock lifecycle. | AUD-037-015 |
| IMPORTANT | [Quickstart commands](./quickstart.md#L34) do not match argparse; [rehearsal](./rehearsal-results.md#L3) remains deferred, while closure records overstate tested/reviewed evidence. | AUD-037-016 |

The 16 follow-ups below are implementation work for later authorised developer/tester agents,
not actions performed by this audit. Source-only IMPLEMENTED results do not mean production-ready.

## Local Inputs Read In Full

All 19 original spec-local files were read, including embedded amendments and complete checklist tables:

| Input | Scope |
| --- | --- |
| [specification](./spec.md#L1) | Five stories, 15 acceptance scenarios, eight edges, 38 FRs, 11 SCs, clarifications, scope, and Step 8 R1-R9 dispositions. |
| [tasks](./tasks.md#L1) | All 69 original tasks, acceptance text, phase gates, dependencies, and strategy notes. |
| [plan](./plan.md#L1) | Performance and security constraints, PD-037-01 through PD-037-06, constitution checks, and post-polish assertions. |
| [research](./research.md#L1) | RES-01 through RES-05 and persona-derived implementation commitments. |
| [data model](./data-model.md#L1) | All row types, publication lifecycle, provenance, revision, and metadata invariants. |
| [quickstart](./quickstart.md#L1) | Prerequisites, workflows 1-4, endpoint promises, and failure recovery. |
| [rehearsal record](./rehearsal-results.md#L1) | Local PASS assertions and explicit live Step 9 deferral. |
| [quality checklist](./checklists/requirements.md#L1) | All 16 quality items and stale clarification notes. |
| [reviewer checklist](./checklists/capstone-evidence-pack.checklist.md#L1) | All 84 CHK items, traceability table, closure note, and deferrals. |
| [operational synthesis](./synthesis/step1-ops.md#L1) | Ten-persona synthetic input across five artefacts. |
| [sector synthesis](./synthesis/step1-sectors.md#L1) | 58-persona synthetic input, sequencing, authority, and cross-sector tensions. |
| [technical synthesis](./synthesis/step4-tech.md#L1) | 17-persona synthetic input, auth, audit, accessibility, contracts, and SLO duties. |
| [OpenAPI](./contracts/openapi.evidence-pack.yaml#L1) | All four reads, security, success/error payloads, and historical-publication contract. |
| [risk schema](./contracts/risk-register.schema.json#L1) | Canonical risk envelope, row, and provenance contract. |
| [roadmap schema](./contracts/adoption-roadmap.schema.json#L1) | Canonical wave, lead-agency, cadence, and rollback contract. |
| [KPI schema](./contracts/executive-kpi-surface.schema.json#L1) | Canonical criterion, threshold, observation, and consolidation contract. |
| [RAI schema](./contracts/responsible-ai-register.schema.json#L1) | Canonical framework, principle, NIST profile, and evidence-cell contract. |
| [ledger schema](./contracts/feature-value-ledger.schema.json#L1) | Canonical feature contributions and sibling tradeoffs population. |
| [metadata schema](./contracts/publication-gate-metadata.schema.json#L1) | Canonical manual-ratio, sign-off, date, and gate-status contract. |

## Initial Controlling-Path Finding

**IMPORTANT: publication discovery fails open when required artefacts are absent.**
The [CLI](../../scripts/evidence_pack_gate/__main__.py#L12) delegates to
[the gate](../../scripts/evidence_pack_gate/gate.py#L200). Its discovery loop skips absent roots,
selects only recognised `artefact_id` values, and has no required-five population comparison;
the final decision is `passed=not failures`. A source tree with no discoverable artefacts and
no broken links therefore has a success path. This contradicts the complete-pack publication
obligations in [FR-001](./spec.md#L118) and [FR-009](./spec.md#L126).

Local hypothesis: an empty or incomplete required population can be labelled PASS.
Cheap discriminating check: inspect the CLI-to-`run_gate` control flow and required-population
comparison, not run it; validate this report's local links and unchecked remediation ID.

## Remediation Tasks

- [ ] AUD-037-001 Require the complete canonical artefact population before publication

**Priority: IMPORTANT. Affected:** FR-001, FR-008, FR-009, SC-002; T045, T046, T047;
RES-04 complete-pack publication. Expected: all five canonical artefacts and their companion
citation surfaces are mandatory. Observed: missing directories and unrecognised sidecars can
escape [discovery](../../scripts/evidence_pack_gate/gate.py#L200). Duplicate IDs are not rejected.
Impact: a pass label need not establish that a complete evidence pack was inspected.

**Developer instructions:** use an explicit required path/ID manifest and reconcile discovered
inputs with it before validation. Require the Markdown companions and paired tradeoff log;
reject empty/missing/duplicate/unknown required entries with actionable failures. Keep optional
unrelated JSON separate. Bind `--repo-root` consistently to schemas as well as inputs: currently
[schema resolution](../../scripts/evidence_pack_gate/gate.py#L129) ignores the CLI root. Preserve
CLI exit-code compatibility. Depend on AUD-037-004 and AUD-037-005 for citation/semantic checks.

**Tester home and cases:** extend
[gate-link tests](../../tests/contract/spec_037/test_publication_gate_link_check.py#L13) and
[shared fixtures](../../tests/contract/spec_037/conftest.py#L18) with actual CLI/`run_gate` tests.
Use an empty tree, each of five missing sidecars in turn, missing Markdown/log, unknown ID,
duplicate recognised IDs, malformed JSON/non-object JSON, and a complete valid five-artefact
fixture. Assert nonzero CLI status and exact missing-path diagnostics; complete input alone
passes. A separate temporary root must use its own schema set, not repository-global schemas.

**Future validation:** in a configured isolated Python environment with `scripts` on `PYTHONPATH`,
run `pytest tests/contract/spec_037 -q` and the gate CLI against disposable positive/negative
fixture roots. Expected: no skipped tests and no zero-artefact PASS. **Done:** exact population
checks precede all validation and no incomplete pack can be published.

- [ ] AUD-037-002 Enforce authenticated authorised reads and tenant-scoped read auditing

**Priority: CRITICAL. Affected:** FR-005, FR-021, FR-029; T014, T015, T016, T017,
T035, T036, T039; OpenAPI security and read-audit contract; technical synthesis security duties.

**Expected versus observed:** all four routes require an Entra bearer and an allowed existing
AppRole, and reads produce the required audit evidence. The router is mounted by
[API registration](../../apps/api/app/api/router.py#L93), but the protected prefix sets in
[Entra middleware](../../apps/api/app/middleware/entra_auth.py#L38) and
[RBAC middleware](../../apps/api/app/middleware/rbac_check.py#L32) omit evidence-pack.
[Legacy authentication](../../apps/api/app/middleware/auth_middleware.py#L19) supplies anonymous
defaults and does not reject the request. The routes have no auth dependency. The
[web client](../../apps/web/src/lib/governance/evidence-pack/client.ts#L31) sends Accept but no
bearer, while the [audit middleware](../../apps/api/app/middleware/audit_appender.py#L89) skips
GETs and [over-cap read helper](../../apps/api/app/services/governance/evidence_pack_writer.py#L110)
has no caller in the inspected source. Application-level access and read-attribution obligations
are unmet; deployed EasyAuth configuration and external exposure are UNVERIFIED.

**Developer instructions:** protect the four read routes using the existing validated principal
and closed AppRole inventory; update the matching route-family allowlist; carry tenant and actor
identity into audit records; connect read auditing, including over-cap reads. Reconcile the
OpenAPI promise of every read with T035's over-cap minimum explicitly. Integrate the existing
server-compatible bearer acquisition/forwarding path in the web client without exposing tokens
or adding roles. Preserve unrelated middleware routes and the read-only HTTP surface. This work
depends on the durable publication/audit adapter work in AUD-037-003.

**Tester home and cases:** extend the existing
[API fixture](../../apps/api/tests/contract/spec_037/conftest.py#L8) to exercise the real middleware
stack rather than only mounting a naked router. Extend the existing
[list test](../../apps/api/tests/contract/spec_037/test_route_list_artefacts.py#L9),
[latest test](../../apps/api/tests/contract/spec_037/test_route_get_artefact.py#L9),
[history test](../../apps/api/tests/contract/spec_037/test_route_get_publication.py#L9), and
[publish integration test](../../tests/integration/spec_037/test_publish_pipeline.py#L13).
Use valid existing roles, no bearer, malformed/expired/wrong-audience bearer, disallowed role,
spoofed identity headers, and distinct tenant principals. Assert 200 only for authorised reads,
401/403 Problem Details otherwise, no data disclosure, and exact audit actor/tenant/event counts
for ordinary, over-cap, and failed reads. Assert bearer forwarding without credential logging.

**Future validation:** after an authorised developer configures the repository's supported Python
environment and isolated auth/storage fixtures, run `uv run pytest apps/api/tests/contract/spec_037 tests/integration/spec_037 -q`.
Expected: no skipped auth cases, explicit rejection assertions, and recorded read events. Do not
use live cloud credentials for unit/contract verification. **Done:** the real application path,
not only the router fixture, satisfies the auth and audit contract.

- [ ] AUD-037-003 Connect validated publication to durable storage and real historical reads

**Priority: CRITICAL. Affected:** FR-005, FR-009, FR-029, FR-035, FR-037, FR-038;
T016, T032, T034, T035, T036, T045, T046, T067; PD-037-04; publication state machine;
quickstart Workflow 2 and failure recovery.

**Expected versus observed:** a passed merge publishes a validated immutable snapshot, cache
entry, and audit record; historical reads retrieve that snapshot. The
[writer](../../apps/api/app/services/governance/evidence_pack_writer.py#L36) performs no schema,
link, cap, prior-version, or sign-off validation. All three callbacks default to `None`, so it
can return success without persistence. Sequential callback writes have no retry, idempotency,
partial-failure recovery, or explicit override event. The only inspected invocation is the
[integration test](../../tests/integration/spec_037/test_publish_pipeline.py#L45), which supplies
list-appending callbacks and schema-invalid rows. The CI job runs only the gate; there is no
production publisher invocation in the bounded search of `apps`, `packages`, `scripts`, `tests`,
`.github`, and `infra`. [Historical reads](../../apps/api/app/api/routes/governance/evidence_pack.py#L174)
compare the requested ID with the current repository sidecar, not Blob history. Renamed publisher
references were searched before classifying this as missing integration, not a missing filename.

**Developer instructions:** make required storage/audit adapters explicit; add a production
publication entrypoint reachable after a successful gate; revalidate the exact payload being
published; enforce identity, immutable publication IDs, and prior-revision linkage. Use an
idempotent publication state machine that never exposes an incomplete publication as current
and preserves immutable data when a later sink fails. Implement Cosmos cache then source fallback
for latest reads and Blob-backed historical reads. Emit publish and override events through the
existing audit convention. Do not add a public mutation route or new top-level Azure resources;
preserve the four existing read URLs and schema compatibility. Coordinate storage policy work
and authentication with the owning platform and API maintainers.

**Tester home and cases:** extend the existing
[publish test](../../tests/integration/spec_037/test_publish_pipeline.py#L13) and
[historical-read test](../../apps/api/tests/contract/spec_037/test_route_get_publication.py#L9).
Use valid complete payloads and two different revisions; assert exact stored bytes, IDs, actor,
ratio, and prior snapshot survival. Reject schema-invalid, empty, over-cap unsigned, future-dated,
reused-ID, and altered-prior-row payloads before visibility. Inject failure at each sink, retries,
and duplicate publication delivery; assert no false success, no partial latest view, no deleted
archive, and exactly-once logical audit attribution. Replace the permissive 200-or-404 history
assertion with deterministic 200 for an old snapshot and 404 for a genuinely absent ID.

**Future validation:** with isolated storage/audit doubles first, run `uv run pytest tests/integration/spec_037 apps/api/tests/contract/spec_037 -q`.
An explicitly approved later staging rehearsal must separately establish real persistence and
immutable archive retrieval. **Done:** a real publishing entrypoint reaches mandatory adapters,
invalid input cannot publish, partial failures are recoverable, and old revisions remain readable.

- [ ] AUD-037-004 Validate structured citations and every companion Markdown surface

**Priority: IMPORTANT. Affected:** FR-003, FR-008, FR-011, FR-020, FR-022, FR-028,
FR-032, FR-034; SC-002; T021, T045, T047, T051, T056, T057, T058, T059, T060, T064,
T066; stale-citation and superseded-surface edges.

**Expected versus observed:** every back-citation resolves to its file and section. The
[link helper](../../scripts/evidence_pack_gate/gate.py#L97) only recognises inline Markdown
links, strips fragments without checking headings, skips fragment-only links, and mishandles
parenthesised paths. The [root list](../../scripts/evidence_pack_gate/gate.py#L191) omits the
tradeoff-log directory and superseded documents. Generated risk citations are code spans, and
JSON `ref`, `section`, `adr_path`, and consolidation fields are not walked. Full structured
inspection found two broken risk citation targets: the reference in
[RISK-NEW-002](../../docs/risk-register/RISK-NEW-002.md#L19) uses a nonexistent governance-hub
partitioning path; [RISK-NEW-003](../../docs/risk-register/RISK-NEW-003.md#L21) uses a moved ADR.
Replacements exist at [partitioning documentation](../../docs/architecture/cosmos-partitioning.md#L1)
and [Phi boundary ADR](../../docs/corpus/aidr/decisions/adr-033-phi-shadow-boundary.md#L1).
There are zero section fields in the 358 nested citations of risk, roadmap, KPI, and RAI
combined. The ledger's only two section values describe waves, not a heading in its cited spec.

**Developer instructions:** validate structured reference fields and render clickable citations;
use a Markdown parser with heading/explicit-anchor resolution and platform-neutral path casing.
Validate the paired log, all superseded surfaces, and references inside inline-code/path fields
according to a documented contract. Correct moved references through dated revisions, not source
deletion. Treat telemetry URI resolution separately from local file existence; do not claim an
external sink is healthy from a URI string. Coordinate with AUD-037-006's revision discipline.

**Tester home and cases:** extend
[link-check tests](../../tests/contract/spec_037/test_publication_gate_link_check.py#L13).
Fixtures: existing file/heading, missing file, renamed target, absent heading, fragment-only link,
reference-style link, JSON-only citation, tradeoff-only broken link, percent-encoded spaces,
parentheses in filenames, Windows/Linux case mismatch, and a sink URI requiring deferred
verification. Assert every mandatory surface is scanned and errors identify row and field.

**Future validation:** `pytest tests/contract/spec_037/test_publication_gate_link_check.py -q`,
then the repaired gate against an isolated complete pack. Expected: all local citations resolve,
negative fixtures fail, external outcomes remain explicitly unverified. **Done:** a broken
back-citation cannot hide behind code spans, JSON, an omitted directory, or a discarded fragment.

- [ ] AUD-037-005 Enforce semantic schema parity and the fixed manual-evidence policy

**Priority: IMPORTANT. Affected:** FR-009, FR-010, FR-011, FR-015, FR-018, FR-019,
FR-024, FR-027, FR-030, FR-033, FR-037, FR-038; SC-002, SC-003, SC-004, SC-005,
SC-006, SC-011; T008, T009, T010, T011, T012, T013, T018, T019, T020, T026, T027,
T028, T029, T030, T031, T032, T033, T045; data-model validation rules.

**Expected versus observed:** schema, models, gate, and published values must agree. Six mirrors
are byte-identical, but the [envelope](../../packages/domain/src/domain/models/evidence_pack/evidence_pack_artefact.py#L13)
does not import or validate the row models. The gate uses JSON Schema without a format checker
and recomputes only the ratio, not equality of both declared counts. Risk score products are
validated only by the detached [RiskRow](../../packages/domain/src/domain/models/evidence_pack/risk_row.py#L45).
No aggregate checks require six categories, all jurisdictions/cohorts, five leading/lagging pairs,
all component/spec/ADR IDs, or nonzero-gap follow-ups. Non-risk schemas omit conditional manual
owner/cadence/automation requirements. The [metadata schema](./contracts/publication-gate-metadata.schema.json#L32)
forbids sign-off below 0.5 but not at exactly 0.5; the
[model](../../packages/domain/src/domain/models/evidence_pack/publication_gate_metadata.py#L42)
allows unnecessary sign-offs and a configurable cap. The helper also trusts a configurable cap;
the full schema still requires sign-off above 0.5, so this is validator disagreement, not a claim
that raising the threshold alone bypasses the complete current gate. Blank/whitespace identities,
invalid dates, arbitrary eight-character basis text, and `pending`/`failed` publication status
are not adequately rejected. RAI `na_justification` can be empty in JSON Schema.

The ledger contains 37 feature rows plus 15 manual tradeoffs, but
[metadata](../../specs/shared/feature-value-ledger.json#L7) and the gate count only the 37
`rows`. This conflicts with the all-row provenance wording; current ratio remains 1.0 either
way, while a mixed-provenance pack could hide manual tradeoffs. The 4-by-8 RAI wording versus
15 independent leaf cells and UUID-v4 versus uuid5 publication IDs also require explicit contract
resolution, not silent schema weakening.

**Developer instructions:** define one reusable semantic validator invoked by CLI and publisher,
with typed artefact-discriminated rows; align canonical schemas, mirrors, Pydantic, and generated
TS. Lock v1 threshold to 0.5, define the combined ledger denominator, recompute all counts,
require valid nonfuture timestamps/UUID policy and passed gate state, enforce conditional fields
and trimmed identities, and reject nonzero gaps without meaningful follow-ups. Preserve known
historical payloads through an explicit versioned read migration. Resolve the RAI/ID ambiguities
with maintainers; do not invent a ninth component or a new metric. Depend on AUD-037-001 and
AUD-037-003 for entrypoint use, AUD-037-011/AUD-037-012 for population ownership.

**Tester home and cases:** extend all six existing schema tests and
[ratio tests](../../tests/contract/spec_037/test_publication_gate_ratio_recompute.py#L46).
Add model/gate parity cases: 0, exactly 0.5, just over 0.5, and 1; correct ratio with wrong
counts; empty rows; manual tradeoff with automated features; missing/blank manual fields;
invalid/future date; duplicate ID; wrong score product; ten copies of one KPI; missing jurisdiction
or lead agency; missing component; empty N/A justification; nonzero gap without a follow-up;
unnecessary sign-off; raised threshold. Assert exact failures, not merely any error, and remove
skip-on-missing-schema behaviour. **Future validation:** `pytest tests/contract/spec_037 -q`
in the configured local environment, then narrow domain type checks. **Done:** every entrypoint
enforces the same complete published-artifact contract and boundary tests reject invalid cases.

- [ ] AUD-037-006 Preserve revisions and stop generating approval or validation evidence

**Priority: IMPORTANT. Affected:** FR-004, FR-005, FR-012, FR-029, FR-035, FR-037,
FR-038; SC-002, SC-005, SC-011; T034, T035, T045, T056, T057, T058, T059, T060,
T067; append-only edge and data-model publication state machine.

**Expected versus observed:** published rows cannot be edited in place; approvals and evidence
status must come from authorised review, and available source data must be consumed. The
[generator](../../scripts/evidence_pack_gate/generate_artefacts.py#L16) explicitly overwrites
the output files. It hard-codes the publication date, uuid5 ID, `Validated`, `passed`, and a
generic implementer sign-off in [envelope generation](../../scripts/evidence_pack_gate/generate_artefacts.py#L27).
Its data builders transcribe risks, metrics, components, specs, and ADRs as literals, not source
extraction. Re-running after changing a literal changes bytes under the same publication ID.
No prior-row comparison or allowed `revises` field enforces the promised revision chain.
All five current artefacts are 100% manual and carry the same generated author sign-off.
The objects are structurally populated; an actual named human decision is UNVERIFIED, not
established by generator output. No claim is made that a historical overwrite actually occurred.

**Developer instructions:** separate draft materialisation from publication; derive available
spec/ADR data through structured extraction; accept genuine dated review records as explicit
inputs; never synthesize approval identities or validation success. Assign new IDs/timestamps
only on real publication, preserve old bytes, require revision linkage, and reject modifications
to already-published row identities. Keep unreviewed/manual evidence Deferred or Unresolved.
Make rendering deterministic for the same immutable input, not by freezing a global timestamp.
Preserve the legacy risk document and constitution. Depend on AUD-037-003/AUD-037-005 and the
artefact-specific remediation tasks for approved migrations and source-of-truth selection.

**Tester home and cases:** use existing
[publish integration tests](../../tests/integration/spec_037/test_publish_pipeline.py#L13) and
[metadata tests](../../tests/contract/spec_037/test_publication_gate_metadata_schema.py#L9).
Assert identical rendering for the same immutable input; a correction creates a new revision
without changing old bytes; reused IDs with different content fail; absent authorisation never
creates sign-off; source changes update draft provenance, not published history; failure before
approval cannot mark `Validated`/`passed`. **Future validation:** `pytest tests/integration/spec_037 tests/contract/spec_037 -q`
with temporary output directories after developer changes. Any generation command must run only
in disposable fixtures until reviewed migration is approved. **Done:** machine generation cannot
masquerade as human approval, and revision/history semantics are enforceable end to end.

- [ ] AUD-037-007 Fail visibly on unavailable artefacts and stale telemetry

**Priority: IMPORTANT. Affected:** FR-005, FR-021, FR-023; SC-008; T015, T017, T024,
T034, T036, T039, T042, T043, T058, T067; degraded-telemetry edge; OpenAPI error contract.

**Expected versus observed:** failures retain honest last-observed timestamps and stale status.
[Latest reads](../../apps/api/app/api/routes/governance/evidence_pack.py#L120) manufacture a 200
stub with `rows: [{}]` and current timestamps when JSON is absent or unparsable. Missing summaries
contain zero rows despite the OpenAPI minimum of one. [Health](../../apps/api/app/api/routes/governance/evidence_pack.py#L192)
reports healthy whenever files parse, even for pending/failed gates or absent observations, and
does not inspect upstream sinks or refresh cadence. The documented force-stale variable has no
implementation in the bounded source search. The [page](../../apps/web/src/app/governance/executive/page.tsx#L24)
catches request failures into empty arrays/null; null health makes `stale` false. All ten current
KPI rows lack both value and observation time. This can show an empty or `n/a` surface without a
degradation warning, not the contracted stale evidence.

**Developer instructions:** remove success stubs from production responses; map absent, invalid,
unavailable, and historical-missing inputs to documented Problem Details. Compute health from
validated publication state and authoritative source freshness, preserving last successful
observations. Model unknown/unavailable as degraded, including null health and partial endpoint
failure. Respect per-KPI cadence; never replace last observation with request time. Keep the
four-route contract and use existing sinks only. Coordinate AUD-037-002/AUD-037-003/AUD-037-008.

**Tester home and cases:** extend the existing latest/health route tests and
[banner tests](../../apps/web/src/app/governance/executive/_components/__tests__/StaleTelemetryBanner.test.tsx#L9).
Add page-level cases in the existing executive test directory: all fresh, old observation,
missing timestamp, malformed/missing JSON, partial API failure, total outage, failed/pending gate,
historical ID absent, force-stale mode if retained, and recovery. Assert correct status/content
type, no fake current timestamp, stale banner in every unknown/outage state, and previous good
values identified as stale. **Future validation:** `pytest apps/api/tests/contract/spec_037 -q`
and `pnpm --filter @ama/web exec vitest run src/app/governance/executive` after discovery is repaired.
**Done:** neither missing data nor failed fetches can appear fresh or successfully published.

- [ ] AUD-037-008 Complete the executive page using the existing shell and evidence primitives

**Priority: IMPORTANT. Affected:** FR-019, FR-020, FR-021, FR-022, FR-023; SC-004,
SC-008, SC-009; T022, T023, T024, T025, T039, T040, T041, T042, T043, T044, T051,
T058, T061; US3; RES-03; PD-037-02; accessibility/locale duties.

**Expected versus observed:** the existing shell presents all five metric ladders, sources,
thresholds, and meaningful state. The [page](../../apps/web/src/app/governance/executive/page.tsx#L44)
and [ladder](../../apps/web/src/app/governance/executive/_components/KpiLadder.tsx#L29) are bespoke
raw markup; neither composes PersonaWorkspace nor audit-row primitives. There is no parent
governance layout supplying them. [Dashboard navigation](../../apps/web/src/app/governance/dashboard/layout.tsx#L7)
has no executive entry. The ladder omits source-of-truth, consolidation links, threshold bands,
observation timestamps, and on-track/at-risk status. The
[ratio strip](../../apps/web/src/app/governance/executive/_components/ManualRowRatioStrip.tsx#L32)
uses an unwrapped flex row and raw long IDs; no matching responsive styling was found in web
source. Existing language assets are not consumed. No chart library import was found in this
slice, which is supported; responsive conformance and screen-reader behaviour are UNVERIFIED.
The source only consolidates dashboard and SLO paths, not all six FR-020 sources, and KPI-CAP-002
cites its own output. Three document banners exist; the three spec-source consolidation duties
remain unreconciled. Types are manually mirrored and cast rather than generated/parity-tested.

**Developer instructions:** compose the existing shell/read primitives, add sibling navigation,
use typed KPI contracts and existing locale/accessibility assets, and render all evidence fields.
Map sources to existing telemetry or honest manual stubs with explicit unavailable state; do not
invent metric emitters or values. Reconcile the six-source consolidation list and add scoped
deprecation links without retiring operational content. Show exactly five artefact positions,
including unavailable states and genuine sign-off status, with responsive layout and meaningful
update announcements. Preserve read-only access and the no-new-charts/infrastructure boundary.
Depend on AUD-037-002/AUD-037-007/AUD-037-013 for auth, freshness, and discovered tests.

**Tester home and cases:** strengthen the three existing executive component tests and
[Playwright suite](../../apps/web/tests/e2e/spec-037/governance-executive.spec.ts#L11).
Check all five criteria and ten KPIs, valid source/threshold links, absence of synthetic values,
hub-to-executive navigation and return, actual focus targets, live ratio changes, empty/partial
data, 320px reflow, forced colours, zoom, long translated labels, and existing locale inheritance.
Assert no horizontal text clipping/overlap and no serious/critical axe violations; test source
imports directly instead of treating non-null rendering as a no-chart assertion.

**Future validation:** after AUD-037-013, run `pnpm --filter @ama/web exec vitest run src/app/governance/executive`
and the repaired spec-037 Playwright project in an authorised local test environment. Separately
measure SC-008 comprehension with a named reviewer. **Done:** the real navigable page carries
the complete ladder and audit context, honours existing composition, and has meaningful a11y tests.

- [ ] AUD-037-009 Render a current risk register and preserve the legacy risk evidence

**Priority: IMPORTANT. Affected:** FR-003, FR-005, FR-010, FR-011, FR-012, FR-013,
FR-014; SC-001, SC-002; T008, T026, T056, T064; US1; CHK005, CHK006, CHK008, CHK014.

**Expected versus observed:** the register is dynamically current, schema-bound, archiveable,
and traceable. All 21 JSON risk rows have the stated fields, correct score products, and all six
categories. The [index](../../docs/risk-register/index.md#L12) is sorted, but the
[renderer](../../scripts/evidence_pack_gate/generate_artefacts.py#L836) freezes today at
2026-05-11 and never emits an overdue counter. At review date 2026-09-14, 19/21 rows are overdue
and none is flagged. The [legacy file](../../docs/risk-register/RISK-AOAI-001.md#L3) retains
qualitative probability/impact and old category names, lacks numeric schema fields and next
review dates, and has no parser/migration validation. That is preservation, not new-schema
compliance. The 18 new Markdown rows omit provenance/review metadata and present citations as
code spans. No explicit NERAG matrix/treatment-state view or per-AIDR-domain coverage mapping
was found in the full risk population; the risk-manager authority requests these explicitly.

**Developer instructions:** derive the index and detailed views from versioned validated data,
accept an explicit as-of date/clock, add overdue flags/count and links to every detail, and retain
numeric likelihood/consequence context for the NERAG matrix. Preserve the three historical AOAI
risks verbatim with an explicit additive schema migration/crosswalk and revision provenance,
rather than silently rewriting their categories. Map the in-scope AIDR operational domains and
identify unsupported domain evidence openly. Depend on AUD-037-004/AUD-037-005/AUD-037-006.

**Tester home and cases:** extend
[risk schema tests](../../tests/contract/spec_037/test_risk_register_schema.py#L36) and the existing
publish integration test with real legacy input and deterministic render fixtures. Assert all
six categories, valid products, tie ordering, past/today/future dates, overdue count 19 for the
current data as of 2026-09-14, no lost historical AOAI values, and aligned Markdown/JSON metadata.
**Future validation:** `pytest tests/contract/spec_037/test_risk_register_schema.py tests/integration/spec_037 -q`;
then a separately authorised timed top-ten risk review. **Done:** the register exposes current
review debt, preserves legacy evidence, and supports its documented matrix and citations.

- [ ] AUD-037-010 Restore the mandated adoption sequence and readiness-to-lessons loop

**Priority: IMPORTANT. Affected:** FR-015, FR-016, FR-017, FR-018, FR-035; SC-003;
T009, T027, T057; US2; readiness-conflict edge; CHK017 through CHK024 and CHK077;
operational and sector synthesis.

**Expected versus observed:** state leads, local government, utilities, transport, volunteer/NGO,
then Commonwealth; every wave has safe rollback and readiness evidence. The full
[five-wave roadmap](../../docs/governance-hub/adoption-roadmap/roadmap.md#L10) includes every
jurisdiction and named state leads, but only three cohort values; utilities and transport are
absent, and Commonwealth appears in WAVE-03 before local government. WAVE-04/WAVE-05 agency names
are generic peak-body placeholders. Training cites 007/024/026, but there is no per-wave AIDR
M&E citation, named lessons-to-next-gate loop, or deviation record for unmet jurisdiction gates.
WAVE-05 rollback lacks the explicit manual/no-data-loss guarantee; WAVE-02 through WAVE-04 rely
on prose inheritance. Step 8 R3/R4 defer narrower LGA/federal content polish, not the required
utilities/transport sequence or safety guarantees.

**Developer instructions:** add the missing cohorts and correct ordering using versioned wave
revisions; require lead-agency coverage for each listed jurisdiction, evidence/owner for readiness,
an explicit readiness-first deviation record, safe manual/no-data-loss rollback for every pilot,
and post-exercise lessons feeding the next wave. Cite existing simulations and AIDR M&E assets;
do not invent deployments, signed MoUs, or new exercise tooling. Carry R3/R4 forward as expressly
deferred v1.1 work. Depend on AUD-037-005/AUD-037-006 for validation and revisions.

**Tester home and cases:** extend
[roadmap schema tests](../../tests/contract/spec_037/test_adoption_roadmap_schema.py#L27).
Assert the complete ordered cohort set and jurisdiction/lead-agency mapping; test missing
utilities/transport, premature Commonwealth, missing agency, blank gate, two wave-one claimants
with one not ready, and each pilot's degraded manual/no-loss path. Verify per-wave existing
training/M&E citations and a named lessons feedback link. **Future validation:**
`pytest tests/contract/spec_037/test_adoption_roadmap_schema.py -q` plus a later Resilience Planner
review of the versioned roadmap. **Done:** sequencing and safe readiness/rollback rules agree
with the original requirement, and future-wave changes preserve prior decisions.

- [ ] AUD-037-011 Replace RAI self-attestation with component-specific evidence and inventory gating

**Priority: IMPORTANT. Affected:** FR-006, FR-024, FR-025, FR-026, FR-027, FR-028,
FR-029, FR-035; SC-005; T011, T029, T050, T059, T064; US4; future-agent edge;
PD-037-05; CHK044 through CHK057.

**Expected versus observed:** every in-scope component has substantiated framework/principle
posture referencing existing evaluation outputs. All eight explicitly named baseline components
are present, including simulation; no evaluation is invoked. Full JSON traversal found 15
leaf cells per component (3 framework cells + 4 NIST profiles + 8 principles), 120 total, not
the [256 claimed in Markdown](../../docs/governance-hub/rai-register/responsible-ai-register.md#L18)
or T059's nine-component/288 expectation. Every component's 15 cells repeat one summary with
`compliant` posture; [the generator](../../scripts/evidence_pack_gate/generate_artefacts.py#L559)
constructs this repetition. All `eval_evidence_refs` point to specifications, not evaluation
outputs; simulation and Foundry references do not even point to spec 030. Markdown truncates
two summaries and does not expose the full cell matrix. No per-principle fairness/contestability
assessment or PI&W privacy mapping can be inferred from the repeated text. The
[discovery instruction](../../.github/instructions/governance-discovery.instructions.md#L203)
requires extending the gate for a sixth artefact, not adding a row before a new agent ships.

**Developer instructions:** reconcile the eight named components versus nine-row task minimum
and literal 4-by-8 claim through explicit contract clarification. Populate the agreed structure
with distinct control/evidence assessments, meaningful N/A justifications, named human approval
points, and existing spec-030 output references. Unsupported posture must remain partial or
Unresolved, not machine-generated compliance. Generate complete stable Markdown from the same
JSON. Add a shipping-component inventory check and applicable governance-discovery requirement
for new components; examine current additions without treating every tool as an AI component.
Preserve full simulation obligations and bounded Foundry carve-out. Do not run evaluations or
broaden the exception to evidence storage. Depend on AUD-037-004/AUD-037-005/AUD-037-006.

**Tester home and cases:** extend
[RAI schema tests](../../tests/contract/spec_037/test_responsible_ai_register_schema.py#L79).
Fixtures: every baseline component, a newly registered AI component, duplicate/missing component,
all approved framework/principle/profile dimensions, blank/whitespace/N/A-without-justification,
spec-only citation mistaken for output evidence, and distinct control findings. Assert simulated
components are not exempted, generated totals equal actual cell counts, all evidence links resolve,
stable complete Markdown, and no model/evaluation invocation. **Future validation:**
`pytest tests/contract/spec_037/test_responsible_ai_register_schema.py -q` and a separate named
RAI Officer review of existing results. **Done:** inventory-complete evidence, not repeated
compliance labels, supports the published posture and future-agent gate.

- [ ] AUD-037-012 Reconcile the full feature and ADR ledgers with their authoritative sources

**Priority: IMPORTANT. Affected:** FR-003, FR-030, FR-031, FR-032, FR-033, FR-034,
FR-035, FR-036; SC-006; T012, T030, T052, T053, T054, T055, T060; US5; sector tensions.

**Expected versus observed:** every merged 001-036 spec and every ADR is accurately represented.
HEAD contains 37 distinct numbered spec documents; the 37-row ledger substitutes nonexistent
`004-rubric-gap-closure` for [001-arch-docs-refresh](../001-arch-docs-refresh/spec.md#L1).
All 15 ADR filenames occur, but ten of eleven 036 rows omit their actual simulation owner and
ADR-036-009 adds unsupported Foundry ownership. For example,
[ADR-036-001](../../docs/aidr/decisions/ADR-036-001-real-sub-agent-invocation.md#L6) selects HTTP
production adapters, whereas [the log](../../docs/governance-hub/feature-value-ledger/tradeoff-log.md#L11)
claims MAF/Foundry migration. ADR-036-002 concerns operator abort/pause/resume, not SDK migration
anchors; ADR-036-007 selects ETag gap-free sequence allocation, not an avoidance of hot partitions;
ADR-036-010/011 concern concrete correlation, SLI and staging-gate amendments, not generic review
cadence. Full ADR-by-ADR assessment appears below. `local-vs-cross-jurisdiction` is absent from
all tradeoffs. Feature magnitudes/gaps are literals with no unit, baseline computation, or
source-section provenance, and the two nonzero-gap rows point to a nonexistent wave heading in
spec 037. The metric trace links no feature ledger back, so bidirectionality is incomplete.

**Developer instructions:** derive the spec/ADR inventory from tracked source, with explicit
inclusion/alias/supersession rules; preserve duplicate number identities. Correct ADR owners,
alternatives, and rationale from each actual source; add the missing tension as a documented
decision, not a relabelled unrelated ADR. Give contributions units, baselines, evidence/status,
and meaningful open follow-ups with resolvable wave/issue/spec anchors. Preserve Asia cohort
deferrals and do not interpret `Validated` attribution as measured achievement. Add the inverse
cross-link; keep spec 016 a coverage-only hygiene row, not an implementation deliverable.
Depend on AUD-037-004/AUD-037-006; do not modify source ADR decisions or invent supersession.

**Tester home and cases:** extend
[ledger schema tests](../../tests/contract/spec_037/test_feature_value_ledger_schema.py#L53).
Compare full tracked ID sets, not counts; test duplicate numbers, removed/renamed specs, invented
IDs, every ADR including amendments, wrong bounding feature, unsupported alternative/rationale,
missing tension, zero/nonzero/negative gap, wrong units, absent follow-up, and one-way trace links.
Assert source-grounded content and preservation of explicit deferrals. **Future validation:**
`pytest tests/contract/spec_037/test_feature_value_ledger_schema.py -q` followed by a Capstone
Reviewer comparison of the full regenerated population. **Done:** equality of populations and
fidelity of meaning, not just matching filename counts, support the inverse ledger.

- [ ] AUD-037-013 Make verification discoverable and replace nominal traceability with real assertions

**Priority: IMPORTANT. Affected:** FR-008, FR-009, FR-021, FR-038; SC-002, SC-009,
SC-011; T005, T008, T009, T010, T011, T012, T013, T014, T015, T016, T017, T018,
T019, T020, T021, T022, T023, T024, T025, T045, T046, T061, T062, T068; QG-1/RES-04.

**Expected versus observed:** tests execute under their declared runners and FR/SC IDs map to
assertions that enforce their obligations. [Vitest includes](../../apps/web/vitest.config.ts#L19)
omit `src/**/__tests__`; [Playwright's testDir](../../apps/web/playwright.config.cts#L4) is
repository-level tests, not the new app-local suite. CI runs neither a spec-037 browser project
nor the API-local tests. Root pytest path setup omits `scripts`, and gate tests use
`importorskip`, so unavailable gate imports can silently skip. Schema tests similarly skip
missing mirrors. Both 53-row CSVs cover 49 distinct IDs, but contain nonexistent test names
such as `test_link_check` and `test_minimal_valid_publication_gate_metadata`, non-test paths,
and unrelated proofs (SC-008 maps to health-enum validation). No spec-037 CSV coverage assertion
was found in CI/scripts/tools. [Branch-protection intent](../../.github/branch-protection.json#L1)
is explicitly descriptive and omits this gate; live required-check settings are UNVERIFIED.
The gate job uses mutable action tags and does not use the planned pnpm/uv setup.

**Developer instructions:** wire existing tests into supported runners/CI, remove skip-on-missing
implementation, and make import/setup failures visible. Validate every CSV test target/node and
its relation to a requirement; separate manual evidence from executable test IDs. Require all
49 IDs and meaningful negative assertions. Add the publication gate to repository protection
intent and obtain actual settings confirmation only in a later authorised operation. Pin job
actions consistently; resolve planned-tooling differences explicitly. Keep unrelated test suites
and existing branch policy intact. Depend on the behaviour tasks for meaningful assertions.

**Tester home and cases:** reuse all existing spec-037 suites plus
[integration tests](../../tests/integration/spec_037/test_publish_pipeline.py#L13).
Assert the exact intended discovered test set, no skips, missing implementation fails, missing
CSV ID/test node fails, manual rows cannot masquerade as tests, and auth/history/empty-pack
negative cases are not replaced by shape checks. For the browser suite, assert actual focus,
five values, dynamic announcements, and reflow rather than non-null activeElement or heading-only
visibility. **Future validation:** `pytest tests/contract/spec_037 apps/api/tests/contract/spec_037 tests/integration/spec_037 -q`,
the repaired Vitest/Playwright commands, and workflow/traceability lint. **Done:** CI genuinely
discovers and enforces the scoped assertions; external branch protection is separately evidenced.

- [ ] AUD-037-014 Wire publication observability to real metrics and alertable outcomes

**Priority: IMPORTANT. Affected:** FR-023, FR-037; T033, T034, T048, T065; RES-05;
plan performance goals; Step 8 R2; SRE/Chaos review duties.

**Expected versus observed:** real publication duration, ratio, and gate-failure signals feed
the existing AU telemetry pipeline. [Ratio emission](../../apps/api/app/services/governance/manual_row_ratio.py#L40)
has an OTel gauge path, but it is reached only from the unwired publisher. Publication duration
is a logger message, not a metric instrument, and the gate never emits a failure-rate metric;
its `dry_run` argument is unused. [CI](../../.github/workflows/ci.yml#L430) is an echo placeholder.
The [catalogue](../../docs/governance-hub/observability/metrics-catalogue.md#L9) says all three
emit and defines a counter as a percentage failure rate without a total-run denominator.
The amendment explicitly defers CI export only; it does not prove the comment's claim that gate
execution reaches application counters. No spec-037 alert resources were found in infra.

**Developer instructions:** emit duration with a suitable histogram, ratio through the existing
gauge pipeline, and gate success/failure counts with a defined denominator/window. Instrument
actual CLI/publisher entrypoints, respect dry-run, bound dimensions, and document export/alert
prerequisites. Wire thresholds through existing observability resources without creating a new
workspace; never expose actor PII or credentials in dimensions. Depend on AUD-037-003 and
AUD-037-013. Keep R2's deferred operational verification visible.

**Tester home and cases:** extend
[publish integration test](../../tests/integration/spec_037/test_publish_pipeline.py#L13) and
existing gate tests with an in-memory metric exporter. Verify successful/failed/partial publish,
each gate failure stage, missing exporter, dry-run, exact names/units/dimensions, percentage
denominator, and no sensitive attributes. **Future validation:**
`pytest tests/integration/spec_037 tests/contract/spec_037 -q` with local exporter fixtures;
later authorised staging observation of duration median <=60s/p95 <=180s,
alert >300s and gate failure rate >5%/24h. **Done:** actual code paths emit the documented
instruments; thresholds have owners and evidence, while unmeasured SLOs stay UNVERIFIED.

- [ ] AUD-037-015 Align the two storage additions with AVM and immutable-retention guarantees

**Priority: IMPORTANT. Affected:** FR-005; SC-009; T037, T038, T063, T069;
PD-037-04/PD-037-06; AVM-first instructions and what-if review duty.

**Expected versus observed:** two child containers reuse existing AU accounts through the
approved AVM composition and retain immutable evidence for the agreed minimum. The
[Cosmos container](../../infra/main.bicep#L763), [Blob container loop](../../infra/main.bicep#L525),
and [immutability policy](../../infra/main.bicep#L784) are raw `Microsoft.*` declarations,
contrary to the plan's no-raw-resource commitment. The 2555-day default has no minimum bound;
no locked-policy lifecycle is shown. Source supports parent reuse, `/artefact_id`, no TTL,
and AU location propagation, not a live retention lock or deployment outcome. Resource counting
must include the immutability-policy grandchild as well as the two containers. The template is
[resource-group scoped](../../infra/main.bicep#L1), whereas T037/T063 name subscription what-if.

**Developer instructions:** use the existing AVM-approved storage/Cosmos pattern or obtain and
document an explicit approved exception before raw declarations. Enforce the agreed minimum
retention and an authorised policy-lock lifecycle; preserve existing accounts, container names,
partitions, residency, and retained data. Validate the actual complete resource graph, including
the policy child. Do not change platform policy or broaden Foundry residency exceptions. Depend
on AUD-037-003 for storage adapters and later platform-authorised policy discovery/what-if.

**Tester home and cases:** extend existing
[parameter tests](../../tests/devops/test_parameter_files.py#L65) for isolated retention/residency
parameters and [publish tests](../../tests/integration/spec_037/test_publish_pipeline.py#L13)
for adapter contracts; the existing infra test directory contains only a placeholder, not proof.
Assert both exact names/parents, `/artefact_id`, TTL policy, AU propagation, minimum retention,
lock-state expectations, and rejection of subminimum/non-AU inputs. Verify historical bytes
cannot be replaced or deleted after the approved lock. **Future validation:**
`pytest tests/devops/test_parameter_files.py tests/integration/spec_037 -q` after scoped additions;
then separately authorised Bicep/PSRule checks and resource-group-scoped what-if, followed
by a disposable staging WORM test. Expected: no new accounts/top-level services, all intended
child resources accounted for, and retention enforcement demonstrated. **Done:** source and
approved deployment evidence support the actual storage guarantee; none is executed here.

- [ ] AUD-037-016 Reconcile operator instructions and review closure with verifiable evidence

**Priority: IMPORTANT. Affected:** FR-004, FR-035, FR-038; SC-001, SC-007, SC-008,
SC-009, SC-011; T002, T007, T046, T061, T063, T067, T068, T069; all phase checkpoints,
quickstart workflows, quality checklist, and Step 8 follow-up duties.

**Expected versus observed:** commands match real entrypoints and completion evidence is
distinguishable from intent. The [quickstart](./quickstart.md#L34) calls `recompute` and
`validate --artefact`, but [argparse](../../scripts/evidence_pack_gate/__main__.py#L12) implements
only `--repo-root` and `--dry-run`. It promises merge-time publication and retry/rollback that
are not wired; its `@ama/e2e`/old browser path is not the current runner. The
[rehearsal script](../../scripts/spec_037_quickstart_rehearsal.ps1#L11) prints COMPLETE without
explicitly checking native exit codes; `$ErrorActionPreference` alone does not establish the
required native-command fail-fast behaviour. Static PowerShell parsing found zero errors;
the unusual opening string is not reported as a syntax defect.
The record claims 20 contract/4 API/2 integration passes, while current source defines 20/5/1
tests; this is historical evidence drift, not proof those historical numbers were impossible.
The record explicitly defers Workflow 1-4 execution. The quality checklist still says three
clarifications remain; the spec explicitly resolves them. CHK closure treats file existence as
execution, cites wrong CHK/task relationships, and has no individual exception links. Step 8's
85-persona total sums to 84 reported votes. R1's 404 implementation exists but its other error
paths are not verified; R6/R7 test-file existence does not settle discovery or assertion quality.

**Developer instructions:** after functional repairs, reconcile the supported CLI and operator
recipe, enforce the rehearsal wrapper's fail-fast exits, use current workspace package
names and scoped commands, and link genuine run artifacts to exact revision/date/environment.
Maintain historical review records rather than retroactively rewriting original task checkboxes.
Record remaining deferred/unverified outcomes explicitly with owners and dependencies; obtain
real auditor and timed-review decisions only later. Preserve supported renamed implementations,
root lock dependencies, and the relocated spec-037 Copilot context instead of creating duplicate
files solely to satisfy old paths. Depend on all relevant remediation tasks.

**Tester home and cases:** extend existing spec-037 gate/integration tests and
[workflow tests](../../tests/devops/test_cd_workflow.py#L15) for entrypoint/exit-code contracts.
Positive path exits zero only after
every required check; unknown arguments, missing module/dependency, first/middle/final native
failure, and absent data exit nonzero with an exact failure. Verify current command discovery,
traceable logs, and no model reruns. **Future validation:**
`pwsh -File scripts/spec_037_quickstart_rehearsal.ps1` on disposable data after the wrapper and
supported quickstart are repaired; then separately approved staging workflows 1-4, timed SC-001/008
review, Step 0 rubric re-review, CI required-check confirmation, and platform what-if. **Done:**
operator instructions are executable and every claimed result has independently inspectable
evidence, with all remaining unknowns honestly labelled.

## Full Static Population Assessment

All five complete JSON sidecars and all six primary Markdown outputs were inspected. Every one
of the 18 new risk detail files and the legacy three-risk file was read in full. RAI inspection
parsed every field and all 120 leaf cells, comparing complete cell objects before collapsing
identical repetitions for review; it was not a sample. All 37 feature rows and 15 tradeoff rows
were read, and every one of the 15 source ADRs, including the long ADR-036-011 amendments, was
read in full. No archive was downloaded or inferred from a PASS label.

| Population | Exact static result | Qualification |
| --- | --- | --- |
| Risk | 21 unique rows: Platform 3, AI 5, Operational 4, Jurisdictional 3, Data 3, Supply-chain 3. All score products agree. | 19 overdue at 2026-09-14; zero current flags/count. Two broken citation targets; legacy schema migration absent. |
| Roadmap | Five waves; nine jurisdiction codes covered; all waves cite 007, 024, 026. | Cohorts are state-lead, local-government, volunteer-ngo only. Utilities, transport, separate final Commonwealth cohort absent. |
| KPI | Ten unique rows; five criteria each have one leading and one lagging. | Zero `current_value`, zero `last_observed_utc`; only two unique `consolidates` paths; self-referential lagging source. |
| RAI | Eight named baseline components; 15 leaf cells each; all 120 populated with `compliant`; one unique complete cell value per component. | Not a 256-cell matrix. No evaluation-output citations; no evidence of review decisions. |
| Feature ledger | 37 rows versus 37 tracked numbered spec documents at HEAD; 36 identities intersect. | Missing 001-arch-docs-refresh; extra 004-rubric-gap-closure. No tracked 002 spec was found, so no synthetic 002 gap is invented. |
| Tradeoff log | All 15 source ADR filenames represented exactly once. | Content fidelity fails despite filename equality; local-vs-cross-jurisdiction tension absent. |
| Manual metadata | All five `rows[]` populations are 100% manual: 21/21, 5/5, 10/10, 8/8, 37/37. | The ledger also has 15 manual tradeoffs: full combined row count is 52, not 37. All use generated implementer sign-off. |
| Publication/archive | Five fixed uuid5 IDs with the same 2026-05-11 publication time are in source; Docker copies the five sidecars. | No connected publisher or Blob history reader. Actual immutable archive contents, retention lock, and prior versions are UNVERIFIED. |
| Citations | Risk 37, roadmap 22, KPI 27, RAI 272, ledger 39 nested reference objects. | First four have zero section fields. Ledger has two wave-description sections that are not headings in the cited spec. |
| Schemas/tests | Six canonical/runtime pairs byte-identical; 20 schema/gate + five API + one integration test definitions. | Equality is inspected state, not a CI equality check; definitions are not collected/executed pass results. |

### Feature Inventory Reconciliation

This is a complete identity comparison at the verified HEAD, not an audit of those other specs.
The ledger row is source data, not evidence that the feature itself works. Duplicate number
families (001 and 036) remain distinct. All tracked nested spec paths were inventoried; no
extra archived/feature-folder spec document altered this set.

| Required source identity | Ledger presence | Interpretation |
| --- | --- | --- |
| 001-arch-docs-refresh | MISSING | Absent from the literal list and sidecar; no explicit supersession found in the bounded inventory. |
| 001-disaster-response-hub | IMPLEMENTED | Identity present; contribution assertions require AUD-037-012. |
| 003-rubric-gap-closure | IMPLEMENTED | Identity present, tagged hygiene. |
| 004-actor-github-agents | IMPLEMENTED | Identity present, tagged hygiene. |
| 005-data-source-governance | IMPLEMENTED | Identity present, tagged hygiene. |
| 006-data-ingestion-storage | IMPLEMENTED | Identity present, tagged hygiene. |
| 007-simulation-tenant-isolation | IMPLEMENTED | Identity present, tagged hygiene. |
| 008-communication-agent | IMPLEMENTED | Identity present; magnitude not independently established. |
| 009-evacuation-agent | IMPLEMENTED | Identity present; magnitude not independently established. |
| 010-monitoring-agent | IMPLEMENTED | Identity present; magnitude not independently established. |
| 011-resource-allocation-agent | IMPLEMENTED | Identity present; magnitude not independently established. |
| 012-risk-assessment-agent | IMPLEMENTED | Identity present; follow-up heading invalid. |
| 013-root-readme | IMPLEMENTED | Identity present, tagged hygiene. |
| 014-azure-openai-integration | IMPLEMENTED | Identity present, tagged hygiene. |
| 015-performance-benchmarks | IMPLEMENTED | Identity present; follow-up heading invalid. |
| 016-automated-demo-script | IMPLEMENTED | Coverage-only hygiene row explicitly excluded from this implementation scope. |
| 017-cd-pipeline | IMPLEMENTED | Identity present, tagged hygiene. |
| 018-aidr-guidance-integration | IMPLEMENTED | Identity present, tagged hygiene. |
| 019-aidr-additional-guidances | IMPLEMENTED | Identity present, tagged hygiene. |
| 020-disaster-mapper-ui | IMPLEMENTED | Identity present, tagged hygiene. |
| 021-governance-dashboard | IMPLEMENTED | Identity present, tagged hygiene. |
| 022-multi-jurisdiction-filter | IMPLEMENTED | Identity present; magnitude not independently established. |
| 023-dashboard-real-data | IMPLEMENTED | Identity present, tagged hygiene. |
| 024-simulation-control-chat | IMPLEMENTED | Identity present, tagged hygiene. |
| 025-agent-spec-compliance | IMPLEMENTED | Identity present, tagged hygiene. |
| 026-sim-warp-playback | IMPLEMENTED | Identity present, tagged hygiene. |
| 027-spec-hardening | IMPLEMENTED | Identity present, tagged hygiene. |
| 028-capstone-alignment | IMPLEMENTED | Identity present, tagged hygiene. |
| 029-progressive-delivery-pipeline | IMPLEMENTED | Identity present, tagged hygiene. |
| 030-llm-eval-framework | IMPLEMENTED | Identity present; zero-magnitude lives-saved attribution is not measurement. |
| 031-simplify-cicd-pipeline | IMPLEMENTED | Identity present, tagged hygiene. |
| 032-rubric-improvements | IMPLEMENTED | Identity present, tagged hygiene. |
| 033-maf-adoption | IMPLEMENTED | Identity present, tagged hygiene. |
| 034-webapp-capstone-coverage | IMPLEMENTED | Identity present, tagged hygiene. |
| 035-webapp-capstone-closure | IMPLEMENTED | Identity present, tagged hygiene. |
| 036-foundry-rag-grounding | IMPLEMENTED | Identity present; magnitude not independently established. |
| 036-sim-agent-extend | IMPLEMENTED | Identity present; ADR ownership is misrepresented separately. |
| 004-rubric-gap-closure (extra) | CONFLICT | Sidecar identity has no tracked matching spec; do not silently equate it to 003. |

### ADR Fidelity

All rows below refer to the existing log and sidecar; filename coverage is 15/15, but semantic
coverage is not. AUD-037-012 owns corrections, preserving each source ADR's decisions.

| Source ADR | Status | Actual source versus log |
| --- | --- | --- |
| [ADR-036-001](../../docs/aidr/decisions/ADR-036-001-real-sub-agent-invocation.md#L6) | CONFLICT | Simulation HTTP/httpx production adapters; log attributes Foundry/MAF migration and different alternatives. |
| [ADR-036-002](../../docs/aidr/decisions/ADR-036-002-direct-rest-lifecycle.md#L25) | CONFLICT | Direct operator abort/pause/resume bypasses LLM; log says REST migration anchors/SDK alternatives. |
| [ADR-036-003](../../docs/aidr/decisions/ADR-036-003-cosmos-session-consistency.md#L31) | CONFLICT | Simulation session-token and sequence consistency; log names RAG freshness/Foundry owner and omits bounded-staleness alternative. |
| [ADR-036-004](../../docs/aidr/decisions/ADR-036-004-apim-token-bucket-circuit-breaker.md#L6) | CONFLICT | Simulation telemetry injection and deterministic fallback; general rate-limit summary omits actual feature and key alternatives. |
| [ADR-036-005](../../docs/aidr/decisions/ADR-036-005-cascade-etag-optimistic-concurrency.md#L27) | CONFLICT | ETag thread-cap enforcement with bounded retry; log's alternatives and Foundry attribution do not match. |
| [ADR-036-006](../../docs/aidr/decisions/ADR-036-006-lessons-capture-blob-worm.md#L6) | PARTIAL | Blob retention headline preserved; simulation lessons/legal-hold context and alternatives replaced with spec-030/Foundry rationale. |
| [ADR-036-007](../../docs/aidr/decisions/ADR-036-007-distributed-sequence-allocator.md#L36) | CONFLICT | Per-simulation ETag sequence counter and fail-closed DLQ; log invents DB-sequence/ULID alternatives and hot-partition rationale. |
| [ADR-036-008](../../docs/aidr/decisions/ADR-036-008-sli-thresholds-rationale.md#L6) | CONFLICT | Five explicit simulation SLIs and staging obligations; log replaces them with generic tiering mapped to 015/Foundry. |
| [ADR-036-009](../../docs/aidr/decisions/ADR-036-009-idempotency-cache-design.md#L39) | PARTIAL | 24h TTL is accurate; actual Cosmos/JCS, conflict/replay, and RBAC alternatives are omitted, extra Foundry ownership unsupported. |
| [ADR-036-010](../../docs/aidr/decisions/ADR-036-010-cycle-2-amendment-cycle.md#L61) | CONFLICT | Eight concrete breaking correlation/SLI/dispatch amendments; log turns them into per-deployment review cadence. |
| [ADR-036-011](../../docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md#L94) | CONFLICT | KQL canonicalisation/staging enforcement plus cycles 4/5 corrections; log says only cross-spec coupling and misses binding alternatives. |
| [ADR-037-01](../../docs/aidr/decisions/adr-037-01-text-first-evidence-pack.md#L16) | IMPLEMENTED | Text-first decision, alternatives and feature attribution are faithfully represented; execution not implied. |
| [ADR-037-02](../../docs/aidr/decisions/adr-037-02-executive-shell-reuse.md#L11) | PARTIAL | Main shell decision represented; log substitutes an embedded-route alternative for the actual pure-Markdown alternative. |
| [ADR-037-03](../../docs/aidr/decisions/adr-037-03-manual-evidence-cap.md#L16) | IMPLEMENTED | Per-artefact cap and human override decision/alternatives represented; generated sign-off does not prove approval. |
| [ADR-037-04](../../docs/aidr/decisions/adr-037-04-three-layer-append-only.md#L11) | IMPLEMENTED | Three-layer decision and alternatives represented; runtime implementation is separately PARTIAL. |

## Original Task Coverage

All 69 task definition lines in [the original task list](./tasks.md#L27) are represented once;
all use `[X]` at the audited revision. There are no suffix task definitions in this source.
Dependency-note repetitions are not new tasks. Historical red/green execution is UNVERIFIED for
every testing task; IMPLEMENTED below refers only to the stated authored source portion.

| Original ID | Original state | Status | Concrete evidence and explanation | Follow-up |
| --- | --- | --- | --- | --- |
| T001 | [X] | IMPLEMENTED | All 11 enumerated directories and their `.gitkeep` files exist; the text says ten but enumerates eleven. [Schema home](../../packages/schemas/spec_037/README.md#L1), [route](../../apps/api/app/api/routes/governance/evidence_pack.py#L1), [gate](../../scripts/evidence_pack_gate/gate.py#L1) confirm populated owners. | none |
| T002 | [X] | IMPLEMENTED | [Root dependency declarations](../../pyproject.toml#L17) and [tracked root lock metadata](../../uv.lock#L43) contain jsonschema/pyyaml. Lock execution not performed. | none |
| T003 | [X] | IMPLEMENTED | [Web devDependencies](../../apps/web/package.json#L38) and [lock importer](../../pnpm-lock.yaml#L64) contain both axe packages. Install outcome unverified. | none |
| T004 | [X] | PARTIAL | Six mirrors byte-equal now; [README](../../packages/schemas/spec_037/README.md#L14) documents canonical ownership but wrongly claims CI equality checking. | AUD-037-005, AUD-037-013 |
| T005 | [X] | PARTIAL | Both [root CSV](../../tests/contract/spec_037/_traceability.csv#L1) and [API CSV](../../apps/api/tests/contract/spec_037/_traceability.csv#L1) have the header and rows; planned lint absent. | AUD-037-013 |
| T006 | [X] | IMPLEMENTED | [Metric trace self-flag](../shared/capstone-metric-trace.md#L34) uses the exact hygiene tag and cites 028 FR-020. | none |
| T007 | [X] | PARTIAL | Required content exists in [relocated context](../../.github/agents/copilot-instructions.md#L66); old path absent. Updater execution/preservation at time of run unverified; do not create duplicate context. | AUD-037-016 |
| T008 | [X] | PARTIAL | [Risk tests](../../tests/contract/spec_037/test_risk_register_schema.py#L36) cover six-category positive and missing treatment; not missing-category or product checks; missing mirrors skip. | AUD-037-005, AUD-037-009, AUD-037-013 |
| T009 | [X] | PARTIAL | [Roadmap tests](../../tests/contract/spec_037/test_adoption_roadmap_schema.py#L27) cover jurisdiction positive/missing rollback, not cohort order or per-jurisdiction agency/safety semantics. | AUD-037-005, AUD-037-010, AUD-037-013 |
| T010 | [X] | PARTIAL | [KPI tests](../../tests/contract/spec_037/test_executive_kpi_surface_schema.py#L37) assert minItems, not leading/lagging population uniqueness or actual sources. | AUD-037-005, AUD-037-008, AUD-037-013 |
| T011 | [X] | PARTIAL | [RAI tests](../../tests/contract/spec_037/test_responsible_ai_register_schema.py#L79) cover one component/missing fairness field, not full inventory or evidence quality. | AUD-037-005, AUD-037-011, AUD-037-013 |
| T012 | [X] | PARTIAL | [Ledger tests](../../tests/contract/spec_037/test_feature_value_ledger_schema.py#L53) use one spec/ADR, not universal inventory or nonzero-gap follow-ups. | AUD-037-005, AUD-037-012, AUD-037-013 |
| T013 | [X] | PARTIAL | [Metadata tests](../../tests/contract/spec_037/test_publication_gate_metadata_schema.py#L9) cover basic cap/range; omit equality boundary, invalid dates and incomplete/blank sign-off. | AUD-037-005, AUD-037-013 |
| T014 | [X] | PARTIAL | [List test](../../apps/api/tests/contract/spec_037/test_route_list_artefacts.py#L9) validates five IDs but accepts synthetic missing-data summaries; naked router fixture. | AUD-037-002, AUD-037-007, AUD-037-013 |
| T015 | [X] | PARTIAL | [Latest test](../../apps/api/tests/contract/spec_037/test_route_get_artefact.py#L9) checks keys only and tolerates 404/422 for unknown IDs; no schema/auth assertions. | AUD-037-002, AUD-037-007, AUD-037-013 |
| T016 | [X] | PARTIAL | [History test](../../apps/api/tests/contract/spec_037/test_route_get_publication.py#L9) permits 200 or 404, so no immutable historical snapshot is required. | AUD-037-002, AUD-037-003, AUD-037-013 |
| T017 | [X] | PARTIAL | [Health test](../../apps/api/tests/contract/spec_037/test_route_health.py#L9) accepts any status enum and an empty list; no outage/freshness proof. | AUD-037-007, AUD-037-013 |
| T018 | [X] | PARTIAL | [Ratio tests](../../tests/contract/spec_037/test_publication_gate_ratio_recompute.py#L46) check 2/10 and mismatch helper only, omit count equality and tradeoffs. | AUD-037-005, AUD-037-013 |
| T019 | [X] | PARTIAL | [Unsigned-cap test](../../tests/contract/spec_037/test_publication_gate_cap_no_signoff.py#L15) tests helper false, not incomplete signatures or nonzero CLI exit. | AUD-037-005, AUD-037-013 |
| T020 | [X] | PARTIAL | [Signed-cap test](../../tests/contract/spec_037/test_publication_gate_cap_with_signoff.py#L15) covers one syntactically complete object, not genuine approval or full gate. | AUD-037-005, AUD-037-006, AUD-037-013 |
| T021 | [X] | PARTIAL | [Link tests](../../tests/contract/spec_037/test_publication_gate_link_check.py#L13) cover one inline file link only; JSON/heading/log scope absent. | AUD-037-004, AUD-037-013 |
| T022 | [X] | PARTIAL | [Ratio unit tests](../../apps/web/src/app/governance/executive/_components/__tests__/ManualRowRatioStrip.test.tsx#L17) assert initial five values/ARIA, not updates; runner excludes file. | AUD-037-008, AUD-037-013 |
| T023 | [X] | PARTIAL | [Ladder unit test](../../apps/web/src/app/governance/executive/_components/__tests__/KpiLadder.test.tsx#L17) does not inspect imports or PersonaWorkspace composition. | AUD-037-008, AUD-037-013 |
| T024 | [X] | PARTIAL | [Banner tests](../../apps/web/src/app/governance/executive/_components/__tests__/StaleTelemetryBanner.test.tsx#L9) cover local boolean rendering; route/page outage path and runner discovery absent. | AUD-037-007, AUD-037-013 |
| T025 | [X] | IMPLEMENTED | [Axe helper](../../apps/web/tests/e2e/spec-037/axe.setup.ts#L23) implements tags and serious/critical assertion; execution/discovery belongs to T061. | AUD-037-013 |
| T026 | [X] | PARTIAL | [RiskRow](../../packages/domain/src/domain/models/evidence_pack/risk_row.py#L19) enforces fields/products, but gate/router never use it and date remains a string. | AUD-037-005, AUD-037-009 |
| T027 | [X] | PARTIAL | [AdoptionWave](../../packages/domain/src/domain/models/evidence_pack/adoption_wave.py#L26) exists; missing aggregate order/agency checks and no runtime wiring. | AUD-037-005, AUD-037-010 |
| T028 | [X] | PARTIAL | [KpiRow](../../packages/domain/src/domain/models/evidence_pack/kpi_row.py#L25) exists; no per-criterion population/freshness validation and not consumed by envelope. | AUD-037-005, AUD-037-007 |
| T029 | [X] | PARTIAL | [RaiRow/RaiCell](../../packages/domain/src/domain/models/evidence_pack/rai_row.py#L15) require fields and N/A justification, but no discriminated union or inventory/evidence enforcement. | AUD-037-005, AUD-037-011 |
| T030 | [X] | PARTIAL | [FeatureValueRow](../../packages/domain/src/domain/models/evidence_pack/feature_value_row.py#L34) and [TradeoffRow](../../packages/domain/src/domain/models/evidence_pack/tradeoff_row.py#L21) exist; no required positive-gap follow-up or source-inventory fidelity. | AUD-037-005, AUD-037-012 |
| T031 | [X] | PARTIAL | [Metadata model](../../packages/domain/src/domain/models/evidence_pack/publication_gate_metadata.py#L22) checks declared count ratio but not actual rows or unnecessary sign-off; dates/cap policy diverge. | AUD-037-005 |
| T032 | [X] | PARTIAL | [Envelope](../../packages/domain/src/domain/models/evidence_pack/evidence_pack_artefact.py#L13) has generic dictionaries, not the six typed row imports promised. | AUD-037-005 |
| T033 | [X] | PARTIAL | [Ratio service](../../apps/api/app/services/governance/manual_row_ratio.py#L28) counts `rows` and emits a gauge, not the specified counter; publisher-only reachability, combined denominator unresolved. | AUD-037-005, AUD-037-014 |
| T034 | [X] | PARTIAL | [Writer](../../apps/api/app/services/governance/evidence_pack_writer.py#L36) sequences optional callbacks but performs no gate validation or production persistence wiring. | AUD-037-003, AUD-037-006, AUD-037-014 |
| T035 | [X] | MISSING | [Writer/read helper](../../apps/api/app/services/governance/evidence_pack_writer.py#L110) has no production audit-writer adapter/caller; no override event; [generic audit](../../apps/api/app/middleware/audit_appender.py#L89) skips GETs. Bounded caller search found only publish test. | AUD-037-002, AUD-037-003 |
| T036 | [X] | PARTIAL | [Four routes](../../apps/api/app/api/routes/governance/evidence_pack.py#L113) are registered; security, history and unavailable-data contracts fail source inspection. | AUD-037-002, AUD-037-003, AUD-037-007 |
| T037 | [X] | PARTIAL | [Cosmos child](../../infra/main.bicep#L763) has correct name/parent/partition; raw resource contradicts AVM requirement and live what-if unverified. | AUD-037-015 |
| T038 | [X] | PARTIAL | [Blob/policy](../../infra/main.bicep#L784) exists with 2555-day default; no minimum/lock lifecycle or AVM composition, live WORM unverified. | AUD-037-015 |
| T039 | [X] | PARTIAL | [Client](../../apps/web/src/lib/governance/evidence-pack/client.ts#L31) has four fetch helpers but no bearer; [types](../../apps/web/src/lib/governance/evidence-pack/types.ts#L39) are manually partial, no codegen/parity test found. | AUD-037-002, AUD-037-005, AUD-037-008 |
| T040 | [X] | PARTIAL | [Ratio strip](../../apps/web/src/app/governance/executive/_components/ManualRowRatioStrip.tsx#L23) has ARIA and data-driven entries, but missing/long values, reflow, updates and axe execution not established. | AUD-037-008, AUD-037-013 |
| T041 | [X] | PARTIAL | [Ladder](../../apps/web/src/app/governance/executive/_components/KpiLadder.tsx#L29) groups text without charts; no PersonaWorkspace/audit primitive reuse. | AUD-037-008 |
| T042 | [X] | IMPLEMENTED | [Banner](../../apps/web/src/app/governance/executive/_components/StaleTelemetryBanner.tsx#L14) renders the supplied stale flag/timestamp; source-level component behaviour only. Parent detection remains broken. | AUD-037-007 |
| T043 | [X] | PARTIAL | [Server page](../../apps/web/src/app/governance/executive/page.tsx#L23) fetches three resources and composes local components, but swallows failures, no shell reuse or page snapshot test. | AUD-037-007, AUD-037-008, AUD-037-013 |
| T044 | [X] | MISSING | [Current navigation](../../apps/web/src/app/governance/dashboard/layout.tsx#L7) lacks executive route; bounded search of web source found no equivalent navigation link. Direct route existence is not hub navigation. | AUD-037-008 |
| T045 | [X] | PARTIAL | [CLI](../../scripts/evidence_pack_gate/__main__.py#L12) and [gate](../../scripts/evidence_pack_gate/gate.py#L200) exist, but checks are schema/ratio/cap then links, not prescribed fail-fast order; population/citations/semantics incomplete. | AUD-037-001, AUD-037-004, AUD-037-005 |
| T046 | [X] | PARTIAL | [CI job](../../.github/workflows/ci.yml#L406) runs after quality with Python/pip, not planned pnpm/uv; [protection intent](../../.github/branch-protection.json#L4) omits it and actual enforcement unverified. | AUD-037-013 |
| T047 | [X] | PARTIAL | [Link roots](../../scripts/evidence_pack_gate/gate.py#L191) omit paired log and superseded documents; JSON references/headings ignored. | AUD-037-004 |
| T048 | [X] | PARTIAL | [Metrics catalogue](../../docs/governance-hub/observability/metrics-catalogue.md#L9) declares thresholds, but CI echo/duration log/failure-rate omission are not metric emission. R2 explicitly defers export. | AUD-037-014 |
| T049 | [X] | IMPLEMENTED | [Hub section](../../docs/governance-hub/index.md#L51) links five artefacts, paired log and executive source page. | none |
| T050 | [X] | IMPLEMENTED | [Governance instruction](../../.github/instructions/governance-discovery.instructions.md#L203) names job/implementation. New-agent RAI duty is separate and not implemented. | AUD-037-011 |
| T051 | [X] | IMPLEMENTED | [Dashboard banner](../../docs/governance-dashboard.md#L147), [SLO banner](../../docs/governance-hub/observability/slo.md#L3), [catalogue banner](../../docs/governance-hub/observability/metrics-catalogue.md#L3) preserve operational role. Broader six-source coverage remains partial. | AUD-037-008 |
| T052 | [X] | IMPLEMENTED | [Text-first ADR](../../docs/aidr/decisions/adr-037-01-text-first-evidence-pack.md#L16) has decision/rationale/alternatives and appears in log. Acceptance's T057 log pointer is stale; T060 owns log. | none |
| T053 | [X] | PARTIAL | [Shell ADR](../../docs/aidr/decisions/adr-037-02-executive-shell-reuse.md#L11) exists with all sections; log loses one actual alternative, actual shell implementation diverges. | AUD-037-008, AUD-037-012 |
| T054 | [X] | IMPLEMENTED | [Cap ADR](../../docs/aidr/decisions/adr-037-03-manual-evidence-cap.md#L16) records decision/alternatives and log entry. Approval is not proved. | none |
| T055 | [X] | IMPLEMENTED | [Append-only ADR](../../docs/aidr/decisions/adr-037-04-three-layer-append-only.md#L11) has decision/alternatives and log entry; actual layers remain incomplete. | none |
| T056 | [X] | PARTIAL | [Risk JSON](../../docs/risk-register/risk-register.json#L21) has 21 rows/six categories; legacy schema, current overdue output, citations and dynamic register obligations incomplete. `index.json` acceptance wording is superseded by explicit canonical sidecar I4. | AUD-037-004, AUD-037-006, AUD-037-009 |
| T057 | [X] | PARTIAL | [Roadmap JSON](../../docs/governance-hub/adoption-roadmap/roadmap.json#L21) covers nine jurisdiction codes and training citations but wrong cohorts/order and incomplete per-pilot safety/lessons. | AUD-037-010 |
| T058 | [X] | PARTIAL | [KPI JSON](../../docs/governance-hub/executive-kpi/surface.json#L21) has ten criterion/kind rows; no observations, incomplete source consolidation/display, timed review deferred. | AUD-037-007, AUD-037-008, AUD-037-016 |
| T059 | [X] | CONFLICT | [RAI output](../../docs/governance-hub/rai-register/responsible-ai-register.md#L18) has eight named components and 120 actual leaf cells, not the task's nine/288; repeated compliance and spec-only evidence incomplete. | AUD-037-005, AUD-037-011 |
| T060 | [X] | PARTIAL | [Ledger](../shared/feature-value-ledger.json#L21) has all 15 ADR identities but wrong owners/content, wrong spec set, missing tension and invalid wave follow-up heading. | AUD-037-004, AUD-037-006, AUD-037-012 |
| T061 | [X] | PARTIAL | [Browser suite](../../apps/web/tests/e2e/spec-037/governance-executive.spec.ts#L11) exists, but not discovered and focus/zoom/update assertions are weak. Step 8 R6/R7 only establish file presence. | AUD-037-008, AUD-037-013 |
| T062 | [X] | PARTIAL | [Each CSV](../../tests/contract/spec_037/_traceability.csv#L1) has 53 rows/49 IDs, but non-test/missing/irrelevant nodes and no CI coverage assertion. | AUD-037-013 |
| T063 | [X] | UNVERIFIED | [Closure deferral](./checklists/capstone-evidence-pack.checklist.md#L240) and [plan](./plan.md#L296) claim local checks but defer live what-if; scope/resource count/AVM issues remain. | AUD-037-015, AUD-037-016 |
| T064 | [X] | IMPLEMENTED | [Risk carve-out citation](../../docs/risk-register/RISK-NEW-003.md#L20) and [RAI builder input](../../scripts/evidence_pack_gate/generate_artefacts.py#L637) name the existing YAML. Approval/current deployment validity remains UNVERIFIED. | none |
| T065 | [X] | PARTIAL | [Ratio gauge](../../apps/api/app/services/governance/manual_row_ratio.py#L40), metadata and catalogue exist; no proven production invocation/export, not a KPI-row metric. | AUD-037-014 |
| T066 | [X] | PARTIAL | [Hub entries](../../docs/governance-hub/index.md#L51) include artefacts/page/ADRs and gate text, not a constraint link; scannability review unverified, unrelated pre-existing hub links not fixed here. | AUD-037-004, AUD-037-016 |
| T067 | [X] | UNVERIFIED | [Canonical rehearsal record](./rehearsal-results.md#L3) explicitly defers end-to-end execution. Local PASS labels do not prove four workflows. | AUD-037-016 |
| T068 | [X] | PARTIAL | [Checklist closure](./checklists/capstone-evidence-pack.checklist.md#L240) asserts 84 closed via tasks/CSVs, not item-specific review evidence; exceptions unlinked and many claims contradicted. | AUD-037-013, AUD-037-016 |
| T069 | [X] | UNVERIFIED | [Post-polish note](./plan.md#L296) claims byte identity/resource counts but records no independently inspectable command output and defers live review. Constitution unchanged by this audit only. | AUD-037-015, AUD-037-016 |

## Functional Requirement Coverage

Every FR definition is represented separately. The evidence column names the actual controlling
source or published data, not the original checkbox. Schema existence and valid-looking manual
objects are not human approval or executed validation. No numbered NFRs are defined locally;
binding unnumbered constraints and review duties are covered in the subsequent tables.

| Requirement | Status | Expected versus observed evidence | Follow-up |
| --- | --- | --- | --- |
| [FR-001](./spec.md#L118) | PARTIAL | [Hub](../../docs/governance-hub/index.md#L51) has exactly five logical artefacts with ledger/log paired; [gate](../../scripts/evidence_pack_gate/gate.py#L200) does not require all five and publication is unwired. | AUD-037-001, AUD-037-003 |
| [FR-002](./spec.md#L119) | IMPLEMENTED | All five Markdown/JSON artefacts are tracked under docs/shared and [hub entries](../../docs/governance-hub/index.md#L51) reference each. Durable runtime snapshots are a separate FR-005 gap. | none |
| [FR-003](./spec.md#L120) | PARTIAL | [Risk details](../../docs/risk-register/RISK-NEW-003.md#L17) and JSON carry references but no section-level citations in risk/roadmap/KPI/RAI; two targets are broken, many Markdown references are code spans. | AUD-037-004, AUD-037-012 |
| [FR-004](./spec.md#L121) | IMPLEMENTED | [Generator write targets](../../scripts/evidence_pack_gate/generate_artefacts.py#L1095) exclude the constitution. This audit made no such change; historical byte-identity assertion in T069 remains UNVERIFIED. | AUD-037-016 |
| [FR-005](./spec.md#L122) | PARTIAL | [Writer](../../apps/api/app/services/governance/evidence_pack_writer.py#L36), schema and generator lack enforced immutable revisions; auth/read audit and mandatory storage adapters absent. AU parents exist in source only. | AUD-037-002, AUD-037-003, AUD-037-006, AUD-037-015 |
| [FR-006](./spec.md#L123) | PARTIAL | [Discovery entry](../../.github/instructions/governance-discovery.instructions.md#L203) names publication constraint; no automatic new-AI-row shipping gate, and live policy/required-check posture not evidenced. | AUD-037-011, AUD-037-013 |
| [FR-007](./spec.md#L124) | IMPLEMENTED | [Metric trace](../shared/capstone-metric-trace.md#L34) carries exact non-capstone-critical-path / delivery-hygiene flag and 028 FR-020 citation. | none |
| [FR-008](./spec.md#L125) | PARTIAL | [CI invocation](../../.github/workflows/ci.yml#L424) exists; [checker](../../scripts/evidence_pack_gate/gate.py#L100) ignores structured refs/headings/log directory. | AUD-037-001, AUD-037-004, AUD-037-013 |
| [FR-009](./spec.md#L126) | PARTIAL | [Schema validation](../../scripts/evidence_pack_gate/gate.py#L163) and cap helper exist, but mandatory population, semantic parity, date formats/counts, complete citation scope and runtime publication enforcement are missing. | AUD-037-001, AUD-037-003, AUD-037-005 |
| [FR-010](./spec.md#L130) | IMPLEMENTED | [Complete risk sidecar](../../docs/risk-register/risk-register.json#L21) has six categories, counts 3/5/4/3/3/3. Future aggregate schema enforcement still needed. | AUD-037-005 |
| [FR-011](./spec.md#L131) | PARTIAL | All 21 JSON rows have numerical fields/products and owners, but [legacy Markdown](../../docs/risk-register/RISK-AOAI-001.md#L3) lacks them and some risk rows cite only an agent/governance document rather than a spec/ADR. | AUD-037-004, AUD-037-009 |
| [FR-012](./spec.md#L132) | PARTIAL | [Original three-risk file](../../docs/risk-register/RISK-AOAI-001.md#L1) survives; it was not adapted or validated under the new numeric schema. Parallel JSON is not a migration of that file. | AUD-037-009 |
| [FR-013](./spec.md#L133) | PARTIAL | [Index](../../docs/risk-register/index.md#L12) is descending by residual score, but [clock](../../scripts/evidence_pack_gate/generate_artefacts.py#L836) is fixed and no overdue summary exists. | AUD-037-009 |
| [FR-014](./spec.md#L134) | PARTIAL | Fields support L/C scoring, but [risk-manager matrix and treatment authority](../../.github/agents/operational/risk-manager.agent.md#L130) are not a dynamic, archive-backed register in this pack. | AUD-037-003, AUD-037-009 |
| [FR-015](./spec.md#L138) | CONFLICT | [Roadmap](../../docs/governance-hub/adoption-roadmap/roadmap.md#L10) skips utilities/transport and places Commonwealth in state-lead WAVE-03, before local-government and volunteer. No explicit amendment authorises this. | AUD-037-010 |
| [FR-016](./spec.md#L139) | PARTIAL | [Wave JSON](../../docs/governance-hub/adoption-roadmap/roadmap.json#L21) has cadence/citations/change/rollback strings; generic agency placeholders, missing required cohorts, and absent lessons/M&E loop limit actual adoption guidance. | AUD-037-010 |
| [FR-017](./spec.md#L140) | PARTIAL | WAVE-01 expressly preserves manual/no-loss defaults; [later pilots](../../docs/governance-hub/adoption-roadmap/roadmap.md#L95) rely on prose inheritance or omit manual/no-loss recovery. | AUD-037-010 |
| [FR-018](./spec.md#L141) | IMPLEMENTED | First three waves provide all eight AU jurisdictions plus Commonwealth, explicit lead agencies and at least one gate in [roadmap JSON](../../docs/governance-hub/adoption-roadmap/roadmap.json#L21). Readiness achievement is not claimed. | AUD-037-010 |
| [FR-019](./spec.md#L145) | IMPLEMENTED | [Ten KPI rows](../../docs/governance-hub/executive-kpi/surface.json#L21) contain exactly one leading and one lagging for each of five criteria. Future schema population guard absent. | AUD-037-005 |
| [FR-020](./spec.md#L146) | PARTIAL | [KPI definitions](../../docs/governance-hub/executive-kpi/surface.json#L21) carry owners/cadences/targets/bands; self-reference and only two consolidation paths fall short of all six named sources. | AUD-037-004, AUD-037-008 |
| [FR-021](./spec.md#L147) | PARTIAL | Markdown/JSON/[read-only page](../../apps/web/src/app/governance/executive/page.tsx#L23) exist; shell/audit reuse, complete fields, bearer path, stable five-ratio error state and navigation are incomplete. | AUD-037-002, AUD-037-007, AUD-037-008 |
| [FR-022](./spec.md#L148) | PARTIAL | Three [document banners](../../docs/governance-dashboard.md#L147) exist and preserve operational roles. No 015/021/030 spec-source consolidation banners were found; page does not render superseded links. | AUD-037-004, AUD-037-008 |
| [FR-023](./spec.md#L149) | PARTIAL | [Local banner](../../apps/web/src/app/governance/executive/_components/StaleTelemetryBanner.tsx#L14) renders a supplied stale flag; actual health lacks sink freshness and null-fetch state disables warning. | AUD-037-007 |
| [FR-024](./spec.md#L153) | PARTIAL | [Eight baseline components](../../docs/governance-hub/rai-register/responsible-ai-register.md#L22) exist with simulation explicitly included; full production posture evidence is not established by repeated cells. | AUD-037-011 |
| [FR-025](./spec.md#L154) | PARTIAL | Four framework keys and four NIST profiles exist in [JSON](../../docs/governance-hub/rai-register/responsible-ai-register.json#L31); one repeated summary per component is not evaluation against each framework. | AUD-037-011 |
| [FR-026](./spec.md#L155) | PARTIAL | Eight principle keys exist per row; [builder](../../scripts/evidence_pack_gate/generate_artefacts.py#L547) repeats one compliant paragraph instead of distinct human/fairness/privacy/safety assessments. | AUD-037-011 |
| [FR-027](./spec.md#L156) | PARTIAL | Current 120 cells are nonblank, but [N/A schema](./contracts/responsible-ai-register.schema.json#L49) permits empty justification and does not reject whitespace; meaningful posture remains unsupported. | AUD-037-005, AUD-037-011 |
| [FR-028](./spec.md#L157) | PARTIAL | [Generator](../../scripts/evidence_pack_gate/generate_artefacts.py#L595) invokes no evaluation, but every eval reference is a spec document, not spec-030 output evidence. | AUD-037-011 |
| [FR-029](./spec.md#L158) | PARTIAL | [RAI Markdown](../../docs/governance-hub/rai-register/responsible-ai-register.md#L1) and JSON pair exist; Markdown truncates evidence and false cell count, archive/read integration absent. | AUD-037-003, AUD-037-006, AUD-037-011 |
| [FR-030](./spec.md#L162) | PARTIAL | [37-row ledger](../shared/feature-value-ledger.json#L21) has hygiene tags but one wrong/missing identity versus the complete HEAD population. | AUD-037-012 |
| [FR-031](./spec.md#L163) | PARTIAL | [Contribution fields](../shared/feature-value-ledger.json#L38) exist, but magnitudes/gaps are hard-coded, unit/baseline interpretation and source derivation are unsupported. Numeric presence is not measured value. | AUD-037-006, AUD-037-012 |
| [FR-032](./spec.md#L164) | PARTIAL | [All 15 log rows](../../docs/governance-hub/feature-value-ledger/tradeoff-log.md#L11) exist; actual ADR ownership/alternatives/rationale disagree as detailed above. | AUD-037-012 |
| [FR-033](./spec.md#L165) | PARTIAL | Both nonzero-gap rows carry follow-up objects, but [builder](../../scripts/evidence_pack_gate/generate_artefacts.py#L706) points to a wave-description section absent from its cited spec; openness/closure effect not evidenced. | AUD-037-004, AUD-037-012 |
| [FR-034](./spec.md#L166) | PARTIAL | [Ledger](../shared/feature-value-ledger.md#L3) links the metric trace; no reciprocal link, population/value mismatch means inverse semantics are incomplete. | AUD-037-012 |
| [FR-035](./spec.md#L170) | PARTIAL | [Generator](../../scripts/evidence_pack_gate/generate_artefacts.py#L653) produces files, but transcribes literal source lists/decisions, overwrites publications and does not consume available source data. | AUD-037-003, AUD-037-006, AUD-037-012 |
| [FR-036](./spec.md#L171) | PARTIAL | [Tradeoff rows](../../docs/governance-hub/feature-value-ledger/tradeoff-log.md#L11) use speed/legality, automation/command and visibility/privacy tags; local/cross-jurisdiction absent. | AUD-037-012 |
| [FR-037](./spec.md#L172) | PARTIAL | Manual tags/role/cadence/target exist in every JSON row; [metadata](../shared/feature-value-ledger.json#L7) omits tradeoff population and generated Validated status is not review evidence. | AUD-037-005, AUD-037-006 |
| [FR-038](./spec.md#L173) | PARTIAL | All five ratio-1.0 outputs carry structurally complete sign-off; [generator](../../scripts/evidence_pack_gate/generate_artefacts.py#L30) authors it itself, actual approval unverified and policy parity/publication enforcement incomplete. | AUD-037-003, AUD-037-005, AUD-037-006 |

## Success Criterion Coverage

| Success criterion | Status | Evidence and limitation | Follow-up |
| --- | --- | --- | --- |
| [SC-001](./spec.md#L189) | UNVERIFIED | [Index](../../docs/risk-register/index.md#L12) permits reading top ten owners, but lacks current overdue data; [timed rehearsal](./rehearsal-results.md#L3) deferred. No sub-five-minute measurement obtained. | AUD-037-009, AUD-037-016 |
| [SC-002](./spec.md#L190) | PARTIAL | CI/checker source exists, but two structured citations are broken and full-link/schema populations are not enforced. No current pipeline outcome claimed. | AUD-037-001, AUD-037-004, AUD-037-005, AUD-037-013 |
| [SC-003](./spec.md#L191) | IMPLEMENTED | [Published roadmap](../../docs/governance-hub/adoption-roadmap/roadmap.json#L21) names all nine jurisdiction lanes with leads and gates. This is coverage, not pilot readiness/deployment approval. | none |
| [SC-004](./spec.md#L192) | PARTIAL | [Ten definitions](../../docs/governance-hub/executive-kpi/surface.json#L21) meet criterion/kind/owner/target/cadence structure, but source-of-truth linkage and displayed evidence incomplete. | AUD-037-008 |
| [SC-005](./spec.md#L193) | CONFLICT | Eight named components exist; [claimed 256 cells](../../docs/governance-hub/rai-register/responsible-ai-register.md#L18) versus 120 actual leaves and task expectation nine/288 require explicit resolution; no substantiated compliance population. | AUD-037-005, AUD-037-011 |
| [SC-006](./spec.md#L194) | PARTIAL | Full comparison: ledger intersects 36/37 tracked specs; 15/15 ADR IDs present but inaccurate contents. [Literal inventory](../../scripts/evidence_pack_gate/generate_artefacts.py#L653) is not an up-to-date universal ledger. | AUD-037-012 |
| [SC-007](./spec.md#L195) | UNVERIFIED | [Rehearsal](./rehearsal-results.md#L3) and [Step 8 log](./spec.md#L243) are not a preserved Step 0 rubric re-score with assessor evidence. No new grading/model run performed. | AUD-037-016 |
| [SC-008](./spec.md#L196) | UNVERIFIED | No timed executive review; [ladder](../../apps/web/src/app/governance/executive/_components/KpiLadder.tsx#L29) has no on-track state and current values are absent. Health-enum test does not establish comprehension. | AUD-037-007, AUD-037-008, AUD-037-016 |
| [SC-009](./spec.md#L197) | PARTIAL | No chart imports in scoped source and two container additions reuse parents; [page](../../apps/web/src/app/governance/executive/page.tsx#L44) does not reuse promised shell. Live infra graph remains UNVERIFIED. | AUD-037-008, AUD-037-015 |
| [SC-010](./spec.md#L198) | IMPLEMENTED | [Self-flag](../shared/capstone-metric-trace.md#L34) explicitly excludes 037 from metric attribution; it has no metric-contributing feature row in the inspected ledger. | none |
| [SC-011](./spec.md#L199) | PARTIAL | Structurally populated sign-offs cover current ratio-1.0 sidecars, not real approval; schema boundary/semantic and publisher gaps prevent an enforced universal guarantee. | AUD-037-003, AUD-037-005, AUD-037-006 |

## Acceptance Scenarios

Audit labels USn-ASn refer to the exact numbered Given/When/Then definitions. All 15 are present.

| Scenario | Status | Static evidence and unmet expectation | Follow-up |
| --- | --- | --- | --- |
| US1-AS1 [source](./spec.md#L31) | PARTIAL | [21 risks](../../docs/risk-register/risk-register.json#L21) cover six categories; automated universal validation is incomplete and not executed here. | AUD-037-005, AUD-037-009 |
| US1-AS2 [source](./spec.md#L32) | PARTIAL | Numeric new rows exist; legacy detailed file lacks required values and spec/ADR section citations are incomplete. [Legacy source](../../docs/risk-register/RISK-AOAI-001.md#L3). | AUD-037-004, AUD-037-009 |
| US1-AS3 [source](./spec.md#L33) | MISSING | [Frozen-date rendering](../../scripts/evidence_pack_gate/generate_artefacts.py#L836) has no current overdue counter; 19 overdue rows are unflagged. | AUD-037-009 |
| US2-AS1 [source](./spec.md#L47) | IMPLEMENTED | [Roadmap](../../docs/governance-hub/adoption-roadmap/roadmap.json#L21) includes nine lanes with named first-appearance leads and gates. | none |
| US2-AS2 [source](./spec.md#L48) | IMPLEMENTED | All five waves' cadence arrays cite existing 007/024/026 capabilities; [first-wave example](../../docs/governance-hub/adoption-roadmap/roadmap.json#L38), full population inspected. | none |
| US2-AS3 [source](./spec.md#L49) | PARTIAL | [WAVE-05](../../docs/governance-hub/adoption-roadmap/roadmap.md#L95) lacks explicit manual/no-loss rollback; other waves rely on inheritance. | AUD-037-010 |
| US3-AS1 [source](./spec.md#L63) | PARTIAL | [KPI JSON](../../docs/governance-hub/executive-kpi/surface.json#L21) has ten definition rows; a self-referential source and missing consolidation/rendered fields undermine complete evidence. | AUD-037-008 |
| US3-AS2 [source](./spec.md#L64) | PARTIAL | [Page](../../apps/web/src/app/governance/executive/page.tsx#L23) fetches repository sidecars with no actual observations or existing shell composition. No new chart import found. | AUD-037-007, AUD-037-008 |
| US3-AS3 [source](./spec.md#L65) | PARTIAL | Three banners exist, but [ladder](../../apps/web/src/app/governance/executive/_components/KpiLadder.tsx#L29) renders no superseded/source links and the six-source set is incomplete. | AUD-037-004, AUD-037-008 |
| US4-AS1 [source](./spec.md#L79) | PARTIAL | Eight baseline rows have four framework/eight principle keys; repeated cells, N/A validation gap and 4-by-8 contract conflict prevent full posture evidence. [Schema](./contracts/responsible-ai-register.schema.json#L49). | AUD-037-005, AUD-037-011 |
| US4-AS2 [source](./spec.md#L80) | MISSING | All evaluation-reference objects name specifications, not existing spec-030 output evidence. [RAI builder](../../scripts/evidence_pack_gate/generate_artefacts.py#L595) has no alternative output citation path. | AUD-037-011 |
| US4-AS3 [source](./spec.md#L81) | PARTIAL | Pair exists and rendering uses deterministic input, but [Markdown](../../docs/governance-hub/rai-register/responsible-ai-register.md#L18) truncates/miscounts and archive integration is absent. | AUD-037-003, AUD-037-006, AUD-037-011 |
| US5-AS1 [source](./spec.md#L95) | PARTIAL | Exact [ledger inventory](../shared/feature-value-ledger.md#L13) omits 001-arch-docs-refresh and adds nonexistent 004-rubric-gap-closure. | AUD-037-012 |
| US5-AS2 [source](./spec.md#L96) | PARTIAL | [Log](../../docs/governance-hub/feature-value-ledger/tradeoff-log.md#L11) lists 15 ADRs, but actual owners and decision content disagree. | AUD-037-012 |
| US5-AS3 [source](./spec.md#L97) | PARTIAL | Two positive-gap rows have nominal follow-ups; [generator](../../scripts/evidence_pack_gate/generate_artefacts.py#L706) cites a non-heading in this spec instead of an open, verifiable wave anchor. | AUD-037-004, AUD-037-012 |

## Edge Cases

| Edge | Status | Static assessment | Follow-up |
| --- | --- | --- | --- |
| EDGE-001 Stale citations [source](./spec.md#L103) | PARTIAL | [Checker](../../scripts/evidence_pack_gate/gate.py#L100) catches simple missing inline files, not JSON refs/headings/moved code-span references. | AUD-037-004 |
| EDGE-002 Schema drift [source](./spec.md#L104) | PARTIAL | [Risk missing-treatment test](../../tests/contract/spec_037/test_risk_register_schema.py#L56) exists, but mirror drift/semantic invariants/mandatory population not enforced. | AUD-037-001, AUD-037-005 |
| EDGE-003 Conflicting jurisdiction sequencing [source](./spec.md#L105) | MISSING | [Five-wave roadmap](../../docs/governance-hub/adoption-roadmap/roadmap.md#L10) has generic gates, no explicit readiness-first conflict/deviation record or corresponding test. | AUD-037-010 |
| EDGE-004 Superseded surface edited [source](./spec.md#L106) | PARTIAL | Three static banners direct readers, but [checker roots](../../scripts/evidence_pack_gate/gate.py#L191) do not enforce them or full six-source coverage. | AUD-037-004, AUD-037-008 |
| EDGE-005 Future AI component ships [source](./spec.md#L107) | MISSING | [Discovery rule](../../.github/instructions/governance-discovery.instructions.md#L215) addresses a sixth artefact, not a new AI component; no shipping-inventory comparison in gate. | AUD-037-011 |
| EDGE-006 Manual cap exceeded [source](./spec.md#L108) | PARTIAL | [Cap helper](../../scripts/evidence_pack_gate/gate.py#L65) rejects simple unsigned excess, but publisher bypass, signature semantics, count parity and boundary cases remain. | AUD-037-003, AUD-037-005, AUD-037-006 |
| EDGE-007 Append-only conflict [source](./spec.md#L109) | MISSING | [Generator writes](../../scripts/evidence_pack_gate/generate_artefacts.py#L1095) overwrite unchanged IDs; no prior-row comparison or supported revision field. | AUD-037-003, AUD-037-006 |
| EDGE-008 Degraded telemetry [source](./spec.md#L110) | PARTIAL | [Banner](../../apps/web/src/app/governance/executive/_components/StaleTelemetryBanner.tsx#L14) exists, but request failures/null health and aged observations do not reliably trigger it. | AUD-037-007 |

## Reviewer Checklist Evidence

All original CHK001-CHK084 definition lines are checked `[X]`; the following assessment does
not change them. Static artifact structure is distinguished from pipeline, archive, approval,
measurement, and human-review claims. The [closure note](./checklists/capstone-evidence-pack.checklist.md#L240)
does not substitute for the per-item evidence below. Task descriptions also cite nonexistent
CHK090/CHK091/CHK092 and sometimes use real CHK IDs for unrelated obligations; the matrix uses
the checklist's actual definitions, not those mistaken task references.

| Checklist ID | Original state | Status | Concrete assessment | Follow-up |
| --- | --- | --- | --- | --- |
| CHK001 | [X] | IMPLEMENTED | [Risk index](../../docs/risk-register/index.md#L1) exists and is linked from hub. | none |
| CHK002 | [X] | IMPLEMENTED | [All risk rows](../../docs/risk-register/risk-register.json#L21) cover six categories. | none |
| CHK003 | [X] | UNVERIFIED | No latest CI run inspected; [schema tests](../../tests/contract/spec_037/test_risk_register_schema.py#L36) use fixtures, not every published row. | AUD-037-005, AUD-037-013 |
| CHK004 | [X] | PARTIAL | JSON fields/products exist; [legacy file](../../docs/risk-register/RISK-AOAI-001.md#L3) lacks numeric fields and spec/ADR citation coverage incomplete. | AUD-037-004, AUD-037-009 |
| CHK005 | [X] | PARTIAL | [Legacy file](../../docs/risk-register/RISK-AOAI-001.md#L1) preserved, not new-schema-validated; historical non-rewrite unverified. | AUD-037-009 |
| CHK006 | [X] | PARTIAL | [Index](../../docs/risk-register/index.md#L12) sorted; frozen date means 19 overdue rows unflagged and no counter. | AUD-037-009 |
| CHK007 | [X] | IMPLEMENTED | [RISK-NEW-003](../../docs/risk-register/RISK-NEW-003.md#L20) references carve-out authority. | none |
| CHK008 | [X] | PARTIAL | Operational/warnings/evacuation risks present, but no explicit Community Recovery/AIDR-domain coverage mapping in complete [risk population](../../docs/risk-register/risk-register.json#L21). | AUD-037-009 |
| CHK009 | [X] | PARTIAL | Two structured targets broken; [checker](../../scripts/evidence_pack_gate/gate.py#L100) ignores them. | AUD-037-004 |
| CHK010 | [X] | UNVERIFIED | Top-ten names/owners readable in [index](../../docs/risk-register/index.md#L12); no <=5-minute reviewer measurement. | AUD-037-016 |
| CHK011 | [X] | PARTIAL | [Generator](../../scripts/evidence_pack_gate/generate_artefacts.py#L1095) permits in-place overwrite, no revision enforcement; actual historical edit unverified. | AUD-037-006 |
| CHK012 | [X] | IMPLEMENTED | [Risk metadata](../../docs/risk-register/risk-register.json#L7) exposes correct 21/21 and ratio 1.0. | none |
| CHK013 | [X] | PARTIAL | [Sign-off object](../../docs/risk-register/risk-register.json#L14) complete syntactically; generated author label does not prove named-auditor approval. | AUD-037-006 |
| CHK014 | [X] | PARTIAL | [Risk-manager authority](../../.github/agents/operational/risk-manager.agent.md#L59) requires dynamic matrix/archive; pack is static and unwired. | AUD-037-003, AUD-037-009 |
| CHK015 | [X] | PARTIAL | [Risk sidecar](../../docs/risk-register/risk-register.json#L36) has zero citation sections and does not cover the checklist's full cited-spec set. | AUD-037-004, AUD-037-009 |
| CHK016 | [X] | IMPLEMENTED | [Roadmap](../../docs/governance-hub/adoption-roadmap/roadmap.md#L1) exists and hub links it. | none |
| CHK017 | [X] | CONFLICT | [Wave sequence](../../docs/governance-hub/adoption-roadmap/roadmap.md#L10) omits utilities/transport and moves Commonwealth forward. | AUD-037-010 |
| CHK018 | [X] | IMPLEMENTED | [First three waves](../../docs/governance-hub/adoption-roadmap/roadmap.json#L21) cover nine lanes with leads and gates. | none |
| CHK019 | [X] | PARTIAL | Fields exist in [wave JSON](../../docs/governance-hub/adoption-roadmap/roadmap.json#L21); generic bodies and incomplete rollback/readiness semantics remain. | AUD-037-010 |
| CHK020 | [X] | IMPLEMENTED | Every cadence cites 007/024/026; [first-wave citations](../../docs/governance-hub/adoption-roadmap/roadmap.json#L38), all five inspected. | none |
| CHK021 | [X] | PARTIAL | [Final-wave rollback](../../docs/governance-hub/adoption-roadmap/roadmap.md#L119) omits manual/no-data-loss statement; other waves use inheritance. | AUD-037-010 |
| CHK022 | [X] | MISSING | No readiness-first deviation handling in full [roadmap](../../docs/governance-hub/adoption-roadmap/roadmap.md#L10) or tests. | AUD-037-010 |
| CHK023 | [X] | MISSING | Full [wave citation sets](../../docs/governance-hub/adoption-roadmap/roadmap.json#L38) contain no per-wave AIDR M&E/Outcomes Indicators link. | AUD-037-010 |
| CHK024 | [X] | MISSING | No named lessons-to-next-readiness-gate loop in [roadmap](../../docs/governance-hub/adoption-roadmap/roadmap.md#L10). | AUD-037-010 |
| CHK025 | [X] | UNVERIFIED | Current CI outcome unavailable; [checker](../../scripts/evidence_pack_gate/gate.py#L100) ignores JSON/path-only citations. | AUD-037-004, AUD-037-013 |
| CHK026 | [X] | PARTIAL | [Generator](../../scripts/evidence_pack_gate/generate_artefacts.py#L1106) overwrites waves; no enforced dated revision rows. | AUD-037-006 |
| CHK027 | [X] | IMPLEMENTED | [Roadmap metadata](../../docs/governance-hub/adoption-roadmap/roadmap.json#L7) exposes 5/5 and ratio 1.0. | none |
| CHK028 | [X] | PARTIAL | [Generated sign-off](../../docs/governance-hub/adoption-roadmap/roadmap.json#L14) is structurally complete; human decision unverified. | AUD-037-006 |
| CHK029 | [X] | PARTIAL | Existing spec refs are present in [JSON](../../docs/governance-hub/adoption-roadmap/roadmap.json#L38), but not section-grounded clickable citations in Markdown. | AUD-037-004 |
| CHK030 | [X] | IMPLEMENTED | [Markdown](../../docs/governance-hub/executive-kpi/surface.md#L1), JSON and [page](../../apps/web/src/app/governance/executive/page.tsx#L23) exist at canonical locations. | none |
| CHK031 | [X] | IMPLEMENTED | [Ten definitions](../../docs/governance-hub/executive-kpi/surface.json#L21) cover five leading/lagging pairs. | none |
| CHK032 | [X] | PARTIAL | Fields exist but self-referential source/incomplete consolidation/display weaken [KPI rows](../../docs/governance-hub/executive-kpi/surface.json#L62). | AUD-037-008 |
| CHK033 | [X] | MISSING | Only dashboard and SLO occur in `consolidates`, not all six required sources; [builder](../../scripts/evidence_pack_gate/generate_artefacts.py#L422) controls the set. | AUD-037-008 |
| CHK034 | [X] | PARTIAL | Three document banners exist; full six-source set and [page superseded links](../../apps/web/src/app/governance/executive/_components/KpiLadder.tsx#L29) absent. | AUD-037-004, AUD-037-008 |
| CHK035 | [X] | PARTIAL | No chart library in slice, but [page](../../apps/web/src/app/governance/executive/page.tsx#L44) does not compose the existing shell or audit primitives. | AUD-037-008 |
| CHK036 | [X] | PARTIAL | [Strip](../../apps/web/src/app/governance/executive/_components/ManualRowRatioStrip.tsx#L23) renders supplied entries; failed summary fetch produces zero entries rather than five explicit states. | AUD-037-007, AUD-037-008 |
| CHK037 | [X] | PARTIAL | [Health/page](../../apps/web/src/app/governance/executive/page.tsx#L35) do not detect stale observations or null-request failures. | AUD-037-007 |
| CHK038 | [X] | UNVERIFIED | Source parents are AU, but [sink URI strings](../../docs/governance-hub/executive-kpi/surface.json#L36) provide no deployed-region evidence. | AUD-037-015, AUD-037-016 |
| CHK039 | [X] | UNVERIFIED | No current CI outcome; [schema test](../../tests/contract/spec_037/test_executive_kpi_surface_schema.py#L37) not actual data/citation population. | AUD-037-005, AUD-037-013 |
| CHK040 | [X] | UNVERIFIED | No timed executive study; [ladder](../../apps/web/src/app/governance/executive/_components/KpiLadder.tsx#L29) lacks on-track/at-risk state. | AUD-037-008, AUD-037-016 |
| CHK041 | [X] | PARTIAL | [Metadata](../../docs/governance-hub/executive-kpi/surface.json#L7) has 10/10 and structural sign-off; actual human approval unverified. | AUD-037-006 |
| CHK042 | [X] | PARTIAL | Zero section fields in all 27 nested [KPI references](../../docs/governance-hub/executive-kpi/surface.json#L21). | AUD-037-004 |
| CHK043 | [X] | IMPLEMENTED | [RAI pair](../../docs/governance-hub/rai-register/responsible-ai-register.md#L1) exists and hub links it. | none |
| CHK044 | [X] | IMPLEMENTED | All eight explicitly named baseline components appear in [register](../../docs/governance-hub/rai-register/responsible-ai-register.md#L22). Actual shipping set needs future inventory guard. | AUD-037-011 |
| CHK045 | [X] | CONFLICT | Simulation has 15 repeated cells, not 32; [production rationale](../../docs/governance-hub/rai-register/responsible-ai-register.md#L8) is present but not complete assessment evidence. | AUD-037-005, AUD-037-011 |
| CHK046 | [X] | PARTIAL | Four framework keys/four NIST profiles populated, but [repeated compliant cells](../../docs/governance-hub/rai-register/responsible-ai-register.json#L31) lack distinct control evidence. | AUD-037-011 |
| CHK047 | [X] | PARTIAL | Eight principle keys populated; [builder](../../scripts/evidence_pack_gate/generate_artefacts.py#L547) copies one summary rather than principle-specific assessment. | AUD-037-011 |
| CHK048 | [X] | PARTIAL | Current cells nonblank; [schema](./contracts/responsible-ai-register.schema.json#L49) permits empty N/A justification and whitespace. | AUD-037-005, AUD-037-011 |
| CHK049 | [X] | PARTIAL | No evaluation rerun, but all eval refs are specs, not outputs; [RAI builder](../../scripts/evidence_pack_gate/generate_artefacts.py#L595). | AUD-037-011 |
| CHK050 | [X] | PARTIAL | [Carve-out YAML](../../infra/parameters/foundry-carveout.yaml#L14) is referenced; 2027-04-08 review dates are future at audit date, not proof approvals or deployed posture are current. | AUD-037-011, AUD-037-016 |
| CHK051 | [X] | PARTIAL | Some component summaries name PIO/IC/logistics review; [generic builder](../../scripts/evidence_pack_gate/generate_artefacts.py#L595) does not name a human approval/escalation point for every component. | AUD-037-011 |
| CHK052 | [X] | MISSING | No per-component PI&W/privacy control mapping; the same paragraph fills each privacy cell in [RAI builder](../../scripts/evidence_pack_gate/generate_artefacts.py#L547). | AUD-037-011 |
| CHK053 | [X] | PARTIAL | Deterministic literal-input render exists; [Markdown](../../docs/governance-hub/rai-register/responsible-ai-register.md#L18) is incomplete and archive retrieval absent. Byte stability across executions unverified. | AUD-037-003, AUD-037-006, AUD-037-011 |
| CHK054 | [X] | UNVERIFIED | [Rehearsal pass labels](./rehearsal-results.md#L37) are not a latest CI run or full RAI validation record. | AUD-037-013, AUD-037-016 |
| CHK055 | [X] | PARTIAL | [8/8 metadata](../../docs/governance-hub/rai-register/responsible-ai-register.json#L7) and generated sign-off are structurally complete, not a real approval. | AUD-037-006 |
| CHK056 | [X] | MISSING | [Instruction](../../.github/instructions/governance-discovery.instructions.md#L215) gates a sixth artefact, not a future AI component row. | AUD-037-011 |
| CHK057 | [X] | PARTIAL | All 272 RAI reference objects have no section; [JSON](../../docs/governance-hub/rai-register/responsible-ai-register.json#L25) gives file-only references. | AUD-037-004, AUD-037-011 |
| CHK058 | [X] | CONFLICT | [Actual log](../../docs/governance-hub/feature-value-ledger/tradeoff-log.md#L1) exists under the plan/T060 path, not the old docs/decisions path named by the checklist. No duplicate log should be created. | AUD-037-016 |
| CHK059 | [X] | PARTIAL | [Ledger](../shared/feature-value-ledger.md#L13) represents 36/37 actual spec IDs plus one nonexistent ID; hygiene tags present. | AUD-037-012 |
| CHK060 | [X] | PARTIAL | Literal magnitude/direction/gap fields present in [JSON](../shared/feature-value-ledger.json#L38), but source-grounded quantitative interpretation absent. | AUD-037-012 |
| CHK061 | [X] | PARTIAL | Two positive-gap follow-ups target a non-heading, not a verifiable open action; [builder](../../scripts/evidence_pack_gate/generate_artefacts.py#L706). | AUD-037-004, AUD-037-012 |
| CHK062 | [X] | PARTIAL | [Ledger link](../shared/feature-value-ledger.md#L3) points to trace; the full [trace](../shared/capstone-metric-trace.md#L1) contains no reciprocal link. | AUD-037-012 |
| CHK063 | [X] | IMPLEMENTED | [Self-flag](../shared/capstone-metric-trace.md#L34) exact tag and 028 FR-020 authority present. | none |
| CHK064 | [X] | IMPLEMENTED | Full [ADR log](../../docs/governance-hub/feature-value-ledger/tradeoff-log.md#L11) has all 15 existing filenames, once each. Content fidelity assessed separately. | AUD-037-012 |
| CHK065 | [X] | PARTIAL | Columns populated, but full ADR comparison shows wrong feature ownership and alternatives/rationale. [First counterexample](../../docs/aidr/decisions/ADR-036-001-real-sub-agent-invocation.md#L6). | AUD-037-012 |
| CHK066 | [X] | PARTIAL | [Log](../../docs/governance-hub/feature-value-ledger/tradeoff-log.md#L11) omits local-vs-cross-jurisdiction; other three tags exist. | AUD-037-012 |
| CHK067 | [X] | UNVERIFIED | No current CI output and [gate roots](../../scripts/evidence_pack_gate/gate.py#L191) omit paired log. | AUD-037-004, AUD-037-013 |
| CHK068 | [X] | PARTIAL | [Generator](../../scripts/evidence_pack_gate/generate_artefacts.py#L1121) overwrites current files under fixed IDs; no enforced revision chain. | AUD-037-006 |
| CHK069 | [X] | PARTIAL | [Ledger metadata](../shared/feature-value-ledger.json#L7) is 37/37, excluding 15 manual tradeoffs; signature generated. | AUD-037-005, AUD-037-006 |
| CHK070 | [X] | PARTIAL | [Builder](../../scripts/evidence_pack_gate/generate_artefacts.py#L706) renders literals, not source extraction of specs/ADRs. | AUD-037-006, AUD-037-012 |
| CHK071 | [X] | UNVERIFIED | [CI job source](../../.github/workflows/ci.yml#L406) exists; no latest pipeline/approval evidence inspected. | AUD-037-013, AUD-037-016 |
| CHK072 | [X] | IMPLEMENTED | Five tracked artefacts and paired log are [linked from hub](../../docs/governance-hub/index.md#L51). | none |
| CHK073 | [X] | UNVERIFIED | [Post-polish statement](./plan.md#L296) is self-attestation, not a supplied pre-spec baseline comparison. Audit itself leaves constitution unchanged. | AUD-037-016 |
| CHK074 | [X] | UNVERIFIED | [AU parent declarations](../../infra/main.bicep#L484) support design intent; real persistence/telemetry region not queried. | AUD-037-015, AUD-037-016 |
| CHK075 | [X] | PARTIAL | Both risk and RAI cite [registry](../../infra/parameters/foundry-carveout.yaml#L14); current approval/deployed compliance not proved. | AUD-037-011, AUD-037-016 |
| CHK076 | [X] | MISSING | No connected publication/read/revision audit path in [writer](../../apps/api/app/services/governance/evidence_pack_writer.py#L36); generator overwrites IDs. | AUD-037-002, AUD-037-003, AUD-037-006 |
| CHK077 | [X] | MISSING | No named feedback wiring in [roadmap](../../docs/governance-hub/adoption-roadmap/roadmap.md#L10); general lessons infrastructure is not tied to these wave gates. | AUD-037-010 |
| CHK078 | [X] | PARTIAL | Canonical route and simulation inclusion/manual metadata exist; [page](../../apps/web/src/app/governance/executive/page.tsx#L44) lacks required reuse and actual sign-off enforcement incomplete. | AUD-037-005, AUD-037-006, AUD-037-008, AUD-037-011 |
| CHK079 | [X] | IMPLEMENTED | Every current JSON risk/wave/KPI/RAI/feature/tradeoff row has manual owner/cadence/automation fields; [generator shape](../../scripts/evidence_pack_gate/generate_artefacts.py#L40) matches inspected outputs. Evidence status truth separate. | AUD-037-006 |
| CHK080 | [X] | PARTIAL | [SC definitions](./spec.md#L189) include measured CI/review/deployment outcomes unavailable from static artefacts; claimed independent verification not established. | AUD-037-016 |
| CHK081 | [X] | PARTIAL | No new chart import in [executive page](../../apps/web/src/app/governance/executive/page.tsx#L12); parent reuse shown, shell reuse absent and historical/deployed resource delta unverified. | AUD-037-008, AUD-037-015 |
| CHK082 | [X] | PARTIAL | [Discoverable gate entry](../../.github/instructions/governance-discovery.instructions.md#L203) exists; actual branch enforcement/future-agent condition not verified. | AUD-037-011, AUD-037-013 |
| CHK083 | [X] | IMPLEMENTED | [Ledger demo row](../shared/feature-value-ledger.md#L30) is explicitly excluded/hygiene; no new demo or FinOps deliverable in generator/page. | none |
| CHK084 | [X] | UNVERIFIED | No <=60-minute assessor completion record; [rehearsal](./rehearsal-results.md#L3) deferred. | AUD-037-016 |

## Specification Quality Checklist

QC labels below are audit-local ordering labels for the 16 unnumbered source items, not new
original requirements. Source state is preserved exactly; fifteen are checked and one is not.

| Audit label | Original state | Original item | Status | Evidence and qualification | Follow-up |
| --- | --- | --- | --- | --- | --- |
| QC-001 | [x] | No implementation details (languages, frameworks, APIs) | CONFLICT | [FR-021](./spec.md#L147) explicitly specifies route, component and shell; intentional clarification conflicts with this generic quality assertion. | AUD-037-016 |
| QC-002 | [x] | Focused on user value and business needs | IMPLEMENTED | [Five stories](./spec.md#L21) state role, value and independent test. | none |
| QC-003 | [x] | Written for non-technical stakeholders | PARTIAL | Stories are readable; [data/lifecycle requirements](./spec.md#L172) include technical metadata/CI conventions. | AUD-037-016 |
| QC-004 | [x] | All mandatory sections completed | IMPLEMENTED | [Specification](./spec.md#L19) contains scenarios, requirements, entities and measurable outcomes. | none |
| QC-005 | [ ] | No [NEEDS CLARIFICATION] markers remain | IMPLEMENTED | [Open Clarifications](./spec.md#L230) explicitly resolves the queued questions; remaining quoted marker mentions are historical, not open questions. Checklist note is stale. | AUD-037-016 |
| QC-006 | [x] | Requirements are testable and unambiguous | PARTIAL | [T059](./tasks.md#L219) nine/288 conflicts with eight named baseline components and canonical sum-shaped RAI model; publication/revision contracts also conflict. | AUD-037-005, AUD-037-011, AUD-037-016 |
| QC-007 | [x] | Success criteria are measurable | IMPLEMENTED | [SCs](./spec.md#L189) give times/counts/ratios. Measurement execution remains UNVERIFIED. | none |
| QC-008 | [x] | Success criteria are technology-agnostic (no implementation details) | CONFLICT | [SC-009](./spec.md#L197) explicitly prescribes governance shell reuse and infrastructure restrictions. | AUD-037-016 |
| QC-009 | [x] | All acceptance scenarios are defined | IMPLEMENTED | Fifteen [Given/When/Then scenarios](./spec.md#L31), all separately covered above. | none |
| QC-010 | [x] | Edge cases are identified | IMPLEMENTED | Eight [edge definitions](./spec.md#L101) are explicit, all separately covered above. | none |
| QC-011 | [x] | Scope is clearly bounded | IMPLEMENTED | [Out of scope](./spec.md#L221) and explicit child-resource clarification constrain work. | none |
| QC-012 | [x] | Dependencies and assumptions identified | IMPLEMENTED | [Assumptions/dependencies](./spec.md#L201) identify existing telemetry, framework texts, paired trace and prior specs. | none |
| QC-013 | [x] | All functional requirements have clear acceptance criteria | PARTIAL | Most map to stories/checks; RAI count/matrix, revision shape, complete ledger denominator and path references remain contradictory. [Data model](./data-model.md#L11). | AUD-037-005, AUD-037-011, AUD-037-016 |
| QC-014 | [x] | User scenarios cover primary flows | IMPLEMENTED | [US1-US5](./spec.md#L21) cover five artefacts; [quickstart](./quickstart.md#L5) covers operator flow intent, not execution. | none |
| QC-015 | [x] | Feature meets measurable outcomes defined in Success Criteria | UNVERIFIED | [Rehearsal](./rehearsal-results.md#L3) defers live outcomes and no independent timed/rubric result exists in local inputs. | AUD-037-016 |
| QC-016 | [x] | No implementation details leak into specification | CONFLICT | Explicit [FR-021 implementation choices](./spec.md#L147) were intentionally adopted; generic template assertion should be reconciled without deleting the requirement. | AUD-037-016 |

## Unnumbered Constraints

UC labels are audit-local cross-references for binding design/nonfunctional obligations; they
are not invented original NFR IDs. Constitution clause names, not the inconsistent NN-number
shorthand in plan/checklist prose, determine meaning. The actual constitution defines NN-1
human authorisation, NN-2 sovereignty, NN-3 privacy, NN-4 interoperability, NN-5 degradation;
WCAG, locale and test-first details are additional explicit spec-037 plan commitments.

| Audit label | Binding obligation and source | Status | Evidence, boundary and follow-up |
| --- | --- | --- | --- |
| UC-001 | Four read-only routes; Entra bearer, ten AIIMS roles plus administrator; [OpenAPI](./contracts/openapi.evidence-pack.yaml#L1). | PARTIAL | Four GETs exist, protected prefixes and bearer forwarding absent. AUD-037-002. No public mutation route proposed. |
| UC-002 | RFC 7807 errors and provenance/tenant-scoped read audit; [OpenAPI](./contracts/openapi.evidence-pack.yaml#L156), [technical synthesis](./synthesis/step4-tech.md#L12). | PARTIAL | Only historical 404 explicitly uses Problem Details; GET audits absent. AUD-037-002, AUD-037-007. |
| UC-003 | No PII in audit payloads; publisher is Entra OID, not display name; [data model](./data-model.md#L17). | PARTIAL | Writer takes arbitrary caller string; positive test uses a known non-PII OID, not rejecting input; generic generated published_by is not OID. AUD-037-002, AUD-037-003, AUD-037-006. |
| UC-004 | AU persistence, bounded model-host carve-out only; [constitution](../../.specify/memory/constitution.md#L246), [plan](./plan.md#L61). | UNVERIFIED | Parent source uses AU location and current registry lists AU models, but no cloud region/approval query performed. No model or data-store exception is inferred. AUD-037-015, AUD-037-016. |
| UC-005 | Schema/link/ratio/sign-off checks in fail-fast order; local dry-run skips metric emission; [RES-04](./research.md#L96). | PARTIAL | Gate does schema/ratio/cap for all discovered files then links; `dry_run` unused and no metrics. AUD-037-001, AUD-037-004, AUD-037-014. |
| UC-006 | JSON Schema draft 2020-12 canonical/runtime parity, Pydantic and TS contract coherence; [RES-01](./research.md#L11). | PARTIAL | Six byte-identical mirrors now, no equality guard; generic envelope and manually partial TS. AUD-037-005, AUD-037-013. |
| UC-007 | Draft -> published -> immutable; no edited/unpublish state, new `revises` record; [data model](./data-model.md#L28). | CONFLICT | Draft-without-ID cannot satisfy publication-required schema, no revision field allowed, generator overwrites same IDs. AUD-037-003, AUD-037-005, AUD-037-006. |
| UC-008 | UUID v4, globally unique publication IDs, server-issued nonfuture time; [envelope rules](./data-model.md#L17). | CONFLICT | Generator creates fixed uuid5 with frozen time; no prior-ID or future-time gate. Writer creates fresh uuid4 but is disconnected. AUD-037-003, AUD-037-005, AUD-037-006. |
| UC-009 | Counts/ratio recomputed once at publish; UI consumes same metadata; [RES-05](./research.md#L130). | PARTIAL | Helper computes primary rows and UI reads them, but counter equality and tradeoff denominator unresolved; publication not wired. AUD-037-005. |
| UC-010 | Sign-off complete above 0.5, absent at/below 0.5; validated/pending status and valid dates; [metadata rules](./data-model.md#L38). | CONFLICT | JSON Schema allows equality-boundary sign-off; Pydantic permits all unnecessary sign-offs and configurable threshold. AUD-037-005. |
| UC-011 | Existing PersonaWorkspace/audit-row composition; no new UI primitives, chart libraries or design tokens; [PD-037-02](../../docs/aidr/decisions/adr-037-02-executive-shell-reuse.md#L11). | PARTIAL | No chart dependency found, but bespoke page/ladder bypass specified primitives. AUD-037-008. |
| UC-012 | WCAG 2.2 AA, keyboard, meaningful live updates, 400% zoom, forced colours, RTL/browser support; [technical synthesis](./synthesis/step4-tech.md#L30), [plan](./plan.md#L47). | UNVERIFIED | ARIA/helper exist; suite discovery and assertions incomplete, no browser or assistive-technology run. AUD-037-008, AUD-037-013, AUD-037-016. |
| UC-013 | Inherit existing multilingual baseline, add no language assets; [plan constraints](./plan.md#L61). | PARTIAL | No new language assets, but executive text bypasses existing locale-aware composition. AUD-037-008. |
| UC-014 | Page p95 first meaningful content <=1.5s; [performance goals](./plan.md#L54). | UNVERIFIED | No measurement artifact in local review inputs; source's concurrent fetches do not prove latency. AUD-037-014, AUD-037-016. |
| UC-015 | Publication median <=60s, p95 <=180s, alert p95 >300s; [performance goals](./plan.md#L54). | UNVERIFIED | Duration is logged, pipeline unwired and measurements absent. AUD-037-003, AUD-037-014, AUD-037-016. |
| UC-016 | Gate wall-clock <=3 minutes on Ubuntu; [performance goals](./plan.md#L54). | UNVERIFIED | Job timeout five minutes is not measured duration or a <=3-minute enforcement gate. AUD-037-014, AUD-037-016. |
| UC-017 | Read API p95 <=200ms cache hit, cold fallback <=1.5s; [performance goals](./plan.md#L54). | UNVERIFIED | Reads are filesystem only; no connected cache or measured baseline. AUD-037-003, AUD-037-014, AUD-037-016. |
| UC-018 | Alertable ratio/duration/gate failure rate on existing OTel; [RES-04/05](./research.md#L96). | PARTIAL | Plan calls them two metrics while tasks/catalogue require three; only ratio gauge path exists, no actual connected publication/gate metrics. AUD-037-014. |
| UC-019 | Existing Cosmos cache, Blob per-publish immutable snapshot, audit writer; partition `/artefact_id`; [plan storage](./plan.md#L25). | PARTIAL | IaC children exist, adapters and production entrypoint absent. Actual archive bytes/lock unverified. AUD-037-003, AUD-037-015. |
| UC-020 | All PRs pass lint/unit/integration, and every code task follows a failing test first; [tasks TDD gate](./tasks.md#L44), [constitution](../../.specify/memory/constitution.md#L290). | UNVERIFIED | Static tests are present with discovery/skip weaknesses; chronology and executed pass histories not established. AUD-037-013, AUD-037-016. |
| UC-021 | IaC what-if/PSRule review, AVM-first, no new top-level resources; [plan constraints](./plan.md#L61). | PARTIAL | Raw spec-037 declarations conflict with AVM promise; resource-group scope versus subscription command, live review deferred. AUD-037-015, AUD-037-016. |
| UC-022 | Post-exercise lessons capture feeds adoption/readiness revisions; [checklist](./checklists/capstone-evidence-pack.checklist.md#L54), [constitution](../../.specify/memory/constitution.md#L290). | MISSING | No named connection from lessons to any roadmap gate in complete roadmap/generator. Existing lessons subsystem is not proof of this connection. AUD-037-010. |
| UC-023 | Risk NERAG matrix, accepted/mitigated/transferred/avoided treatments, audience/authority/uncertainty; [risk manager](../../.github/agents/operational/risk-manager.agent.md#L59). | PARTIAL | Numeric scores/free-text treatments exist, no complete dynamic authority/matrix/uncertainty view or archive. Separate [operational aggregation](../../apps/api/app/services/dashboard_aggregation_service.py#L560) does not consume this portfolio JSON. AUD-037-009. |
| UC-024 | Reviewer time <=10 minutes/artefact, <=60 minutes total; real Step 0 re-review and operator approvals; [checklist](./checklists/capstone-evidence-pack.checklist.md#L1). | UNVERIFIED | Synthetic cohort text and generated sign-off do not establish independent reviewer decisions/time. AUD-037-016. |
| UC-025 | Preserve metric/HYP authority and cohort deferrals; no outcome attribution to 037; [trace](../shared/capstone-metric-trace.md#L1), [028 FR-020](../028-capstone-alignment/spec.md#L165). | PARTIAL | Self-flag correct, but feature list tags 005/006/014/018/019/020/021/023 hygiene although 028 names them critical-path. Magnitudes lack derived evidence. AUD-037-012. |
| UC-026 | Scope: five evidence artefacts only; exclude demo, FinOps, evaluation reruns, new engines/resources, constitution edits; [out of scope](./spec.md#L221). | IMPLEMENTED | Reviewed generator/page do not add these excluded deliverables. Child-resource permission is the explicit C1 amendment, not an inferred general exemption. Other implementation gaps do not authorise scope expansion. |

No original spec-037 HYP/PER/ASM-style IDs are defined in the 19 local inputs. The synthesis
contains persona-derived hypotheses/needs, not tested outcomes. The full metric-trace population
was read: five AU-v1 attribution rows and fifteen PH/JP/BD Deferred rows, including their HYP
references and MoU/licensing/baseline preconditions. None was promoted to measured evidence in
this audit. The 028 critical-path/hygiene conflict above is a documented source disagreement,
not grounds to rewrite older specifications or silently change ledger tags.

## Persona-Derived Duties

The three synthesis files are synthetic canvasses, not 85 independent human approvals. The
operational and technical rows below cover every named persona; sector rows cover every group
and named cluster contained in its 58-persona synthesis, without inventing individual votes.
These duties remain bounded to evidence-pack content, not new operational decisioning features.

### Operational Personas

Source: [complete operational synthesis](./synthesis/step1-ops.md#L1).

| Persona | Duty reflected in this audit | Status and follow-up |
| --- | --- | --- |
| Incident Commander | Decision-grade risks, authority/override, unified command, live KPI context. | PARTIAL: risk prose present, decision/evidence freshness and RAI authority mapping incomplete; AUD-037-007, AUD-037-009, AUD-037-011. |
| Operations Officer | Tactical deployment/scarcity/safety, staged rollout, deployment-speed KPI. | PARTIAL: risks/KPI targets exist, no actual observations or complete wave readiness; AUD-037-008, AUD-037-010. |
| Planning Officer | Provenance/confidence, evolving threats, leading/lagging measures and uncertainty. | PARTIAL: literal fields do not substantiate uncertainty or actual measurements; AUD-037-006, AUD-037-008, AUD-037-011. |
| Logistics Officer | Supply-chain/cold-chain/accountability, procurement readiness, resource-fill metrics. | PARTIAL: scarcity risks and fill-rate target exist, complete sector rollout/telemetry not demonstrated; AUD-037-008, AUD-037-010. |
| Public Information Officer | Human-approved multilingual/accessibility alerts and privacy-aware RAI evidence. | PARTIAL: generic PIO paragraph exists, distinct controls/output evidence and inherited locale/a11y unverified; AUD-037-008, AUD-037-011. |
| Executive Leader | Systemic risk, policy/resource authority, cross-jurisdiction adoption and single outcome view. | PARTIAL: targets/owners exist, no usable current outcome/status ladder or completed timed review; AUD-037-008, AUD-037-010, AUD-037-016. |
| Observer-Auditor | Append-only provenance, approval evidence, post-incident review and justified pilot exit. | PARTIAL: generated labels and unconnected history/audit cannot substantiate this; AUD-037-002, AUD-037-003, AUD-037-006. |
| Risk Manager | Dynamic schema register, NERAG matrix, treatments/ownership/residuals and archive. | PARTIAL: 21 numeric rows exist; legacy/matrix/current-review/archive gaps; AUD-037-009. |
| Resilience Planner | Phased preparedness, existing scenario rehearsals, lessons-to-readiness revisions. | PARTIAL: five waves/citations exist; cohort and feedback-loop gaps; AUD-037-010. |
| Field Coordinator | Degraded connectivity, conservative life-safety defaults and later auditability. | PARTIAL: some risk/rollback prose exists, incomplete per-pilot no-loss and stale-data handling; AUD-037-007, AUD-037-010. |

### Sector Groups

Source: [complete sector synthesis](./synthesis/step1-sectors.md#L1).

| Source group or cluster | Duty assessed | Status and follow-up |
| --- | --- | --- |
| NSW: FRNSW, MRNSW, NSW Ambulance, NSW RFS, NSWPF, SES NSW | Fire/flood/marine/medical/enforcement/volunteer interface risks and lead-agency handoffs. | PARTIAL: initial lead map exists, broad risk coverage does not map each required interface; AUD-037-009, AUD-037-010. |
| VIC: AV, CFA, FRV, SES, VICPOL | Ambulance/fire/SES/police jurisdiction and handoff clarity. | PARTIAL: WAVE-01 names a lead cluster, readiness/agency evidence still manual; AUD-037-010. |
| QLD: QAS, QFD, QPS, SES QLD | Flood/cyclone/fire/search/rescue/ambulance domains. | PARTIAL: WAVE-01 covers jurisdiction, domain/readiness grounding incomplete; AUD-037-009, AUD-037-010. |
| Commonwealth: NEMA, BoM, GA, AFP, ADF, ABF, ASA, RFDS, ARC, SJA, Surf Life Saving | National coordination, COMDISPLAN/DRFA/weather/geospatial/defence and recovery. | PARTIAL: NEMA/BoM/GA/ADF/ABF names exist, order wrong and explicit federal coordination appendix R4 deferred; AUD-037-010. |
| Health | Triage/hospital surge/public health and supply-chain readiness. | PARTIAL: KPI targets exist, no substantiated per-control/outcome evidence; AUD-037-008, AUD-037-011. |
| Local government | Recovery, evacuation centres, vulnerable persons, training/MEMP. | PARTIAL: generic WAVE-04 plus R3 deferral, not complete named/validated workflow; AUD-037-010. |
| Transport | Routing, evacuation and restoration; cohort after utilities. | MISSING: no transport wave in current full roadmap; AUD-037-010. |
| Utility | Critical-service continuity/restoration and cohort before transport. | MISSING: no utilities wave in current full roadmap; AUD-037-010. |
| Volunteer | Credentialing, welfare/training, command authority and conservative fallbacks. | PARTIAL: WAVE-05 exists, named bodies/safe no-loss rollback incomplete; AUD-037-010. |
| Community NGOs | Accessible multilingual community communications and recovery. | PARTIAL: generic pack/brochure names and R3 deferral, not evidence-bearing readiness; AUD-037-010, AUD-037-011. |
| State government | Lead-agency adoption, mutual aid, authority before retiring legacy channels. | PARTIAL: first three waves carry leads/gates but not readiness deviation or signed authority evidence; AUD-037-010, AUD-037-016. |
| Territory government | ACT/NT coverage and jurisdictional authority continuity. | PARTIAL: WAVE-03 names leads, later generic peak-body assertions remain unvalidated; AUD-037-010. |

### Technical Personas

Source: [complete technical synthesis](./synthesis/step4-tech.md#L1).

| Persona | Duty assessed | Status and follow-up |
| --- | --- | --- |
| AI/ML Engineer | Validated structured output, confidence/provenance/timestamps, source-backed RAI. | PARTIAL: DTOs exist but detached and posture generic; AUD-037-005, AUD-037-011. |
| Data Engineer | Schema evolution, immutable archive, relevant partitioning, source extraction. | PARTIAL: mirrors/partition exist, parity enforcement and archive adapter absent; AUD-037-003, AUD-037-005, AUD-037-006. |
| Solution Architect | CQRS-lite, explicit evolution, append-only read models, no silent state change. | PARTIAL: read routes exist, filesystem/stub and overwrite paths violate documented lifecycle; AUD-037-003, AUD-037-006, AUD-037-007. |
| API Architect | Contract-first versions, RFC 7807, provenance, appropriate collection handling. | PARTIAL: OpenAPI written, no schema/auth error parity; pagination is not added gratuitously to fixed-five summaries; AUD-037-002, AUD-037-005, AUD-037-007. |
| Software Developer | Typed handlers, Next.js composition, read-only access and tenant identity. | PARTIAL: handlers/components exist; auth, typed envelope and reuse incomplete; AUD-037-002, AUD-037-005, AUD-037-008. |
| Security Engineer | JWT/RBAC/tenant enforcement, AU and privacy/minimisation. | PARTIAL: protected-route gap and synthetic sign-off; deployed edge enforcement UNVERIFIED; AUD-037-002, AUD-037-006, AUD-037-015. |
| Infrastructure/DevOps | Reuse/AVM, validate-before-deploy, CI enforcement and identities. | PARTIAL: job/children exist, AVM/protection/test-discovery gaps and live review deferred; AUD-037-013, AUD-037-015. |
| QA/Test Engineer | Meaningful contracts/integration/Playwright/axe and no test skips masking absence. | PARTIAL: fixtures/assertions do not enforce promised behaviours or discovery; AUD-037-013. |
| Principal Engineer | Lean scope, meaningful coverage, debt tracking and honest evidence. | PARTIAL: lean footprint supported; disconnected code and false confidence remain; all follow-ups keep existing homes. |
| UX Designer | Scannable/severity-distinct, degraded-mode aware, predictable navigation. | PARTIAL: raw ladder lacks state and entry navigation; R8 polish separately deferred; AUD-037-007, AUD-037-008. |
| Accessibility Tester | WCAG AA, keyboard/live updates, RTL, 400%/forced-colour checks. | UNVERIFIED: helper exists, undiscovered/weak tests and no manual a11y evidence; AUD-037-008, AUD-037-013, AUD-037-016. |
| Compliance Auditor | Privacy/records/framework mapping, genuine sign-off and archive evidence. | PARTIAL: generated posture/approval is not proof; AUD-037-006, AUD-037-011, AUD-037-016. |
| Azure Principal Architect | AU availability/WAF tradeoffs and child-resource reuse. | UNVERIFIED: AU source intent present; no current resource/policy/what-if data; AUD-037-015, AUD-037-016. |
| Chaos Engineer | Bounded failure, partial publication/retrieval, conservative recovery. | PARTIAL: no failure-injection assertions around durable publisher; R9 bypass remains deferred, not permission to weaken gate; AUD-037-003, AUD-037-007. |
| SRE Engineer | Observable SLOs, failure-rate denominator and actionable alerts. | PARTIAL: thresholds documented, real metrics/emission/measurement incomplete; AUD-037-014. |
| Docker & Container Engineer | Thin existing runtime with required packaged artifacts. | PARTIAL: Docker copies sidecars, not a connected cache/archive publisher; packaging source reviewed, image/build outcome UNVERIFIED; AUD-037-003. |
| Product Owner/BA | Measurable value, BDD traceability and meaningful reviewer outcomes. | PARTIAL: scenarios exist; CSVs/quantitative ledger and review evidence inadequate; AUD-037-012, AUD-037-013, AUD-037-016. |

## Design And Amendment Dispositions

### Plan And Research

| Input ID | Status | Assessment and owning follow-up |
| --- | --- | --- |
| PD-037-01 | PARTIAL | [Text-first ADR](../../docs/aidr/decisions/adr-037-01-text-first-evidence-pack.md#L16) and pairs exist, canonical parity is currently true but not guarded and DTOs unused; AUD-037-005. |
| PD-037-02 | PARTIAL | [Shell decision](../../docs/aidr/decisions/adr-037-02-executive-shell-reuse.md#L11) explicit, implementation does not compose it; AUD-037-008. |
| PD-037-03 | PARTIAL | [Cap decision](../../docs/aidr/decisions/adr-037-03-manual-evidence-cap.md#L16) explicit, generated approvals/policy divergence; AUD-037-005, AUD-037-006. |
| PD-037-04 | PARTIAL | [Three-layer decision](../../docs/aidr/decisions/adr-037-04-three-layer-append-only.md#L11) explicit, writer/history disconnected; AUD-037-003, AUD-037-006, AUD-037-015. |
| PD-037-05 | PARTIAL | [Simulation rationale](../../docs/governance-hub/rai-register/responsible-ai-register.md#L8) preserved, full evidence matrix not established; AUD-037-011. |
| PD-037-06 | PARTIAL | Two containers reuse account parents, plus policy child; raw AVM conflict and two-versus-three metric wording; live graph UNVERIFIED; AUD-037-014, AUD-037-015. |
| RES-01 | PARTIAL | Six schemas and DTOs authored, no typed envelope/gate parity; [schema README](../../packages/schemas/spec_037/README.md#L14) overstates runtime usage/equality checks; AUD-037-005. |
| RES-02 | IMPLEMENTED | Canonical flat locations implemented for all five artefacts and hub entries. Old tradeoff-path discrepancy is documented, not evidence of missing relocated log. |
| RES-03 | PARTIAL | Server Component/no-chart intent supported; composition, accessibility and navigation incomplete; AUD-037-008, AUD-037-013. |
| RES-04 | PARTIAL | CI module/job exist, fail-fast order, mandatory population, citation coverage and merge enforcement incomplete; AUD-037-001, AUD-037-004, AUD-037-013. |
| RES-05 | PARTIAL | Ratio helper/metadata/gauge shape exist; publisher/emission and count agreement incomplete; AUD-037-005, AUD-037-014. |

### Clarifications And Supersession

| Source clarification | Status | Explicit authority and effect |
| --- | --- | --- |
| Q1 Manual provenance | PARTIAL | [Clarifications](./spec.md#L14) permit genuine manual stubs, not fabricated validation/approval. Fields present; AUD-037-005, AUD-037-006. |
| Q2 Simulation production RAI | PARTIAL | [Clarification](./spec.md#L15) forbids watermark exemptions; baseline simulation row exists but posture evidence incomplete; AUD-037-011. |
| Q3 Executive hosting | PARTIAL | [Clarification](./spec.md#L16) fixes sibling route and existing shell reuse; route exists, reuse/navigation absent; AUD-037-008. |
| Q4 Per-artefact cap | PARTIAL | [Clarification](./spec.md#L17) selects <=0.5 or named auditor; structural blocks do not prove a person signed; AUD-037-005, AUD-037-006. |
| I1 KPI filename | SUPERSEDED | [Explicit filename resolution](./spec.md#L234) makes surface Markdown/JSON canonical; missing older kpi-surface filenames are not implementation gaps. |
| I2 Roadmap filename | SUPERSEDED | [Explicit resolution](./spec.md#L235) makes roadmap Markdown/JSON canonical. |
| I3 RAI filename | SUPERSEDED | [Explicit resolution](./spec.md#L236) fixes responsible-ai-register pair and PD-037-05 wording. |
| I4 Risk sidecar/index distinction | SUPERSEDED | [Explicit resolution](./spec.md#L237) distinguishes risk-register JSON from human index; T056's residual index.json wording is not a missing artifact. |
| I5 Banner scope | SUPERSEDED | [Explicit resolution](./spec.md#L238) permits section-scoped banners; no demand to delete operational SLO/dashboard/catalogue content. |
| C1 Top-level resource boundary | SUPERSEDED | [Explicit resolution](./spec.md#L239) permits two child containers and existing-pipeline metrics despite older absolute no-infra wording. It does not waive AVM, residency or WORM checks. |

The log-path discrepancy is **CONFLICT**, not proven supersession: US5/checklist name an older
docs/decisions location, while [RES-02](./research.md#L29), plan, T060 and the actual hub choose
the governance-hub location. Keep the working implementation and obtain an explicit path-contract
resolution; do not duplicate the log. Likewise, the later
[spec 040 relationship](../040-success-criteria/spec.md#L29) says it contributes outputs to this
pack, not that it replaces or retires spec 037. Its alternate page/route cannot silently satisfy
this spec's missing publication, shell, or evidence duties.

### Step 8 Review And Deferred Work

All nine records below come from the [embedded Step 8 log](./spec.md#L243). Its absent session-only
triage file was not fetched or reconstructed. The stated 85-persona population yields only 84
votes from 65 + 17 + 2; endorsements are synthetic, not independent human approval evidence.

| Record | Recorded disposition | Static assessment | Follow-up |
| --- | --- | --- | --- |
| R1 RFC 7807 404 | APPLIED | IMPLEMENTED for historical 404 via `_problem_response`; broader validation/auth/unavailable errors not established. Reviewer decision itself UNVERIFIED. | AUD-037-002, AUD-037-007 |
| R2 CI metric echo | DEFERRED to Step 9 | PARTIAL: deferral is explicit, echo remains; gate also lacks claimed application metric connection. | AUD-037-014, AUD-037-016 |
| R3 LGA/MEMP/evac-centre/vulnerable-person detail | DEFERRED v1.1 | PARTIAL: generic LGA wording remains; maintain this explicit narrower deferral, not a waiver of mandatory cohort/safety rules. | AUD-037-010, AUD-037-016 |
| R4 Federal responder appendix | DEFERRED v1.1 | PARTIAL: some NEMA/COMDISPLAN text exists, no explicit appendix; do not silently remove the recorded follow-up. | AUD-037-010, AUD-037-016 |
| R5 Self-referential KPI | DEFERRED v1.1 | PARTIAL: self-reference remains in KPI-CAP-002; impacts source-of-truth obligation, not established by a wording-polish label. | AUD-037-008 |
| R6 Missing Playwright | REJECTED | PARTIAL: file exists, so literal absence was false; current runner does not discover it. File presence does not prove E2E coverage. | AUD-037-013 |
| R7 Missing axe/zoom/high-contrast | REJECTED | PARTIAL: helper and test labels exist; no discovery and inadequate reflow/focus assertions, no executed evidence. | AUD-037-008, AUD-037-013 |
| R8 Severity grouping | DEFERRED v1.1 | PARTIAL: explicit polish deferral retained; mandatory KPI status/threshold presentation still requires work independently. | AUD-037-008, AUD-037-016 |
| R9 Kill-switch/hotfix bypass | DEFERRED v1.1 | UNVERIFIED future decision; fail-fast policy is explicitly intentional for v1. Do not introduce a bypass as an audit fix. | AUD-037-016 |

The amendment expressly introduces **no FR-039 or SC-012**. The audit therefore retains exactly
38 FRs and 11 SCs, with no fabricated suffix requirements. Canonical filename and child-resource
changes above are the only scoped supersessions relied on.

## Review Evidence And Limits

| Review/execution duty | Available static record | Assessment |
| --- | --- | --- |
| Test-first red gate, then green contract suites | [Task checkpoints](./tasks.md#L44) and [rehearsal claims](./rehearsal-results.md#L37). | UNVERIFIED historical execution/chronology. Current source has 20/5/1 definitions; reported history says 20/4/2. No logs proving exact revision/environment/skip counts are linked. |
| Full operator workflows 1-4 | [Canonical deferral](./rehearsal-results.md#L3). | UNVERIFIED; expressly deferred, not completed. Script invokes only local gate/tests, not add/publish/override/read workflow. |
| Branch-protected publication and CI success | [Job](../../.github/workflows/ci.yml#L406), [descriptive protection file](../../.github/branch-protection.json#L1). | PARTIAL source, UNVERIFIED actual branch settings/run outcome. No cloud/GitHub query made. |
| Schema/link universal pass | Generated metadata says passed; [gate source](../../scripts/evidence_pack_gate/gate.py#L200) is incomplete. | PARTIAL; archive or complete population cannot be inferred from this label. Two JSON citations are statically broken. |
| Bicep/PSRule/what-if and no-new-resource claim | [Post-polish plan](./plan.md#L296), [checklist closure](./checklists/capstone-evidence-pack.checklist.md#L240). | UNVERIFIED execution, with source conflicts on AVM/scope/retention. Existing template/compiled artifact is not a live deployment diff. |
| Constitution unchanged since pre-spec baseline | [Post-polish statement](./plan.md#L296) uses HEAD~9, task names HEAD~. | UNVERIFIED historical comparison; no explicit pre-spec SHA bound to evidence. This audit did not change it. |
| Genuine auditor overrides for five manual-heavy artifacts | Same generic author sign-off is generated for all five. | UNVERIFIED reviewer identity/decision; no source-based inference of a human approval or forgery allegation. |
| RAI framework/ethics review | Synthetic persona text and repeated compliant rows. | PARTIAL authored structure, UNVERIFIED compliance decisions; no new model evaluation was run. |
| Risk <=5m, executive <=2m, whole review <=60m | Checkboxes and deferred rehearsal only. | UNVERIFIED measurements; no invented timings or rubric score. |
| Step 0 rubric improvement | No preserved re-score in the 19 local inputs; Step 8 is a different synthetic review. | UNVERIFIED; requires later assessor evidence. |
| Persona/cross-cohort approval | Three synthesis inputs and aggregate Step 8 narrative. | UNVERIFIED independent approval; nine dispositions assessed individually, vote-count inconsistency retained. |
| WCAG, keyboard, zoom, forced-colour and browser behaviour | Helper/test sources exist. | UNVERIFIED outcomes; no browser execution and runner/assertion gaps documented. |
| SLOs and observability | Catalogue thresholds, ratio emitter and CI echo. | UNVERIFIED observed SLOs, known source emission gaps; no telemetry queries or measurements. |

### Negative-Search Boundaries

| Claimed absence/gap | Bounded source inspected and replacement check |
| --- | --- |
| Production publisher/adapters/read audit | Full writer/route/CLI/CI source; references to `publish_artefact`, `append_audit_for_read`, publisher/writer names and storage IDs in apps/packages/scripts/tests/.github/infra. Only test invocation found; Docker explicitly records deferral. |
| Missing executive navigation/composition | Executive page/components/client/types, governance directory/layout/navigation, workspace primitive and web-source reference search. Root/global shell is not the explicitly required PersonaWorkspace/audit-row composition. |
| Missing risk dynamic/archive integration | Full risk population/generator/gate and separate operational risk view/aggregation read. The latter uses another data source; it is not this portfolio JSON. |
| Missing cohort/M&E/lessons requirements | Every roadmap row and full Markdown, generator wave builder, schema/model and roadmap tests. No replacement wave file found in the artifact folder. |
| Missing RAI output evidence/new-agent gate | All RAI fields/cells/references, full generator, RAI schema/model/tests, discovery instruction and CI/gate. Specifications are cited, not evaluation output records. |
| Wrong/missing ledger identities and ADR fidelity | Full tracked HEAD spec-path population including nested paths; all ledger rows, all 15 ADRs including amendments, generator literal lists and metric trace. Nonexistent 004 alias is not presumed superseded. |
| Broken citations | Every nested ref plus Markdown artifacts inspected; filename replacement search finds partitioning document and Phi ADR elsewhere. Missing historical paths are not missing underlying capabilities. |
| Missing test/traceability enforcement | Root/API/spec conftests, exact pytest workflow paths, full runner configs, both CSVs and scoped CI/scripts/tools reference search. Existing fixtures permit skipped imports/missing mirrors; no spec-037 CSV guard found. |
| No explicit later replacement | [Spec 040](../040-success-criteria/spec.md#L29) explicitly contributes to 037; no retirement declaration. Other implementation-review reports were not read. |

Applicable local review instructions and detailed review checklist, Bicep baseline/policy
instructions for the inspected child resources, governance-discovery source, API-patterns
security guidance, and the Python fact-grounded skill were read. This remained a static audit:
no environment configuration, imports, model calls, cloud discovery, framework evaluation,
dependency installation, build, product test, or verification script was executed. Live-policy,
deployed-resource, approval and model-quality questions are deliberately left UNVERIFIED.

## Future Validation Handoff

Commands in remediation tasks are **future instructions**, not executed checks. Establish an
authorised disposable checkout/test-data workspace, Python >=3.12 with the repository's selected
environment/dependencies and package paths, and the existing pnpm toolchain first. The gate module
requires `scripts` on `PYTHONPATH`; do not rely on import-skipping tests. Fix runner discovery
before interpreting zero discovered tests as success. Future platform/browser work additionally
requires explicit approval, isolated tenant/storage fixtures or approved staging resources,
and genuine human decision records. Do not rerun spec-030 evaluations to fill RAI evidence.

| Gate | Future command or procedure | Expected result and boundary |
| --- | --- | --- |
| Contract/integration behaviour | `pytest tests/contract/spec_037 apps/api/tests/contract/spec_037 tests/integration/spec_037 -q` | Meaningful positive/negative tests pass with zero missing-implementation skips; fake schemas/storage are not production evidence. |
| Real CLI contract | `python -m evidence_pack_gate --repo-root <disposable-fixture-root> --dry-run` | Complete valid pack returns 0; each missing/corrupt/unauthorised fixture returns nonzero. Do not point generator/rehearsal at production or original evidence. |
| UI unit | `pnpm --filter @ama/web exec vitest run src/app/governance/executive` after discovery repair | All intended tests discovered, actual data/failure/reflow/source-link states asserted. |
| Browser/a11y | `pnpm --filter @ama/web exec playwright test spec-037` after project repair | Isolated local services only; exact four-route/page workflows, keyboard/reflow and axe assertions, with saved results tied to revision. |
| Delivery/workflow/retention | `pytest tests/devops/test_cd_workflow.py tests/devops/test_parameter_files.py -q` after scoped assertion additions | Publication dependencies, fail-fast wrapper and retention/residency constraints enforced. Source tests alone do not prove Azure policy or WORM. |
| Platform | Approved Bicep/PSRule validation and resource-group-scoped what-if, then isolated archive lock/read tests | Complete graph includes two containers plus policy child; no top-level services added; genuine retention/history evidence. Exact live commands must be grounded in then-current environment and policy. |
| Human/measurement closure | Named reviewer runs supported quickstart workflows 1-4, risk/executive timed tasks, complete checklist and Step 0 rubric re-review | Real decisions and durations tied to the resulting revision; no auto-generated approval, retrospective checkbox repair or fabricated pass labels. |

## Audit Integrity

Completed 2026-09-14 at the expected source revision. These are audit-integrity results,
not product verification results:

- All 19 original local input files read completely; the sole authored file is this report.
- Exact original task-ID/state comparison: 69/69, no duplicates, omissions or suffix loss; all original `[X]` states preserved. Dependency-note repetitions excluded.
- Task status totals: 13 IMPLEMENTED, 50 PARTIAL, 2 MISSING, 1 CONFLICT, 3 UNVERIFIED.
- Exact requirement/SC sets: 38/38 FRs and 11/11 SCs, each represented separately.
- Exact scenario sets: 15/15 Given/When/Then scenarios and 8/8 edge cases.
- Checklist comparison: 84/84 reviewer IDs/states and 16/16 quality-item texts/states.
- Additional coverage: 26 unnumbered constraints, six plan decisions, five research notes, nine Step 8 dispositions, all clarifications and named synthesis persona/group duties.
- Follow-up integrity: 16 unique AUD-037 IDs, every task unchecked on its own checkbox line, and every follow-up reference resolves to a defined task.
- Local citation validation: 541/541 file links and single-line anchors resolve across 129 distinct existing targets.
- Balanced-parentheses parsing checked with three synthetic path strings, including nested parentheses and percent-encoded spaces; no fixture files created.
- Six canonical/runtime schema pairs compared byte-for-byte and matched; source-population comparisons and source-test counts used PowerShell text/JSON/CSV parsing, not product code.
- Rehearsal PowerShell source parsed without execution: zero syntax errors. This does not validate native exit-code handling or unsupported CLI commands.
- Report editor diagnostics: no errors. HEAD rechecked as `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a`; tracked source changes: zero.

Only the report was changed. No verification script, product test, build, import, model call,
browser/server, cloud query/deployment, installation, runtime/debugger, external approval,
branch or commit was performed. Runtime success, immutable archive contents, deployment state,
measurements and human decisions remain UNVERIFIED. Implementation and execution work is
left to future authorised agents under the 16 tasks above.

### 2026-09-18 Implementation Pass

This pass was performed as an isolated context for spec 037 only. Three parallel technical reviews examined evidence
population gating, authenticated/audited reads, and generated-artifact provenance. The source-completable false-pass
defect was corrected: the gate now reconciles raw discovered artefact IDs against the five canonical IDs and records
missing or duplicate population failures before schema/link validation.

Validation: direct `run_gate()` execution against the current repository returned `passed=True` with `artefacts_seen=5`;
the legacy focused link tests were both skipped because they use `importorskip`, so skipped-test evidence remains open.

Remaining open work includes Entra/RBAC/read auditing, mandatory publisher durability, historical immutable reads,
complete citation/schema/manual-row validation, generated provenance, CI discovery, retention/immutability, deployment,
and human/rehearsal evidence.
