# Static Implementation Audit: 025 Agent Specification Compliance

## Scope and Revision

- Review date: 2026-09-14.
- Expected source revision: `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a`.
- Observed HEAD: `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a`; no revision difference.
- Scope: only the obligations of specification 025, including its later embedded amendments,
  and the source, configuration, assertions, and attributable evidence needed to assess them.
- This is a fresh independent, static review. No other implementation-review report was read or used.
  Pre-existing untracked audit artifacts were left untouched. No tracked source changes were present
  at the initial read-only worktree check.
- Only this report may be written. No source, specification, original task state, evidence, index,
  commit, or branch changes are authorized.
- No application imports, tests, builds, browsers, servers, runtime/debug execution, installations,
  cloud queries, resource operations, or external approvals are performed. Future commands are
  instructions only, not executed validation or evidence of successful execution.
- Evidence statuses follow the Review Contract: IMPLEMENTED, PARTIAL, MISSING, CONFLICT,
  UNVERIFIED, and SUPERSEDED. IMPLEMENTED credits inspected static behavior or authored artifacts,
  not deployment, performance, human approval, or runtime success. Replacement requires explicit
  retirement evidence; a deprecation comment alone does not retire this specification's obligations.

## Review Summary

The shared retry helper has an async implementation and uses an individual-attempt timeout;
the claim that it is entirely synchronous is not supported by current source
([handoffs.py](../../apps/agents/common/handoffs.py#L124)). FR-002's per-sequence wording and
T005's per-attempt instruction need separate assessment. The dedicated test's single-attempt
timeout case asserts only the final dead-letter status, not elapsed time or concurrent progress
([test_async_handoff_retry.py](../../tests/unit/test_async_handoff_retry.py#L86)).

All 89 original tasks are unchecked in the source task list. This report preserves those states and
independently evaluates 23 functional requirements, 9 success criteria, 24 acceptance scenarios, five
edge cases, and the assumptions/persona/hypothesis/scope/review obligations below. Authored helpers,
relocated resources and existing tests receive credit, but the traced paths do not support declaring
the feature complete. No SC measurement, test execution, deployment or human sign-off was performed.

## Local Inputs Read in Full

The eight pre-existing local documents were read completely, including their final sections:
[spec.md](spec.md), [tasks.md](tasks.md), [plan.md](plan.md), [research.md](research.md),
[data-model.md](data-model.md), [quickstart.md](quickstart.md),
[contracts/openapi-delta.md](contracts/openapi-delta.md), and
[checklists/requirements.md](checklists/requirements.md). No separate local review record exists in
the enumerated folder. The Review Contract was read in full from the audit README's first 59 lines;
no inventory entries or other implementation-review reports were consulted. The repository's code-review
instructions and detailed review checklist, code-commenting instructions, Python fact-grounded skill,
and Cosmos DB review skill informed the static review. Runtime and environment claims remain unverified.

## Findings and Open Remediation

### High: Management Identity Is Not Verified

The registered management dependency calls `jwt.decode(..., verify_signature=False)` in non-local
environments ([auth.py](../../apps/api/app/middleware/auth.py#L62)). This is not production identity
validation. The existing EasyAuth middleware only copies headers/default claims
([auth_middleware.py](../../apps/api/app/middleware/auth_middleware.py#L19)); the later Entra middleware
protects a fixed prefix list that excludes radius and dead-letter routes
([entra_auth.py](../../apps/api/app/middleware/entra_auth.py#L37)). Invalid-token exceptions also escape
without the dependency's structured failure logger. The dedicated tests select local API-key mode only
([test_management_auth.py](../../tests/unit/test_management_auth.py#L18)). Deployment-level protection
cannot be presumed from these files.

- [ ] AUD-025-001 Enforce verified management identity and complete authorization auditing

  **Original obligations:** FR-021; T013, T014, T015, T024, T036; contracts 4a-4d, 6.
  **Expected versus actual / impact:** Production requires a valid Azure identity, operator/admin reads
  and redelivery, admin-only radius writes, and logged 401/403 failures. The dependency trusts unverified
  token claims; forged role claims can reach privileged handlers if no external protection intervenes.
  **Developer instructions:** Own the fix in `app.middleware.auth` and the registered management routers.
  Reuse the existing Entra validation implementation where appropriate, but cover these paths, use a
  constrained algorithm/JWKS/issuer/audience/expiry policy, fail closed on missing configuration, and use
  one trusted principal for role checks. Preserve explicitly local API-key compatibility; do not trust
  client-supplied EasyAuth headers or allow test-principal bypasses in production. Log every invalid-token
  and forbidden-role path without logging tokens. Protect inspection as a management operation too.
  **Tester instructions:** Extend existing
  [test_management_auth.py](../../tests/unit/test_management_auth.py#L1),
  [test_dead_letter_api.py](../../tests/contract/test_dead_letter_api.py#L1), and the existing radius API
  contract tests. Use locally signed token fixtures with a mocked JWKS transport, not a mocked decoder:
  valid operator/admin, viewer, wrong issuer/audience/key, expired/malformed/unsigned token, missing
  credentials, forged headers, and production with incomplete configuration. Assert 401/403 and audit
  fields; assert operator writes fail and admin writes pass through the real app router.
  **Future validation:** In a prepared repository test environment, run
  `python -m pytest tests/unit/test_management_auth.py tests/contract/test_dead_letter_api.py tests/contract/test_radius_lookup_api.py -v`.
  Expected: verified positive identities only, the exact negative status/audit assertions above, and no
  network calls. **Completion:** No unverified production identity path remains for spec-025 management.

### High: Dead-Letter Recovery Has Disconnected Stores and a Shadowed API

The monitoring producer's default callback only fabricates an ID
([pipeline.py](../../apps/agents/monitoring/pipeline.py#L64)). The new API uses a separate module dictionary
([dead_letters.py](../../apps/api/app/api/routes/dead_letters.py#L15)); its manual handler only marks
`pending` and returns 202 ([dead_letters.py](../../apps/api/app/api/routes/dead_letters.py#L74)).
The older GET is registered first ([router.py](../../apps/api/app/api/router.py#L73)), before the newer
router at line 94, so normal routing reaches the old store/schema rather than the new status filters
and audit fields. The startup helper exists but no caller was found beyond its definition and lifecycle
re-export in the bounded `apps/agents/**/*.py` search
([startup.py](../../apps/agents/common/startup.py#L14)). The new store's Cosmos read uses `handoff_id` as
partition key, conflicting with T016/T018's planned target-agent partitioning
([dead_letters.py](../../apps/agents/common/dead_letters.py#L65)).

- [ ] AUD-025-002 Connect durable dead-letter persistence, startup, inspection, and manual delivery

  **Original obligations:** FR-003a, FR-021; T016, T017, T019, T020, T021, T024, T025; US1; edge case EC-02;
  contracts 3a, 3b, 5a, 6.
  **Expected versus actual / impact:** Exhausted handoffs must survive process loss, be inspectable, and
  actually redeliver. ID-only callbacks and isolated dictionaries cannot provide this; an accepted manual
  request can remain pending forever, and the public GET returns a different schema.
  **Developer instructions:** Connect the controlling agent factories/lifespans and delivery callbacks to
  `common.dead_letters.DeadLetterStore`, with a single durable schema/partition strategy shared by the API.
  Register and stop the worker in the agent process, not in the API. Reconcile the two GET registrations
  and older `app.services.dead_letter_service` consumers compatibly; preserve tenant/incident boundaries
  and existing resolution clients. Make manual acceptance enqueue or invoke real agent-process delivery,
  propagate errors, and persist a durable operation identity. Do not silently fall back to memory in
  production or report every Cosmos read error as not-found.
  **Tester instructions:** Extend existing
  [test_dead_letter_lifecycle.py](../../tests/unit/test_dead_letter_lifecycle.py#L1),
  [test_dead_letter_api.py](../../tests/contract/test_dead_letter_api.py#L1), and
  [test_async_handoff_retry.py](../../tests/unit/test_async_handoff_retry.py#L1). Use an injected durable
  repository fixture shared by separately constructed agent/API clients: exhaust delivery, reconstruct
  clients, list/filter/page by target/status/incident, manually redeliver, and observe the receiver and
  persisted outcome. Include absent records, storage errors, shutdown cancellation, duplicate IDs across
  tenants, and three unavailable targets. Assert the real registered GET exposes the complete schema.
  **Future validation:** In the prepared test environment, run
  `python -m pytest tests/unit/test_dead_letter_lifecycle.py tests/contract/test_dead_letter_api.py tests/unit/test_async_handoff_retry.py -v`.
  Expected: durable round-trip and actual receiver invocation, correct 202/404 semantics and one canonical
  GET route. **Completion:** Exhaustion-to-inspection-to-redelivery is one connected, durable lifecycle.

### High: Redelivery Does Not Enforce Backoff, Fairness, or Terminal Immutability

The poller fetches only the default first 20 records, skips exhausted records without advancing pages,
and serially awaits deliveries ([dead_letters.py](../../apps/agents/common/dead_letters.py#L196)). Its
backoff is computed but not scheduled; a successful callback return is treated as delivery success
regardless of returned handoff state ([dead_letters.py](../../apps/agents/common/dead_letters.py#L209)).
The terminal transition happens on an auto failure if any manual attempt already occurred, rather than
on failure of the required subsequent manual attempt. Neither store update nor direct attempt methods
enforce read-only terminal entries. Tests manually assign a terminal status or overwrite entries; they
do not instantiate the poller ([test_dead_letter_lifecycle.py](../../tests/unit/test_dead_letter_lifecycle.py#L46)).

- [ ] AUD-025-003 Enforce the recoverable and permanently failed dead-letter state machine

  **Original obligations:** FR-003a; T016, T018, T022, T023, T025; US1; EC-02; 50-concurrent-redelivery scale;
  research R14 and contracts 5a/5b.
  **Expected versus actual / impact:** Three failed automatic recoveries followed by one failed manual
  recovery must become immutable, auditable permanent failure. Current scheduling can starve later
  records, retry flapping agents without the promised backoff, or strand manual failures in pending.
  **Developer instructions:** In `common.dead_letters`, add persisted attempt timestamps/next-attempt
  scheduling, paginated fair selection, bounded concurrent workers, atomic claims/OCC, explicit outcome
  handling and recoverable cancellation. Apply target-health gating and backoff, then enforce ordered
  auto/manual counters and terminal rejection at every mutation/delivery boundary, including the API.
  Align successful status naming (`delivered` versus contract `redelivered`) and the documented 409 JSON
  envelope explicitly, without breaking existing consumers. Depend on AUD-025-002's shared durable store.
  **Tester instructions:** Extend the existing lifecycle and API tests with a fake clock, >20 entries,
  flapping health, 50 concurrently claimable entries, duplicate workers, callback returns of failed or
  dead-lettered handoffs, cancellation, and storage conflicts. Exercise exactly three auto failures then
  one manual failure; assert timestamps/reasons/counters, 409 envelope, and zero later delivery or writes.
  **Future validation:** With injected time/health/delivery and no external services, run
  `python -m pytest tests/unit/test_dead_letter_lifecycle.py tests/contract/test_dead_letter_api.py -v`.
  Expected: no retry before due time, no starvation/double claim, and terminal entries remain unchanged.
  **Completion:** Every allowed transition and forbidden transition has a persisted audit trail and an
  assertion through both worker and management paths.

### High: Async Helpers Do Not Make Their Pipeline Callers Non-Blocking

All six original sleep sites were converted to `asyncio.sleep`, a real partial implementation. However,
`run_async` synchronously waits on `future.result()` inside a running event loop
([async_bridge.py](../../apps/agents/common/async_bridge.py#L15)). Risk assessment calls this bridge for
versioning and sequential downstream delivery
([pipeline.py](../../apps/agents/risk_assessment/pipeline.py#L392),
[pipeline.py](../../apps/agents/risk_assessment/pipeline.py#L575)); communication does likewise for
delivery ([pipeline.py](../../apps/agents/communication/pipeline.py#L596)). The OCC helpers call synchronous
container methods, and the async channel loop calls synchronous providers with no two-second timeout
([delivery.py](../../apps/agents/communication/delivery.py#L161)). The later executor's elapsed budget is
checked only after an exception, not around an in-flight attempt
([_base.py](../../apps/agents/maf_runtime/workflow/executors/_base.py#L108)).

The dedicated benchmark uses `max_retries=0` for its slow case
([test_pipeline_latency.py](../../tests/benchmark/test_pipeline_latency.py#L47)); the helper's loop then
performs zero deliveries. There is no 100-run ingestion-to-final-delivery P95 assertion in that file.
FR-002/SC-002's sequence-blocking wording versus T005's individual-attempt timeout is an explicit
contract ambiguity, not proof that seven-plus seconds of async waiting itself blocks the event loop.
The relocated [ADR-F02](../../docs/corpus/aidr/decisions/adr-f02-async-bridge.md#L20) explicitly chooses
the bridge as a migration compromise. It is credited as design evidence, but does not retire FR-001/002
or establish that a synchronous future wait meets their concurrency/latency guarantees.

- [ ] AUD-025-004 Remove blocking retry callers and test the complete latency boundary

  **Original obligations:** FR-001, FR-002, FR-003; SC-001, SC-002; T004, T005, T006, T007, T008, T009,
  T010, T011, T012, T026; US1-AS1, US1-AS2, US1-AS3; 1,000-concurrent-signal scale.
  **Expected versus actual / impact:** One failed downstream delivery must not stall independent signals.
  Async sleeps coexist with synchronous bridges, Cosmos calls, provider calls, and sequential fan-out;
  current timing assertions can pass without invoking the operation whose latency they claim to bound.
  **Developer instructions:** Own the end-to-end conversion in the operational pipeline entry methods,
  their agent HTTP/background callers, four version counters, channel service, and MAF executor boundary.
  Await genuinely async I/O or explicitly isolate synchronous I/O without waiting on its future from the
  event loop; use bounded concurrent independent fan-out while retaining per-incident ordering, OCC,
  tenant isolation, and cancellation safety. Set actual attempt deadlines and a resolved sequence budget.
  Preserve existing structured helper events and add equivalent outcome/attempt coverage to every retry
  path. Do not treat a no-client channel branch as confirmed delivery. Obtain an explicit requirements
  resolution of attempt timeout, event-loop blocking time, and end-to-end elapsed time before claiming SCs.
  **Tester instructions:** Extend existing
  [test_async_handoff_retry.py](../../tests/unit/test_async_handoff_retry.py#L1),
  [test_pipeline_latency.py](../../tests/benchmark/test_pipeline_latency.py#L1), and the four existing
  agent versioning unit test files. Through the actual entry path, process three signals while one
  injected provider fails; assert the other two finish, a loop heartbeat progresses, provider invocation
  counts are nonzero, cancellation completes, and every telemetry record has the required extra fields.
  Cover sync-adapter delay, all attempts timing out, concurrent incident isolation, zero/negative retry
  configuration, and channel independence. Benchmark 100 real pipeline-path iterations with one failed
  agent; compute P95 from ingestion through final delivery and assert <=5 seconds, not a helper-only mean.
  **Future validation:** In the prepared test environment with injected providers, run
  `python -m pytest tests/unit/test_async_handoff_retry.py tests/unit/test_risk_assessment_versioning.py tests/unit/test_communication_versioning.py tests/unit/test_evacuation_versioning.py tests/unit/test_resource_allocation_versioning.py tests/benchmark/test_pipeline_latency.py -v`.
  Expected: nonblocking concurrency assertions and the resolved <=2-second/<=5-second metrics pass with
  nonzero work. **Completion:** Correct helper behavior is demonstrably preserved at all actual callers;
  measured outcomes remain UNVERIFIED until attributable benchmark evidence exists.

### High: Hazard Maps and Management Radii Are Not Connected to Assessments

The assessment pipeline normalizes away top-level coordinates and location identifiers
([pipeline.py](../../apps/agents/risk_assessment/pipeline.py#L256)), and the assessment constructor omits
the optional `hazard_map` ([agent.py](../../apps/agents/risk_assessment/agent.py#L232),
[hazard_assessment.py](../../packages/domain/src/domain/models/hazard_assessment.py#L49)). Bounded searches
of the agent and API Python sources found the new generator/named-location classes only in their helper
modules, not in the controlling assessment stages. The newer risk executor delegates to a facade whose
legacy path creates a decision record, not a spatial assessment
([risk_assessment_agent.py](../../apps/agents/maf_runtime/agents/risk_assessment_agent.py#L25)).

The radius API edits `_radius_store`, independent of `HazardRadiusRepository`
([radius_lookup.py](../../apps/api/app/api/routes/radius_lookup.py#L53)). Cosmos wrappers and seed values
exist, but they do not establish live production wiring or seed execution. The generator defaults absent
coordinates to `(0,0)`, discards supplied geometry/per-signal severity, buffers in degrees, and casts one
global severity to integer ([hazard_map.py](../../apps/agents/risk_assessment/hazard_map.py#L45)). It does
not validate WGS84 bounds or preserve the highest severity of heterogeneous signals. Its Feature wrapper
is not the complete existing `HazardMap` model, which also requires string severity, confidence, and
time horizon ([hazard_assessment.py](../../packages/domain/src/domain/models/hazard_assessment.py#L7)).
The helper tests use only explicit point dictionaries and a local radius repository
([test_hazard_map.py](../../tests/unit/test_hazard_map.py#L18)); named-location tests are also local-only
([test_named_locations.py](../../tests/unit/test_named_locations.py#L13)).

- [ ] AUD-025-005 Produce validated persisted hazard maps from shared live radius and location data

  **Original obligations:** FR-004, FR-004a, FR-005, FR-006; SC-003; T027, T028, T029, T030, T031, T032,
  T033, T034, T035, T036, T037, T038; US2-AS1, US2-AS2, US2-AS3; EC-01; research R2, R11, R12;
  data-model HazardMap/HazardRadiusLookup/NamedLocation and contracts 4a-4d.
  **Expected versus actual / impact:** Every located assessed hazard needs actionable persisted geometry;
  coordinate-less signals must resolve or reject, and radius edits must affect the next generation.
  Disconnected helpers and stores leave consumers without the promised output; defaulting a missing
  location to the equator can manufacture a false affected area once the helper is connected.
  **Developer instructions:** Connect the assessment entry, normalization, generator, persistence and
  downstream serializers, including the selected workflow path. Inject one Cosmos-backed radius/location
  repository into both API and agent factories; seed idempotently without overwriting operator edits.
  Preserve original geometry and location identifiers, resolve missing coordinates with audited lookup,
  reject unresolved/invalid locations before generating maps, and handle per-signal severity/merging.
  Define a compatible numeric-to-domain-severity adapter and geometry-versus-Feature representation;
  retain required confidence/time/timestamp fields. Validate all five positive finite radii, severity
  1-5, WGS84 bounds, duplicate-create concurrency, and store errors distinctly from missing records.
  Use an appropriate local projection/geodesic strategy or explicitly justify the approximation and
  its AU-latitude error bounds. Depend on AUD-025-001 for trusted write identities and AUD-025-004 for I/O.
  **Tester instructions:** Extend existing
  [test_hazard_map.py](../../tests/unit/test_hazard_map.py#L1),
  [test_named_locations.py](../../tests/unit/test_named_locations.py#L1), and
  [test_radius_lookup_api.py](../../tests/contract/test_radius_lookup_api.py#L1). Use the same injected
  repository across API and assessment factories: PUT radii then generate without restart, reconstruct
  both, and assert the stored assessment and consumer geometry. Test supplied polygons, point buffers at
  Sydney/Melbourne latitudes, overlap/adjacency/disjoint zones with different severities, valid zero
  coordinates, missing/null coordinates, a known and unknown device ID, invalid bounds, negative/NaN
  radii, missing severity keys, storage outages, and concurrent duplicate creation. Assert rejection has
  the original location ID, no fabricated map, highest merged severity, geometry validity, and audit fields.
  **Future validation:** In a prepared environment with Shapely and injected repositories, run
  `python -m pytest tests/unit/test_hazard_map.py tests/unit/test_named_locations.py tests/contract/test_radius_lookup_api.py -v`.
  Expected: complete persisted map round-trips, live configuration visibility, and strict negative-path
  assertions. **Completion:** Every located assessment uses real configured spatial data; unrelated
  dashboard-only geometry cannot substitute for agent output.

### High: Outbound Alerts Do Not Traverse the Required Three Safety Layers

The real communication entry calls the synchronous processing pipeline
([agent.py](../../apps/agents/communication/agent.py#L185)). Stage 7 skips templates/template fallbacks,
validates only LLM text with `validate`, and replaces rejected content without validating the replacement
([pipeline.py](../../apps/agents/communication/pipeline.py#L367)). Bounded searches of agent Python sources
found `validate_factual` and `validate_tone` definitions but no pipeline caller. The existing LLM mixin
does provide an earlier Azure/keyword check, but does not supply the omitted factual/tone checks and
returns unvalidated fallback text ([llm_mixin.py](../../apps/agents/common/llm_mixin.py#L154)).

The helper's factual check accepts an empty source dictionary and only searches for expected substrings,
not conflicting facts ([content_safety.py](../../apps/agents/common/content_safety.py#L198)). Its tone
check accepts unrecognized tiers, and its Azure adapter reports only `severity_N`, not the violation
category ([content_safety.py](../../apps/agents/common/content_safety.py#L135)). Non-local managed-identity
construction and the normalized fields deserve static credit; SDK response compatibility and real
language coverage are not proven. The consolidated tests never supply an Azure SDK response or verify
credential selection ([test_content_safety_pipeline.py](../../tests/unit/test_content_safety_pipeline.py#L81)).

- [ ] AUD-025-006 Enforce factual, tone, and categorized content safety on every outbound message

  **Original obligations:** FR-007(a/b/c), FR-008; SC-004; T039, T040, T041, T042, T046, T047, T048, T049,
  T051; US3-AS1, US3-AS2; ContentSafetyResult entity; research R3/R13.
  **Expected versus actual / impact:** Every outbound alert needs category-aware moderation, verified
  originating facts, and an English pre-translation tier check. Template and fallback bypasses plus
  disconnected validators leave harmful, inaccurate, or over-urgent alerts eligible for approval.
  **Developer instructions:** Own orchestration in `communication.pipeline`, `communication.translator`
  and `common.content_safety`, including the MAF-facing alert path. Carry authoritative hazard, severity,
  location and warning tier from intake; validate complete English title/body/actions before translation,
  and moderate every final language/version including operator edits and replacement templates. Reject
  or explicitly review missing/conflicting source facts rather than treating absence as a match. Return
  violation categories and normalized confidence/method for every layer, persist the results, and block
  rejected versions. Validate the adapter against the declared SDK's real response model instead of
  assumed per-category attributes. Preserve managed identity outside explicit local development and
  locale compatibility (`en-AU`/`zh-Hans` mapped to corpus `en`/`zh`).
  **Tester instructions:** Extend existing
  [test_content_safety_pipeline.py](../../tests/unit/test_content_safety_pipeline.py#L1),
  [test_communication_pipeline.py](../../tests/unit/test_communication_pipeline.py#L1), and
  [test_communication_translator.py](../../tests/unit/test_communication_translator.py#L1). Use SDK-shaped
  response fixtures at severities 0, 2, 4, 6; assert category labels, confidence 4/6, and managed-identity
  versus local credential construction with no network. Exercise all six locales, safe urgent text,
  each moderation category, wrong and missing facts, text containing both correct and contradictory
  facts, unknown/Advice/Watch-and-Act/Emergency tiers, operator edits, and unsafe template substitutions.
  Assert English tone is checked before translation, every final variant is checked, and rejected
  versions never reach the delivery spy. Do not stub the validation decisions being tested.
  **Future validation:** In the prepared test environment with SDK dependencies and injected clients, run
  `python -m pytest tests/unit/test_content_safety_pipeline.py tests/unit/test_communication_pipeline.py tests/unit/test_communication_translator.py -v`.
  Expected: full positive/negative pipeline assertions and complete persisted layer metadata.
  **Completion:** All outbound paths enforce the three layers; corpus accuracy remains UNVERIFIED until
  attributable evaluation evidence meets SC-004.

### High / Conflict: Fallback Probing and Alert Review Semantics Are Incomplete

The relocated content-safety breaker has the requested default threshold, cooldown and five event names,
but `is_open` returns false to every caller while half-open; no single-probe claim is enforced
([content_safety_circuit_breaker.py](../../apps/agents/common/content_safety_circuit_breaker.py#L35)).
Only the helper receives `review_flag=True`; Stage 7 and persistence omit that metadata and every alert
is created `pending_review` ([pipeline.py](../../apps/agents/communication/pipeline.py#L515)). This does
not implement immediate annotated delivery or retroactive retraction. The default fallback still has
only two English keywords ([content_safety.py](../../apps/agents/common/content_safety.py#L65)).

Immediate no-approval delivery in FR-009/US3-AS3 also conflicts with this spec's unchanged-HITL assumption,
F07 and SCP-075, and with the constitution's public-output review gate
([constitution.md](../../.specify/memory/constitution.md#L285)). No retirement/exception can be inferred
from a later generic workflow or from the plan's authored PASS table.
The accepted [keyword fallback ADR](../../docs/corpus/aidr/decisions/adr-f07-keyword-fallback.md#L38)
also requires human review before publication; [ADR-033-03](../../docs/corpus/aidr/decisions/adr-033-03-hitl-spec-008-delegation.md#L9)
retains spec-008 approval authority. Neither explicitly identifies FR-009 as retired or amended.

- [ ] AUD-025-007 Resolve fallback approval authority and enforce a single-probe audited fallback lifecycle

  **Original obligations:** FR-009; T043, T044, T045, T050, T051; US3-AS3; EC-04; F07; SCP-075; plan
  constitutional gates 12/14; review_flag entity and research R9.
  **Expected versus actual / impact:** Outages should avoid repeated service timeouts while retaining
  visible degraded-mode status and a legitimate operator remedy. Concurrent probes and lost fallback
  metadata defeat that control; silently removing approval would violate a stronger documented gate.
  **Developer instructions:** Have the product/security/public-information owners record an explicit
  authority resolution for FR-009 versus the constitution/F07 through the existing governance process.
  Do not bypass approval pending that resolution. In `common.content_safety_circuit_breaker`, atomically
  grant one half-open probe and route all others to fallback; retain per-outage counts and complete
  transition telemetry. Propagate validation method/review flag through `ContentSafetyDetail`, alert
  persistence, serializers, delivery and reviewer views. Implement the resolved delivery rule, authorized
  false-positive override, manual pause and retroactive retraction with an immutable audit trail.
  Dependencies: AUD-025-001 identity, AUD-025-006 validation, existing approval/tenant safeguards.
  **Tester instructions:** Extend the existing content-safety and communication pipeline/approval tests
  using an injected monotonic clock and SDK transport. Assert failure counts 1/2/3, 60-second boundary,
  concurrent validators with exactly one probe, success/failure recovery, no automatic throttle, and
  accurate five-event extra fields/fallback summary. Assert flagged metadata survives persistence and
  reaches reviewers/recipients; test unauthorized override/retraction and the explicitly resolved human
  gate without assuming that source text proves an approval occurred.
  **Future validation:** After the documented policy resolution, in the prepared isolated test environment,
  run `python -m pytest tests/unit/test_content_safety_pipeline.py tests/unit/test_communication_pipeline.py tests/unit/test_communication_approval.py -v`.
  Expected: single-probe recovery and policy-consistent observable fallback/override/retraction behavior.
  **Completion:** Explicit authority evidence exists and the implementation, tests and contract agree;
  obtaining approvals or executing these tests is outside this audit.

### High: Translation Still Uses Lexical Similarity and Can Score Its Own Fallback

The actual implementation is relocated from the planned delivery module to
[translator.py](../../apps/agents/communication/translator.py#L273). It still counts words; it does not
call an embedding service. Back-translation excludes action items and supplies the original English
body as fallback ([translator.py](../../apps/agents/communication/translator.py#L247)); the mixin returns
that text on outage ([llm_mixin.py](../../apps/agents/common/llm_mixin.py#L202)), so self-comparison can score
1.0 without validating the translated meaning. Low scores do set a real flag in the pipeline, which is
partial credit ([pipeline.py](../../apps/agents/communication/pipeline.py#L358)). The new quality tests
exercise a separate test-local cosine function and constants, not production translation
([test_translation_quality.py](../../tests/unit/test_translation_quality.py#L17)).

- [ ] AUD-025-008 Use semantic translation scoring without self-comparison or unchecked action text

  **Original obligations:** FR-019, FR-020; SC-009; T078, T079, T080, T081, T082; US8-AS1, US8-AS2, US8-AS3;
  research R8 and R16's appended embedding/fallback paragraphs; FR-007(c) tone-drift dependency.
  **Expected versus actual / impact:** Meaning-preserving rephrasing should pass >=0.85; directional,
  severity and critical-term changes should be flagged. Word overlap and original-text fallback can
  conceal dangerous meaning changes, including instructions omitted from the back-translation request.
  **Developer instructions:** Fix `communication.translator` and Stage 6, not the obsolete planned file
  location. Inject the configured Azure embedding client/deployment, score complete title/body/actions,
  validate vector dimensions/finite nonzero norms, and preserve the 0.85 boundary. Treat failed or
  template-substituted back-translation as unverified/flagged, never an independent identical translation.
  If the explicitly specified lexical outage fallback is retained, emit `embedding_fallback`, preserve
  degraded provenance and review flags, and do not count it as semantic-quality success. Persist and
  surface low-score warnings with score, target language and actual alert ID. Reuse common embedding
  infrastructure only after connecting it to this caller; existing RAG embeddings alone are not delivery.
  **Tester instructions:** Extend existing
  [test_communication_translator.py](../../tests/unit/test_communication_translator.py#L1),
  [test_translation_quality.py](../../tests/unit/test_translation_quality.py#L1), and pipeline tests using
  an injected embedding transport and the real scoring method. Assert the client receives distinct
  original/back-translated complete text, paraphrases pass, north/south and severity swaps fail, 0.85
  passes, 0.849 flags, empty/zero/malformed vectors fail safely, outage is annotated, and original-text
  fallback cannot pass as independently verified. Evaluate >=30 labeled pairs per language, including
  >=10 preserving and >=10 altering, through the production scorer rather than hand-selected vectors.
  **Future validation:** In the prepared environment with injected model clients, run
  `python -m pytest tests/unit/test_communication_translator.py tests/unit/test_translation_quality.py tests/unit/test_communication_pipeline.py -v`.
  Expected: production-path scoring/flags and >=90% accuracy per the documented corpus evaluation.
  **Completion:** Connected embedding validation covers all meaningful alert text and its degraded path
  cannot masquerade as a successful quality measurement.

### High: Transport Requirements Stop at the Plan and Conflict with the Receiver

Evacuation calculates transport requirements, persists a plan and returns without a resource handoff
([pipeline.py](../../apps/agents/evacuation/pipeline.py#L283)). The relocated shared DTO is a flat request,
not the contract's non-empty `transportRequirements` list with GeoJSON pickup/dropoff and numeric priority
([handoff_payloads.py](../../apps/agents/common/handoff_payloads.py#L17)). The actual transport coordinator
puts priority, pickup and destination into free-text notes
([transport.py](../../apps/agents/evacuation/transport.py#L140)). Resource intake expects `vehicleType`,
`quantity`, `pickupLocation`, and string priority
([pipeline.py](../../apps/agents/resource_allocation/pipeline.py#L313)); `normalise_urgency` calls `.lower()`
on that priority ([priority.py](../../apps/agents/resource_allocation/priority.py#L49)). Passing the required
integer therefore cannot be handled by that path. Existing contract tests assert the old shape
([test_resource_allocation_handoff.py](../../tests/contract/test_resource_allocation_handoff.py#L33)).
The replacement workflow runs evacuation and resource allocation concurrently with the same risk input,
so it does not carry evacuation output into resource planning either
([builder.py](../../apps/agents/maf_runtime/workflow/builder.py#L132)). Searches of agent Python producers
and DTO references found no alternative sender implementing contract 1a.

- [ ] AUD-025-009 Deliver typed evacuation transport requirements into priority-aware allocation

  **Original obligations:** FR-010, FR-011; SC-005; T054, T055, T056, T057, T058, T059; US4-AS1, US4-AS2,
  US4-AS3; research R4/R16; data-model TransportHandoffPayload/TransportRequirement; contract 1a.
  **Expected versus actual / impact:** Non-ambulatory transport needs must arrive as actionable typed
  requests and be processed 5-first. Current calculations do not result in delivery; manually supplying
  the new contract would collide with older field names and string-priority parsing.
  **Developer instructions:** Own the producer in `evacuation.transport` and the post-persistence pipeline
  stage, the shared DTO, and the resource pipeline/priority adapter. Preserve structured capacity,
  vehicle count/type, pickup/dropoff GeoJSON, zone/plan references, vulnerability and severity-aligned
  priority instead of recovering them from notes. Validate positive counts and integer 1-5; sort on that
  priority and preserve old clients through an explicit versioned/canonical adapter. Send idempotently via
  the connected nonblocking delivery/dead-letter path (AUD-025-002/004). For MAF, make allocation depend on
  evacuation output or dispatch an equivalent typed event; parallel risk-only inputs are insufficient.
  Distinguish true all-ambulatory zero demand from missing facility data, and emit the specified skip log
  only for the former. Retain human deployment authority and simulation isolation.
  **Tester instructions:** Extend existing
  [test_handoff_payloads.py](../../tests/unit/test_handoff_payloads.py#L1),
  [test_evacuation_transport.py](../../tests/unit/test_evacuation_transport.py#L1),
  [test_resource_allocation_pipeline.py](../../tests/unit/test_resource_allocation_pipeline.py#L136), and
  [test_resource_allocation_handoff.py](../../tests/contract/test_resource_allocation_handoff.py#L1).
  Start with real facility/zone/assembly fixtures and an injected receiver/repository; assert exact
  contract serialization, source/target/tenant/plan identity, capacity and both coordinates in resulting
  demands, and 5-before-1 allocation under scarcity. Cover priority 0/6/string/bool, zero vehicles, missing
  dropoff, all-ambulatory versus missing-data cases, duplicate events and receiver outage/recovery.
  **Future validation:** In the prepared isolated environment after AUD-025-002/004, run
  `python -m pytest tests/unit/test_handoff_payloads.py tests/unit/test_evacuation_transport.py tests/unit/test_resource_allocation_pipeline.py tests/contract/test_resource_allocation_handoff.py -v`.
  Expected: a real producer-to-receiver assertion,
  preserved legacy compatibility, correct numeric ordering and the exact zero-demand skip event.
  **Completion:** Every qualifying plan creates a durable delivered transport handoff; schema-only tests
  and an empty MAF facade plan do not constitute completion.

### High: Resource Plans Do Not Become Agency-Scoped Dispatch Notifications

Resource processing persists the deployment plan, writes audit and returns; there is no Stage 8b sender
([pipeline.py](../../apps/agents/resource_allocation/pipeline.py#L139)). The shared dispatch DTO instead
contains a summary and optional untyped assignments, not contract 1b's required assignment structure
([handoff_payloads.py](../../apps/agents/common/handoff_payloads.py#L40)). Communication retrieves assessment
and recommendation fields rather than dispatch assignments
([pipeline.py](../../apps/agents/communication/pipeline.py#L225)), and deduplicates by incident/hazard without
agency ([dedup.py](../../apps/agents/communication/dedup.py#L58)). If per-agency messages were simply added,
later agencies sharing the incident/general hazard could be discarded. Neither the DTO tests nor the
existing bus-chain test proves recipient dispatch; the latter subscribes a no-op handler
([test_handoff_chain.py](../../tests/integration/test_handoff_chain.py#L11)).

- [ ] AUD-025-010 Produce and consume actionable per-agency dispatch notifications

  **Original obligations:** FR-012, FR-013; SC-006; T060, T061, T062, T063, T064; US5-AS1, US5-AS2,
  US5-AS3; data-model DispatchHandoffPayload/DispatchAssignment; contract 1b; research R5.
  **Expected versus actual / impact:** Each persisted personnel/supply assignment must be communicated
  to its assigned agency. Plan-only persistence and generic public-alert intake leave field teams without
  actionable notifications and risk dropping or exposing another agency's assignments if wired naively.
  **Developer instructions:** Own the post-persistence resource stage and assignment-to-notification
  mapping, shared DTO, and communication intake/segmentation/dedup. Preserve originating inventory/agency
  identity, quantity, destination Point/name, resource detail, and mapping 5=critical, 4=high, 3=moderate,
  1/2=low. Group only after successful persistence, deliver one idempotent event per agency, and key
  notification dedup/recipient selection by tenant, plan version, agency and dispatch type. Distinguish
  operational dispatch from public warnings; retain applicable safety, language and approval controls.
  Implement equivalent workflow ordering/consumption, not merely nested plan dictionaries. Depend on
  AUD-025-002/004/006/009; do not silently claim dispatch when persistence or a delivery client is absent.
  **Tester instructions:** Extend existing
  [test_resource_allocation_pipeline.py](../../tests/unit/test_resource_allocation_pipeline.py#L1),
  [test_handoff_payloads.py](../../tests/unit/test_handoff_payloads.py#L77),
  [test_communication_handoff.py](../../tests/unit/test_communication_handoff.py#L1), and
  [test_handoff_chain.py](../../tests/integration/test_handoff_chain.py#L1). Use two agencies with different
  personnel/supply assignments in one incident; assert exactly two deliveries, no cross-agency fields,
  retained quantities/destinations, numeric-to-string priority mapping, and actual receiver consumption.
  Cover missing agency, invalid counts/type/geometry, duplicate plan-version delivery, a new version,
  persistence failure, and communication outage with nonblocking retry/dead-letter/recovery.
  **Future validation:** In the prepared isolated environment, run
  `python -m pytest tests/unit/test_resource_allocation_pipeline.py tests/unit/test_handoff_payloads.py tests/unit/test_communication_handoff.py tests/integration/test_handoff_chain.py -v`.
  Expected: receiver and per-agency privacy assertions, not just a persisted plan
  or bus status. **Completion:** Every eligible persisted assignment is delivered to the correct agency
  through a validated, idempotent communication path.

### High: Road-Closure Primitives Are Not Connected to Monitoring or Route Updates

Closed edges really are excluded by Dijkstra
([router.py](../../apps/agents/evacuation/router.py#L228)), and closure/reopening helpers are implemented
([road_network.py](../../apps/agents/evacuation/road_network.py#L196)). However, Monitoring's only triage
delivery is the risk handoff ([pipeline.py](../../apps/agents/monitoring/pipeline.py#L289)); its completed
processing path has no closure/reopening classification. The shared road DTO uses `full/partial/weight_limit`
and defaults coordinates to zero instead of contract 1c's closure/reopening discriminant and optional
location ([handoff_payloads.py](../../apps/agents/common/handoff_payloads.py#L61)). Evacuation's intake
always follows the assessment-planning path; its graph mutations are zone-derived
([pipeline.py](../../apps/agents/evacuation/pipeline.py#L566)). The existing replanner recognizes closure
trigger descriptions but does not apply them to the graph
([replanner.py](../../apps/agents/evacuation/replanner.py#L100)). A no-path result becomes an empty list,
not a zone/shelter-specific result ([router.py](../../apps/agents/evacuation/router.py#L135)).
The bounded apps Python search found simulation road feeds and replan inputs but no alternative
Monitoring-to-Evacuation closure/reopening delivery, nearest-edge handler, or specified modification log.
The actual [replan entry](../../apps/agents/evacuation/agent.py#L190) contains `pass` blocks for graph,
route, transport, version and persistence work, then reports `material_change=True`; its emitted
PlanUpdated event is therefore not evidence that routes were changed.

- [ ] AUD-025-011 Connect road closure and reopening signals to graph state and affected-plan notifications

  **Original obligations:** FR-014, FR-015; SC-007; T065, T066, T067, T068, T069, T070; US6-AS1, US6-AS2,
  US6-AS3; EC-05; data-model RoadClosureSignalPayload; contract 1c; research R6.
  **Expected versus actual / impact:** Reported road conditions must change the next routes and notify
  already-dispatched affected zones. Existing mutable graph helpers do not establish receipt or use of
  Monitoring signals; empty route output also obscures which zone/shelter pair needs intervention.
  **Developer instructions:** Implement a typed road-event branch in Monitoring and a distinct Evacuation
  intake handler before assessment planning. Support explicit segment IDs and validated nearest-edge
  spatial matching, reject ambiguous/missing locations, preserve closure provenance and baseline weights,
  and prevent reopening one source from clearing an independent hazard closure. Persist/replay incident
  graph state as required across replicas; emit action/signal/segment/road audit fields. Connect the
  existing replanner and notification path to affected active plans, and return explicit no-viable-route
  outcomes rather than routing through blocked edges. Preserve existing zone rules and simulation/tenant
  boundaries; use AUD-025-002/004's delivery and AUD-025-010's scoped notification mechanisms.
  **Tester instructions:** Extend existing
  [test_evacuation_road_network.py](../../tests/unit/test_evacuation_road_network.py#L175),
  [test_evacuation_handoff.py](../../tests/contract/test_evacuation_handoff.py#L1), and
  [test_handoff_payloads.py](../../tests/unit/test_handoff_payloads.py#L99). Use the existing road-network
  fixture plus a tiny two-path graph: send a real Monitoring closure, recompute, assert the segment is
  excluded; reopen and assert original routing/weights. Cover nearest-edge ties, invalid/unknown segment,
  repeated/stale events, independent overlapping closures, all paths blocked, and closure after dispatch.
  Assert affected zone/shelter IDs, source-signal audit metadata, and updated notification recipients.
  **Future validation:** In the prepared environment with injected delivery and clock, run
  `python -m pytest tests/unit/test_evacuation_road_network.py tests/contract/test_evacuation_handoff.py tests/unit/test_handoff_payloads.py -v`.
  Expected: producer-to-graph-to-notification
  assertions and no blocked-edge traversal. **Completion:** Direct signal-driven routing and update
  delivery work together; helper-only mutation tests are insufficient.

### High: IoT Normalization Does Not Satisfy the Actual Monitoring Envelope

The adapter emits `signal_id/source_id/signal_type/longitude/latitude/ingested_at`
([iot_adapter.py](../../apps/agents/monitoring/iot_adapter.py#L139)), while Monitoring validates a
`SignalEnvelope` requiring nested source, category, occurred/received timestamps, location, confidence,
freshness and validation status ([signal_envelope.py](../../apps/api/app/validators/signal_envelope.py#L26),
[pipeline.py](../../apps/agents/monitoring/pipeline.py#L80)). No model validation or pipeline submission
connects these shapes. The bounded apps source/config search found IoT handling only in the adapter,
not a mounted `/api/v1/iot/telemetry` route. Its Event Grid handshake is a helper return, not an HTTP endpoint.

Dedup correctly uses a locked device/sequence key and schedules 30-second eviction, but missing sequence
defaults to zero ([iot_adapter.py](../../apps/agents/monitoring/iot_adapter.py#L94)). The contract 2a example
omits that key; multiple legitimate messages from one device can therefore collide. Keys are marked
before downstream validation/acceptance, and missing locations become zero coordinates. Tests assert the
adapter's private output shape, not canonical-envelope validation, TTL expiry, or broker-to-pipeline
behavior ([test_iot_adapter.py](../../tests/unit/test_iot_adapter.py#L52)).

- [ ] AUD-025-012 Connect reliable IoT ingestion to canonical signal validation and delivery acknowledgment

  **Original obligations:** FR-016, FR-017, FR-018; SC-008; T071, T072, T073, T074, T075, T077; US7-AS1,
  US7-AS2, US7-AS3; EC-01, EC-03; 10,000-message/second scale; IoTSignalMessage/SignalEnvelope entities;
  contract 2a and research R7.
  **Expected versus actual / impact:** Valid telemetry must reach Monitoring within five seconds with
  duplicate suppression and retained outage delivery. The emitted shape cannot pass the actual intake,
  there is no webhook route, and zero-sequence/default-coordinate behavior can lose or mislocate signals.
  **Developer instructions:** Own the adapter and the explicitly selected service entrypoint/router.
  Register validation and telemetry HTTP handling, define Event Grid/CloudEvents batch/body decoding and
  trusted device identity, and produce the real SignalEnvelope before submitting to the existing pipeline.
  Specify required sequence metadata instead of silently assigning zero; preserve timestamp, metadata,
  category and location semantics, including named-location resolution. Coordinate dedup reservation and
  release with successful durable acceptance so failed attempts can be retried. Define replica-local
  dedup assumptions explicitly, retain bounded TTL memory, and implement backpressure/acknowledgments
  that let the infrastructure retain life-safety messages rather than silently acknowledge loss.
  Dependencies: AUD-025-004 concurrency, AUD-025-005 location, AUD-025-013 infrastructure wiring.
  **Tester instructions:** Extend existing
  [test_iot_adapter.py](../../tests/unit/test_iot_adapter.py#L1) and
  [test_async_handoff_retry.py](../../tests/unit/test_async_handoff_retry.py#L1), using the real envelope
  validator and an injected Monitoring receiver. Test subscription validation over HTTP, both event
  discriminator forms, batch/encoded bodies as supported by the explicit contract, invalid values/time,
  required sequence absence, same/different device and sequence, exact 30-second eviction, retries after
  failed intake, named/no location, concurrent duplicates, receiver outage and queue pressure. Assert
  required model fields, one accepted pipeline entry, no premature success acknowledgment, retained
  recovery and no fabricated coordinates. Use fake time for unit expiry; measure throughput separately.
  **Future validation:** In the prepared isolated environment, run
  `python -m pytest tests/unit/test_iot_adapter.py tests/unit/test_async_handoff_retry.py -v`.
  Expected: HTTP-to-canonical-pipeline assertions, deterministic TTL behavior and retry-safe acceptance.
  **Completion:** A registered, authenticated transport path produces accepted canonical envelopes;
  five-second and 10K/s outcomes require attributable subsequent measurements.

### High: Authored Infrastructure and Current Runtime Do Not Activate These Capabilities

Relocated infrastructure deserves credit: AU-restricted Content Safety with managed identity,
local-auth disabled, role/diagnostic hooks, and an IoT Hub/Event Grid topic with optional retrying
subscription are authored ([content-safety.bicep](../../infra/modules/content-safety.bicep#L27),
[iot-hub.bicep](../../infra/modules/iot-hub.bicep#L31)). But root calls supply only name/location/tags
([main.bicep](../../infra/main.bicep#L453)). Consequently the caller-principal list is empty and the empty
webhook default suppresses the subscription ([iot-hub.bicep](../../infra/modules/iot-hub.bicep#L81)).
Both resources disable public access, while the root does not connect their private access path. A
separate Content Safety PE module exists but is not referenced by these root calls. Their outputs are
not passed into the agent/API environment blocks
([main.bicep](../../infra/main.bicep#L1036), [main.bicep](../../infra/main.bicep#L1140)). No spec-025
dead-letter/radius/named-location containers were found in the bounded infrastructure search.

The shipped agent container runs `python -m dispatcher`
([Dockerfile](../../apps/agents/Dockerfile#L48),
[dispatcher entry](../../apps/agents/dispatcher/__main__.py#L12)). That app exposes health and simulation role
invocation, returning chat summaries, not the operational pipelines or IoT/poller startup
([agent.py](../../apps/agents/dispatcher/agent.py#L191)). A newer workflow exists, but its legacy facades
return placeholder plans/decision records and its MAF path parses model text; this is not explicit
retirement of spec-025's deterministic obligations. The manifest requires Python >=3.12 while the local
quickstart says 3.11+. Environment examples split settings by service but omit an agents `ENVIRONMENT`
selection; root deployment uses `COSMOS_ENDPOINT`, not the documented `COSMOS_DB_ENDPOINT`.

- [ ] AUD-025-013 Wire the selected operational runtime to its infrastructure and compatible configuration

  **Original obligations:** T001, T003, T053, T076, T083, T084, T086; FR-003a, FR-006, FR-007, FR-016,
  FR-021; plan platform/residency/managed-identity/scale constraints; quickstart; contracts 2a, 2b, 6, 7.
  **Expected versus actual / impact:** Resource declarations and dependency additions must connect to
  reachable, correctly configured services. Current defaults omit the subscription, service-user grant,
  feature endpoints and durable containers, while the container starts a different simulation surface.
  **Developer instructions:** Have the service/runtime owners explicitly select and wire the operational
  entrypoint while preserving the simulation dispatcher contract. Retain feature obligations through any
  MAF migration; a replacement needs explicit approved retirement/compatibility evidence, not a comment.
  In the root template and relocated modules, pass the real agent identity, endpoint, diagnostics,
  private networking/DNS and webhook authentication; provision and inject the shared store containers
  and schema-consistent partition keys. Validate Event Grid reachability to the internal-ingress service
  without disabling network protections. Size IoT throughput from a documented model rather than assume
  default S1 capacity 1 establishes 10K/s. Follow repository AVM/policy rules; external availability,
  policy discovery and deployment remain separate future authorized work. Align environment names,
  explicit production auth, embedding deployment, API `/api` versus contract `/api/v1`, and the existing
  dev/staging/production profiles without breaking current clients. Update the recipe for Python 3.12+
  and actual test/module locations through a later authorized change, not this audit.
  **Tester instructions:** Use existing `tests/devops` and `tests/contract` test homes and their text/config
  assertion pattern; a dedicated spec-025 infrastructure/startup test file there would be **proposed new**,
  not existing evidence. Extend existing IoT, management and radius tests with factory configuration
  fixtures. Assert nonempty webhook/principal arguments, endpoint injection, correct partitions,
  startup/poller/router registration, AU resource locations, production-key rejection, and unchanged
  legacy HTTP consumers. Negative fixtures should omit required settings, supply unknown environments,
  cross service-variable aliases, and select the dispatcher without operational wiring.
  **Future validation:** Once the proposed static infrastructure tests exist, run
  `python -m pytest tests/devops tests/contract/test_radius_lookup_api.py tests/contract/test_dead_letter_api.py tests/unit/test_iot_adapter.py -v`;
  in a separately prepared Bicep environment run `bicep build infra/main.bicep` and the repository's IaC
  lint gate. These are future commands only. Expected: correct compiled wiring and executable app-factory
  assertions; compilation alone does not establish deployment, capacity, reachability or approval.
  **Completion:** The selected runtime consumes the provisioned services with verified static contracts,
  and any deployment/performance claims are supported by separate attributable evidence.

### Important: Test Scaffolding Is Not Acceptance Evidence and Most New Unit Tests Are Outside CI Discovery

All twelve language directories exist but contain only empty `.gitkeep` placeholders. Scoped filename
searches for content-safety/translation data in JSON/JSONL/CSV/YAML found no replacement corpus; searches
of test consumers found no SC-004 corpus runner. The existing benchmark directory has no content-safety
accuracy benchmark. The main CI job runs contract/integration tests and benchmarks, not the root unit
directory ([ci.yml](../../.github/workflows/ci.yml#L131)); other workflow unit selections are confined to
eval or spec-035. The root test setup supplies import paths
([conftest.py](../../tests/conftest.py#L10)), so authoring files alone does not add them to that CI command.

Alternative pipeline benchmarks exist, but repeatedly reuse the same signal/handoff IDs with
session-scoped deduplicators and no-op delivery, and do not assert the spec-025 failed-agent end-to-end
P95 ([test_pipeline_performance.py](../../tests/benchmark/test_pipeline_performance.py#L188)). The benchmark
comparison hook even skips regression failure when `CI` is set
([conftest.py](../../tests/benchmark/conftest.py#L87)). These observations limit evidence credit; no test
was executed and no pass/fail result is inferred.

- [ ] AUD-025-014 Establish meaningful corpora, acceptance assertions, CI discovery, and attributable results

  **Original obligations:** T002, T012, T015, T025, T026, T037, T038, T047, T048, T049, T050, T051, T052,
  T052b, T058, T059, T063, T064, T070, T077, T081, T082, T085, T086; SC-001 through SC-009;
  all story independent tests; 1,000 signals / 10K IoT messages per second / 50 redeliveries; R15.
  **Expected versus actual / impact:** Acceptance must exercise connected production logic with meaningful
  assertions and representative labeled data. Placeholder corpora, test-local reimplementations, mocked
  decisions, zero-attempt timing and undiscovered unit files cannot establish the promised outcomes.
  **Developer instructions:** The test/CI owners should extend the existing test homes named in
  AUD-025-001 through AUD-025-013, connect them to required CI selection, and retain current test naming
  compatibility with an explicit quickstart mapping. Populate the existing six-language corpus folders
  with labeled, provenance-bearing fixtures and a manifest recording category/locale/counts, reviewer
  attribution and hashes. Require >=50 unsafe and >=50 safe per language covering all six specified
  violation categories, plus >=30 translation pairs per language with >=10 preserving and >=10 altering.
  New corpus files and a dedicated accuracy benchmark are **proposed**, not existing evidence. Keep
  deterministic client-shape tests separate from real model accuracy/latency evidence; never fabricate
  results or obtain external approval as part of this audit.
  **Tester instructions:** After implementation and environment preparation, execute the original
  unit/contract/integration/benchmark scope with unique non-deduplicated work items, inspect collection
  lists, and inject a deliberate incorrect result to show the relevant gate fails. Assert each locale's
  unsafe detection >=95%, safe pass >=99%, semantic accuracy >=90%, P95 <=5 seconds under a failed agent,
  <=2-second resolved blocking boundary, and no loss under specified scale/recovery cases. Record exact
  command, SHA, dependencies/configuration, corpus hashes, seed, sample counts, per-language confusion
  matrices, timing distribution and immutable result references. CI gate status is not inferred from YAML.
  **Future validation:** In a prepared Python 3.12+ test environment, run
  `python -m pytest tests/unit/ tests/contract/ tests/integration/ tests/benchmark/ -v --tb=short` and replay
  the corrected 13 quickstart commands. A separate authorized measurement environment is required for
  actual service throughput/model accuracy. Expected: all required cases are collected, meaningful
  assertions pass, deliberate regressions fail, and attributable artifacts substantiate any SC claim.
  **Completion:** Required acceptance coverage is executable/discovered and successful outcomes have
  trustworthy attributable evidence; until then execution tasks and measurable SCs remain UNVERIFIED.

### Important: Review Declarations and Later Amendments Lack Spec-Specific Closure Evidence

The checklist marks all 16 items complete, including no implementation detail and achieved measurable
outcomes ([requirements.md](checklists/requirements.md#L9)), although the specification names concrete
SDK/auth/database/circuit-breaker mechanisms and the static findings contradict feature completion.
The plan's 15 pre-design PASS claims and eight post-design additions are authored assessments, not signed
reviews or measured results. The 11 phase consultation rosters have no attributable local outputs.

The required F02 ADR is not the relocated async-bridge ADR: the former must document collection/triage
ownership. The F07 keyword-fallback and later HITL ADRs support human review but do not explicitly record
the specified dismissal of autonomous-public-alert wording. Searches were bounded to this local folder
and the decision registers under `docs/aidr/decisions`, `docs/corpus/aidr/decisions`, and `docs/decisions`.
No equivalent F02 decision was found; F07 is partially supported by the inspected existing HITL decisions.

PER-067/068's validation claim is not a dated named practitioner attestation. The referenced operational
profiles explicitly defer concrete identities to review
([spec.md](../001-disaster-response-hub/spec.md#L169)); the persona contract requires named/dated
SME/practitioner records ([persona-profile.md](../027-spec-hardening/contracts/persona-profile.md#L16)).
HYP-023's named `HYP-HYP-023` stub does not exist in the referenced evidence folder or the bounded HYP-023
filename search; its naming also conflicts with the `HYP-NNN` contract. Portfolio-wide structural rubric
snapshots ([rubric-postfeature.md](../028-capstone-alignment/evidence/rubric-postfeature.md#L3)) do not
establish this spec's consultation history or +1-band causal outcome. D-009/non-AU deferral is explicit
([decision-record.md](../028-capstone-alignment/evidence/decision-record.md#L13)); it is not retired by the
constitution's later limited model-hosting carve-out.

- [ ] AUD-025-015 Reconcile local contracts and attach attributable decision, persona, and review evidence

  **Original obligations:** T087, T088; F02/F07 dismissal records; PER-067, PER-068, PER-069; HYP-023;
  SCP-074, SCP-075, SCP-076, SCP-077; all local checklist/constitution-check claims and 11 phase actor
  consultation obligations; quickstart/research/contract consistency.
  **Expected versus actual / impact:** Decisions and validation must be traceable to the correct
  obligation and named evidence, not to similarly numbered ADRs, generic PASS text or portfolio means.
  Unresolved authority and stale recipes can cause unsafe implementation or mistaken completion claims.
  **Developer instructions:** The product-owner/BA, observer/auditor and designated technical owners should
  add or link the actual collection-versus-triage decision and explicitly map the public-alert autonomy
  dismissal to the existing HITL decisions, including AUD-025-007's conflict resolution. Preserve all
  original history; do not silently rewrite task states or freeze a new baseline retroactively. Reconcile
  `/api/v1` versus `/api`, GeoJSON Feature versus geometry, severity/priority types, status/envelope naming,
  required IoT sequence, and Python/test/path changes through authorized spec governance. Create the
  correctly named HYP-023 stub as a **proposed new artifact** only in its authorized owning workflow;
  keep it Not tested until a bounded per-spec measurement and consultation record exist. Replace or
  substantiate validated persona declarations with named, dated, scenario-linked SME/practitioner
  evidence; keep PH/JP/BD placeholders and their D-009/data-sharing/calibration preconditions deferred.
  **Tester instructions:** Use the existing
  [validate-section-coverage.ps1](../028-capstone-alignment/scripts/validate-section-coverage.ps1#L35)
  as a structural reference only: it checks headings, not meaning, sign-offs, or outcomes. A spec-025-only
  semantic/link/attestation validator in an existing test home is **proposed**. It should reject missing
  stub links, double-prefixed HYP IDs, unsigned/undated validation, portfolio-only hypothesis measurements,
  false resolved markers, contradictory contracts, missing phase consultations, and unauthorized scope
  promotion. Accept a correct six-section stub marked Not tested and explicit unresolved/deferred states.
  **Future validation:** After an authorized documentation update, run a spec-025-scoped PowerShell text
  validator for links/IDs/required evidence fields, followed by the relevant existing contract tests.
  Expected: structural checks pass while unperformed reviews/measurements still show UNVERIFIED.
  **Completion:** Explicit decisions resolve contradictions, all referenced artifacts exist, and claims
  of consultation/approval/uplift have attributable records. This audit obtains none of those approvals.

## Requirement Coverage

There are 23 numbered FRs (including FR-003a and FR-004a) and 9 SCs. FR-007(a), (b), and (c) are
subclauses, not three additional original IDs. Cross-spec FR numbers in the later persona/hypothesis
prose retain their referenced scope. SC status below is evidence status for the measurable outcome;
the underlying static defect is stated alongside it rather than inventing a failed runtime result.

| Requirement | Status | Expected obligation and inspected evidence | Follow-up |
| --- | --- | --- | --- |
| FR-001 | PARTIAL | [Nonblocking pipelines](spec.md#L152): async leaf retries exist, but [run_async](../../apps/agents/common/async_bridge.py#L15) waits synchronously and pipeline I/O remains synchronous. | AUD-025-004 |
| FR-002 | CONFLICT | [Two-second sequence cap](spec.md#L153) differs from T005's per-attempt rule; [helper](../../apps/agents/common/handoffs.py#L142) times attempts, [channel retry](../../apps/agents/communication/delivery.py#L161) does not. | AUD-025-004, AUD-025-015 |
| FR-003 | PARTIAL | [Structured attempt/final outcomes](spec.md#L154) are present in the [shared helper](../../apps/agents/common/handoffs.py#L148), but not equivalently structured/bounded across OCC and channel callers. | AUD-025-004 |
| FR-003a | PARTIAL | [Durable recovery/terminal state](spec.md#L155): [store/poller](../../apps/agents/common/dead_letters.py#L48) exist; callbacks, API and startup are disconnected, backoff is not scheduled, manual delivery does not run, terminal immutability is not enforced. | AUD-025-002, AUD-025-003 |
| FR-004 | PARTIAL | [Agent-produced hazard map](spec.md#L159): [generator](../../apps/agents/risk_assessment/hazard_map.py#L29) exists, but [assessment construction](../../apps/agents/risk_assessment/agent.py#L232) never populates the map. | AUD-025-005 |
| FR-004a | PARTIAL | [Named lookup or validation rejection](spec.md#L160): [repository](../../apps/agents/risk_assessment/named_locations.py#L38) resolves/logs standalone; pipeline does not call it and [generator](../../apps/agents/risk_assessment/hazard_map.py#L50) fabricates zero coordinates on absence. | AUD-025-005 |
| FR-005 | PARTIAL | [Geometry/severity/type/time](spec.md#L161) exist on a [standalone Feature](../../apps/agents/risk_assessment/hazard_map.py#L64), not every assessed hazard's persisted domain map; heterogeneous severity is not preserved. | AUD-025-005 |
| FR-006 | PARTIAL | [Five hazard types, severities 1-5, editable Cosmos radii, first-deploy seed, next-generation visibility](spec.md#L162): [repository/seeds](../../apps/agents/risk_assessment/hazard_radius.py#L17) exist, but [API store](../../apps/api/app/api/routes/radius_lookup.py#L53) is independent memory and generator is unwired. | AUD-025-005, AUD-025-013 |
| FR-007 | PARTIAL | [All outbound messages; Azure categories, originating facts, English pre-translation tone, production MI](spec.md#L166): [MI branch and validators](../../apps/agents/common/content_safety.py#L73) exist, but [Stage 7](../../apps/agents/communication/pipeline.py#L367) bypasses templates and never invokes factual/tone; result loses categories/layer metadata. | AUD-025-006 |
| FR-008 | PARTIAL | [All translated languages](spec.md#L167): [translator loop](../../apps/agents/communication/translator.py#L58) supports six configured locales, but [tests](../../tests/unit/test_content_safety_pipeline.py#L81) only establish keyword/language heuristics, not Azure locale coverage. | AUD-025-006, AUD-025-014 |
| FR-009 | CONFLICT | [Three-failure/60s/single-probe fallback, five events, immediate flagged delivery, retraction, no throttle](spec.md#L168): [breaker](../../apps/agents/common/content_safety_circuit_breaker.py#L35) lacks probe exclusivity; [persistence](../../apps/agents/communication/pipeline.py#L515) always waits for review; [ADR](../../docs/corpus/aidr/decisions/adr-f07-keyword-fallback.md#L38) and constitution require that review. | AUD-025-007, AUD-025-015 |
| FR-010 | MISSING | [Create and deliver transport](spec.md#L172): [completed evacuation path](../../apps/agents/evacuation/pipeline.py#L283) persists/returns without sender; bounded producer/DTO/workflow search found no equivalent transport transfer. | AUD-025-009 |
| FR-011 | CONFLICT | [Vehicle/capacity/pickup/dropoff/integer priority](spec.md#L173): [shared DTO](../../apps/agents/common/handoff_payloads.py#L17) and [receiver](../../apps/agents/resource_allocation/pipeline.py#L313) use different schemas; [priority parser](../../apps/agents/resource_allocation/priority.py#L49) requires a string. | AUD-025-009 |
| FR-012 | MISSING | [Per-assignment communication handoff](spec.md#L177): [allocation path](../../apps/agents/resource_allocation/pipeline.py#L139) has no post-persistence dispatch sender; workflow aggregation is not an agency handoff. | AUD-025-010 |
| FR-013 | CONFLICT | [Assignment type, quantity, destination, agency](spec.md#L178): [dispatch DTO](../../apps/agents/common/handoff_payloads.py#L40) accepts untyped optional assignments; [communication intake](../../apps/agents/communication/pipeline.py#L225) ignores dispatch structure. | AUD-025-010 |
| FR-014 | PARTIAL | [Direct Monitoring closures/reopenings before route calculation](spec.md#L182): [graph mutations](../../apps/agents/evacuation/road_network.py#L196) and route exclusion exist, but no Monitoring sender or distinct receiving handler was found. | AUD-025-011 |
| FR-015 | MISSING | [Originating signal/segment modification log](spec.md#L183): [zone-driven mutations](../../apps/agents/evacuation/pipeline.py#L602) lack that signal audit and the named event is absent in bounded agent search. | AUD-025-011 |
| FR-016 | PARTIAL | [Standard IoT pathway plus HTTP](spec.md#L187): [adapter](../../apps/agents/monitoring/iot_adapter.py#L69) and [IoT module](../../infra/modules/iot-hub.bicep#L31) exist, but webhook is not mounted and subscription condition is false by root default. | AUD-025-012, AUD-025-013 |
| FR-017 | CONFLICT | [Canonical SignalEnvelope before pipeline](spec.md#L188): [adapter output](../../apps/agents/monitoring/iot_adapter.py#L139) omits required [intake model](../../apps/api/app/validators/signal_envelope.py#L26) fields. | AUD-025-012 |
| FR-018 | PARTIAL | [Composite device/sequence 30-second TTL dedup](spec.md#L189): [locked cache/eviction](../../apps/agents/monitoring/iot_adapter.py#L43) exists; sequence defaults to zero, pipeline integration/TTL assertion/replica acceptance remain incomplete. | AUD-025-012, AUD-025-014 |
| FR-019 | MISSING | [Embedding semantic similarity](spec.md#L193): relocated [production scorer](../../apps/agents/communication/translator.py#L273) still uses word counts; searched common embedder is a RAG helper, not a translator caller. | AUD-025-008 |
| FR-020 | PARTIAL | [Below-0.85 human review flag](spec.md#L194): [Stage 6](../../apps/agents/communication/pipeline.py#L358) flags low scores, but body-only lexical scoring and original-text fallback can evade the intended semantic check. | AUD-025-008 |
| FR-021 | PARTIAL | [Authenticated/authorized management with logged 401/403](spec.md#L198): [dependency](../../apps/api/app/middleware/auth.py#L62) disables signature verification, inspection is unprotected by it, token failures miss audit, outer Entra excludes these paths. | AUD-025-001, AUD-025-002 |
| SC-001 | UNVERIFIED | [P95 <=5s under single-agent failure](spec.md#L213): [latency benchmark](../../tests/benchmark/test_pipeline_latency.py#L24) lacks 100-run full-path P95; [alternative pipeline benchmarks](../../tests/benchmark/test_pipeline_performance.py#L188) are isolated stages with reused IDs/no-op delivery. No attributable measurement reviewed. | AUD-025-004, AUD-025-014 |
| SC-002 | UNVERIFIED | [<=2s measured sequence blocking](spec.md#L214): [slow benchmark](../../tests/benchmark/test_pipeline_latency.py#L47) invokes zero attempts and asserts <5s; asynchronous sleeps alone do not prove caller responsiveness. | AUD-025-004, AUD-025-014 |
| SC-003 | UNVERIFIED | [100% located assessments have polygons](spec.md#L215): [helper tests](../../tests/unit/test_hazard_map.py#L31) do not inspect stored assessments and [constructor](../../apps/agents/risk_assessment/agent.py#L232) omits map. | AUD-025-005, AUD-025-014 |
| SC-004 | UNVERIFIED | [>=95% unsafe detection, >=99% safe pass, >=50+50 per six languages/all six categories](spec.md#L216): [tests](../../tests/unit/test_content_safety_pipeline.py#L81) are keyword/direct helper assertions; twelve corpus directories contain placeholders, no measured classification corpus. | AUD-025-006, AUD-025-014 |
| SC-005 | UNVERIFIED | [100% qualifying transport handoffs delivered](spec.md#L217): [evacuation pipeline](../../apps/agents/evacuation/pipeline.py#L283) never sends; [old intake test](../../tests/contract/test_resource_allocation_handoff.py#L33) constructs its own message. | AUD-025-009, AUD-025-014 |
| SC-006 | UNVERIFIED | [100% resource plans notify communication](spec.md#L218): [allocation pipeline](../../apps/agents/resource_allocation/pipeline.py#L139) lacks sender; [DTO test](../../tests/unit/test_handoff_payloads.py#L77) is not a recipient assertion. | AUD-025-010, AUD-025-014 |
| SC-007 | UNVERIFIED | [Routes exclude received closures](spec.md#L219): [graph tests](../../tests/unit/test_evacuation_road_network.py#L175) directly mutate graph, not Monitoring-to-Evacuation receipt. Closed-edge algorithm is credited, measured connected behavior is not. | AUD-025-011, AUD-025-014 |
| SC-008 | UNVERIFIED | [IoT <=5s with dedup](spec.md#L220): [adapter tests](../../tests/unit/test_iot_adapter.py#L52) stop at noncanonical dictionary; no broker/registered-route/pipeline measurement. | AUD-025-012, AUD-025-014 |
| SC-009 | UNVERIFIED | [>=90% semantic accuracy with >=30 pairs/language and >=10 preserving/altering](spec.md#L221): [test-local cosine](../../tests/unit/test_translation_quality.py#L17) and empty corpus scaffolds cannot substantiate accuracy. | AUD-025-008, AUD-025-014 |

## Acceptance Scenarios

`USn-ASm` are report-local labels for the original numbered scenarios, not new requirements. Each row
assesses the complete scenario, not merely its supporting helper. Actual execution remains UNVERIFIED.

| Scenario | Status | Evidence and scenario-specific result | Follow-up |
| --- | --- | --- | --- |
| US1-AS1 | PARTIAL | [Unavailable downstream does not block caller](spec.md#L20): [async helper](../../apps/agents/common/handoffs.py#L124) yields, but [bridge](../../apps/agents/common/async_bridge.py#L15) blocks pipeline callers. | AUD-025-004 |
| US1-AS2 | PARTIAL | [Other two signals progress](spec.md#L21): [helper tests](../../tests/unit/test_async_handoff_retry.py#L38) have no three-signal concurrent caller assertion. | AUD-025-004, AUD-025-014 |
| US1-AS3 | PARTIAL | [Exhaustion logs/continues/<2s](spec.md#L22): [helper final event](../../apps/agents/common/handoffs.py#L178) exists; no per-sequence deadline or durable callback by default. | AUD-025-002, AUD-025-004 |
| US2-AS1 | PARTIAL | [Located flood assessment polygon](spec.md#L36): [generator tests](../../tests/unit/test_hazard_map.py#L31) cover standalone geometry; [agent constructor](../../apps/agents/risk_assessment/agent.py#L232) omits map. | AUD-025-005 |
| US2-AS2 | PARTIAL | [Merged/adjacent severity zones](spec.md#L37): [union](../../apps/agents/risk_assessment/hazard_map.py#L61) exists but applies a global severity, not highest input severity. | AUD-025-005 |
| US2-AS3 | PARTIAL | [Point-to-severity radius](spec.md#L38): [radius buffer](../../apps/agents/risk_assessment/hazard_map.py#L45) exists standalone; API edits and domain severity are not connected. | AUD-025-005 |
| US3-AS1 | PARTIAL | [Categorized multilingual blocking](spec.md#L52): [Azure helper](../../apps/agents/common/content_safety.py#L135) uses severity-only rejection and [Stage 7](../../apps/agents/communication/pipeline.py#L380) skips templates. | AUD-025-006 |
| US3-AS2 | PARTIAL | [Urgent safe message passes to delivery](spec.md#L53): [keyword/tone tests](../../tests/unit/test_content_safety_pipeline.py#L182) cover helpers, not actual safe six-language delivery. Approval remains separate. | AUD-025-006, AUD-025-014 |
| US3-AS3 | CONFLICT | [Three failures then immediate flagged delivery](spec.md#L54): [breaker](../../apps/agents/common/content_safety_circuit_breaker.py#L35) partially works, but [alert](../../apps/agents/communication/pipeline.py#L519) remains pending_review and policy requires review. | AUD-025-007 |
| US4-AS1 | MISSING | [Finalized transport handoff sent](spec.md#L68): [post-persistence path](../../apps/agents/evacuation/pipeline.py#L302) has no sender. | AUD-025-009 |
| US4-AS2 | CONFLICT | [Vehicle/capacity/both points/priority triage](spec.md#L69): [receiver](../../apps/agents/resource_allocation/pipeline.py#L313) expects camelCase/string priority and omits dropoff/capacity. | AUD-025-009 |
| US4-AS3 | MISSING | [All ambulatory skips and explains](spec.md#L70): [coordinator](../../apps/agents/evacuation/transport.py#L94) logs missing facility data, not the required ambulatory guard/event. | AUD-025-009 |
| US5-AS1 | MISSING | [Persisted assignments produce dispatch](spec.md#L84): [allocation completion](../../apps/agents/resource_allocation/pipeline.py#L139) returns without notification. | AUD-025-010 |
| US5-AS2 | MISSING | [Each agency receives only its assignments](spec.md#L85): [communication retrieval](../../apps/agents/communication/pipeline.py#L225) has no dispatch/agency consumer; [dedup](../../apps/agents/communication/dedup.py#L58) is incident/hazard only. | AUD-025-010 |
| US5-AS3 | MISSING | [Unavailable communication retries/logs](spec.md#L86): [sender path](../../apps/agents/resource_allocation/pipeline.py#L139) absent, so shared retry availability cannot prove this case. | AUD-025-002, AUD-025-004, AUD-025-010 |
| US6-AS1 | PARTIAL | [Monitoring closure changes next route](spec.md#L100): [closed-edge exclusion](../../apps/agents/evacuation/router.py#L228) exists; Monitoring/receiving path is unconnected. | AUD-025-011 |
| US6-AS2 | PARTIAL | [Reopening restores weight](spec.md#L101): [remove_closure](../../apps/agents/evacuation/road_network.py#L205) restores status, but no reopening handoff handler invokes it. | AUD-025-011 |
| US6-AS3 | PARTIAL | [No viable route for blocked pair](spec.md#L102): [Dijkstra](../../apps/agents/evacuation/router.py#L135) returns no path without unsafe traversal, but pair-specific reporting is absent. | AUD-025-011 |
| US7-AS1 | PARTIAL | [Reading reaches pipeline <=5s](spec.md#L116): [adapter](../../apps/agents/monitoring/iot_adapter.py#L139) emits incompatible fields; no HTTP caller or timing evidence. | AUD-025-012, AUD-025-014 |
| US7-AS2 | PARTIAL | [At-least-once dedup before entry](spec.md#L117): [dedup tests](../../tests/unit/test_iot_adapter.py#L17) prove key comparisons only, not TTL expiry/acceptance/replica integration. | AUD-025-012 |
| US7-AS3 | PARTIAL | [Retained outage recovery](spec.md#L118): [subscription retry policy](../../infra/modules/iot-hub.bicep#L97) is authored but conditional subscription is not enabled by [root](../../infra/main.bicep#L466). | AUD-025-012, AUD-025-013 |
| US8-AS1 | CONFLICT | [Semantic not lexical score](spec.md#L132): [translator](../../apps/agents/communication/translator.py#L273) explicitly computes word-frequency similarity. | AUD-025-008 |
| US8-AS2 | UNVERIFIED | [Meaning-preserving rephrasing >=0.85](spec.md#L133): [quality test](../../tests/unit/test_translation_quality.py#L48) uses chosen vectors unrelated to text/model outputs. | AUD-025-008, AUD-025-014 |
| US8-AS3 | PARTIAL | [Meaning inversion below threshold and flagged](spec.md#L134): [Stage 6 flag](../../apps/agents/communication/pipeline.py#L358) exists; no actual inversion corpus and fallback self-comparison can evade it. | AUD-025-008, AUD-025-014 |

### Independent Tests and User Value

The eight independent-test instructions are distinct review obligations; none was executed here.

| Story / Persona / Independent Test | Status | Inspected evidence and limitation | Follow-up |
| --- | --- | --- | --- |
| US1 / emergency coordinator / failure latency | UNVERIFIED | [Story test](spec.md#L16), [helper benchmark](../../tests/benchmark/test_pipeline_latency.py#L47): no connected failed-agent P95/concurrent work measurement. | AUD-025-004, AUD-025-014 |
| US2 / emergency coordinator / located map output | PARTIAL | [Story test](spec.md#L32), [generator tests](../../tests/unit/test_hazard_map.py#L31): helper output, not returned/persisted assessment. | AUD-025-005 |
| US3 / system owner / safe versus unsafe alerts | UNVERIFIED | [Story test](spec.md#L48), [consolidated tests](../../tests/unit/test_content_safety_pipeline.py#L81): no representative multilingual model corpus. | AUD-025-006, AUD-025-007, AUD-025-014 |
| US4 / emergency coordinator / transport recipient | MISSING | [Story test](spec.md#L64), [producer completion](../../apps/agents/evacuation/pipeline.py#L302): no receiver delivery assertion. | AUD-025-009 |
| US5 / field team leader / actionable assignment | MISSING | [Story test](spec.md#L80), [allocation completion](../../apps/agents/resource_allocation/pipeline.py#L139): no dispatch or inspected equivalent scoped workspace task. | AUD-025-010 |
| US6 / emergency coordinator / closure then replan | PARTIAL | [Story test](spec.md#L96), [graph tests](../../tests/unit/test_evacuation_road_network.py#L175): direct helper mutation, not signal-to-graph integration. | AUD-025-011 |
| US7 / sensor operator / standard telemetry pathway | PARTIAL | [Story test](spec.md#L112), [adapter tests](../../tests/unit/test_iot_adapter.py#L52): dictionary-only helper, not broker/HTTP/pipeline round-trip. | AUD-025-012, AUD-025-013 |
| US8 / multilingual recipient / semantic back-translation | UNVERIFIED | [Story test](spec.md#L128), [test-local scorer](../../tests/unit/test_translation_quality.py#L17): no production semantic-quality evidence. | AUD-025-008, AUD-025-014 |

## Original Task Traceability

Source: the complete [tasks.md](tasks.md), including all phase notes, dependencies, actor rosters and
the suffixed T052b. All 89 original states are `[ ]`; none was changed. A static IMPLEMENTED status
does not mark the original task done or establish an execution claim. Proposed missing test paths are
not linked as evidence; relocated existing tests are linked and their actual assertions described.

| Original task | Original state | Status | Inspected evidence and explanation | Follow-up |
| --- | --- | --- | --- | --- |
| T001 | [ ] | PARTIAL | [Agent manifest](../../apps/agents/pyproject.toml#L10) declares Shapely, Content Safety, IoT, NumPy and existing SDKs; [API manifest](../../apps/api/pyproject.toml#L10) declares PyJWT crypto. Per-app dev extras are absent; install/compatibility execution is UNVERIFIED. | AUD-025-013, AUD-025-014 |
| T002 | [ ] | IMPLEMENTED | All six locales exist under both corpus roots; example tracked [safety placeholder](../../tests/fixtures/content_safety/en/.gitkeep) and [translation placeholder](../../tests/fixtures/translation_quality/en/.gitkeep). This task is directory scaffolding only, not corpus data. | None |
| T003 | [ ] | PARTIAL | [Agent example](../../apps/agents/.env.example#L12) and [API example](../../apps/api/.env.example#L7) contain subsets of requested settings; not all eight in both, agents ENVIRONMENT is omitted, deployment uses another Cosmos name. | AUD-025-013 |
| T004 | [ ] | IMPLEMENTED | [Async helper](../../apps/agents/common/handoffs.py#L124) uses Awaitable delivery, awaited sleep, existing retry fields and dead-letter callback; caller behavior is separately deficient. | AUD-025-004 |
| T005 | [ ] | IMPLEMENTED | [wait_for](../../apps/agents/common/handoffs.py#L142) wraps each attempted delivery with timeout 2.0 as T005 says. This does not resolve FR-002's per-sequence ambiguity or synchronous caller blocking. | AUD-025-004, AUD-025-015 |
| T006 | [ ] | IMPLEMENTED | [Helper telemetry](../../apps/agents/common/handoffs.py#L148) emits delivered/retry/dead-letter events with the specified extra keys. A fabricated/None dead-letter ID is not persistence proof. | AUD-025-002, AUD-025-004 |
| T007 | [ ] | PARTIAL | [Risk counter](../../apps/agents/risk_assessment/versioning.py#L39) awaits sleep; [caller](../../apps/agents/risk_assessment/pipeline.py#L392) uses blocking run_async instead of await. | AUD-025-004 |
| T008 | [ ] | PARTIAL | [Communication counter](../../apps/agents/communication/versioning.py#L42) is async; [pipeline](../../apps/agents/communication/pipeline.py#L468) bridges synchronously and container I/O stays synchronous. | AUD-025-004 |
| T009 | [ ] | PARTIAL | [Evacuation counter](../../apps/agents/evacuation/versioning.py#L39) is async; [versioning stage](../../apps/agents/evacuation/pipeline.py#L970) uses run_async. | AUD-025-004 |
| T010 | [ ] | PARTIAL | [Resource counter](../../apps/agents/resource_allocation/versioning.py#L48) is async; [caller](../../apps/agents/resource_allocation/pipeline.py#L659) blocks through run_async. | AUD-025-004 |
| T011 | [ ] | PARTIAL | [Channel retry](../../apps/agents/communication/delivery.py#L161) sleeps asynchronously, but providers remain synchronous and [delivery caller](../../apps/agents/communication/pipeline.py#L596) bridges synchronously. | AUD-025-004 |
| T012 | [ ] | PARTIAL | [Retry tests](../../tests/unit/test_async_handoff_retry.py#L38) cover helper success/exhaustion and event names; no three concurrent callers, elapsed <2s, complete telemetry fields or final-exhaustion event assertion. | AUD-025-004, AUD-025-014 |
| T013 | [ ] | PARTIAL | [Management dependency](../../apps/api/app/middleware/auth.py#L62) implements local key/role branch but deliberately disables JWT signature verification. | AUD-025-001 |
| T014 | [ ] | PARTIAL | [401/403 log helpers](../../apps/api/app/middleware/auth.py#L31) exist, but [JWT validation exceptions](../../apps/api/app/middleware/auth.py#L110) bypass those audit calls. | AUD-025-001 |
| T015 | [ ] | PARTIAL | [Auth tests](../../tests/unit/test_management_auth.py#L18) run only local API-key scenarios and one log-name check; production admin/operator/viewer/expiry/signature cases absent. | AUD-025-001, AUD-025-014 |
| T016 | [ ] | PARTIAL | [DeadLetterEntry](../../apps/agents/common/dead_letters.py#L24) has requested fields, but free-form status and unrestricted counters do not enforce max-three/terminal rules. | AUD-025-002, AUD-025-003 |
| T017 | [ ] | MISSING | [Exhaustion callback](../../apps/agents/common/handoffs.py#L178) never builds/persists an entry itself; [producer default](../../apps/agents/monitoring/pipeline.py#L64) only returns an ID. Optional store API is not connected to exhaustion. | AUD-025-002 |
| T018 | [ ] | PARTIAL | [Poller](../../apps/agents/common/dead_letters.py#L145) has health loop/counters, but calculated backoff is unused, first-page-only selection can starve records, and no delivery-status/transition/concurrency safeguards exist. | AUD-025-003 |
| T019 | [ ] | PARTIAL | [Startup helper](../../apps/agents/common/startup.py#L14) can start/stop an injected poller; only its definition/re-export was found, while [actual entry](../../apps/agents/dispatcher/__main__.py#L12) starts dispatcher. | AUD-025-002, AUD-025-013 |
| T020 | [ ] | CONFLICT | [Relocated list handler](../../apps/api/app/api/routes/dead_letters.py#L24) has filters/paging but uses its own dictionary and is shadowed by [earlier GET registration](../../apps/api/app/api/router.py#L73). | AUD-025-002 |
| T021 | [ ] | PARTIAL | [Manual endpoint](../../apps/api/app/api/routes/dead_letters.py#L49) increments manual attempts and returns 202/404 but never invokes or queues delivery. | AUD-025-002, AUD-025-003 |
| T022 | [ ] | PARTIAL | [Auto failure branch](../../apps/agents/common/dead_letters.py#L235) checks counters in the wrong auto/manual ordering; subsequent manual failure is unimplemented and store updates are unrestricted. | AUD-025-003 |
| T023 | [ ] | PARTIAL | [409 branch](../../apps/api/app/api/routes/dead_letters.py#L61) exists; HTTPException nests the specified object under detail, and no terminal endpoint assertion exists. | AUD-025-003 |
| T024 | [ ] | PARTIAL | [Redelivery route dependency](../../apps/api/app/api/routes/dead_letters.py#L49) is attached, but it relies on unverified production claims. | AUD-025-001 |
| T025 | [ ] | PARTIAL | Relocated [lifecycle tests](../../tests/unit/test_dead_letter_lifecycle.py#L37) cover model assignment and in-memory CRUD, not a poller, backoff, 3-auto+1-manual transition, durable audit or 409. | AUD-025-003, AUD-025-014 |
| T026 | [ ] | PARTIAL | [Benchmark](../../tests/benchmark/test_pipeline_latency.py#L24) tests the helper only; zero attempts bypass its slow case, with no 100-run full-path P95 <=5s calculation. | AUD-025-004, AUD-025-014 |
| T027 | [ ] | IMPLEMENTED | [HazardRadiusLookup and repository](../../apps/agents/risk_assessment/hazard_radius.py#L34) provide specified fields and injectable Cosmos operations; production wiring is T029/T033/T035 work. | AUD-025-005 |
| T028 | [ ] | IMPLEMENTED | [NamedLocation and repository](../../apps/agents/risk_assessment/named_locations.py#L17) provide requested fields and Cosmos lookup by location_id. No claim of population/deployment is made. | AUD-025-005 |
| T029 | [ ] | PARTIAL | [Radius CRUD/seed](../../apps/agents/risk_assessment/hazard_radius.py#L67) contains the 25 seed values and operations; create is read-then-upsert, storage errors become defaults, and seed/live API linkage is absent. | AUD-025-005, AUD-025-013 |
| T030 | [ ] | PARTIAL | [resolve](../../apps/agents/risk_assessment/named_locations.py#L38) returns coordinates/logs source or raises LocationResolutionError, not the specified validation boundary; no pipeline caller and storage outages look like lookup misses. | AUD-025-005 |
| T031 | [ ] | PARTIAL | [Generator](../../apps/agents/risk_assessment/hazard_map.py#L29) uses Shapely point buffer/mapping and properties but defaults missing coordinates, lacks range checks and emits a wrapper needing domain adaptation. | AUD-025-005 |
| T032 | [ ] | PARTIAL | [unary_union](../../apps/agents/risk_assessment/hazard_map.py#L61) merges geometry; one global severity replaces the required highest per-signal severity. Overlap may legitimately yield Polygon, not always MultiPolygon. | AUD-025-005, AUD-025-015 |
| T033 | [ ] | MISSING | [Assessment stage](../../apps/agents/risk_assessment/pipeline.py#L392) calls the agent and persists its result without HazardMapGenerator; [constructor](../../apps/agents/risk_assessment/agent.py#L232) leaves hazard_map unset. | AUD-025-005 |
| T034 | [ ] | MISSING | [Signal normalization](../../apps/agents/risk_assessment/pipeline.py#L256) drops top-level location IDs/coordinates; no named-location pre-processing call was found. | AUD-025-005 |
| T035 | [ ] | PARTIAL | [Relocated radius routes](../../apps/api/app/api/routes/radius_lookup.py#L65) implement CRUD shapes/statuses, but use a separate module dictionary and actual /api prefix rather than documented /api/v1. | AUD-025-005, AUD-025-013 |
| T036 | [ ] | PARTIAL | [Read/write dependencies](../../apps/api/app/api/routes/radius_lookup.py#L65) distinguish management/admin roles; underlying JWT signature verification is disabled. | AUD-025-001 |
| T037 | [ ] | PARTIAL | Relocated [hazard tests](../../tests/unit/test_hazard_map.py#L31) cover point/union/distant geometry and increasing radii, not exact metric radius, heterogeneous maximum severity, bounds or persisted domain output. | AUD-025-005, AUD-025-014 |
| T038 | [ ] | PARTIAL | Relocated [named-location tests](../../tests/unit/test_named_locations.py#L38) check coordinates and custom exception only; identifier in error, audit fields and pipeline rejection are not asserted. | AUD-025-005, AUD-025-014 |
| T039 | [ ] | PARTIAL | [Azure client branch](../../apps/agents/common/content_safety.py#L73) selects managed identity/non-local versus key/local and analyzes text; assumed SDK response fields, categorization and live wiring are unverified/incomplete. | AUD-025-006, AUD-025-013 |
| T040 | [ ] | IMPLEMENTED | [ContentSafetyResult](../../apps/agents/common/content_safety.py#L45) has normalized confidence and validation_method; helper branches implement severity/6 and binary mappings. Persistence/consumer integration is separately incomplete. | AUD-025-006 |
| T041 | [ ] | PARTIAL | [Factual validator](../../apps/agents/common/content_safety.py#L198) checks substring presence and reports binary confidence, but accepts absent source facts, misses contradictions and is not called by the pipeline. | AUD-025-006 |
| T042 | [ ] | PARTIAL | [Tone validator](../../apps/agents/common/content_safety.py#L235) checks Advice/Watch-and-Act keyword escalation; no English pre-translation caller, valid-tier enforcement or complete tier boundary coverage. | AUD-025-006 |
| T043 | [ ] | PARTIAL | Relocated [content-safety breaker](../../apps/agents/common/content_safety_circuit_breaker.py#L16) has required default fields/states; half-open grants more than one probe under concurrent callers. | AUD-025-007 |
| T044 | [ ] | PARTIAL | [Breaker logging](../../apps/agents/common/content_safety_circuit_breaker.py#L54) implements five event names/fields, but close omits zero-count fallback summary and concurrency/transition semantics lack assertions. | AUD-025-007 |
| T045 | [ ] | CONFLICT | [Fallback helper](../../apps/agents/common/content_safety.py#L163) flags results, but [pipeline persistence](../../apps/agents/communication/pipeline.py#L519) always holds review and drops flag; [ADR](../../docs/corpus/aidr/decisions/adr-f07-keyword-fallback.md#L38) mandates pre-publication review. | AUD-025-007, AUD-025-015 |
| T046 | [ ] | MISSING | [Stage 7](../../apps/agents/communication/pipeline.py#L367) invokes only validate, skips templates, and never calls factual/tone; no complete three-layer orchestration was found in bounded agent search. | AUD-025-006 |
| T047 | [ ] | MISSING | Planned Azure-specific tests are absent; [consolidated tests](../../tests/unit/test_content_safety_pipeline.py#L81) use no SDK response/credential fixtures, severity normalization or six-language Azure assertions. | AUD-025-006, AUD-025-014 |
| T048 | [ ] | PARTIAL | [Consolidated factual tests](../../tests/unit/test_content_safety_pipeline.py#L116) cover matching/missing hazard and location, not severity mismatch, confidence assertions or partial/contradictory facts. | AUD-025-006, AUD-025-014 |
| T049 | [ ] | PARTIAL | [Consolidated tone tests](../../tests/unit/test_content_safety_pipeline.py#L160) cover Advice/Emergency examples, not Watch-and-Act boundaries or English-before-translation ordering. | AUD-025-006, AUD-025-014 |
| T050 | [ ] | PARTIAL | [Breaker tests](../../tests/unit/test_content_safety_pipeline.py#L19) cover basic trip/cooldown/success/count; probe failure, all telemetry fields and concurrent single probe are untested. | AUD-025-007, AUD-025-014 |
| T051 | [ ] | MISSING | Planned integration file is absent; [existing pipeline test](../../tests/unit/test_communication_pipeline.py#L85) mocks translator and only asserts an English alert exists, not required Azure/factual/tone/fallback scenarios. | AUD-025-006, AUD-025-014 |
| T052 | [ ] | MISSING | [Existing safety scaffold](../../tests/fixtures/content_safety/en/.gitkeep) and the other five locales are empty; bounded corpus/consumer searches found no >=600-message replacement. | AUD-025-014 |
| T052b | [ ] | MISSING | No content-safety accuracy benchmark exists among enumerated benchmark files; [current pipeline benchmark](../../tests/benchmark/test_pipeline_latency.py#L24) is unrelated to per-language detection/pass rates. | AUD-025-014 |
| T053 | [ ] | IMPLEMENTED | Relocated [Content Safety module](../../infra/modules/content-safety.bicep#L27) declares AU-restricted account, system identity and endpoint/resource-ID outputs. Actual deployment, policy and resource availability remain UNVERIFIED. | AUD-025-013 |
| T054 | [ ] | CONFLICT | Relocated [transport DTO](../../apps/agents/common/handoff_payloads.py#L17) is flat and string-priority, lacking required nested requirements, capacity/dropoff Points and numeric constraints; actual [coordinator](../../apps/agents/evacuation/transport.py#L149) uses notes. | AUD-025-009 |
| T055 | [ ] | MISSING | [Evacuation completion](../../apps/agents/evacuation/pipeline.py#L302) has no Stage 9b or delivery call; bounded shared DTO/agent/workflow producer search found no equivalent. | AUD-025-009 |
| T056 | [ ] | MISSING | [Transport coordinator](../../apps/agents/evacuation/transport.py#L94) has missing-data/zero returns, not the all-ambulatory handoff skip guard and structured log. | AUD-025-009 |
| T057 | [ ] | CONFLICT | [Transport extraction](../../apps/agents/resource_allocation/pipeline.py#L313) feeds raw priority to [string normalizer](../../apps/agents/resource_allocation/priority.py#L49), not descending integer 5-first sorting. | AUD-025-009 |
| T058 | [ ] | PARTIAL | [DTO tests](../../tests/unit/test_handoff_payloads.py#L20) and [receiver test](../../tests/unit/test_resource_allocation_pipeline.py#L140) exist, but use old flat/string formats and never assert producer delivery or numeric triage. | AUD-025-009, AUD-025-014 |
| T059 | [ ] | CONFLICT | Planned contract file absent; [existing resource intake contract](../../tests/contract/test_resource_allocation_handoff.py#L33) asserts old camelCase/string fields without GeoJSON pickup/dropoff/capacity/numeric priority. | AUD-025-009, AUD-025-014 |
| T060 | [ ] | CONFLICT | [Shared dispatch DTO](../../apps/agents/common/handoff_payloads.py#L40) uses deployment_summary/resource_assignments, not required dispatch_type/typed assignments/plan_id schema. | AUD-025-010 |
| T061 | [ ] | MISSING | [Allocation post-persistence path](../../apps/agents/resource_allocation/pipeline.py#L139) has no agency grouping, priority mapping or communication sender. | AUD-025-010 |
| T062 | [ ] | MISSING | [Allocation completion](../../apps/agents/resource_allocation/pipeline.py#L146) logs plan generation, not validated per-agency dispatch or dispatch_notification_sent. | AUD-025-010 |
| T063 | [ ] | PARTIAL | [Dispatch DTO tests](../../tests/unit/test_handoff_payloads.py#L77) cover defaults; [allocation tests](../../tests/unit/test_resource_allocation_pipeline.py#L177) only inspect plans, not two agency payloads, actual dispatch or unavailable receiver. | AUD-025-010, AUD-025-014 |
| T064 | [ ] | MISSING | Planned communication handoff contract absent; [existing handoff chain test](../../tests/integration/test_handoff_chain.py#L11) uses a no-op Monitoring-to-Risk subscriber, not dispatch enum/GeoJSON/nonempty/agency checks. | AUD-025-010, AUD-025-014 |
| T065 | [ ] | CONFLICT | [Shared road DTO](../../apps/agents/common/handoff_payloads.py#L61) uses full/partial/weight_limit and required segment/zero coordinates, not road_closure/road_reopening with optional segment/Point and source_signal_id. | AUD-025-011 |
| T066 | [ ] | MISSING | [Monitoring completed processing](../../apps/agents/monitoring/pipeline.py#L379) does not classify road closure/reopening or map coordinates to road events. | AUD-025-011 |
| T067 | [ ] | MISSING | [Monitoring triage](../../apps/agents/monitoring/pipeline.py#L289) only builds risk-assessment escalation; no closure handoff to Evacuation was found. | AUD-025-011 |
| T068 | [ ] | PARTIAL | [Graph methods](../../apps/agents/evacuation/road_network.py#L196) exist; [Evacuation intake](../../apps/agents/evacuation/pipeline.py#L383) follows assessment planning, not segment/nearest-edge closure/reopening handling. | AUD-025-011 |
| T069 | [ ] | MISSING | [Graph application](../../apps/agents/evacuation/pipeline.py#L602) has no originating-signal modification event; scoped agent search found no road_network_modified emission. | AUD-025-011 |
| T070 | [ ] | PARTIAL | Relocated [road-network tests](../../tests/unit/test_evacuation_road_network.py#L175) assert direct close/reopen, not handoff-driven rerouting, no-route pair output or source-signal audit. | AUD-025-011, AUD-025-014 |
| T071 | [ ] | PARTIAL | [IoT model](../../apps/agents/monitoring/iot_adapter.py#L21) has all named fields but defaults most supposedly required telemetry data and location instead of enforcing valid canonical input. | AUD-025-012 |
| T072 | [ ] | CONFLICT | [normalise](../../apps/agents/monitoring/iot_adapter.py#L121) returns a dictionary with a different shape from the real [SignalEnvelope](../../apps/api/app/validators/signal_envelope.py#L26), not that validated model. | AUD-025-012 |
| T073 | [ ] | IMPLEMENTED | [IoT dedup](../../apps/agents/monitoring/iot_adapter.py#L35) uses composite tuple keys, an async lock, default 30-second TTL and call_later eviction; integration/acknowledgment defects are separate. | AUD-025-012 |
| T074 | [ ] | PARTIAL | [Event helper](../../apps/agents/monitoring/iot_adapter.py#L69) decodes one dictionary and returns a handshake response, but has no HTTP route/200 acknowledgment handler. | AUD-025-012 |
| T075 | [ ] | MISSING | [Monitoring path](../../apps/agents/monitoring/pipeline.py#L379) never uses the adapter; [shipped dispatcher](../../apps/agents/dispatcher/agent.py#L191) mounts no telemetry endpoint. | AUD-025-012, AUD-025-013 |
| T076 | [ ] | PARTIAL | Relocated [IoT module](../../infra/modules/iot-hub.bicep#L31) provisions Hub/topic and optional webhook; [root call](../../infra/main.bicep#L466) leaves webhook empty, so no subscription is instantiated. S1=10K/s not evidenced. | AUD-025-012, AUD-025-013 |
| T077 | [ ] | PARTIAL | [IoT tests](../../tests/unit/test_iot_adapter.py#L17) cover duplicates/device separation/handshake, but never assert 30-second expiry, canonical SignalEnvelope or actual HTTP/pipeline entry. | AUD-025-012, AUD-025-014 |
| T078 | [ ] | MISSING | Correct relocated [translator scorer](../../apps/agents/communication/translator.py#L273) remains lexical; no embedding-client caller in that path. | AUD-025-008 |
| T079 | [ ] | MISSING | [Back-translation fallback](../../apps/agents/communication/translator.py#L247) reuses original body or returns 0.5; there is no configured embedding request or embedding_fallback event for its outage. | AUD-025-008 |
| T080 | [ ] | PARTIAL | [Stage 6](../../apps/agents/communication/pipeline.py#L358) sets back_translation_flagged and audit/metrics on low scores, but exact warning metadata/actual alert ID and complete semantic coverage are absent. | AUD-025-008 |
| T081 | [ ] | PARTIAL | Relocated [quality tests](../../tests/unit/test_translation_quality.py#L17) reimplement cosine locally; [translator tests](../../tests/unit/test_communication_translator.py#L12) assert lexical behavior, not a mocked embedding client, outage log or pipeline review flag. | AUD-025-008, AUD-025-014 |
| T082 | [ ] | MISSING | [Translation scaffold](../../tests/fixtures/translation_quality/en/.gitkeep) and five other locales contain no pairs; bounded data-file search found no >=180-pair corpus replacement. | AUD-025-014 |
| T083 | [ ] | PARTIAL | [Root module references](../../infra/main.bicep#L453) exist for relocated resources and AU location; no caller identity, webhook, diagnostics or endpoint injection connects their behavior. | AUD-025-013 |
| T084 | [ ] | PARTIAL | Existing [dev](../../infra/main.parameters.dev.json#L4), [staging](../../infra/main.parameters.staging.json#L4), [production](../../infra/main.parameters.production.json#L4) profiles cover location but omit new service configuration. Historical development filename is relocated, not wholly absent. | AUD-025-013, AUD-025-015 |
| T085 | [ ] | UNVERIFIED | [Original execution task](tasks.md) requires full suite success; [CI selection](../../.github/workflows/ci.yml#L131) omits root unit tests and no attributable spec-025 full-sweep result was inspected. Nothing executed here. | AUD-025-014 |
| T086 | [ ] | UNVERIFIED | [Quickstart](quickstart.md#L6) has outdated Python requirement, historical filenames and unconnected deployment settings; no attributable replay of its 13 commands/install/env/deployment recipe. | AUD-025-013, AUD-025-014, AUD-025-015 |
| T087 | [ ] | MISSING | [Required F02 decision](spec.md#L262) concerns collection/triage, while relocated [ADR-F02](../../docs/corpus/aidr/decisions/adr-f02-async-bridge.md#L9) concerns retries. Bounded decision-register search found no equivalent collection-boundary ADR. | AUD-025-015 |
| T088 | [ ] | PARTIAL | [Keyword fallback ADR](../../docs/corpus/aidr/decisions/adr-f07-keyword-fallback.md#L38) and [HITL delegation ADR](../../docs/corpus/aidr/decisions/adr-033-03-hitl-spec-008-delegation.md#L9) support approval rationale, but do not explicitly record this spec's dismissed autonomy claim; FR-009 still conflicts. | AUD-025-007, AUD-025-015 |

## Edge Cases and Unnumbered Obligations

EC-01..EC-05, ASM-L01..ASM-L07 and NFR-L01..NFR-L08 are **report-local labels** for unnumbered source
bullets/plan constraints, not additions to the original specification. Source obligation counts are
kept separate from the 23 FRs and 9 SCs.

| Edge case | Status | Expected handling and inspected evidence | Follow-up |
| --- | --- | --- | --- |
| EC-01 | PARTIAL | [Missing coordinates](spec.md#L140): [named lookup](../../apps/agents/risk_assessment/named_locations.py#L38) exists but is not called; [generator](../../apps/agents/risk_assessment/hazard_map.py#L50) and [IoT adapter](../../apps/agents/monitoring/iot_adapter.py#L135) default to zero instead of resolve/reject. | AUD-025-005, AUD-025-012 |
| EC-02 | PARTIAL | [All downstream agents unavailable](spec.md#L141): [async retries](../../apps/agents/common/handoffs.py#L124) exist, but callbacks do not persist and [poller](../../apps/agents/common/dead_letters.py#L196) has sequential first-page recovery without actual backoff. | AUD-025-002, AUD-025-003, AUD-025-004 |
| EC-03 | MISSING | [IoT exceeds pipeline capacity without signal loss](spec.md#L142): [adapter](../../apps/agents/monitoring/iot_adapter.py#L121) returns a dictionary without queue/backpressure/acknowledgment coordination; conditional [subscription](../../infra/modules/iot-hub.bicep#L81) is not enabled. | AUD-025-012, AUD-025-013 |
| EC-04 | PARTIAL | [Authorized false-positive override](spec.md#L143): an [approval endpoint](../../apps/agents/communication/agent.py#L217) exists, but accepts body role/user fields and does not establish a trusted safety-override/retraction path; validation metadata is not persisted. | AUD-025-001, AUD-025-006, AUD-025-007 |
| EC-05 | MISSING | [Closure after routes dispatched](spec.md#L144): [replan entry](../../apps/agents/evacuation/agent.py#L190) has placeholder graph/route/persistence steps and an event without a new plan; no affected-zone update delivery. | AUD-025-010, AUD-025-011 |

| Assumption | Status | Inspected evidence and assessment | Follow-up |
| --- | --- | --- | --- |
| ASM-L01 | PARTIAL | [Existing HazardMap sufficient](spec.md#L225): [domain model](../../packages/domain/src/domain/models/hazard_assessment.py#L7) exists, but numeric severity/Feature output requires an explicit compatible adapter and confidence/time-horizon fields. | AUD-025-005 |
| ASM-L02 | PARTIAL | [Handoff infrastructure already functional](spec.md#L226): [retry helper](../../apps/agents/common/handoffs.py#L124) exists; unconnected delivery/persistence and old receiver schemas invalidate assuming end-to-end function. | AUD-025-002, AUD-025-009, AUD-025-010 |
| ASM-L03 | UNVERIFIED | [External Content Safety available](spec.md#L227): [module](../../infra/modules/content-safety.bicep#L27) is authored, but root omits client identity/endpoint/access wiring and no deployment evidence was established. | AUD-025-013 |
| ASM-L04 | PARTIAL | [IoT at gateway boundary](spec.md#L228): [Hub/topic](../../infra/modules/iot-hub.bicep#L31) follows the architectural boundary; normalization, subscription and pipeline connectivity remain incomplete. | AUD-025-012, AUD-025-013 |
| ASM-L05 | IMPLEMENTED | [Threshold stays 0.85](spec.md#L229): [configuration](../../apps/agents/communication/config.py#L29) defaults to 0.85 and Stage 6 uses it. Semantic suitability/accuracy is not established by preserving the constant. | AUD-025-008, AUD-025-014 |
| ASM-L06 | CONFLICT | [HITL unchanged and safety before approval](spec.md#L230) conflicts with FR-009's immediate no-approval rule; [pipeline](../../apps/agents/communication/pipeline.py#L519) and [ADR](../../docs/corpus/aidr/decisions/adr-f07-keyword-fallback.md#L38) retain review. | AUD-025-007, AUD-025-015 |
| ASM-L07 | UNVERIFIED | [1,000 signals / 10K IoT per second / 50 redeliveries](spec.md#L231): no attributable combined-scale measurement; see the three individual NFR rows below and [benchmark](../../tests/benchmark/test_pipeline_performance.py#L188). | AUD-025-004, AUD-025-012, AUD-025-014 |

| Nonfunctional constraint | Status | Inspected evidence and assessment | Follow-up |
| --- | --- | --- | --- |
| NFR-L01 | UNVERIFIED | [1,000 concurrent signals](plan.md#L20): [bridge](../../apps/agents/common/async_bridge.py#L15) blocks callers; [benchmark](../../tests/benchmark/test_pipeline_performance.py#L188) does not exercise 1,000 concurrent full-path signals. | AUD-025-004, AUD-025-014 |
| NFR-L02 | UNVERIFIED | [10K IoT messages/second](plan.md#L20): [Hub default](../../infra/modules/iot-hub.bicep#L15) is S1 capacity 1 with no sizing proof; adapter timer-per-key memory and downstream backpressure are not load-validated. | AUD-025-012, AUD-025-013, AUD-025-014 |
| NFR-L03 | UNVERIFIED | [50 concurrent redeliveries](plan.md#L20): [poller](../../apps/agents/common/dead_letters.py#L196) serially processes one default page; no bounded concurrent worker or load assertion. | AUD-025-003, AUD-025-014 |
| NFR-L04 | PARTIAL | [Azure Container Apps/Linux, existing multi-service structure](plan.md#L16): [Dockerfile](../../apps/agents/Dockerfile#L21) and [root container resource](../../infra/main.bicep#L1109) exist, but shipped runtime is a simulation dispatcher rather than these pipelines. | AUD-025-013 |
| NFR-L05 | UNVERIFIED | [AU data residency](plan.md#L19): [new modules](../../infra/modules/content-safety.bicep#L8) restrict AU regions and [profiles](../../infra/main.parameters.production.json#L4) use australiaeast; actual storage/telemetry/model transit location and approvals are not established. Limited constitutional model-endpoint carve-out is not a data-store exemption. | AUD-025-013, AUD-025-015 |
| NFR-L06 | PARTIAL | [Production managed identity/auth](plan.md#L19): [Content Safety MI branch](../../apps/agents/common/content_safety.py#L87) exists, but [root](../../infra/main.bicep#L453) supplies no service-user principal and management JWT is not verified. | AUD-025-001, AUD-025-013 |
| NFR-L07 | CONFLICT | [Interoperability/additive API contracts](plan.md#L40): [signal model](../../apps/api/app/validators/signal_envelope.py#L26), [handoff DTOs](../../apps/agents/common/handoff_payloads.py#L17), and [actual API prefix](../../apps/api/app/core/settings.py#L10) disagree with local contracts. | AUD-025-005, AUD-025-009, AUD-025-010, AUD-025-011, AUD-025-012, AUD-025-015 |
| NFR-L08 | UNVERIFIED | [Privacy/no new PII and human-reviewed output](plan.md#L42): declaration is not a privacy or security review; [auth failure](../../apps/api/app/middleware/auth.py#L62) and [agency-free dispatch](../../apps/agents/common/handoff_payloads.py#L40) need correction before asserting protected information flow. | AUD-025-001, AUD-025-007, AUD-025-010, AUD-025-015 |

## Later Persona, Hypothesis and Scope Amendments

| Original obligation | Status | Inspected evidence and assessment | Follow-up |
| --- | --- | --- | --- |
| PER-067 | UNVERIFIED | [Operational cross-reference](spec.md#L270) exists; [referenced profiles](../001-disaster-response-hub/spec.md#L169) name reviewer roles and defer concrete identities, not the [named/dated practitioner evidence](../027-spec-hardening/contracts/persona-profile.md#L16) required to establish validation. | AUD-025-015 |
| PER-068 | UNVERIFIED | [Technical actor cross-reference](spec.md#L271) exists and [actor spec](../004-actor-github-agents/spec.md#L53) describes technical roles; a catalogue is not proof of consultation or SME validation for spec 025. | AUD-025-015 |
| PER-069 | IMPLEMENTED | [PH/JP/BD placeholder](spec.md#L272) is explicit and conditional on D-009/SME validation; [decision record](../028-capstone-alignment/evidence/decision-record.md#L19) retains that deferral. No non-AU validation claimed or requested here. | None |
| HYP-023 | PARTIAL | [Falsifiable +1-band hypothesis](spec.md#L278) exists, but named double-prefixed stub is missing; [portfolio baseline](../028-capstone-alignment/evidence/rubric-baseline.md#L7) and [post snapshot](../028-capstone-alignment/evidence/rubric-postfeature.md#L3) are not per-spec measured uplift or actor-consultation evidence. Outcome UNVERIFIED. | AUD-025-015 |
| SCP-074 | IMPLEMENTED | [Country-specific deferral](spec.md#L286) names D-009, regulatory/data-sharing and QA/product calibration preconditions. [D-009 record](../028-capstone-alignment/evidence/decision-record.md#L13) does not clear them; deferred capability is not missing current scope. | None |
| SCP-075 | CONFLICT | [Constitution unchanged; tension must be RISK](spec.md#L287): immediate fallback delivery contradicts the [human review gate](../../.specify/memory/constitution.md#L285); no explicit local risk/resolution retires it. | AUD-025-007, AUD-025-015 |
| SCP-076 | PARTIAL | [Defers to 018/008 and governance arbitration](spec.md#L288) is authored; [later HITL ADR](../../docs/corpus/aidr/decisions/adr-033-03-hitl-spec-008-delegation.md#L9) preserves 008 authority but no explicit FR-009 arbitration record was found. | AUD-025-015 |
| SCP-077 | IMPLEMENTED | [Meta flag and canonical bullet](spec.md#L280) declare enabling scope per [meta contract](../028-capstone-alignment/contracts/meta-spec-flag.contract.md#L14). This removes capstone-outcome ownership, not this spec's enumerated runtime FRs. | None |
| F02 | MISSING | [Dismissed social-connector finding](spec.md#L262) still requires a collection/triage ADR. [Same-numbered ADR](../../docs/corpus/aidr/decisions/adr-f02-async-bridge.md#L9) addresses retries instead; no equivalent found in the bounded decision registers. | AUD-025-015 |
| F07 | PARTIAL | [Autonomy dismissal](spec.md#L263) is supported in principle by [HITL ADR](../../docs/corpus/aidr/decisions/adr-033-03-hitl-spec-008-delegation.md#L9), but its explicit dismissal trace and FR-009 resolution are missing. | AUD-025-007, AUD-025-015 |

## Research and Clarification Coverage

Every research decision and all 20 session clarifications were read. Explicit replacement is credited
only where a cited later local text says what changes; none of the original tasks is marked SUPERSEDED.

| Research decision | Status | Evidence, amendment handling and assessment | Follow-up |
| --- | --- | --- | --- |
| R1 | PARTIAL | [Async/gather decision](research.md#L6): leaf async conversion exists, [pipeline](../../apps/agents/risk_assessment/pipeline.py#L575) uses sequential bridge calls. [ADR-F02](../../docs/corpus/aidr/decisions/adr-f02-async-bridge.md#L20) records compromise, not retirement of concurrency. | AUD-025-004 |
| R2 | PARTIAL | [Deterministic polygons/merge](research.md#L28) implemented only in [helper](../../apps/agents/risk_assessment/hazard_map.py#L29). R2's static string-key radius-table aspect is SUPERSEDED explicitly by [R12](research.md#L240), not the polygon obligation. | AUD-025-005 |
| R3 | PARTIAL | [Azure primary/keywords fallback](research.md#L55): [client](../../apps/agents/common/content_safety.py#L73) and [AU module](../../infra/modules/content-safety.bicep#L27) exist, but runtime integration/locale accuracy is not complete. | AUD-025-006, AUD-025-013 |
| R4 | CONFLICT | [Transport Stage 9b](research.md#L71) absent at [producer](../../apps/agents/evacuation/pipeline.py#L302). Its string-priority example is explicitly replaced by [R16](research.md#L340), not retained as the authoritative wire type. | AUD-025-009 |
| R5 | MISSING | [Per-agency communication handoff](research.md#L101): [allocation completion](../../apps/agents/resource_allocation/pipeline.py#L139) has no sender and communication lacks dispatch consumption. | AUD-025-010 |
| R6 | PARTIAL | [Monitoring road events/spatial matching](research.md#L132): [graph primitives](../../apps/agents/evacuation/road_network.py#L196) exist but the sender/nearest-edge receiver is absent. | AUD-025-011 |
| R7 | PARTIAL | [IoT gateway/normalization/dedup](research.md#L146): [adapter](../../apps/agents/monitoring/iot_adapter.py#L69) and [Hub module](../../infra/modules/iot-hub.bicep#L31) exist; broker semantics/10K throughput/retention are not proven by declarations. | AUD-025-012, AUD-025-013 |
| R8 | MISSING | [Semantic embeddings](research.md#L162): [translator](../../apps/agents/communication/translator.py#L273) remains lexical. Existing model availability is an assumption, not a connected translation embedding call. | AUD-025-008 |
| R9 | PARTIAL | [Single-probe breaker/five events](research.md#L174): [relocated breaker](../../apps/agents/common/content_safety_circuit_breaker.py#L35) has states/events but no exclusive probe claim. | AUD-025-007 |
| R10 | PARTIAL | [Production RBAC/local key](research.md#L195): [dependency](../../apps/api/app/middleware/auth.py#L62) disables signature verification. | AUD-025-001 |
| R11 | PARTIAL | [Named-location resolution](research.md#L214): [repository](../../apps/agents/risk_assessment/named_locations.py#L38) exists but pipeline never uses it. | AUD-025-005 |
| R12 | PARTIAL | [Cosmos-backed editable radius/first-deploy seed](research.md#L238): [repository](../../apps/agents/risk_assessment/hazard_radius.py#L48) is separate from the [API dictionary](../../apps/api/app/api/routes/radius_lookup.py#L53). Explicitly supersedes R2's static table only. | AUD-025-005, AUD-025-013 |
| R13 | PARTIAL | [Unified confidence/method](research.md#L271): [helper result](../../apps/agents/common/content_safety.py#L45) has mappings, but pipeline-specific details do not carry them to persistence/consumers. | AUD-025-006, AUD-025-007 |
| R14 | PARTIAL | [Terminal state/order/audit](research.md#L293): [poller failure branch](../../apps/agents/common/dead_letters.py#L235) differs in order and lacks last_attempt_at/immutability. | AUD-025-003 |
| R15 | MISSING | [Corpus minimums](research.md#L318): [safety](../../tests/fixtures/content_safety/en/.gitkeep) and [translation](../../tests/fixtures/translation_quality/en/.gitkeep) roots contain placeholders, not labeled corpora. | AUD-025-014 |
| R16 | CONFLICT | [Integer transport priority](research.md#L338) conflicts with [receiver parser](../../apps/agents/resource_allocation/priority.py#L49). The same section's appended embedding/fallback paragraphs were also read; [translator](../../apps/agents/communication/translator.py#L273) does not implement them. | AUD-025-008, AUD-025-009 |

`CL-01..CL-20` identify the unnumbered clarification answers in source order.

| Clarification | Status | Controlling source, evidence and assessed result | Follow-up |
| --- | --- | --- | --- |
| CL-01 | PARTIAL | [Auto/manual durable recovery and backoff](spec.md#L237): [poller](../../apps/agents/common/dead_letters.py#L196) and API are not connected/scheduled. | AUD-025-002, AUD-025-003 |
| CL-02 | PARTIAL | [Hazard/severity radius table](spec.md#L238): [seeds](../../apps/agents/risk_assessment/hazard_radius.py#L17) use later R12's explicit values; explanatory examples here are not the final seed data. | AUD-025-005 |
| CL-03 | PARTIAL | [No automatic throttle/manual pause](spec.md#L239): [pipeline](../../apps/agents/communication/pipeline.py#L519) always holds review; no connected manual fallback pause control was found. | AUD-025-007 |
| CL-04 | MISSING | [Direct Monitoring road handoff](spec.md#L240): [triage](../../apps/agents/monitoring/pipeline.py#L289) only produces risk escalation. | AUD-025-011 |
| CL-05 | MISSING | [Embedding similarity, model unspecified](spec.md#L241): [production scorer](../../apps/agents/communication/translator.py#L273) remains word-frequency based; the suggested research model is not a reason to require a different model arbitrarily. | AUD-025-008 |
| CL-06 | CONFLICT | [Immediate fallback and retroactive retraction](spec.md#L242) conflicts with [accepted fallback ADR](../../docs/corpus/aidr/decisions/adr-f07-keyword-fallback.md#L38) and constitutional pre-publication review. | AUD-025-007, AUD-025-015 |
| CL-07 | PARTIAL | [Read-only permanent failure](spec.md#L243): [store](../../apps/agents/common/dead_letters.py#L133) permits overwrites and manual handler does not perform failure transition. | AUD-025-003 |
| CL-08 | PARTIAL | [MI only in production](spec.md#L244): [client branch](../../apps/agents/common/content_safety.py#L87) is authored but root does not inject the service identity/endpoint configuration. | AUD-025-006, AUD-025-013 |
| CL-09 | UNVERIFIED | [Large-scale targets](spec.md#L245): [stage benchmarks](../../tests/benchmark/test_pipeline_performance.py#L188) are not 1,000/10K/50 concurrency evidence. | AUD-025-014 |
| CL-10 | PARTIAL | [3 failures/60s/probe](spec.md#L246): [breaker](../../apps/agents/common/content_safety_circuit_breaker.py#L35) implements timing but no probe exclusivity. | AUD-025-007 |
| CL-11 | PARTIAL | [Device/sequence 30s in-memory TTL](spec.md#L247): [cache](../../apps/agents/monitoring/iot_adapter.py#L35) implemented; default sequence 0/integration/expiry testing undermine full pathway. | AUD-025-012 |
| CL-12 | UNVERIFIED | [Absolute P95 replaces old 50% claim](spec.md#L248): this is explicit retirement of that baseline-dependent formulation; [benchmark](../../tests/benchmark/test_pipeline_latency.py#L47) does not establish the new target. | AUD-025-004, AUD-025-014 |
| CL-13 | MISSING | [Tone on English before translation](spec.md#L249): [pipeline stage order](../../apps/agents/communication/pipeline.py#L122) drafts all languages first and never invokes validate_tone. | AUD-025-006, AUD-025-008 |
| CL-14 | PARTIAL | [Five Cosmos radius rows/1-5/admin edits/seed](spec.md#L250): [helper seed](../../apps/agents/risk_assessment/hazard_radius.py#L116) exists without shared API/startup wiring. | AUD-025-005, AUD-025-013 |
| CL-15 | CONFLICT | [Integer severity-aligned priority](spec.md#L251): [normalise_urgency](../../apps/agents/resource_allocation/priority.py#L49) accepts strings and does not preserve five-level ordering. | AUD-025-009 |
| CL-16 | PARTIAL | [Resolve then reject location](spec.md#L252): [repository](../../apps/agents/risk_assessment/named_locations.py#L38) exists but [generator](../../apps/agents/risk_assessment/hazard_map.py#L50) defaults absence to zero. | AUD-025-005 |
| CL-17 | PARTIAL | [RBAC middleware/local API key](spec.md#L253): [auth dependency](../../apps/api/app/middleware/auth.py#L62) exists without verified production identity. | AUD-025-001 |
| CL-18 | PARTIAL | [Full breaker telemetry](spec.md#L254): [logging](../../apps/agents/common/content_safety_circuit_breaker.py#L54) is authored; concurrent transitions and all fields/counts are not asserted. | AUD-025-007, AUD-025-014 |
| CL-19 | PARTIAL | [Normalized 0-1 score](spec.md#L255): [common result](../../apps/agents/common/content_safety.py#L45) implements mapping, but stored communication details omit normalized layer outputs. | AUD-025-006 |
| CL-20 | MISSING | [Sized six-category/multilingual corpora](spec.md#L256): [existing fixtures](../../tests/fixtures/content_safety/en/.gitkeep) are scaffolds; no labeled corpus/consumer found in the bounded search. | AUD-025-014 |

## Data Model Coverage

All 12 top-level data-model entries, both nested payload entities, and the additional SignalEnvelope
and DispatchNotification entities from the spec are assessed below. Relationships and state transitions
are assessed as behavior, not merely as fields that can be assigned.

| Entity | Status | Evidence and assessed contract | Follow-up |
| --- | --- | --- | --- |
| DM-01 AgentHandoffEvent | PARTIAL | [No-schema-change input](data-model.md#L8), [existing model](../../apps/agents/common/handoffs.py#L26): envelope/tenant fields preserved, but statuses are unconstrained and durable delivery lifecycle incomplete. | AUD-025-002, AUD-025-003 |
| DM-02 ContentSafetyResult | PARTIAL | [Extended result](data-model.md#L17), [helper dataclass](../../apps/agents/common/content_safety.py#L45): confidence/method/review_flag exist, but persisted [ContentSafetyDetail](../../apps/agents/communication/models.py#L167) omits those fields. | AUD-025-006, AUD-025-007 |
| DM-03 HazardAssessment | PARTIAL | [Populate existing field](data-model.md#L37), [constructor](../../apps/agents/risk_assessment/agent.py#L232): map remains optional and unpopulated. | AUD-025-005 |
| DM-04 HazardMap | CONFLICT | [Geometry/WGS84/highest severity](data-model.md#L42), [domain model](../../packages/domain/src/domain/models/hazard_assessment.py#L7) requires string severity/confidence/time horizon; [generator](../../apps/agents/risk_assessment/hazard_map.py#L64) emits integer-severity Feature and lacks bounded coordinates/heterogeneous severity. | AUD-025-005 |
| DM-05 HazardRadiusLookup | PARTIAL | [Cosmos/seed/update contract](data-model.md#L57), [repository](../../apps/agents/risk_assessment/hazard_radius.py#L34): model and 25 values exist, API/storage wiring/validation/concurrent create incomplete. | AUD-025-005 |
| DM-06 TransportHandoffPayload | CONFLICT | [Nonempty requirements/plan/zones](data-model.md#L91) differ from [flat shared DTO](../../apps/agents/common/handoff_payloads.py#L17). | AUD-025-009 |
| DM-07 TransportRequirement | CONFLICT | [Positive counts, both Points, int priority](data-model.md#L102): [actual coordinator](../../apps/agents/evacuation/transport.py#L140) stores contextual fields in notes and [receiver](../../apps/agents/resource_allocation/pipeline.py#L313) expects old keys. | AUD-025-009 |
| DM-08 NamedLocation | PARTIAL | [WGS84 lookup](data-model.md#L114), [repository](../../apps/agents/risk_assessment/named_locations.py#L17): fields/lookup/log exist, but no pipeline resolution or validation boundary; storage errors collapse to absence. | AUD-025-005 |
| DM-09 ContentSafetyCircuitBreaker | PARTIAL | [State machine](data-model.md#L130), [relocated implementation](../../apps/agents/common/content_safety_circuit_breaker.py#L16): fields/defaults exist, half-open concurrency is not exclusive. | AUD-025-007 |
| DM-10 DeadLetterEntry | PARTIAL | [Terminal/audit contract](data-model.md#L146), [model/store](../../apps/agents/common/dead_letters.py#L24): fields exist without enforced state/count bounds, ordered recovery or read-only updates. | AUD-025-003 |
| DM-11 DispatchHandoffPayload | CONFLICT | [Nonempty typed assignments/plan/incident](data-model.md#L159), [actual DTO](../../apps/agents/common/handoff_payloads.py#L40): optional untyped assignments/summary use different names and no operational_dispatch discriminant. | AUD-025-010 |
| DM-12 DispatchAssignment | MISSING | [Required agency/type/count/destination and priority mapping](data-model.md#L173): [ResourceAssignment](../../apps/agents/resource_allocation/models.py#L246) stores resource/demand IDs; no typed notification adapter enriches it from [inventory managing_org_id](../../apps/agents/resource_allocation/models.py#L280). | AUD-025-010 |
| DM-13 RoadClosureSignalPayload | CONFLICT | [Closure/reopening/optional segment/Point/source](data-model.md#L189) differs from [full/partial shared DTO](../../apps/agents/common/handoff_payloads.py#L61), which is unconnected. | AUD-025-011 |
| DM-14 IoTSignalMessage | PARTIAL | [Raw telemetry fields](data-model.md#L203), [model](../../apps/agents/monitoring/iot_adapter.py#L21): permissive defaults and zero-sequence extraction do not enforce complete valid telemetry or canonical normalization. | AUD-025-012 |
| DM-15 SignalEnvelope | CONFLICT | [Spec normalized signal](spec.md#L202), [actual canonical validator](../../apps/api/app/validators/signal_envelope.py#L26): adapter output cannot satisfy required nested source/times/scores/status/location. | AUD-025-012 |
| DM-16 DispatchNotification | MISSING | [Spec outbound assignment entity](spec.md#L206), [allocation completion](../../apps/agents/resource_allocation/pipeline.py#L139): no producer/consumer delivers agency-scoped notification content. | AUD-025-010 |

The [relationship diagram and three state-transition sections](data-model.md#L224) are only partially
realized: signal-to-map and transport/dispatch/road/IoT connections have the findings above; terminal
dead-letter immutability is absent; content safety uses `passed/failed_with_fallback` plus method/flag
instead of preserving the documented unavailable state; direct graph `open/closed` mutation is supported
but signal-driven transitions are not. No blanket SUPERSEDED inference is applied to these relationships.

## API Contract Coverage

The contract overview's "one new endpoint" summary is stale relative to its later sections. All 15
substantive clauses below were assessed. The root uses `/api`, whereas the local contract repeatedly
specifies `/api/v1`; a compatibility decision is required instead of silently renaming live endpoints.

| Clause | Status | Inspected evidence and assessed contract | Follow-up |
| --- | --- | --- | --- |
| CT-01 / 1a transport | CONFLICT | [Contract](contracts/openapi-delta.md#L14): [sender completion](../../apps/agents/evacuation/pipeline.py#L302) missing, [receiver](../../apps/agents/resource_allocation/pipeline.py#L313) has incompatible payload/priority. | AUD-025-009 |
| CT-02 / 1b dispatch | CONFLICT | [Contract](contracts/openapi-delta.md#L49): [DTO](../../apps/agents/common/handoff_payloads.py#L40) and [communication retrieval](../../apps/agents/communication/pipeline.py#L225) omit required typed agency assignments. | AUD-025-010 |
| CT-03 / 1c road | CONFLICT | [Contract](contracts/openapi-delta.md#L85): [DTO](../../apps/agents/common/handoff_payloads.py#L61) has different closure types; no sender/receiver registration. | AUD-025-011 |
| CT-04 / 2a IoT | CONFLICT | [Envelope example](contracts/openapi-delta.md#L117) omits required sequence; [parser](../../apps/agents/monitoring/iot_adapter.py#L94) defaults zero and returns a noncanonical envelope without HTTP handling. | AUD-025-012, AUD-025-015 |
| CT-05 / 2b Content Safety | PARTIAL | [Analyze request/response](contracts/openapi-delta.md#L149): [client](../../apps/agents/common/content_safety.py#L135) sends text and normalizes severity, but actual SDK response shape/transport and full pipeline layers are unverified/incomplete. | AUD-025-006 |
| CT-06 / 3a dead-letter GET | CONFLICT | [Filters/schema/pagination](contracts/openapi-delta.md#L168): [older GET](../../apps/api/app/api/dead_letters.py#L20) wins registration and returns another store/schema with no target/status filter. | AUD-025-002 |
| CT-07 / 3b manual redelivery | PARTIAL | [202/404 contract](contracts/openapi-delta.md#L202): [handler](../../apps/api/app/api/routes/dead_letters.py#L54) updates a dictionary only and does not deliver. | AUD-025-002, AUD-025-003 |
| CT-08 / 4a radius list | PARTIAL | [Read/role contract](contracts/openapi-delta.md#L222): [handler](../../apps/api/app/api/routes/radius_lookup.py#L65) lists a local table under weak JWT auth. | AUD-025-001, AUD-025-005 |
| CT-09 / 4b radius get | PARTIAL | [Single/404 contract](contracts/openapi-delta.md#L242): [handler](../../apps/api/app/api/routes/radius_lookup.py#L71) implements 404 against local dictionary, not shared agent storage. | AUD-025-001, AUD-025-005 |
| CT-10 / 4c radius update | PARTIAL | [Admin/timestamps contract](contracts/openapi-delta.md#L251): [handler](../../apps/api/app/api/routes/radius_lookup.py#L80) changes local radii/timestamp/identity with no validated shared Cosmos visibility. | AUD-025-001, AUD-025-005 |
| CT-11 / 4d radius create | PARTIAL | [201/409 contract](contracts/openapi-delta.md#L267): [handler](../../apps/api/app/api/routes/radius_lookup.py#L102) has local duplicate check but no shared persistence/strict radii validation. | AUD-025-001, AUD-025-005 |
| CT-12 / 5a terminal GET | CONFLICT | [Full audit contract](contracts/openapi-delta.md#L288): [registered old GET](../../apps/api/app/api/dead_letters.py#L20) returns older resolution records; newer fields do not establish terminal audit lifecycle. | AUD-025-002, AUD-025-003 |
| CT-13 / 5b immutable 409 | PARTIAL | [Read-only/error object](contracts/openapi-delta.md#L323): [409 branch](../../apps/api/app/api/routes/dead_letters.py#L61) exists but nests detail; store/direct worker paths lack immutable rejection. | AUD-025-003 |
| CT-14 / 6 management auth | PARTIAL | [Auth/error/audit](contracts/openapi-delta.md#L336): [dependency](../../apps/api/app/middleware/auth.py#L62) is not verified JWT auth; GET inspection falls outside its route dependencies. | AUD-025-001 |
| CT-15 / 7 unchanged public APIs | UNVERIFIED | [Compatibility promise](contracts/openapi-delta.md#L362): [router](../../apps/api/app/api/router.py#L56) retains existing signal/plan/alert surfaces, but current prefix differs and no before/after compatibility execution is available. | AUD-025-013, AUD-025-014, AUD-025-015 |

## Review and Checklist Assessment

### Original Requirements Checklist

CHK-025-01..CHK-025-16 are report-local labels in source order. Every original checklist state remains
`[x]`; the independent status assesses the claim, not whether a box is checked. An authored checklist
is credited, but no named reviewer/date/run artifact in this folder establishes execution or approval.

| Checklist item | Original state | Status | Inspected evidence and assessment | Follow-up |
| --- | --- | --- | --- | --- |
| CHK-025-01 | [x] | CONFLICT | [No implementation detail](checklists/requirements.md#L9) conflicts with [FR-007](spec.md#L166)'s SDK credential class and [FR-009](spec.md#L168)'s exact Python logging calls. | AUD-025-015 |
| CHK-025-02 | [x] | IMPLEMENTED | [User/business focus](checklists/requirements.md#L10): [eight stories](spec.md#L10) explain coordinator, owner, field leader, sensor operator and recipient value. Authorship only. | None |
| CHK-025-03 | [x] | PARTIAL | [Nontechnical audience](checklists/requirements.md#L11): story language is accessible, but [FR-009](spec.md#L168)/[FR-018](spec.md#L189) embed circuit code/cache mechanics. | AUD-025-015 |
| CHK-025-04 | [x] | IMPLEMENTED | [Mandatory sections complete](checklists/requirements.md#L12): entire [spec](spec.md) includes scenarios, edges, requirements, entities, SCs, assumptions, clarifications, dismissals and later amendments. | None |
| CHK-025-05 | [x] | IMPLEMENTED | [No unresolved marker](checklists/requirements.md#L16): full [spec](spec.md) has no bracketed NEEDS CLARIFICATION placeholder. Absence of a marker is not absence of the identified conflicts. | None |
| CHK-025-06 | [x] | CONFLICT | [Testable/unambiguous](checklists/requirements.md#L17): [sequence cap](spec.md#L153) versus T005 and [fallback delivery](spec.md#L168) versus unchanged HITL disagree. | AUD-025-004, AUD-025-007, AUD-025-015 |
| CHK-025-07 | [x] | IMPLEMENTED | [Measurable criteria](checklists/requirements.md#L18): [nine SCs](spec.md#L213) specify thresholds, timing or 100% delivery/geometry; measurement itself is UNVERIFIED. | AUD-025-014 |
| CHK-025-08 | [x] | PARTIAL | [Technology-agnostic SCs](checklists/requirements.md#L19): most outcomes are user-observable, but [SC-004](spec.md#L216) explicitly binds Azure AI category coverage. | AUD-025-015 |
| CHK-025-09 | [x] | IMPLEMENTED | [Scenarios defined](checklists/requirements.md#L20): [spec stories](spec.md#L10) provide exactly 24 numbered scenarios, all traced above. | None |
| CHK-025-10 | [x] | IMPLEMENTED | [Edges identified](checklists/requirements.md#L21): [five explicit edges](spec.md#L138) all traced above; implementation is separately incomplete. | None |
| CHK-025-11 | [x] | PARTIAL | [Bounded scope](checklists/requirements.md#L22): [SCP deferrals](spec.md#L286) and meta flag are explicit, but constitutional and communication authority conflicts remain unresolved. | AUD-025-007, AUD-025-015 |
| CHK-025-12 | [x] | IMPLEMENTED | [Dependencies/assumptions identified](checklists/requirements.md#L23): [seven assumptions](spec.md#L223), [plan context](plan.md#L10) and [task dependencies](tasks.md#L332) are authored. Their truth/readiness is not established. | AUD-025-013, AUD-025-015 |
| CHK-025-13 | [x] | PARTIAL | [Clear acceptance for every FR](checklists/requirements.md#L27): stories cover primary features, but management, recovery ordering and policy boundaries need the detailed contract reconciliation/tests above. | AUD-025-003, AUD-025-014, AUD-025-015 |
| CHK-025-14 | [x] | IMPLEMENTED | [Primary user flows](checklists/requirements.md#L28): [US1-US8](spec.md#L10) and independent tests span the eight retained findings; authored coverage is distinct from delivery. | None |
| CHK-025-15 | [x] | UNVERIFIED | [Feature meets measurable outcomes](checklists/requirements.md#L29): [helper-only benchmark](../../tests/benchmark/test_pipeline_latency.py#L47), empty corpus scaffolds and absent senders do not prove any claimed full-feature result. | AUD-025-014 |
| CHK-025-16 | [x] | CONFLICT | [No implementation leakage](checklists/requirements.md#L30): [Cosmos CRUD](spec.md#L162), [DefaultAzureCredential](spec.md#L166), and [exact log events](spec.md#L168) contradict the declaration. | AUD-025-015 |

### Plan Constitution Gates

All source states below are authored `PASS`, not attributable human approvals. `PG-01..PG-15` identify
the first table; `PD-01..PD-08` identify each post-design addition. The post-design summary says 15/15,
but its actual additions table contains eight rows; both were read, neither is execution evidence.

| Gate | Authored state | Status | Inspected evidence and assessment | Follow-up |
| --- | --- | --- | --- | --- |
| PG-01 Primacy of Life | PASS | PARTIAL | [Plan](plan.md#L28); [pipeline safety bypass](../../apps/agents/communication/pipeline.py#L380) leaves the claimed protection incomplete. | AUD-025-006, AUD-025-007 |
| PG-02 National EM principles | PASS | PARTIAL | [Plan](plan.md#L29); [radius seeds](../../apps/agents/risk_assessment/hazard_radius.py#L17) cover five types but cross-agent delivery is unconnected. | AUD-025-005, AUD-025-009, AUD-025-010 |
| PG-03 AIIMS mapping | PASS | IMPLEMENTED | [Plan mapping](plan.md#L30) and [constitutional mapping](../../.specify/memory/constitution.md#L34) explicitly align responsibilities. This credits architectural authorship, not operational validation. | AUD-025-015 |
| PG-04 Multi-hazard | PASS | PARTIAL | [Plan](plan.md#L31); [five-type repository](../../apps/agents/risk_assessment/hazard_radius.py#L17) exists but assessments never consume it. | AUD-025-005 |
| PG-05 Auditability | PASS | PARTIAL | [Plan](plan.md#L32); [helper events](../../apps/agents/common/handoffs.py#L148) exist, while durable/manual/road/auth audit gaps remain. | AUD-025-001, AUD-025-003, AUD-025-011 |
| PG-06 Warning tiers | PASS | PARTIAL | [Plan](plan.md#L33); [tone helper](../../apps/agents/common/content_safety.py#L235) is not called before translation. | AUD-025-006 |
| PG-07 Warning principles | PASS | PARTIAL | [Plan](plan.md#L34); [lexical scoring](../../apps/agents/communication/translator.py#L273) and safety bypass do not ensure accurate language/public safety. | AUD-025-006, AUD-025-008 |
| PG-08 Total Warning System | PASS | PARTIAL | [Plan](plan.md#L35); [IoT adapter](../../apps/agents/monitoring/iot_adapter.py#L139) is not connected to canonical monitoring input. | AUD-025-012 |
| PG-09 Evacuation framework | PASS | PARTIAL | [Plan](plan.md#L36); [transport computation](../../apps/agents/evacuation/transport.py#L74) exists, but handoff and road-update pathways are absent. | AUD-025-009, AUD-025-011 |
| PG-10 Azure platform | PASS | PARTIAL | [Plan](plan.md#L37); [root Azure modules](../../infra/main.bicep#L453) are authored without activation wiring or connected embeddings. | AUD-025-013 |
| PG-11 Residency | PASS | UNVERIFIED | [Plan](plan.md#L38); [AU parameter profiles](../../infra/main.parameters.production.json#L4) are static, not evidence of deployed residency, private access, telemetry handling or approvals. | AUD-025-013, AUD-025-015 |
| PG-12 Human authorization | PASS | CONFLICT | [Plan](plan.md#L39) simultaneously claims preservation and fallback no-review delivery; [constitution](../../.specify/memory/constitution.md#L285) requires prior review. | AUD-025-007, AUD-025-015 |
| PG-13 Interoperability | PASS | CONFLICT | [Plan](plan.md#L40); [IoT output](../../apps/agents/monitoring/iot_adapter.py#L139) and [handoff DTOs](../../apps/agents/common/handoff_payloads.py#L17) do not match the declared contracts. | AUD-025-009, AUD-025-010, AUD-025-011, AUD-025-012 |
| PG-14 Degradation | PASS | PARTIAL | [Plan](plan.md#L41); [poller](../../apps/agents/common/dead_letters.py#L196) and [breaker](../../apps/agents/common/content_safety_circuit_breaker.py#L35) lack required recovery guarantees. | AUD-025-003, AUD-025-007 |
| PG-15 Privacy | PASS | UNVERIFIED | [Plan](plan.md#L42) declares no new PII; no named privacy-review evidence was available, and [management auth](../../apps/api/app/middleware/auth.py#L62) is deficient. | AUD-025-001, AUD-025-015 |
| PD-01 Cosmos radius | PASS | PARTIAL | [Post-design claim](plan.md#L141); [API dictionary](../../apps/api/app/api/routes/radius_lookup.py#L53) is not the agent Cosmos repository. | AUD-025-005 |
| PD-02 Named location | PASS | PARTIAL | [Post-design claim](plan.md#L142); [resolver](../../apps/agents/risk_assessment/named_locations.py#L38) has no assessment caller. | AUD-025-005 |
| PD-03 Circuit telemetry | PASS | PARTIAL | [Post-design claim](plan.md#L143); [breaker](../../apps/agents/common/content_safety_circuit_breaker.py#L35) permits multiple probes and lacks complete telemetry assertions. | AUD-025-007 |
| PD-04 Management RBAC | PASS | PARTIAL | [Post-design claim](plan.md#L144); [auth](../../apps/api/app/middleware/auth.py#L62) does not validate signatures. | AUD-025-001 |
| PD-05 Permanent failure | PASS | PARTIAL | [Post-design claim](plan.md#L145); [store update](../../apps/agents/common/dead_letters.py#L133) is unrestricted and manual failure lifecycle absent. | AUD-025-003 |
| PD-06 Normalized score | PASS | PARTIAL | [Post-design claim](plan.md#L146); [helper result](../../apps/agents/common/content_safety.py#L45) has fields but [stored detail](../../apps/agents/communication/models.py#L167) does not propagate them. | AUD-025-006 |
| PD-07 Test corpora | PASS | MISSING | [Post-design claim](plan.md#L147); [fixture scaffold](../../tests/fixtures/content_safety/en/.gitkeep) is empty, as are the other language and translation folders. | AUD-025-014 |
| PD-08 Priority | PASS | CONFLICT | [Post-design claim](plan.md#L148); [receiver normalizer](../../apps/agents/resource_allocation/priority.py#L49) rejects the required integer representation. | AUD-025-009 |

### Phase Consultation and Checkpoint Evidence

All listed actors are intended reviewers in the original task document, not people or agents claimed
to have performed reviews in this audit. No roster was replayed; no approval was requested. The rosters,
their input/output expectations, dependency plan, MVP/incremental strategy and final metrics table were
read in full. Each phase has no attributable local consultation outputs; checkpoint prose is not a result.

| Phase obligation | Status | Required review/inspection evidence and assessment | Follow-up |
| --- | --- | --- | --- |
| RV-01 Setup | UNVERIFIED | [Roster](tasks.md#L20): solution architecture, infrastructure, QA and security must assess dependencies/fixtures/CVEs. [Manifests](../../apps/agents/pyproject.toml#L10) show declarations only; no named review/installation result. | AUD-025-013, AUD-025-014, AUD-025-015 |
| RV-02 Foundation | UNVERIFIED | [Roster](tasks.md#L38): API, principal engineer, SRE, security, compliance and data review async ordering, time budgets, identity and partitioning. [Checkpoint](tasks.md#L64) is not proof those checks passed. | AUD-025-001, AUD-025-002, AUD-025-004, AUD-025-015 |
| RV-03 Recovery | UNVERIFIED | [Roster](tasks.md#L74): data, SRE, observer, operations, chaos and API review recovery/backoff/lifecycle/API. [Lifecycle tests](../../tests/unit/test_dead_letter_lifecycle.py#L37) are CRUD-only; no claimed chaos/recovery run established. | AUD-025-003, AUD-025-014, AUD-025-015 |
| RV-04 Hazard maps | UNVERIFIED | [Roster](tasks.md#L106): risk manager, BoM, GA, planning, data, observer and local government validate radius values/spatial output/device naming. [Seeds](../../apps/agents/risk_assessment/hazard_radius.py#L17) are authored values, not practitioner approval. | AUD-025-005, AUD-025-015 |
| RV-05 Safety | UNVERIFIED | [Roster](tasks.md#L140): PIO, security, compliance, AI/ML, chaos, SRE, infrastructure, accessibility and QA review moderation/tone/languages/circuit/infra/corpora. [Tests](../../tests/unit/test_content_safety_pipeline.py#L81) do not establish these reviews or multilingual accuracy. | AUD-025-006, AUD-025-007, AUD-025-014, AUD-025-015 |
| RV-06 Transport | UNVERIFIED | [Roster](tasks.md#L180): logistics, operations, transport, incident commander, health and API review vehicles/vulnerability/priority/schema. [Old receiver test](../../tests/contract/test_resource_allocation_handoff.py#L33) is not the new contract or operational approval. | AUD-025-009, AUD-025-015 |
| RV-07 Dispatch | UNVERIFIED | [Roster](tasks.md#L207): field coordination, operations, logistics, PIO, community NGOs, local government and API review agency relevance/dispatch. [DTO](../../apps/agents/common/handoff_payloads.py#L40) cannot prove stakeholder validation. | AUD-025-010, AUD-025-015 |
| RV-08 Roads | UNVERIFIED | [Roster](tasks.md#L234): operations, transport, incident commander, planning, data and state government review closures/spatial matching/replanning. [Graph tests](../../tests/unit/test_evacuation_road_network.py#L175) are not direct-signal exercise evidence. | AUD-025-011, AUD-025-015 |
| RV-09 IoT | UNVERIFIED | [Roster](tasks.md#L261): data, infrastructure, SRE, BoM, utility, container and solution architecture review gateway/throughput/sensor mapping. [Hub defaults](../../infra/modules/iot-hub.bicep#L15) do not establish 10K/s or acknowledged outage retention. | AUD-025-012, AUD-025-013, AUD-025-015 |
| RV-10 Translation | UNVERIFIED | [Roster](tasks.md#L290): AI/ML, PIO, accessibility and QA review semantic model/threshold/languages/corpus. [test-local vectors](../../tests/unit/test_translation_quality.py#L17) are not model or native-language review evidence. | AUD-025-008, AUD-025-014, AUD-025-015 |
| RV-11 Polish | UNVERIFIED | [Roster](tasks.md#L312): infrastructure, observer, QA, compliance, incident commander, container and speckit.analyze review integrated deployment/ADRs/regressions. [Final checkpoint](tasks.md#L328) and [checklist](checklists/requirements.md#L29) are authored claims, not execution/sign-off. | AUD-025-013, AUD-025-014, AUD-025-015 |

Foundation-first ordering, the eight post-foundation parallel story lanes, intra-story model-to-service-to-
pipeline-to-API-to-test ordering, and polish prerequisites are all stated in [Dependencies](tasks.md#L332).
No chronological record establishes that those gates occurred. In particular US5 agency delivery depends
on usable US4 transport priority and communication contracts even if tasks are scheduled in parallel.
Static files do not demonstrate the MVP or final checkpoints; no actor-consultation checkbox is invented.

### Quickstart Command Coverage

All 13 feature commands were inspected as text, plus both contract commands and the two broader suite
commands. Original non-existent paths below are historical recipe targets, not proposed evidence.

| Recipe command | Status | Existing test home and what it actually establishes | Follow-up |
| --- | --- | --- | --- |
| QS-01 async_handoff_retry | PARTIAL | [Existing file](../../tests/unit/test_async_handoff_retry.py#L38): helper assertions, missing concurrency/elapsed/full telemetry checks. | AUD-025-004, AUD-025-014 |
| QS-02 hazard_map_generation | PARTIAL | Relocated to [test_hazard_map.py](../../tests/unit/test_hazard_map.py#L31): helper geometry, not pipeline map. | AUD-025-005, AUD-025-015 |
| QS-03 content_safety_azure | MISSING | No equivalent SDK-backed assertion in [consolidated tests](../../tests/unit/test_content_safety_pipeline.py#L81); the historical dedicated file is absent. | AUD-025-006, AUD-025-014 |
| QS-04 content_safety_factual | PARTIAL | Relocated [factual tests](../../tests/unit/test_content_safety_pipeline.py#L116) have a limited direct-helper set. | AUD-025-006, AUD-025-015 |
| QS-05 content_safety_tone | PARTIAL | Relocated [tone tests](../../tests/unit/test_content_safety_pipeline.py#L160) omit Watch-and-Act/order assertions. | AUD-025-006, AUD-025-015 |
| QS-06 circuit_breaker | PARTIAL | Relocated [safety breaker tests](../../tests/unit/test_content_safety_pipeline.py#L19) differ from the separate LLM breaker test homes. | AUD-025-007, AUD-025-015 |
| QS-07 evacuation_transport_handoff | PARTIAL | [Shared DTO tests](../../tests/unit/test_handoff_payloads.py#L20) and [transport calculation](../../tests/unit/test_evacuation_transport.py#L1) do not prove handoff delivery. | AUD-025-009, AUD-025-015 |
| QS-08 resource_dispatch_handoff | PARTIAL | [Dispatch DTO tests](../../tests/unit/test_handoff_payloads.py#L77) assert defaults, not agency notification. | AUD-025-010, AUD-025-015 |
| QS-09 road_network_dynamic | PARTIAL | [Road graph tests](../../tests/unit/test_evacuation_road_network.py#L175) mutate helpers directly; no Monitoring handler. | AUD-025-011, AUD-025-015 |
| QS-10 iot_adapter | PARTIAL | [Existing IoT tests](../../tests/unit/test_iot_adapter.py#L52) use the adapter's incompatible dictionary shape and omit TTL expiry. | AUD-025-012, AUD-025-014 |
| QS-11 translation_embedding | PARTIAL | Relocated [quality tests](../../tests/unit/test_translation_quality.py#L17) are a test-local cosine implementation; [translator tests](../../tests/unit/test_communication_translator.py#L12) remain lexical. | AUD-025-008, AUD-025-015 |
| QS-12 dead_letter_redelivery | PARTIAL | Relocated [lifecycle tests](../../tests/unit/test_dead_letter_lifecycle.py#L37) do not exercise the poller/manual receiver/terminal state. | AUD-025-003, AUD-025-015 |
| QS-13 named_location_lookup | PARTIAL | Relocated [lookup tests](../../tests/unit/test_named_locations.py#L38) assert local coordinates/error type, not pipeline/audit. | AUD-025-005, AUD-025-015 |

The two historical handoff contract commands have no equivalent new-contract test; existing
[resource intake contract](../../tests/contract/test_resource_allocation_handoff.py#L33) checks the old
format and [bus-chain test](../../tests/integration/test_handoff_chain.py#L11) uses a no-op subscriber.
The broad `-k` expression also misses renamed tests such as named_locations/translation_quality unless
their selected test names happen to match. [Quickstart prerequisites](quickstart.md#L6) say Python 3.11+
while both package manifests require 3.12+, and its development parameter filename is now dev. The
dependency, environment, deployment and all test commands remain unexecuted/UNVERIFIED (T086).

### Applied Review Instructions

The [repository review instruction](../../.github/instructions/code-review.instructions.md#L1) and its
[detailed checklist](../../.github/instructions/references/code-review-checklists.md#L1) were applied to
the scoped surfaces only. This is not a repository-wide security, performance or style certification.

| Review area | Status | Coverage and limit | Follow-up |
| --- | --- | --- | --- |
| Code quality/error handling | PARTIAL | Names/models are readable; ignored persistence exceptions, placeholder replan work, duplicated stores and unconnected helpers are evidenced above. No unrelated stylistic cleanup requested. | AUD-025-002, AUD-025-005, AUD-025-011 |
| Security/input/auth/cryptography | PARTIAL | JWT signatures/roles, admin writes, canonical message input, source identity, tenant/agency routing and secret placeholders reviewed. Parameterized Cosmos filter values are credited. External CVE/installed dependency checks and deployed security remain UNVERIFIED. | AUD-025-001, AUD-025-010, AUD-025-012, AUD-025-013 |
| Assertions/determinism/independence | PARTIAL | Test-local algorithms, mocked decision points, helper-only coverage, persistent fixture state/dedup, absent negative cases and CI collection were inspected. No tests ran. | AUD-025-014 |
| Performance/resources | PARTIAL | Synchronous I/O/bridges, serial first-page polling, unused backoff, timer-per-key dedup and benchmark bypasses were examined; no latency, memory or RU measurement performed. | AUD-025-003, AUD-025-004, AUD-025-012, AUD-025-014 |
| Architecture/boundaries | PARTIAL | Actual dispatcher, legacy callers, MAF facades/executors, stores and receivers traced; no blanket migration retirement assumed. Dependency/compatibility fixes are specified at controlling owners. | AUD-025-009, AUD-025-010, AUD-025-013 |
| Documentation/reviews/IaC | PARTIAL | All local docs, amendments, checklist gates, actor rosters, existing ADRs and relevant Bicep instructions read. API/recipe/authority drift identified; no policy/resource discovery, AVM lookup, Bicep build or external approval occurred. | AUD-025-013, AUD-025-015 |

### 2026-09-18 Implementation Pass

This pass was performed as an isolated context for spec 025 only. Three parallel technical reviews examined management
identity, dead-letter reliability, and agent safety handoffs. The source-completable terminal-state gap was narrowed:
the redelivery poller now returns immediately for `permanently_failed` entries, including when invoked directly outside
its status-filtered query path. A focused regression test confirms no receiver callback or attempt counter mutation.

Validation: `python -m pytest tests/unit/test_dead_letter_lifecycle.py -q` returned `8 passed`.

Remaining open work includes verified production identity/JWKS, durable dead-letter/API unification, full terminal
immutability under aliased stores, retry/backoff timing, transport/dispatch handoffs, hazard geometry, content-safety
provider evidence, road adaptation, CI gates, deployment, performance, and human review.
