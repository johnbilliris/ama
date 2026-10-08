# Static Implementation Audit: 027 Spec Hardening

## Metadata and Boundaries

- Review date: 2026-09-14.
- Expected revision: `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a`.
- Observed revision: `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a`; matches the requested revision.
- Scope: feature 027 and the authored specification/governance surfaces needed to establish its obligations.
  This is not a portfolio implementation audit or a runtime implementation request.
- Existing worktree: untracked audit artifacts were present before this review and were left untouched.
  No other implementation-review report was read. No existing report was present in this directory.
- Only this report is writable. Source, original tasks/specifications, evidence, checklists, and the audit index are unchanged.
- Static inspection only: no product tests, verification-script execution, builds, imports, servers, browser sessions,
  cloud operations, installs, runtime/debug calls, or external approvals. Future commands below are not execution claims.
- Governing contract: [Review Contract](../001-spec-implementation-audit/README.md#L11) and
  [code-review instructions](../../.github/instructions/code-review.instructions.md#L13).
- No delegation was used. Required review/commenting instructions and the agent-customization and Python
  fact-grounded-coding skills were read for the inspected planning definitions and test-source boundaries.
- Verdict: **PARTIAL**, with unresolved safety/governance conflicts. Existing authored work is substantial,
  but neither the original checked tasks nor the verifier's success message establishes completion.
- Accounting: **56 original tasks** (all originally `[x]`, including `T013b`), **36 FRs**, **10 SCs**,
  **9 acceptance scenarios**, **5 edge cases**, **6 appended amendment items**, and **14 unchecked follow-ups**.
  The target-artifact assessment additionally covers all **13 NFRs**, **18 persona blocks**, **6 original
  hypothesis packs**, **40 gap mappings**, **3 Open Deltas**, and **16 original checklist checkboxes**.

## Inputs and Evidence Limits

All 17 original local documents were read in full: [specification](spec.md#L1), [tasks](tasks.md#L1),
[plan](plan.md#L1), [research](research.md#L1), [data model](data-model.md#L1),
[quickstart](quickstart.md#L1), [checklist](checklists/requirements.md#L1),
[contract index](contracts/README.md#L1), [assumption contract](contracts/assumption-row.md#L1),
[NFR contract](contracts/nfr-row.md#L1), [persona contract](contracts/persona-profile.md#L1),
[hypothesis contract](contracts/hypothesis-row.md#L1), [evidence contract](contracts/evidence-pack-stub.md#L1),
[delta contract](contracts/open-delta-row.md#L1), [trace contract](contracts/traceability-row.md#L1),
[gap contract](contracts/gap-id-register-row.md#L1), and [owner contract](contracts/codeowners-entry.md#L1).

Direct deliverables and downstream inputs read in full: spec 001's [specification](../001-disaster-response-hub/spec.md#L1),
[plan](../001-disaster-response-hub/plan.md#L1), [research](../001-disaster-response-hub/research.md#L1),
[data model](../001-disaster-response-hub/data-model.md#L1), [tasks](../001-disaster-response-hub/tasks.md#L1),
[quickstart](../001-disaster-response-hub/quickstart.md#L1), [OpenAPI](../001-disaster-response-hub/contracts/openapi.yaml#L1),
[signal schema](../001-disaster-response-hub/contracts/signal-envelope.schema.json#L1), and all six evidence packs
listed below. The [gap register](../shared/gap-id-register.md#L1), [CODEOWNERS](../../.github/CODEOWNERS#L1),
[verifier](../../scripts/verify-spec-hardening.ps1#L1), Spec-Kit prerequisite/setup/common scripts, both planning
prompts, planning agent, [manual workflow](../../.github/workflows/spec-035-gate.yml#L1),
[lint configuration](../../.markdownlint.jsonc#L1), and [root manifest](../../package.json#L1) were inspected.
The [architecture-only CI lint job](../../.github/workflows/ci.yml#L445) was inspected as a possible relocated gate.

Context and explicit amendments: [capstone brief](../../capstone.md#L1),
[constitution](../../.specify/memory/constitution.md#L1), [regional annex](../../docs/disaster-response-hub/regional-adaptation-asia-pacific.md#L1),
feature 028's [specification](../028-capstone-alignment/spec.md#L1), [research](../028-capstone-alignment/research.md#L1),
[decision record](../028-capstone-alignment/evidence/decision-record.md#L1),
[rubric baseline](../028-capstone-alignment/evidence/rubric-baseline.md#L1),
[postfeature snapshot](../028-capstone-alignment/evidence/rubric-postfeature.md#L1), and
[018's reciprocal Recovery authority](../018-aidr-guidance-integration/spec.md#L342).
These are dependencies of 027's amendments, not separate audits. No other implementation-review report was opened.

Representative reachable consumers and assertions: [alert router registration](../../apps/api/app/api/router.py#L61),
[publish route](../../apps/api/app/api/routes/alerts.py#L37),
[service](../../apps/api/app/services/public_alert_service.py#L47),
[domain model](../../packages/domain/src/domain/models/public_alert.py#L31),
[live contract test](../../tests/contract/test_live_incident_contract.py#L10),
[coordination assertions](../../tests/integration/test_live_incident_coordination.py#L8),
[quickstart fixture](../../tests/simulation/test_quickstart_rehearsals.py#L21),
[metric assertions](../../tests/simulation/test_exercise_metrics.py#L6), and
[Incident Commander agent definition](../../.github/agents/operational/incident-commander.agent.md#L30).
No Python was imported, executed, or used for file I/O. No environment was installed or changed.

Read-only Git metadata identifies original feature commit `4600202b965426214ebd483214d2ba6fa0fd2db1`
(2026-04-24, subject `027-spec-hardening`) and later amendment commit
`996a1f04ebcdaafe9270e97ec71bcb816da212a5` (2026-04-25). The original commit changes spec 001 and creates all
six packs together. This establishes artifact provenance, not a passing verification run, an independent SME
review, PR approval, branch protection, or deployed performance. Subsequent file edits are assessed at the requested HEAD.

Evidence statuses mean: **IMPLEMENTED** = supported authored behavior/artifact; **PARTIAL** = specific unmet portion;
**MISSING** = absent after stated search; **CONFLICT** = incompatible requirements/current artifacts;
**UNVERIFIED** = execution/outcome/approval not established; **SUPERSEDED** = explicit replacement evidence.
An IMPLEMENTED documentation row never certifies runtime operation or the actor participation named in the original task.

## Prioritized Findings

### P1: Open Deltas Do Not Gate Planning (AUD-027-002)

The [planning agent](../../.github/agents/speckit.plan.agent.md#L23) calls
[setup-plan](../../.specify/scripts/powershell/setup-plan.ps1#L24), which copies the plan template without
checking hardening deltas. The claimed `-RequirePlan` integration in the
[verifier header](../../scripts/verify-spec-hardening.ps1#L11) is not implemented in
[prerequisite parameters](../../.specify/scripts/powershell/check-prerequisites.ps1#L17).
The [actual delta check](../../scripts/verify-spec-hardening.ps1#L146) accepts only `OD-` rows, skips
`unassigned`, and tests whether a target's plan already exists; it has no current-feature argument.
The only discovered caller is a [manual workflow](../../.github/workflows/spec-035-gate.yml#L3).
This neither prevents initial planning nor establishes a required PR gate.

Negative search: tracked `.specify/`, `.github/`, `scripts/`, `tests/`, and `tools/` were searched for
`verify-spec-hardening`, `RequirePlan`, `Open Deltas`, and `blocking_phase`; the planner, prerequisite
script, AMA planning prompt, and sole workflow caller were inspected. No relocated enforcement was found.

### P1: Safety-Approval Contradictions Remain Unreconciled (AUD-027-011)

The hardened [human-approved CAP dispatch rule](../001-disaster-response-hub/spec.md#L507) conflicts with
the downstream [autonomous approval enum](../001-disaster-response-hub/contracts/openapi.yaml#L515),
[data-model enum](../001-disaster-response-hub/data-model.md#L285), and
[quickstart's alternate-mode exception](../001-disaster-response-hub/quickstart.md#L59).
The actual [publishability check](../../apps/api/app/services/public_alert_service.py#L47) accepts
`pending_approval`, and the [registered route](../../apps/api/app/api/routes/alerts.py#L37) forwards directly to it.
The [test](../../tests/contract/test_live_incident_contract.py#L30) pre-seeds an approved alert; it does not
establish rejection of pending approval. No corresponding contradiction appears in the
[three Open Deltas](../001-disaster-response-hub/spec.md#L583). This is a concrete FR-032 reconciliation
failure and a shared-code risk; no live dispatch, authentication bypass, or external harm was demonstrated.

### P2: Claimed Five-Invariant Verification Is Incomplete (AUD-027-003)

The [gap loop](../../scripts/verify-spec-hardening.ps1#L58) only looks up cited IDs; it does not compare
register and canonical-table states, uniqueness, monotonicity, or resolving links. The
[hypothesis loop](../../scripts/verify-spec-hardening.ps1#L81) accepts any existing evidence file and never
compares its status with the hypothesis. The [signature loop](../../scripts/verify-spec-hardening.ps1#L97)
only checks NFR cells, not assumption, hypothesis, or persona transitions. The
[scope loop](../../scripts/verify-spec-hardening.ps1#L126) only compares hazard names and silently skips
missing sections. Nevertheless, the [success message](../../scripts/verify-spec-hardening.ps1#L162)
claims all five invariants pass. These are source-derived failure cases, not executed mutation tests.

### P2: Review Authority Is Role-Only and Provisionally Bypassed (AUD-027-004)

[Assumption provenance](../001-disaster-response-hub/spec.md#L100),
[NFR signatures](../001-disaster-response-hub/spec.md#L151), and
[persona validators](../001-disaster-response-hub/spec.md#L169) use actor handles or generic panel descriptions,
not attributable names and dates. The [authority subsection](../001-disaster-response-hub/spec.md#L568)
substitutes any maintainer plus any SME for FR-034's artifact-specific proposer/countersigner matrix.
[OD-003](../001-disaster-response-hub/spec.md#L585) explicitly admits the missing names but uses
`none (authoring workflow)` instead of the required plan-blocking deadline.
The [interim owner](../../.github/CODEOWNERS#L22) is commented out; team existence, membership and approval
enforcement are UNVERIFIED, not assumed absent. An [actor profile](../../.github/agents/operational/incident-commander.agent.md#L30)
is a role definition, not an actual practitioner's sign-off.

### P2: Autonomy Categories and Override Windows Are Incomplete (AUD-027-008)

The seven [authored rows](../001-disaster-response-hub/spec.md#L505) are not FR-025's seven required categories.
There is no explicit evacuation-routing, resource-pre-positioning, SMS/voice-draft, or de-escalation/closure row;
field-task assignment is only partly represented by internal resource assignment. `Decide` and
`Decide (with human over-ride)` do not specify the required bounded override window. A public evacuation order
is not interchangeable with evacuation-route recommendation. Counting seven rows therefore cannot establish SC-007.

### P2: NFR Promotion Leaves Concrete Quality Commitments Missing (AUD-027-009)

[NFR-005](../001-disaster-response-hub/spec.md#L155) retains 60-second visibility but does not promote the
[plan's](../001-disaster-response-hub/plan.md#L20) under-2-second initial load or under-500-ms read-API p95 targets;
the plan lacks the required source-pointer comments. [NFR-011](../001-disaster-response-hub/spec.md#L161)
sets a training-pack refresh deadline, not an onboarding target for unassisted SC-003 completion.
[NFR-003](../001-disaster-response-hub/spec.md#L153) names STRIDE but not all four mandated threats.
[NFR-002](../001-disaster-response-hub/spec.md#L152) does not explicitly classify location retention;
[audit rows](../001-disaster-response-hub/spec.md#L158) provide immutability/retention/recovery targets without
a defined export/record format. Names of standards and proposed dashboards do not prove numeric basis approval.

### P2: Persona Counts Mask Missing Profiles and Validation Detail (AUD-027-005)

All 18 [persona blocks](../001-disaster-response-hub/spec.md#L167) were inspected. All have goals/pains/top-3
tasks but lack per-profile device, language, technical-proficiency and time-tolerance fields; general ASM-008
does not map those values to each persona. Thirteen `aiims_function` values are outside the contract enum and
none is `Intelligence`. The [community cohort](../001-disaster-response-hub/spec.md#L301) substitutes broad
CALD/remote/disability archetypes for separately required native-language, limited-literacy, low-vision and
hard-of-hearing coverage. The [second accessibility operator](../001-disaster-response-hub/spec.md#L421)
is voice/switch access, not the mandated hard-of-hearing field worker. No block supplies a dated named validator;
the SC-003 "validated" cohort is therefore UNVERIFIED.

### P2: Hypothesis States, Falsifiers and Evidence Packs Diverge (AUD-027-006)

All six [hypothesis rows](../001-disaster-response-hub/spec.md#L441) and their six packs use `Proposed`,
which neither FR-020 nor the local hypothesis contract permits. None uses the mandated full statement form.
[HYP-005](../001-disaster-response-hub/spec.md#L445) leaves the tolerance undefined;
[HYP-006](../001-disaster-response-hub/spec.md#L446) leaves the adaptation envelope/window unbounded.
The packs are real stubs, not missing files, but omit required authority metadata and the visible
`No observations yet` marker. The [later decision](../028-capstone-alignment/evidence/decision-record.md#L20)
explicitly records the six packs as carry-over, not repaired or retired.
The appended [HYP-025](spec.md#L272) has no status or bounded window, and its claimed evidence stub is absent
after filename and content searches across tracked `specs/`; only the amendment and a generator watermark refer to it.
The rubric snapshots are authored structural assessments, not attributable independent review or HYP-025 settlement.

### P2: Jurisdiction Rationale and Deferred Register Are Incomplete (AUD-027-007)

[Australia is explicit](../001-disaster-response-hub/spec.md#L456), but the target Scope lacks the dated
Australia-over-Asia rationale required by FR-022. It covers all Australian tiers, conflicting with
[T010](tasks.md#L93) and [research R-9](research.md#L127), which require one named state/territory.
The 16 [deferred rows](../001-disaster-response-hub/spec.md#L463) have reasons/triggers but no `target_feature`
or extensibility-evidence fields and use lowercase kinds rather than the specified enum. All seven required
excluded hazards are named; none is silently missing. The annex's six linked country seed/language files are
absent, and no relocated implementation was found by name or country/source search in the seed/template/fixture
surfaces. The annex itself remains authored design evidence, not runnable adaptation evidence or a scope override.

### P2: Remaining Scope Lists Do Not Form a Complete Boundary (AUD-027-013)

The [source list](../001-disaster-response-hub/spec.md#L514) admits open platform APIs and any licensed
third-party feed without a licensing instrument/moderation duty per source or an exclusion rule.
The [citizen list](../001-disaster-response-hub/spec.md#L529) omits explicit push-app, two-way-SMS and voice-IVR
decisions. The [integration list](../001-disaster-response-hub/spec.md#L539) omits named CAD/EOC/GIS/SCADA/
cell-broadcast dispositions and an exclude-all-others rule. The [Recovery stance](../001-disaster-response-hub/spec.md#L523)
provides a referral, not a hand-off contract; later 018 ownership does not supply that interface here.
The [rehearsal rules](../001-disaster-response-hub/spec.md#L554) define isolation but never select shipped,
imported or user-authored content as the single FR-030 boundary.

### P2: Misinformation Handling Has No Required Normative Commitment (AUD-027-014)

The [target FR list](../001-disaster-response-hub/spec.md#L70) provides provenance and degraded-input handling,
but no misinformation-specific detection/down-ranking FR naming operator-visible evidence. The
[rebuttal-drafting row](../001-disaster-response-hub/spec.md#L510), [provenance NFR](../001-disaster-response-hub/spec.md#L157),
and [unsettled HYP-005](../001-disaster-response-hub/spec.md#L445) do not replace FR-012's required commitment
or an explicit v1 deferral. The [representative test](../../tests/integration/test_live_incident_coordination.py#L8)
asserts authoritative-vs-social scoring, not coordinated-misinformation detection or an evidence surface.

### P2: Traceability Claims Closure While Every Gap Remains Open (AUD-027-010)

All 40 [canonical rows](spec.md#L207) say `Resolved`, while all 40
[register rows](../shared/gap-id-register.md#L19) say `Open` with no evidence link.
The canonical resolving cells are prose, and `evidence/HYP-006.md` is relative to 027 rather than the actual
001 pack. The [changelog pointer](../001-disaster-response-hub/spec.md#L595) is unlinked prose, not the
required anchor-bearing row. The register omits per-allocation dates required by FR-036.
The register is not missing: a static inventory of 544 tracked spec text artifacts found exactly 40 literal
gap IDs, all registered, currently unique and contiguous. This validates present coverage, not append-only history.

### P2: Document Tooling Is Not the Claimed Scoped Gate (AUD-027-012)

The [configuration](../../.markdownlint.jsonc#L8) globally disables line-length and inline-HTML rules while
its header claims no global disables. Its `ignores` property is in a rule-config file, not a demonstrated
CLI2 path override. No `markdownlint-cli2` or `markdown-link-check` dependency appears in the inspected root/
workspace manifests or lockfile. The only discovered lint/link CI job targets
[architecture documentation](../../.github/workflows/ci.yml#L474), not the hardening artifacts.
Historical T049/T050 execution remains UNVERIFIED; neither missing local dependencies nor authored checkmarks
are proof that those commands did or did not run on another machine.

### P2: Required Reviewer Checklist and Close-out Are Unsupported (AUD-027-001)

The original [task](tasks.md#L356) requires T054 to create one checkbox per FR, SC, and Open Delta.
The delivered [checklist](checklists/requirements.md#L8) instead contains 16 generic checked statements.
The [specification](spec.md#L95) defines 36 FRs and 10 SCs, so this cannot meet the 46-item minimum even before
the 3 current deltas (49 minimum today). [T052](tasks.md#L346) is checked but the
[plan](plan.md#L163) still says Phase 2 is not started and has no seal. Spec 001 lacks the required
`Last reviewed` line. No local attributable records establish the SC-001/SC-009 walkthroughs, T051 execution,
or T053 PR approval and green CI; commit metadata alone cannot establish those outcomes.
Its checked readiness statements are authored self-attestations, not evidence of practitioner walkthroughs or approvals.

## Follow-up Tasks

- [ ] AUD-027-001 Replace the generic checklist with obligation-level review evidence

**Source obligations and original tasks:** T007, T049, T050, T051, T052, T053, T054; FR-033; SC-001, SC-009;
the specification's Evaluation Method and
the local [checklist](checklists/requirements.md#L16).

**Expected versus observed:** At least one checkbox per 36 FRs, 10 SCs, and each Open Delta is required;
only 16 generic checked items are authored, versus 49 including today's deltas. The plan seal and target
Last-reviewed line are absent. No completion or human-review outcome is inferred from existing marks.

**Impact:** A reviewer cannot establish complete coverage or reliably distinguish an authored requirement from a verified outcome.

**Developer instructions:** The product-owner/BA owns the existing checklist with QA and observer/auditor review.
Map every original obligation explicitly, retain supported review history, and separate static completeness from
human acceptance. Preserve original requirement IDs and the 027-to-001 ownership boundary; do not fabricate signatures.
Reconcile plan phase status and actual review dates; do not backdate a seal. Record any genuine PR/check results
with their revision, and record unperformed activities as unverified rather than inventing retrospective evidence.

**Tester instructions:** Use the existing checklist and original task/specification documents as the verification homes.
Assert every FR/SC has its own review item; removing an item must be detected; an Open Delta must have a corresponding
review item even when other checks pass. A checked generic statement must not count as an attributable walkthrough.

**Future commands, prerequisites, and expected outcomes:** With PowerShell 7, use
`Select-String -Path specs/027-spec-hardening/checklists/requirements.md -Pattern 'FR-|SC-|OD-'`
and compare to the original FR/SC/delta sets; expect no omitted or duplicated obligations. Use `git diff --check`
for document integrity, not as proof of review. Actual SC-001/SC-009
walkthroughs require the named independent human roles and attributable records; those activities were not performed here.

**Completion criteria:** Complete obligation-level checklist coverage and separately attributable evidence for any
claimed human acceptance, with unperformed reviews explicitly left unverified.

- [ ] AUD-027-002 Enforce feature-scoped Open Delta checks before planning writes

**Source obligations and original tasks:** FR-032; SC-008; T046, T047, T055;
[Open Delta contract](contracts/open-delta-row.md#L31), data-model invariant 5, and Quickstart step 7.

**Expected versus observed:** An unresolved plan-blocking delta must reject entry for its owning feature before
planning begins. The plan creator has no check; the verifier instead inspects already-existing plans globally.
The advertised `-RequirePlan` parameter does not exist, and the workflow is manually dispatched.

**Impact:** Planning can proceed on contradictions that the specification explicitly requires to be resolved first;
adding the current global check later would also risk blocking unrelated features.

**Developer instructions:** The Spec-Kit tooling owner and principal engineer own the existing setup-plan,
prerequisite script, planning agent, AMA prompt, and verifier boundary. Resolve the running feature with the
existing feature-path mechanism; enforce the approved delta schema before any template copy or other plan write.
Preserve normal planning outside this monorepo and unaffected-feature behavior. Coordinate schema/authority
decisions with the product owner; document one real integration point and propagate failure unchanged.

**Tester instructions:** Existing homes are the Spec-Kit PowerShell scripts and their caller definitions;
no hardening-specific test caller was found in the scoped search above. A dedicated fixture suite is proposed,
not existing evidence. In an isolated temporary repository, cover matching unresolved delta with no plan yet,
matching resolved delta with a valid resolution, unrelated delta, malformed target, unassigned ownership,
and a non-monorepo invocation. Assert rejection occurs before creation or overwrite and identifies the delta.

**Future commands, prerequisites, and expected outcomes:** After the fix, with PowerShell 7 and an isolated
fixture repository, invoke its `.specify/scripts/powershell/setup-plan.ps1 -Json` using the fixture's feature
selection. Matching unresolved deltas must exit nonzero without writes; resolved/unrelated cases must preserve
the established JSON contract. Inspect CI event wiring separately; a manual job is not evidence of branch protection.

**Completion criteria:** Every supported planning entry point reaches a fail-closed, feature-scoped guard before
writes; positive, negative, and first-plan cases have attributable test results. No external enforcement is
claimed without independent configuration/review evidence.

- [ ] AUD-027-003 Implement the declared cross-entity invariants and negative coverage

**Source obligations and original tasks:** T046; FR-020, FR-031, FR-032, FR-034, FR-035, FR-036;
[data-model invariants](data-model.md#L301), entity validations, and the local row/file contracts.

**Expected versus observed:** The verifier promises gap symmetry, evidence lockstep, transition signatures,
scope consistency, and plan ordering. Current checks are narrower than these obligations and accept structurally
incomplete inputs without validating the relevant invariant.

**Impact:** A green success message can certify internally contradictory or incomplete governance artifacts.

**Developer instructions:** The tooling developer owns the existing verifier, with QA and principal-engineer review.
Parse complete sections/rows without discarding empty cells; validate required fields, accepted enums, and
nonempty collections against an explicitly reconciled contract. Compare both sides of register/traceability and
hypothesis/evidence relationships. Validate all state-bearing entities and all required scope categories.
Retain useful diagnostics and stable command behavior; coordinate the planning-specific check with AUD-027-002.
Append-only/history checks need an explicit baseline revision, not fabricated historical execution evidence.

**Tester instructions:** Use the existing verifier and the 027 contracts as the fixture specification; a new
hardening test suite is proposed. Required negative fixtures: register/traceability status mismatch; duplicate
or skipped gap allocation; absent resolving link; mismatched hypothesis/evidence status; missing transition
signer; missing or empty section; capitalized `Hazard` classification; a deferred citizen surface also in scope;
and an unresolved target without a plan. Valid complete fixtures must pass, and each single breach must fail
with its invariant and entity ID. No fixture was written or run in this audit.

**Future commands, prerequisites, and expected outcomes:** After implementation, run the fixture-local
`pwsh -File scripts/verify-spec-hardening.ps1` with PowerShell 7; expect exit 0 only for complete valid input and
exit 1 with an actionable diagnostic for each synthetic breach. Use a temporary repository because the current
script resolves inputs relative to its own directory. Existing product tests are not substitutes for these checks.

**Completion criteria:** All five invariants and their required entity checks are actually enforced, with
negative assertions proving detection; the success message accurately describes the performed checks.
These are future completion criteria, not results of this static audit.

- [ ] AUD-027-004 Restore attributable artifact-specific review authority

**Source obligations and original tasks:** FR-001, FR-016, FR-032, FR-034, FR-035; T005, T006, T012,
T016, T017, T018, T019, T020, T021, T022, T023, T026, T027, T047, T053; Clarifications 2, 3, 6, 7.

**Expected versus observed:** Named eligible proposers and countersigners must record effective transitions;
privacy/security/residency NFRs additionally need the named privacy reviewer. Current roles/generic panels are
not identities, the matrix is replaced by generic maintainer authority, and OD-003 waives the deadline.

**Impact:** Provisional NFRs/personas can be described as normative/validated without the required accountable review.

**Developer instructions:** Product-owner/BA, security and compliance own the target authority matrix, changelog,
provisional-item deltas and CODEOWNERS. Restore domain-SME plus planner/privacy for assumptions, test lead plus
planner for hypotheses, and UX lead plus jurisdiction SME for personas. Record names, dates, independent roles
and review provenance only when genuine. Require the planner's drafting attribution for NFR targets or explicitly
resolve the conflicting task actor assignments. Mark unsigned items provisional with real owner, feature and
plan deadline. Preserve the actual 028 directory name; do not create the obsolete holistic-hardening directory.

**Tester instructions:** Use the existing persona/evidence contracts, target rows and CODEOWNERS as fixtures.
Check an eligible independent pair succeeds; the same person twice, role-only values, missing date, wrong-role
countersign, and missing required privacy reviewer fail. A commented owner cannot satisfy interim ownership.
Authority evidence must not be substituted with an actor-agent transcript or a generic team label.

**Future commands, prerequisites, and expected outcomes:** After AUD-027-003, run
`pwsh -File scripts/verify-spec-hardening.ps1` in isolated valid/invalid fixtures; expect explicit signature errors.
`git log --format=fuller -- .github/CODEOWNERS specs/001-disaster-response-hub/spec.md` can establish change
provenance, not team membership or approvals. Those require separately authorized read-only GitHub evidence;
actual signatures require the human reviewers, not this audit.

**Completion criteria:** Correct matrix, attributable effective signatures, explicit provisional status and
plan-blocking unresolved deltas; team/approval claims remain unverified until independently evidenced.

- [ ] AUD-027-005 Complete the persona profiles and cohort mapping

**Source obligations and original tasks:** FR-014, FR-015, FR-016, FR-017; SC-004; US2-AS3;
T026, T027, T028, T029, T030, T031; E-4 and the persona contract; appended PER-073.

**Expected versus observed:** Every mandated archetype needs complete context and usability fields and an
explicit jurisdiction-validation state. Eighteen blocks exist, but required archetypes/fields, enum conformance,
scenario links, two-sided authority and named validation records are incomplete.

**Impact:** UX cannot define the promised cohort or test SC-003 without private assumptions about participants and tasks.

**Developer instructions:** UX lead owns the existing inline persona section with AIIMS/domain and accessibility
SMEs. Complete device, language, context, proficiency, time tolerance, goals, pains, authority and top-three tasks
for each profile; add missing Intelligence and hearing/vision/literacy coverage without silently substituting
motor-access profiles. Map existing P-* IDs to the agreed PER taxonomy instead of renumbering downstream IDs.
Use real scenario links, mitigated FR links for adversaries, and explicit non-AU placeholders. Coordinate actual
validation and proxy eligibility with AUD-027-004/AUD-027-011, not fictional role credentials.

**Tester instructions:** Review all 18 current profiles plus any additions against the existing persona contract.
Check each of six AIIMS functions and every FR-015 archetype independently; a generic disability profile must
not count as all access needs. Negative cases: missing language/device, unilateral-only authority, free-text
invalid enum, nonexistent scenario, role-only validator, or placeholder counted in the validated SC-003 cohort.

**Future commands, prerequisites, and expected outcomes:** After validator repair use
`pwsh -File scripts/verify-spec-hardening.ps1` in fixture copies; expect each missing field/archetype to fail.
`Select-String -Path specs/001-disaster-response-hub/spec.md -Pattern 'persona_id:|aiims_function:|validated_by:'`
supports inventory only. Actual usability and jurisdiction validation need consented representative participants
and the named reviewers, with results stored in the existing profile/evidence homes.

**Completion criteria:** Every mandated archetype and usability field has attributable, contract-conformant
coverage; SC-003 references only the genuinely validated named cohort.

- [ ] AUD-027-006 Reconcile hypothesis lifecycles and complete their evidence contracts

**Source obligations and original tasks:** FR-018, FR-019, FR-020, FR-021; SC-005, SC-006; US3-AS1, US3-AS2;
T013, T013b, T040, T041, T042, T043, T044; appended HYP-025 and Clarifications 4 and 9.

**Expected versus observed:** Hypotheses use the mandated persona/outcome/falsifier/window form, allowed states
and creation-time packs. The original six exist but use `Proposed`; HYP-005/HYP-006 have unbounded tolerances;
HYP-025's stated pack is missing, and its "regression" falsifier cannot reject a zero-to-less-than-one-band uplift.

**Impact:** An assessor cannot reproducibly falsify the claims or audit a valid status transition.

**Developer instructions:** Test lead and product owner own the existing six rows/packs and HYP-025 amendment.
Resolve lifecycle precedence explicitly, then use Not tested for unobserved claims without implying execution.
Specify quantified thresholds, personas, bounded windows and real linked decisions; retain all three SC causal
cross-references. Update existing packs in place with the required history/authority structure and visible
no-observations marker. Agree HYP-025 ownership with 028; its missing pack is a proposed artifact, not existing
evidence. Preserve prior authoring history and document any schema migration.

**Tester instructions:** Use the six existing packs as fixture homes and the local hypothesis/evidence contracts.
Check row/pack status equality, required fields, real relative targets and bounded falsifiers. Negative cases:
existing but mismatched pack, arbitrary Proposed/Validated state against the selected enum, absent window,
undefined tolerance, and an HYP-025 uplift of +0.5 with no regression. Boundary uplift +1 should satisfy its
quantitative condition; snapshots without attributable methodology must not count as settled evidence.

**Future commands, prerequisites, and expected outcomes:** After AUD-027-003/AUD-027-011, run
`pwsh -File scripts/verify-spec-hardening.ps1` against isolated fixtures; each breach must fail. A text check
`git grep -n HYP-025 -- specs` must find a real owned pack reference, not just a generator watermark. Rehearsal,
comparative study and rubric settlement are future separately authorized work, not required to invent observations now.

**Completion criteria:** Conformant untested records exist for every hypothesis, all references resolve, and
subsequent observed transitions require real evidence and signatures; no missing evidence is replaced by a checkbox.

- [ ] AUD-027-007 Resolve the reference jurisdiction and complete deferral provenance

**Source obligations and original tasks:** FR-003, FR-022, FR-023, FR-024; US1-AS1; T010, T011, T012,
T024, T032; research R-9; E-7/E-8; clarification 1 and appended ASM-083/SCP-083.

**Expected versus observed:** A dated rationale, agreed reference jurisdiction and complete deferred records are
required. Australia is clear, all seven excluded hazards exist, but state-versus-country scope conflicts and
deferral targets/evidence/kind values do not satisfy the specified schema.

**Impact:** Reviewers cannot determine the committed evaluation boundary or prerequisites for credible promotion.

**Developer instructions:** Product owner, planner and jurisdiction SMEs own the existing Scope/Assumptions and
deferred/hazard tables. Resolve country-wide versus one-state scope with an explicit dated decision; do not
silently reverse Australia-first or claim Asia delivery. Add target feature or literal unassigned, correct kinds,
evidence citations (or honest none) and promotion conditions to every deferral. Keep the four capability and
seven hazard exclusions, and update annex references to existing artifacts or identify them as proposals.
Coordinate Recovery ownership with 018, not a new competing recovery implementation.

**Tester instructions:** Use existing scope tables, constitution Principle III and the annex as comparison inputs.
Check all 3 jurisdictions, 7 excluded hazards, 4 capability deferrals and remaining rows, including unique kinds,
targets, evidence and triggers. Removing one hazard or pointing at a nonexistent seed must fail; no evidence
must be represented as none, not a invented file. A new seed alone must never promote a jurisdiction.

**Future commands, prerequisites, and expected outcomes:** After repair run
`pwsh -File scripts/verify-spec-hardening.ps1` in isolated fixtures and the scoped Markdown checks after
AUD-027-012. `Test-Path` on each authored evidence target must succeed, unless the cell explicitly states none.
Named SMEs must approve the dated jurisdiction rationale independently; no external approvals were requested here.

**Completion criteria:** One explicit reference scope, a self-contained dated rationale, complete deferral
provenance and no missing named hazards; unvalidated assets remain deferred.

- [ ] AUD-027-008 Classify every required agent action and its override boundary

**Source obligations and original tasks:** FR-025; SC-007; US2-AS4; T033; autonomy portions of T009 and T047.

**Expected versus observed:** All seven named categories require one of the three defined classes and a bounded
operator window where autonomous execution is allowed. The current seven different rows do not meet that set.

**Impact:** Safety-sensitive route, assignment and closure decisions can be planned without a clear approval contract.

**Developer instructions:** Security engineer owns the table with incident-controller, operations and PIO review.
Explicitly classify public publication, evacuation routing, pre-positioning, SMS/voice drafts, new-signal ranking,
field-task assignment and de-escalation/closure. Define override duration, veto handling, timeout/default behavior
and audit obligation where applicable. Distinguish advice from irreversible action; preserve mandatory human
approval for public dispatch and evacuation, and coordinate existing-consumer deltas through AUD-027-011.

**Tester instructions:** The existing autonomy table and contract/live coordination tests are reference homes.
Compare required category sets, not row counts. Negative cases: order substituted for route, voice drafting
omitted, Decide with no veto window, and timeout causing an irreversible action without approval. The approved
advisory-only case must not be treated as automatic public execution. Runtime assertions belong to the assigned
follow-on feature; no test or application change is made in this documentation audit.

**Future commands, prerequisites, and expected outcomes:** After invariant repair,
`pwsh -File scripts/verify-spec-hardening.ps1` on fixture documents must reject every missing category/window.
An independently approved scope matrix and follow-on compatibility review are prerequisites for runtime tests.

**Completion criteria:** All seven required categories have unambiguous classes, approval owners and override
semantics, with any current implementation disagreement explicitly owned and plan-blocking.

- [ ] AUD-027-009 Restore the omitted NFR targets and measurement boundaries

**Source obligations and original tasks:** FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010,
FR-013, FR-035; T017, T018, T019, T020, T021, T022, T023; US2-AS1 and US2-AS2.

**Expected versus observed:** Existing targets must be promoted unchanged with measurement surface and signed
basis; all specified threat, location-retention, onboarding and audit-format obligations must be explicit.
Current NFRs omit several of those obligations or substitute release-document freshness for onboarding.

**Impact:** Downstream tests and DPIA design depend on thresholds and rules that are not actually fixed.

**Developer instructions:** Planner owns NFR drafting; SRE, security, privacy, accessibility, interoperability
and training SMEs own their domains. Promote initial-load <2 s and read-API p95 <500 ms with exclusions/network
profiles intact; add source pointers to the plan. Enumerate all four required threats and location-data handling.
Define an onboarding target tied to SC-003 and a durable audit record/export format. Resolve the combined
interoperability row versus T021's three-row requirement explicitly. Use real basis citations and names or mark
targets provisional under AUD-027-004; do not change runtime or capstone numerical outcomes under feature 027.

**Tester instructions:** Existing inputs are spec 001's plan, 13 NFR rows and quickstart. Check every row's target,
measurement and evaluation surface plus required bases/signatures. Negative cases: dropped API target, latency
that includes model time when excluded by the plan, no location retention category, absent coordinated-misinfo
threat, unsigned privacy NFR, and training-pack update substituted for unassisted onboarding measurement.

**Future commands, prerequisites, and expected outcomes:** Use
`Select-String -Path specs/001-disaster-response-hub/plan.md,specs/001-disaster-response-hub/spec.md -Pattern '500|2 seconds|NFR source moved'`
for the promotion cross-check, then the repaired verifier in fixtures. Actual latency, onboarding, retention and
restore claims require future approved workloads, cohorts, privacy rules and observation records; none are proven here.

**Completion criteria:** All mandated NFR content is normative or explicitly provisional, source targets agree,
and every proposed measurement has a concrete surface without fabricated results or approvals.

- [ ] AUD-027-010 Reconcile gap states and make traceability navigable

**Source obligations and original tasks:** FR-031, FR-033, FR-036; SC-002, SC-008; T004, T007, T012,
T015, T039, T045, T047, T048; E-1/E-10 and trace/register contracts.

**Expected versus observed:** Current gap and trace states agree, all resolving items/pack paths are real,
allocations are dated, and spec 001 has one anchor-bearing pointer row. Forty mappings exist but disagree with
the register, point by prose, omit allocation dates and do not trace all Open Deltas.

**Impact:** Closure and maintenance decisions cannot be independently followed or replayed from the canonical table.

**Developer instructions:** Product-owner/BA owns the canonical table/register with observer-auditor review.
Preserve all IDs and truthful states; do not mass-mark gaps Resolved to match an inaccurate table. Link each
mapping to a real existing requirement/section and each pack to its owning directory; retain the single canonical
table and add only a pointer row in spec 001. Reconcile the requirement for Open Delta references with the
40-gap table schema explicitly. Add factual allocation dates/withdrawal reasons without rewriting history.
Coordinate validator comparisons with AUD-027-003 and closure decisions with the substantive follow-ups.

**Tester instructions:** Use all 40 original register/trace rows, not a sample. Assert ID-set equality, agreed
states, valid resolving anchors, correct HYP relative paths, allocation metadata, and one pointer/no duplicate table.
Negative cases: a 41st duplicate, one mismatched status, resolving prose with no anchor, missing evidence, a
withdrawn ID reused, and an omitted delta. A registered but Open gap is valid bookkeeping, not automatic closure.

**Future commands, prerequisites, and expected outcomes:** Run the repaired
`pwsh -File scripts/verify-spec-hardening.ps1` against valid and single-breach fixtures; expect appropriate
nonzero results. `git log --follow -- specs/shared/gap-id-register.md` supports append-only provenance review;
use real prior revisions, not current-file contiguity, to assess no deletion/reuse over time.

**Completion criteria:** Exhaustive gap coverage is preserved, closure states are evidence-based, all actual
references resolve, and allocation/history rules are verifiably maintained.

- [ ] AUD-027-011 Reconcile conflicting contracts and record downstream safety deltas

**Source obligations and original tasks:** FR-001, FR-016, FR-018, FR-020, FR-022, FR-032, FR-034,
FR-035; SC-008; T005, T009, T010, T013, T013b, T047; all local entity contracts and edge cases EC-01/EC-04.

**Expected versus observed:** Normative requirements, templates and consumers must agree or carry governed
deltas. Assumption/hypothesis states, proxy rules, authority, delta IDs/phases and the single-state rule conflict.
Downstream autonomous alert modes and the pending-approval service path are not listed in Open Deltas.

**Impact:** Applying one published contract can violate another, while known safety differences remain unowned.

**Developer instructions:** Product owner and principal engineer own specification/contract reconciliation;
security/privacy review safety and residency rules. Record explicit precedence or approved amendments instead
of silently treating tasks, research or later timestamps as supersession. For each contradiction, reconcile the
documentation or create an owned follow-on delta with a real feature, deadline and resolution link. Runtime
owners are the alert router/service and shared PublicAlert model, but any runtime repair belongs to an explicitly
assigned follow-on feature, not this report or a silent expansion of documentation-only 027. Preserve public
API compatibility during later schema migration. Retain the constitution's bounded model-hosting carve-out;
an APP-8 disclosure must not be interpreted as unrestricted non-AU operational-data persistence.

**Tester instructions:** Existing homes include the live contract/coordination tests and quickstart fixtures cited
above. For future runtime work, assert approved authorized publish succeeds; pending/unapproved/rejected alert
publication fails without mutating state; a supplied persona string is not evidence of approval. For docs, test
every lifecycle enum, documented proxy eligibility, DELTA/OD identifier and blocking phase against the reconciled
contract, and ensure no contradiction is merely marked none/unassigned without governance.

**Future commands, prerequisites, and expected outcomes:** After explicit follow-on ownership and approved
implementation, `pytest tests/contract/test_live_incident_contract.py tests/integration/test_live_incident_coordination.py -q`
is a relevant existing test entry point, but must be extended with the negative assertions first. It requires the
project's configured Python dependencies and isolated in-memory fixtures. It was not run here. Documentation
fixtures use the repaired verifier; expect one consistent contract and explicit blocking diagnostics for unresolved deltas.

**Completion criteria:** A documented compatible contract decision for every listed conflict, real ownership and
plan gating for deferred changes, and attributable later safety tests before any runtime completion claim.

- [ ] AUD-027-012 Make Markdown and link checks reproducible and correctly scoped

**Source obligations and original tasks:** T002, T049, T050, T053; research R-7; plan testing/quality gates;
Quickstart step 10 and the no-global-rule-disable constraint.

**Expected versus observed:** Declared tools and path-local exceptions validate every touched document and
relative link. Current rule disables are global; no inspected dependency/PR job establishes this hardening gate.

**Impact:** Another developer cannot reproduce the asserted doc checks from the declared workspace toolchain,
and broader Markdown quality is weakened by exceptions intended only for spec tables.

**Developer instructions:** Tooling/DevOps owner and principal engineer own the existing lint configuration,
manifest/lockfile and CI boundary. Use supported CLI2 configuration for ignores/path scope; retain strict rules
elsewhere. Declare/pin the intended tooling through normal dependency management when separately authorized.
Validate all 027, amended 001 and shared documents while excluding non-Markdown CODEOWNERS from Markdown lint.
Do not mask broken links with broad ignores; distinguish illustrative fenced placeholders from actual citations.

**Tester instructions:** Use the existing configuration, original documents and actual broken annex/trace targets
as static fixtures. Long spec table succeeds under its local exception; unrelated Markdown still enforces line
length; missing local targets/anchors fail; external URLs are not queried by the relative-link gate. Ensure
the gate runs for a relevant PR, not only manual dispatch or architecture-doc changes.

**Future commands, prerequisites, and expected outcomes:** After dependency/config repair, with the pinned tools
already installed, run `pnpm exec markdownlint-cli2 "specs/027-spec-hardening/**/*.md" "specs/001-disaster-response-hub/**/*.md" "specs/shared/**/*.md"`.
Run the selected relative-only checker over the same Markdown set with explicit external-URL exclusion.
Expected: zero violations on valid docs and nonzero for each synthetic bad link/out-of-scope rule breach.
No install, lint CLI execution or network link-check was performed in this audit.

**Completion criteria:** Reproducible dependencies, genuinely scoped exceptions and a reachable required doc gate,
with fresh revision-bound results rather than retrospective assertion.

- [ ] AUD-027-013 Complete source, surface, integration and rehearsal scope contracts

**Source obligations and original tasks:** FR-023, FR-026, FR-027, FR-028, FR-029, FR-030;
US2-AS4; T034, T035, T036, T037, T038; E-7/E-8 and the Recovery ownership amendment.

**Expected versus observed:** Each permitted source has licensing/moderation rules; every named citizen surface
and integration has a disposition; Recovery has a handoff interface; rehearsal content has one origin boundary.
Current lists and isolation rules provide only part of that contract.

**Impact:** Ingestion, UX, integration and scenario authors can make incompatible assumptions about what v1 includes.

**Developer instructions:** Data governance/privacy own the source whitelist; UX/PIO own citizen channels;
API architecture owns integration/handoff contracts; QA/planner own scenario origin. Complete these existing
subsections with explicit exclusions, real licensing instruments and moderation duties, named owners, protocol/
payload/version/auth boundaries and promotion conditions. Define Recovery referral contents/recipient/acknowledgment
in coordination with authoritative spec 018. Choose one shipped/imported/user-authored origin without weakening
rehearsal isolation or silently introducing live integrations.

**Tester instructions:** Use existing Scope tables, OpenAPI and signal-envelope contracts as verification homes.
Assert every FR-named item has a unique status; an unnamed platform or commercial feed is denied by default;
missing license/moderation cannot be treated as licensed. Check public dashboard, push app, two-way SMS, IVR,
CAD, EOC, GIS, SCADA and cell broadcast explicitly. Rehearsal-origin ambiguity and a missing Recovery recipient
or payload must fail. Published fictional examples must not be counted as executed integrations.

**Future commands, prerequisites, and expected outcomes:** After scope-validator repair,
`pwsh -File scripts/verify-spec-hardening.ps1` on exhaustive document fixtures must detect every omission and
deferred/in-scope collision. Future integration tests need the agreed contracts and non-live adapters; no provider
connection, licensing approval or live dispatch is part of this audit.

**Completion criteria:** A complete, testable and owner-assigned v1 boundary with honest exclusions and deferrals,
compatible with 018 Recovery ownership and the existing human-approval/isolation rules.

- [ ] AUD-027-014 Specify misinformation detection and operator-visible evidence

**Source obligations and original tasks:** FR-012; T025; related T019/T029/T042;
REQ-GAP-009, HYP-GAP-005 and the misinformation edge case in the hardened target.

**Expected versus observed:** A normative v1 detection/down-ranking rule with an operator evidence surface,
or a reasoned explicit deferral, is required. Provenance labels, drafting and an unbounded hypothesis are not that FR.

**Impact:** Users can see trust tiers without a defined response to coordinated falsehoods or a way to inspect the evidence.

**Developer instructions:** PIO owns the normative commitment with AI/data and security SME review. Specify
detection inputs, treatment of uncertain/contradictory signals, down-ranking/fallback and the exact evidence shown
to operators; or explicitly defer with rationale and a governed DEF row. Preserve authoritative-source primacy,
human approval of rebuttals and privacy limits. Route algorithm/UI changes to the relevant follow-on owners;
do not implement them as untracked work in this documentation-only feature.

**Tester instructions:** Existing scoring/guardrail assertions in the live coordination test are the starting
home, not sufficient coverage. Future cases: coordinated spoofed authority is flagged/down-ranked with source
evidence; an isolated legitimate community report is not automatically rejected; contradictory official feeds
escalate to a human; absence of corroboration is visible; a rebuttal never auto-publishes. Link assertions to the
specified surface and quantitative HYP-005 tolerance, not a fabricated exercise result.

**Future commands, prerequisites, and expected outcomes:** After separately approved implementation and test
extension, `pytest tests/integration/test_live_incident_coordination.py -q` is an existing entry point requiring
the configured project environment and isolated fixtures. Expect concrete detection/evidence/fallback assertions;
an authoritative-score-greater-than-social assertion alone must not close this obligation.

**Completion criteria:** Either the complete normative detection/evidence requirement or an explicit justified v1
deferral, with traceability and ownership; no claim of operational effectiveness without future measured evidence.

## Requirement and Success-Criterion Coverage

IDs in this table belong to feature 027. References to spec 001 identify the authored deliverable, not a second audit.
SC-003 below assesses the presence of target/method/surface, not target validity, approval, or observed compliance.

| Requirement | Status | Inspected evidence and explanation | Follow-up |
| --- | --- | --- | --- |
| FR-001 | CONFLICT | [Obligation](spec.md#L101); all 8 [assumptions](../001-disaster-response-hub/spec.md#L102) carry basis/test/owner/date, but use Proposed rather than Unvalidated and role-only signatures. | AUD-027-004, AUD-027-011 |
| FR-002 | PARTIAL | [Obligation](spec.md#L102); [ASM-001](../001-disaster-response-hub/spec.md#L104) through ASM-008 cover the eight topics, including numeric connectivity/AI floors; Asia-country sovereignty remains generic/deferred and accountable review is unverified. | AUD-027-004, AUD-027-007 |
| FR-003 | IMPLEMENTED | [Obligation](spec.md#L103); [ASM-001](../001-disaster-response-hub/spec.md#L104) explicitly states Australia, deferred Asia claims and the capstone divergence. Its validation is not claimed. | - |
| FR-004 | PARTIAL | [Obligation](spec.md#L107); [13-row NFR table](../001-disaster-response-hub/spec.md#L149) has targets/methods/surfaces, but [plan performance targets](../001-disaster-response-hub/plan.md#L20) are incompletely promoted. | AUD-027-009 |
| FR-005 | IMPLEMENTED | [Obligation](spec.md#L108); [NFR-001](../001-disaster-response-hub/spec.md#L151) names WCAG 2.2 AA and operator/public P1 surfaces with measurable audit targets. Conformance/sign-off is not established. | - |
| FR-006 | PARTIAL | [Obligation](spec.md#L109); [NFR-002](../001-disaster-response-hub/spec.md#L152) states classification, retention buckets, erasure SLA and APP-8 rules; location-specific classification/retention is not fixed, and residency exception wording needs constitutional reconciliation. | AUD-027-009, AUD-027-011 |
| FR-007 | PARTIAL | [Obligation](spec.md#L110); [NFR-003](../001-disaster-response-hub/spec.md#L153) specifies phishing-resistant MFA, token lifetimes and HSM storage, but STRIDE is not the four required named threat cases. | AUD-027-009 |
| FR-008 | PARTIAL | [Obligation](spec.md#L111); [NFR-005](../001-disaster-response-hub/spec.md#L155) preserves 60-second visibility but omits <2 s initial load and <500 ms API p95 from the plan. | AUD-027-009 |
| FR-009 | IMPLEMENTED | [Obligation](spec.md#L112); [NFR-006](../001-disaster-response-hub/spec.md#L156) names CAP 1.2, EDXL-DE 2.0 and Sendai mapping; T021's separate-row and approval obligations remain partial below. | - |
| FR-010 | PARTIAL | [Obligation](spec.md#L113); [NFR-011](../001-disaster-response-hub/spec.md#L161) requires training-pack refresh, not the onboarding target on which SC-003 depends. | AUD-027-009 |
| FR-011 | IMPLEMENTED | [Obligation](spec.md#L114); [DEF-011](../001-disaster-response-hub/spec.md#L475), [DEF-012](../001-disaster-response-hub/spec.md#L476), [DEF-013](../001-disaster-response-hub/spec.md#L477), [DEF-014](../001-disaster-response-hub/spec.md#L478) explicitly defer all four capability areas with reasons. | - |
| FR-012 | PARTIAL | [Obligation](spec.md#L115); [FR list](../001-disaster-response-hub/spec.md#L70), [NFR-007](../001-disaster-response-hub/spec.md#L157), [HYP-005](../001-disaster-response-hub/spec.md#L445) and rebuttal drafting do not provide the required misinformation-specific FR or explicit deferral. | AUD-027-014 |
| FR-013 | PARTIAL | [Obligation](spec.md#L116); [NFR-008](../001-disaster-response-hub/spec.md#L158) and [NFR-012](../001-disaster-response-hub/spec.md#L162) specify immutable logging, seven years and restore/replay targets, but not a definite record/export format. | AUD-027-009 |
| FR-014 | PARTIAL | [Obligation](spec.md#L120); all 18 [profiles](../001-disaster-response-hub/spec.md#L167) have goals/pains/tasks but lack the required per-persona device, language, proficiency and time/context detail. | AUD-027-005 |
| FR-015 | PARTIAL | [Obligation](spec.md#L121); [operational](../001-disaster-response-hub/spec.md#L171), [executive](../001-disaster-response-hub/spec.md#L271), [community](../001-disaster-response-hub/spec.md#L301), [adversarial](../001-disaster-response-hub/spec.md#L373), [accessibility](../001-disaster-response-hub/spec.md#L403) cohorts exist, but mandated archetypes are not all explicitly profiled. | AUD-027-005 |
| FR-016 | PARTIAL | [Obligation](spec.md#L122); [profile introduction](../001-disaster-response-hub/spec.md#L169) admits identities await review; generic jurisdiction scopes and scalar validators are not dated named validation records. Human validation is UNVERIFIED; no named Asia placeholder profiles appear in the target deferral register. | AUD-027-004, AUD-027-005 |
| FR-017 | PARTIAL | [Obligation](spec.md#L123); [SC-003](../001-disaster-response-hub/spec.md#L127) names all seven operational roles and first-attempt/no-facilitator completion, but the referenced validated set is unproven. | AUD-027-004, AUD-027-005 |
| FR-018 | PARTIAL | [Obligation](spec.md#L127); [six rows](../001-disaster-response-hub/spec.md#L441) make design claims but none supplies the complete mandated capability/outcome/persona/falsifier/window sentence. | AUD-027-006, AUD-027-011 |
| FR-019 | IMPLEMENTED | [Obligation](spec.md#L128); [HYP-001](../001-disaster-response-hub/spec.md#L441), [HYP-002](../001-disaster-response-hub/spec.md#L442), [HYP-003](../001-disaster-response-hub/spec.md#L443), [HYP-004](../001-disaster-response-hub/spec.md#L444), [HYP-005](../001-disaster-response-hub/spec.md#L445), [HYP-006](../001-disaster-response-hub/spec.md#L446) cover all six themes; form/settlement is assessed separately. | - |
| FR-020 | PARTIAL | [Obligation](spec.md#L129); all six existing packs are listed below, but use Proposed, omit required signatures and marker, and have incomplete transition history schema. HYP-025 has no pack after relocation search. | AUD-027-003, AUD-027-006 |
| FR-021 | IMPLEMENTED | [Obligation](spec.md#L130); [SC-004](../001-disaster-response-hub/spec.md#L128), [SC-005](../001-disaster-response-hub/spec.md#L129), [SC-006](../001-disaster-response-hub/spec.md#L130) cite HYP-001/002/003 and the [authority rule](../001-disaster-response-hub/spec.md#L571) requires reopening. | - |
| FR-022 | PARTIAL | [Obligation](spec.md#L134); [Scope declaration](../001-disaster-response-hub/spec.md#L456) identifies Australia and portability deferral, but no dated in-target rationale explains selection over Asia; single-state instructions conflict. | AUD-027-007 |
| FR-023 | PARTIAL | [Obligation](spec.md#L135); [16 deferred rows](../001-disaster-response-hub/spec.md#L463) cover 3 countries, 7 hazards and 6 capabilities, but lack evidence/target columns and required case-sensitive kinds; missing surfaces/integrations are not fully deferred. | AUD-027-007, AUD-027-013 |
| FR-024 | PARTIAL | [Obligation](spec.md#L136); [11 hazards](../001-disaster-response-hub/spec.md#L486) include all four in-scope and seven explicitly excluded hazards; reasons/triggers exist, but required evidence citations and operational-definition/AIDR-link task detail are incomplete. | AUD-027-007 |
| FR-025 | PARTIAL | [Obligation](spec.md#L137); [autonomy table](../001-disaster-response-hub/spec.md#L505) has seven rows but not the required category set or defined override windows. | AUD-027-008 |
| FR-026 | PARTIAL | [Obligation](spec.md#L138); [source tiers](../001-disaster-response-hub/spec.md#L514) name examples but omit per-platform licensing/moderation and explicit exclusion of all others. | AUD-027-013 |
| FR-027 | PARTIAL | [Obligation](spec.md#L139); [Recovery stance](../001-disaster-response-hub/spec.md#L523) and [018 ownership](../018-aidr-guidance-integration/spec.md#L342) are explicit, but the promised hand-off interface remains a generic referral. | AUD-027-013 |
| FR-028 | PARTIAL | [Obligation](spec.md#L140); [citizen list](../001-disaster-response-hub/spec.md#L529) excludes a public dashboard/portal but does not classify push app, two-way SMS and voice IVR explicitly. | AUD-027-013 |
| FR-029 | PARTIAL | [Obligation](spec.md#L141); [integration list](../001-disaster-response-hub/spec.md#L539) covers several named agencies/protocols but not the required closed boundary for CAD/EOC/GIS/SCADA/cell broadcast and all others. | AUD-027-013 |
| FR-030 | PARTIAL | [Obligation](spec.md#L142); [rehearsal subsection](../001-disaster-response-hub/spec.md#L554) governs isolation and authorship roles, not one selected shipped/imported/user-authored content boundary. | AUD-027-013 |
| FR-031 | PARTIAL | [Obligation](spec.md#L146); [canonical table](spec.md#L203) exists once with 40 rows, but resolving entries are prose, relative packs are misbased and the [target pointer](../001-disaster-response-hub/spec.md#L595) is not an anchor-bearing changelog row. | AUD-027-010 |
| FR-032 | PARTIAL | [Obligation](spec.md#L147); [three deltas](../001-disaster-response-hub/spec.md#L583) omit known safety/NFR contradictions, owners/deadlines and valid plan blocking; the actual planning entry point is unguarded. | AUD-027-002, AUD-027-011 |
| FR-033 | PARTIAL | [Obligation](spec.md#L148); [changelog](../001-disaster-response-hub/spec.md#L589) has a dated 027 summary but no required Last-reviewed line or attributable transition signatures. | AUD-027-001, AUD-027-004, AUD-027-010 |
| FR-034 | PARTIAL | [Obligation](spec.md#L149); [authority rule](../001-disaster-response-hub/spec.md#L564) and [CODEOWNERS](../../.github/CODEOWNERS#L16) exist, but the exact role matrix/signature effectiveness is not implemented and external ownership enforcement is unverified. | AUD-027-004, AUD-027-011 |
| FR-035 | PARTIAL | [Obligation](spec.md#L150); all [13 NFR rows](../001-disaster-response-hub/spec.md#L151) contain role/basis cells, not named planner/SME/privacy approval; [OD-003](../001-disaster-response-hub/spec.md#L585) is not a governed provisional-NFR blocker. | AUD-027-004, AUD-027-009 |
| FR-036 | PARTIAL | [Obligation](spec.md#L151); [40-row register](../shared/gap-id-register.md#L19) covers all literal cited gap IDs and is currently contiguous, but allocation dates/withdrawal-reason fields and historical append-only enforcement are missing. | AUD-027-003, AUD-027-010 |
| SC-001 | UNVERIFIED | [Criterion](spec.md#L184); no named independent reviewer read-through or four-question score record was found in the complete local inputs; [generic checklist](checklists/requirements.md#L27) is not that evidence. | AUD-027-001 |
| SC-002 | PARTIAL | [Criterion](spec.md#L185); all 40 [gap rows](spec.md#L207) are mapped, but some mappings are incomplete/non-navigable and every state disagrees with the register. | AUD-027-010 |
| SC-003 | IMPLEMENTED | [Criterion](spec.md#L186); all 13 [NFR rows](../001-disaster-response-hub/spec.md#L151) contain a target, measurement method and a described surface. Missing mandated content/authority is separately captured under FR-004/035. | - |
| SC-004 | PARTIAL | [Criterion](spec.md#L187); [18 profiles](../001-disaster-response-hub/spec.md#L167) do not provide all required per-persona fields; the validated-for-v1 population itself is unverified, not an empty-set pass. | AUD-027-004, AUD-027-005 |
| SC-005 | PARTIAL | [Criterion](spec.md#L188); all [six rows](../001-disaster-response-hub/spec.md#L441) carry a status, but it is outside both allowed enums and the required form is incomplete. | AUD-027-006, AUD-027-011 |
| SC-006 | IMPLEMENTED | [Criterion](spec.md#L189); exhaustive review of [HYP-001 through HYP-006](../001-disaster-response-hub/spec.md#L441) confirms all six themes, without claiming experiments succeeded. | - |
| SC-007 | PARTIAL | [Criterion](spec.md#L190); the [autonomy table](../001-disaster-response-hub/spec.md#L505) does not enumerate/classify the full required seven-category set. | AUD-027-008 |
| SC-008 | PARTIAL | [Criterion](spec.md#L191); every named downstream file was read, and [approval enum](../001-disaster-response-hub/contracts/openapi.yaml#L515), [quickstart exception](../001-disaster-response-hub/quickstart.md#L59), performance and contract conflicts are not governed in Open Deltas. | AUD-027-002, AUD-027-011 |
| SC-009 | UNVERIFIED | [Criterion](spec.md#L192); no attributable privacy-reviewer DPIA outline and test-lead matrix derived without blocking clarifications were found; generic role descriptions and [checkmarks](checklists/requirements.md#L29) do not establish the outcome. | AUD-027-001 |
| SC-010 | IMPLEMENTED | [Criterion](spec.md#L193); read-only word-boundary inspection finds [Australia](../001-disaster-response-hub/spec.md#L456) within the first 200 Scope words. This narrow check does not establish the missing rationale or reviewer outcome. | - |

## Acceptance Scenarios and Edge Cases

Each scenario has its own row. Review status concerns the required artifact/outcome, not a fabricated execution.

| Scenario | Status | Inspected evidence and explanation | Follow-up |
| --- | --- | --- | --- |
| US1-AS1 | PARTIAL | [Scenario](spec.md#L49); Australia and country deferrals exist in [Scope](../001-disaster-response-hub/spec.md#L454), but the dated in-target rationale and complete promotion/evidence register are absent. | AUD-027-007 |
| US1-AS2 | IMPLEMENTED | [Scenario](spec.md#L50); all seven [target SCs](../001-disaster-response-hub/spec.md#L125) explicitly use the v1 Australian cohort and retain the 50%, 24-hour and 30% targets. | - |
| US1-AS3 | PARTIAL | [Scenario](spec.md#L51); [portability text](../001-disaster-response-hub/spec.md#L459) rejects the guarantee and names HYP-006, but its [falsifier](../001-disaster-response-hub/spec.md#L446) lacks a bounded test envelope/window. | AUD-027-006 |
| US2-AS1 | IMPLEMENTED | [Scenario](spec.md#L65); all [13 NFR rows](../001-disaster-response-hub/spec.md#L151) state targets, methods and surfaces. This is structural presence only; missing specific NFR obligations remain findings. | - |
| US2-AS2 | PARTIAL | [Scenario](spec.md#L66); [privacy NFR](../001-disaster-response-hub/spec.md#L152) has retention/erasure/APP-8 rules but location treatment and constitutional residency compatibility remain incomplete. | AUD-027-009, AUD-027-011 |
| US2-AS3 | PARTIAL | [Scenario](spec.md#L67); all [profiles](../001-disaster-response-hub/spec.md#L167) were reviewed; device/language/context fields are not supplied per profile and validation is unproven. | AUD-027-004, AUD-027-005 |
| US2-AS4 | PARTIAL | [Scenario](spec.md#L68); [Scope subsections](../001-disaster-response-hub/spec.md#L450) exist but action/source/surface/integration sets and handoff/content-origin boundaries are incomplete. | AUD-027-007, AUD-027-008, AUD-027-013 |
| US3-AS1 | PARTIAL | [Scenario](spec.md#L82); [six hypothesis statements](../001-disaster-response-hub/spec.md#L441) do not follow the required form; HYP-005/HYP-006 are not quantitatively bounded. | AUD-027-006 |
| US3-AS2 | UNVERIFIED | [Scenario](spec.md#L83); all six [packs](../001-disaster-response-hub/evidence/HYP-001.md#L1) are stubs with matching but invalid Proposed status. No actual rehearsal/status-transition evidence establishes the conditional outcome. | AUD-027-006 |
| EC-01 | PARTIAL | [Downstream-conflict edge](spec.md#L87); [known approval exception](../001-disaster-response-hub/quickstart.md#L59) is not reconciled or recorded among the three deltas. | AUD-027-011 |
| EC-02 | PARTIAL | [Jurisdiction-dispute edge](spec.md#L88); [portability warning](../001-disaster-response-hub/spec.md#L459) rejects annex authority, but target Scope has no dated rationale/change record for the jurisdiction dispute rule. | AUD-027-007 |
| EC-03 | IMPLEMENTED | [Invalidation edge](spec.md#L89); [explicit rule](../001-disaster-response-hub/spec.md#L570) requires reopening the dependent decision and linked SCs in the same PR; no actual invalidation is claimed. | - |
| EC-04 | PARTIAL | [Persona-conflict edge](spec.md#L90); [target SC-003](../001-disaster-response-hub/spec.md#L127) names roles, but profile authority, missing archetypes and contract enums remain unreconciled. | AUD-027-005, AUD-027-011 |
| EC-05 | IMPLEMENTED | [Asia-asset edge](spec.md#L91); [Scope](../001-disaster-response-hub/spec.md#L459) and [later deferral](../001-disaster-response-hub/spec.md#L609) prevent assets from implying v1 promotion. Referenced missing assets are a provenance defect, not evidence of expanded scope. | - |

## Appended Amendments

The later six items are reviewed as part of 027. They do not authorize auditing or repairing the rest of the portfolio.

| Amendment | Status | Inspected evidence and explanation | Follow-up |
| --- | --- | --- | --- |
| ASM-082 | CONFLICT | [Amendment](spec.md#L261) declares 027 contracts authoritative; [028 D-002](../028-capstone-alignment/research.md#L23) claims reuse, but original contract/spec enums and proxy rules already disagree. | AUD-027-011 |
| ASM-083 | IMPLEMENTED | [Amendment](spec.md#L262) explicitly limits 027 to 001 and assigns propagation to 028, consistent with the [scope note](spec.md#L18). | - |
| PER-073 | UNVERIFIED | [Amendment](spec.md#L268) points to the target's supposed validated set, but [profiles](../001-disaster-response-hub/spec.md#L169) only promise later identity capture and do not expose the claimed PER-001 identifiers. | AUD-027-004, AUD-027-005 |
| HYP-025 | MISSING | [Amendment](spec.md#L272) promises a pack at 028/evidence/HYP-025; no such file or renamed evidence body was found in tracked specs. Status/window and an adequate uplift falsifier are also absent; rubric snapshots do not substitute for this pack. | AUD-027-006 |
| SCP-082 | IMPLEMENTED | [Amendment](spec.md#L278) explicitly labels 027 as enabling/non-critical-path; this is an ownership declaration, not proof of portfolio outcomes. | - |
| SCP-083 | IMPLEMENTED | [Amendment](spec.md#L279) assigns cross-spec propagation to 028; [028 FR-019](../028-capstone-alignment/spec.md#L148) provides the replacement context. | - |

The bounded cohort inventory for the rubric claim covered exactly 27 current files: 001-disaster-response-hub
and numbered 003 through 028. All 27 have the four H2 headers. This proves header presence only, not their
content quality, historical scores or faithful contract reuse. No fresh rubric grading was performed and no
scores from other specifications are accepted as attributable human approval.

## Original Task Coverage

Each original ID and original checkbox is preserved verbatim. All 56 source tasks were checked; that state
is not the review status. No original task is collapsed into a range. Actor participation and test/approval
execution remain unverified unless separately evidenced, even where the authored artifact is IMPLEMENTED.

| Task | Original state | Status | Inspected evidence and explanation | Follow-up |
| --- | --- | --- | --- | --- |
| T001 | [x] | IMPLEMENTED | [Shared register](../shared/gap-id-register.md#L1), [evidence directory contents](../001-disaster-response-hub/evidence/HYP-001.md#L1) and [GitHub configuration](../../.github/CODEOWNERS#L1) establish the required scaffolding exists. | - |
| T002 | [x] | PARTIAL | [Lint config](../../.markdownlint.jsonc#L8) disables rules globally; no declared hardening lint dependency/job establishes the required scope. | AUD-027-012 |
| T003 | [x] | SUPERSEDED | [T046](tasks.md#L316) explicitly replaces the stub; [StubMode=false](../../scripts/verify-spec-hardening.ps1#L23) selects the current verifier. Do not restore the obsolete always-success stub. | - |
| T004 | [x] | IMPLEMENTED | [Register](../shared/gap-id-register.md#L19) has the contract's eight columns and all 40 original Open rows owned by 001; exhaustive current-ID inventory passes. Later closure requirements are separate. | - |
| T005 | [x] | PARTIAL | [Team entries](../../.github/CODEOWNERS#L16) exist, but the [interim owner](../../.github/CODEOWNERS#L25) is commented and [OD-002](../001-disaster-response-hub/spec.md#L584) is not plan-blocking; team existence/size is unverified. | AUD-027-004, AUD-027-011 |
| T006 | [x] | PARTIAL | [Authority section](../001-disaster-response-hub/spec.md#L564) lacks the exact artifact-specific role matrix and effective two-signature record. | AUD-027-004 |
| T007 | [x] | PARTIAL | [Changelog](../001-disaster-response-hub/spec.md#L589) has a dated summary, but no Last-reviewed line or linked anchor-bearing pointer row. | AUD-027-001, AUD-027-010 |
| T008 | [x] | IMPLEMENTED | [Open Deltas header](../001-disaster-response-hub/spec.md#L581) matches the seven-column [contract](contracts/open-delta-row.md#L5); later row values/governance are separately deficient. | - |
| T009 | [x] | PARTIAL | [Authored sections](../001-disaster-response-hub/spec.md#L98) exist, but heading levels, deferred/scope column schemas and profile shapes do not uniformly match the promised templates. | AUD-027-005, AUD-027-007, AUD-027-011 |
| T010 | [x] | CONFLICT | [Task requires one state](tasks.md#L93); [Scope](../001-disaster-response-hub/spec.md#L456) covers Commonwealth/all tiers and lacks the dated rationale/citations. | AUD-027-007, AUD-027-011 |
| T011 | [x] | PARTIAL | [3 country and 7 hazard rows](../001-disaster-response-hub/spec.md#L465) exist, but target_feature/evidence fields and valid kind casing are absent; six annex asset targets are missing after relocation search. | AUD-027-007 |
| T012 | [x] | PARTIAL | [ASM-001](../001-disaster-response-hub/spec.md#L104) states the decision, but signatures are role-only and [A-GAP-003](../shared/gap-id-register.md#L23) remains Open without evidence. | AUD-027-004, AUD-027-010 |
| T013 | [x] | PARTIAL | [Portability disclaimer](../001-disaster-response-hub/spec.md#L459) names HYP-006, but [OD-001](../001-disaster-response-hub/spec.md#L583) and [pack exemption](../001-disaster-response-hub/evidence/HYP-006.md#L33) contradict the same-commit/no-exemption instructions. | AUD-027-006, AUD-027-011 |
| T013b | [x] | PARTIAL | [HYP-006 row](../001-disaster-response-hub/spec.md#L446) and [pack](../001-disaster-response-hub/evidence/HYP-006.md#L1) were authored with spec 001 in the original feature commit, but state/form/history do not satisfy the specified contract; gate execution is unverified. | AUD-027-006 |
| T014 | [x] | IMPLEMENTED | All seven [target SCs](../001-disaster-response-hub/spec.md#L125) explicitly scope numeric outcomes to the Australian v1 cohort. | - |
| T015 | [x] | PARTIAL | [Canonical mappings](spec.md#L209) exist, but all corresponding [register states](../shared/gap-id-register.md#L21) remain Open and unlinked. | AUD-027-010 |
| T016 | [x] | PARTIAL | [ASM-002 through ASM-008](../001-disaster-response-hub/spec.md#L105) cover the seven topics, but named accountable review and required gap-closure updates are absent. | AUD-027-004, AUD-027-010 |
| T017 | [x] | PARTIAL | [NFR-001](../001-disaster-response-hub/spec.md#L151) has WCAG 2.2 AA, numeric targets and observable audit methods, but required named drafting/countersign evidence is unverified. | AUD-027-004 |
| T018 | [x] | PARTIAL | [Privacy rows](../001-disaster-response-hub/spec.md#L152) cover broad retention/erasure/APP-8 but not explicit location handling or named privacy approval. | AUD-027-004, AUD-027-009 |
| T019 | [x] | PARTIAL | [NFR-003](../001-disaster-response-hub/spec.md#L153) specifies MFA/session/key commitments but not the four named threats or actual signatures. | AUD-027-004, AUD-027-009 |
| T020 | [x] | PARTIAL | [NFR-005](../001-disaster-response-hub/spec.md#L155) omits two [plan targets](../001-disaster-response-hub/plan.md#L20); plan has no required adjacent NFR-source pointer comments. | AUD-027-009 |
| T021 | [x] | PARTIAL | [NFR-006](../001-disaster-response-hub/spec.md#L156) names all three standards in one row, not the required three; actual contract conformance/approvals remain unverified. | AUD-027-004, AUD-027-009 |
| T022 | [x] | PARTIAL | [NFR-011](../001-disaster-response-hub/spec.md#L161) sets release-training refresh, not a numeric onboarding target or rehearsal basis. | AUD-027-009 |
| T023 | [x] | PARTIAL | [Audit targets](../001-disaster-response-hub/spec.md#L162) state seven years and one-hour restore, but a defined record/export format and named countersigns are absent. | AUD-027-004, AUD-027-009 |
| T024 | [x] | IMPLEMENTED | [DEF-011](../001-disaster-response-hub/spec.md#L475), [DEF-012](../001-disaster-response-hub/spec.md#L476), [DEF-013](../001-disaster-response-hub/spec.md#L477), [DEF-014](../001-disaster-response-hub/spec.md#L478) provide the four permitted reasoned v1 exclusions. Actor participation is not established. | - |
| T025 | [x] | PARTIAL | [Target FRs](../001-disaster-response-hub/spec.md#L70) have no misinformation-specific detection/evidence obligation or explicit deferral; [HYP-005](../001-disaster-response-hub/spec.md#L445) is not an FR. | AUD-027-014 |
| T026 | [x] | PARTIAL | [Seven operational profiles](../001-disaster-response-hub/spec.md#L171) exist but enum values, complete fields and named jurisdiction validators do not satisfy the contract. | AUD-027-004, AUD-027-005 |
| T027 | [x] | PARTIAL | [Two executive profiles](../001-disaster-response-hub/spec.md#L271) have neither Non-AIIMS-Governance enum values nor named SME validators. | AUD-027-004, AUD-027-005 |
| T028 | [x] | PARTIAL | [Five community profiles](../001-disaster-response-hub/spec.md#L301) are not complete distinct coverage of native-language, low-literacy, low-vision and hard-of-hearing archetypes. | AUD-027-005 |
| T029 | [x] | PARTIAL | [Two adversaries](../001-disaster-response-hub/spec.md#L373) exist, but do not link a mitigating FR or conform to the persona contract. | AUD-027-005, AUD-027-014 |
| T030 | [x] | PARTIAL | [Screen-reader and voice/switch profiles](../001-disaster-response-hub/spec.md#L403) do not explicitly provide the required hard-of-hearing field worker. | AUD-027-005 |
| T031 | [x] | PARTIAL | [SC-003](../001-disaster-response-hub/spec.md#L127) names all seven roles and unassisted completion, but calls an unverified cohort validated. | AUD-027-004, AUD-027-005 |
| T032 | [x] | PARTIAL | [11 hazards](../001-disaster-response-hub/spec.md#L486) provide the right 4+7 split, but lack the promised operational definitions/AIDR URLs and complete deferred evidence. | AUD-027-007 |
| T033 | [x] | PARTIAL | [Seven autonomy rows](../001-disaster-response-hub/spec.md#L505) do not cover the seven required categories or bounded override windows. | AUD-027-008 |
| T034 | [x] | PARTIAL | [Community sources](../001-disaster-response-hub/spec.md#L514) name platforms/tiers, not licensing instruments, moderation duties and exclusions. | AUD-027-013 |
| T035 | [x] | PARTIAL | [Recovery statement](../001-disaster-response-hub/spec.md#L523) is explicit and later [018 authority](../018-aidr-guidance-integration/spec.md#L342) is recognized, but referral is not a handoff contract. | AUD-027-013 |
| T036 | [x] | PARTIAL | [Citizen table](../001-disaster-response-hub/spec.md#L529) has different rows from the required public-dashboard/push/SMS/IVR set. | AUD-027-013 |
| T037 | [x] | PARTIAL | [Integration table](../001-disaster-response-hub/spec.md#L539) has protocols/directions but lacks all named boundary decisions and owning-agent handles. | AUD-027-013 |
| T038 | [x] | PARTIAL | [Rehearsal rules](../001-disaster-response-hub/spec.md#L554) never select one content-origin boundary. | AUD-027-013 |
| T039 | [x] | PARTIAL | [Canonical rows](spec.md#L217) claim closure, while all [register rows](../shared/gap-id-register.md#L29) remain Open. | AUD-027-010 |
| T040 | [x] | PARTIAL | [HYP-001](../001-disaster-response-hub/spec.md#L441) and [HYP-002](../001-disaster-response-hub/spec.md#L442) exist with falsifiers but do not use the required form/state or concrete linked FR/NFR fields. | AUD-027-006 |
| T041 | [x] | PARTIAL | [HYP-003](../001-disaster-response-hub/spec.md#L443) and [HYP-004](../001-disaster-response-hub/spec.md#L444) exist; HYP-004's linked-decision cell is free product prose rather than the required performance NFR link. | AUD-027-006 |
| T042 | [x] | PARTIAL | [HYP-005](../001-disaster-response-hub/spec.md#L445) is unique and HYP-006 is not duplicated; agreed tolerance remains unspecified and form/state fail. | AUD-027-006 |
| T043 | [x] | PARTIAL | Five [original stubs](../001-disaster-response-hub/evidence/HYP-001.md#L1) plus HYP-006 exist, each with one authored history row, but status is Proposed and required history/signature/marker fields are missing. | AUD-027-006 |
| T044 | [x] | IMPLEMENTED | [SC-004](../001-disaster-response-hub/spec.md#L128), [SC-005](../001-disaster-response-hub/spec.md#L129), [SC-006](../001-disaster-response-hub/spec.md#L130) explicitly cite the respective hypotheses and reopening rule. | - |
| T045 | [x] | PARTIAL | [Six HYP-GAP mappings](spec.md#L234) contain pack text, but paths are not correct links and [register states](../shared/gap-id-register.md#L46) are Open. | AUD-027-010 |
| T046 | [x] | PARTIAL | [Verifier](../../scripts/verify-spec-hardening.ps1#L58) implements only subsets of five advertised invariants; no hardening negative-assertion callers were found in tracked tooling/tests. It was not executed. | AUD-027-003 |
| T047 | [x] | PARTIAL | [Safety enum](../001-disaster-response-hub/contracts/openapi.yaml#L515), [quickstart exception](../001-disaster-response-hub/quickstart.md#L59), NFR/contract drift and invalid delta governance survive the claimed sweep. | AUD-027-011 |
| T048 | [x] | PARTIAL | [Canonical table](spec.md#L207) has exactly 40 rows, but every state conflicts with the register and links/delta references are incomplete. | AUD-027-010 |
| T049 | [x] | UNVERIFIED | [Task](tasks.md#L331) claims execution; no revision-bound lint result was found, and [global disables](../../.markdownlint.jsonc#L8) contradict its quality constraint. | AUD-027-001, AUD-027-012 |
| T050 | [x] | UNVERIFIED | [Task](tasks.md#L336) claims relative-link validation; no attributable result was found. The canonical mappings/pointer are not usable links and annex asset targets are absent. | AUD-027-001, AUD-027-007, AUD-027-010, AUD-027-012 |
| T051 | [x] | UNVERIFIED | [Walkthrough](quickstart.md#L16) has no recorded independent outcome; several demanded states/proxy/owner checks conflict with the actual artifacts. | AUD-027-001, AUD-027-011 |
| T052 | [x] | CONFLICT | [Checked task](tasks.md#L346) requires sealing; [plan status](plan.md#L163) still says tasks not started, and the target changelog lacks a Last-reviewed line. | AUD-027-001 |
| T053 | [x] | UNVERIFIED | [Task](tasks.md#L351) requires PR, CODEOWNERS review, 40-gap description and green CI; local commit metadata and [manual workflow](../../.github/workflows/spec-035-gate.yml#L3) do not establish these outcomes. | AUD-027-001, AUD-027-004, AUD-027-012 |
| T054 | [x] | PARTIAL | [16 generic checkboxes](checklists/requirements.md#L8) fall short of the 36 FR + 10 SC + 3 current delta items required by [T054](tasks.md#L356). | AUD-027-001 |
| T055 | [x] | MISSING | [Planner](../../.github/agents/speckit.plan.agent.md#L23), [setup](../../.specify/scripts/powershell/setup-plan.ps1#L24), [prerequisites](../../.specify/scripts/powershell/check-prerequisites.ps1#L17) and both planning prompts have no claimed guard; tracked caller search finds only manual CI. | AUD-027-002 |

## Complete Target-Artifact Assessment

### NFR Content and Authority

Every row was read, not sampled. Authority is UNVERIFIED for all 13: none supplies the required actual planner,
SME and (where applicable) privacy-reviewer names. Presence of role labels is not an approved numeric basis.

| Artifact | Content status | Evidence and remaining boundary | Follow-up |
| --- | --- | --- | --- |
| 001:NFR-001 | IMPLEMENTED | [Accessibility](../001-disaster-response-hub/spec.md#L151): WCAG 2.2 AA, all operator/public P1 flows, automated/manual audit and keyboard completion targets. Actual conformance unverified. | AUD-027-004 |
| 001:NFR-002 | PARTIAL | [Privacy](../001-disaster-response-hub/spec.md#L152): buckets/erasure stated, location treatment not explicit; APP-8 exception needs constitutional limits. | AUD-027-004, AUD-027-009, AUD-027-011 |
| 001:NFR-003 | PARTIAL | [Security](../001-disaster-response-hub/spec.md#L153): MFA/token/HSM commitments, but four required threat cases omitted. | AUD-027-004, AUD-027-009 |
| 001:NFR-004 | IMPLEMENTED | [Reliability](../001-disaster-response-hub/spec.md#L154): availability, RTO/RPO and rollback targets with SLO/drill methods, not observed results. | AUD-027-004 |
| 001:NFR-005 | PARTIAL | [Performance](../001-disaster-response-hub/spec.md#L155): online/degraded refresh and ingest targets; missing promoted initial-load/API targets. | AUD-027-004, AUD-027-009 |
| 001:NFR-006 | IMPLEMENTED | [Interoperability](../001-disaster-response-hub/spec.md#L156): CAP/EDXL/Sendai named; combined-row/task-shape conflict and real conformance evidence remain. | AUD-027-004, AUD-027-009 |
| 001:NFR-007 | IMPLEMENTED | [Provenance privacy](../001-disaster-response-hub/spec.md#L157): tier labels and visibility on every surface; not a misinformation detection FR. | AUD-027-004, AUD-027-014 |
| 001:NFR-008 | PARTIAL | [Observability](../001-disaster-response-hub/spec.md#L158): one-second logging, append-only storage and five-minute replay target; definite audit format missing. | AUD-027-004, AUD-027-009 |
| 001:NFR-009 | CONFLICT | [Residency](../001-disaster-response-hub/spec.md#L159): APP-8 exception for primary/replica/backup copies is broader than the constitution's model-endpoint-only carve-out. No out-of-AU persistence is inferred to have occurred. | AUD-027-004, AUD-027-011 |
| 001:NFR-010 | IMPLEMENTED | [Cost](../001-disaster-response-hub/spec.md#L160): 20% variance target and unit-cost measurement method exist; approved envelope/basis is unverified. | AUD-027-004 |
| 001:NFR-011 | PARTIAL | [Training](../001-disaster-response-hub/spec.md#L161): release-pack freshness target, not initial onboarding competency/time target. | AUD-027-004, AUD-027-009 |
| 001:NFR-012 | PARTIAL | [Audit retention](../001-disaster-response-hub/spec.md#L162): seven-year minimum and annual one-hour restore target; format and actual legal/SME approval unproven. | AUD-027-004, AUD-027-009 |
| 001:NFR-013 | IMPLEMENTED | [Language accessibility](../001-disaster-response-hub/spec.md#L163): Australian English plus Simplified Chinese, locale audit and native-speaker review requirement. Execution unverified. | AUD-027-004 |

### Persona Inventory

All 18 profiles lack complete per-profile device/language/proficiency/time fields and named dated validation;
all are PARTIAL with follow-up AUD-027-005 and authority follow-up AUD-027-004. There is no Intelligence profile.
The table below records individual additional evidence so cohort counts cannot hide substitutions.

| Persona | Status | Inspected profile and specific issue |
| --- | --- | --- |
| P-OPS-IC | PARTIAL | [Incident Controller](../001-disaster-response-hub/spec.md#L174): Control is valid; statutory authority lacks explicit countersign boundary and validator identity/date. |
| P-OPS-OPS | PARTIAL | [Operations Officer](../001-disaster-response-hub/spec.md#L188): Operations is valid; scenario tokens are not links and practitioner provenance is generic. |
| P-OPS-LOG | PARTIAL | [Logistics Officer](../001-disaster-response-hub/spec.md#L202): Logistics is valid; empty accessibility list and generic SME description do not provide a complete study profile. |
| P-OPS-PIO | PARTIAL | [PIO](../001-disaster-response-hub/spec.md#L216): Public Information is valid; multilingual tasks have no per-profile language/device specification. |
| P-OPS-FIELD | PARTIAL | [Field Coordinator](../001-disaster-response-hub/spec.md#L230): Operations (field) is outside the enum; generic accessibility mentions do not supply the hearing-specific archetype. |
| P-OPS-PLAN | PARTIAL | [Resilience Planner](../001-disaster-response-hub/spec.md#L244): Planning is valid; scenario authorship is not the missing rehearsal-origin contract. |
| P-OPS-AUDIT | PARTIAL | [Observer/Auditor](../001-disaster-response-hub/spec.md#L258): Governance (cross-cut) is outside the enum; read-only authority and internal panel label lack required detail. |
| P-EXEC-MIN | PARTIAL | [Minister/Premier](../001-disaster-response-hub/spec.md#L274): Strategic oversight is not Non-AIIMS-Governance; no named executive SME. |
| P-EXEC-MAYOR | PARTIAL | [Mayor](../001-disaster-response-hub/spec.md#L288): Local strategic liaison is outside the enum; Recovery referral is not an interface definition. |
| P-COM-CALD-HH | PARTIAL | [CALD household](../001-disaster-response-hub/spec.md#L304): Recipient of public information is outside the enum; low-literacy mention is not a separately complete mandated profile. |
| P-COM-REMOTE | PARTIAL | [Remote resident](../001-disaster-response-hub/spec.md#L318): invalid function enum; SMS/radio fallback mentions leave citizen-surface scope unresolved. |
| P-COM-FIRSTNATIONS | PARTIAL | [First Nations liaison](../001-disaster-response-hub/spec.md#L332): Cultural liaison is outside the enum; this useful addition does not replace a required native-language/low-literacy profile. |
| P-COM-DISAB | PARTIAL | [Disability/carer](../001-disaster-response-hub/spec.md#L346): broad screen-reader/caption needs do not differentiate low-vision and hard-of-hearing residents; invalid function enum. |
| P-COM-TOURIST | PARTIAL | [Tourist](../001-disaster-response-hub/spec.md#L360): required archetype exists; function enum and full profile/provenance remain incomplete. |
| P-ADV-MISINFO | PARTIAL | [Misinformation actor](../001-disaster-response-hub/spec.md#L376): Threat model is outside enum; no mitigating FR link or accountable validation. |
| P-ADV-INSIDER | PARTIAL | [Insider](../001-disaster-response-hub/spec.md#L390): same enum/provenance gaps and no explicit mitigating FR link. |
| P-ACC-SCREEN | PARTIAL | [Screen-reader operator](../001-disaster-response-hub/spec.md#L406): useful AT details but Operational (any function) is outside enum; not an explicitly validated low-vision profile. |
| P-ACC-VOICE | PARTIAL | [Voice/switch operator](../001-disaster-response-hub/spec.md#L420): motor-access profile does not satisfy hard-of-hearing field worker; invalid function enum. |

### Original Hypothesis Packs

All six rows and packs were inspected in full. All six pack statuses match the row as Proposed, but that state is
invalid under both published contracts. Each has one authored history row; none has the required frontmatter
owning_feature/drafter/countersigner, complete transition-history columns, or exact no-observations marker.
Populated prose instructions and supplementary negative criteria are not observations.

| Artifact | Status | Inspected evidence and remaining issue | Follow-up |
| --- | --- | --- | --- |
| 001:HYP-001 | PARTIAL | [Pack](../001-disaster-response-hub/evidence/HYP-001.md#L1): two-cycle safety/response criteria and method exist; required statement persona/form and valid untested lifecycle absent. | AUD-027-006 |
| 001:HYP-002 | PARTIAL | [Pack](../001-disaster-response-hub/evidence/HYP-002.md#L1): earlier evacuation/baseline criteria exist; template/state/authority remain incomplete. | AUD-027-006 |
| 001:HYP-003 | PARTIAL | [Pack](../001-disaster-response-hub/evidence/HYP-003.md#L1): comparative orchestration method and two-cycle window exist; structured linked FR/NFR and mandated form missing. | AUD-027-006 |
| 001:HYP-004 | PARTIAL | [Pack](../001-disaster-response-hub/evidence/HYP-004.md#L1): 64-kbps/10-second criteria exist; row lacks the required NFR-linked decision/form, and no degraded-connectivity result is recorded. | AUD-027-006 |
| 001:HYP-005 | PARTIAL | [Pack](../001-disaster-response-hub/evidence/HYP-005.md#L1): describes an injection experiment but leaves agreed tolerance/latency unspecified. | AUD-027-006, AUD-027-014 |
| 001:HYP-006 | PARTIAL | [Pack](../001-disaster-response-hub/evidence/HYP-006.md#L1): expert-review protocol is authored; no bounded envelope/window, and the Open Delta exemption conflicts with creation-time evidence requirements. | AUD-027-006, AUD-027-011 |

### Gap and Scope Inventories

| Gap family | Count | Register status | Canonical status | Static assessment |
| --- | --- | --- | --- | --- |
| A-GAP | 8 | All Open | All Resolved | All cited IDs registered; all 8 states disagree. |
| REQ-GAP | 10 | All Open | All Resolved | All cited IDs registered; all 10 states disagree. |
| PER-GAP | 7 | All Open | All Resolved | All cited IDs registered; all 7 states disagree. |
| HYP-GAP | 6 | All Open | All Resolved | All cited IDs registered; all 6 states disagree and pack text is misbased. |
| SCP-GAP | 9 | All Open | All Resolved | All cited IDs registered; all 9 states disagree. |

The exhaustive gap-reference scan read 544 tracked Markdown/YAML/JSON specification artifacts, excluding
implementation-review reports. It found no unregistered literal numeric gap IDs. Template placeholders and
non-gap ASM/HYP/PER/SCP reservation families are not mistaken for missing gap allocations.
Every current category is contiguous from 001. This is not proof of historical no-delete/no-reuse behavior.

| Required autonomy category | Status | Actual representation |
| --- | --- | --- |
| Public alert publication | IMPLEMENTED | CAP dispatch requires a human approver in the target table; downstream compatibility is separately unresolved. |
| Evacuation routing | PARTIAL | Human-only evacuation order is not an explicit routing classification. |
| Resource pre-positioning | PARTIAL | Cross-border request and internal assignment do not define pre-positioning. |
| SMS/voice alert drafting | PARTIAL | Misinformation rebuttal drafting does not classify channel-specific alert drafts. |
| New-signal recommendation reprioritisation | CONFLICT | Decide is labeled advisory with no explicit override window or distinction between advisory sorting and execution. |
| Field-task assignment | PARTIAL | Internal resource assignment is only partial coverage and has no timed veto window. |
| De-escalation/closure | PARTIAL | No row classifies this category despite all-clear handling appearing in the representative service. |

The hazard inventory is complete by named set: bushfire, flood, tropical cyclone and severe storm are in scope;
earthquake, tsunami, extreme heat, pandemic/biosecurity, CBRN, space weather and cyber-physical hazards are
explicitly deferred. Deferral quality/links remain partial. The three Asia jurisdictions and four capability
deferrals are present; all 16 deferred rows lack the promised target/evidence schema. No country seed/template
is treated as deployed or as proof of data licensing.

## Contract Conflicts and Explicit Supersession

Later dates or checkmarks are not supersession. The following decisions preserve supported existing work while
identifying where one documented rule cannot safely be inferred to override another.

| Item | Status | Repository evidence and treatment |
| --- | --- | --- |
| Original stub stage | SUPERSEDED | [T046](tasks.md#L316) expressly expands T003; [current verifier](../../scripts/verify-spec-hardening.ps1#L23) disables stub mode. Restoring the stub is not remediation. |
| Cross-spec propagation owner | SUPERSEDED | [027 scope note](spec.md#L18) assigns propagation to 028-capstone-alignment; [028 Out of Scope](../028-capstone-alignment/spec.md#L217) explicitly rejects creating the phantom holistic-hardening directory. Residual CODEOWNERS/contract examples must be reconciled. |
| Recovery indicators owner | SUPERSEDED | [028 D-005](../028-capstone-alignment/research.md#L47), [001 DEF-015](../001-disaster-response-hub/spec.md#L479) and [018 reciprocal declaration](../018-aidr-guidance-integration/spec.md#L342) explicitly assign indicators/triggers/phase exits to 018. This does not implement the missing 001 referral contract. |
| Blanket inference-region prohibition | SUPERSEDED | [Constitution v1.2 carve-out](../../.specify/memory/constitution.md#L245) permits named non-AU model endpoints only, preserving the [ban on regulated-data persistence](../../.specify/memory/constitution.md#L260). No other data-store exception may be inferred. |
| Assumption lifecycle | CONFLICT | [FR-001](spec.md#L101) says Unvalidated/Validated/Invalidated; [contract](contracts/assumption-row.md#L23) says Proposed/Validated/Invalidated/Withdrawn. No explicit lifecycle amendment reconciles them. |
| Hypothesis form and lifecycle | CONFLICT | [FR-018/020](spec.md#L127) require We-believe form and Not tested/Supported/Invalidated/Inconclusive; [contract](contracts/hypothesis-row.md#L9) uses If-then and Under validation/Validated/Withdrawn; actual rows/packs use Proposed, allowed by neither. |
| Named proxy eligibility | CONFLICT | [FR-016](spec.md#L122) and [T026](tasks.md#L194) permit documented named proxies, while the [persona contract](contracts/persona-profile.md#L33), E-4 and Quickstart reject proxy-only review. Do not silently disqualify an otherwise eligible named proxy. |
| Authority and interim owners | CONFLICT | [FR-034](spec.md#L149) specifies artifact-specific proposer/countersign pairs; [research R-3](research.md#L50) substitutes CODEOWNERS team signatures, actual text uses generic maintainer/SME, and [T005](tasks.md#L56) permits an interim individual while its contract forbids one. |
| Open Delta schema and ordering | CONFLICT | [FR-032](spec.md#L147) requires owner/feature/firm plan deadline; [contract](contracts/open-delta-row.md#L5) lacks owner/deadline fields, uses DELTA IDs, and allows other phases. Actual rows use OD IDs and none phases; the verifier only parses OD and existing plans. |
| Reference jurisdiction granularity | CONFLICT | [T010](tasks.md#L93) and [R-9](research.md#L127) demand one Australian state/territory; [target Scope](../001-disaster-response-hub/spec.md#L456) is country-wide. R-9's NSW-capstone scenario basis is not present in the inspected [brief](../../capstone.md#L38). |
| Evidence-at-creation exemption | CONFLICT | [FR-020](spec.md#L129) and T013b require a same-commit stub; [plan](plan.md#L32) permits dangling-anchor deltas and [HYP-006 pack](../001-disaster-response-hub/evidence/HYP-006.md#L33) claims that exemption. No explicit normative relaxation is recorded. |
| NFR shape and authorization | CONFLICT | [FR-004/035](spec.md#L107) require evaluation surface and named planner/SME/privacy attribution; the [contract](contracts/nfr-row.md#L5) has no surface field and prohibits prose targets while delivered rows use compound prose. T017-T023 name different drafters; precedence needs a documented decision. |
| Original six evidence stubs after 028 | PARTIAL | [Decision-record carry-over](../028-capstone-alignment/evidence/decision-record.md#L20) and [postfeature snapshot](../028-capstone-alignment/evidence/rubric-postfeature.md#L51) expressly leave them unchanged. New 028 stub conventions are not proof of repair or retirement of 027's obligations. |
| Table cardinality and delta traceability | CONFLICT | [E-10](data-model.md#L291) requires count equality with the monorepo register, whereas [FR-031](spec.md#L146) scopes canonical changes to 027 and [delta contract](contracts/open-delta-row.md#L34) requires delta rows there too. Growth/extra delta rows cannot be reconciled by a bare 40-row count. |

The four original feature-level [assumptions](spec.md#L165) are policy premises: accepted critical review,
annex non-authority, Australia-first domain rationale, and documentation-only delivery. They do not constitute
SME validation evidence. The later [D-009](../028-capstone-alignment/research.md#L73) explicitly leaves the
AU-only-residency/capstone-sovereignty tension unresolved; the report does not treat that tension as settled.

### Entity and Enforcement Assessment

| Entity | Status | Full-source assessment |
| --- | --- | --- |
| E-1 Gap | PARTIAL | Current 40 IDs are registered/contiguous; allocation dates, truthful closure links, append-only history and exhaustive validator checks are incomplete. |
| E-2 Assumption | CONFLICT | Eight dated rows cover topics, but lifecycle/authority differs from the normative spec; transitions are not checked by the verifier. |
| E-3 NFR | PARTIAL | All 13 rows have observable targets/methods, but concrete omissions and unsigned/provisional authority remain; the verifier only performs limited cell checks. |
| E-4 Persona | PARTIAL | All 18 blocks inspected; 13 enum mismatches, no Intelligence and incomplete fields/provenance. Proxy rule conflicts with FR-016. |
| E-5 Hypothesis | PARTIAL | Six themes and SC cross-references exist; all states are invalid, form/decision references incomplete, and some falsifiers are unbounded. |
| E-6 Evidence Pack | PARTIAL | Six existing stubs, not six observations; status equality is presently textual but not enforced. Mandatory metadata/history shape and HYP-025 pack are missing. |
| E-7 Scope Boundary | PARTIAL | Explicit hazard list but no contract-shaped SCP boundary rows for all named action/surface/integration decisions. Missing sections are not fail-closed in the verifier. |
| E-8 Deferred Scope | PARTIAL | Sixteen rows exist, but kind/target/evidence fields and required boundary links are incomplete; validator compares hazards only. |
| E-9 Open Delta | PARTIAL | Three OD rows do not implement required owners/deadlines/resolution governance, and the plan writer is not guarded. |
| E-10 Traceability Link | PARTIAL | Forty rows exist once but all states disagree with the register, resolving cells are not usable anchors, and delta traceability/cardinality needs explicit reconciliation. |

## Review and Checklist Evidence

### Every Original Checklist Checkbox

These 16 original `[x]` values are preserved only as historical source states. This is the pre-planning
quality checklist for 027, not the obligation-level delivery checklist promised by T054. Labels CHK-01 to
CHK-16 are report-local references, not new original task IDs. Follow-up for its incompleteness is AUD-027-001;
substantive content defects are assigned to their separate tasks above.

| Item | Original state | Status | Inspected checkbox and assessment |
| --- | --- | --- | --- |
| CHK-01 | [x] | PARTIAL | [No implementation details](checklists/requirements.md#L9): standards are deliberately normative, but the specification also prescribes Git/CODEOWNERS/script mechanisms; the generic checkbox is not a delivery certificate. |
| CHK-02 | [x] | IMPLEMENTED | [User value/business needs](checklists/requirements.md#L10): three stories explicitly address reviewer, planner, tester, legal and UX needs. |
| CHK-03 | [x] | PARTIAL | [Non-technical audience](checklists/requirements.md#L11): narrative intent is present; self-sufficient readability/usability has no independent review evidence and contract conflicts remain. |
| CHK-04 | [x] | IMPLEMENTED | [Mandatory sections](checklists/requirements.md#L12): local specification contains stories, requirements, assumptions, scope and success criteria. This is presence, not fulfilled implementation. |
| CHK-05 | [x] | IMPLEMENTED | [No clarification marker](checklists/requirements.md#L16): no outstanding NEEDS CLARIFICATION placeholder exists in the original 027 specification; the checklist's own literal is not an unresolved requirement. |
| CHK-06 | [x] | PARTIAL | [Testable/unambiguous requirements](checklists/requirements.md#L17): lifecycle, proxy, authority and plan contracts conflict with the normative requirements. |
| CHK-07 | [x] | IMPLEMENTED | [Measurable SC definitions](checklists/requirements.md#L18): numerical/observable criteria are authored. No pass rate or measured outcome is thereby established. |
| CHK-08 | [x] | IMPLEMENTED | [Technology-agnostic SCs](checklists/requirements.md#L19): the SCs concern documentation/readiness outcomes rather than mandating a runtime stack; document-search criteria fit this feature. |
| CHK-09 | [x] | IMPLEMENTED | [Acceptance scenarios defined](checklists/requirements.md#L20): all 9 original scenarios exist and are individually assessed above. |
| CHK-10 | [x] | IMPLEMENTED | [Edge cases identified](checklists/requirements.md#L21): all 5 exist and are individually assessed above. |
| CHK-11 | [x] | PARTIAL | [Scope bounded](checklists/requirements.md#L22): 001-only ownership is clear, but state/country and several target boundaries are still incompatible or unspecified. |
| CHK-12 | [x] | IMPLEMENTED | [Dependencies/assumptions identified](checklists/requirements.md#L23): local plan/contracts and policy assumptions are enumerated; their correctness/approvals remain separate questions. |
| CHK-13 | [x] | PARTIAL | [Every FR has clear acceptance](checklists/requirements.md#L27): FR statements and stories exist, but the promised FR-by-FR review evidence is absent and contradictory contracts prevent a single acceptance rule. |
| CHK-14 | [x] | IMPLEMENTED | [Primary flows covered](checklists/requirements.md#L28): the three stories cover alignment, role readiness and falsifiable claims. Actual readiness is unverified. |
| CHK-15 | [x] | UNVERIFIED | [Measurable outcomes met](checklists/requirements.md#L29): no attributable SC-001/SC-009 walkthrough results; structural findings also prevent blanket completion. |
| CHK-16 | [x] | PARTIAL | [No implementation leakage](checklists/requirements.md#L30): duplicates the generic content check, not an obligation-specific audit of the hardening scripts/configuration. |

### Quickstart and Formal Reviews

Every step of the [10-step quickstart](quickstart.md#L16) was read as source. No command or walkthrough was executed.
Several steps ask for a Validated record or a second hypothesis status although all current records are Proposed;
that conflict cannot be resolved by claiming the review ran successfully.

| Step or review | Status | Evidence assessment |
| --- | --- | --- |
| QS-01 Assumptions/signatures | PARTIAL | Eight rows exist; no Validated row or named CODEOWNERS signer can satisfy the instructed sample. |
| QS-02 NFR target/authority | PARTIAL | Thirteen target/method rows exist; role-only signatures and missing specific commitments prevent completion. |
| QS-03 Personas/functions | PARTIAL | No Intelligence profile; missing fields and named validation; proxy-only rule conflicts with FR-016. |
| QS-04 Hypothesis packs | PARTIAL | All six original packs exist; state/form/history issues remain and no pair has the requested different statuses. |
| QS-05 Scope | PARTIAL | Sections exist but single-state, action-category, source/surface/integration and content-origin details fail. |
| QS-06 Canonical traceability | PARTIAL | Forty-row canonical table exists without a duplicate, but target pointer/anchors/state equality fail. |
| QS-07 Delta plan gating | PARTIAL | OD-001 is unassigned, OD-002/003 have none phases; no reachable pre-plan enforcement. |
| QS-08 Gap inventory | IMPLEMENTED | Current exhaustive text inventory confirms all 40 literal gap IDs and contiguous per-prefix suffixes; historical append-only behavior is unverified. |
| QS-09 CODEOWNERS | UNVERIFIED | Team syntax exists. Membership, two-person independence, effective GitHub ownership/branch protection and actual approvals were not queried. |
| QS-10 Lint/verification execution | UNVERIFIED | Script/config inspected only; documented tool availability and hardening CI reachability are deficient. |
| Pre-research constitution review | UNVERIFIED | [Plan](plan.md#L58) records PASS assertions; no attributable independent review record proves the review occurred. |
| Post-design constitution review | UNVERIFIED | [Plan](plan.md#L84) records REVIEWED/PASS despite the contract mismatches identified above. Authored self-assessment is not approval. |
| US1 independent read-through | UNVERIFIED | [Story test](spec.md#L45) requires a new reviewer answering four questions; no named participant/question/result record was found. |
| US2 four-role readiness review | UNVERIFIED | [Story test](spec.md#L61) requires planner/test/privacy/UX outputs without blockers; no attributable artifacts establish all four outcomes. |
| US3 theme inspection | IMPLEMENTED | All six required themes are present by source inspection; rehearsals, status transitions and claims about outcome effectiveness remain unverified. |
| Task-named actor participation | UNVERIFIED | The [actor summary](tasks.md#L450) is a work assignment; inspected role definitions are not evidence the named actors contributed or countersigned. |
| T047 consistency sweep | PARTIAL | All named downstream inputs were inspected afresh; contradictions survive without corresponding deltas. No attributable original speckit.analyze review record was found locally. |
| T053 PR/check completion | UNVERIFIED | Local commit metadata proves committed artifacts, not a PR description, requested reviewer, approval, protected-branch setting or passing historical job. |
| Rubric uplift / HYP-025 | UNVERIFIED | Two authored 028 snapshots report 1.8 to 3.8; no hypothesis pack, bounded HYP-025 test window or attributable independent grading establishes settlement. Header counts are not rubric scoring. |

### Every Current Open Delta

| Delta | Status | Inspected evidence and governance assessment | Follow-up |
| --- | --- | --- | --- |
| OD-001 | PARTIAL | [Row](../001-disaster-response-hub/spec.md#L583) names Asia portability and existing pack, but target is unassigned, no owner/deadline is present and neither target-spec resolution nor automatic claiming/gating is implemented. | AUD-027-002, AUD-027-006, AUD-027-010 |
| OD-002 | PARTIAL | [Row](../001-disaster-response-hub/spec.md#L584) records possible team nonexistence but uses none (governance), not the required plan deadline; the interim CODEOWNERS line is commented. Team existence remains unverified. | AUD-027-002, AUD-027-004, AUD-027-011 |
| OD-003 | PARTIAL | [Row](../001-disaster-response-hub/spec.md#L585) admits role-only signatures but treats them as none (authoring workflow), with no named owner/deadline or real resolution evidence. | AUD-027-002, AUD-027-004, AUD-027-011 |

### Authored Versus Observed Evidence

The [quickstart's historical validated-results block](../001-disaster-response-hub/quickstart.md#L62) is an
authored assertion. The [metric test](../../tests/simulation/test_exercise_metrics.py#L9) supplies constructed
baseline/hub timestamps, ratios and survey scores; it supports arithmetic assertions, not real exercises or
human satisfaction. Its evacuation example asserts 3.5 hours, not the required 24-hour outcome.
The [publish fixture](../../tests/simulation/test_quickstart_rehearsals.py#L70) starts with an approved alert,
so successful-path assertions are not evidence of rejecting unapproved publication.

The [028 sign-off section](../028-capstone-alignment/evidence/decision-record.md#L36) credits bulk-author
scripts and structural checks; it does not name an eligible human persona reviewer or record the 027 required
four-role walkthrough. Generated content, role labels, standards names, countermeasure descriptions and checked
tasks are not promoted into human-review, execution, performance, residency or deployment evidence.

## Negative Search Scope

- Planning enforcement: all tracked `.specify/`, `.github/`, `scripts/`, `tests/`, `tools/` searched for verifier,
  RequirePlan, Open Delta and blocking-phase references; both prompts, planning agent and actual setup/prerequisite
  implementations inspected. No relocated pre-plan guard; only manual spec-035 workflow calls the verifier.
- HYP-025 pack: tracked `specs/` filename inventory plus content search for HYP-025 found only the 027 amendment
  and 028 generator watermark. Existing rubric baseline/postfeature files were read but are not an owned HYP-025 pack.
- Persona/requirement relocation: the complete target spec, its downstream documents/contracts, all evidence files,
  local file inventory and named role agent were inspected. No target persona directory or linked replacement
  profile artifact exists. Other role definitions cannot satisfy the in-spec schema or actual human validation.
- Asia assets: repository filename search for Philippines/Japan/Bangladesh and fil/ja/bn JSON files, plus country/
  agency/language text search across domain seeds, alert templates and fixtures, found no replacements for the
  six annex targets. Incidental country words in Australian disaster history are not operational country feeds.
- Lint/link tooling: tracked manifest/lockfile, configuration and workflows searched for markdownlint and
  markdown-link-check; only architecture-doc CI was found. No install or network query was made to infer local/global tools.
- Review records: all 17 local documents and direct evidence/commit metadata were inspected; no named
  walkthrough/approval results were found. External PR/team/protected-branch state remains explicitly unverified.
- Claims of all gap references: full current inventory of 544 tracked spec text artifacts, excluding other audit
  reports, not a sample. The 27-file header check for HYP-025 is separately bounded to its cited historical cohort.

## Validation and Handoff

This review did not execute any future command listed in the remediation tasks. Product tests, the hardening
verifier, builds, imports, servers, browsers, cloud/provider operations, installs and external approvals were not run.
No source, original task/spec/evidence/checklist/index file was edited; no branch or commit was created.

Completed document-only checks at this revision:

- Expected/observed HEAD match; scoped read-only Git status/log inspected, preserving pre-existing untracked work.
- All 17 original local inputs read in full; all required downstream 001 documents and six packs read in full.
- All 56 original task IDs, order and checkbox states preserved; T013b has its own row.
- All 36 FRs, 10 SCs, 9 scenarios, 5 edges and 6 appended items have separate coverage rows.
- All 13 NFRs, 18 personas, 6 original packs, 40 gap mappings, 3 deltas and 16 checklist items individually assessed
  or exhaustively inventoried as documented above; quickstart's 10 steps and formal review obligations assessed.
- All 14 follow-ups are unique, unchecked and include obligations, expected/observed, impact, developer/tester
  instructions, future prerequisites/commands/outcomes and completion criteria. Proposed fixtures/packs are not linked as evidence.
- Report text-integrity checks passed for original IDs/states/order, all coverage sets, the 14 unchecked task
  bodies, table shapes and all 465 local targets/line bounds.
- The coordinating reviewer performs the final editor-diagnostic and end-of-file formatting checks.
  These document-only checks do not establish product execution or external approvals.

Original-task status totals: **6 IMPLEMENTED, 42 PARTIAL, 1 MISSING, 2 CONFLICT, 4 UNVERIFIED, 1 SUPERSEDED**.
The 14 follow-ups remain future developer/tester/reviewer work. Main blockers are the missing planning guard,
incomplete invariant checks, unreconciled safety/contract boundaries and absent attributable approval/readiness
evidence. These require the assigned future work; static review cannot close them by relabeling checkboxes.

### 2026-09-18 Implementation Pass

This pass was performed as an isolated context for spec 027 only. Three parallel technical reviews examined verifier
and planner gating, safety/approval contradictions, and persona/hypothesis evidence authority. The source-completable
planning defect was corrected: `verify-spec-hardening.ps1` now accepts an optional feature ID and reports matching
unresolved `blocking_phase=plan` deltas even before `plan.md` exists; `setup-plan.ps1` invokes that preflight before
copying or creating a plan.

Validation: PowerShell AST parsing passed for both scripts. No plan was created and no cloud or approval operation was
run. Broader invariant completeness, shared publication contracts, CODEOWNERS enforcement, named countersigns, and
human evidence remain open.
evidence. These require the assigned future work; static review cannot close them by relabeling checkboxes.
