# Spec 028 Static Implementation Audit

## Scope and Method

- Review date: 2026-09-14.
- Expected and observed HEAD: `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a`.
- Audit subject: specification 028, including the portfolio artifacts it requires; other specifications are not independently audited.
- Working-tree baseline: tracked files were clean; unrelated untracked audit reports and the audit-index directory existed. Their contents are not evidence and are not read or changed.
- Sole writable artifact: this report. No original task state, source, evidence, index, branch, or commit is changed.
- Method: static document/source/configuration/test-assertion inspection and read-only text/integrity checks only. No application imports, tests, repository verifiers, builds, browsers, servers, cloud queries, deployments, installations, runtime/debug calls, or approvals.
- Contract: [Review Contract](../001-spec-implementation-audit/README.md#L11); [review rules](../../.github/instructions/code-review.instructions.md#L1).
- Assessment: PARTIAL, with contract conflicts and unverified closeout claims. Original task checkboxes are not completion evidence.
- Population: the closed 27-spec partition in research D-008 and the literal 41 current root numbered spec files were both inspected for 028-owned obligations. The additional 14 are reported separately, not independently audited.
- Delegation integrity: three isolated read-only summaries were rejected for unsupported or out-of-scope assertions; findings below were checked directly. Three temporary session notes created contrary to the delegation restriction were removed, restoring the initially empty session memory. No delegated summary is used as evidence.
- Final metadata observation: HEAD is unchanged and tracked files remain clean. Untracked implementation reports for specs 029, 030, and 031 appeared during this audit in addition to this report; their origin is not established, and they were not read, edited, or removed. Pre-existing audit material was preserved.

## Findings

Priority order: first address safety-contract drift (AUD-028-010), evidence/metric integrity (002, 008, 009, 014, 015), and the validation blind spot (001). Then repair missing content (003-007), identifier/authority contracts (011-012), scope and handoff decisions (013, 016), and the bounded feed prerequisite (017). Severity labels below are P1 important integrity/safety risks and P2 correctness/maintainability risks; this static audit does not establish a live production incident.

### P1: The multilingual fallback does not inherit its named safety owner

[Spec 008 FR-CAP-008-002](../008-communication-agent/spec.md#L365) substitutes an English-baseline classifier when language confidence is low. Its claimed owner instead [holds signals for human review and forbids automatic handoff on unavailable/unexpected evaluation](../010-monitoring-agent/spec.md#L135). This documentation conflict could guide a future implementation to fail open; no runtime defect is asserted here. Follow-up: AUD-028-010.

### P1: Heading presence does not establish the required content coverage

[FR-001 through FR-005](spec.md#L114) and [SC-001](spec.md#L199) require assumption counts and references, persona contracts, falsifiable hypotheses with evidence, and explicit deferred scope. The [validator](scripts/validate-section-coverage.ps1#L35) discovers numbered folders, tests only four headings, counts one bracketed marker spelling, and emits CSV. It does not validate those content obligations, inspect research/tasks markers, or fail on a false heading result. The [closure record](evidence/decision-record.md#L26) cannot use heading booleans alone as proof of the full gate. Follow-up: AUD-028-001.

### P1: New allocations collide with pre-existing identities

The [allocation block](../shared/gap-id-register.md#L68) declares zero pre-feature ASM/HYP watermarks, while [spec 001 already defines ASM-001 through ASM-008](../001-disaster-response-hub/spec.md#L103) and [HYP-001 through HYP-006](../001-disaster-response-hub/spec.md#L441). Read-only Git inspection of parent `996a1f04ebcdaafe9270e97ec71bcb816da212a5^` confirms these precede feature 028. [Spec 003](../003-rubric-gap-closure/spec.md#L259) now assigns different meanings to ASM-001 and [HYP-001](../003-rubric-gap-closure/spec.md#L275). [Spec 001 SCP-080](../001-disaster-response-hub/spec.md#L609) and [spec 026 SCP-080](../026-sim-warp-playback/spec.md#L207) also differ. The [US1 allocator](scripts/apply-us1-hardening.ps1#L23) starts at zero and does not consume the promised register/SQL watermark. A range reservation is not a per-entry identity ledger; the [REQ reservation](../shared/gap-id-register.md#L72) is unused despite the [cross-spec requirement mapping rule](data-model.md#L66). The [US2 cursor](scripts/apply-us2-hypotheses.ps1#L21) starts at 26 but [skips an already-authored agent](scripts/apply-us2-hypotheses.ps1#L161) before consuming that agent's three IDs, so an interrupted rerun can reuse earlier IDs for a later agent; its skip bypasses missing-stub repair. Follow-up: AUD-028-002.

### P1: Generic hypotheses have no evidence packs and do not use the agreed format

There are 24 generic authoring hypotheses in specs 003 through 026, plus HYP-025 in 027 and HYP-026 in 028. [The generator](scripts/apply-us1-hardening.ps1#L122) substitutes `If ... then ...` for the [required statement](contracts/evidence-stub.contract.md#L17) and constructs a doubled `HYP-HYP-...` path without creating a stub. [Spec 027](../027-spec-hardening/spec.md#L272) and [spec 028](spec.md#L250) point to absent singly-prefixed stubs. The only root-owner HYP evidence files found are six legacy spec-001 files and the fifteen country files. None establishes evidence for these 26 distinct new authoring hypotheses. Lack of rubric regression also does not falsify failure to achieve the asserted +1 uplift. Follow-up: AUD-028-005.

### P1: The metric trace is structurally incompatible and overstates outcome ownership

The [contract](contracts/capstone-metric-trace.contract.md#L9) fixes seven columns with Status last and exact owner-cell grammar; the [trace](../shared/capstone-metric-trace.md#L9) puts Status third, uses prose/path/range owners, places deferral prerequisites in Baseline, and adds [a second table](../shared/capstone-metric-trace.md#L33). All 20 metric/cohort pairs exist, but no row meets all owner-format rules. Follow-up: AUD-028-008.

The [economic-loss AU row](../shared/capstone-metric-trace.md#L27) has no HYP ID. The [lives-saved row](../shared/capstone-metric-trace.md#L11) cites coordination/evacuation/orchestration hypotheses rather than a quantified annual lives-saved hypothesis. [The five benchmark SC additions](../015-performance-benchmarks/spec.md#L208) describe scenario types but do not supply numerical baselines or concrete exercise-artifact identifiers. The fifteen deferred hypotheses are real authored artifacts, but risk-calibration error is not economic-loss reduction, and [JP immediate evacuation](../009-evacuation-agent/evidence/HYP-031.md#L4) is not 24-hour early evacuation. `Validated` in this contract means reference validation only, never a measured disaster outcome. Follow-up: AUD-028-009.

### P1: The closeout record declares gates passed without the required records

[The decision record](evidence/decision-record.md#L7) claims all nine SCs passed. Its [gate table](evidence/decision-record.md#L27) substitutes country deferral for the SC-003 independent-reviewer timing experiment, overlap for SC-004 marker absence, and marker absence for SC-006 overlap. [SC-003](spec.md#L201) is explicitly deferred and non-blocking, not passed. No timing records, validator CSV, per-stub/persona audit, overlap audit, monotonicity diff, critique report, or analysis report were found in the bounded searches below. The differently named decision record is retained as partial T065 authorship evidence, but lacks either required first-line decision and T064 finding dispositions. Its final sentence demotes T064/T066 without an approved amendment. Follow-up: AUD-028-014.

### P1: The rubric uplift claim is not a reproducible measurement against the named rubric

[The baseline](evidence/rubric-baseline.md#L5) claims a grader run from an unavailable SQL inventory; it says 17/27 have assumptions and then lists 11 missing, and says three scope sections while listing five. [The post snapshot](evidence/rubric-postfeature.md#L3) defines its own structural five-level scale, omits a comparable timestamp/run identifier and five-criterion H2 layout, and relies on contradicted content-conformance assertions. [The authoritative rubric](../../AMA_Rubric_Asia.md#L7) does not contain the five named criterion rows; no approved mapping to its actual criteria is supplied. The arithmetic 1.8 to 3.8 is correct, but SC-009's provenance, comparable population, and rubric-method gate are UNVERIFIED. The real renamed post snapshot is not MISSING. Follow-up: AUD-028-015.

### P2: Assumption, persona, and country-scope content remains incomplete

[The authoring template](scripts/apply-us1-hardening.ps1#L96) deliberately emits bare assumptions and omits drafter/countersigner fields; [existing headings skip authoring](scripts/apply-us1-hardening.ps1#L156). For example, [spec 010](../010-monitoring-agent/spec.md#L215), [014](../014-azure-openai-integration/spec.md#L225), and [017](../017-cd-pipeline/spec.md#L149) retain unmapped assumptions without the explicitly required D-009 risk. [Spec 027](../027-spec-hardening/spec.md#L257) has only two untagged assumptions; [028](spec.md#L182) has tags but no resolvable per-entry ASM identifiers. Follow-up: AUD-028-003.

[Generic persona blocks](../003-rubric-gap-closure/spec.md#L263) are prose catalogue pointers, not the required [YAML and profile sections](../027-spec-hardening/contracts/persona-profile.md#L5). Non-AU placeholders have prose preconditions rather than the T062a list shape. [027](../027-spec-hardening/spec.md#L268) supplies only one broad reference. The [canonical 001 set](../001-disaster-response-hub/spec.md#L169) itself defers concrete SME identities, so copied `validated` labels are not human consultation evidence. Follow-up: AUD-028-004.

[013 scope](../013-root-readme/spec.md#L206), [014 scope](../014-azure-openai-integration/spec.md#L247), [015 scope](../015-performance-benchmarks/spec.md#L179), [024 scope](../024-simulation-control-chat/spec.md#L409), and [027 scope](../027-spec-hardening/spec.md#L274) do not supply the required country/hazard deferral with promotion conditions. The eleven canonical meta bullets are present and must be preserved. Follow-up: AUD-028-006.

### P2: AU-only requirements lack inline assumption citations

The read-only inventory of all 41 current root numbered spec files found zero concrete `[AU-only ... see ASM-<three digits>]` citations. Definite AU-specific obligations include [014 FR-001/FR-005](../014-azure-openai-integration/spec.md#L192), [006 storage](../006-data-ingestion-storage/spec.md#L258), and [013 FR-001/FR-008](../013-root-readme/spec.md#L135). General persona or scope prose does not satisfy [FR-005a](spec.md#L119). Follow-up: AUD-028-007.

### P2: Language identifiers are fixed in statements despite an explicit deferral

[Spec 008](../008-communication-agent/spec.md#L364) states identifier choice is deferred, yet HYP-027/028/029 and [their stubs](../008-communication-agent/evidence/HYP-027.md#L4) require `fil-PH`, `ja-JP`, and `bn-BD` corpora. These are operative test prerequisites, not merely illustrative text. Follow-up: AUD-028-011.

### P2: Authoritative intent exists but reciprocal rules are not the canonical contract

[006 FR-024](../006-data-ingestion-storage/spec.md#L254) is explicitly retained as a contract-level pointer; [008](../008-communication-agent/spec.md#L367) reciprocally supersedes it. [011](../011-resource-allocation-agent/spec.md#L357) and [018](../018-aidr-guidance-integration/spec.md#L342) express recovery authority, while [008](../008-communication-agent/spec.md#L366) defers warning escalation. Preserve that supported work. Most rules nevertheless split the token from its value with backticks, use different capability strings, and append rules far from the governed requirement. The 008 supersession note is not an `authoritative for:` declaration. [027's stale-name replacement and scope note](../027-spec-hardening/spec.md#L18) are implemented, but its canonical reciprocal pair with 028 is absent. These are exact-contract defects, not evidence that all ownership intent is missing. Follow-up: AUD-028-012.

### P2: The population and preservation rules disagree with their implementation

[Research D-008](research.md#L68) closes the population at 27, whereas [FR-001](spec.md#L114) and the [validator](scripts/validate-section-coverage.ps1#L35) cover every current numbered folder. There are 41 matching spec files, including both 001 and both 036 folders; the extra 14 are not grandfathered by an explicit 028 amendment. [034 continues to defer to 028](../034-webapp-capstone-coverage/spec.md#L1098), not replace it. A separate stale-duplicate removal proposal required by [the scope amendment](spec.md#L192) was not found; the excluded historical duplicate folder was not edited. Clarify scope before expanding implementation. Follow-up: AUD-028-013.

### P2: The handoff instructions contain contradictory validation and dependency rules

[The task execution note](tasks.md#L82) names T034 as the 027 preparation task, although [T034](tasks.md#L219) authors communication hypotheses; the correct preparation task is T009. Several per-owner notes similarly point one task ahead. [The meta-task check](tasks.md#L307) combines a regex start anchor with `-SimpleMatch`, so valid bullets cannot satisfy that literal pattern. [Quickstart marker discovery](quickstart.md#L35) uses regex alternation as a filesystem glob and demands zero bare strings even though requirement/example text contains them; the validator instead checks only colon markers in spec files. [T063a](tasks.md#L387) accepts 80% at <=10 minutes while SC-003 says under 10 minutes per spec. [The final checkpoint](tasks.md#L406) incorrectly calls all nine SCs grep-verifiable. The documentation-only plan and T007's executable helper also need an explicit tooling exception, not silent expansion. Follow-up: AUD-028-016.

### P2: The Japanese candidate feed lacks a bounded freshness precondition

[T013](tasks.md#L114) requires a freshness SLO for every candidate feed. [PAGASA and BWDB/FFWC](../006-data-ingestion-storage/spec.md#L381) have age bounds, but the JMA entry says `24x7 freshness SLO` and sub-second ingestion validation. Continuous availability and processing latency do not bound the age of received source data. Follow-up: AUD-028-017. No actual feed integration is required by this documentation feature.

## Inputs and Search Limits

All 16 local input files were read completely: [specification](spec.md#L1), [tasks](tasks.md#L1), [plan](plan.md#L1), [research](research.md#L1), [data model](data-model.md#L1), [quickstart](quickstart.md#L1), [checklist](checklists/requirements.md#L1), [metric contract](contracts/capstone-metric-trace.contract.md#L1), [stub contract](contracts/evidence-stub.contract.md#L1), [meta contract](contracts/meta-spec-flag.contract.md#L1), [baseline](evidence/rubric-baseline.md#L1), [post snapshot](evidence/rubric-postfeature.md#L1), [decision record](evidence/decision-record.md#L1), [US1 author](scripts/apply-us1-hardening.ps1#L1), [US2 author](scripts/apply-us2-hypotheses.ps1#L1), and [validator](scripts/validate-section-coverage.ps1#L1). No other local amendment, review, contract, checklist, or evidence document exists in that recursive inventory.

Additional direct inputs: all 41 root spec files' applicable sections and full-file declaration searches; all 21 existing root-owner HYP evidence files; [shared register](../shared/gap-id-register.md#L1); [shared trace](../shared/capstone-metric-trace.md#L1); [persona contract](../027-spec-hardening/contracts/persona-profile.md#L1); [capstone brief](../../capstone.md#L1); [rubric](../../AMA_Rubric_Asia.md#L1); [grader skill](../../.github/skills/ama-rubric-grader/SKILL.md#L1); [constitution including amendment 1.2.0](../../.specify/memory/constitution.md#L1); [code-commenting rules](../../.github/instructions/code-commenting.instructions.md#L1); [review reference](../../.github/instructions/references/code-review-checklists.md#L1); [package scripts](../../package.json#L1); [CI](../../.github/workflows/ci.yml#L1); [existing hardening verifier](../../scripts/verify-spec-hardening.ps1#L1); [architecture citation checker](../../tools/lint/check_spec_cross_refs.py#L1); [synthetic ledger test](../../tests/contract/spec_037/test_feature_value_ledger_schema.py#L9); [pipeline benchmarks](../../tests/benchmark/test_pipeline_performance.py#L1); [isolated text-inventory test pattern](../../tests/integration/test_manifest_lint_detects_missing_entry.py#L22); [reciprocal-reference test pattern](../../tests/contract/test_rag_optout_lint.py#L102).

No external legal/current-service verification was attempted. Named laws are assessed against 028's requested text, not certified as current or sufficient law. Model-hosting-only residency language has an explicit later replacement in constitution 1.2.0; it does not authorize non-AU platform-data persistence or supersede the whole 028 feature. No original task is assigned SUPERSEDED without an explicit task replacement.

| Search | Exact bounded scope and terms | Result and evidentiary limit |
| --- | --- | --- |
| NEG-01 | Recursive filenames under `specs/`, `docs/`, `artifacts/`, `tools/`, `tests/`, `.github/`, excluding every `implementation-review-tasks.md` and the audit-index tree; requested evidence names plus hyphen/underscore variants, `spec_inventory`, `id_watermarks`. | Only renamed post snapshot found. No persistent SQL export or requested closeout audits. This does not prove a historical session never ran. |
| NEG-02 | Recursive `HYP-*.md` filenames and hypothesis references under `specs/`, `docs/`, `artifacts/`, excluding all implementation reports. Checked exact doubled paths, corrected single paths, owning-spec evidence folders and central 028 evidence. | 21 existing files: six legacy plus fifteen country stubs. No packs for the 26 new generic hypotheses, including 025/026. Legacy same-number files have different statements, so are not replacements. |
| NEG-03 | All 41 root numbered `spec.md` files; four H2 declarations, all assumptions/personas/hypotheses/scope sections, AU-only citation grammar with concrete numeric IDs, `taxonomy.mapp`, drafter/countersigner mapping, D-009 risk statements. | 27 complete heading sets, zero concrete AU-only citations; only 005/006/009 have newly tagged explicit D-009 ASM risk lines. Bare 028 risk prose and old 001 residency assumptions do not establish universal propagation. |
| NEG-04 | All active workflow files, `tests/`, `tools/`, package scripts; `validate-section-coverage`, `apply-us1`, `apply-us2`, `capstone-metric-trace`, `evidence-stub.contract`, `spec_inventory`, `id_watermarks`, `verify-spec-hardening`. | Existing verifier is 001/027-specific; architecture citation checker checks numbers, not content. Spec-037 synthetic schema tests mention the trace path but never parse the file. No dedicated 028 contract test found. Plan does not mandate a new CI step; absence is not independently a deployment defect. |
| NEG-05 | Recursive permitted Markdown/text under `specs/`, `docs/`, `artifacts/`; `specs/feature` near `remove`, `removal`, `delete`; filenames containing duplicate/removal variants. | Only promises in 028 spec found, not a removal proposal. Excluded duplicate specifications were not independently reviewed. |
| NEG-06 | All root numbered folders' `spec.md`, `research.md`, `tasks.md`, excluding audit material; bracketed colon markers and bare phrase separately. | Three colon-form markers remain in 036-sim-agent-extend at lines 5000-5002 as historical questions; later clarification resolves them. Literal zero-marker gate conflicts with retaining history/examples. No unresolved 028-local decision is inferred just from a quoted marker. |

## Future Validation Conventions

Everything in this section and the tasks below is a future instruction, not executed audit work. Approval for implementation, required runtimes, and an isolated fixture checkout are prerequisites. Do not run the bulk authoring scripts on the working portfolio as a test. Keep archive inputs and original identifiers immutable unless the maintainer approves a documented compatibility migration.

- FV-01: proposed new text-contract test home `tests/contract/test_capstone_alignment_docs.py`, following the existing [reciprocal-reference assertions](../../tests/contract/test_rag_optout_lint.py#L102) and [isolated inventory fixtures](../../tests/integration/test_manifest_lint_detects_missing_entry.py#L22). Prerequisites: existing project Python/pytest environment plus PowerShell 7 for helper subprocess tests; fixtures must not import application packages or need network/cloud credentials. Future command: `uv run pytest tests/contract/test_capstone_alignment_docs.py -q -k <task-filter>` after the proposed tests exist. Expected: valid fixture passes, each malformed fixture fails with precise file/ID diagnostics.
- FV-02: future helper invocation `pwsh -File specs/028-capstone-alignment/scripts/validate-section-coverage.ps1 -RepoRoot <isolated-fixture-root>`. Expected: stable CSV columns, exact scope inventory and nonzero exit on invalid content after remediation. The present implementation does not yet deliver those expectations.
- FV-03: read-only historical comparison `git diff <recorded-baseline-sha> <candidate-sha> -- specs/shared/gap-id-register.md` plus full identity/reference inventory. Prerequisites: both commits locally available, approved alias/migration policy. Expected: preservation of historical meanings, no reused identities, every new canonical requirement mapped. A plus-only diff alone is insufficient.
- FV-04: future authorized review activities, not product tests: rubric-grader assessment, independent reviewer timings, `rubber-duck` critique, and `/speckit.analyze`. Prerequisites: agreed criteria/scope, identified independent reviewers, captured run metadata and actual findings. Expected: reproducible evidence, honest untested/unapproved states, and explicit dispositions. No cloud deployment is necessary to complete this documentation audit.

## Remediation Tasks

- [ ] AUD-028-001 Enforce the complete portfolio content contract in the validation workflow
  - Affected requirements/tasks: FR-001, FR-002, FR-003, FR-004, FR-005, FR-005a, FR-015, FR-021, FR-023; SC-001, SC-004, SC-005; T007, T058, T062, T062a.
  - Expected versus observed and impact: the required content must be established for every scoped artifact; the current validator reports only heading presence and a narrow marker count. A positive CSV can conceal invalid or absent content and must not establish completion.
  - Developer instructions: extend the existing [validation owner](scripts/validate-section-coverage.ps1#L22) and its documented invocation, preserving the existing CSV columns or explicitly versioning additions. Define exact folder discovery, distinguish clarification examples from unresolved markers, validate document references and required content without executing product code, and return a failing exit code for contract violations. Reconcile the scope contract before changing discovery.
  - Tester instructions: use FV-01's proposed home and existing isolated-inventory/reciprocal-reference test patterns. Include a complete valid spec; a heading-only spec; an absent hypothesis stub; an invalid assumption target; malformed/non-AU validated personas; research/tasks-only markers; duplicate numeric prefixes; and excluded shared/feature folders. Assert content failures and nonzero exit, and retain the CSV compatibility assertion. A scope-empty directory must fail rather than report a vacuous pass.
  - Future command, prerequisites, expected result: after owner-approved source remediation, PowerShell 7 and an isolated fixture tree are prerequisites; run `pwsh -File specs/028-capstone-alignment/scripts/validate-section-coverage.ps1 -RepoRoot <fixture-root>`. Valid fixtures must succeed and invalid fixtures must identify the exact file/obligation and fail. This command was not run in this audit.
  - Completion criteria: all agreed scoped files are examined, every contract failure has a deterministic diagnostic, negative fixtures cannot produce a passing gate, and execution evidence is recorded only by the future tester.

- [ ] AUD-028-002 Repair global identity allocation without silently renumbering history
  - Affected requirements/tasks: FR-014, FR-022, SC-007; E-006/E-013; T001, T003, T005, T008, T009, T010, T011, T012, T013, T014, T015, T016, T017, T018, T019, T020, T021, T022, T023, T024, T025, T026, T027, T028, T029, T030, T031, T032, T033, T034, T035, T036, T037, T038, T060.
  - Expected versus observed and impact: global monotonic identities must resolve to one meaning. Zero-start allocators reuse legacy ASM/HYP IDs; range prose omits per-entry owners, REQ mappings, and actual high-water marks; interrupted US2 reruns can reuse IDs or fail to repair stubs.
  - Developer instructions: own the [register](../shared/gap-id-register.md#L62), [US1 allocator](scripts/apply-us1-hardening.ps1#L23), and [US2 allocator](scripts/apply-us2-hypotheses.ps1#L21). Inventory all declared identities and references, preserve pre-feature meanings, and obtain an explicit collision/alias migration decision because blanket renumbering violates FR-022. Bind stable owner/cohort keys to reserved IDs rather than mutable skip-sensitive cursors; fill missing paired artifacts idempotently. Map new cross-spec FR-CAP entries to REQ entries or obtain an explicit E-006 amendment. Do not change runtime identities.
  - Tester instructions: use FV-01/FV-03 and the existing reciprocal-reference test home pattern. Fixtures: pre-existing ASM-008/HYP-006, gaps from skipped sections, duplicate SCP-080, populated first agent with empty second agent, existing hypothesis with deleted stub, and two repeat runs. Assert globally unique meanings, preserved old references, monotonically new claims, deterministic outputs, and zero changes on a complete rerun.
  - Future commands/prerequisites/results: FV-01 filter `identity`, FV-03, and author scripts only in an isolated disposable fixture after review approval. All collisions must be diagnosed; no fixture may silently overwrite a historical claim.
  - Completion criteria: every new entry has a resolvable owner, collisions have approved compatibility records, reservation/usage counts match definitions, and partial reruns preserve the exact owner-to-ID mapping.

- [ ] AUD-028-003 Complete assumption taxonomy and privacy-tension mappings
  - Affected requirements/tasks: FR-001, FR-005, SC-001; D-002/D-009, E-002, unnumbered residency constraint; T008, T009, T010, T011, T012, T013, T014, T015, T016, T017, T018, T019, T020, T021, T022, T023, T024, T025, T026, T027, T028, T029, T030, T031, T032, T033.
  - Expected versus observed and impact: each scoped spec needs at least three tagged assumptions with resolving IDs and inherited role metadata. Existing heading skips leave legacy lists unmapped; new template bullets remain bare; explicitly required D-009 risks in 010/014/017 are absent.
  - Developer instructions: repair [Build-Sections](scripts/apply-us1-hardening.ps1#L63) and the per-owner Assumptions surfaces in the population table below. Preserve original prose and IDs; append an explicit legacy-to-canonical mapping with tag, basis/test, drafter, different countersigner, status, linked gaps and cohort. Review every PII/location/persona-touching owner, not the generator's `pii` boolean alone. Respect constitution 1.2.0's bounded model-hosting exception while retaining unresolved platform-data sovereignty constraints. Depends on AUD-028-002 and AUD-028-013.
  - Tester instructions: FV-01 in the existing static-contract test tier. Fixtures: three complete assumptions; two entries; three bare bullets; legacy A-001 mapped correctly/incorrectly; same drafter and countersigner; absent D-009 in 010/014/017; non-PII owner with explicit justified non-applicability. Assert exact tags, resolvable links and no invented approvals.
  - Future commands/prerequisites/results: FV-01 filter `assumption` and FV-02 after taxonomy/scope decisions; every owner must pass content assertions without rewriting archived source facts.
  - Completion criteria: all scoped legacy and new entries map explicitly, privacy risk obligations are accounted for per owner, and all unsupported validation/signature claims remain provisional.

- [ ] AUD-028-004 Make persona references contract-conformant and provenance-honest
  - Affected requirements/tasks: FR-003, FR-005, FR-023, SC-001; E-004, US1 scenario 2, T008, T009, T010, T011, T012, T013, T014, T015, T016, T017, T018, T019, T020, T021, T022, T023, T024, T025, T026, T027, T028, T029, T030, T031, T032, T033, T062a.
  - Expected versus observed and impact: at least two concrete persona profiles/references must supply contract fields and applicability. Current catalogue-wide prose pointers omit those fields, 027 has one pointer, and `validated` labels lack named review provenance.
  - Developer instructions: use the [existing persona contract](../027-spec-hardening/contracts/persona-profile.md#L5), [canonical 001 set](../001-disaster-response-hub/spec.md#L167), and owning Personas sections. Define an approved reference/placeholder representation because the inherited schema requires an SME entry while FR-023 intentionally defers non-AU validation. Preserve country placeholders, add structured nonempty promotion lists, reference specific roles/IDs, and distinguish authored role descriptions from human sign-off. Never synthesize a reviewer identity or date. Depends on AUD-028-002/013.
  - Tester instructions: follow the existing static reciprocal-reference tests in FV-01. Cover two valid references, one broad catalogue pointer, absent authority boundary, invalid jurisdiction enum, scalar `validated_by`, empty non-AU preconditions, PH/JP/BD wrongly marked validated, and a deferred profile correctly carrying no completed approval. Assert shape, role applicability and provenance requirements separately.
  - Future commands/prerequisites/results: FV-01 filter `persona`; future authorized SME review only where promotion is requested. A placeholder must pass placeholder shape without being called human-validated.
  - Completion criteria: every owner has at least two resolvable persona descriptions; non-AU status is explicit; T062a audit is per persona, and every claimed human validation links to an actual review record.

- [ ] AUD-028-005 Supply co-located evidence for every new generic hypothesis
  - Affected requirements/tasks: FR-004, FR-015, SC-001, E-003; T008, T009, T010, T011, T012, T013, T014, T015, T016, T017, T018, T019, T020, T021, T022, T023, T024, T025, T026, T027, T028, T029, T030, T031, T032, T033, T062; appended HYP-026.
  - Expected versus observed and impact: each new hypothesis needs a persona, falsifiable outcome, window and owning-folder evidence at creation. The 26 generic hypotheses have wrong/absent stubs and mostly test authoring-process proxies with weaker falsification than the asserted uplift.
  - Developer instructions: repair the [hypothesis template](scripts/apply-us1-hardening.ps1#L122), [027 HYP-025](../027-spec-hardening/spec.md#L272), [028 HYP-026](spec.md#L250), and each owning Hypotheses block. After identity reconciliation, add the correctly named co-located six-heading stubs, not central empty placeholders. Rewrite statements to the agreed format and an actual measurable domain/operator benefit; pipeline-only owners still need a reliability/operator hypothesis. Preserve the fifteen valid country statements and explicitly grandfathered legacy packs.
  - Tester instructions: FV-01 using existing marker-to-file/reciprocal test patterns. Cover doubled prefix, wrong owner directory, same ID but different legacy statement, absent pack, wrong heading order, fewer than two prerequisites, unbounded window, zero uplift without regression, and out-of-sequence status promotion. Assert exact statement correspondence and that all 26 new claims have one correct pack.
  - Future commands/prerequisites/results: FV-01 filter `hypothesis`, then FV-02; prerequisites are approved identifiers and owner-reviewed measurable statements. No experiment is run merely to fill a stub; initial status remains `Not tested`.
  - Completion criteria: no orphan or mislocated new hypothesis; every falsification can reject failure of the stated benefit; counts reconcile between definitions, register, and evidence.

- [ ] AUD-028-006 Restore explicit country and hazard deferrals in retained scope sections
  - Affected requirements/tasks: FR-002, FR-005, SC-001; US1 scenario 4, edges 1/2/3; T008, T009, T020, T021, T022, T031 and all per-owner scope obligations.
  - Expected versus observed and impact: at least three scope entries and a country/hazard deferral with promotion preconditions are required. Existing sections in 013/014/015/024/027 were skipped; generic metadata elsewhere cannot substitute for an explicit scope rule.
  - Developer instructions: amend those owning Out-of-Scope sections additively, preserving their valid exclusions and the eleven canonical meta flags. Reuse [001's deferred register](../001-disaster-response-hub/spec.md#L461) through an explicit taxonomy mapping where appropriate, rather than replacing it with two unmapped bullets. Name PH/JP/BD or a capstone hazard, the relevant legal/feed/language/SME prerequisites and decision owner; do not activate deferred runtime features. Depends on identity/scope decisions.
  - Tester instructions: FV-01's static document fixtures: three ordinary exclusions without a country; country name without prerequisites; inherited detailed register with valid mapping; meta-only paragraph; and a complete country-specific deferral. Assert distinction between non-applicable today and silently omitted, and preserve all 11 exact meta bullets.
  - Future commands/prerequisites/results: FV-01 filter `scope_items`, FV-02 after approved text edits. All scoped owners must satisfy both count and meaningful deferral checks.
  - Completion criteria: no owner relies on a heading or generic Asia mention alone; original exclusions and valid country preconditions remain intact.

- [ ] AUD-028-007 Bind every effective AU-only requirement to its assumption
  - Affected requirements/tasks: FR-005a, SC-001, US1 scenario 5; clarification 2026-04-25 item 2; T008 through T033 owner-hardening obligations, T058, T066. This amendment lacks a dedicated original implementation task.
  - Expected versus observed and impact: inline concrete ASM citations must justify each AU-only FR; zero current numeric citations were found, including explicitly Australian storage, language, region and jurisdiction requirements.
  - Developer instructions: review every FR and its continuation lines in each agreed owner file, not only occurrences already tagged AU-only. Add a citation to a resolving same-spec or shared assumption, without narrowing portable requirements gratuitously. Coordinate with AUD-028-002/003; preserve existing FR IDs and functional semantics. Add explicit task ownership for this previously uncovered amendment.
  - Tester instructions: FV-01 static-contract tier; fixtures for Australian region FR, multi-line nine-jurisdiction FR, generic geography-neutral FR, invalid ASM target, old ambiguous reused ASM, and literal example `[AU-only ... ASM-###]`. Assert the first two have valid inline links, portable FR remains untagged, and examples do not count as implementation.
  - Future commands/prerequisites/results: FV-01 filter `au_scope`, FV-02 after owner-reviewed applicability classification; expected zero AU-only orphan requirements and no false positives for portable FRs.
  - Completion criteria: a full per-FR applicability inventory reconciles to citations and canonical assumption meanings; no sample-based universal claim.

- [ ] AUD-028-008 Restore the metric trace schema and make its writer preserve it
  - Affected requirements/tasks: FR-013, SC-002, D-003, E-012; T004, T039, T040, T041, T042, T043, T061.
  - Expected versus observed and impact: one seven-column table, Status last, exact owner grammar and 20 unique pairs. The actual table and writer use incompatible shapes; the writer's replacement rows have fewer cells, so rerunning it on a skeleton cannot produce the required schema.
  - Developer instructions: own [trace](../shared/capstone-metric-trace.md#L9), [contract](contracts/capstone-metric-trace.contract.md#L9), and [US2 trace writer](scripts/apply-us2-hypotheses.ps1#L222). Use structured row construction and stable metric/cohort keys. Resolve the real `SC-CAP-015-*` ID versus three-digit-only grammar conflict explicitly; do not renumber legacy SCs silently. Move the later criticality table only via a compatible referenced artifact or approved contract amendment, retaining spec-037's authored classification. Depends on AUD-028-009/013.
  - Tester instructions: extend the FV-01 proposed text tests, not just [synthetic ledger-schema assertions](../../tests/contract/spec_037/test_feature_value_ledger_schema.py#L53). Fixtures: valid 20-row cross-product, duplicate/missing cohort, swapped columns, short generated row, extra table, bad owner, empty deferred prerequisites, and a complete rerun. Assert all cells against the real file and contract.
  - Future commands/prerequisites/results: FV-01 filter `metric_schema`; writer only in disposable fixtures after approval. Expected exact schema parity, 20 unique rows and deterministic rerun with no artifact loss.
  - Completion criteria: producer, reader, task validation, and stored trace agree; no compatibility-breaking silent truncation or second uncontracted table.

- [ ] AUD-028-009 Give each metric a semantically valid owner and bounded baseline
  - Affected requirements/tasks: FR-012, FR-013, SC-002; T022, T039, T040, T041, T042, T043, T061.
  - Expected versus observed and impact: five outcome metrics require genuine SC/HYP owners, quantitative baseline units and a reproducible method. Economic loss lacks an AU HYP, lives-saved cites indirect proxies, and the benchmark additions name scenario descriptions rather than identified baseline records.
  - Developer instructions: coordinate [015 SC-CAP additions](../015-performance-benchmarks/spec.md#L208), [001 SC/HYP owners](../001-disaster-response-hub/spec.md#L125), [012 calibration hypotheses](../012-risk-assessment-agent/spec.md#L354), and the shared trace. Define or reference a measured/modelled annual lives-saved hypothesis and an economic-loss hypothesis; document causal assumptions, units, denominator and annualization separately from proxy metrics. Retain JP immediate-onset routing but do not reinterpret it as a 24-hour prediction. Future baseline acquisition is prerequisite evidence, never fabricate values to satisfy the schema.
  - Tester instructions: use the existing [benchmark home](../../tests/benchmark/test_pipeline_performance.py#L188) for future scenario measurements and FV-01 for text linkage. Fixtures: matching response/evacuation/logistics owner; nonexistent HYP; calibration-only economic claim; immediate-onset JP event; zero/negative baseline denominator; missing annualization; and all-cohorts-deferred metric. Assert semantic metric mapping and honest unmeasured status, not mere ID existence.
  - Future commands/prerequisites/results: FV-01 filter `metric_owner`; only later, with approved baseline packs and scenario contracts, use the owner's benchmark/evaluation command. No product benchmark was run here. Expected named records with units, valid denominator and explicit modelled-versus-real outcome labels.
  - Completion criteria: all five metrics have a justified concrete SC/HYP pair somewhere across cohorts and each trace claim is reproducible; deferred cohorts retain real prerequisites.

- [ ] AUD-028-010 Align multilingual misinformation fallback with fail-closed ownership
  - Affected requirements/tasks: FR-006, T015; D-004 and inherited spec-010 FR-006/FR-007.
  - Expected versus observed and impact: spec 008 must inherit the named owner's hold/no-handoff rule, not invent an English-classifier fallback that could be interpreted as sufficient safety clearance.
  - Developer instructions: amend only the [008 deferred requirement](../008-communication-agent/spec.md#L365) and matching [US1 template](scripts/apply-us1-hardening.ps1#L208) to accurately reference [010's owner](../010-monitoring-agent/spec.md#L135). Distinguish classifier unavailability, low confidence, invalid output and language mismatch; hold for authorized review and do not auto-dispatch. Preserve the existing six-language AU contract and human approval boundary; runtime implementation is a separately authorized feature.
  - Tester instructions: use FV-01 alongside the existing static-reference test pattern. Fixtures: unavailable classifier, invalid response, unsupported locale, low confidence with apparently credible English fallback, and authorized human disposition. Assert no wording permits an automatic handoff while the safety check is unresolved; accepted content still uses the existing approval chain.
  - Future commands/prerequisites/results: FV-01 filter `fallback_contract` after agreement by communication/monitoring owners. Expected both documents specify the same fail-closed behavior; no production invocation required.
  - Completion criteria: exact ownership reference and failure semantics agree; no source change is represented as an already deployed multilingual capability.

- [ ] AUD-028-011 Keep language identifier selection genuinely deferred
  - Affected requirements/tasks: FR-006, D-004, T015, T034; clarification 2026-04-24 item 2.
  - Expected versus observed and impact: per-country non-English capability is required, but identifiers are to be selected later in owning research. Operative hypothesis and corpus prerequisites currently hard-code the supposedly undecided codes.
  - Developer instructions: own [008 language FR and hypotheses](../008-communication-agent/spec.md#L363), its three stubs, and both authoring templates. Use country/language placeholders in normative prerequisites or record an explicit approved identifier decision in owning research before making them binding. Preserve distinctions between Filipino/Tagalog, regional coverage and Bengali variants; illustrative contract examples are not an approval record.
  - Tester instructions: FV-01, existing text-reference pattern. Positive fixtures defer codes while naming all three countries and safety/back-translation checks; negatives hard-code a code only in a falsification corpus or stub; edge fixture contains an explicitly non-normative example. Assert normative code choices resolve to research decisions and examples are not counted as implemented choices.
  - Future commands/prerequisites/results: FV-01 filter `language_identifier`; prerequisites are owner-reviewed placeholder semantics or actual research decision evidence. Expected no undecided identifier is a mandatory test dependency.
  - Completion criteria: spec, stubs and generators all share the same decision state and preserve all three country hypotheses.

- [ ] AUD-028-012 Normalize reciprocal ownership rules without erasing supported pointers
  - Affected requirements/tasks: FR-016, FR-017, FR-018, FR-019, SC-006; canonical phrasing amendment; T008, T009, T013, T015, T018, T025, T044, T045, T046, T059.
  - Expected versus observed and impact: exact capability-matched owner/defer rules are required on both sides. Intent and 006's contract pointer exist, but split code spans, varying capability names and missing canonical owner lines defeat the promised verification.
  - Developer instructions: preserve [006 FR-024's pointer](../006-data-ingestion-storage/spec.md#L254), [008 supersession](../008-communication-agent/spec.md#L367), [001 DEF-015](../001-disaster-response-hub/spec.md#L479), [011 recovery](../011-resource-allocation-agent/spec.md#L357), [018 authority](../018-aidr-guidance-integration/spec.md#L342), and [027 replacement note](../027-spec-hardening/spec.md#L18). Add one canonical complete line per actual governed relationship, with matching capability strings inside the governed section. Bind 027/028 propagation authority explicitly; distinguish examples and generic conditional boilerplate from rules. Do not reopen unrelated recovery-product scope.
  - Tester instructions: FV-01 with the existing [bidirectional-reference tests](../../tests/contract/test_rag_optout_lint.py#L109) as pattern. Fixtures: valid pair, owner-only, defer-only, two authoritative owners, backtick-split token, quoted example, original 006 pointer retained, and 027 stale name. Assert exactly one owner and all real deferrers, not raw keyword counts.
  - Future commands/prerequisites/results: FV-01 filter `authority`; future T059 export after owner agreement. Expected canonical pairs resolve without changing the established 018 owner or non-warning timeout boundary.
  - Completion criteria: each enumerated overlap passes reciprocal semantic and exact-line checks, and original IDs/stale-name correction remain preserved.

- [ ] AUD-028-013 Resolve the closed-versus-dynamic population and author the removal proposal
  - Affected requirements/tasks: FR-001 through FR-005, FR-020, SC-001, SC-008; D-008, E-001, edge 6, unnumbered duplicate-removal obligation; T001, T007, T058, T066.
  - Expected versus observed and impact: a single complete population definition must govern authoring and validation. Closed 27 and literal 41 disagree; duplicate numeric folder prefixes cannot be collapsed safely; a separate promised stale-folder proposal is absent.
  - Developer instructions: obtain a spec-maintainer decision through the existing clarification/amendment process, naming exact folder identities and whether later specs inherit these rules. Update the agreed manifest, validator, local plan and future ownership policy together. Do not silently exempt 028 itself or conflate the two 001/036 folders. Author a separate removal proposal, clearly not a deletion, for the excluded historical feature duplicates; proposed path: `specs/028-capstone-alignment/evidence/feature-duplicates-removal-proposal.md`. Do not merge removal or alter those original specs as this remediation's side effect.
  - Tester instructions: FV-01 using the existing isolated inventory fixture pattern. Cover 27 named files, the additional 14, two same-prefix folders, a numbered folder with no spec, excluded shared/feature trees and a later owner explicitly deferring to 028. Assert exact selected identities and documented exclusions; verify proposal has affected paths, preserved-reference plan, risks and a separate approval boundary.
  - Future commands/prerequisites/results: FV-01 filter `population`, FV-02 after written scope decision; expected one unambiguous denominator without undocumented grandfathering.
  - Completion criteria: source requirements, closed partition, inventory and validator agree; all affected later artifacts are explicitly accounted for; proposal exists without any unauthorized removal.

- [ ] AUD-028-014 Correct closeout claims and retain actual review and execution evidence
  - Affected requirements/tasks: SC-003, SC-004, SC-005, SC-006, SC-007, SC-008; T001, T003, T006, T058, T059, T060, T061, T062, T062a, T063a, T064, T065, T066; actor-consultation lines and plan/checklist attestations.
  - Expected versus observed and impact: authored artifacts, test execution, consultation and approvals are distinct. The closure record remaps SC IDs and calls absent experiments/audits passed; it is not the required T065 decision/disposition record.
  - Developer instructions: maintain [decision record](evidence/decision-record.md#L1) as historical authored evidence with an explicit correction, not a fabricated replacement run. Reconcile each gate to the exact spec meaning. Recover authentic SQL/run artifacts where available, otherwise retain UNVERIFIED and schedule real future activity. T063a remains post-merge/non-blocking; no fake reviewer names or timings. Preserve review findings/dispositions and exact T065 branch decision only after T064 actually occurs. The absent audit paths named by the original tasks are required future outputs, not existing links.
  - Tester instructions: use FV-01 for evidence-metadata checks and FV-04 for authorized review activities. Fixtures: authored-only PASS claim, wrong SC meaning, missing run ID/SHA, incomplete critique dispositions, one/three independent reviewers, four/five specs each, 10-minute boundary, and a documented No answer. Assert unestablished outcomes stay unverified and post-merge deferral does not block merge.
  - Future commands/prerequisites/results: FV-04 after content remediation; FV-01 filter `evidence_provenance`. Future timing output uses `Reviewer | Spec | Minutes | Five-Qs-Answered? | Notes`, at least 15 actual observations and the resolved threshold from AUD-028-016. Expected authentic reviewer/run evidence or explicit remaining blockers.
  - Completion criteria: no unsupported all-gates-passed statement; every execution/review claim has a source record and every absent activity is honestly classified, including named actor consultations.

- [ ] AUD-028-015 Establish a comparable and reproducible rubric assessment
  - Affected requirements/tasks: SC-009, D-007, appended HYP-026; T002, T063.
  - Expected versus observed and impact: baseline and post snapshots must assess the same population against an approved mapping to the named rubric. Existing custom rows/scales and unsupported structural counts do not establish the claimed +2 uplift.
  - Developer instructions: preserve the [frozen baseline](evidence/rubric-baseline.md#L1) and [renamed post snapshot](evidence/rubric-postfeature.md#L1); append a provenance correction rather than retroactively rescore history. Have the maintainer define how the five feature dimensions map to actual [rubric rows](../../AMA_Rubric_Asia.md#L7) and [grader workflow](../../.github/skills/ama-rubric-grader/SKILL.md#L15). Record exact input SHA/population, method version, timestamp, run ID, rationales and bands for both comparable observations. If the historical baseline cannot be reproduced, leave the historical uplift UNVERIFIED and prospectively establish a new evaluation lane.
  - Tester instructions: FV-01 and future FV-04 grader run. Fixtures: five complete comparable criteria, missing criterion, mismatched input sets, synthetic run identifier without output, aggregate gain hiding a negative individual delta, +0.99 mean gain, and exactly +1 with zero individual regressions. Assert both composite conditions and provenance, not arithmetic alone.
  - Future commands/prerequisites/results: authorized `ama-rubric-grader` invocation only after the mapping/baseline decision; FV-01 filter `rubric`. Expected traceable scores and preserved historical uncertainty, never fabricated SME or execution evidence.
  - Completion criteria: accepted rubric mapping and two comparable verifiable snapshots support the claimed gate, or the report explicitly states that the historical gate remains unverified.

- [ ] AUD-028-016 Reconcile dependency, marker, and acceptance-test instructions
  - Affected requirements/tasks: FR-005a, FR-021, FR-022, SC-003, SC-004, SC-009; T007, T008, T009, T015, T016, T017, T018, T019, T022, T047, T048, T049, T050, T051, T052, T053, T054, T055, T056, T057, T058, T063a, T064, T065, T066.
  - Expected versus observed and impact: future developers/testers need coherent task IDs, discovery syntax, evidence predicates and ordering. Current instructions contain off-by-one references, a literal regex-anchor test, incompatible marker semantics, mismatched timing acceptance and parallel critique before its evidence dependencies.
  - Developer instructions: amend [tasks](tasks.md#L82), [quickstart](quickstart.md#L15), [plan](plan.md#L8), and the approved clarification section together. Preserve all original IDs and checkbox history; correct reference targets, give FR-005a an explicit execution owner, sequence T064 after its required evidence, and T065/T066 after real review. Decide how historical/quoted markers are retained and resolve `<10` versus `<=10`/80% explicitly. A narrowly documented authoring-tool exception must not authorize product code changes or retroactive approvals.
  - Tester instructions: FV-01 static docs tests plus PowerShell fixture checks patterned on the existing inventory tests. Cover every original task reference, self/cyclic dependency, a valid meta bullet with regex versus SimpleMatch, spec-only/research-only/task-only unresolved marker, historical resolved marker, exact 10 minutes and 79%/80% timing distributions. Assert rules match source rather than silently relaxing gates.
  - Future commands/prerequisites/results: FV-01 filter `handoff_contract`, FV-02 and future `/speckit.analyze` after approved amendments. Expected no unresolved HIGH/CRITICAL cross-artifact inconsistencies, all lesser findings dispositioned, and no false claim that grep proves experiments.
  - Completion criteria: all task links and gate definitions agree, sequential dependencies are valid, and both human and automated validation instructions are runnable against the intended scope.

- [ ] AUD-028-017 Define a measurable Japanese feed freshness prerequisite
  - Affected requirements/tasks: FR-009, T013, P-004; JMA FR-CAP-006-002 and monitoring HYP-034 dependency.
  - Expected versus observed and impact: every deferred candidate feed needs testable validation preconditions. JMA's 24x7 statement cannot distinguish a continuously available stale feed from fresh seismic alerts.
  - Developer instructions: update the owning [JMA candidate entry](../006-data-ingestion-storage/spec.md#L382) and [US1 source template](scripts/apply-us1-hardening.ps1#L196) with an owner-approved maximum source-data age, timestamp basis, assessment window and stale/absent-data handling. Keep availability, source freshness and processing latency separate; reference rather than invent licensing approval. Preserve PH/BD thresholds and deferred scope.
  - Tester instructions: FV-01 using the existing isolated text-contract patterns. Fixtures: 24x7-only statement, source age exactly at/above the chosen bound, missing or future source timestamp, stale-but-low-latency event, and a complete age/window/failure rule. Assert that availability or processing latency alone cannot satisfy the freshness field.
  - Future commands/prerequisites/results: FV-01 filter `feed_freshness` after feed-owner agreement on the bound and timestamp semantics; no live feed request needed. Expected all three country candidates have independently measurable prerequisites.
  - Completion criteria: JMA has a falsifiable freshness contract, both copies agree, and no future test confuses up-time with data age.

## Portfolio Artifact Accounting

Every row below was checked against its actual owner text, including original/retained sections and appended blocks. This is the artifact population required by 028, not an audit of each owner's runtime product. Codes: A = assumption taxonomy/mapping defect (AUD-028-003); P = persona shape/provenance defect (004); H = generic hypothesis/pack defect (005); O = missing country/hazard deferral or unmapped retained scope (006); U = AU-only citation work (007, only where effective FR scope is AU-only). All 27 named files have the four headings; none establishes all four content contracts. A broad actor catalogue pointer is not two specific schema-complete persona profiles.

| Owner artifact | Direct assumption/persona/hypothesis/scope evidence | Status and concrete content result | Follow-up |
| --- | --- | --- | --- |
| 001-disaster-response-hub | [A](../001-disaster-response-hub/spec.md#L98), [P](../001-disaster-response-hub/spec.md#L167), [H](../001-disaster-response-hub/spec.md#L435), [O](../001-disaster-response-hub/spec.md#L605) | PARTIAL: eight legacy table ASMs plus two untagged additions; detailed personas lack completed named reviews; six legacy packs retained; scope reference exists but no full taxonomy mapping. | AUD-028-002, AUD-028-003, AUD-028-004, AUD-028-006, AUD-028-007 |
| 003-rubric-gap-closure | [A/P](../003-rubric-gap-closure/spec.md#L255), [H/O](../003-rubric-gap-closure/spec.md#L271) | PARTIAL: three ASMs, only one tagged; three generic persona references; new HYP-001 collides with legacy meaning and has no pack; country deferral and meta bullet present. | AUD-028-002, AUD-028-003, AUD-028-004, AUD-028-005, AUD-028-007 |
| 004-actor-github-agents | [A/P](../004-actor-github-agents/spec.md#L157), [H/O](../004-actor-github-agents/spec.md#L173) | PARTIAL: three ASMs, one tagged; catalogue partly self-references; HYP-002 missing its own pack; PH/JP/BD deferral and meta bullet present. | AUD-028-002, AUD-028-003, AUD-028-004, AUD-028-005, AUD-028-007 |
| 005-data-source-governance | [A/P](../005-data-source-governance/spec.md#L203), [H/O/FR](../005-data-source-governance/spec.md#L220) | PARTIAL: four ASMs, two tagged including D-009; P/H defects; all four named privacy regimes and non-AU prerequisites are authored. | AUD-028-002, AUD-028-003, AUD-028-004, AUD-028-005, AUD-028-007 |
| 006-data-ingestion-storage | [legacy A/O](../006-data-ingestion-storage/spec.md#L305), [new sections/feeds](../006-data-ingestion-storage/spec.md#L345) | PARTIAL: four new ASMs, two tagged including D-009; unmapped retained H3 lists; P/H defects; three feed candidates, JMA freshness unbounded; FR-024 contract pointer present. | AUD-028-002, AUD-028-003, AUD-028-004, AUD-028-005, AUD-028-007, AUD-028-012, AUD-028-017 |
| 007-simulation-tenant-isolation | [all sections](../007-simulation-tenant-isolation/spec.md#L217) | PARTIAL: three ASMs, one tagged; P/H defects; three substantive scope items and canonical meta bullet present. | AUD-028-003, AUD-028-004, AUD-028-005, AUD-028-007 |
| 008-communication-agent | [A](../008-communication-agent/spec.md#L305), [P/H/O/country](../008-communication-agent/spec.md#L338) | PARTIAL: eleven retained untagged assumptions, no D-009 ASM; P/H defects; three valid country stubs; explicit language deferrals conflict with operative codes and fallback owner. | AUD-028-003, AUD-028-004, AUD-028-005, AUD-028-007, AUD-028-010, AUD-028-011, AUD-028-012 |
| 009-evacuation-agent | [all sections/country](../009-evacuation-agent/spec.md#L319) | PARTIAL: four ASMs, two tagged including D-009; generic P/H defects; three country hypotheses distinguish PH/BD pre-warning from JP immediate routing. | AUD-028-003, AUD-028-004, AUD-028-005, AUD-028-007 |
| 010-monitoring-agent | [A](../010-monitoring-agent/spec.md#L215), [P/H/O/country](../010-monitoring-agent/spec.md#L258) | PARTIAL: eight unmapped retained assumptions; required D-009 absent; P/H defects; three country monitoring hypotheses/stubs present. | AUD-028-003, AUD-028-004, AUD-028-005, AUD-028-007 |
| 011-resource-allocation-agent | [all sections/country](../011-resource-allocation-agent/spec.md#L324) | PARTIAL: three ASMs, one tagged; P/H defects; three logistics stubs and recovery deferral present. | AUD-028-003, AUD-028-004, AUD-028-005, AUD-028-007, AUD-028-012 |
| 012-risk-assessment-agent | [all sections/country](../012-risk-assessment-agent/spec.md#L310) | PARTIAL: three ASMs, one tagged; hazard table references an absent local RISK ASM; P/H defects; deferred hazard rows and three calibration stubs present. | AUD-028-003, AUD-028-004, AUD-028-005, AUD-028-007, AUD-028-009 |
| 013-root-readme | [A/O](../013-root-readme/spec.md#L187), [P/H](../013-root-readme/spec.md#L218) | PARTIAL: nine unmapped assumptions; P/H defects; ordinary exclusions and canonical meta bullet, but no explicit country/hazard promotion rule. | AUD-028-003, AUD-028-004, AUD-028-005, AUD-028-006, AUD-028-007 |
| 014-azure-openai-integration | [A/O](../014-azure-openai-integration/spec.md#L225), [P/H](../014-azure-openai-integration/spec.md#L275) | PARTIAL: eight unmapped assumptions; required D-009 absent; P/H/O/U defects. Later model-hosting carve-out is bounded, not a blanket replacement. | AUD-028-003, AUD-028-004, AUD-028-005, AUD-028-006, AUD-028-007 |
| 015-performance-benchmarks | [A/O](../015-performance-benchmarks/spec.md#L160), [P/H/SC](../015-performance-benchmarks/spec.md#L189) | PARTIAL: seven A-* assumptions lack mapping/tags; P/H/O defects; all five SC-CAP rows exist but lack concrete quantitative baseline records. | AUD-028-003, AUD-028-004, AUD-028-005, AUD-028-006, AUD-028-008, AUD-028-009 |
| 016-automated-demo-script | [all sections](../016-automated-demo-script/spec.md#L126) | PARTIAL: six unmapped assumptions; P/H defects; country deferral and canonical meta flag present. Simulated approvals are not human evidence. | AUD-028-003, AUD-028-004, AUD-028-005, AUD-028-007, AUD-028-014 |
| 017-cd-pipeline | [A](../017-cd-pipeline/spec.md#L149), [P/H/O/FR](../017-cd-pipeline/spec.md#L203) | PARTIAL: ten unmapped assumptions, required D-009 absent; P/H defects; additive region-per-country deferred FR and meta flag present. | AUD-028-003, AUD-028-004, AUD-028-005, AUD-028-007 |
| 018-aidr-guidance-integration | [A](../018-aidr-guidance-integration/spec.md#L284), [P/H/O/authority](../018-aidr-guidance-integration/spec.md#L317) | PARTIAL: seven unmapped assumptions; P/H defects; recovery and timeout authority intent present, canonical pairs incomplete. | AUD-028-003, AUD-028-004, AUD-028-005, AUD-028-007, AUD-028-012 |
| 019-aidr-additional-guidances | [A](../019-aidr-additional-guidances/spec.md#L211), [P/H/O](../019-aidr-additional-guidances/spec.md#L268) | PARTIAL: seven unmapped assumptions; P/H defects; explicit country deferral, no independent replacement of 018 authority. | AUD-028-003, AUD-028-004, AUD-028-005, AUD-028-007 |
| 020-disaster-mapper-ui | [A](../020-disaster-mapper-ui/spec.md#L200), [P/H/O](../020-disaster-mapper-ui/spec.md#L248) | PARTIAL: ten unmapped location/residency assumptions; P/H defects; country deferral present. | AUD-028-003, AUD-028-004, AUD-028-005, AUD-028-007 |
| 021-governance-dashboard | [all sections](../021-governance-dashboard/spec.md#L258) | PARTIAL: nine unmapped assumptions; P/H defects; identity-bearing audit scope needs D-009 assessment; country deferral present. | AUD-028-003, AUD-028-004, AUD-028-005, AUD-028-007 |
| 022-multi-jurisdiction-filter | [all sections/hierarchy](../022-multi-jurisdiction-filter/spec.md#L134) | PARTIAL: six unmapped assumptions; P/H defects; all nine AU nodes and three country placeholder nodes/prerequisites are preserved explicitly. | AUD-028-003, AUD-028-004, AUD-028-005, AUD-028-007 |
| 023-dashboard-real-data | [all sections](../023-dashboard-real-data/spec.md#L205) | PARTIAL: nine unmapped assumptions; P/H defects; country deferral present; no runtime-data verification inferred. | AUD-028-003, AUD-028-004, AUD-028-005, AUD-028-007 |
| 024-simulation-control-chat | [O](../024-simulation-control-chat/spec.md#L409), [A/P/H](../024-simulation-control-chat/spec.md#L432) | PARTIAL: three ASMs, one tagged; P/H defects; existing scope has no country/hazard prerequisite; canonical meta flag present. | AUD-028-003, AUD-028-004, AUD-028-005, AUD-028-006, AUD-028-007 |
| 025-agent-spec-compliance | [A](../025-agent-spec-compliance/spec.md#L223), [P/H/O](../025-agent-spec-compliance/spec.md#L266) | PARTIAL: seven unmapped assumptions; P/H defects; country deferral and canonical meta flag present. | AUD-028-003, AUD-028-004, AUD-028-005, AUD-028-007 |
| 026-sim-warp-playback | [all sections](../026-sim-warp-playback/spec.md#L173) | PARTIAL: eight unmapped assumptions; P/H defects; SCP-080/081 collide with 001 additions; country deferral and meta flag present. | AUD-028-002, AUD-028-003, AUD-028-004, AUD-028-005 |
| 027-spec-hardening | [replacement](../027-spec-hardening/spec.md#L18), [all added sections](../027-spec-hardening/spec.md#L257) | PARTIAL: two untagged assumptions, one persona pointer, HYP-025 pack absent, no country deferral; stale-name fix and meta flag supported. | AUD-028-003, AUD-028-004, AUD-028-005, AUD-028-006, AUD-028-012 |
| 028-capstone-alignment | [A](spec.md#L182), [O](spec.md#L209), [P/H](spec.md#L240) | PARTIAL: ten tagged but unallocated assumptions; generic persona blocks; missing HYP-026 pack; no self-exemption from content rules; meta flag present. | AUD-028-002, AUD-028-003, AUD-028-004, AUD-028-005, AUD-028-006, AUD-028-013 |

### Additional Literal-Scope Population

These fourteen files are outside D-008's closed partition but inside FR-001's current path rule. All were included in full-file heading/ID/citation searches and applicable section inspection. None is called historically undelivered by 028 merely because it was authored later. Their status against the disputed 028 contract is CONFLICT pending AUD-028-013. No new runtime audit is implied.

| Artifact | Direct text evidence | Current 028 content result | Follow-up |
| --- | --- | --- | --- |
| 001-arch-docs-refresh | [Assumptions](../001-arch-docs-refresh/spec.md#L253) | CONFLICT: ordinary assumptions; no required Personas/Hypotheses/Out-of-Scope H2 set. Numeric 001 is not the disaster-hub artifact. | AUD-028-013 |
| 029-progressive-delivery-pipeline | [Assumptions/constraints](../029-progressive-delivery-pipeline/spec.md#L292) | CONFLICT: no Personas/Hypotheses/Out-of-Scope H2 set; Foundry carve-out is not a 028 taxonomy replacement. | AUD-028-013 |
| 030-llm-eval-framework | [Assumptions/scope](../030-llm-eval-framework/spec.md#L209) | CONFLICT: assumptions and ordinary exclusions, no Personas/Hypotheses H2s or country promotion rule. | AUD-028-013 |
| 031-simplify-cicd-pipeline | [Assumptions/scope](../031-simplify-cicd-pipeline/spec.md#L194) | CONFLICT: no Personas/Hypotheses H2s; retirement of another pipeline design does not retire 028. | AUD-028-013 |
| 032-rubric-improvements | [Assumptions](../032-rubric-improvements/spec.md#L344) | CONFLICT: no required Personas/Hypotheses/Out-of-Scope H2 set. | AUD-028-013 |
| 033-maf-adoption | [Assumptions/scope](../033-maf-adoption/spec.md#L180) | CONFLICT: no Personas/Hypotheses H2s; ordinary exclusions do not provide capstone-country prerequisites. | AUD-028-013 |
| 034-webapp-capstone-coverage | [A/H/O](../034-webapp-capstone-coverage/spec.md#L1015), [authority](../034-webapp-capstone-coverage/spec.md#L1096) | CONFLICT: untagged local ASM-001 meanings and three HYP IDs without co-located 028 packs; no Personas H2; explicit 028 deferral is retained, not supersession. | AUD-028-013, AUD-028-002 |
| 035-webapp-capstone-closure | [A/O](../035-webapp-capstone-closure/spec.md#L239) | CONFLICT: ten untagged local ASMs, no Personas/Hypotheses H2s; Asia explicitly deferred via 034/028. | AUD-028-013, AUD-028-002 |
| 036-foundry-rag-grounding | [A/O](../036-foundry-rag-grounding/spec.md#L425) | CONFLICT: twelve A* assumptions, ordinary scope exclusions, no Personas/Hypotheses H2s. | AUD-028-013 |
| 036-sim-agent-extend | [H3 assumptions](../036-sim-agent-extend/spec.md#L1658) | CONFLICT: all four exact required H2s absent; twelve untagged H3 assumptions. Cohort syntheses are not persona-schema evidence. | AUD-028-013 |
| 037-capstone-evidence-pack | [A/O/dependency](../037-capstone-evidence-pack/spec.md#L201) | CONFLICT: no Personas/Hypotheses H2s; names 028's flag contract but adds a separate table to the single-table trace. | AUD-028-013, AUD-028-008 |
| 038-help-docs-chat | [A/O](../038-help-docs-chat/spec.md#L296) | CONFLICT: no Personas/Hypotheses H2s; tenant/persona model reuse is not two contract-complete persona references. | AUD-028-013 |
| 039-test-data-provisioning | [Assumptions](../039-test-data-provisioning/spec.md#L227) | CONFLICT: twenty A-* assumptions; no Personas/Hypotheses/Out-of-Scope H2 set; scope exclusions embedded in assumptions. | AUD-028-013 |
| 040-success-criteria | [A/qualified O heading](../040-success-criteria/spec.md#L283) | CONFLICT: no Personas/Hypotheses H2s; qualified Out-of-Scope heading fails current exact matcher; modelled outcomes expressly distinguished from real outcomes. | AUD-028-013 |

### Country Hypothesis Population

All fifteen files were read completely: each has the same six required H2s in order, three prerequisite bullets, named window, quantified falsification, literal `Not tested`, and an owning-spec reference. IMPLEMENTED below describes authored hypothesis/stub content, never an observed experiment or approval. Every stub also points to missing HYP-026 and uses a generic ASM reference rather than a specific assumption ID; resolve via AUD-028-002/005. The separate generic authoring hypothesis in each agent still fails FR-004.

| Hypothesis | Owner statement and complete stub | Content status | Cohort-specific assertion | Follow-up |
| --- | --- | --- | --- | --- |
| HYP-027 | [008 statement](../008-communication-agent/spec.md#L374), [stub](../008-communication-agent/evidence/HYP-027.md#L1) | PARTIAL | PH misinformation/delivery, Jun-Nov, true-positive <70%; operative `fil-PH` contradicts identifier deferral. | AUD-028-011 |
| HYP-028 | [008 statement](../008-communication-agent/spec.md#L377), [stub](../008-communication-agent/evidence/HYP-028.md#L1) | PARTIAL | JP quarterly, true-positive <70% or p95 delivery >10s; operative `ja-JP` unresolved. | AUD-028-011 |
| HYP-029 | [008 statement](../008-communication-agent/spec.md#L380), [stub](../008-communication-agent/evidence/HYP-029.md#L1) | PARTIAL | BD Apr-Sep, true-positive <65%; operative `bn-BD` unresolved. | AUD-028-011 |
| HYP-030 | [009 statement](../009-evacuation-agent/spec.md#L355), [stub](../009-evacuation-agent/evidence/HYP-030.md#L1) | IMPLEMENTED | PH pre-warned >=24h benefit; <12h falsifies; topology/tabletop/D-009 prerequisites. | AUD-028-005 |
| HYP-031 | [009 statement](../009-evacuation-agent/spec.md#L358), [stub](../009-evacuation-agent/evidence/HYP-031.md#L1) | IMPLEMENTED | JP immediate first recommendation <=60s; p95 >120s falsifies; not a 24h predictive metric. | AUD-028-005, AUD-028-009 |
| HYP-032 | [009 statement](../009-evacuation-agent/spec.md#L361), [stub](../009-evacuation-agent/evidence/HYP-032.md#L1) | IMPLEMENTED | BD pre-warning >=24h, <12h falsifies; shelter/topology/exercise prerequisites. | AUD-028-005 |
| HYP-033 | [010 statement](../010-monitoring-agent/spec.md#L285), [stub](../010-monitoring-agent/evidence/HYP-033.md#L1) | IMPLEMENTED | PH availability <95% or p95 alert >10min falsifies during named typhoon season. | AUD-028-005 |
| HYP-034 | [010 statement](../010-monitoring-agent/spec.md#L288), [stub](../010-monitoring-agent/evidence/HYP-034.md#L1) | IMPLEMENTED | JP seismic event-to-alert p95 >60s falsifies quarterly; separate from source-data age. | AUD-028-005, AUD-028-017 |
| HYP-035 | [010 statement](../010-monitoring-agent/spec.md#L291), [stub](../010-monitoring-agent/evidence/HYP-035.md#L1) | IMPLEMENTED | BD availability <95% falsifies during monsoon; BWDB/validator/D-009 prerequisites. | AUD-028-005 |
| HYP-036 | [011 statement](../011-resource-allocation-agent/spec.md#L364), [stub](../011-resource-allocation-agent/evidence/HYP-036.md#L1) | IMPLEMENTED | PH archipelagic logistics >=30% benefit; <15% falsifies in typhoon window. | AUD-028-005 |
| HYP-037 | [011 statement](../011-resource-allocation-agent/spec.md#L367), [stub](../011-resource-allocation-agent/evidence/HYP-037.md#L1) | IMPLEMENTED | JP urban rail/road logistics >=30%; <15% falsifies quarterly. | AUD-028-005 |
| HYP-038 | [011 statement](../011-resource-allocation-agent/spec.md#L370), [stub](../011-resource-allocation-agent/evidence/HYP-038.md#L1) | IMPLEMENTED | BD deltaic logistics >=30%; <15% falsifies during monsoon. | AUD-028-005 |
| HYP-039 | [012 statement](../012-risk-assessment-agent/spec.md#L358), [stub](../012-risk-assessment-agent/evidence/HYP-039.md#L1) | IMPLEMENTED | PH calibration error >25% falsifies; >=10 held-out events prerequisite; not economic loss. | AUD-028-005, AUD-028-009 |
| HYP-040 | [012 statement](../012-risk-assessment-agent/spec.md#L361), [stub](../012-risk-assessment-agent/evidence/HYP-040.md#L1) | IMPLEMENTED | JP calibration error >20% falsifies quarterly; held-out event corpus prerequisite. | AUD-028-005, AUD-028-009 |
| HYP-041 | [012 statement](../012-risk-assessment-agent/spec.md#L364), [stub](../012-risk-assessment-agent/evidence/HYP-041.md#L1) | IMPLEMENTED | BD calibration error >30% falsifies during monsoon; held-out corpus prerequisite. | AUD-028-005, AUD-028-009 |

The six legacy packs were also read in full: [HYP-001](../001-disaster-response-hub/evidence/HYP-001.md#L1), [HYP-002](../001-disaster-response-hub/evidence/HYP-002.md#L1), [HYP-003](../001-disaster-response-hub/evidence/HYP-003.md#L1), [HYP-004](../001-disaster-response-hub/evidence/HYP-004.md#L1), [HYP-005](../001-disaster-response-hub/evidence/HYP-005.md#L1), [HYP-006](../001-disaster-response-hub/evidence/HYP-006.md#L1). Their authored templates are IMPLEMENTED; actual experiments and named signatures are UNVERIFIED. [The post snapshot's carry-over](evidence/rubric-postfeature.md#L51) explicitly excludes conversion of these older packs; this does not waive creation of the 26 new packs or make legacy packs replacement evidence for reused IDs.

## Original Task Coverage

Exactly 68 original task definitions, including T062a and T063a; every original checkbox is `[ ]`. No original task lacks a checkbox. IMPLEMENTED means the specified authored artifact is supported by source, not that named actors actually consulted, commands ran, or humans approved. Process-only tasks stay UNVERIFIED where records are absent. Actor-consultation provenance for per-owner tasks is separately assessed by AUD-028-014; a label naming an agent is not evidence of consultation.

| Original task | Original checkbox | Status | Direct evidence and assessment | Follow-up |
| --- | --- | --- | --- | --- |
| T001 | [ ] | UNVERIFIED | [Task](tasks.md#L27) requires persistent SQL inventory; [baseline](evidence/rubric-baseline.md#L5) claims it but no export/run record was found (NEG-01). Current text inventory is 41, not proof of that session. | AUD-028-013, AUD-028-014 |
| T002 | [ ] | CONFLICT | [Baseline](evidence/rubric-baseline.md#L11) has scores/run label but contradictory counts and unmapped rubric criteria; historical grading not established. | AUD-028-015 |
| T003 | [ ] | CONFLICT | [Zero watermark claim](../shared/gap-id-register.md#L69) conflicts with [pre-existing ASMs](../001-disaster-response-hub/spec.md#L103); SQL session remains unverified. | AUD-028-002, AUD-028-014 |
| T004 | [ ] | PARTIAL | [Trace](../shared/capstone-metric-trace.md#L9) contains 20 unique pairs, but wrong column order/owner forms and extra table; original skeleton execution unverified. | AUD-028-008 |
| T005 | [ ] | CONFLICT | [Allocation block](../shared/gap-id-register.md#L62) exists and register diff is additive, but starting watermarks and per-entry ownership are wrong. | AUD-028-002 |
| T006 | [ ] | IMPLEMENTED | Local [evidence](evidence/decision-record.md#L1) and all five agent folders contain files: [008](../008-communication-agent/evidence/HYP-027.md#L1), [009](../009-evacuation-agent/evidence/HYP-030.md#L1), [010](../010-monitoring-agent/evidence/HYP-033.md#L1), [011](../011-resource-allocation-agent/evidence/HYP-036.md#L1), [012](../012-risk-assessment-agent/evidence/HYP-039.md#L1). Creation order not inferred. | - |
| T007 | [ ] | IMPLEMENTED | [CSV helper](scripts/validate-section-coverage.ps1#L33) implements the requested narrow heading/marker inventory. Its execution is not established and it cannot satisfy the stronger content gates. | AUD-028-001 |
| T008 | [ ] | PARTIAL | [001 additions](../001-disaster-response-hub/spec.md#L598), [DEF-015](../001-disaster-response-hub/spec.md#L479) and country preconditions exist; two bare ASMs/unmapped scope and reused SCP IDs remain. | AUD-028-002, AUD-028-003, AUD-028-004, AUD-028-006, AUD-028-012 |
| T009 | [ ] | PARTIAL | [027 replacement note](../027-spec-hardening/spec.md#L18) is implemented; [added sections](../027-spec-hardening/spec.md#L257) have two bare ASMs, one persona, missing HYP-025 pack and no country deferral. | AUD-028-003, AUD-028-004, AUD-028-005, AUD-028-006, AUD-028-012 |
| T010 | [ ] | PARTIAL | [003](../003-rubric-gap-closure/spec.md#L255) has headings/scope/meta, but bare ASMs, generic personas and missing HYP-001 pack. | AUD-028-002, AUD-028-003, AUD-028-004, AUD-028-005 |
| T011 | [ ] | PARTIAL | [004](../004-actor-github-agents/spec.md#L157) explicitly defers PH/JP/BD; A/P/H content contracts remain incomplete. | AUD-028-003, AUD-028-004, AUD-028-005 |
| T012 | [ ] | PARTIAL | [005 risk and regimes](../005-data-source-governance/spec.md#L207) provide D-009 and all four laws; generic assumptions/personas/pack still fail hardening. | AUD-028-003, AUD-028-004, AUD-028-005 |
| T013 | [ ] | PARTIAL | [006 additions](../006-data-ingestion-storage/spec.md#L345) include risk and all three feeds; JMA age limit, mappings and generic pack are incomplete. | AUD-028-003, AUD-028-004, AUD-028-005, AUD-028-017 |
| T014 | [ ] | PARTIAL | [007](../007-simulation-tenant-isolation/spec.md#L217) preserves deferral/meta, but three ASMs have one tag and P/H are incomplete. | AUD-028-003, AUD-028-004, AUD-028-005 |
| T015 | [ ] | PARTIAL | [008 language/fallback/timeout](../008-communication-agent/spec.md#L363) exists; inherited fallback is misstated and supposedly deferred codes are operative. | AUD-028-003, AUD-028-004, AUD-028-005, AUD-028-010, AUD-028-011, AUD-028-012 |
| T016 | [ ] | PARTIAL | [009](../009-evacuation-agent/spec.md#L319) adds D-009 and country scope; generic A/P/H defects remain despite valid country stubs. | AUD-028-003, AUD-028-004, AUD-028-005 |
| T017 | [ ] | PARTIAL | [010 assumptions](../010-monitoring-agent/spec.md#L215) remain unmapped with no required risk; [generic pack pointer](../010-monitoring-agent/spec.md#L270) is broken. | AUD-028-003, AUD-028-004, AUD-028-005 |
| T018 | [ ] | PARTIAL | [011](../011-resource-allocation-agent/spec.md#L324) has recovery pointer and country scope; A/P/H and exact canonical rules incomplete. | AUD-028-003, AUD-028-004, AUD-028-005, AUD-028-012 |
| T019 | [ ] | PARTIAL | [012 hazard additions](../012-risk-assessment-agent/spec.md#L341) preserve country-deferred instances, but reference a missing RISK ASM; generic A/P/H defects remain. | AUD-028-003, AUD-028-004, AUD-028-005 |
| T020 | [ ] | PARTIAL | [013](../013-root-readme/spec.md#L187) retains unmapped assumptions/no country deferral; persona/hypothesis sections exist, contrary to rejected delegated summary. | AUD-028-003, AUD-028-004, AUD-028-005, AUD-028-006 |
| T021 | [ ] | PARTIAL | [014](../014-azure-openai-integration/spec.md#L225) lacks D-009 risk and country deferral; [P/H sections](../014-azure-openai-integration/spec.md#L275) do exist but are incomplete. | AUD-028-003, AUD-028-004, AUD-028-005, AUD-028-006 |
| T022 | [ ] | PARTIAL | [015 SC-CAP rows](../015-performance-benchmarks/spec.md#L208) cover five metric labels, but not concrete quantitative baseline records; A/P/H/O defects persist. | AUD-028-003, AUD-028-004, AUD-028-005, AUD-028-006, AUD-028-009 |
| T023 | [ ] | PARTIAL | [016](../016-automated-demo-script/spec.md#L126) has ordinary assumptions and generic P/H; country deferral/meta preserved. | AUD-028-003, AUD-028-004, AUD-028-005 |
| T024 | [ ] | PARTIAL | [017](../017-cd-pipeline/spec.md#L149) lacks required risk; [deferred topology](../017-cd-pipeline/spec.md#L231) exists, not a deployment record. | AUD-028-003, AUD-028-004, AUD-028-005 |
| T025 | [ ] | PARTIAL | [018 authority](../018-aidr-guidance-integration/spec.md#L342) is stated, but A/P/H and canonical governed-section pairs remain incomplete. | AUD-028-003, AUD-028-004, AUD-028-005, AUD-028-012 |
| T026 | [ ] | PARTIAL | [019](../019-aidr-additional-guidances/spec.md#L211) retains seven unmapped assumptions and generic P/H; country deferral supported. | AUD-028-003, AUD-028-004, AUD-028-005 |
| T027 | [ ] | PARTIAL | [020](../020-disaster-mapper-ui/spec.md#L200) retains untagged location assumptions; generic P/H incomplete; country scope exists. | AUD-028-003, AUD-028-004, AUD-028-005 |
| T028 | [ ] | PARTIAL | [021](../021-governance-dashboard/spec.md#L258) retains unmapped identity/audit assumptions; generic P/H incomplete. | AUD-028-003, AUD-028-004, AUD-028-005 |
| T029 | [ ] | PARTIAL | [022 hierarchy](../022-multi-jurisdiction-filter/spec.md#L180) preserves nine AU nodes plus three placeholders; [legacy A/P/H](../022-multi-jurisdiction-filter/spec.md#L134) incomplete. | AUD-028-003, AUD-028-004, AUD-028-005 |
| T030 | [ ] | PARTIAL | [023](../023-dashboard-real-data/spec.md#L205) has nine unmapped assumptions, generic P/H, explicit country scope. | AUD-028-003, AUD-028-004, AUD-028-005 |
| T031 | [ ] | PARTIAL | [024](../024-simulation-control-chat/spec.md#L409) has meta flag but no country promotion rule; A/P/H incomplete. | AUD-028-003, AUD-028-004, AUD-028-005, AUD-028-006 |
| T032 | [ ] | PARTIAL | [025](../025-agent-spec-compliance/spec.md#L223) retains unmapped assumptions and generic P/H; meta/country scope present. | AUD-028-003, AUD-028-004, AUD-028-005 |
| T033 | [ ] | PARTIAL | [026](../026-sim-warp-playback/spec.md#L173) has eight unmapped assumptions/generic P/H and reused scope IDs; meta/country scope present. | AUD-028-002, AUD-028-003, AUD-028-004, AUD-028-005 |
| T034 | [ ] | PARTIAL | [008 country statements](../008-communication-agent/spec.md#L374) and all three stubs are structurally authored; operative codes violate deferred identifier choice. | AUD-028-011, AUD-028-014 |
| T035 | [ ] | IMPLEMENTED | [009 statements](../009-evacuation-agent/spec.md#L355), [PH](../009-evacuation-agent/evidence/HYP-030.md#L1), [JP](../009-evacuation-agent/evidence/HYP-031.md#L1), [BD](../009-evacuation-agent/evidence/HYP-032.md#L1) implement the three requested authored tests. Consultation/execution unverified. | AUD-028-014 |
| T036 | [ ] | IMPLEMENTED | [010 statements](../010-monitoring-agent/spec.md#L285), [PH](../010-monitoring-agent/evidence/HYP-033.md#L1), [JP](../010-monitoring-agent/evidence/HYP-034.md#L1), [BD](../010-monitoring-agent/evidence/HYP-035.md#L1) define the requested feed/latency hypotheses. | AUD-028-014 |
| T037 | [ ] | IMPLEMENTED | [011 statements](../011-resource-allocation-agent/spec.md#L364), [PH](../011-resource-allocation-agent/evidence/HYP-036.md#L1), [JP](../011-resource-allocation-agent/evidence/HYP-037.md#L1), [BD](../011-resource-allocation-agent/evidence/HYP-038.md#L1) define 30% topology-specific logistics hypotheses. | AUD-028-014 |
| T038 | [ ] | IMPLEMENTED | [012 statements](../012-risk-assessment-agent/spec.md#L358), [PH](../012-risk-assessment-agent/evidence/HYP-039.md#L1), [JP](../012-risk-assessment-agent/evidence/HYP-040.md#L1), [BD](../012-risk-assessment-agent/evidence/HYP-041.md#L1) define quantified calibration hypotheses. | AUD-028-014 |
| T039 | [ ] | PARTIAL | [Lives rows](../shared/capstone-metric-trace.md#L11) exist, but aggregate proxies do not supply the required annual lives HYP/baseline; owner grammar wrong. | AUD-028-008, AUD-028-009 |
| T040 | [ ] | PARTIAL | [Response rows](../shared/capstone-metric-trace.md#L15) cite relevant 001 owners and country hypotheses; owner formatting/baseline prerequisites incomplete. | AUD-028-008, AUD-028-009 |
| T041 | [ ] | PARTIAL | [Evacuation rows](../shared/capstone-metric-trace.md#L19) cite relevant AU/PH/BD hypotheses; JP is immediate routing, not 24h benefit; schema incomplete. | AUD-028-008, AUD-028-009 |
| T042 | [ ] | PARTIAL | [Logistics rows](../shared/capstone-metric-trace.md#L23) cite genuine related hypotheses but lack schema-conformant owners and quantitative baselines. | AUD-028-008, AUD-028-009 |
| T043 | [ ] | CONFLICT | [Economic rows](../shared/capstone-metric-trace.md#L27) mark AU Validated with no HYP ID; country risk-calibration stubs do not assert economic loss reduction. | AUD-028-008, AUD-028-009 |
| T044 | [ ] | PARTIAL | [006 FR-024](../006-data-ingestion-storage/spec.md#L254) is a retained contract pointer; [008 supersession](../008-communication-agent/spec.md#L367) exists. Exact canonical owner/pair grammar still fails. | AUD-028-012 |
| T045 | [ ] | PARTIAL | [008 deferral](../008-communication-agent/spec.md#L366) and [018 authority](../018-aidr-guidance-integration/spec.md#L343) exist; capability phrasing/complete-line placement differs. | AUD-028-012 |
| T046 | [ ] | PARTIAL | [001](../001-disaster-response-hub/spec.md#L479), [011](../011-resource-allocation-agent/spec.md#L357), [018](../018-aidr-guidance-integration/spec.md#L342) establish one intended recovery owner; exact canonical and non-example checks incomplete. | AUD-028-012 |
| T047 | [ ] | IMPLEMENTED | [003 canonical meta bullet](../003-rubric-gap-closure/spec.md#L279), once within Out of Scope, concrete supported-spec list. | - |
| T048 | [ ] | IMPLEMENTED | [004 canonical meta bullet](../004-actor-github-agents/spec.md#L181), once within Out of Scope. | - |
| T049 | [ ] | IMPLEMENTED | [007 canonical meta bullet](../007-simulation-tenant-isolation/spec.md#L241), once, concrete supported-spec list. | - |
| T050 | [ ] | IMPLEMENTED | [013 canonical meta bullet](../013-root-readme/spec.md#L208), once within retained Out of Scope. | - |
| T051 | [ ] | IMPLEMENTED | [016 canonical meta bullet](../016-automated-demo-script/spec.md#L165), once, concrete list. | - |
| T052 | [ ] | IMPLEMENTED | [017 canonical meta bullet](../017-cd-pipeline/spec.md#L219), once within Out of Scope. | - |
| T053 | [ ] | IMPLEMENTED | [024 canonical meta bullet](../024-simulation-control-chat/spec.md#L411), once within retained Out of Scope. | - |
| T054 | [ ] | IMPLEMENTED | [025 canonical meta bullet](../025-agent-spec-compliance/spec.md#L282), once within Out of Scope. | - |
| T055 | [ ] | IMPLEMENTED | [026 canonical meta bullet](../026-sim-warp-playback/spec.md#L201), once, concrete list. | - |
| T056 | [ ] | IMPLEMENTED | [027 canonical meta bullet](../027-spec-hardening/spec.md#L276), once, concrete list. | - |
| T057 | [ ] | IMPLEMENTED | [028 canonical meta bullet](spec.md#L211), once, complete critical-path set. | - |
| T058 | [ ] | UNVERIFIED | [Validator source](scripts/validate-section-coverage.ps1#L35) exists; requested CSV absent (NEG-01); [claimed result](evidence/decision-record.md#L26) does not establish execution/content conformance. | AUD-028-001, AUD-028-014 |
| T059 | [ ] | UNVERIFIED | [Authority source](../018-aidr-guidance-integration/spec.md#L342) supplies intent, but requested line-numbered audit file absent and canonical pairs incomplete. | AUD-028-012, AUD-028-014 |
| T060 | [ ] | CONFLICT | Read-only historical diff confirms 14 register additions and no deletions, but [zero watermark](../shared/gap-id-register.md#L69) is false; requested saved diff absent. | AUD-028-002, AUD-028-014 |
| T061 | [ ] | CONFLICT | [Stored trace](../shared/capstone-metric-trace.md#L9) fails owner/column rules; no metric-trace audit output found. | AUD-028-008, AUD-028-009, AUD-028-014 |
| T062 | [ ] | PARTIAL | All fifteen [country packs](../008-communication-agent/evidence/HYP-027.md#L1) were directly inventoried/read, with individual rows above; requested per-pack audit absent. | AUD-028-014 |
| T062a | [ ] | PARTIAL | All 25 added non-AU persona bullets carry placeholder prose, e.g. [028](spec.md#L246), but no required YAML/list representation or saved per-persona audit. | AUD-028-004, AUD-028-014 |
| T063 | [ ] | CONFLICT | Real renamed [post snapshot](evidence/rubric-postfeature.md#L1) has correct arithmetic but custom unmapped grading/provenance and wrong layout. | AUD-028-015 |
| T063a | [ ] | UNVERIFIED | [Explicit post-merge deferral](spec.md#L201) is supported; no actual >=3-reviewer, >=15-observation record. Non-blocking, not passed. | AUD-028-014, AUD-028-016 |
| T064 | [ ] | UNVERIFIED | [Closeout note](evidence/decision-record.md#L40) calls critique optional without an amendment; no critique findings/dispositions report found. | AUD-028-014, AUD-028-016 |
| T065 | [ ] | CONFLICT | [Differently named decision record](evidence/decision-record.md#L1) exists, but not either required first-line decision or T064 dispositions/diff. | AUD-028-014, AUD-028-016 |
| T066 | [ ] | UNVERIFIED | [Required analysis](tasks.md#L401) has no report, while gate/scope/dependency conflicts remain visible in source. This audit did not run that agent. | AUD-028-013, AUD-028-014, AUD-028-016 |

## Numbered Requirement Coverage

Exactly 24 FR definitions (including FR-005a), zero separately numbered NFR definitions, and nine SC definitions. Supplemental nonfunctional, entity, scope and amendment constraints are accounted for separately below.

| Requirement | Status | Direct evidence and assessment | Follow-up |
| --- | --- | --- | --- |
| FR-001 | PARTIAL | [Definition](spec.md#L114); 27 headings exist, but population table shows untagged/unmapped assumptions and [027 only two](../027-spec-hardening/spec.md#L261). | AUD-028-002, AUD-028-003, AUD-028-013 |
| FR-002 | PARTIAL | [Definition](spec.md#L115); country deferrals exist widely, but [013](../013-root-readme/spec.md#L206), 014/015/024/027 and mapping gaps remain. | AUD-028-006, AUD-028-013 |
| FR-003 | PARTIAL | [Definition](spec.md#L116), [persona contract](../027-spec-hardening/contracts/persona-profile.md#L5); generic catalogue pointers lack fields; 027 has one. | AUD-028-004 |
| FR-004 | PARTIAL | [Definition](spec.md#L117); fifteen valid country stubs coexist with [26 new generic claims without packs](scripts/apply-us1-hardening.ps1#L124). | AUD-028-005 |
| FR-005 | MISSING | [Required mappings](spec.md#L118); full scoped section/search inventory finds no required legacy-to-001 taxonomy-mapping rows; retained lists and template references are not mappings. | AUD-028-003, AUD-028-004, AUD-028-006 |
| FR-005a | MISSING | [Inline rule](spec.md#L119); zero concrete citations across all 41 files (NEG-03), despite definite [014 AU FRs](../014-azure-openai-integration/spec.md#L192). | AUD-028-007 |
| FR-006 | PARTIAL | [008 FR-CAP](../008-communication-agent/spec.md#L363) names all three language packs/preconditions; fallback-owner conflict and operative identifier selection remain. | AUD-028-010, AUD-028-011 |
| FR-007 | IMPLEMENTED | [005 country regimes](../005-data-source-governance/spec.md#L239) name AU/JP/PH/BD laws with non-AU deferral/preconditions. Authored text only, not legal approval. | - |
| FR-008 | IMPLEMENTED | [022 hierarchy](../022-multi-jurisdiction-filter/spec.md#L180) explicitly preserves nine AU jurisdictions and adds PH/JP/BD placeholders with conditions. | - |
| FR-009 | IMPLEMENTED | [006 three candidates](../006-data-ingestion-storage/spec.md#L381) name feeds and validation preconditions. T013's stronger quantified-freshness obligation remains partial. | AUD-028-017 |
| FR-010 | IMPLEMENTED | [017 deferred topology FR](../017-cd-pipeline/spec.md#L231) preserves AU default and external decision ownership; no deployment claim established. | - |
| FR-011 | IMPLEMENTED | All five agents have three country hypotheses and literal Not tested stubs, individually accounted above, e.g. [008](../008-communication-agent/spec.md#L370) and [012](../012-risk-assessment-agent/spec.md#L354). | AUD-028-011 |
| FR-012 | PARTIAL | [015 five SC additions](../015-performance-benchmarks/spec.md#L208) exist; [economic AU HYP absent](../shared/capstone-metric-trace.md#L27); baseline/semantic ownership gaps persist. | AUD-028-009 |
| FR-013 | CONFLICT | [Required shape](spec.md#L133) versus [stored trace](../shared/capstone-metric-trace.md#L9): wrong columns/owner grammar and second table, despite correct 20-pair cardinality. | AUD-028-008 |
| FR-014 | CONFLICT | [Allocations](../shared/gap-id-register.md#L62) reuse prior IDs, omit per-entry mappings and leave REQ unused. | AUD-028-002 |
| FR-015 | PARTIAL | [Six-heading rule](spec.md#L135); fifteen of 41 newly authored hypotheses have packs; 26 generic packs absent (NEG-02). | AUD-028-005 |
| FR-016 | PARTIAL | [006 contract pointer](../006-data-ingestion-storage/spec.md#L254) and [008 supersession](../008-communication-agent/spec.md#L367) supported; appended canonical owner line absent. | AUD-028-012 |
| FR-017 | PARTIAL | [008](../008-communication-agent/spec.md#L366)/[018](../018-aidr-guidance-integration/spec.md#L343) document intent but not the exact canonical matched rule. | AUD-028-012 |
| FR-018 | PARTIAL | [001 DEF-015](../001-disaster-response-hub/spec.md#L479), [011](../011-resource-allocation-agent/spec.md#L357), [018](../018-aidr-guidance-integration/spec.md#L342) establish intended sole authority; canonical syntax incomplete. | AUD-028-012 |
| FR-019 | IMPLEMENTED | [027 lines 18/20](../027-spec-hardening/spec.md#L18) replace stale feature name and retain the limited-scope note. Separate canonical-pair amendment remains partial. | AUD-028-012 |
| FR-020 | IMPLEMENTED | Exactly 11 canonical bullets in the required set, individually linked in T047-T057 coverage; [self flag](spec.md#L211) matches critical-path complement. | - |
| FR-021 | CONFLICT | [Zero-marker rule](spec.md#L167) conflicts with quoted history/examples and narrower [validator](scripts/validate-section-coverage.ps1#L46); not proof of unresolved decisions. | AUD-028-001, AUD-028-016 |
| FR-022 | PARTIAL | [Register append](../shared/gap-id-register.md#L62) is historically +14/-0, and names are preserved; reused identities undermine preservation and generator/tooling exceptions are not reconciled. Full historical product-byte identity is not claimed. | AUD-028-002, AUD-028-016 |
| FR-023 | IMPLEMENTED | All 25 newly added aggregate non-AU persona bullets explicitly say placeholder with promotion prose, e.g. [003](../003-rubric-gap-closure/spec.md#L269) and [028](spec.md#L246). T062a's stronger YAML/list check still fails. | AUD-028-004 |
| SC-001 | PARTIAL | [100% content gate](spec.md#L199) not established by 27 headings; full population table documents content failures and extra 14 scope conflict. | AUD-028-001, AUD-028-003, AUD-028-004, AUD-028-005, AUD-028-006, AUD-028-013 |
| SC-002 | PARTIAL | [Trace](../shared/capstone-metric-trace.md#L11) has all five metric groups but no economic AU HYP ID and no direct annual lives hypothesis; schema also invalid. | AUD-028-008, AUD-028-009 |
| SC-003 | UNVERIFIED | [Post-merge timing criterion](spec.md#L201) has no observation record; absence is non-blocking, not PASS. | AUD-028-014, AUD-028-016 |
| SC-004 | CONFLICT | [Zero marker criterion](spec.md#L202), quoted local mentions and three historical colon markers in the full literal scope differ from [validator semantics](scripts/validate-section-coverage.ps1#L46). | AUD-028-001, AUD-028-016 |
| SC-005 | IMPLEMENTED | Fifteen distinct country statements/packs are present, fully read and individually accounted above, with Not tested and preconditions. No experiment claimed. | AUD-028-011 |
| SC-006 | PARTIAL | [Ownership intent](../018-aidr-guidance-integration/spec.md#L342) exists for all named overlaps, but exact reciprocal grammar and evidence export incomplete. | AUD-028-012, AUD-028-014 |
| SC-007 | CONFLICT | [Pre-existing definitions](../001-disaster-response-hub/spec.md#L103) contradict [zero watermark](../shared/gap-id-register.md#L69); plus-only diff does not prove non-reuse. | AUD-028-002 |
| SC-008 | IMPLEMENTED | Required 11 meta bullets verified one by one in task table; [contract](contracts/meta-spec-flag.contract.md#L14) satisfied for the closed set. | - |
| SC-009 | UNVERIFIED | [Baseline](evidence/rubric-baseline.md#L1) and [post arithmetic](evidence/rubric-postfeature.md#L35) exist, but no comparable approved rubric mapping/run provenance establishes uplift. | AUD-028-015 |

## Acceptance Scenario Accounting

Each identifier below is an audit locator for the original story/scenario number, not a new requirement or checkbox. Thirteen original acceptance scenarios are listed separately from six edge cases.

| Scenario | Status | Expected behavior and direct evidence | Follow-up |
| --- | --- | --- | --- |
| US1-AS1 | PARTIAL | [Original](spec.md#L44): every spec has >=3 tagged referenced assumptions; [027 two untagged entries](../027-spec-hardening/spec.md#L261) and full population inventory disconfirm universal coverage. | AUD-028-003, AUD-028-013 |
| US1-AS2 | PARTIAL | [Original](spec.md#L45): >=2 schema personas/references; [027 one](../027-spec-hardening/spec.md#L268) and generic prose references fail. | AUD-028-004 |
| US1-AS3 | PARTIAL | [Original](spec.md#L46): exact-format hypothesis plus pack; [generic HYP-001](../003-rubric-gap-closure/spec.md#L275) is wrong format/missing pack; country artifacts supported separately. | AUD-028-005 |
| US1-AS4 | PARTIAL | [Original](spec.md#L47): scope count/country prerequisites; [retained 013 scope](../013-root-readme/spec.md#L206) has none. | AUD-028-006 |
| US1-AS5 | MISSING | [Original](spec.md#L48): every effective AU FR has inline ASM; all concrete citations absent (NEG-03), including [014](../014-azure-openai-integration/spec.md#L192). | AUD-028-007 |
| US2-AS1 | PARTIAL | [Original](spec.md#L62): owners/baseline/method per metric; [economic row](../shared/capstone-metric-trace.md#L27) lacks HYP and quantitative baseline. | AUD-028-008, AUD-028-009 |
| US2-AS2 | PARTIAL | [Original](spec.md#L63): each country row explicit validated/deferred; all 15 are Deferred, but owner-cell preconditions are in the wrong columns. | AUD-028-008 |
| US2-AS3 | PARTIAL | [Original](spec.md#L64): each cited ID exists; most do, economic AU names none and lives row uses ranges/proxies; global IDs collide. | AUD-028-002, AUD-028-008, AUD-028-009 |
| US3-AS1 | PARTIAL | [Original](spec.md#L78): [006 contract-level pointer](../006-data-ingestion-storage/spec.md#L254) implemented; canonical reciprocal amendment remains unsatisfied. | AUD-028-012 |
| US3-AS2 | PARTIAL | [Original](spec.md#L79): both warning-timeout scope statements exist in [008](../008-communication-agent/spec.md#L366)/[018](../018-aidr-guidance-integration/spec.md#L343), exact matched phrasing incomplete. | AUD-028-012 |
| US3-AS3 | PARTIAL | [Original](spec.md#L80): sole intended recovery owner is [018](../018-aidr-guidance-integration/spec.md#L342), other two defer; canonical syntax remains partial. | AUD-028-012 |
| US4-AS1 | IMPLEMENTED | [Original](spec.md#L94): [027 stale reference replacement](../027-spec-hardening/spec.md#L18) directly supported. | - |
| US4-AS2 | IMPLEMENTED | [Original](spec.md#L95): [013](../013-root-readme/spec.md#L208), [016](../016-automated-demo-script/spec.md#L165), [025](../025-agent-spec-compliance/spec.md#L282), [026](../026-sim-warp-playback/spec.md#L201) carry required meta ownership flags. | - |

| Edge case | Status | Direct evidence and assessment | Follow-up |
| --- | --- | --- | --- |
| EDGE-01 | PARTIAL | [Inherited persona rule](spec.md#L101); [022](../022-multi-jurisdiction-filter/spec.md#L155) references catalogues without schema-complete profiles/applicability. | AUD-028-004 |
| EDGE-02 | PARTIAL | [No-data-model owner still needs a hypothesis](spec.md#L102); [017 HYP-015](../017-cd-pipeline/spec.md#L215) is generic author-consultation uplift, not a pipeline/operator hypothesis with a pack. | AUD-028-005 |
| EDGE-03 | IMPLEMENTED | [Non-country-relevant meta requirement](spec.md#L103); [004 scope](../004-actor-github-agents/spec.md#L185) explicitly names PH/JP/BD and promotion prerequisites. | - |
| EDGE-04 | MISSING | [Legacy mapping rule](spec.md#L104); [010 existing assumptions](../010-monitoring-agent/spec.md#L215) retain the old form without a mapping row (NEG-03). | AUD-028-003 |
| EDGE-05 | PARTIAL | [Exactly-one-authority rule](spec.md#L105); [018 owner](../018-aidr-guidance-integration/spec.md#L342) is supported but examples/conditional boilerplate are not safely discriminated by raw grep. | AUD-028-012 |
| EDGE-06 | PARTIAL | [Excluded duplicate proposal rule](spec.md#L106); explicit exclusion is authored, historical metadata shows no duplicate-folder changes in the feature commit, but no separate proposal found (NEG-05). | AUD-028-013 |

## Clarification and Amendment Accounting

All twelve Q/A bullets in the two local clarification sessions are included, plus the appended persona/hypothesis/scope content in the entity and constraint tables. Audit locators CL-01 etc. are not original task IDs or invented checkboxes.

| Clarification | Status | Source, controlling decision, and observed outcome | Follow-up |
| --- | --- | --- | --- |
| CL-01 | PARTIAL | [2026-04-24 recovery owner](spec.md#L12): 018 authority and 001/011 deferrals exist; exact canonical pairs incomplete. | AUD-028-012 |
| CL-02 | PARTIAL | [Language-code deferral](spec.md#L13): country/language intent preserved, but 008 hypotheses bind concrete codes. | AUD-028-011 |
| CL-03 | CONFLICT | [Seven-column, 20-row metric schema](spec.md#L14): correct cross-product, wrong column/owner structure and extra table. | AUD-028-008 |
| CL-04 | IMPLEMENTED | [Expanded eleven-meta set](spec.md#L15): all named canonical bullets present; separate later-population decision remains open. | AUD-028-013 |
| CL-05 | PARTIAL | [Stub minimum content](spec.md#L16): fifteen country packs conform, 26 generic packs absent. | AUD-028-005 |
| CL-06 | UNVERIFIED | [Composite uplift threshold](spec.md#L17): preserved numerically; comparable grader evidence not established. | AUD-028-015 |
| CL-07 | PARTIAL | [2026-04-25 four-section decision](spec.md#L21): four H2s exist in the closed set, but content fails and checklist still describes five mandatory sections. | AUD-028-001, AUD-028-016 |
| CL-08 | MISSING | [FR-005a promoted](spec.md#L22): no concrete inline AU-only citations in current owner population; no dedicated implementation task. | AUD-028-007, AUD-028-016 |
| CL-09 | PARTIAL | [T062a added](spec.md#L23): original task exists and prose placeholder tagging exists, but YAML/list validation and persisted audit do not. | AUD-028-004, AUD-028-014 |
| CL-10 | IMPLEMENTED | [Reviewer timing deferred](spec.md#L24): T063a remains post-merge/non-blocking. Actual SC-003 execution remains UNVERIFIED and closure PASS is wrong. | AUD-028-014 |
| CL-11 | PARTIAL | [Per-metric owner aggregation](spec.md#L25): AU owner suffices across cohorts, but economic loss lacks one; no all-deferred metric may pass. | AUD-028-009 |
| CL-12 | PARTIAL | [Canonical owner/defer templates](spec.md#L26), [both-side rule](spec.md#L152): intent exists, exact complete pair syntax/placement not met. | AUD-028-012 |

| Independent test | Status | Source and accounting | Follow-up |
| --- | --- | --- | --- |
| IT-US1 | PARTIAL | [Five-spec reviewer check](spec.md#L40): this audit inspected the full population, but missing content prevents the promised self-contained answers; no timed human test occurred. | AUD-028-001, AUD-028-003, AUD-028-004, AUD-028-005, AUD-028-006, AUD-028-007, AUD-028-014 |
| IT-US2 | CONFLICT | [Trace test](spec.md#L58) asks each row to have owners and mentions a separate column per cohort, inconsistent with clarified long-form deferred rows. | AUD-028-008, AUD-028-016 |
| IT-US3 | PARTIAL | [Ownership grep](spec.md#L74) finds words but cannot distinguish templates/conditional boilerplate from canonical reciprocal declarations. | AUD-028-012 |
| IT-US4 | IMPLEMENTED | [Meta independent test](spec.md#L90): all required Out-of-Scope flags are authored; future literal-SimpleMatch command defect accounted separately. | AUD-028-016 |

### Embedded Assumptions

These ten source bullets have no original checkbox and mostly no ASM ID; SA-* are audit locators only. The missing per-entry IDs are an implementation finding, not a reason to omit the obligations.

| Constraint | Status | Source and expected versus observed | Follow-up |
| --- | --- | --- | --- |
| SA-01 | PARTIAL | [Capstone authoritative/AU divergence justified](spec.md#L184): country deferrals authored, but inline FR assumptions and metric ownership incomplete. | AUD-028-003, AUD-028-007, AUD-028-009 |
| SA-02 | PARTIAL | [Accept 027 and reuse taxonomy](spec.md#L185): reused names, not complete roles/schema/monotonic semantics. | AUD-028-002, AUD-028-003, AUD-028-004 |
| SA-03 | IMPLEMENTED | [Non-AU validation deferred](spec.md#L186): all new non-AU persona bullets remain placeholders; no SME validation claimed for those cohorts. | AUD-028-004 |
| SA-04 | IMPLEMENTED | [Country references documentation-only](spec.md#L187): actual additions are deferred descriptions/stubs; no functional country deployment is implied by this assessment. | - |
| SA-05 | CONFLICT | [One monotonic register](spec.md#L188): zero-start counters and multiple meanings per ID contradict the single-source rule. | AUD-028-002 |
| SA-06 | UNVERIFIED | [Checklist marker triage without rewrite](spec.md#L189): no triage record in the bounded local/shared/evidence searches; do not infer triage from checked boxes. | AUD-028-014, AUD-028-016 |
| SA-07 | IMPLEMENTED | [Preserve nine AU jurisdictions](spec.md#L190): [022 hierarchy](../022-multi-jurisdiction-filter/spec.md#L183) enumerates exactly the existing nine plus deferred countries. | - |
| SA-08 | PARTIAL | [Evidence at creation](spec.md#L191): fifteen country packs exist; 26 generic packs do not. | AUD-028-005 |
| SA-09 | PARTIAL | [Exclude stale duplicates, author proposal](spec.md#L192): exclusion exists; separate removal proposal absent after NEG-05. | AUD-028-013 |
| SA-10 | PARTIAL | [Sovereignty tension in each affected spec](spec.md#L193): explicit new ASM risk only in 005/006/009; mandated 010/014/017 omitted; later model-hosting exception is limited. | AUD-028-003 |

### Scope and Dependencies

| Constraint | Status | Source and accounting | Follow-up |
| --- | --- | --- | --- |
| OOS-01 | IMPLEMENTED | [028 enabling/meta classification](spec.md#L211): canonical bullet present with complete critical-path set. | - |
| OOS-02 | IMPLEMENTED | [No product-source rewrite](spec.md#L213): inspected authoring scripts target spec/evidence Markdown; this audit changed no product file. No claim of all mixed-commit source attribution is made. | - |
| OOS-03 | IMPLEMENTED | [No agent rearchitecture/ports](spec.md#L214): country additions describe deferred capability; no agent or port change is required to resolve the documentation findings. | - |
| OOS-04 | PARTIAL | [No spec/ID rename](spec.md#L215): paths preserved; reused IDs create incompatible meanings. Repair must preserve historical references through an approved migration. | AUD-028-002 |
| OOS-05 | IMPLEMENTED | [Do not reverse AU-v1](spec.md#L216): country rows stay deferred; later constitution model-hosting carve-out is not general country activation. | - |
| OOS-06 | IMPLEMENTED | [Do not create phantom feature](spec.md#L217): [027 replacement](../027-spec-hardening/spec.md#L18) uses 028-capstone-alignment. | - |
| OOS-07 | IMPLEMENTED | [Do not implement Asia feeds/languages/law mappings](spec.md#L218): authored candidate/placeholder rules explicitly defer implementation. | - |
| OOS-08 | IMPLEMENTED | [Do not edit capstone/rubric](spec.md#L219): read-only feature-commit numstat found no changes to either authoritative input. This report preserves them. | - |
| OOS-09 | PARTIAL | [Historical duplicate folder excluded](spec.md#L220): preserved; separate proposal not found. | AUD-028-013 |
| OOS-10 | IMPLEMENTED | [Non-AU SME validation deferred](spec.md#L221): no requirement to invent or obtain those approvals in 028. | - |
| OOS-11 | IMPLEMENTED | [Do not resolve sovereignty tension](spec.md#L222): [decision record](evidence/decision-record.md#L13) retains it; propagation is separately incomplete. | AUD-028-003 |
| OOS-12 | UNVERIFIED | [Checklist marker rewrite excluded, triage required](spec.md#L223): no triage evidence; no checklist was changed by this audit. | AUD-028-014, AUD-028-016 |
| DEP-01 | PARTIAL | [027 taxonomy/contract dependency](spec.md#L227): reference files exist and were read, but complete reuse is not implemented. | AUD-028-002, AUD-028-003, AUD-028-004, AUD-028-005 |
| DEP-02 | PARTIAL | [Writable monotonic register](spec.md#L228): register exists; correctness is violated and real branch/approval permissions are not asserted. | AUD-028-002, AUD-028-014 |
| DEP-03 | IMPLEMENTED | [Authoritative capstone/rubric inputs](spec.md#L229): both files exist and remain named inputs; rubric mapping is still unresolved. | AUD-028-015 |

## Design and Contract Accounting

The eight unnumbered Key Entities in the source specification are all covered here: Spec -> E-001; Metric -> E-007; Cohort -> E-008; Hazard -> E-009; Privacy Regime -> E-010; Cross-Agency Protocol -> E-011; Gap-ID Register -> E-013; Metric Trace -> E-012. Additional data-model entities E-002 through E-006 govern the appended assumption/persona/hypothesis/scope/requirement artifacts, not runtime database schemas.

| Entity constraint | Status | Source and assessment of required fields/invariants | Follow-up |
| --- | --- | --- | --- |
| E-001 | PARTIAL | [Spec identity/sections/classification](data-model.md#L9): full-folder identity required; four-section content and closed/dynamic partition disagree. | AUD-028-001, AUD-028-013 |
| E-002 | PARTIAL | [ASM fields](data-model.md#L23): IDs/tags/statement/roles/status/links/cohorts and metric/hazard/cohort/privacy relevance not universally populated. | AUD-028-002, AUD-028-003 |
| E-003 | PARTIAL | [HYP fields/state transitions](data-model.md#L37): fifteen country statements/window/status packs exist; generic owners/evidence/format incomplete. No tested transition inferred. | AUD-028-005, AUD-028-014 |
| E-004 | PARTIAL | [Persona fields/reference/placeholder contract](data-model.md#L50): prose placeholders preserve intent but do not implement inherited schema and provenance. | AUD-028-004 |
| E-005 | PARTIAL | [SCP identity/scope/promotion fields](data-model.md#L57): many concrete country deferrals; retained sections lack mappings and SCP IDs collide. | AUD-028-002, AUD-028-006 |
| E-006 | MISSING | [New cross-spec FR mirrored to REQ](data-model.md#L66): [register says REQ unused](../shared/gap-id-register.md#L72); no per-FR REQ mapping. | AUD-028-002 |
| E-007 | PARTIAL | [Five exact metric enums/owner rules](data-model.md#L71): all enums present; missing economic HYP and weak annual lives attribution. | AUD-028-009 |
| E-008 | IMPLEMENTED | [Four exact cohorts/deferred prerequisites](data-model.md#L81): all AU-v1/PH/JP/BD combinations present; grammar issues assessed under E-012. | AUD-028-008 |
| E-009 | PARTIAL | [012 hazard ownership/downstream applicability](data-model.md#L87): [hazard table](../012-risk-assessment-agent/spec.md#L345) and fifteen downstream country hypotheses exist; risk-assumption reference unresolved. | AUD-028-003 |
| E-010 | IMPLEMENTED | [Privacy regimes and 005 owner](data-model.md#L92): all requested law labels/deferred conditions authored. No current-law or regulator-approval certification. | - |
| E-011 | IMPLEMENTED | [Protocol placeholders](data-model.md#L98), [source labels](spec.md#L178): AU AIIMS, PH NDRRMC/NDRP, JP Cabinet plan, BD SOD and ASEAN-AHA retained as placeholders, not executable integrations. | - |
| E-012 | CONFLICT | [Trace columns/cardinality/status](data-model.md#L103): cardinality correct; stored header/owner grammar incompatible. | AUD-028-008 |
| E-013 | CONFLICT | [Register invariant](data-model.md#L110): prior numeric maxima were nonzero; reused meanings violate global monotonicity. | AUD-028-002 |

| Research decision/pattern | Status | Source and assessment | Follow-up |
| --- | --- | --- | --- |
| D-001 | PARTIAL | [Markdown-only/no runtime changes](research.md#L15): owned outputs are documentation, but executable author helpers and validator require the tooling exception demanded by tasks. | AUD-028-016 |
| D-002 | PARTIAL | [Exact inherited taxonomy](research.md#L23): field/tag/ID/statement differences remain. | AUD-028-002, AUD-028-003, AUD-028-004, AUD-028-005 |
| D-003 | CONFLICT | [Single static trace schema](research.md#L31): wrong header and owner grammar, second table. | AUD-028-008 |
| D-004 | PARTIAL | [Defer identifiers to owning research](research.md#L39): later operative corpus codes contradict it. | AUD-028-011 |
| D-005 | PARTIAL | [Recovery authority = 018](research.md#L47): intended owner supported; exact canonical pair incomplete. | AUD-028-012 |
| D-006 | PARTIAL | [Six fixed stub headings](research.md#L55): fifteen country packs comply, 26 generic ones absent. | AUD-028-005 |
| D-007 | UNVERIFIED | [Composite rubric gate](research.md#L63): arithmetic claimed, actual comparable grading method/provenance not established. | AUD-028-015 |
| D-008 | CONFLICT | [Closed disjoint 16+11 partition](research.md#L68): correct named set, incompatible with every-current-folder requirement. | AUD-028-013 |
| D-009 | PARTIAL | [Document, do not resolve sovereignty tension](research.md#L73): decision retained; per-PII-owner propagation incomplete. | AUD-028-003 |
| P-001 | CONFLICT | [Append-only identity pattern](research.md#L85): plus-only register addition does not establish unique new numeric meaning. | AUD-028-002 |
| P-002 | PARTIAL | [Per-owner evidence co-location](research.md#L89): country packs co-located, generic packs absent and centrally mislinked. | AUD-028-005 |
| P-003 | PARTIAL | [Closed cohort cells](research.md#L93): trace has exact cohorts; generic hypotheses/assumptions omit explicit structured cohort fields. | AUD-028-003, AUD-028-005 |
| P-004 | IMPLEMENTED | [Country instances of existing hazard classes](research.md#L97): [012 table](../012-risk-assessment-agent/spec.md#L345) appends PH/JP/BD instances rather than replacing AU classes. | AUD-028-003 |

Research's six resolved-unknown rows are fully accounted for by CL-01 (recovery), CL-02 (codes), CL-03 (trace), CL-04 (meta set), CL-05 (stub minimum), and CL-06 (rubric threshold), respectively. Recorded decisions are authored resolution evidence, not proof of consultations or resulting implementation conformance.

| Contract obligation | Status | Source and concrete accounting | Follow-up |
| --- | --- | --- | --- |
| CT-M01 | CONFLICT | [One H1/intro/table only](contracts/capstone-metric-trace.contract.md#L9): actual trace has additional blockquotes and second table. | AUD-028-008 |
| CT-M02 | CONFLICT | [Seven ordered typed columns](contracts/capstone-metric-trace.contract.md#L9): Status wrong position; owners prose; baselines not quantitative with units. All seven fields assessed. | AUD-028-008, AUD-028-009 |
| CT-M03 | IMPLEMENTED | [Exactly 20 unique cross-product pairs](contracts/capstone-metric-trace.contract.md#L22): all five metrics and four cohorts present exactly once. | - |
| CT-M04 | IMPLEMENTED | [No Unresolved on close](contracts/capstone-metric-trace.contract.md#L31): zero Unresolved data rows; this does not establish valid owner cells. | - |
| CT-M05 | CONFLICT | [Deferred owner-cell prefix/preconditions](contracts/capstone-metric-trace.contract.md#L32): all fifteen deferred rows place prerequisites in Baseline instead. | AUD-028-008 |
| CT-M06 | CONFLICT | [Validated owner grammar/existence](contracts/capstone-metric-trace.contract.md#L33): all five AU rows violate owner grammar; economic row has no HYP ID. | AUD-028-008, AUD-028-009 |
| CT-M07 | UNVERIFIED | [Versioned feature changes/unidirectional statuses](contracts/capstone-metric-trace.contract.md#L50): named features exist, but no archived complete transition evidence or approved schema departure. | AUD-028-008, AUD-028-014 |
| CT-H01 | PARTIAL | [Owning-folder location](contracts/evidence-stub.contract.md#L7): fifteen co-located country packs, 26 generic packs absent. | AUD-028-005 |
| CT-H02 | PARTIAL | [Exactly six H2s in order](contracts/evidence-stub.contract.md#L11): all fifteen country packs satisfy it; missing generic packs cannot pass. | AUD-028-005 |
| CT-H03 | PARTIAL | [Exact hypothesis statement format](contracts/evidence-stub.contract.md#L17): fifteen country statements conform; 26 generic If/then statements do not. | AUD-028-005 |
| CT-H04 | PARTIAL | [At least two prerequisites](contracts/evidence-stub.contract.md#L21): all fifteen existing new packs have three bullets; generic packs absent. | AUD-028-005 |
| CT-H05 | PARTIAL | [Named/bounded window](contracts/evidence-stub.contract.md#L26): PH Jun-Nov, JP quarterly, BD Apr-Sep in all fifteen; generic windows missing. | AUD-028-005 |
| CT-H06 | PARTIAL | [Quantified falsification](contracts/evidence-stub.contract.md#L30): all fifteen have numerical thresholds; missing generic packs and rubric benefit/falsification mismatch remain. Boolean-only contract allowance must not silently weaken FR-015's quantified rule. | AUD-028-005, AUD-028-016 |
| CT-H07 | PARTIAL | [Literal Not tested at creation](contracts/evidence-stub.contract.md#L34): fifteen packs correct; no execution inferred, 26 absent. | AUD-028-005 |
| CT-H08 | PARTIAL | [Linked owning spec](contracts/evidence-stub.contract.md#L37): all fifteen correct; generic packs absent; secondary HYP-026 pack dependency unresolved. | AUD-028-005 |
| CT-H09 | PARTIAL | [Filename/ID/register alignment](contracts/evidence-stub.contract.md#L50): country filenames valid; generic doubled names invalid/missing, per-entry register missing. | AUD-028-002, AUD-028-005 |
| CT-H10 | UNVERIFIED | [Owning feature and later status change control](contracts/evidence-stub.contract.md#L81): no observed promotion or actual branch/approval record; no experiment performed here. | AUD-028-014 |
| CT-F01 | IMPLEMENTED | [Closed 11-meta/16-critical sets](contracts/meta-spec-flag.contract.md#L6): named partition matches all eleven canonical bullets. Dynamic future scope is a separate conflict. | AUD-028-013 |
| CT-F02 | IMPLEMENTED | [Exact substituted bullet, correct section, one per owner](contracts/meta-spec-flag.contract.md#L12): T047-T057 provide each direct citation; no literal list placeholder remains in canonical bullets. | - |

## Checklist and Review Accounting

Original checkboxes below are transcribed, not changed or treated as proof. `none` means the source has no checkbox. `QC-*` and `PP-*` are audit locators; source tasks retain their own T IDs above.

### Requirements Checklist

| Item | Original checkbox | Original checklist text | Status | Evidence and assessment | Follow-up |
| --- | --- | --- | --- | --- | --- |
| QC-01 | [x] | No implementation details (languages, frameworks, APIs) | PARTIAL | [Checklist](checklists/requirements.md#L9); documentation-only intent, but spec prescribes YAML/regex/filesystem formats and validation tooling. | AUD-028-016 |
| QC-02 | [x] | Focused on user value and business needs | IMPLEMENTED | [Checklist](checklists/requirements.md#L10); four user stories explicitly describe reviewer/evaluator value. | - |
| QC-03 | [x] | Written for non-technical stakeholders | PARTIAL | [Checklist](checklists/requirements.md#L11); readable stories coexist with technical contracts and unresolved navigation/provenance issues. | AUD-028-004, AUD-028-014 |
| QC-04 | [x] | All mandatory sections completed | PARTIAL | [Checklist](checklists/requirements.md#L12); headers present, not complete content. | AUD-028-001, AUD-028-003, AUD-028-004, AUD-028-005, AUD-028-006 |
| QC-05 | [x] | No [NEEDS CLARIFICATION] markers remain | CONFLICT | [Checklist](checklists/requirements.md#L16); literal phrase/marker semantics differ from unresolved-decision semantics. | AUD-028-016 |
| QC-06 | [x] | Requirements are testable and unambiguous | CONFLICT | [Checklist](checklists/requirements.md#L17); scope population, canonical syntax and rubric mapping conflicts remain. | AUD-028-013, AUD-028-015, AUD-028-016 |
| QC-07 | [x] | Success criteria are measurable | PARTIAL | [Checklist](checklists/requirements.md#L18); numerical goals exist, but rubric mapping/baselines and human timings are not established. | AUD-028-009, AUD-028-014, AUD-028-015 |
| QC-08 | [x] | Success criteria are technology-agnostic (no implementation details) | PARTIAL | [Checklist](checklists/requirements.md#L19); SCs explicitly depend on automated grep and grader tooling. | AUD-028-016 |
| QC-09 | [x] | All acceptance scenarios are defined | IMPLEMENTED | [Checklist](checklists/requirements.md#L20); thirteen original scenarios enumerated separately above. | - |
| QC-10 | [x] | Edge cases are identified | IMPLEMENTED | [Checklist](checklists/requirements.md#L21); six explicit edges accounted above. | - |
| QC-11 | [x] | Scope is clearly bounded | CONFLICT | [Checklist](checklists/requirements.md#L22); closed 27 versus literal 41, self-obligations and helper exception unresolved. | AUD-028-013, AUD-028-016 |
| QC-12 | [x] | Dependencies and assumptions identified | IMPLEMENTED | [Checklist](checklists/requirements.md#L23); ten local assumptions and three dependencies are authored; fulfillment assessed separately. | - |
| QC-13 | [x] | All functional requirements have clear acceptance criteria | PARTIAL | [Checklist](checklists/requirements.md#L27); FR-005a lacks implementation ownership; several gate predicates conflict. | AUD-028-007, AUD-028-016 |
| QC-14 | [x] | User scenarios cover primary flows | IMPLEMENTED | [Checklist](checklists/requirements.md#L28); four intended documentation workflows present. | - |
| QC-15 | [x] | Feature meets measurable outcomes defined in Success Criteria | CONFLICT | [Checklist](checklists/requirements.md#L29); missing packs/owners and unverified timings/rubric invalidate blanket completion. | AUD-028-005, AUD-028-009, AUD-028-014, AUD-028-015 |
| QC-16 | [x] | No implementation details leak into specification | PARTIAL | [Checklist](checklists/requirements.md#L30); technical validation prescriptions need consistent documentation-feature framing. | AUD-028-016 |

Checklist notes are also assessed: [all-items-pass, technology-agnostic, five mandatory sections](checklists/requirements.md#L34) conflict with later four-section clarification and observed content; [trace and overlap priorities](checklists/requirements.md#L36) are valid intent but not proof of fulfillment; [zero markers/readiness](checklists/requirements.md#L38) does not establish implementation or external review. These are authored assertions with no original checkbox (`none`), covered by AUD-028-014/016.

### Plan Progress

| Item | Original checkbox | Original progress text | Status | Evidence and assessment | Follow-up |
| --- | --- | --- | --- | --- | --- |
| PP-01 | [x] | Phase 0 research complete (9 decisions, 4 patterns, 6 unknowns -> all resolved) | IMPLEMENTED | [Source progress](plan.md#L116), [research](research.md#L13): all named authored records exist; external consultation not inferred. | AUD-028-014 |
| PP-02 | [x] | Phase 1 design complete (data-model.md, 3 contracts, quickstart.md) | IMPLEMENTED | [Source progress](plan.md#L117): all five named design documents exist and were fully read. | - |
| PP-03 | [x] | Constitution gate passed (one documented tension, Complexity Tracking updated) | PARTIAL | [Source progress](plan.md#L118); authored fifteen-row assessment exists but integrity/fallback/risk-propagation findings remain. | AUD-028-003, AUD-028-010, AUD-028-014 |
| PP-04 | [x] | Agent context file refreshed via update-agent-context.ps1 -AgentType copilot | UNVERIFIED | [Source progress](plan.md#L119) claims an execution; no supporting refresh/run record in local inputs. | AUD-028-014 |
| PP-05 | [ ] | Phase 2 tasks - owned by /speckit.tasks (NOT produced by /speckit.plan) | IMPLEMENTED | [Source progress](plan.md#L120); [68 task definitions](tasks.md#L23) exist despite this unchecked planning-era item. | - |

### Plan Gates

All fifteen constitution-table entries have original checkbox state `none`; the source's authored Pass/Documented labels are not approvals. The post-design re-check repeats the same assessment and creates no new independently executed gate.

| Gate | Original checkbox | Source clause | Status | Evidence and assessment | Follow-up |
| --- | --- | --- | --- | --- | --- |
| PG-01 | none | Primacy of life | PARTIAL | [Plan](plan.md#L32): lives-saved prioritized, but missing direct HYP/baseline and fallback contract conflict. | AUD-028-009, AUD-028-010 |
| PG-02 | none | Eleven AEMA principles | IMPLEMENTED | [Plan](plan.md#L33): doctrine is retained; no new principle or country activation asserted. | - |
| PG-03 | none | AIIMS functional alignment | PARTIAL | [Plan](plan.md#L34): 018 ownership intent retained; canonical pairs incomplete. | AUD-028-012 |
| PG-04 | none | Multi-hazard, multi-agency | IMPLEMENTED | [Plan](plan.md#L35), [012 table](../012-risk-assessment-agent/spec.md#L345): country-scoped hazard instances explicitly added. | - |
| PG-05 | none | Transparency and auditability | CONFLICT | [Plan](plan.md#L36): reused identities/missing new packs contradict full traceability claim. | AUD-028-002, AUD-028-005, AUD-028-014 |
| PG-06 | none | Warning and public information | CONFLICT | [Plan](plan.md#L37): claimed inheritance differs from 010's fail-closed fallback. | AUD-028-010 |
| PG-07 | none | Evacuation framework | PARTIAL | [Plan](plan.md#L38): real pre-warned/immediate hypotheses exist; metric trace conflates JP immediate latency with 24h early benefit. | AUD-028-009 |
| PG-08 | none | Recovery support | PARTIAL | [Plan](plan.md#L39): 018 intended authority supported, exact reciprocal rule incomplete. | AUD-028-012 |
| PG-09 | none | Cloud platform and infrastructure | IMPLEMENTED | [Plan](plan.md#L40): 017 deferred topology text added; no country deployment certified. | - |
| PG-10 | none | Human-in-the-loop | IMPLEMENTED | [Plan](plan.md#L41): documentation-only country additions do not execute operational actions. Human review claims assessed independently. | AUD-028-014 |
| PG-11 | none | Data sovereignty | PARTIAL | [Plan](plan.md#L42): unresolved tension correctly named, required per-owner propagation incomplete and later limited carve-out must be respected. | AUD-028-003 |
| PG-12 | none | Privacy by design | IMPLEMENTED | [Plan](plan.md#L43): four named law regimes/deferred prerequisites exist as text; legal approval unverified. | - |
| PG-13 | none | Interoperability | IMPLEMENTED | [Plan](plan.md#L44): no runtime CAP/EDXL/GeoJSON/OpenAPI schema change required by feature artifacts. | - |
| PG-14 | none | Graceful degradation | CONFLICT | [Plan](plan.md#L45): new multilingual fallback prose differs from its inherited fail-closed owner. | AUD-028-010 |
| PG-15 | none | Quality gates and PR review | UNVERIFIED | [Plan](plan.md#L46): no new CI step required; actual lint/test/PR approvals not established by static source. | AUD-028-014 |

### Plan Constraints

| Constraint | Status | Source and assessment | Follow-up |
| --- | --- | --- | --- |
| PC-01 | CONFLICT | [Markdown-only approach](plan.md#L8) versus T007 and three executable helper files; bounded authoring-tool exception unresolved. | AUD-028-016 |
| PC-02 | IMPLEMENTED | [No runtime/infra/schema change](plan.md#L8): inspected feature writers target docs only. No independent runtime-product implementation is required or evaluated here. | - |
| PC-03 | IMPLEMENTED | [Markdown storage/no runtime entities](plan.md#L16), [documentation entities](data-model.md#L5): retained; ephemeral planning SQL is not a product database implementation. | - |
| PC-04 | PARTIAL | [Grep/schema/rubric testing strategy](plan.md#L17): heading helper exists, complete content/real rubric checks absent. No new CI lane is mandated. | AUD-028-001, AUD-028-015 |
| PC-05 | UNVERIFIED | [Git/human PR review platform](plan.md#L18): actual reviewer approval and actors' consultations not established. | AUD-028-014 |
| PC-06 | UNVERIFIED | [<=10-minute reviewer goal](plan.md#L20): no observations, strictness conflicts with SC-003/T063a. | AUD-028-014, AUD-028-016 |
| PC-07 | CONFLICT | [27 folders/20 trace rows/>=15 HYP scale](plan.md#L22): 20 rows and 15 country packs supported; actual literal folder denominator 41. | AUD-028-013 |
| PC-08 | PARTIAL | [Append-only/marker/preservation constraints](plan.md#L21): register diff additive but IDs reused, marker semantics inconsistent; full mixed-commit product-byte equality not established. | AUD-028-002, AUD-028-016 |
| CX-01 | PARTIAL | [Document sovereignty tension, do not resolve](plan.md#L107): architectural rationale exists; risk propagation incomplete. | AUD-028-003 |
| CX-02 | PARTIAL | [Single shared trace rationale](plan.md#L108): central artifact exists, but schema/ownership claims fail. | AUD-028-008, AUD-028-009 |

### Evidence Records

| Record or required activity | Status | Direct evidence/absence and disposition | Follow-up |
| --- | --- | --- | --- |
| Pre-feature rubric | UNVERIFIED | [Existing snapshot](evidence/rubric-baseline.md#L1): authored scores, timestamp and run label; underlying SQL inventory/approved rubric mapping absent. Do not rewrite the frozen record. | AUD-028-015 |
| Post-feature rubric | UNVERIFIED | [Renamed snapshot](evidence/rubric-postfeature.md#L1): authored arithmetic, not a reproducible comparable official grading run. | AUD-028-015 |
| Always-emit decision | PARTIAL | [Existing different-name record](evidence/decision-record.md#L1): preserve supported decisions; correct remapped SC PASS claims and missing T065 decision structure. | AUD-028-014 |
| Validation execution outputs | UNVERIFIED | [Task-required artifacts](tasks.md#L351): no CSV, overlap/monotonicity/metric/stub/persona audit records found (NEG-01). Static findings here are not replacement execution records. | AUD-028-014 |
| Independent reviewer timing | UNVERIFIED | [SC-003/T063a deferral](spec.md#L201): no real timings; future non-blocking activity, not a failed product feature. | AUD-028-014, AUD-028-016 |
| Critique and analysis | UNVERIFIED | [T064/T066](tasks.md#L391): no original review reports found; closure note's optional status is unsupported. Audit subagents were not executions of those tasks. | AUD-028-014, AUD-028-016 |
| Human consultations and approvals | UNVERIFIED | [Role-only validation placeholders](../001-disaster-response-hub/spec.md#L169) and [generic actor-consultation prose](../003-rubric-gap-closure/spec.md#L260) are not SME interviews, human reviews, or approvals. | AUD-028-004, AUD-028-014 |
| Country experiments | UNVERIFIED | All fifteen country packs explicitly state Not tested; their licenses, deployments, corpora and sign-offs are prerequisites, not completed facts. | AUD-028-014 |
| Existing country hypothesis authorship | IMPLEMENTED | Fifteen exact statements/stubs were individually read; preserve quantified windows/prerequisites and the twelve unaffected non-language statements. | AUD-028-005, AUD-028-011 |
| Historical spec-001 packs | IMPLEMENTED | Six authored packs explicitly grandfathered by [carry-over note](evidence/rubric-postfeature.md#L51); experiments/signatures stay UNVERIFIED. | AUD-028-014 |

## Validation

Focused report checks were performed immediately after substantive edits. Source comparisons passed for all 68 original IDs and exact `[ ]` states, 33 numbered requirements/SCs, thirteen acceptance scenarios with exact source anchors, six edge cases, seventeen unique unchecked AUD headings with all required fields, all sixteen original checklist texts/states and all five plan checkbox states. All supplementary populations were checked for complete/unique counts, including twelve clarifications, nineteen contract obligations, and all 41 current owner artifacts. All 595 Markdown evidence links resolve to existing nonblank source lines within bounds. Citation checks exposed two overlong targets; both were corrected and the same check passed. Final report editor diagnostics: no errors. Session memory is restored to its initially empty state. No product checks were executed.

Only this report is an audit deliverable. No validator file was created; all integrity logic is ephemeral read-only PowerShell text inspection. No Python file I/O, product test, repository verifier, build, browser, server, cloud request, installation, runtime/debug session, original evidence update, approval, branch, or commit operation was performed. Terminal `rg` was unavailable, so PowerShell and workspace search were used with explicit exclusions of other implementation audit reports.

Remaining blockers are documentary/approval boundaries for future work: approved identity compatibility policy, explicit population decision, an accepted rubric mapping with a reproducible baseline, and authentic review/run evidence. The post-merge timing experiment remains non-blocking. Finishing this static report does not complete or check any original task.

### 2026-09-18 Implementation Pass

This pass was performed as an isolated context for spec 028 only. Three parallel technical reviews examined validator
scope/content enforcement, global identity/evidence allocation, and safety/metric closeout claims. The source-completable
validator defect was corrected: `validate-section-coverage.ps1` now fails when no numbered `spec.md` files are discovered
instead of returning a successful header-only CSV, preventing a vacuous pass.

Validation: PowerShell parsing passed; process-only `-ExecutionPolicy Bypass` validation emitted the expected CSV header
and data rows. The normal invocation was blocked by the machine's unsigned-script execution policy. Empty-fixture
negative execution was not run. Identity collisions, metric schema/ownership, safety authority, rubric mapping, and human
evidence remain open.
