# Implementation Review Tasks: 015 Performance Benchmarks

## Scope and Verdict

**Review date:** 2026-09-11. **Source revision:** `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a`.
The checkout HEAD matched that revision; no tracked changes were present at the start of this review.
This is an isolated, static, review-only audit of the canonical specification and historical task home.
It follows the [Review Contract](../../001-spec-implementation-audit/README.md#L12).
Only the two local implementation-review task reports are authorized writes. No source, original task,
specification, evidence, index, branch, or commit was changed. No delegation, product import, test,
benchmark, build, deployment, cloud query, or external approval was performed.

**Verdict:** A substantial benchmark scaffold exists, but its green status is not a reliable performance gate.
CI explicitly bypasses regression failures; SLO failures do not determine verdicts; repeated pipeline
samples become duplicate rejection; and the LLM benchmark selects a legacy-only path. Historical timing
JSON exists, but does not prove representative execution or the advertised outcomes at this revision.

**Coverage:** 34 original tasks: 34 `[X]`, zero unchecked. Their audit dispositions are 14 IMPLEMENTED,
14 PARTIAL, 2 CONFLICT, 1 SUPERSEDED, and 3 UNVERIFIED. Coverage also includes 13 FRs, 9 original SCs,
5 capstone SCs, 13 acceptance scenarios, 8 edge cases, 10 clarification decisions, 7 assumptions,
6 dependencies, 3 persona amendments, and HYP-013. There are 21 unchecked AUD-015 follow-ups.

### Evidence Statuses

| Status | Meaning in this report |
| --- | --- |
| IMPLEMENTED | Inspected source supports the scoped behavior or authored artifact; no runtime success is implied. |
| PARTIAL | Some implementation exists, but a named obligation is absent or contradicted. |
| MISSING | A required artifact or behavior was not found after the stated scoped search. |
| CONFLICT | Specification, design instructions, or current behavior disagree and need explicit resolution. |
| UNVERIFIED | Source cannot establish execution, outcome, approval, or deployed state. |
| SUPERSEDED | Explicit repository evidence documents replacement; this does not certify the replacement's execution. |

## Inputs and Evidence Boundary

All eleven local input documents were read completely, including appendices and checklist notes:

| Input | Scope |
| --- | --- |
| [spec.md](../../015-performance-benchmarks/spec.md#L1) | Full original specification, both clarification sessions, personas, hypothesis, and five capstone amendments. |
| [tasks.md](tasks.md#L1) | All 34 task checkboxes, phase checkpoints, dependency ordering, and implementation notes. |
| [plan.md](plan.md#L1) | Scope, performance goals, constitution PASS declarations, and file layout. |
| [research.md](research.md#L1) | R-001 through R-012, including error handling, measurement boundaries, and baseline promotion. |
| [data-model.md](data-model.md#L1) | Native results, comparison records, SLO semantics, provenance, and validation rules. |
| [quickstart.md](quickstart.md#L1) | Every documented command and baseline-management instruction; none executed. |
| [benchmark-modules.md](contracts/benchmark-modules.md#L1) | Four original module interfaces and the expressly permitted injectable circuit-breaker clock. |
| [comparison-wrapper.md](contracts/comparison-wrapper.md#L1) | Constants, records, invocation, error policies, and output contract. |
| [ci-workflow.md](contracts/ci-workflow.md#L1) | Two-minute safeguard, upload-always policy, retention, and temporary branch trigger. |
| [requirements.md](../../015-performance-benchmarks/checklists/requirements.md#L1) | Sixteen checked specification-quality declarations, not execution certificates. |
| [performance.md](../../015-performance-benchmarks/checklists/performance.md#L1) | All 54 unchecked deep-review questions, not approved requirements or completed validation. |

The two target directories contain no separate local execution transcript, approval record, or evidence
directory. Additional directly relevant evidence was read: the complete capstone trace, persona/evidence
contracts, both feature-028 rubric snapshots, saved economic-loss rows and summary, and the actual code
and assertion paths cited below. No other specification's implementation-review report was opened.
Applicable code-review instructions and the Python fact-grounded coding skill were followed. The AMA
rubric and grader skill were consulted to distinguish a real criterion assessment from structural
snapshots; this audit does not invent a new grade. No interpreter or runtime facts were inferred.

### Scoped Searches and Relocated Implementations

| Search scope and symbols | Result and limit of inference |
| --- | --- |
| All benchmark modules; callers under tests, apps, scripts, tools, and GitHub workflows for `compare_benchmarks`, `benchmark-json`, `perf-benchmark`, and benchmark names | The comparator is called by [conftest.py](../../../tests/benchmark/conftest.py#L70); the product CI caller is [ci.yml](../../../.github/workflows/ci.yml#L148). No separate comparator assertion suite or alternative CI failure gate was found in those scopes. |
| Original helper names and module layout | Helpers moved to [benchmark_helpers.py](../../../tests/benchmark/benchmark_helpers.py#L12). This is not missing implementation. All four original benchmark modules remain. |
| All five pipeline entry points and their deduplicators; neighboring unit tests | The calls exist. [Monitoring](../../../apps/agents/monitoring/pipeline.py#L107), [risk](../../../apps/agents/risk_assessment/dedup.py#L35), [evacuation](../../../apps/agents/evacuation/dedup.py#L35), [resource](../../../apps/agents/resource_allocation/dedup.py#L35), and [communication](../../../apps/agents/communication/dedup.py#L42) retain duplicate state across repeated samples. |
| LLM implementations and LLM/Foundry contract tests | [LLMClient](../../../apps/agents/common/llm_client.py#L55) now supports the production Foundry branch; [Foundry contract tests](../../../tests/contract/test_foundry_chat_client.py#L158) provide typed fake-response patterns. No replacement production-path timing benchmark was found in the benchmark directory or inspected callers. |
| Capstone identifiers and paired-exercise symbols under tests, apps, scripts, tools, shared trace, and relevant documentation | Found the [paired harness](../../../tests/simulation/paired_exercise_harness.py#L171), [economic-loss writer](../../../tests/measurement/sc005_economic_loss.py#L91), [evidence replay](../../../apps/api/app/services/evidence/simulation/orchestrator.py#L29), and [test-support evaluator](../../../apps/api/app/services/outcome_evaluator_service.py#L121). These are credited below, not treated as missing because they moved. |
| `HYP*013*` filenames across the workspace; `HYP-013` in feature-028/shared artifacts and relevant docs | No matching evidence stub or feature-015-specific hypothesis result was found. The actual advertised missing name is recorded in [spec.md](../../015-performance-benchmarks/spec.md#L201); portfolio rubric snapshots are not that stub. |
| Benchmark output tracking and ignore rules | Git tracks the keep-file and baseline. [The broad ignore rule](../../../.gitignore#L38) does not untrack them. The current result is ignored local evidence, not part of the source revision. |

The installed plugin source was read only as auxiliary local evidence: it saves JSON before yielding to
normal session-finish hooks ([plugin.py](../../../.venv/Lib/site-packages/pytest_benchmark/plugin.py#L379)).
Therefore no hook-order defect is asserted. Its output option opens a file directly
([plugin.py](../../../.venv/Lib/site-packages/pytest_benchmark/plugin.py#L258)); the benchmark harness and CI
command provide no missing-parent creation. The installed plugin is not proof of CI's resolved version.

## Saved Measurements, Not Certified Outcomes

Both native JSON files were parsed completely, including every benchmark record and its raw-data array.
The [tracked baseline](../../../.benchmarks/baseline.json#L141) identifies dirty revision
`42027955ef7d1099012fc4fb2c48087749ea5cc7`, Windows, pytest-benchmark 5.2.3, and
[2026-04-12T13:30:10Z](../../../.benchmarks/baseline.json#L36124).
The [ignored current artifact](../../../.benchmarks/current.json#L141) identifies dirty revision
`aa2e559897d158cd82d455baaf2d46e6fbb23a91` and
[2026-04-14T03:12:20Z](../../../.benchmarks/current.json#L16549), also Windows and plugin 5.2.3.
Dirty metadata alone does not invalidate a measurement, but the changed source and fixture set are not
captured in a reproducible execution manifest. Neither file establishes the September revision's result.

All 14 records contain min/max, rounds, iterations, SLO metadata, and raw samples. The figures below
are saved medians in milliseconds, rounded for display, not measurements performed in this audit.

| Metric | Baseline median ms | Local current median ms | Baseline/current rounds |
| --- | --- | --- | --- |
| Health monitoring | 2.39935 | 5.31110 | 52 / 91 |
| Health risk | 2.15930 | 5.73200 | 379 / 198 |
| Health evacuation | 2.05920 | 6.21470 | 245 / 91 |
| Health resource | 2.58790 | 6.24890 | 269 / 84 |
| Health communication | 2.45345 | 5.79050 | 344 / 71 |
| CB closed-to-open | 0.02860 | 0.08430 | 5590 / 172 |
| CB open-to-half-open | 0.03050 | 0.07080 | 9931 / 5069 |
| CB full recovery | 0.03110 | 0.09470 | 9728 / 6068 |
| LLM legacy overhead | 0.04300 | 0.08800 | 5900 / 3085 |
| Pipeline monitoring | 0.73550 | 2.87415 | 582 / 72 |
| Pipeline risk | 0.05920 | 0.06340 | 457 / 400 |
| Pipeline evacuation | 0.02530 | 0.05130 | 23 / 8 |
| Pipeline resource | 0.01640 | 0.04880 | 1881 / 361 |
| Pipeline communication | 0.05770 | 0.06040 | 19 / 55 |

The source-to-record anchors include [health](../../../.benchmarks/baseline.json#L151),
[CB recovery](../../../.benchmarks/baseline.json#L17248), [LLM](../../../.benchmarks/baseline.json#L27017),
and [pipelines](../../../.benchmarks/baseline.json#L32958). Raw samples permit later percentile derivation;
no P95/P99 was calculated here. Sample totals do not measure the whole command's setup/teardown duration.
The evacuation fixture was also parsed completely: [50 nodes, 120 edges, five assembly areas](../../../data/road-networks/far-north-qld-sample.json#L1),
no initially closed edges, version 1.0.0, last updated 2026-04-16. Benchmark JSON does not identify this
fixture version or prove nonempty population/facility processing.

### Measurement Callers and Assertions

The feature-015 path is [CI directory invocation](../../../.github/workflows/ci.yml#L148) to the four
original benchmark modules, pytest-benchmark native output, then [session-end comparison](../../../tests/benchmark/conftest.py#L70).
The five health assertions check HTTP 200; the five pipeline benchmarks assert no outcome; the legacy
LLM assertion checks only the `text` key; the CB assertions check states. None of those test bodies
asserts the advertised latency ceiling. The original 14 records are therefore not 14 proved SLOs.

The relocated capstone path is [replay router](../../../apps/api/app/services/evidence/simulation/router.py#L25)
to [scorecard builder](../../../apps/api/app/services/evidence/simulation/scorecard_builder.py#L41)
to [synthetic pairs](../../../apps/api/app/services/evidence/simulation/orchestrator.py#L29).
[The integration assertion](../../../tests/integration/test_baseline_vs_ama_delta.py#L21) checks five KPI
identities, not achieved targets; [the benchmark-register test](../../../tests/contract/test_evidence_benchmarks.py#L22)
checks row kinds, not source validity. Those tests are within the
[CI contract/integration command](../../../.github/workflows/ci.yml#L133).

[Paired-harness tests](../../../tests/simulation/test_paired_exercise_harness.py#L46) assert generated
response/reallocation/loss factors. The [response](../../../tests/simulation/test_sc002_lead_time_paired.py#L22),
[evacuation](../../../tests/simulation/test_sc003_evacuation_lead.py#L22), and
[reallocation](../../../tests/simulation/test_sc004_reallocation_reduction.py#L16) tests also consume the
same generator; their staging-labeled variants still do so. The long-horizon evacuation test constructs
one 72-hour example when the generated 2.5-12-hour scenarios contain none, not 30 observed long exercises.
The [economic-loss staging variant](../../../tests/measurement/sc005_economic_loss.py#L125) likewise uses
the local generator and does not load the WORM records claimed by its module description.
Searching all workflow YAML callers found no invocation of the simulation/measurement directories or
this explicit economic-loss module. This is scoped negative CI evidence, not a claim about every
possible manual command or remote job. AUD-015-016/017/018 cover these shared paths only insofar as they
are offered as evidence for feature-015's amended metrics.

## Prioritized Findings

P1 means an important correctness or misleading-pass defect; P2 means a material coverage, provenance,
or maintainability gap. Shared-service findings below are limited to obligations independently owned by
feature 015; remediation must coordinate with the service's current owner, not rewrite unrelated behavior.

| Priority | Concrete finding and impact | Follow-up |
| --- | --- | --- |
| P1 | [CI bypass](../../../tests/benchmark/conftest.py#L87) leaves a successful pytest exit unchanged despite a >=50% regression. A non-continue-on-error workflow step does not repair this. | AUD-015-001 |
| P1 | [SLO result](../../../tests/benchmark/compare_benchmarks.py#L181) is never used in status aggregation. Equality also passes strict health/pipeline/LLM limits, and dynamic CB targets are ignored. Over-budget work can print PASS or FIRST_RUN. | AUD-015-002 |
| P1 | [Constant IDs and session fixtures](../../../tests/benchmark/test_pipeline_performance.py#L189) feed deduplicators repeatedly. Calibration and measured rounds after the first attempt time rejection instead of complete processing. | AUD-015-003 |
| P1 | [Communication fixture](../../../tests/benchmark/test_pipeline_performance.py#L166) supplies an unconfigured translator MagicMock, not typed content. [The pipeline catches exceptions](../../../apps/agents/communication/pipeline.py#L159) and returns None, which the benchmark never rejects. | AUD-015-004 |
| P1 | [Resource fixture](../../../tests/benchmark/test_pipeline_performance.py#L144) never loads/adds inventory. [Inventory starts empty](../../../apps/agents/resource_allocation/inventory.py#L47), so resource matching is not meaningfully sampled even on the first accepted handoff. | AUD-015-005 |
| P1 | [Risk's default construction](../../../apps/agents/risk_assessment/pipeline.py#L75) reaches [LLMClient construction](../../../apps/agents/common/llm_mixin.py#L27), and [monitoring import](../../../apps/agents/monitoring/agent.py#L15) can configure telemetry from ambient environment. There is no suite-level hermetic guard. | AUD-015-006 |
| P1 | [The LLM fixture](../../../tests/benchmark/test_llm_performance.py#L28) forces `_chat_complete = None` and bypasses construction. [The current production branch](../../../apps/agents/common/llm_client.py#L174) is not benchmarked. | AUD-015-007 |
| P1 | [The hook's fixed file](../../../tests/benchmark/conftest.py#L72) can compare an old result after a subset/no-output run or ignore a custom output. Missing/corrupt current data returns a PASS report. | AUD-015-008 |
| P1 | [Input validation](../../../tests/benchmark/compare_benchmarks.py#L101) checks only a top-level key; wrong arrays, entries, stats, nonfinite values, and duplicate short names are not validated. Results may crash, disappear, or be misclassified. | AUD-015-009 |
| P1 | [Later measurement definitions](../../../apps/api/app/services/evidence/measurement/renderer.py#L11) change the original outcome meanings; [target scoring](../../../apps/api/app/services/evidence/simulation/scorecard_builder.py#L34) accepts any improvement rather than the amended quantitative targets. | AUD-015-016 |
| P1 | [Paired treatment factors](../../../tests/simulation/paired_exercise_harness.py#L171) guarantee improvements and [prototype baselines](../../../apps/api/app/services/evidence/benchmarks/seed.py#L211) are seeded constants. These do not establish five representative AU-v1 outcomes. | AUD-015-017 |
| P2 | [CB benchmarks](../../../tests/benchmark/test_circuit_breaker_performance.py#L48) time setup/fake-clock operations; HALF_OPEN-to-CLOSED has no separate timing and full recovery has no duration-bound assertion. | AUD-015-010 |
| P2 | [The metadata helper](../../../tests/benchmark/benchmark_helpers.py#L17) stores only three metadata keys. Comparison status, transition/configuration details, and artifact-correlated provenance are not persisted by the hook; first-run notices are not logged per metric. | AUD-015-011 |
| P2 | [Health fixtures](../../../tests/benchmark/conftest.py#L28) use empty app factories. [Resource health](../../../apps/agents/resource_allocation/agent.py#L287), for example, reports an uninitialized agent while still returning HTTP 200. Only transport success is asserted. | AUD-015-012 |
| P2 | [CI now permits five minutes](../../../.github/workflows/ci.yml#L148); the directory also collects [manual-timer tests](../../../tests/benchmark/test_pipeline_latency.py#L27) and [AIDR tests](../../../tests/benchmark/test_aidr_performance.py#L32). No complete-command <60s receipt was found. | AUD-015-013 |
| P2 | Historical native data proves artifact existence, not valid full-workload execution, baseline approval, runner-noise calibration, 30 days of accessible CI artifacts, or T032/T033 completion at this revision. | AUD-015-014 |
| P2 | [Quickstart subset commands](quickstart.md#L21) do not write fresh JSON; its native `--benchmark-compare` instruction is not the custom wrapper's comparison interface. No command-by-command rehearsal record exists locally. | AUD-015-015 |
| P2 | [Thirty-pair summary](../../../docs/aidr/exercise-summaries/spec-036-baseline.md#L3) has only [five companion raw rows](../../../tests/measurement/sc005_economic_loss.ndjson#L1); [the round-trip test](../../../tests/measurement/sc005_economic_loss.py#L109) overwrites the shared output with five pairs. | AUD-015-018 |
| P2 | [HYP-013](../../015-performance-benchmarks/spec.md#L201) references a nonexistent, nonconforming double-prefix evidence filename. Portfolio-level structural scores cannot establish this feature's consultation/uplift hypothesis. | AUD-015-019 |
| P2 | [AU persona validation labels](../../015-performance-benchmarks/spec.md#L193) are not named, dated approval evidence. [Referenced profiles](../../001-disaster-response-hub/spec.md#L169) explicitly defer concrete reviewer identities. PH/JP/BD remain correctly labeled placeholders. | AUD-015-020 |
| P2 | Plan/checklist PASS declarations and feature-028 rubric snapshots do not establish [feature-015 SC-009](../../015-performance-benchmarks/spec.md#L158), the separate Performance and reliability criterion. The 54-question performance review remains open. | AUD-015-021 |

## Original Task Coverage

Each row preserves the original checkbox literally. IMPLEMENTED describes the narrow original obligation,
not the validity of every measurement that uses it. No original task checkbox is changed by this report.

| Task | Original state | Status | Original obligation | Inspected implementation/test evidence | Follow-ups |
| --- | --- | --- | --- | --- | --- |
| T001 | [X] | IMPLEMENTED | [Create root output directory and empty keep-file](tasks.md#L22). | [.gitkeep](../../../.benchmarks/.gitkeep) exists empty and is tracked; missing-directory behavior is separately incomplete. | AUD-015-008 |
| T002 | [X] | IMPLEMENTED | [Ignore current output, retain tracked baseline](tasks.md#L23). | [.gitignore](../../../.gitignore#L33) ignores current; Git confirms baseline remains tracked despite the later broad rule. | None |
| T003 | [X] | PARTIAL | [Five session clients, async/metadata helpers, comparison hook](tasks.md#L24). | [Clients and hook](../../../tests/benchmark/conftest.py#L28); [relocated helpers](../../../tests/benchmark/benchmark_helpers.py#L12). Hook, setup fidelity, and isolation gaps remain. | AUD-015-001, AUD-015-006, AUD-015-008, AUD-015-012 |
| T004 | [X] | IMPLEMENTED | [ComparisonReport and MetricComparison fields](tasks.md#L34). | [Both dataclasses](../../../tests/benchmark/compare_benchmarks.py#L53) include timestamp, SHA, paths, verdict, results, and summary. Persistence is a separate gap. | AUD-015-011 |
| T005 | [X] | IMPLEMENTED | [Named health/pipeline/LLM SLO registry](tasks.md#L35). | [All eleven specified constants](../../../tests/benchmark/compare_benchmarks.py#L29) have the intended numeric values; enforcement is separate. | AUD-015-002 |
| T006 | [X] | PARTIAL | [Load and validate malformed native JSON with warnings](tasks.md#L36). | [Loader](../../../tests/benchmark/compare_benchmarks.py#L85) handles parse/missing-key errors but not array, entry, or numeric schema validity. | AUD-015-009 |
| T007 | [X] | IMPLEMENTED | [Read git SHA or return unknown](tasks.md#L37). | [get_commit_sha](../../../tests/benchmark/compare_benchmarks.py#L108) checks return code and catches process/timeout errors. No runtime fallback exercise performed. | AUD-015-011 |
| T008 | [X] | PARTIAL | [50/20% thresholds, PASS, FIRST_RUN, BASELINE_ONLY, zero-baseline handling](tasks.md#L38). | [Comparison branches](../../../tests/benchmark/compare_benchmarks.py#L184) exist for well-formed inputs; schema/identity, invalid current values, and notice gaps remain; no dedicated assertion suite found. | AUD-015-008, AUD-015-009, AUD-015-011 |
| T009 | [X] | IMPLEMENTED | [Human-readable statuses, names, SLO values, changes](tasks.md#L39). | [Formatter](../../../tests/benchmark/compare_benchmarks.py#L330) and [encoding fallback](../../../tests/benchmark/conftest.py#L79) are authored. SLO labels do not make verdicts correct. | AUD-015-002, AUD-015-011 |
| T010 | [X] | IMPLEMENTED | [Replace concurrent load test with monitoring GET health, group, 0.100s metadata, HTTP 200](tasks.md#L53). | [Monitoring benchmark](../../../tests/benchmark/test_api_performance.py#L17) follows the specified pattern; no old concurrent batch remains in that file. | AUD-015-002, AUD-015-012 |
| T011 | [X] | IMPLEMENTED | [Risk health benchmark, 0.075s](tasks.md#L54). | [Risk benchmark](../../../tests/benchmark/test_api_performance.py#L27) calls the real health route with metadata and status assertion. | AUD-015-002, AUD-015-012 |
| T012 | [X] | IMPLEMENTED | [Evacuation health benchmark, 0.075s](tasks.md#L55). | [Evacuation benchmark](../../../tests/benchmark/test_api_performance.py#L37) calls the route and checks HTTP 200, not initialized-state work. | AUD-015-002, AUD-015-012 |
| T013 | [X] | IMPLEMENTED | [Resource health benchmark, 0.100s](tasks.md#L56). | [Resource benchmark](../../../tests/benchmark/test_api_performance.py#L47) has the required call and metadata. | AUD-015-002, AUD-015-012 |
| T014 | [X] | IMPLEMENTED | [Communication health benchmark, 0.100s](tasks.md#L57). | [Communication benchmark](../../../tests/benchmark/test_api_performance.py#L57) has the required call and metadata. | AUD-015-002, AUD-015-012 |
| T015 | [X] | CONFLICT | [Print comparison and set exit 1 on failures](tasks.md#L71). | [Hook](../../../tests/benchmark/conftest.py#L87) adds a CI exemption that contradicts the obligation. | AUD-015-001, AUD-015-008 |
| T016 | [X] | SUPERSEDED | [Initial empty baseline placeholder](tasks.md#L72). | [T033](tasks.md#L137) expressly promotes measured data; [tracked baseline records](../../../.benchmarks/baseline.json#L151) replace the placeholder. Do not recreate an empty baseline. | AUD-015-014 |
| T017 | [X] | PARTIAL | [Five pipeline factories with LLM mocks and disconnected stores](tasks.md#L86). | [Factories](../../../tests/benchmark/test_pipeline_performance.py#L94) exist, but risk uses default LLM construction, resource inventory is empty, and translator outputs are unspecified. | AUD-015-003, AUD-015-004, AUD-015-005, AUD-015-006 |
| T018 | [X] | PARTIAL | [Monitoring async process_signal and 2s median](tasks.md#L87). | [asyncio.run benchmark](../../../tests/benchmark/test_pipeline_performance.py#L189) awaits work, but repeats one signal ID; [unit test](../../../tests/unit/test_monitoring_pipeline.py#L141) separately asserts dedup behavior. | AUD-015-002, AUD-015-003, AUD-015-006 |
| T019 | [X] | PARTIAL | [Risk synchronous full pipeline, 2s](tasks.md#L88). | [Benchmark](../../../tests/benchmark/test_pipeline_performance.py#L196), [intake](../../../apps/agents/risk_assessment/pipeline.py#L97), and [unit duplicate assertion](../../../tests/unit/test_risk_assessment_pipeline.py#L77) expose the repeated-ID path. | AUD-015-002, AUD-015-003, AUD-015-006 |
| T020 | [X] | PARTIAL | [Evacuation synchronous full pipeline, 2s](tasks.md#L89). | [Benchmark](../../../tests/benchmark/test_pipeline_performance.py#L203) loads the sample road network but repeats the handoff; [unit tests](../../../tests/unit/test_evacuation_pipeline.py#L148) distinguish plan from duplicate None. | AUD-015-002, AUD-015-003 |
| T021 | [X] | PARTIAL | [Resource synchronous full pipeline, 2s](tasks.md#L90). | [Benchmark](../../../tests/benchmark/test_pipeline_performance.py#L210) repeats IDs and supplies no resources; [unit fixtures](../../../tests/unit/test_resource_allocation_pipeline.py#L48) show usable populated inventory. | AUD-015-002, AUD-015-003, AUD-015-005 |
| T022 | [X] | PARTIAL | [Communication synchronous full pipeline, 2s](tasks.md#L91). | [Benchmark](../../../tests/benchmark/test_pipeline_performance.py#L217) ignores output; [unit positive case](../../../tests/unit/test_communication_pipeline.py#L86) instead configures ContentBlock and asserts PublicAlert. | AUD-015-002, AUD-015-003, AUD-015-004 |
| T023 | [X] | PARTIAL | [Instant SDK-shaped LLM response fixture](tasks.md#L105). | [Legacy fixture](../../../tests/benchmark/test_llm_performance.py#L21) exists, but bypasses constructor and the current production branch. | AUD-015-007 |
| T024 | [X] | PARTIAL | [generate_response overhead, shared metadata, text assertion, 0.500s](tasks.md#L106). | [Benchmark](../../../tests/benchmark/test_llm_performance.py#L49) measures the legacy happy path only and has no SLO assertion. | AUD-015-002, AUD-015-007 |
| T025 | [X] | IMPLEMENTED | [Import common breaker and use 0.1s timeout](tasks.md#L120). | [Imports/constant](../../../tests/benchmark/test_circuit_breaker_performance.py#L10) satisfy the setup task. | AUD-015-010 |
| T026 | [X] | IMPLEMENTED | [Time three failures reaching OPEN](tasks.md#L121). | [Closed-to-open test](../../../tests/benchmark/test_circuit_breaker_performance.py#L21) times the operation and asserts OPEN; construction is included in its sample. | AUD-015-010 |
| T027 | [X] | PARTIAL | [Time OPEN-to-HALF_OPEN after timeout](tasks.md#L122). | [Fake-clock test](../../../tests/benchmark/test_circuit_breaker_performance.py#L48) verifies state; the [module contract](contracts/benchmark-modules.md#L190) permits clock injection, but elapsed recovery is not recorded. | AUD-015-010 |
| T028 | [X] | PARTIAL | [Full recovery cycle and <=2x timeout assertion](tasks.md#L123). | [Full-cycle test](../../../tests/benchmark/test_circuit_breaker_performance.py#L77) asserts states and attaches metadata, not the duration bound; comparator has no CB target. | AUD-015-002, AUD-015-010 |
| T029 | [X] | CONFLICT | [Whole-directory JSON invocation and two-minute safeguard](tasks.md#L133). | [CI](../../../.github/workflows/ci.yml#L148) has the invocation but a five-minute timeout. No feature-015 waiver was found in its inputs. | AUD-015-013 |
| T030 | [X] | IMPLEMENTED | [Upload always, named results artifact, native JSON path, 30-day retention](tasks.md#L134). | [Upload configuration](../../../.github/workflows/ci.yml#L152) preserves these behaviors with a pinned newer action version; actual uploads are unverified. | AUD-015-011, AUD-015-014 |
| T031 | [X] | UNVERIFIED | [Temporary feature push trigger](tasks.md#L135). | [Current triggers](../../../.github/workflows/ci.yml#L3) omit it; [contract](contracts/ci-workflow.md#L70) explicitly allows removal after merge. Absence today does not prove the historical task was missed. | AUD-015-014 |
| T032 | [X] | UNVERIFIED | [Execute full suite, validate JSON/report, confirm exit zero](tasks.md#L136). | Historical JSON has no matching full-command transcript or exit receipt; current source exposes false-pass paths. No execution was performed here. | AUD-015-014 |
| T033 | [X] | PARTIAL | [Promote verified results and commit reference baseline](tasks.md#L137). | [A baseline is tracked](../../../.benchmarks/baseline.json#L141); its representative workload, promotion review, and current compatibility are unverified. | AUD-015-003, AUD-015-014 |
| T034 | [X] | UNVERIFIED | [Execute every quickstart command and verify it](tasks.md#L138). | [Quickstart](quickstart.md#L1) is authored; no local rehearsal receipt proves command correctness or execution. | AUD-015-015 |

## Requirement and Success-Criterion Coverage

| ID | Status | Original obligation and evidence | Follow-ups |
| --- | --- | --- | --- |
| FR-001 | IMPLEMENTED | [Five in-process GET health measurements](../../015-performance-benchmarks/spec.md#L121) are present in [health tests](../../../tests/benchmark/test_api_performance.py#L17); realism and CI outcome are separate. | AUD-015-012, AUD-015-014 |
| FR-002 | PARTIAL | [Full direct pipelines including async monitoring](../../015-performance-benchmarks/spec.md#L122): [all calls exist](../../../tests/benchmark/test_pipeline_performance.py#L189), but duplicate state and incomplete fixture workloads invalidate full-workload medians. | AUD-015-003, AUD-015-004, AUD-015-005, AUD-015-006 |
| FR-003 | PARTIAL | [Mocked application-side LLM overhead](../../015-performance-benchmarks/spec.md#L123): [legacy mock](../../../tests/benchmark/test_llm_performance.py#L21) excludes the now-current Foundry branch. | AUD-015-007 |
| FR-004 | PARTIAL | [Three transition timings and total recovery](../../015-performance-benchmarks/spec.md#L124): [three tests](../../../tests/benchmark/test_circuit_breaker_performance.py#L21) omit a separate HALF_OPEN-to-CLOSED measurement and actual total recovery duration. | AUD-015-010 |
| FR-005 | CONFLICT | [Strict health/pipeline/LLM and inclusive recovery limits](../../015-performance-benchmarks/spec.md#L125): [registry exists](../../../tests/benchmark/compare_benchmarks.py#L29), but verdict ignores SLO failure and uses inclusive comparison everywhere. | AUD-015-002 |
| FR-006 | PARTIAL | [Native root JSON plus SLO/regression metadata](../../015-performance-benchmarks/spec.md#L130): [CI output](../../../.github/workflows/ci.yml#L150) and three extra keys exist; structured comparison results are not persisted. | AUD-015-008, AUD-015-011 |
| FR-007 | PARTIAL | [>=20% visible nonblocking warning](../../015-performance-benchmarks/spec.md#L131): [logger.warning branch](../../../tests/benchmark/compare_benchmarks.py#L232) exists for valid matching records; input/freshness correctness lacks assurance. | AUD-015-008, AUD-015-009 |
| FR-008 | CONFLICT | [>=50% must fail CI](../../015-performance-benchmarks/spec.md#L132) is contradicted by [CI exemption](../../../tests/benchmark/conftest.py#L87). | AUD-015-001 |
| FR-009 | PARTIAL | [All external services mocked](../../015-performance-benchmarks/spec.md#L133): several dependencies are disconnected, but [default risk client](../../../apps/agents/common/llm_mixin.py#L27) and [environment-triggered telemetry](../../../apps/agents/monitoring/agent.py#L15) remain reachable. | AUD-015-006 |
| FR-010 | CONFLICT | [All timing via pytest-benchmark](../../015-performance-benchmarks/spec.md#L134): all original 14 use the fixture, while the whole-directory CI command also collects [manual timers](../../../tests/benchmark/test_pipeline_latency.py#L35). | AUD-015-013 |
| FR-011 | IMPLEMENTED | [Uploadable structured artifacts](../../015-performance-benchmarks/spec.md#L135): native JSON and [upload-always configuration](../../../.github/workflows/ci.yml#L152) exist. | AUD-015-011, AUD-015-014 |
| FR-012 | PARTIAL | [Per-metric first-run/removed notices](../../015-performance-benchmarks/spec.md#L136): [FIRST_RUN](../../../tests/benchmark/compare_benchmarks.py#L184) is only appended, while [BASELINE_ONLY](../../../tests/benchmark/compare_benchmarks.py#L266) logs at INFO, normally hidden by default logging. | AUD-015-009, AUD-015-011 |
| FR-013 | IMPLEMENTED | [Continue after individual errors](../../015-performance-benchmarks/spec.md#L137): [lazy per-agent fixtures](../../../tests/benchmark/conftest.py#L28), [no fail-fast addopts](../../../pyproject.toml#L43), and session-end aggregation support it statically. No fault-injection execution was observed. | AUD-015-001, AUD-015-009, AUD-015-014 |
| SC-001 | PARTIAL | [Every CI run records/checks five agents](../../015-performance-benchmarks/spec.md#L150): directory invocation exists; SLO verdict is ineffective and actual run evidence is absent. | AUD-015-002, AUD-015-014 |
| SC-002 | CONFLICT | [75ms safety-critical versus 100ms general](../../015-performance-benchmarks/spec.md#L151): correct constants do not hold agents to a ceiling without enforcement. | AUD-015-002 |
| SC-003 | UNVERIFIED | [All pipelines under 2s on every CI run](../../015-performance-benchmarks/spec.md#L152): saved repeated-ID timings are not representative pipeline evidence. | AUD-015-003, AUD-015-014 |
| SC-004 | PARTIAL | [Automatic >=20% warnings](../../015-performance-benchmarks/spec.md#L153): comparison branch exists; current-run correlation and synthetic boundary assertion coverage are incomplete. | AUD-015-008, AUD-015-009 |
| SC-005 | CONFLICT | [>=50% regressions block merging](../../015-performance-benchmarks/spec.md#L154): hook explicitly prevents regression-driven failure in CI; branch protection state was not queried. | AUD-015-001 |
| SC-006 | UNVERIFIED | [At least 30 days of accessible history](../../015-performance-benchmarks/spec.md#L155): [retention-days 30](../../../.github/workflows/ci.yml#L159) is authored policy, not proof of actual historical artifact availability. | AUD-015-014 |
| SC-007 | UNVERIFIED | [Entire command under 60s](../../015-performance-benchmarks/spec.md#L156): no complete wall-clock receipt; [five-minute cap](../../../.github/workflows/ci.yml#L149) also disagrees with the two-minute safeguard. | AUD-015-013, AUD-015-014 |
| SC-008 | PARTIAL | [Chaos-comparable state/timing/SHA structure](../../015-performance-benchmarks/spec.md#L157): names imply some transitions, but [metadata](../../../tests/benchmark/benchmark_helpers.py#L17) omits explicit clock, threshold, timeout, and transition records. No chaos tool is required. | AUD-015-010, AUD-015-011 |
| SC-009 | UNVERIFIED | [Performance and reliability score 3 to >=4](../../015-performance-benchmarks/spec.md#L158): [actual rubric row](../../../AMA_Rubric_Asia.md#L47) has no feature-015-specific dated assessment in reviewed evidence. | AUD-015-021 |
| SC-CAP-015-001 | PARTIAL | [>=1,000 lives/year and major-flood pre/post outcomes](../../015-performance-benchmarks/spec.md#L208): [seeded 50-life baseline](../../../apps/api/app/services/evidence/benchmarks/seed.py#L305) and [test-input subtraction](../../../apps/api/app/services/outcome_evaluator_service.py#L132) do not establish an annualized, calibrated estimate. | AUD-015-016, AUD-015-017 |
| SC-CAP-015-002 | CONFLICT | [50% faster alert-to-acknowledgement median](../../015-performance-benchmarks/spec.md#L209): [later definition](../../../apps/api/app/services/evidence/measurement/renderer.py#L20) uses call-to-arrival; replay sets a 0.55 factor and accepts any improvement. | AUD-015-016, AUD-015-017 |
| SC-CAP-015-003 | CONFLICT | [24h earlier warning-to-recommended-start outcome](../../015-performance-benchmarks/spec.md#L210): [renderer](../../../apps/api/app/services/evidence/measurement/renderer.py#L28) uses completion; paired output uses simulated order times, not that measured delta. | AUD-015-016, AUD-015-017 |
| SC-CAP-015-004 | CONFLICT | [30% allocated-versus-idle utilisation uplift](../../015-performance-benchmarks/spec.md#L211): [inventory utilisation](../../../apps/agents/resource_allocation/inventory.py#L258) exists but is not connected to the benchmark; route acceptance, clicks, and reallocations are different measures. | AUD-015-005, AUD-015-016, AUD-015-017 |
| SC-CAP-015-005 | PARTIAL | [30% Sendai-aligned modelled loss reduction](../../015-performance-benchmarks/spec.md#L212): [synthetic loss model](../../../tests/simulation/paired_exercise_harness.py#L171) and summary exist, but calibration/provenance are absent and raw-summary coverage disagrees. Modelled evidence is allowed; guaranteed improvement is not validation. | AUD-015-016, AUD-015-017, AUD-015-018 |

## Acceptance-Scenario Coverage

AS labels below are audit identifiers for the original numbered scenarios, preserving all 13 separately.

| Scenario | Status | Expected behavior and inspected support | Follow-ups |
| --- | --- | --- | --- |
| US1-AS1 | PARTIAL | [Five health medians and 100/75ms SLO comparison](../../015-performance-benchmarks/spec.md#L10): all names recorded, but no effective ceiling verdict. | AUD-015-002, AUD-015-012 |
| US1-AS2 | PARTIAL | [25% health regression warns](../../015-performance-benchmarks/spec.md#L10): valid-record comparison branch supports it; no dedicated synthetic assertion or CI receipt. | AUD-015-009, AUD-015-014 |
| US1-AS3 | CONFLICT | [55% health regression fails CI](../../015-performance-benchmarks/spec.md#L10): CI exemption suppresses the failure exit. | AUD-015-001 |
| US2-AS1 | PARTIAL | [Five mocked full pipelines below 2s](../../015-performance-benchmarks/spec.md#L26): repeated IDs and incomplete mocks do not represent that workload. | AUD-015-002, AUD-015-003, AUD-015-004, AUD-015-005, AUD-015-006 |
| US2-AS2 | PARTIAL | [30% evacuation regression warns and names agent](../../015-performance-benchmarks/spec.md#L26): formatter identifies the benchmark, but the sampled path is duplicate intake. | AUD-015-003, AUD-015-009 |
| US3-AS1 | PARTIAL | [Mocked round trip below 500ms](../../015-performance-benchmarks/spec.md#L41): legacy-path timing exists, current-path timing and enforced limit do not. | AUD-015-002, AUD-015-007 |
| US3-AS2 | PARTIAL | [>=20% retry/parsing overhead warns](../../015-performance-benchmarks/spec.md#L41): only one legacy success response is exercised; current branch and retry/error fixtures are absent from timing coverage. | AUD-015-007, AUD-015-009 |
| US4-AS1 | IMPLEMENTED | [Three failures reach OPEN and record operation time](../../015-performance-benchmarks/spec.md#L56): [test](../../../tests/benchmark/test_circuit_breaker_performance.py#L21) asserts OPEN. Below-threshold behavior is separately asserted in [contract tests](../../../tests/contract/test_llm_circuit_breaker.py#L34). | AUD-015-010 |
| US4-AS2 | PARTIAL | [OPEN through HALF_OPEN to CLOSED, recovery <=2x timeout](../../015-performance-benchmarks/spec.md#L56): state assertions exist, recovery elapsed time and bound do not. | AUD-015-010 |
| US5-AS1 | PARTIAL | [Native timestamp/agent/statistics/SLO output, derivable percentiles](../../015-performance-benchmarks/spec.md#L71): historical records contain these; missing comparison metadata and current-run provenance remain. | AUD-015-008, AUD-015-011 |
| US5-AS2 | PARTIAL | [>=20% baseline-relative warning](../../015-performance-benchmarks/spec.md#L71): valid comparison logic exists, with no parser/threshold contract test coverage located. | AUD-015-009 |
| US5-AS3 | CONFLICT | [>=50% baseline-relative CI failure](../../015-performance-benchmarks/spec.md#L71): not enforced when CI is set. | AUD-015-001 |
| US5-AS4 | UNVERIFIED | [PR reviewer downloads and compares historical artifact](../../015-performance-benchmarks/spec.md#L71): upload configuration exists; no download/retention execution receipt reviewed. | AUD-015-014 |

## Edge-Case Coverage

| Edge | Status | Original case and observed boundary | Follow-ups |
| --- | --- | --- | --- |
| EC-01 | PARTIAL | [No baseline](../../015-performance-benchmarks/spec.md#L88): current metrics become FIRST_RUN; per-metric notice is not logged and no automatic baseline overwrite occurs. | AUD-015-011 |
| EC-02 | IMPLEMENTED | [One agent fails to start](../../015-performance-benchmarks/spec.md#L88): lazy fixtures and default pytest continuation permit other cases; actual failure-injection result remains unverified. | AUD-015-001, AUD-015-014 |
| EC-03 | PARTIAL | [In-process mocks eliminate network/mock-server delay](../../015-performance-benchmarks/spec.md#L88): instant legacy LLM mock exists, but risk/default telemetry paths are not isolated. | AUD-015-006, AUD-015-007 |
| EC-04 | MISSING | [Output directory absent](../../015-performance-benchmarks/spec.md#L88): no creation in benchmark code or CI invocation; installed plugin's file-opening option requires the parent to exist. A tracked keep-file only handles clean checkouts. | AUD-015-008 |
| EC-05 | UNVERIFIED | [20/50% tolerates runner variability](../../015-performance-benchmarks/spec.md#L88): no repeated like-for-like runner study; skipping failures in CI is not the specified relative-comparison mitigation. | AUD-015-001, AUD-015-014 |
| EC-06 | PARTIAL | [New metric absent from baseline](../../015-performance-benchmarks/spec.md#L88): FIRST_RUN branch and formatted NEW label exist, but promised logging notice and validity checks are incomplete. | AUD-015-009, AUD-015-011 |
| EC-07 | IMPLEMENTED | [Baseline-only metric](../../015-performance-benchmarks/spec.md#L88): [BASELINE_ONLY branch](../../../tests/benchmark/compare_benchmarks.py#L259) reports removal and does not mark regression; visible notice configuration needs follow-up. | AUD-015-011 |
| EC-08 | CONFLICT | [Warnings visible/nonblocking; failures nonzero](../../015-performance-benchmarks/spec.md#L88): warning logging exists, CI failure behavior is explicitly disabled. | AUD-015-001 |

## Clarifications and Amendments

| Decision | Status | Full decision coverage | Follow-ups |
| --- | --- | --- | --- |
| C01 | PARTIAL | [Session 1: native pytest-benchmark JSON plus thin wrapper](../../015-performance-benchmarks/spec.md#L103). Native records exist; comparison metadata is not archived. | AUD-015-011 |
| C02 | IMPLEMENTED | [Session 1: repository-root output is canonical](../../015-performance-benchmarks/spec.md#L104). Hook and CI use it; alternate working directory/output handling still needs repair. | AUD-015-008 |
| C03 | IMPLEMENTED | [Session 1: replace old concurrent health benchmark in place](../../015-performance-benchmarks/spec.md#L105). Current file contains five single-request functions. | None |
| C04 | PARTIAL | [Session 1: direct pipeline entry points, not full HTTP processing](../../015-performance-benchmarks/spec.md#L106). Entry points are correct; their repeated samples are not full processing. | AUD-015-003 |
| C05 | CONFLICT | [Session 1: uniform <2s pipeline limit](../../015-performance-benchmarks/spec.md#L107). Registry is uniform, verdict enforcement is absent. | AUD-015-002 |
| C06 | CONFLICT | [Session 2: logging warnings versus failure exit](../../015-performance-benchmarks/spec.md#L111). CI bypass conflicts with this clarification. | AUD-015-001 |
| C07 | UNVERIFIED | [Session 2: entire command <60s, two-minute safeguard](../../015-performance-benchmarks/spec.md#L112). No elapsed receipt; current timeout is five minutes. | AUD-015-013, AUD-015-014 |
| C08 | PARTIAL | [Session 2: chaos support is schema only](../../015-performance-benchmarks/spec.md#L113). No missing chaos comparison tool is claimed; explicit transition/configuration data still needs implementation. | AUD-015-010, AUD-015-011 |
| C09 | PARTIAL | [Session 2: first-run semantics for new metrics; notice-only removed metrics](../../015-performance-benchmarks/spec.md#L114). Branches exist but visible per-metric notices are incomplete. | AUD-015-011 |
| C10 | PARTIAL | [Session 2: async monitoring and commit SHA metadata](../../015-performance-benchmarks/spec.md#L115). Async execution and SHA helper exist; comparison provenance is not persisted/correlated to the selected artifact. | AUD-015-008, AUD-015-011 |
| PER-037 | PARTIAL | [AU operational persona cross-reference](../../015-performance-benchmarks/spec.md#L193) and [role descriptions](../../001-disaster-response-hub/spec.md#L169) exist; named/date-specific SME validation is not established. | AUD-015-020 |
| PER-038 | PARTIAL | [Technical actor cross-reference](../../015-performance-benchmarks/spec.md#L194) exists; it is a group reference, not a feature-scoped approval receipt. | AUD-015-020 |
| PER-039 | IMPLEMENTED | [PH/JP/BD placeholder and promotion preconditions](../../015-performance-benchmarks/spec.md#L195) are explicit. No overseas validation or baseline is claimed by this audit. | AUD-015-020 |
| HYP-013 | MISSING | [The promised stub](../../015-performance-benchmarks/spec.md#L201) was not located by filename/content searches; consultation and feature-specific score uplift remain UNVERIFIED. | AUD-015-019 |

The five SC-CAP-015 amendments are individually covered in the requirement table. The full
[capstone trace](../../shared/capstone-metric-trace.md#L1) was inspected: five AU-v1 rows say Validated and
15 PH/JP/BD rows say Deferred. These labels assign ownership; they are not observations or permission
to promote a country cohort. Neither this report nor future offline harness fixes clear D-009 or SME gates.

### Assumptions, Dependencies, and Boundaries

| ID | Status | Evidence and qualification | Follow-ups |
| --- | --- | --- | --- |
| A-001 | PARTIAL | [In-process client fixtures](../../../tests/benchmark/conftest.py#L28) exist; they do not prove initialized normal-state agent workloads or measured setup duration. | AUD-015-012, AUD-015-014 |
| A-002 | PARTIAL | Direct pipeline calls exist, but session state and mock fidelity compromise representative processing. | AUD-015-003, AUD-015-004, AUD-015-005 |
| A-003 | PARTIAL | LLM injection is possible through [constructor chat_complete](../../../apps/agents/common/llm_client.py#L55); benchmark currently uses legacy private fields. | AUD-015-007 |
| A-004 | IMPLEMENTED | [Common breaker methods](../../../apps/agents/common/circuit_breaker.py#L69) directly drive transitions without network failures. | AUD-015-010 |
| A-005 | UNVERIFIED | Old Windows measurements versus Linux CI and no noise-calibration receipt cannot establish consistent relative timing. | AUD-015-014 |
| A-006 | IMPLEMENTED | The existing plugin supplies native timing/raw samples; no extra timing framework is needed to repair the original suite. | AUD-015-013 |
| A-007 | IMPLEMENTED | Root paths and tracked baseline are present; no evidence claims the old agents-local directory is canonical. | AUD-015-008 |
| D-001 | IMPLEMENTED | [Root dev minimum](../../../pyproject.toml#L27), [agent dependency](../../../apps/agents/pyproject.toml#L20), and [CI installation](../../../.github/workflows/ci.yml#L39) exist. CI's actual resolved version is unverified. | AUD-015-014 |
| D-002 | IMPLEMENTED | All five inspected application factories expose GET health. | AUD-015-012 |
| D-003 | IMPLEMENTED | [LLMClient exists](../../../apps/agents/common/llm_client.py#L44); its production implementation changed while the benchmark boundary did not. | AUD-015-007 |
| D-004 | IMPLEMENTED | [Common circuit breaker exists](../../../apps/agents/common/circuit_breaker.py#L26). The ingestion breaker is a different implementation and not substitute evidence. | AUD-015-010 |
| D-005 | PARTIAL | [CI invocation/upload](../../../.github/workflows/ci.yml#L148) exist, but bypass and timeout conflict remain. | AUD-015-001, AUD-015-013 |
| D-006 | IMPLEMENTED | [Original health file](../../../tests/benchmark/test_api_performance.py#L1) is replaced in place; the old concurrent worker pattern is absent. | None |

All six original exclusions remain boundaries: no high-concurrency load/stress requirement, no live
Azure/LLM timing, no dashboard implementation, no frontend timing, no database timing, and no automatic
baseline promotion. Later evidence services are inspected only to trace the amendments, not to authorize
unrelated fixes. Recommendations below preserve these exclusions and keep external approvals future-only.

## Review and Checklist Evidence

[The requirements checklist](../../015-performance-benchmarks/checklists/requirements.md#L9) has 16 `[x]` items. Its statement that the
feature meets measurable outcomes is authored specification-readiness text, not a benchmark run.
[The performance checklist](../../015-performance-benchmarks/checklists/performance.md#L14) has 54 `[ ]` items. Research answers several
questions, but no checked review or named approver was found locally. Questions identifying gaps do not,
by themselves, create new mandatory product requirements.

The following disposition covers every CHK ID; every original state remains unchecked:

| Checklist IDs | Status | Evidence assessment / required follow-up |
| --- | --- | --- |
| CHK001, CHK003, CHK006, CHK018, CHK052 | PARTIAL | Research R-005/R-006 defines async wrappers, default calibration, serial execution, and grouping; repeated-ID fidelity and later non-plugin tests remain. AUD-015-003, AUD-015-013. |
| CHK002, CHK013, CHK020, CHK039, CHK049 | PARTIAL | R-009 and quickstart define explicit root baseline promotion; no fresh-input/compatibility or approval record proves it safe. AUD-015-008, AUD-015-014, AUD-015-015. |
| CHK004, CHK005, CHK007, CHK010, CHK011, CHK044 | PARTIAL | Comparison interface and human formatter are authored; accurate verdicts, notices, and persisted report fields remain incomplete. AUD-015-002, AUD-015-009, AUD-015-011. |
| CHK008, CHK015, CHK043, CHK050, CHK053 | PARTIAL | CI contract describes output/upload and 30-day retention; configuration partly matches, execution and timeout compliance do not. AUD-015-013, AUD-015-014. |
| CHK009, CHK023, CHK032, CHK037 | PARTIAL | Five explicit fixtures/default continuation support report-all; no complete fault-injection test receipt or missing-agent manifest check. AUD-015-001, AUD-015-009, AUD-015-014. |
| CHK012, CHK027, CHK038 | PARTIAL | CB contract permits clocks and states a recovery budget, but individual transition/recovery/configuration evidence is incomplete. AUD-015-010, AUD-015-011. |
| CHK014, CHK029, CHK030, CHK031, CHK041, CHK046, CHK047 | UNVERIFIED | Runner noise, variance, resource pressure, concurrent-file isolation, and resolved-version suitability have no measured validation record. Assess proportionately, without introducing load testing. AUD-015-013, AUD-015-014. |
| CHK016, CHK035, CHK036, CHK040, CHK042 | PARTIAL | SHA fallback and corruption policy exist; shape/numeric validation, identity, artifact integrity, and schema compatibility need explicit decisions/tests. AUD-015-008, AUD-015-009, AUD-015-011. |
| CHK017, CHK034, CHK045, CHK048 | PARTIAL | R-007/R-012 define client boundaries, but current production-path mocks and initialized health fixtures are not represented. AUD-015-006, AUD-015-007, AUD-015-012. |
| CHK019, CHK021, CHK022, CHK026, CHK028 | CONFLICT | R-004/R-010 resolve 20/50% examples and inclusive regression thresholds; SLO enforcement and CI failure disagree with the approved semantics. AUD-015-001, AUD-015-002, AUD-015-009. |
| CHK024, CHK025, CHK033, CHK051, CHK054 | UNVERIFIED | External rubric assessment, full-command/setup duration, execution traceability, and maintained benchmark scope require evidence beyond authored gates. AUD-015-013, AUD-015-014, AUD-015-021. |

[Feature-028 baseline](../../028-capstone-alignment/evidence/rubric-baseline.md#L1) and
[post-feature snapshot](../../028-capstone-alignment/evidence/rubric-postfeature.md#L1) score five structural
criteria across 27 specifications. They do not score feature-015's Performance and reliability criterion
or prove per-change actor consultation. The [persona contract](../../027-spec-hardening/contracts/persona-profile.md#L15)
requires named, dated validation; a role-only label is not a recorded approval. The
[hypothesis contract](../../028-capstone-alignment/contracts/evidence-stub.contract.md#L1) requires a
single-prefix filename and six sections; the advertised HYP-HYP-013 file is absent.

## Open Remediation Tasks

All tasks below are future work. Source-owner links identify implementation surfaces, not authorization
to edit them during this audit. Positive, negative, and edge cases are tester instructions, not executed
results. V01-V10 refer to the future-only validation matrix that follows.

- [ ] **AUD-015-001 (P1): Restore the CI regression failure contract.**

**Obligations:** T015, FR-008, SC-005, US1-AS3, US5-AS3, C06/EC-08. Expected >=50% to fail after all cases; actual CI exemption preserves success, allowing regressions through.
**Developer:** Owner [session hook](../../../tests/benchmark/conftest.py#L70). Remove environment-based suppression, preserve pre-existing pytest error/interruption exits, and aggregate all comparisons. Keep warnings nonblocking; address hardware comparability through AUD-015-014, not a bypass. Dependencies: AUD-015-008/009 for trustworthy inputs.
**Tester:** In the proposed V01 reporting tests, inject 19%, 20%, 25%, 49.9%, 50%, and 55% records with CI both present and absent. Positive: warnings exit zero. Negative: any failure exits nonzero. Edge: simultaneous regressions plus a fixture error still report other agents and preserve failure.
**Completion:** Identical local/CI classification for all valid fixtures, no failure downgraded, all metrics reported. V01 then V07; NOT RUN.

- [ ] **AUD-015-002 (P1): Enforce SLOs independently of relative regressions.**

**Obligations:** T005/T009/T018-T024/T028, FR-005, SC-001/002/003. Expected strict 100/75ms, 2s, 500ms limits and inclusive <=2x recovery; actual `slo_pass` is unused and CB targets are absent from lookup.
**Developer:** Owner [comparison](../../../tests/benchmark/compare_benchmarks.py#L175) and [formatter](../../../tests/benchmark/compare_benchmarks.py#L330). Represent absolute SLO failure explicitly, including FIRST_RUN, improving, and zero-baseline cases. Validate dynamic CB targets; do not silently loosen thresholds or change percentage-warning semantics. Coordinate the incomplete SLO-verdict design with the SRE owner.
**Tester:** Positive: V01 fixtures just below each strict ceiling pass, and recovery exactly twice timeout passes. Negative: exactly at/above strict ceilings, 80ms risk with unchanged baseline, 2.1s improving pipeline, and over-budget first run fail. Edge: a genuinely targetless metric still gets regression checking.
**Completion:** No over-budget required metric is green; report and structured verdict agree. V01, V04-V07; NOT RUN. Depends on AUD-015-009; the resulting SLO policy is an input to AUD-015-010.

- [ ] **AUD-015-003 (P1): Make every pipeline timing sample execute the full intended work.**

**Obligations:** T017-T022, FR-002, US2, SC-003. Expected repeated full processing; actual session-scoped caches and constant handoff/signal IDs redirect subsequent iterations to duplicate rejection.
**Developer:** Owner [pipeline benchmarks](../../../tests/benchmark/test_pipeline_performance.py#L94). Reset per-sample state using setup outside the measured region, or construct genuinely independent inputs including communication's incident/hazard key. Keep real pipeline/dedup behavior; do not disable production dedup. Bound audit/version/inventory/road-state accumulation. Monitoring success must be checked through stage/audit/delivery observations because its return is normally None.
**Tester:** Reuse all five [pipeline unit-test patterns](../../../tests/unit/test_monitoring_pipeline.py#L63). Positive: calibration and at least ten measured samples each reach terminal stages. Negative: deliberate duplicate sample is detected by the benchmark guard. Edge: unique handoff IDs with one communication incident/hazard must not silently pass as full work.
**Completion:** Zero duplicate/error samples counted as successful full-workload timings, explicit terminal assertions for all five agents. V02/V03, then new approved baseline via AUD-015-014; NOT RUN.

- [ ] **AUD-015-004 (P1): Give communication benchmarks valid, asserted content outputs.**

**Obligations:** T017/T022, FR-002/009, US2-AS1. Expected drafting/back-translation/safety/versioning workload; actual unconfigured translator mock permits empty or exception-return paths with no result assertion.
**Developer:** Owner [communication fixture](../../../tests/benchmark/test_pipeline_performance.py#L166); reuse the typed [unit fixture example](../../../tests/unit/test_communication_pipeline.py#L86). Return concrete ContentBlock dictionaries, deterministic back-translation values, and controlled safety dependencies. Keep approval/delivery outside the process_handoff timing boundary as the real pipeline does. Depends on AUD-015-003/006.
**Tester:** Positive: nonempty PublicAlert with expected languages and version each sample. Negative: translator exception, missing English block, invalid block, or swallowed pipeline error cannot count as a normal success sample. Edge: a valid safety fallback is separately labeled and contains concrete content.
**Completion:** Typed output and stage-call assertions reject the current unconfigured-mock pattern. V02/V03; NOT RUN.

- [ ] **AUD-015-005 (P1): Exercise real resource matching against a populated fixture.**

**Obligations:** T017/T021, FR-002, SC-003, SC-CAP-015-004. Expected meaningful allocation work; actual empty inventory produces no eligible-resource workload and the result is ignored.
**Developer:** Owner [resource benchmark fixture](../../../tests/benchmark/test_pipeline_performance.py#L144). Reuse [unit resource builders](../../../tests/unit/test_resource_allocation_pipeline.py#L48); provide matching and competing resources with capabilities, locations, and explicit demand quantities. Assert allocation output; reset resource state per sample, and record workload size. Do not introduce live inventory/database calls. Depends on AUD-015-003.
**Tester:** Positive: nonempty assignments and timelines with conservation of demand. Negative: empty inventory must be separately identified as shortfall, not the normal baseline. Edge: insufficient quantity, reserved resources, and competing demands exercise matching instead of no-op loops.
**Completion:** Every normal timed sample matches at least one resource and reports the fixed inventory/demand cardinality. V02/V03; NOT RUN.

- [ ] **AUD-015-006 (P1): Isolate all benchmark dependencies from ambient cloud configuration.**

**Obligations:** T003/T017, FR-009, EC-03, A-002. Expected fully offline deterministic execution; actual default risk LLM construction and telemetry import can respond to live environment settings.
**Developer:** Owners [benchmark setup](../../../tests/benchmark/conftest.py#L28), [risk factory](../../../tests/benchmark/test_pipeline_performance.py#L110), and [monitoring import](../../../apps/agents/monitoring/agent.py#L15). Install environment/transport/exporter guards before imports and inject deterministic external-client fakes while retaining real application work. Isolate audit outputs in temporary locations; never rewrite real credentials or product configuration.
**Tester:** Positive: populated fake endpoint/telemetry environment still uses only fakes. Negative: network, credential acquisition, or exporter attempt fails a focused harness test. Edge: construction failure and one unavailable mocked dependency leave other benchmark cases running. Use inert dummy strings, never real credentials.
**Completion:** Zero external calls/export attempts with explicit guard coverage. V01-V07 only after guards exist; NOT RUN. Coordinate with AUD-015-003/004/007/012.

- [ ] **AUD-015-007 (P1): Benchmark the current LLM response path, retaining labeled legacy coverage only if needed.**

**Obligations:** T023/T024, FR-003, US3. Expected current application serialization/parsing/retry overhead; actual `__new__` fixture forces a test-only SDK branch and asserts only key presence.
**Developer:** Owners [LLM benchmark](../../../tests/benchmark/test_llm_performance.py#L21) and [current client](../../../apps/agents/common/llm_client.py#L55). Use constructor injection with a deterministic typed Foundry response, preserving real model selection, message construction, and extraction. Label legacy and retry/error paths separately so a baseline cannot compare unlike implementations. No real inference or model changes. Depends on AUD-015-006.
**Tester:** Reuse [Foundry fake shape](../../../tests/contract/test_foundry_chat_client.py#L158). Positive: verify messages, purpose routing, text, usage, and timeout propagation. Negative: unexpected response shape, missing configuration, or fake failure must not produce a successful sample. Edge: empty text, absent usage, and controlled retry paths remain deterministic.
**Completion:** Current branch is explicitly exercised and timed below enforced 500ms on approved runs; legacy measurements cannot masquerade as current. V05 and V01 boundary cases; NOT RUN.

- [ ] **AUD-015-008 (P1): Compare only the selected run and handle missing output explicitly.**

**Obligations:** T003/T015/T029/T034, FR-006, EC-04, R-002/R-003. Expected fresh selected output; actual fixed path can read old JSON, and missing/corrupt current data returns PASS. Research says missing current is an error while the wrapper's example/error table says skip: resolve this explicitly.
**Developer:** Owners [hook](../../../tests/benchmark/conftest.py#L70), [current loading](../../../tests/benchmark/compare_benchmarks.py#L150), and [CI invocation](../../../.github/workflows/ci.yml#L148). Resolve the configured result path against the repository, create its parent before the plugin opens it, and verify run identity. Intentional disabled/no-output runs must not consume stale files; requested but missing output must fail clearly. Baselines remain read-only.
**Tester:** V01 isolated directories: canonical/custom output, alternate working directory, no parent, absent/malformed/empty current, old JSON, and --benchmark-skip. Positive: exactly the selected fresh artifact is compared. Negative: requested output failure is nonzero. Edge: intentional skip is explicit and preserves existing pytest failure.
**Completion:** No stale verdicts or silent required-output loss; parent creation works without the keep-file. V01/V07/V08; NOT RUN.

- [ ] **AUD-015-009 (P1): Validate comparison records and protect metric identity.**

**Obligations:** T006/T008, data-model validation rules, FR-007/008/012/013. Expected safe complete comparison; actual loader accepts any benchmarks value, missing medians default to zero, and name dictionaries overwrite collisions.
**Developer:** Owner [loader/comparator](../../../tests/benchmark/compare_benchmarks.py#L85). Validate collection, entry, stats, and finite numeric types; reject bool/string/null/nonfinite medians and apply the documented nonpositive-value policy. Preserve native fullname/parameter identity, with an explicit migration for existing baseline names. Corrupt optional baselines warn/skip; corrupt required current input is an execution error. Continue valid metric reporting without hiding invalid entries. Depends on AUD-015-008's policy resolution.
**Tester:** V01 fixtures cover wrong array types, null entries/stats, missing median, zero/negative values, NaN/infinity, duplicate names/fullnames, improvements, new/removed metrics, and exact/adjacent 20/50% boundaries. Positive: correct named records survive. Negative: invalid current cannot pass. Edge: optional corrupt baseline does not block a valid first run or overwrite history.
**Completion:** Every input metric is accounted for exactly once with deterministic status; no uncaught schema exception or silently overwritten record. V01; NOT RUN.

- [ ] **AUD-015-010 (P2): Separate transition overhead from recovery elapsed time.**

**Obligations:** T025-T028, FR-004/005, SC-008, US4. Expected individual transitions plus bounded recovery; actual fake-clock full-cycle CPU time is presented with recovery metadata and no duration assertion.
**Developer:** Owner [CB module](../../../tests/benchmark/test_circuit_breaker_performance.py#L21). Keep permitted fake-clock state tests, label them as operation overhead, add distinct HALF_OPEN-to-CLOSED timing, and separately record total recovery under an explicit clock model. Export failure threshold, recovery timeout, from/to states, timing basis, and units. Use pytest-benchmark for timing; do not compare fake elapsed time to real elapsed baselines. Depends on AUD-015-002's SLO policy; provide configuration fields to AUD-015-011 and sampling-duration inputs to AUD-015-013.
**Tester:** Reuse [common-breaker contract tests](../../../tests/contract/test_llm_circuit_breaker.py#L19), not the ingestion breaker. Positive: all three transitions and recovery recorded. Negative: failed probe reopens; recovery over twice timeout fails. Edge: before/at/after timeout and changed configuration invalidate unlike baselines without sleeping through long default timeouts.
**Completion:** Four distinct timing obligations are visible and correctly bounded; no microsecond fake-clock sample is claimed as observed 100ms recovery. V06/V01; NOT RUN.

- [ ] **AUD-015-011 (P2): Persist truthful comparison metadata and visible notices.**

**Obligations:** T004/T007/T009, FR-006/012, SC-008, US5-AS1. Expected artifact-correlated verdicts/provenance and notices; actual report is in memory/stdout only, and first-run metrics have no logging call.
**Developer:** Owners [metadata helper](../../../tests/benchmark/benchmark_helpers.py#L17), [report formatter](../../../tests/benchmark/compare_benchmarks.py#L330), and [upload](../../../.github/workflows/ci.yml#L152). Preserve native raw JSON; add a documented companion comparison artifact or compatible metadata extension. Include source artifact commit, comparator revision, timestamp, SLO result, regression result, baseline identity, and CB configuration. Make first-run/removed notices visible without making them blocking. Never relabel old data with HEAD as its measurement revision. Depends on AUD-015-002/008/009/010.
**Tester:** Positive: archived structured values equal console status for all metric types. Negative: contradictory source/run identity is rejected or explicitly separated. Edge: unknown git SHA, Unicode-limited console, removed-only/new-only metrics, and failed runs still retain truthful artifacts.
**Completion:** Every required metric has durable SLO/regression status and provenance; stdout/log notices are observable under CI quiet mode. V01/V07/V08; NOT RUN.

- [ ] **AUD-015-012 (P2): Identify and cover representative health-check states.**

**Obligations:** T003/T010-T014, FR-001, US1-AS1, A-001. Expected useful per-agent health baselines; actual factory defaults omit agents and exercise uninitialized/degraded branches, while asserting only HTTP 200. Literal route benchmarks exist and are credited.
**Developer:** Owner [health fixtures](../../../tests/benchmark/conftest.py#L28). Add deterministic initialized-state dependencies for normal health workloads, with in-process LLM/store fakes where the route would call them. Keep uninitialized/degraded measurements separately named if useful. Use lifecycle cleanup and record fixture state; do not change production health semantics merely to make tests green. Depends on AUD-015-006.
**Tester:** Positive: five normal-state responses with expected health checks and enforced 100/75ms ceilings. Negative: missing agent/road network or fake unhealthy dependency must not be mislabeled healthy. Edge: one fixture startup failure reports ERROR while other agents complete.
**Completion:** Every health result identifies the state measured and covers the intended branch with substantive assertions. V04/V01; NOT RUN.

- [ ] **AUD-015-013 (P2): Restore a bounded, clearly scoped CI benchmark command.**

**Obligations:** T029, FR-010, SC-007, C07, R-006. Expected all required categories in <60s including setup/teardown and a two-minute safeguard; actual five-minute cap and later manual-timing tests have no reconciled feature-015 scope.
**Developer:** Owners [workflow](../../../.github/workflows/ci.yml#L148) and [benchmark directory](../../../tests/benchmark/test_pipeline_latency.py#L1). Enumerate collected categories, keep all original obligations, and reconcile later suites through explicit owner-approved selection or compatible timing conversion. Do not silently drop another specification's gate. Restore the prescribed safeguard or obtain a recorded amendment; record full-command elapsed time and stable sampling settings.
**Tester:** Positive: all expected metric identities and sample counts under 60s including clients and teardown. Negative: omitted agent/category or runaway benchmark fails visibly. Edge: cold startup, one agent error, and normal calibration variation do not bypass collection or corrupt artifacts.
**Completion:** A documented collection manifest, approved timeout policy, and matching CI-equivalent wall-clock receipts. V07 after AUD-015-001 through AUD-015-012 as applicable; NOT RUN.

- [ ] **AUD-015-014 (P2): Establish reproducible baseline and execution evidence.**

**Obligations:** T016/T031/T032/T033, SC-003/006/007, A-005. Expected a reviewed measured reference and execution receipts; actual tracked historical JSON lacks representative-path, approval, and full-command evidence for this revision.
**Developer:** Owners [baseline](../../../.benchmarks/baseline.json#L141), benchmark maintainers, and CI owner. After measurement repairs, capture revision plus any dirty-source digest, fixture/config versions, runner identity, plugin versions, exact command, exit status, all sample identities, and whole-command duration. Calibrate repeatability on comparable runners. Promote only by explicit authorized review; do not auto-update baseline or erase historical files. Recover historical feature-trigger evidence if available rather than re-adding a development branch.
**Tester:** Positive: reproduce a reference and download/inspect authorized CI receipts for retention, including a failed-run artifact. Negative: empty, wrong-workload, failed, or unapproved results cannot be promoted. Edge: different hardware/configuration is marked incomparable, not exempted from all gates.
**Completion:** Reproducible approved baseline, representative <2s pipeline evidence, <60s command receipt, and actual >=30-day artifact availability evidence or explicit UNVERIFIED status. V07/V08; NOT RUN. Depends on sampling, isolation, verdict, and metadata repairs.

- [ ] **AUD-015-015 (P2): Make every quickstart instruction accurate and verifiable.**

**Obligations:** T034 and local user workflows. Expected runnable fresh-result comparisons; actual subset commands produce no JSON and native compare syntax targets plugin saved runs, not the wrapper's baseline contract.
**Developer:** Owner [quickstart](quickstart.md#L21), with [plugin option semantics](../../../.venv/Lib/site-packages/pytest_benchmark/plugin.py#L264) as local supporting evidence. In a future authorized documentation change, specify repository cwd, required API/agent/test dependencies, selected environment, explicit output for comparisons, intentional no-output mode, and guarded manual promotion. Distinguish native plugin storage from wrapper comparison. Do not execute documented commits as part of this audit.
**Tester:** Positive: rehearse each command in an isolated offline workspace and retain command/output/exit receipts. Negative: old output, wrong cwd, or native saved-run mismatch is clearly diagnosed. Edge: first run, missing output directory, Windows shell syntax, and category-only runs remain meaningful.
**Completion:** Every documented command has a verified outcome or an explicit prerequisite/limitation; no stale comparison. V01, V03-V08; NOT RUN. Depends on AUD-015-008/013/014.

- [ ] **AUD-015-016 (P1): Reconcile capstone metric definitions and target predicates.**

**Obligations:** All five SC-CAP-015 criteria and their benchmark-scenario mapping. Expected exact original measurements/thresholds; actual [renderer definitions](../../../apps/api/app/services/evidence/measurement/renderer.py#L11) and [any-improvement predicate](../../../apps/api/app/services/evidence/simulation/scorecard_builder.py#L34) are not equivalent.
**Developer:** Owners: feature-015 SRE/product owner and the current evidence-service owner. Define one versioned mapping for annualized lives, alert-to-acknowledgement median, warning-to-recommended-start lead improvement, allocated-versus-idle utilisation uplift, and calibrated avoided loss. Preserve distinctions from response-arrival, evacuation-completion, click-count, and reallocation proxies. Require explicit ownership/amendment resolution before changing shared definitions; keep the original quantitative targets visible.
**Tester:** Extend [measurement contract tests](../../../tests/contract/test_evidence_measurement_method.py#L1) and [delta integration tests](../../../tests/integration/test_baseline_vs_ama_delta.py#L21). Positive: correct units/signals and exact threshold boundaries for all five. Negative: 1% improvement must not satisfy 30/50% targets. Edge: zero baseline, missing acknowledgements, annualization window, and order/completion timestamp substitution are rejected or indeterminate.
**Completion:** Five explicit, owner-approved, semantically equivalent mappings and threshold tests, not generic improvement flags. V09; NOT RUN. Precedes AUD-015-017.

- [ ] **AUD-015-017 (P1): Supply representative capstone evidence without treating synthetic targets as outcomes.**

**Obligations:** Five SC-CAP-015 amendments; AU baselines advertised as recorded today. Expected traceable exercises or independently justified scenario models; actual seeded baselines and guaranteed treatment factors prove only scaffolding.
**Developer:** Owners [paired harness](../../../tests/simulation/paired_exercise_harness.py#L171), [replay synthesis](../../../apps/api/app/services/evidence/simulation/orchestrator.py#L29), and [benchmark register](../../../apps/api/app/services/evidence/benchmarks/seed.py#L211). Keep synthetic fixtures labeled synthetic and separate from validated evidence. Connect authorized deidentified recorded exercises or independently calibrated models to the approved five definitions, with pairing, cohorts, denominators, uncertainty, and source references. For lives and economic loss, publish modelling limitations and avoid claims of observed lives saved. Do not activate PH/JP/BD gates or call live services without new authorization.
**Tester:** Positive: independently computed results reproduce raw evidence for all five metrics. Negative: seeded improvement factors, missing data, unsupported extrapolation, or a negative/control-neutral outcome cannot be published as validated success. Edge: incomplete pairs, duplicate events, zero denominators, and imputed data produce explicit uncertainty/exclusion.
**Completion:** Five evidence-backed AU scenario mappings with honest outcome status, or explicit remaining UNVERIFIED outcomes; no automatic promotion from deterministic mock tests. V09/V10; NOT RUN. Depends on AUD-015-016 and appropriate external evidence/approval prerequisites.

- [ ] **AUD-015-018 (P2): Keep economic-loss raw data and summaries consistent.**

**Obligations:** SC-CAP-015-005 evidence integrity. Expected raw rows backing every summary pair; actual [five-row data](../../../tests/measurement/sc005_economic_loss.ndjson#L1) disagrees with [30-pair summary](../../../docs/aidr/exercise-summaries/spec-036-baseline.md#L3).
**Developer:** Owner [economic-loss writer and round-trip test](../../../tests/measurement/sc005_economic_loss.py#L91). Use temporary paths for test-only writes, publish raw/summary artifacts together under one run identity, and store source hashes and pair counts. Do not retrospectively edit the old measurements in this audit; a future correction must preserve their provenance. This shared writer issue independently affects feature-015's loss-evidence obligation.
**Tester:** Positive: summary count, pair IDs, mean, and interval reproduce from the complete same-run raw set. Negative: five rows paired with a 30-row summary fail integrity validation. Edge: reordered test execution, interrupted writes, repeat runs, and duplicate pair IDs never overwrite a validated result silently.
**Completion:** Round-trip tests cannot modify canonical evidence; one-to-one raw/summary coverage is validated. V10 in an isolated workspace only; NOT RUN. Depends on AUD-015-016/017 for outcome validity, not for the immediate isolation fix.

- [ ] **AUD-015-019 (P2): Resolve HYP-013's missing evidence artifact and scope.**

**Obligations:** HYP-013 and the [evidence-stub contract](../../028-capstone-alignment/contracts/evidence-stub.contract.md#L9). Expected a conforming stub plus feature-specific test/consultation evidence; actual double-prefix reference resolves nowhere, and the supplied rubric scores are portfolio-wide.
**Developer:** Owners: feature-015 specification owner with feature-027/028 evidence maintainers. In future authorized work, establish one correctly located single-prefix HYP-013 artifact, with six required sections, at least two preconditions, bounded measurement window, falsification rule, and initial Not tested status. Preserve historical snapshots; bind feature-specific before/after evidence and genuine actor consultations rather than generating retrospective approvals.
**Tester:** Positive: reference resolves and required fields match HYP-013. Negative: double prefix, wrong feature, missing preconditions, or portfolio-average substitution fails. Edge: untested hypothesis and contradictory per-criterion results remain visible without automatic promotion.
**Completion:** Valid linked artifact and explicit tested/untested state; no false consultation/uplift claim. V08 document inspection; NOT RUN. No delegation is authorized by this task during the audit.

- [ ] **AUD-015-020 (P2): Establish persona-validation provenance without promoting placeholders.**

**Obligations:** PER-037/038/039 and the [persona contract](../../027-spec-hardening/contracts/persona-profile.md#L15). Expected specific role/scenario mappings and named, dated validation; actual grouped references and role-only validators do not establish sign-off.
**Developer:** Owners: specification/product owner, SRE/QA representatives, and authorized operational reviewers. Map operational and technical persona groups to concrete profiles, authority boundaries, scenarios, and accessible validation records. Reuse genuine existing records where available; otherwise retain UNVERIFIED status. Keep PH/JP/BD placeholders gated on D-009 and SME validation.
**Tester:** Positive: each claimed validated mapping has a real reviewer name, role, date, and representative scenario. Negative: role-only labels, missing countersign authority, or unsupported country promotion fail review. Edge: technical actors are not misrepresented as statutory operational authorities.
**Completion:** Two AU group references have traceable validation or explicit limitations; all three deferred cohorts retain their gates. V08 document inspection; NOT RUN. Depends on obtaining authentic review evidence, not on generated text.

- [ ] **AUD-015-021 (P2): Reconcile review evidence and assess the correct rubric criterion.**

**Obligations:** SC-009, plan gates, 16-item requirements checklist, and CHK001-CHK054. Expected documented review disposition and a Performance and reliability score of >=4 from a stated baseline of 3; actual artifacts assert structural readiness, not those results.
**Developer:** Owners: SRE, QA, and independent rubric reviewer. After technical repairs, record a disposition for every open performance question, separating answered design questions, accepted risks, and verified executions. Request a dated feature-specific assessment against [the actual rubric criterion](../../../AMA_Rubric_Asia.md#L47), with evidence and limitations. Keep feature-028's five-criterion structural snapshots separate from both SC-009 and HYP-013. Do not backfill original checkboxes or impersonate approvers.
**Tester:** Positive: review references the exact revised artifacts/run receipts and explains each criterion conclusion. Negative: checked tasks, a schema-valid file, or portfolio +2 mean alone cannot close SC-009. Edge: incomplete external approvals or residual runtime gaps remain UNVERIFIED even when document checks pass.
**Completion:** All 54 questions dispositioned in a new authorized record, original states preserved, and an authentic scoped assessment proving the target or explicitly stating it is unmet/unverified. V08 plus authorized human assessment; NOT RUN. Depends on AUD-015-014/019/020 and relevant technical closures.

## Future-Only Validation Matrix

**Nothing in this matrix was executed.** Commands are for later authorized developer/tester work, not
permission to run product code in this review. Use a selected Python 3.12+ environment with the API,
agent packages, pytest, pytest-benchmark, pytest-asyncio, and their declared dependencies installed.
Run from repository root in an isolated workspace with network/credential/exporter guards, no real
service endpoints, and all staging flags unset. Implement the referenced fixes first. Preserve existing
baseline/evidence files until a separately authorized promotion/correction. Report exact command,
environment, fixture version, exit status, elapsed time, and artifact identity for every actual run.

| Check | Future command / procedure | Prerequisites and expected result | Audit result |
| --- | --- | --- | --- |
| V01 | `pytest tests/unit/test_benchmark_reporting.py -q` | **Proposed new test file**, not existing evidence. Cover comparator, hook, identity, schema, threshold/SLO boundaries, notices, and offline guards described above. All focused assertions pass, including CI failure cases. | NOT RUN |
| V02 | `pytest tests/unit/test_monitoring_pipeline.py tests/unit/test_risk_assessment_pipeline.py tests/unit/test_evacuation_pipeline.py tests/unit/test_resource_allocation_pipeline.py tests/unit/test_communication_pipeline.py -q` | Add sample-validity assertions using the existing fixtures; ensure offline guards first. Valid outputs, explicit duplicate rejection, and deterministic stage coverage pass. | NOT RUN |
| V03 | `pytest tests/benchmark/test_pipeline_performance.py --benchmark-json=.benchmarks/current.json -q` | Sample-state/content fixes and directory creation complete. Five representative pipeline metrics, asserted terminal work, enforced <2s medians. | NOT RUN |
| V04 | `pytest tests/benchmark/test_api_performance.py --benchmark-json=.benchmarks/current.json -q` | Initialized-state fakes and comparison repairs complete. Five named health metrics; strict <100ms/<75ms and fixture-state assertions. | NOT RUN |
| V05 | `pytest tests/benchmark/test_llm_performance.py tests/contract/test_foundry_chat_client.py --benchmark-json=.benchmarks/current.json -q` | Current-branch constructor-injected fake implemented, no network. Correct request/response semantics and enforced <500ms; legacy records separately labeled. | NOT RUN |
| V06 | `pytest tests/benchmark/test_circuit_breaker_performance.py tests/contract/test_llm_circuit_breaker.py --benchmark-json=.benchmarks/current.json -q` | Explicit timing model and dynamic SLO support. Three distinct transitions plus total recovery; exact recovery boundary and failed probe assertions pass. | NOT RUN |
| V07 | `pytest tests/benchmark/ --benchmark-json=.benchmarks/current.json -q` | Full collection reconciled, comparable approved baseline, external calls blocked. Capture outer command start/end including setup/teardown: <60s, all required identities, warning-only exit 0, injected >=50% regression nonzero. Verify actual CI upload on success and failure later. | NOT RUN |
| V08 | `git ls-files --stage -- .benchmarks/.gitkeep .benchmarks/baseline.json`; document/JSON provenance and link review | Static inventory is not product execution. For future acceptance, verify versioned artifacts, source/summary counts, approval identities, hypothesis/profile contracts, and authorized retention receipts. Manual baseline promotion requires separate approval, never automatic copying. | NOT RUN as acceptance; tracking was inspected during audit |
| V09 | `pytest tests/contract/test_evidence_measurement_method.py tests/integration/test_baseline_vs_ama_delta.py -q` | Extend existing assertions to exact five definitions/thresholds and supplied approved fixtures; current tests' field/count checks alone are insufficient. Reject wrong signals, proxy substitutions, and unsupported success labels. | NOT RUN |
| V10 | `pytest tests/measurement/sc005_economic_loss.py -q` | Only after output isolation and source-validity fixes, in a disposable workspace; explicit filename is needed because it is not a default test-prefixed module. Raw/summary agreement and non-tautological input tests pass; staging remains skipped. Synthetic passes do not certify operational outcomes. | NOT RUN |

## Audit Validation Receipt

Report-only validation on 2026-09-11: exact 34 task IDs and original states; allowed evidence statuses;
exact 27 FR/SC IDs; 13 scenario rows; 8 edge rows; 10 clarification decisions; all 54 CHK IDs; and 21
unique unchecked follow-ups passed. Local link existence and line bounds passed; editor diagnostics
were clear. These checks are rerun after each report edit and for the rebased historical copy. They
validate report integrity only, not product behavior, benchmark outcomes, or external approval.
