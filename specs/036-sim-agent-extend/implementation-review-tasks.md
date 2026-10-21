# Implementation Review: 036-sim-agent-extend

## Review Metadata

- Review date: 2026-09-14.
- Reviewed source revision: `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a`, confirmed with read-only `git rev-parse HEAD`.
- Scope: this specification only; controlling shared implementation is inspected only where this specification depends on it.
- Existing report: absent on the initial read; no prior report content was replaced.
- Contract: [Review Contract](../001-spec-implementation-audit/README.md#L1).
- Method: independent static source, test-assertion, configuration, and recorded-document inspection. No product execution, model calls, deployments, external approvals, or runtime measurements.
- Write boundary: this report only. Original specifications, tasks, checklists, evidence, source, configuration, and audit index are unchanged.
- Status: COMPLETE independent static audit. This is not implementation acceptance, a passing product-test result, or production approval.

**Coverage:** 289 original tasks; 73 functional requirements; 14 success criteria; 54 story scenarios; 59 explicit amendment acceptance clauses; 576 checklist items; 5 adapter review items; 2 quoted specification checkbox alternatives; 37 final-sweep gates; 26 unique open follow-ups.

**Assessment:** Preserve the useful models, canonical data, adapter scaffolding, normalization tests and Cycle 4/5 documentary fixes. The active extension still has source-backed authorization, simulation-egress, operational-agent, telemetry-consumption, lifecycle, audit, map, and release-gate gaps. No measured success criterion, deployed protection or human approval is certified by this static review.

## Evidence Rules

`IMPLEMENTED` means inspected source satisfies the stated scoped obligation, not that it ran successfully. `PARTIAL` means a named part exists but an obligation is missing or contradicted. `MISSING` is used only after the bounded replacement/caller searches described here. `CONFLICT` identifies unresolved competing contracts. `UNVERIFIED` covers execution, measurements, deployment, and approval without attributable evidence. `SUPERSEDED` requires an explicit cited replacement and does not erase an original task.

Independent review-only contexts read the complete local inputs and inspected bounded source slices; none was authorised to write or delegate. An initial incomplete handoff was rejected and replaced by complete, bounded reads. No other implementation-review report was read. All recommendations below are future work, not authorisation to execute them during this audit.

### Controlling Paths and Bounded Searches

- API registration: [router](../../apps/api/app/api/router.py#L68) mounts the legacy simulation, spec-036, playback, and chat routers. The application [middleware composition](../../apps/api/app/main.py#L24) contains no spec-036 idempotency middleware.
- Chat: [mounted chat controller](../../apps/api/app/api/routes/simulation_chat.py#L45) uses the production invoker; [tool execution](../../apps/api/app/services/simulation/controller_service.py#L927) is the controlling branch. The registered injection/pause/resume tool names have no matching execution branches. Searches covered controller tools/service, simulation routes, turn-barrier/cascade helpers, and their callers in API/agents/packages.
- Injection: [REST route](../../apps/api/app/api/routes/simulations_036.py#L176) calls the injection handler then [factory](../../apps/api/app/services/simulation/signal_pipeline_factory.py#L29) and [orchestrator](../../apps/api/app/services/simulation/signal_pipeline_orchestrator.py#L234). Searches for publisher event consumers, actual subscriber calls, LLM-call registration, and idempotency repository callers covered API/agents/packages. An event publication is not subscriber consumption.
- Storage: [audit writer](../../apps/api/app/services/simulation/audit_writer.py#L251), [state repository](../../apps/api/app/services/simulation/repositories/simulation_state.py#L68), sequence/idempotency/synthetic-signal repositories, and their factories were inspected. Missing historical repository paths were resolved to current owners before assessment.
- Web: [active simulation page](../../apps/web/src/app/simulations/[tenantId]/page.tsx#L574), chat stream/parser, map reducer/component, shared map, and live-log consumers were inspected. Searches covered web application/components/hooks/lib and shared UI; fixture-supplied props are not active-page wiring.
- Release: [staging workflow](../../.github/workflows/staging-promotion.yml#L130), [gate helper](../../tests/staging_gates.py#L249), actual CD workflow, KQL, telemetry producers, root infrastructure references, and relevant test assertions/discovery were inspected. Searches covered workflows, API/agent/package event names and timestamp dimensions, both infrastructure entry points, and test homes. No KQL or infrastructure was executed.

## Impact-Ordered Findings

| Priority | Status | Finding and controlling evidence | Follow-up |
| --- | --- | --- | --- |
| P1 security | PARTIAL | Coordinator authorization compares claims with an optional header, not the simulation definition's owning tenant; omitting the header bypasses that comparison. The outcome route accepts absent roles. [Authorization](../../apps/api/app/api/dependencies/simulation_rbac.py#L227), [outcome](../../apps/api/app/api/routes/simulations_036.py#L844). | AUD-036-SIM-002 |
| P1 security | PARTIAL | Communication delivery tests a different simulation prefix from the active chat boundary; supplied SDK clients can reach its send branch. This is a conditional source defect, not evidence of a real send. [Predicate](../../apps/agents/communication/delivery.py#L66), [SDK branch](../../apps/agents/communication/delivery.py#L208). | AUD-036-SIM-003 |
| P1 correctness | PARTIAL | Six HTTP adapters exist, but their dispatcher uses short role prompts, no operational-handler invocation, and empty citations. Its degraded fallback is not represented as a structured degraded response. [Dispatcher](../../apps/agents/dispatcher/agent.py#L208), [response parser](../../apps/api/app/services/simulation/sub_agents/_base.py#L108). | AUD-036-SIM-004 |
| P1 correctness | PARTIAL | Injection is registered as a tool but has no controller execution branch. REST fan-out publishes events and records producer completion as acknowledgement, without invoking subscribed agents; utility/transport have no category bridge. [Tools](../../apps/api/app/services/simulation/controller_tools.py#L175), [execution](../../apps/api/app/services/simulation/controller_service.py#L946), [bridge](../../apps/api/app/services/simulation/signal_pipeline_orchestrator.py#L104), [publish loop](../../apps/api/app/services/simulation/signal_pipeline_orchestrator.py#L337). | AUD-036-SIM-005 |
| P1 safety | PARTIAL | The handler evaluates life safety before parsing without category/confidence, returns only one signal, and returns contradiction IDs separately; the REST route does not apply those IDs to its persisted signal. No production LLM-call registration was found; the route passes no circuit probe. [Handler](../../apps/agents/simulation_telemetry_injection/handler.py#L75), [route](../../apps/api/app/api/routes/simulations_036.py#L298). | AUD-036-SIM-006 |
| P1 safety | PARTIAL | Tuple/ladder helpers do not control controller dispatch; location-specific agency resolution and ambiguity barriers are absent from that active path. [Dispatch](../../apps/api/app/services/simulation/controller_service.py#L946), [tuple fallback](../../apps/api/app/services/simulation/jurisdiction_routing.py#L69). | AUD-036-SIM-007 |
| P1 integrity | PARTIAL | Audit allocation happens before payload validation and separate persistence, so invalid payload or create failure consumes a number. DLQ is a process buffer; unavailable Cosmos initialization falls back to memory, and several routes swallow required audit failures. [Allocation/validation](../../apps/api/app/services/simulation/audit_writer.py#L314), [DLQ](../../apps/api/app/services/simulation/audit_writer.py#L407), [factory](../../apps/api/app/services/simulation/audit_writer.py#L520). | AUD-036-SIM-008 |
| P1 reliability | PARTIAL | The idempotency repository exists but has no route/middleware caller in the searched API tree; headers are merely copied into selected audits. [Repository](../../apps/api/app/repositories/simulation_idempotency_repository.py#L287), [route](../../apps/api/app/api/routes/simulations_036.py#L226). | AUD-036-SIM-009 |
| P1 reliability | PARTIAL | Pause/resume/abort can report success after state persistence errors. Chat uses tenant slugs as simulation IDs while REST validates UUIDs and maintains a separate lifecycle document. Abort drains a registry that controller work does not register with. [Chat ID](../../apps/api/app/api/routes/simulation_chat.py#L78), [pause](../../apps/api/app/api/routes/simulations_036.py#L623), [abort](../../apps/api/app/api/routes/simulations_036.py#L527). | AUD-036-SIM-010 |
| P1 correctness | PARTIAL | Cascade hook is not called by the controller; thread cap is process-local and cap-denial cannot obtain the candidate API it calls. It logs degradation without attaching a payload to the selected thread. [Hook](../../apps/api/app/services/simulation/controller_cascade_hook.py#L49), [cap](../../apps/api/app/services/simulation/thread_cap_service.py#L94), [denial](../../apps/api/app/services/simulation/cascade_orchestrator.py#L323). | AUD-036-SIM-011 |
| P1 correctness | PARTIAL | No overlay stream is passed from the active page, and no publisher-to-feed consumer connection was found. Even supplied events are filtered to Point before map rendering. [Page](../../apps/web/src/app/simulations/[tenantId]/page.tsx#L574), [Point filter](../../apps/web/src/components/simulation-map.tsx#L219). | AUD-036-SIM-001, AUD-036-SIM-012 |
| P1 safety | PARTIAL | Communication persistence/approval bypasses the watermark helper. Active text/audio paths do not enforce curated English-first bilingual output for the expanded locale set; repeated watermark embedding can discard the message body. [Pipeline](../../apps/agents/communication/pipeline.py#L543), [embed](../../apps/api/app/services/simulation/public_warning_watermark_guard.py#L49). | AUD-036-SIM-014 |
| P1 integrity | PARTIAL | Abort claims lessons started without enqueueing; normal archive does not trigger this capture. Persisted generation bypasses the six-section builder, uses current generation time, and can report a URI after retention errors. [Abort response](../../apps/api/app/api/routes/simulations_036.py#L579), [generator](../../apps/api/app/services/simulation/lessons_capture.py#L365), [retention](../../apps/api/app/services/simulation/lessons_capture_blob_worm.py#L107). | AUD-036-SIM-015 |
| P1 release | PARTIAL | CD deploys after CI, independently of staging-promotion; the staging workflow only creates a local tag. Z1/Z2 and 200-concurrent load evidence are not consumed by the gate. [CD](../../.github/workflows/cd.yml#L19), [deploy](../../.github/workflows/cd.yml#L225), [gate selection](../../.github/workflows/staging-promotion.yml#L130). | AUD-036-SIM-016 |
| P1 release | PARTIAL | Smoke posts signal-shaped fields to a chat-text-only endpoint and defaults to a non-UUID simulation slug. Even with valid authorization it cannot meet the expected 202 contract. [Smoke](../../.github/workflows/staging-promotion.yml#L285), [request model](../../apps/api/app/api/routes/simulations_036.py#L88), [ID validator](../../apps/api/app/api/routes/simulations_036.py#L164). | AUD-036-SIM-017 |
| P1 release | PARTIAL | KQL result collation overwrites sub-agent series by model, missing Z7 percentages default to 100, and non-finite metrics are not rejected. Refusal output uses logging/optional local JSONL rather than the required durable audit transport. [Collation](../../.github/workflows/staging-promotion.yml#L157), [helper](../../tests/staging_gates.py#L283), [sink](../../tests/staging_gates.py#L144). | AUD-036-SIM-018 |
| P1 observability | PARTIAL | Current Z6/Z7 queries are improved, but their invocation-complete/client-delivered event producers were not located in the scoped application paths. The gap alert counts uncertainty events instead of missing sequence values. [Queries](../../infra/observability/sli-kql.json#L76), [alert](../../infra/bicep/modules/simulation-app-insights-alerts.bicep#L92). | AUD-036-SIM-019 |
| P1 deployment | PARTIAL | The selected root differs from the root that invokes simulation containers; the latter's Event Hubs call is commented. Missing publisher namespace selects in-memory publication. [Selected root](../../azure.yaml#L8), [alternate invocation](../../infra/bicep/main.bicep#L546), [publisher](../../apps/api/app/services/simulation/event_hub_publisher.py#L181). | AUD-036-SIM-020 |
| P1 governance | PARTIAL | NEMA throttle metadata exists but its write guard has no active simulation invocation caller. Degraded-mode signal construction has no bounded-outage/recovery consumers. [Governor](../../apps/api/app/services/resource_governor.py#L45), [mode builder](../../apps/agents/simulation_telemetry_injection/degraded_mode.py#L14). | AUD-036-SIM-021, AUD-036-SIM-022 |
| P1 governance | PARTIAL | The spec registry permits entries without tenant/deployment/evidence/mandatory approver; alternative review workflows are manual-only and read a different registry. No daily/PR marker-to-registry enforcement was found in workflows/tools/API/registry searches. [Schema](../../infra/foundry/carveout-registry.schema.json#L24), [manual workflow](../../.github/workflows/foundry-carveout-review.yml#L3). | AUD-036-SIM-026 |
| P2 accessibility | PARTIAL | Controller emits generic tool results while the dedicated UI branch expects `sub_agent.reply`. The separate accessible live-log is unmounted and uses different event names and a local locale whitelist. [Producer](../../apps/api/app/services/simulation/controller_service.py#L790), [consumer](../../apps/web/src/components/simulation-chat-pane.tsx#L515), [page](../../apps/web/src/app/simulations/[tenantId]/page.tsx#L590). | AUD-036-SIM-013 |
| P2 contract | CONFLICT | Current documents disagree on HTTP status/error schemas, trigger-source contexts, dispatch-success coexistence, and old task details. Historical PASS matrices do not cover current amendments. [OpenAPI](contracts/openapi-simulation.yaml#L209), [binding data model](data-model.md#L927), [review overlap claim](analyze-cycle2-pass2.md#L201). | AUD-036-SIM-023 |
| P2 verification | UNVERIFIED | Recorded counts, scenario outcomes, audio availability, WORM retention, external issue/ADR state, and cohort approvals lack current attributable execution or approval receipts in the inspected local evidence. [Historical sweep](final-sweep-report.md#L60), [latest close](spec.md#L6473). | AUD-036-SIM-024 |
| P2 validation | PARTIAL | The KQL validity walker precollects later `let` bindings and preserves columns removed by `summarize`/`project`; it can accept semantically out-of-scope fields despite canonical-string agreement. [Walker](../../tests/contract/test_sli_kql_runtime_validity.py#L350), [scope handling](../../tests/contract/test_sli_kql_runtime_validity.py#L625). | AUD-036-SIM-025 |

## Preserved Source-Supported Work

The real HTTP adapter registry replaced the old literal stub registrations; aliases and timeout/cancellation exception handling exist in [SubAgentInvoker](../../apps/api/app/services/simulation/sub_agent_invoker.py#L146). Canonical 16-layer taxonomy, reducer geometry construction, Advice-yellow palette, nine-name AIIMS mapping, structured dispatch statuses, per-edge UUIDs, RFC 8785 array canonicalisation, and caller-sequence rejection are useful implemented components. They do not prove active subscriber execution, visual rendering, or durable audit.

The gate helper checks ordinary numeric breaches and aggregate sample floors and constructs distinct refusal envelopes before raising. Current KQL contains staging/smoke-tenant filters, corrected model thresholds and Z7's defined deployment dimension. Cycle 5's database-scope comment assertions exist and are REQUIRED. These findings preserve supported amendment work rather than repeating defects from older amendment narratives as if they still existed.

## Source-Backed Findings

### Visual Overlay Rendering Is Incomplete

**PARTIAL, high impact.** [Amendment B](spec.md#L29) explicitly requires visual rendering of all applicable overlay geometries; the accessibility digest is supplementary. The controlling [simulation map](../../apps/web/src/components/simulation-map.tsx#L219) filters the map-bound collection to Point geometry and excludes the separately collected non-point geometries from its rendered collection. Polygon and line shapes therefore cannot reach the map through this component even when supplied as valid overlay events. Text descriptions do not satisfy the amended visual requirement.

## Open Remediation Tasks

- [ ] AUD-036-SIM-001 Render every applicable overlay geometry on the simulation map

  **Original obligations:** FR-027; T-I04, T-R04, T-R07. Expected: map-rendered closed-set layers including applicable LineString, Polygon, MultiPolygon, and directional wind representations. Actual: only Point overlays reach the map; other geometry is summarised as text. Impact: coordinators cannot inspect hazard extents or route geometry visually.

  **Developer instructions:** Update the simulation-map integration and its shared map owner to carry the canonical overlay geometry without converting areas or lines into point markers. Preserve the existing point features, accessible digest, tenant/simulation isolation, and existing map consumers. Do not change the canonical layer vocabulary or remove accessible summaries to implement the visual path.

  **Tester instructions:** Extend [non-point tests](../../apps/web/tests/unit/spec_036/simulation-map-non-point.test.tsx#L22) and [map tests](../../apps/web/tests/unit/spec_036/simulation-map.test.tsx#L1), replacing the shared-map mock for geometry assertions. Supply all 16 applicable layers, Point/LineString/Polygon/MultiPolygon, wind bearing 270 then 90, four AWS tiers plus unknown, stale/update/remove events, and empty input. Assert real layer construction and geometry/style updates, not summary text alone. Future validation: V-WEB; requires installed workspace dependencies and an isolated map SDK test boundary. Expected: exact geometry and style assertions pass without changing legacy point consumers.

  **Done criteria:** Every applicable canonical layer reaches a visual map layer, geometry updates/removals are reflected, existing point behaviour remains compatible, and accessible summaries remain available. Visual/runtime outcomes remain UNVERIFIED until separately executed and recorded.

- [ ] AUD-036-SIM-002 Authorize the simulation owner before reads writes and replay

  **Original obligations:** FR-007, FR-016, FR-049, FR-050, FR-051, FR-059; T-M01, T-M02, T-M03, T-M04, T-AA05. **Expected/actual/impact:** JWT role plus authoritative simulation membership must precede access and simulation-scoped auditing. [Coordinator authorization](../../apps/api/app/api/dependencies/simulation_rbac.py#L227) checks only an optional header; [tenant middleware](../../apps/api/app/middleware/tenant_middleware.py#L47) defaults UUID routes to live and does not reject failed membership; [outcome read](../../apps/api/app/api/routes/simulations_036.py#L844) permits absent roles. A known foreign simulation ID is not an authorization grant.

  **Developer instructions:** Resolve simulation UUID to its tenant/participants from the authoritative repository, validate the authenticated subject/app role and membership, then bind tenant context before audit/cache/storage. Guard all mutations, chat/history, recent signals, outcomes and export; permit only the documented observer read capabilities. Remove anonymous/default-role acceptance on production paths without breaking explicit test overrides. Treat client tenant/viewport headers as advisory. Keep denial audit in a security-owned scope so rejection cannot write into or reveal another tenant's exercise. Do not weaken production authentication middleware or broaden roles to make smoke tests pass.

  **Tester instructions:** Extend [RBAC integration](../../tests/integration/test_rbac_enforcement_036.py#L43) using the full middleware stack and an authoritative two-simulation fixture. Test owner coordinator, owner observer reads, observer writes, anonymous, expired/wrong-audience token, foreign UUID with absent/matching/spoofed header, non-member chat slug, and cached response after role revocation. Assert 401/403 as contracted, no signal/lifecycle/cache side effects, no foreign read, and attributable denial audit. Future validation: V-API with synthetic identities and disposable repositories; no live token required. **Done:** every entry path enforces owner membership and simulation context, including cache hits and read routes.

- [ ] AUD-036-SIM-003 Enforce simulation egress refusal at every publication and SDK boundary

  **Original obligations:** FR-035, FR-036, FR-037, FR-038, FR-040, FR-042; SC-006, SC-008; T-F03, T-F04, T-F05, T-F06, T-F07, T-F08. **Expected/actual/impact:** simulation communication must never reach a real channel and must produce a complete synthetic receipt. [Delivery predicate](../../apps/agents/communication/delivery.py#L66) differs from the active `sim-` namespace; its [SDK branch](../../apps/agents/communication/delivery.py#L208) is reachable with configured clients. [Publication](../../apps/api/app/services/public_alert_service.py#L66) lacks the simulation guard and its delivery short-circuit is not the required receipt. No real send is claimed here.

  **Developer instructions:** Reuse a single authoritative tenant-mode predicate in public publication, agent delivery, HTTP wrappers and direct SDK adapters. Refuse before invoking any SDK/network client, regardless of human approval or channel. Return the exact `[SIMULATION]` prefix followed by one ASCII space, with channel, audience, message ID, simulated timestamp and block reason; persist a typed hashed receipt. Preserve real-tenant HITL/IC/PIO/Executive approval requirements and existing real delivery behavior. Integrate Triple Zero prominence and channel-state annotations without suggesting any real emergency call was placed. This task depends on authoritative tenant binding in AUD-036-SIM-002.

  **Tester instructions:** Extend [communication delivery tests](../../tests/unit/test_communication_delivery.py#L1), [handler tests](../../tests/unit/test_communication_watermark_handler.py#L19) and the existing outbound-wrapper tests. Use raising SDK spies for SMS/email/webhook/social/voice, `sim-*` and live contexts, missing/ambiguous context, approved/unapproved warnings, retry and direct adapter calls. Assert zero simulation transport calls, complete deterministic receipt/audit, and unchanged authorised live behavior. Future validation: V-COMMS with all transports replaced by spies. **Done:** every egress boundary refuses synthetic publication with an attributable receipt; zero-egress execution evidence remains separately required.

- [ ] AUD-036-SIM-004 Connect adapters to operational agents and preserve invocation provenance

  **Original obligations:** FR-001, FR-002, FR-004, FR-005, FR-006, FR-007, FR-060; T-A05, T-B04, T-C01, T-C10. **Expected/actual/impact:** six operational agents should process tenant-scoped state, not merely adopt six short personas. [Dispatcher](../../apps/agents/dispatcher/agent.py#L208) calls a shared chat model with no operational-handler dispatch and returns empty citations; fallback text is returned without a structured degraded flag. [Adapter parsing](../../apps/api/app/services/simulation/sub_agents/_base.py#L108) can treat it as success. Named HTTP adapters alone do not meet real-agent invocation.

  **Developer instructions:** Route each adapter to the existing corresponding operational implementation inside the approved agent runtime; retain the three-app topology and existing role aliases. Propagate verified simulation tenant, jurisdiction, per-edge correlation, session/read token, prompt fingerprint and deployment identity. Persist invocation and response provenance with typed timeout/cancel/citation-violation outcomes. Preserve cancellation exceptions, use nonblocking I/O, enforce 30-second read/120-second hard budget and wire the five-second acknowledgement callback. Reject ungrounded success and wrong-tenant citations; do not fabricate deployment/prompt values when unavailable. Integrate privacy/model-host controls in AUD-036-SIM-026.

  **Tester instructions:** Extend [endpoint tests](../../apps/api/tests/test_inject_telemetry_endpoint.py#L1) and [pipeline integration](../../tests/integration/test_signal_pipeline_e2e_036.py#L75) with six operational-handler spies behind the actual dispatcher. Assert each role calls its real owner once, sees a new tenant signal, returns attributed substantive output, and persists IDs/hash. Cover 404/429/503, empty model answer, timeout, cancellation and foreign citation with exact degraded status and typed audit. Future validation: V-API with model/transport doubles, then separately authorised staging validation for real-model output. **Done:** no short-prompt-only operational substitute or falsely successful fallback remains on the connected path.

- [ ] AUD-036-SIM-005 Join controller injection subscriber consumption and same-turn deduplication

  **Original obligations:** FR-008, FR-009, FR-011, FR-012, FR-015, FR-018, FR-026, FR-067, FR-068, FR-069; T-C10, T-L01, T-L02, T-L04, T-L05, T-L06, T-L07, T-L08, T-L09, T-L10, T-AA13, T-AA14, T-AA15. **Expected/actual/impact:** injection must land before substantive calls and acknowledge actual subscribers once. [Tool registration](../../apps/api/app/services/simulation/controller_tools.py#L175) has no matching [execution branch](../../apps/api/app/services/simulation/controller_service.py#L927). [Fan-out](../../apps/api/app/services/simulation/signal_pipeline_orchestrator.py#L337) acknowledges a publish, not consumption, and omits utility/transport from its bridge. The integration [assertions](../../tests/integration/test_signal_pipeline_e2e_036.py#L100) prove only memory-backed records/nonempty lists.

  **Developer instructions:** Implement the registered tool through the same authorised injection service as REST; sequence parse, durable write, tenant event publication, subscriber acceptance and reply aggregation under the turn barrier. Invoke remaining intent targets only if not already subscribers; share one injection correlation and one per-edge UUID across response/audit/chat. Consume the canonical cascade/category targets without inventing unknown agent names. Separate durable-write failure (not an accepted injection) from post-write degraded dispatch; do not return 202 for failed persistence. Preserve all attempted subscriber statuses and stable ordering. Resolve contradictory success-event/trigger-source wording explicitly through AUD-036-SIM-023; do not silently change a public enum.

  **Tester instructions:** Extend [pipeline integration](../../tests/integration/test_signal_pipeline_e2e_036.py#L75), [round-trip cascade tests](../../tests/e2e/test_cascade_orchestrator_round_trip.py#L53), and existing degraded-dispatch/body-audit tests. Use a chat turn with telemetry plus a Risk question; assert fresh signal visible before Risk, exactly one Risk call, other intent targets once, exact sets for nine categories, shared/per-edge IDs, JCS body/audit equality. Cover partial/total subscriber failure, five-second ack timeout, persist/publish failure and duplicate transport delivery. Future validation: V-API with fake Event Hubs acknowledgements and disposable storage. **Done:** real consumption and same-turn state visibility are proven at connected boundaries, not inferred from publication.

- [ ] AUD-036-SIM-006 Apply typed safety provenance and freshness rules on every injection path

  **Original obligations:** FR-008, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-065; T-A01, T-A02, T-A03, T-C01, T-C02, T-C03, T-C04, T-C05, T-C06, T-C07, T-C08, T-C09, T-AA01, T-AA02, T-AA03, T-AA04. **Expected/actual/impact:** multi-signal parsing and post-parse category/confidence gating must preserve all provenance. [Handler](../../apps/agents/simulation_telemetry_injection/handler.py#L75) gates before category/confidence exist and returns one signal. [Signal schema](../../packages/domain/src/domain/models/synthetic_signal.py#L48) omits injecting user/source and permits absent turn correlation. Contradictions are returned outside the signal and discarded by REST. Recent-signal query failures become empty history; no registered production strict-parser or circuit probe was found.

  **Developer instructions:** Bind the existing strict structured parser through production startup; support ordered arrays of discriminated category-specific signal models, server-derived user/source/tenant/correlation/timestamps and validated GPS/category parameters. Strip only known Cosmos transport/system metadata at the repository deserialization boundary before strict domain validation; preserve user-supplied unknown-field rejection. Apply the canonical five-category low-confidence refusal rule after parsing, accept non-life-safety low confidence, and keep downstream degraded re-evaluations distinct. Load category-specific recent history on REST/controller/cascade/replay, persist contradiction IDs, and calculate stale state without rewriting immutable history. Integrate Content Safety, PII scrubbing and independent parse-attempt versus successful-injection quotas; refusal must not spend the success quota. Require hash and correct hash-source for accepted/refused/fallback attempts; truncate is not PII scrubbing for exception messages. Never infer a successful model call from fallback extraction.

  **Tester instructions:** Extend [injection endpoint tests](../../apps/api/tests/test_inject_telemetry_endpoint.py#L1), [prompt-source tests](../../tests/unit/test_audit_envelope_prompt_hash_source.py#L1) and pipeline tests. Parameterise all nine categories and three confidences; two signals from one turn; incomplete location/provenance; unknown/disabled category; contradicting concurrent signals; boundary ages; failed history read; real-action request; names/email/phone in prompt and exception. Assert no writes on life-safety-low, one success-budget charge per accepted turn, independent breaker/refusal audits, persisted source/user/shared correlation and exact hash preimages. Future validation: V-API with deterministic parser/content-safety/fake-clock fixtures. **Done:** every ingress applies the same validated, attributable contract and emits no raw PII.

- [ ] AUD-036-SIM-007 Make jurisdiction and intent resolution control operational dispatch

  **Original obligations:** FR-017, FR-018, FR-019, FR-020, FR-021, FR-022, FR-023, FR-024, FR-025; T-G01, T-G02, T-G03, T-G04, T-G05, T-G06, T-G07, T-G08, T-X01, T-X02, T-X03, T-X04, T-X05, T-X06, T-X07, T-X08. **Expected/actual/impact:** deterministic, location-aware routing must precede agency invocation. Active [controller dispatch](../../apps/api/app/services/simulation/controller_service.py#L946) bypasses the helpers. [Tuple routing](../../apps/api/app/services/simulation/jurisdiction_routing.py#L69) returns candidates for invalid hints; [ladder](../../apps/api/app/services/simulation/jurisdiction_ladder.py#L62) lacks required sim/thread inputs and can default to AU instead of clarification.

  **Developer instructions:** Resolve explicit mention, sole sim jurisdiction, server-revalidated centroid, latest hazard thread, then clarification, recording the exact step and mismatch. Consume the existing authoritative boundary dataset and tuple registry before dispatch. Add location/subclass predicates for RFS/FRNSW, CFA/FRV, SACFS/SAMFS and NT dual fire; preserve DFES/QFD/TFS, SES leads, ACT ESA-first, medical branding, support-versus-combat roles and explicit NSW escalation consent. Explicit agent intent wins only within authorised doctrinal scope; invalid hints cannot broaden fan-out. Keep unresolved cases read-only and auditable.

  **Tester instructions:** Extend [tuple integration](../../tests/integration/test_jurisdiction_routing_tuples.py#L65) and [jurisdiction tests](../../apps/api/tests/test_jurisdiction_routing.py#L1) from actual controller requests. Include all eight jurisdictions, Darwin structure/Katherine grass fire, rural/urban boundaries, ACT medical/policing, known/unknown hints, missing viewport, server/client disagreement, last-thread tie and explicit Planning. Assert exact agency set or one clarify result, no speculative calls, correct audit tuple/step and no NSW escalation without consent. Future validation: V-ROUTING with versioned static boundary fixtures and spy agents. **Done:** tuple membership fixtures are complemented by active-path location/intent decisions.

- [ ] AUD-036-SIM-008 Make audit persistence gap-free durable and fail-closed

  **Original obligations:** FR-005, FR-048, FR-049, FR-050, FR-051, FR-060, FR-065, FR-067, FR-069, FR-070; T-A06, T-A18, T-B02, T-B06, T-B09, T-B11, T-N01, T-N02, T-N03, T-N04, T-N05, T-N06, T-N07, T-N08, T-AA02, T-AA09, T-AA10, T-AA21. **Expected/actual/impact:** typed append-only audit must not lose numbers or records on failure. [Writer](../../apps/api/app/services/simulation/audit_writer.py#L314) allocates before validation/persistence; [DLQ](../../apps/api/app/services/simulation/audit_writer.py#L407) is memory-only; [factory](../../apps/api/app/services/simulation/audit_writer.py#L520) references an unresolved Cosmos-container provider and falls back on errors. Schema rejection or create failure leaves a consumed allocation. Hash-source is optional at active writes; truncating exceptions is not redaction.

  **Developer instructions:** Validate before reservation and commit sequence plus envelope atomically or via a documented recoverable single-writer/outbox protocol preserving the gap invariant across replicas and crashes. Wire the actual AU Cosmos audit and DLQ containers using managed identity; refuse production startup/operations on missing durable dependencies. Make typed audit failures propagate before claimed success/side effects where mandated; handle repair without rewriting prior envelopes. Populate immutable prompt provenance and per-edge correlations, apply real PII scrubbing, and wire historical-name migration into actual export/lessons reads. Keep DLQ `-1` outside the dense main stream and forbid caller-supplied positive sequence values.

  **Tester instructions:** Extend [writer wire-up tests](../../tests/unit/test_audit_writer_sequence_wireup_036.py#L1), [sequence repository tests](../../tests/unit/test_simulation_sequence_repository_036.py#L1), and [fail-closed tests](../../tests/unit/test_audit_sequence_fr048_fail_closed_036.py#L1). Use two writer instances sharing storage; 100 concurrent writes; invalid payload; conflict/retry exhaustion; create failure after allocation; process interruption; unavailable DLQ; legacy enum read and exception PII. Assert unique dense committed main sequence, durable attributable failed-attempt records, no fake successful response, exact hash source, and stable replay/export. Future validation: V-STORAGE using emulator/faithful conditional-write fixtures, never live audit data. **Done:** durable failure recovery and gap-free committed audit are demonstrated across the actual writer path.

- [ ] AUD-036-SIM-009 Integrate durable idempotency before lifecycle side effects

  **Original obligations:** FR-066; T-B08, T-O01, T-O02, T-O03, T-O04, T-O05, T-O06, T-O07, T-O08, T-O09, T-AA15. **Expected/actual/impact:** each authorised replay must return its original response without re-execution. The [cache](../../apps/api/app/repositories/simulation_idempotency_repository.py#L287) has no active route caller; it combines miss lookup with post-effect upsert, has no in-memory expiry, writes `sim_id` rather than the declared `/simulation_id`, and builds IDs containing route slashes. Merely adding a late call would not handle concurrent misses/crashes safely.

  **Developer instructions:** Add shared authorised lookup/reservation/commit handling to pause/resume/abort/inject before side effects, using opaque valid storage IDs and the actual partition property. Use the maintained RFC8785 implementation, non-sliding 86400-second TTL, persisted response/status/header whitelist and distributed conflict protection. Reconcile the documented post-effect crash window explicitly; do not promise exactly-once from an upsert race. Apply current body-conflict 422 and lifecycle-conflict 409 semantics, fresh RBAC before replay, cross-user audit on authorised replay, cached sequence-uncertainty503 and uncached paused-write409. Keep independent route namespaces and compatibility for old cache entries.

  **Tester instructions:** Extend [repository tests](../../tests/unit/test_simulation_idempotency_repository_036.py#L1), [JCS vectors](../../tests/contract/test_jcs_canonicalisation_036.py#L1), [fail-closed tests](../../tests/contract/test_idempotency_fail_closed_036.py#L1) through the mounted routes. Test reordered/float/Unicode bodies, mismatch, two simultaneous equal keys, same key across verbs, response-loss retry, different authorised subject, revoked role, 24-hour boundary, storage failure and pause-resume-replay. Assert one side effect, byte-identical cached response, valid partition/ID, no sliding TTL and documented conflicts. Future validation: V-STORAGE with deterministic clock and shared conditional-write storage. **Done:** all four endpoints enforce replay at the side-effect boundary, including degraded responses.

- [ ] AUD-036-SIM-010 Unify lifecycle state and register cancellable controller work

  **Original obligations:** FR-059; T-A04, T-B01, T-E01, T-E02, T-E03, T-E04, T-E05, T-E06, T-P01, T-P02, T-P03, T-P05. **Expected/actual/impact:** pause must stop new work, resume must not replay, abort must cancel active calls and persist terminal state. [Chat](../../apps/api/app/api/routes/simulation_chat.py#L78) uses tenant slug as simulation ID while REST requires UUID and separate lifecycle state. [State reads](../../apps/api/app/services/simulation/repositories/simulation_state.py#L126) classify every storage error as missing; route recovery can bootstrap and then swallow persistence errors. No controller registration with cancellation was found.

  **Developer instructions:** Resolve a canonical simulation identity and use the same versioned lifecycle document across page, chat, REST, workers and invocation dispatch. Distinguish 404 from unavailable/unauthorised storage; never bootstrap unknown or failed reads during mutation without verified ownership/existence. Enforce state before every new invocation, not just injection; persist transitions truthfully and surface ETag conflict/unavailability. Register in-flight work with cleanup, finish current pause steps only, and atomically stop new abort work. Queue lessons through AUD-036-SIM-015 and return queued/started fields truthfully. Preserve legacy tenant-route compatibility via explicit translation, not a second independent state machine.

  **Tester instructions:** Extend [lifecycle tests](../../apps/api/tests/test_lifecycle_endpoints.py#L88) and [persistence integration](../../tests/integration/test_lifecycle_state_persistence_036.py#L1) without manually registering the only task under test. Start work through chat, pause during a slow step, refuse next invocation, resume without replay, abort and observe CancelledError plus one typed cancel per edge. Cover duplicate abort, stale ETag, storage403/429/timeout, absent UUID and slug mapping. Future validation: V-API/V-STORAGE with fake tasks/clock/storage. **Done:** all active paths share durable state and truthful cancellation/transition responses.

- [ ] AUD-036-SIM-011 Connect cascades to a distributed cap and real annotation attachment

  **Original obligations:** FR-043, FR-044, FR-045, FR-046, FR-047, FR-052, FR-057, FR-068; T-D01, T-D02, T-D03, T-D04, T-D05, T-D06, T-D07, T-D08, T-D09, T-D10, T-D12, T-D13, T-Q01, T-Q02, T-Q03, T-Q04, T-Q05, T-Q06, T-Y01, T-Y02, T-Y03, T-Y04, T-Y05, T-Y06, T-AA20. **Expected/actual/impact:** canonical one-hop cascades must respect a shared five-hazard cap and attach overflow annotations. The [hook](../../apps/api/app/services/simulation/controller_cascade_hook.py#L49) is disconnected and omits cap injection; [cap](../../apps/api/app/services/simulation/thread_cap_service.py#L94) is process-local; [denial](../../apps/api/app/services/simulation/cascade_orchestrator.py#L323) calls an unavailable candidate method and only logs selected annotation metadata.

  **Developer instructions:** Invoke post-reply cascade processing from the controller/subscriber result path with verified parent correlation and state. Use canonical matrix targets, explicit evacuation alias, depth-one refusal, and distributed hazard-only acquisition/release against the canonical state. Provide actual active-thread records to the deterministic five-step ladder and persist/stream the selected annotation without allocating another hazard slot. Refuse sixth coordinator-created hazards with split-simulation guidance; never silently drop cascade targets. Fresh explicit user re-entry gets a new origin/budget, not transitive depth laundering. Preserve annotation exclusion, existing add/remove compatibility and canonical target aliases.

  **Tester instructions:** Extend [cap tests](../../tests/unit/test_cascade_thread_cap_036.py#L159), [hook tests](../../tests/integration/test_controller_cascade_hook.py#L28), and [round-trip tests](../../tests/e2e/test_cascade_orchestrator_round_trip.py#L53). Two replicas share five slots; test sixth user thread, sixth cascade, annotation-only load, release, each ladder tie/no-host edge, all five source categories, depth two and explicit fresh action. Assert exact target identities, one persisted/visible annotation, correct parent/per-edge audit, no slot leaks and deterministic chosen host. Future validation: V-ROUTING/V-STORAGE. **Done:** connected cascades enforce capacity and produce the required actual annotation artifact.

- [ ] AUD-036-SIM-012 Connect authoritative overlay publication replay and active-page state

  **Original obligations:** FR-027, FR-028, FR-029, FR-030, FR-031, FR-032, FR-033, FR-034; T-A07, T-D11, T-I01, T-I02, T-I03, T-R02; SC-010. **Expected/actual/impact:** telemetry and agent responses must update the active map, including reconnect/staleness. [Page](../../apps/web/src/app/simulations/[tenantId]/page.tsx#L574) never passes overlay events; publisher/reducer helpers have no connected feed/route. Static props cannot establish real-time delivery.

  **Developer instructions:** Connect actual signal/sub-agent mutations to the existing canonical overlay publisher, authorised SSE endpoint, state reducer and map props. Preserve complete audit geometry, monotonic per-simulation IDs, Last-Event-ID replay and authoritative initial snapshot; isolate live/other-simulation data. Implement stale/remove behavior, visible clustering, AIIMS/SIM modifiers, nonlinear TC updates and transport rerouting without changing unrelated live-map contracts. Keep visual-layer work in AUD-036-SIM-001 and actual latency instrumentation in AUD-036-SIM-019.

  **Tester instructions:** Extend [map tests](../../apps/web/tests/unit/spec_036/simulation-map.test.tsx#L1) from a mounted-page stream fixture and [publisher tests](../../apps/api/tests/test_map_overlay_publisher.py#L1). Test create/update/stale/remove/batch, malformed/unknown event, reconnect duplicates and gaps, full snapshot replacement, another tenant, large polygon/51 pins, TC category and closed-road reroute. Assert active map receives exact current geometry, original audit geometry remains unchanged and reconnect converges. Future validation: V-WEB/V-API with SSE bytes and fake clock. **Done:** the actual page consumes an authorised replayable feed and all transformation assertions pass.

- [ ] AUD-036-SIM-013 Stream attributed sub-agent progress into the accessible chat log

  **Original obligations:** FR-003, FR-004, FR-005, FR-006, FR-061, FR-064; T-I05, T-I06, T-I07, T-I08, T-V01, T-V02, T-V03, T-V04. **Expected/actual/impact:** partial output, acknowledgement, agent identity and provenance must be visible and accessible. [Controller result](../../apps/api/app/services/simulation/controller_service.py#L946) discards reply metadata; the [UI](../../apps/web/src/components/simulation-chat-pane.tsx#L515) expects an unproduced event, and [page](../../apps/web/src/app/simulations/[tenantId]/page.tsx#L590) does not mount the separate live log.

  **Developer instructions:** Define one compatible producer/consumer event contract for invocation start, partial reply, soft ack, completion/degradation and cancellation, carrying sub-agent/AIIMS/hash/correlation safely. Share the stream with the mounted polite labelled `role=log` region; keep real-time visual and screen-reader content equivalent, including empty state. Use the shared locale table and request/jurisdiction/default resolution, curated prefix and `lang`, event-ID dedup on reconnect, and cleanup on unmount. Do not expose raw prompts or duplicate every token as an assertive announcement. Preserve current generic Controller deltas and legacy tool-result consumers.

  **Tester instructions:** Extend [chat tests](../../apps/web/tests/unit/spec_036/simulation-chat-pane.test.tsx#L15) and [live-log tests](../../apps/web/__tests__/simulation-live-log.test.tsx#L56) with serialized actual Controller events through the stream parser and mounted page. Cover two interleaved agents, sub-second first event, slow ack, timeout/cancel, missing metadata, malformed event, reconnect duplicate, empty log, known/unknown/NT locales and unmount. Assert attribution/hash, stable ordering, polite live region and locale parity; add axe against the mounted surface and later separately record assistive-technology results. Future validation: V-WEB. **Done:** connected visual and accessible chat receive the same attributed progress without relying on prop-only fixtures.

- [ ] AUD-036-SIM-014 Apply curated watermarks before persistence approval and rendering

  **Original obligations:** FR-035, FR-039, FR-040, FR-058, FR-064; T-A08, T-F01, T-F02a, T-F02b, T-F03, T-F04, T-F05, T-F06, T-F07, T-F08, T-W01, T-W02, T-W03, T-W04. **Expected/actual/impact:** warning content must carry the English-first curated text/audio watermark before any stored, approved or rendered artifact. [Communication persistence](../../apps/agents/communication/pipeline.py#L543) does not call its standalone watermark handler. [Text loader](../../apps/api/app/services/simulation/watermark_text_loader.py#L18) consumes the smaller YAML instead of the expanded shared locale set; [audio](../../apps/api/app/services/simulation/audio_watermark_service.py#L98) prepends one clip, not a guaranteed bilingual pair. Repeated [embedding](../../apps/api/app/services/simulation/public_warning_watermark_guard.py#L49) loses original content.

  **Developer instructions:** Put the existing guard at the real pre-persistence/pre-approval boundary and every render/export path. Make embedding idempotent while preserving body bytes; enforce canonical English first and curated locale second, including shared jurisdiction priority and all required remote-language entries. Unknown text/audio locales fall back to the English asset with one typed missing-locale audit, never model-generated watermark translation. Bind speech catalog pointers to actual staged assets and versioned approvals, preserving original locale/content and request correlation; fail closed if the mandatory English asset is unavailable. Keep channel safety independent of watermark presence (AUD-036-SIM-003).

  **Tester instructions:** Extend [watermark handler tests](../../tests/unit/test_communication_watermark_handler.py#L19) and [locale coverage](../../tests/contract/test_watermark_locale_coverage.py#L63) through the actual pipeline. Exercise 30-plus locales, six named remote locales, known/unknown/missing asset, repeated embedding, localized content, caption/PDF/email/HTML output, and audio ordering with byte/waveform fixtures. Assert preserved body, English-first prefix, exactly one fallback audit and zero approval/persistence of unwatermarked output. Future validation: V-COMMS; asset/voice QA requires separately approved staging and human reviewers. **Done:** active text/audio consumers use the shared approved catalog and all mandatory artifacts retain the watermark.

- [ ] AUD-036-SIM-015 Queue and persist deterministic complete exercise outcomes

  **Original obligations:** FR-049, FR-054, FR-055, FR-059, FR-060; T-B05, T-E03, T-H01, T-H02, T-H03, T-H04, T-H05, T-H06, T-P04, T-S01, T-S02, T-S03, T-S04, T-S05, T-S06, T-S07, T-S08, T-S09. **Expected/actual/impact:** end/abort must queue a retriable job and persist all six ordered sections, full provenance and verifiable WORM artifacts. [Abort](../../apps/api/app/api/routes/simulations_036.py#L579) claims start without enqueue. [Persisted generation](../../apps/api/app/services/simulation/lessons_capture.py#L365) bypasses the rich builder and uses wall-clock generation time; [projection](../../apps/api/app/services/simulation/lessons_capture.py#L213) omits reply/hash/citation detail. [Retention errors](../../apps/api/app/services/simulation/lessons_capture_blob_worm.py#L107) are swallowed, and [read provider](../../apps/api/app/services/simulation/outcome_signed_url.py#L127) defaults to an empty index.

  **Developer instructions:** Enqueue the same durable lessons job from normal completion and abort, with idempotent event identity and truthful queued status. Serialize the six-section builder using full invocation responses, hashes, participant summary, chronological audit, IC decisions/approvals, refusals/degradation and coherent lessons. Derive deterministic generated metadata from pinned inputs/version; preserve byte equality on identical regeneration and append a new version when inputs change. Persist Blob retention/legal hold and Cosmos index as a recoverable transaction, expose failures and retries, bind authorised signed-URL reads/export, and do not overwrite immutable history. Preserve data classification, tenant isolation, seven-year policy and approved access duration.

  **Tester instructions:** Extend [lessons tests](../../apps/api/tests/test_lessons_capture_and_export.py#L1), [full AAR tests](../../tests/integration/test_lessons_capture_full_aar.py#L172), [outcome read](../../tests/contract/test_outcome_read_api.py#L40), and lifecycle tests through route->queue->worker->index->read. Include normal end, abort, duplicate delivery, all six sections, timeout/cancel/refusal decisions, two identical generations including generated timestamp, failed upload/index/legal hold then retry, cross-tenant read and URL expiry. Assert exact bytes/hash, full content/provenance, one logical queued job, retained source evidence and no success on retention failure. Future validation: V-LESSONS with queue/Blob/Cosmos contract doubles, then authorised WORM staging. **Done:** complete deterministic outcomes are available through the real lifecycle and authorised read path.

- [ ] AUD-036-SIM-016 Make production promotion consume the full candidate-bound staging gate

  **Original obligations:** FR-063, FR-071; SC-001, SC-010, SC-013, SC-014; T-J09, T-Z02, T-Z03, T-Z05, T-AA17, T-AA35, T-AA42. **Expected/actual/impact:** the production candidate must be blocked by missing/red/stale required staging evidence. [CD](../../.github/workflows/cd.yml#L19) deploys following CI independently of the staging workflow, whose [promote step](../../.github/workflows/staging-promotion.yml#L335) creates only a local tag. The [gate](../../.github/workflows/staging-promotion.yml#L130) omits required Z1/Z2 and load evidence.

  **Developer instructions:** Bind actual production eligibility to candidate SHA, staging environment, exact build label, evidence time and every currently required SLI/load result. Preserve current explicit Z3/Z4/Z5 warn-only treatment without silently retiring the 200-concurrent throughput requirement; reconcile FR-071 wording through AUD-036-SIM-023. Ensure deployment and remote promotion tagging are unreachable when the gate fails. Keep OIDC, protected-environment approvals and immutable evidence; neither tests that merely assert no pre-existing tag nor a post-deploy health request replaces the pre-deploy gate.

  **Tester instructions:** Extend [promotion canaries](../../tests/e2e/test_staging_promotion_gates.py#L265) to drive the actual workflow decision/adapter with fake CI artifacts and a disposable git/deployment spy. Matching green candidate passes; missing/red Z1/Z2/Z6/Z7, expired evidence, wrong SHA/environment, failed/absent load or skipped gate refuses. Assert no tag push or deploy call and one refusal artifact; operational-only warnings do not block. Future validation: V-GATES with workflow fixtures, no Azure or real repository mutation. **Done:** every production deployment path consumes the full fresh candidate-bound gate and no bypass remains.

- [ ] AUD-036-SIM-017 Generate smoke traffic that satisfies the real injection contract

  **Original obligations:** FR-072; SC-013; T-AA19, T-AA36; quality CHK117, CHK137, CHK158. **Expected/actual/impact:** staging smoke must create accepted telemetry, not merely count constructed payloads. [Workflow](../../.github/workflows/staging-promotion.yml#L285) uses a slug and signal-shaped body rejected by the UUID/chat-text [endpoint contract](../../apps/api/app/api/routes/simulations_036.py#L88).

  **Developer instructions:** Provision/select an active UUID simulation belonging to the dedicated smoke tenant and acquire the per-run OIDC bearer with the correct API audience/app role. Send valid contract requests for the five source categories, assert 202 and explicit false degraded status, and verify actual persisted/consumed signals and client delivery metrics. Guard tenant/environment before network work; never grant production-tenant access or replace OIDC with a long-lived secret. Treat forty requests as traffic, not proof of thirty samples in each required metric series. Keep replica, dataset and resource budgets bounded.

  **Tester instructions:** Extend [smoke floor tests](../../tests/e2e/test_staging_smoke_injection_floor.py#L81), [pollution tests](../../tests/integration/test_smoke_injection_no_prod_pollution.py#L24) and existing endpoint tests with captured real workflow payloads. Positive UUID/role/body creates signals; slug, schema extras, missing chat text, wrong audience/tenant, expired token, 202 degraded and non-202 all stop the job. Assert accepted category set and emitted metric dimensions, not POST-string presence. Future validation: V-SMOKE with a local ASGI fixture; real traffic only in separately approved staging. **Done:** emitted requests and observed telemetry satisfy both REST and gate contracts.

- [ ] AUD-036-SIM-018 Preserve metric series and durably audit every promotion refusal

  **Original obligations:** FR-071, FR-073; SC-013, SC-014; T-AA17, T-AA35, T-AA40, T-AA41, T-AA42. **Expected/actual/impact:** every required valid series must meet thresholds and each refusal must be durable before failure propagates. [Collation](../../.github/workflows/staging-promotion.yml#L157) overwrites sub-agent rows by model, missing Z7 values can default green, and [comparisons](../../tests/staging_gates.py#L283) permit non-finite data. [Default sink](../../tests/staging_gates.py#L144) logs/optionally writes local JSONL, not allocator-backed audit.

  **Developer instructions:** Preserve `(sub_agent, model_deployment)` dimensions through KQL collation and require explicit finite numeric metrics, valid integer counts, expected rows and fresh times. No missing field may become green default; fail with typed diagnostic before evaluating malformed input. Audit refusal through a real durable transport using UUID, helper hash, actor, workflow run, build label, breached SLIs and underages before propagating the nonzero result. Keep two concurrent refusals separate and do not log secrets/raw payloads. Preserve boundary equality and intentional warning-versus-breach bands; audit unavailability cannot authorise promotion.

  **Tester instructions:** Extend [threshold tests](../../tests/integration/test_assert_sli_thresholds_z6_z7.py#L46), [envelope tests](../../tests/unit/test_assert_sli_thresholds_envelope_writer.py#L93), and [concurrency](../../tests/integration/test_staging_promotion_concurrency.py#L66). Supply actual columns/rows with same-model Risk5500/Evac1200 in both orders, NaN/Infinity/null/bool/string metrics, missing fields, negative/fractional counts, 29/30 samples, fresh/stale/future times and store failure. Assert both row orders refuse, every malformed shape is typed/audited, one durable sequence per refusal, two distinct concurrent rows and no success marker. Future validation: V-GATES with disposable audit storage; no live KQL. **Done:** no metric is erased/defaulted green and all refusals are durably attributable.

- [ ] AUD-036-SIM-019 Instrument the real latency drift and audit-gap boundaries

  **Original obligations:** FR-003, FR-005, FR-006, FR-028, FR-029, FR-048, FR-063, FR-073; SC-001, SC-010, SC-013; T-A17, T-B12, T-J07, T-K01, T-K02, T-N03, T-N07, T-Z01, T-Z02, T-Z04, T-AA13, T-AA16, T-AA18, T-AA34. **Expected/actual/impact:** canonical queries need actual connected metric producers. Scoped application searches did not find the Z6 completion/Z7 client-receipt events or required clock dimensions. [Gap alert](../../infra/bicep/modules/simulation-app-insights-alerts.bicep#L92) counts uncertainty instead of [actual gaps](../../infra/observability/sli-kql.json#L25). [Load checker](../../tests/load/assert_locust_thresholds.py#L14) allows 5000ms and defaults absent values to zero versus the amended 3500ms obligation.

  **Developer instructions:** Emit completion and client-receipt events at the real boundaries with tenant/env/sub-agent/deployment/finite timestamps; propagate real OTel parent/child context rather than only hex strings in event metadata. Preserve sampling/cardinality/residency limits and a reliable arrival clock policy. Align alerts with committed sequence gaps, separate uncertainty/DLQ, and reconcile the load metric's parse-only versus end-to-end scope. Require nonempty 200-concurrent-run evidence, count, error percentage and 3500ms limit where contracted; malformed/no-row results fail closed. Do not manufacture event observations to fill sample floors.

  **Tester instructions:** Extend [SLI gate tests](../../tests/e2e/test_staging_promotion_gates.py#L93), [schema tests](../../tests/contract/test_sli_kql_schema_v2.py#L66) and [map SLO harness](../../tests/load/test_sc010_map_overlay_slo.py#L39). Capture exporter events from actual invocation/overlay receipt; verify all dimensions and real span relationships. Test sequences `[1,2,3]`/`[1,3]` with no uncertainty event, no samples, skewed clocks, CSV3500/3501ms, 1%/>1% errors and zero requests. Future validation: V-GATES/V-MEASURE; measurement runs need separately approved staging and pinned candidate. **Done:** query contracts correspond to observed producers and threshold/evidence failures cannot silently pass.

- [ ] AUD-036-SIM-020 Wire simulation dependencies through the selected infrastructure root

  **Original obligations:** FR-009, FR-015, FR-048, FR-051, FR-062, FR-063; T-A09, T-A10, T-A11, T-A12, T-J01, T-J02, T-J03, T-J04, T-J05, T-J06, T-J08, T-J10, T-J11, T-J12, T-J13, T-J14, T-J15, T-J16, T-J17, T-J18, T-J19, T-J20, T-J22, T-J23, T-L04, T-N01, T-N05, T-O01, T-AA18, T-AA38. **Expected/actual/impact:** source declarations must participate in the selected deployment graph. [Selected root](../../azure.yaml#L8) is not the [alternate root invoking simulation containers](../../infra/bicep/main.bicep#L546); Event Hubs are commented there and the selected API configuration does not set the required publisher namespace. Declared modules alone do not prove deployability or deployment.

  **Developer instructions:** Reconcile selected-root module composition, database/container names and partition fields, hub-name strategy, API/agent env bindings, identity role assignments and monitoring outputs. Follow AVM-first and existing governance, AU data residency, private endpoints, CMK/AAD-only, three-app cap and separated simulation/live permissions. Never enable memory fallbacks in production to hide unavailable infrastructure. The Cycle4/5 database-scoped smoke role is explicitly retained, not partition isolation; query filtering is telemetry filtering, not an authorization substitute. Do not deploy or change resource scope as part of this audit.

  **Tester instructions:** Extend [container wiring tests](../../tests/unit/test_cosmos_simulation_containers_amend.py#L140) to the actual selected root and [smoke isolation assertions](../../tests/contract/test_smoke_tenant_isolation.py#L240). Positive root contains active dependencies/settings/least-privilege bindings; commented module, missing env, incompatible partition property, namespace mismatch, live-tenant role or extra app fails. Future validation: V-INFRA, requiring separately prepared Bicep/AVM toolchain and later approved what-if; no deployment is implied. **Done:** selected-root static graph, compiled/what-if evidence and runtime configuration are attributable and consistent.

- [ ] AUD-036-SIM-021 Enforce NEMA priority at the actual simulation work boundary

  **Original obligations:** FR-056; T-J21 and retained governance/operational obligations. **Expected/actual/impact:** real Level-3 activation must suspend/throttle simulation capacity while preserving real alerts and non-dismissable operator warning. [Governor](../../apps/api/app/services/resource_governor.py#L45) has no active caller on the inspected simulation invocation path; metadata-only changes do not prevent work.

  **Developer instructions:** Subscribe to the actual authorised NEMA activation/resolution source and gate new parsing, sub-agent dispatch and simulated publication at their common execution boundary. Persist the throttle decision/reason and emit the priority banner through active SSE, preserving in-flight cleanup and all real-tenant notifications. No model/tool can disable the throttle; recovery follows the documented authorised resolution and capacity policy. Coordinate tenant binding/lifecycle/cap work without replacing their separate controls.

  **Tester instructions:** Extend [NEMA tests](../../tests/integration/test_fr056_nema_throttle.py#L48) using actual route calls, not only direct governor calls. Activate Level3 during simulation dispatch; assert subsequent simulation work is refused/deprioritised, banner cannot be dismissed, real notifications are delivered unchanged, unauthorised activation is rejected and resolution restores only permitted capacity. Future validation: V-ROUTING with synthetic activation events and work/notification spies. **Done:** actual simulation work consumes the real-priority gate and every transition is audited.

- [ ] AUD-036-SIM-022 Implement bounded degraded-mode behavior and automatic recovery

  **Original obligations:** FR-041, FR-045, FR-053; SC-012; T-C13 and retained degraded-exercise obligations. **Expected/actual/impact:** coordinator-injected blackout/unavailability/partition must affect communication/replies for a bounded window and recover visibly. [Builder](../../apps/agents/simulation_telemetry_injection/degraded_mode.py#L14) only constructs a signal; no operational window/recovery consumer was found. Generic HTTP failure fallback does not implement a deliberate exercise window.

  **Developer instructions:** Persist configured outage mode, scope, start/end and original correlation; apply it to affected simulation-only subscribers/channels while preserving safety warnings and real-tenant work. Produce explicit cached/stale low-confidence replies during the window, distinguish partitioned group effects, and restore state once with recovery audit and visible chat/map update. Validate duration/scope and use durable time so replica restart does not prolong/erase the window. Keep initial low-confidence life-safety refusal separate from valid post-injection degraded re-evaluation.

  **Tester instructions:** Extend [pipeline integration](../../tests/integration/test_signal_pipeline_e2e_036.py#L75) and existing degraded-mode unit coverage with fake-clock blackout, one unavailable agent and partitioned participant group. Assert behavior before/during/at expiry, unaffected subscribers/live tenant, duplicate/reordered events, overlapping windows, restart and automatic recovery audit. Future validation: V-API with fake clock and recorded cached replies; later SC-012 needs at least 50 attributable injections. **Done:** window behavior and automatic recovery are implemented in active consumers and measured separately.

- [ ] AUD-036-SIM-023 Reconcile public contracts original tasks and explicit supersession

  **Original obligations:** FR-008, FR-009, FR-048, FR-063, FR-066, FR-067, FR-069, FR-070, FR-071, FR-073; T-A06, T-A18, T-A19, T-O05, T-O06, T-O07, T-AA07, T-AA08, T-AA10, T-AA11, T-AA12, T-AA22, T-AA23, T-AA24, T-AA25, T-AA26, T-AA29, T-AA49, T-AA50, T-AA53, T-AA54, T-AA60. **Expected/actual/impact:** spec, schema, HTTP and migration guidance should describe one compatible contract. [OpenAPI200](contracts/openapi-simulation.yaml#L209) differs from [Ack202](data-model.md#L927); required arrays, trigger enums and503 semantics differ. [Error handler](../../apps/api/app/middleware/error_handler.py#L163) stringifies structured details, replacing specific types/extensions with generic errors and discarding exception headers. Audit common discriminator omits the26th declared entry; SSE batch introduces a forbidden property. Historical task summaries also assign unrelated completed work to task IDs.

  **Developer instructions:** Produce a narrow approved reconciliation for each concrete contradiction, citing authoritative clarifications and preserving locked historical task/mirror text with explicit supersession notes. Keep spec036-only problem+json and unchanged legacy envelopes; preserve structured problem type/extensions/headers and the2xx integrity-warning carve-out. Align current OpenAPI, Pydantic, audit discriminator, SSE batch, strict-model schema, SDK migration and context-specific enums in the same compatible release. Add the originally required domain exports and schema-generation/check pipeline using existing domain/codegen owners, with drift assertions against generated consumers. Resolve full-failure success-event coexistence and five-versus-seven-SLI wording explicitly; do not use documentation cleanup to waive original behavior or measurements. No original file is modified in this audit.

  **Tester instructions:** Extend [route allow-list tests](../../tests/contract/test_spec_036_route_allow_list.py#L1), [schema tests](../../tests/contract/test_sli_kql_schema_v2.py#L1), [endpoint tests](../../apps/api/tests/test_inject_telemetry_endpoint.py#L1) and existing audit/SDK tests. Assert actual202 response/status/required arrays, every 4xx/5xx structured type and Retry-After, legacy route unchanged,26 discriminator variants, SSE batch strict validation, historical kebab reads/new Pascal writes and all trigger contexts. Future validation: V-CONTRACT with no live services; later SDK release requires explicit compatibility approval. **Done:** every conflict has cited disposition and connected contract tests enforce the chosen surface.

- [ ] AUD-036-SIM-024 Replace historical closure claims with attributable validation and review evidence

  **Original obligations:** SC-001, SC-002, SC-003, SC-004, SC-005, SC-006, SC-007, SC-008, SC-009, SC-010, SC-011, SC-012, SC-013, SC-014; all FS gates; T-B16, T-F02a, T-F02b, T-N06, T-N07, T-S08, T-U03, T-W03, T-W04, T-Z02, T-AA41, T-AA42, T-AA45, T-AA48, T-AA55, T-AA56, T-AA61. **Expected/actual/impact:** execution/latency/outcome/deployment/approval claims require reproducible attributable records. [Sweep](final-sweep-report.md#L60) records older v0.2.0 counts with known failures; [latest3400 claim](spec.md#L6473) lacks current raw run/candidate linkage. Property tests, manually entered counts, catalog URIs and persona synthesis are not real outcomes, waveform checks, WORM state, issue status or human approval.

  **Developer instructions:** After source fixes, make the existing required suites discoverable in CI, replace assertion-only/mocked shortcuts with connected contract tests, and collect immutable evidence recording SHA, dirty-tree status, environment, tool versions, dataset/seed, command, raw results, timestamps and signer/approver. Preserve historical records without retroactively checking original tasks. Pin matched baseline/intervention cohorts and required sample sizes; distinguish model-quality, economic/evacuation/resource outcomes, latency, safety, accessibility, retention and deployment. Retrieve external issue/review receipts only with separate authorization; missing evidence remains UNVERIFIED. Do not force an old exact total to hide newly discovered failures.

  **Tester instructions:** Use the existing suites named in this report and the scenario/SC tables, including [measurement matrix](sc-measurement-matrix.md#L8) only as a historical index. Verify discovery of simulation web, unit, contract, integration, canary/load suites; assert no unexpected skip/xfail, correct full-app fixtures, and reproducible raw artifacts. Future validation: V-MEASURE, with expressly approved staging, model budgets, safe synthetic datasets and named human accessibility/governance reviewers. Expected outcomes are the exact current SC thresholds, not historical PASS prose. **Done:** each execution/approval/deployed-state assertion has current attributable evidence; unresolved gates remain open.

- [ ] AUD-036-SIM-025 Enforce top-down KQL column scope in the validity gate

  **Original obligations:** FR-073; T-AA30, T-AA31, T-AA32, T-AA33, T-AA43, T-AA44, T-AA45, T-AA46, T-AA47, T-AA48; quality CHK210. **Expected/actual/impact:** canonical equality must be supplemented by in-scope column validation. [Walker](../../tests/contract/test_sli_kql_runtime_validity.py#L350) precollects later let bindings and [retains columns](../../tests/contract/test_sli_kql_runtime_validity.py#L625) removed by projection/aggregation; both contract and implementation can agree on an invalid query.

  **Developer instructions:** Preserve the chosen lightweight offline walker and unchanged six-step canonicaliser, but track table schemas/bindings top-down with replacement semantics for project and summarize. Honour lexical quoting/comments/member accesses, only earlier scalar lets and declared columns, and intentional fail-fast union rejection. Emit SLI, unresolved name, source line and complete canonical query; do not add a Kusto runtime dependency or accept unknown columns to make current queries pass.

  **Tester instructions:** Extend [validity suite](../../tests/contract/test_sli_kql_runtime_validity.py#L350) and existing canonicaliser golden tests. Reject forward let, project-away then reference, summarize-away then project and union; accept preserved group keys, aggregate aliases, member access and quoted strings. Apply identical invalid mutations to both spec/implementation fixture queries so equality alone is green but validity is red. Future validation: V-CONTRACT, pure offline fixtures. **Done:** all declared SLIs are dynamically enumerated and scope defects fail with useful diagnostics, without skips or whitelist broadening.

- [ ] AUD-036-SIM-026 Enforce the canonical carve-out registry and model privacy boundary

  **Original obligations:** FR-062; T-U01, T-U02, T-U03, T-U04, T-U05, T-K05, T-K07; Constitution NN-2/NN-3. **Expected/actual/impact:** tenant/deployment/reason/evidence/expiry/approver are mandatory and referenced carve-outs must be evaluated on PR/daily cadence. [Schema](../../infra/foundry/carveout-registry.schema.json#L24) requires different fields and optional approver; [tests](../../tests/unit/test_foundry_carveout_registry.py#L99) pin that weaker shape. [Alternative review](../../.github/workflows/foundry-carveout-review.yml#L3) and [six-month workflow](../../.github/workflows/foundry-carveout-review-6mo.yml#L11) are manual-only, use another registry, and the former's PR-only comment job is unreachable from its trigger. Dispatcher model traffic also bypasses the controller's optional model gateway.

  **Developer instructions:** Reconcile the competing registries through an explicitly versioned canonical schema or documented adapter; require attributable approvals/evidence and expiry per tenant/deployment. Add actual PR and daily evaluation, marker-to-entry identity matching, missing/empty/stale rejection and exact model-deployment coverage. Enforce the existing data-minimisation/deny policy at every non-AU model egress, including dispatcher calls; never treat a governance seed's approval text as an executable permission or rewrite old hashes to imply new approvals. Preserve the bounded model-host exception, AU storage/telemetry and existing consumers' read compatibility. Separate policy enforcement from obtaining human approval.

  **Tester instructions:** Extend [registry tests](../../tests/unit/test_foundry_carveout_registry.py#L99) and [workflow tests](../../tests/devops/test_foundry_carveout_workflow.py#L1). Use empty registry with/without referenced markers, unknown IDs, missing evidence/approver, expired/future dates, tenant/deployment mismatch, PR/scheduled trigger fixtures, and sensitive prompt routed through controller versus dispatcher. Assert fail-closed missing approval, consistent privacy filtering/denial and reachable required CI jobs; no external inference calls. Future validation: V-CONTRACT with fake gateway/clock and local registry fixtures. **Done:** all model-host exceptions are attributable, checked on required cadence and enforced at each active egress boundary.

## Future Validation Catalog

These are instructions for a separately authorised implementation/testing session, NOT commands executed by this audit. Prerequisites: prepared Python3.12+ environment, repository import paths and declared dependencies; Node/pnpm workspace dependencies for web; external services replaced by explicit doubles unless a staging run is separately approved. Tests must be extended with the cases in their follow-up before a green result is meaningful. Existing filenames in the commands are test homes, not claims that those tests already cover every case.

```text
V-API: python -m pytest apps/api/tests/test_inject_telemetry_endpoint.py apps/api/tests/test_lifecycle_endpoints.py tests/integration/test_signal_pipeline_e2e_036.py tests/integration/test_rbac_enforcement_036.py -q
V-STORAGE: python -m pytest tests/unit/test_simulation_sequence_repository_036.py tests/unit/test_audit_writer_sequence_wireup_036.py tests/unit/test_simulation_idempotency_repository_036.py tests/contract/test_idempotency_fail_closed_036.py tests/contract/test_jcs_canonicalisation_036.py -q
V-ROUTING: python -m pytest tests/integration/test_jurisdiction_routing_tuples.py tests/unit/test_cascade_thread_cap_036.py tests/integration/test_controller_cascade_hook.py tests/e2e/test_cascade_orchestrator_round_trip.py tests/integration/test_fr056_nema_throttle.py -q
V-COMMS: python -m pytest tests/unit/test_communication_delivery.py tests/unit/test_communication_watermark_handler.py tests/contract/test_watermark_locale_coverage.py -q
V-LESSONS: python -m pytest apps/api/tests/test_lessons_capture_and_export.py tests/integration/test_lessons_capture_full_aar.py tests/contract/test_outcome_read_api.py -q
V-GATES: python -m pytest tests/integration/test_assert_sli_thresholds_z6_z7.py tests/unit/test_assert_sli_thresholds_envelope_writer.py tests/integration/test_staging_promotion_concurrency.py tests/e2e/test_staging_promotion_gates.py -q
V-SMOKE: python -m pytest tests/e2e/test_staging_smoke_injection_floor.py tests/integration/test_smoke_injection_no_prod_pollution.py apps/api/tests/test_inject_telemetry_endpoint.py -q
V-CONTRACT: python -m pytest tests/contract/test_spec_036_route_allow_list.py tests/contract/test_sli_kql_schema_v2.py tests/contract/test_sli_kql_canonical_match.py tests/contract/test_sli_kql_runtime_validity.py tests/unit/test_foundry_carveout_registry.py tests/devops/test_foundry_carveout_workflow.py -q
V-INFRA: python -m pytest tests/unit/test_cosmos_simulation_containers_amend.py tests/contract/test_smoke_tenant_isolation.py -q
V-WEB: pnpm --filter @ama/web exec vitest run tests/unit/spec_036 __tests__/simulation-live-log.test.tsx tests/a11y/simulation-map-non-point.test.tsx
V-MEASURE: python -m pytest tests/load/test_sc010_map_overlay_slo.py -q
```

V-MEASURE is only one existing harness, not a complete SC certification command: separately execute the pinned paired-exercise, load, safety, chaos, model and accessibility protocols identified in the SC table. Its current live node skips; a skipped node or manufactured timing fixture cannot count as measured latency. Human approval, deployed-resource state, Speech asset reachability, KQL ingestion and WORM enforcement need separately attributable observations and cannot be established by the static commands above.

## Complete Input Manifest

All 29 original local documents were read completely across the independent review contexts and coordinating review: 20,397 physical lines. Original summaries using 66 FRs, 12 SCs, 233 tasks, or historical document lengths are not current inventories. The rejected initial handoff was not used to certify completeness. Required Review Contract lines1-59, code-review instructions, applicable code-commenting/Bicep instructions, Python fact-grounded/Cosmos review guidance, and the current Constitution were also consulted; no runtime guidance was executed.

| Input | Lines | Assessment boundary |
| --- | --- | --- |
| [spec.md](spec.md#L1) | 6477 | Complete original requirements, five amendment cycles, clarifications, cohorts, assumptions, scenarios, edges and close records. |
| [tasks.md](tasks.md#L1) | 2772 | Complete prior ranges, amendments, all61 AA headings and37 FS gates; all original task states are none. |
| [plan.md](plan.md#L1) | 1978 | Complete decisions, deployment/identity/latency/compatibility assumptions and late-cycle immutability rules. |
| [research.md](research.md#L1) | 575 | Complete12 decisions, R13-R18, risks, costs and ADR references; costs are historical estimates. |
| [data-model.md](data-model.md#L1) | 1095 | Complete models, persistence, replay, AIIMS and Cycle2 contract changes. |
| [quickstart.md](quickstart.md#L1) | 269 | Procedure and historical completion claim only; no step executed. |
| [fr-coverage-matrix.md](fr-coverage-matrix.md#L1) | 56 | Historical grouped coverage; not proof for current FRs. |
| [sc-measurement-matrix.md](sc-measurement-matrix.md#L1) | 21 | Historical SC-1 through SC-12 keys differ from canonical SC definitions. |
| [final-sweep-report.md](final-sweep-report.md#L1) | 158 | Recorded2026-05-09 assertions, failures and sign-off; no current run evidence. |
| [analyze-cycle2-pass1.md](analyze-cycle2-pass1.md#L1) | 222 | Formal documentary consistency review, not implementation execution. |
| [analyze-cycle2-pass2.md](analyze-cycle2-pass2.md#L1) | 294 | Recorded closures and residuals assessed against current inputs. |
| [contracts/audit-envelope.md](contracts/audit-envelope.md#L1) | 816 | 26 typed sections, shared discriminator and dispatch/refusal contracts. |
| [contracts/error-responses.md](contracts/error-responses.md#L1) | 238 | Six-route problem-details scope and legacy compatibility. |
| [contracts/idempotency-cache.md](contracts/idempotency-cache.md#L1) | 242 | 24-hour replay, JCS, ordering, lifecycle, headers and crash window. |
| [contracts/openapi-changelog.md](contracts/openapi-changelog.md#L1) | 127 | Breaking-version/SDK migration obligations; release not assumed. |
| [contracts/openapi-simulation.yaml](contracts/openapi-simulation.yaml#L1) | 644 | Actual v0.3.0 paths and schemas, including inconsistencies. |
| [contracts/sli-thresholds.md](contracts/sli-thresholds.md#L1) | 534 | All operational/runtime SLIs, thresholds, KQL and canonicalisation. |
| [contracts/sse-map-overlay.md](contracts/sse-map-overlay.md#L1) | 202 | Six events,16 layers, replay/snapshot/batch/geometry contracts. |
| [contracts/sub-agent-adapter.md](contracts/sub-agent-adapter.md#L1) | 275 | Adapter compatibility, timeout/session/provenance; five unchecked review items. |
| [contracts/telemetry-injection-llm.md](contracts/telemetry-injection-llm.md#L1) | 431 | Strict parser, safety, quotas, multiple signals, hash/fallback contract. |
| [checklists/accessibility-and-cald.md](checklists/accessibility-and-cald.md#L1) | 150 | 47 items:33 checked,14 unchecked. |
| [checklists/amendment-pass.md](checklists/amendment-pass.md#L1) | 545 | 100 unchecked items. |
| [checklists/audit-and-provenance.md](checklists/audit-and-provenance.md#L1) | 214 | 65 items:47 checked,18 unchecked. |
| [checklists/graceful-degradation.md](checklists/graceful-degradation.md#L1) | 216 | 71 items:56 checked,15 unchecked. |
| [checklists/integration-and-test-coverage.md](checklists/integration-and-test-coverage.md#L1) | 118 | 58 checked design/test-enumerability items. |
| [checklists/multi-jurisdiction.md](checklists/multi-jurisdiction.md#L1) | 169 | 31 unchecked items. |
| [checklists/quality.md](checklists/quality.md#L1) | 1198 | 144 unchecked items, CHK101 through CHK244. |
| [checklists/requirements.md](checklists/requirements.md#L1) | 270 | 16 checked unnumbered criteria and six review iterations. |
| [checklists/safety-and-life-primacy.md](checklists/safety-and-life-primacy.md#L1) | 91 | 44 checked items; safety execution is not implied. |

The nine checklist files contain576 items:254 checked and322 unchecked. Five unchecked adapter acceptance items and two unchecked quoted CHK237 alternatives in the specification are assessed separately. Neither quoted alternative is an extra original task or a duplicate item in the quality checklist.

## Evidence Reference Key

Coverage cells use the following clickable source references. Each points to inspected existing source/test/configuration at a precise current line. A source link proves only the assessment stated in its cell, never a test run. Follow-up IDs identify the detailed instructions above; a dash means no new remediation for that narrowly implemented artifact, not runtime approval.

Supporting assertions include [JCS], [LAYERS-TEST], [MAP-TEST], [KQL-TEST], [SMOKE-TEST] and [REGISTRY-TEST]. Operational boundaries include [WORM], [INFRA], [ROOT], [ALERT], [CI] and [ERRORS]. Documentary reconciliation uses [CONTRACT], [TASKS], [PLAN] and [C5]. These are reference links to specific evidence, not execution receipts.

[AUTH]: ../../apps/api/app/api/dependencies/simulation_rbac.py#L227
[TENANT]: ../../apps/api/app/middleware/tenant_middleware.py#L47
[ROUTE]: ../../apps/api/app/api/routes/simulations_036.py#L176
[CHAT]: ../../apps/api/app/services/simulation/controller_service.py#L927
[TOOLS]: ../../apps/api/app/services/simulation/controller_tools.py#L175
[DISPATCH]: ../../apps/agents/dispatcher/agent.py#L208
[ADAPTER]: ../../apps/api/app/services/simulation/sub_agents/_base.py#L108
[INVOKER]: ../../apps/api/app/services/simulation/sub_agent_invoker.py#L90
[PIPE]: ../../apps/api/app/services/simulation/signal_pipeline_orchestrator.py#L234
[INJECT]: ../../apps/agents/simulation_telemetry_injection/handler.py#L75
[SIGNAL]: ../../packages/domain/src/domain/models/synthetic_signal.py#L48
[SIGNALS]: ../../apps/api/app/repositories/synthetic_signals_repository.py#L75
[STATE]: ../../apps/api/app/services/simulation/repositories/simulation_state.py#L126
[AUDIT]: ../../apps/api/app/services/simulation/audit_writer.py#L314
[SEQUENCE]: ../../apps/api/app/repositories/simulation_sequence_repository.py#L1
[CACHE]: ../../apps/api/app/repositories/simulation_idempotency_repository.py#L287
[JCS]: ../../apps/api/app/repositories/simulation_idempotency_repository.py#L82
[RBAC-TEST]: ../../tests/integration/test_rbac_enforcement_036.py#L43
[PIPE-TEST]: ../../tests/integration/test_signal_pipeline_e2e_036.py#L75
[CAP]: ../../apps/api/app/services/simulation/thread_cap_service.py#L94
[CASCADE]: ../../apps/api/app/services/simulation/cascade_orchestrator.py#L323
[LADDER]: ../../apps/api/app/services/simulation/cascade_affinity_ladder.py#L58
[TUPLES]: ../../apps/api/app/services/simulation/jurisdiction_routing.py#L69
[TUPLE-TEST]: ../../tests/integration/test_jurisdiction_routing_tuples.py#L65
[MATRIX]: ../../packages/domain/src/domain/sim_cascade_matrix.py#L1
[AIIMS]: ../../packages/domain/src/domain/models/aiims_mapping.py#L1
[RECORD]: ../../packages/domain/src/domain/models/sub_agent_invocation_record.py#L1
[MAP]: ../../apps/web/src/components/simulation-map.tsx#L219
[MAP-PAGE]: ../../apps/web/src/app/simulations/[tenantId]/page.tsx#L574
[MAP-REDUCER]: ../../apps/web/src/lib/sse/map-overlay-dispatch.ts#L94
[MAP-PUBLISH]: ../../apps/api/app/services/simulation/map_overlay_publisher.py#L149
[LAYERS]: ../../packages/domain/src/domain/models/sim_layer_taxonomy.py#L1
[LAYERS-TEST]: ../../tests/unit/test_sim_layer_taxonomy.py#L1
[MAP-TEST]: ../../apps/web/tests/unit/spec_036/simulation-map-non-point.test.tsx#L91
[LIVELOG]: ../../apps/web/src/components/simulation-live-log.tsx#L114
[LIVELOG-TEST]: ../../apps/web/__tests__/simulation-live-log.test.tsx#L56
[COMMS]: ../../apps/agents/communication/delivery.py#L66
[WATERMARK]: ../../apps/api/app/services/simulation/public_warning_watermark_guard.py#L49
[LOCALES]: ../../apps/api/app/services/simulation/data/sim_locale_table.json#L1
[LOCALES-TEST]: ../../tests/contract/test_watermark_locale_coverage.py#L63
[LESSONS]: ../../apps/api/app/services/simulation/lessons_capture.py#L365
[DRAFT]: ../../apps/api/app/services/simulation/lessons_capture.py#L213
[AAR-TEST]: ../../tests/integration/test_lessons_capture_full_aar.py#L172
[WORM]: ../../apps/api/app/services/simulation/lessons_capture_blob_worm.py#L107
[EXPORT]: ../../apps/api/app/services/simulation/audit_export.py#L67
[OUTCOME]: ../../apps/api/app/services/simulation/outcome_signed_url.py#L127
[WORKFLOW]: ../../.github/workflows/staging-promotion.yml#L130
[GATE]: ../../tests/staging_gates.py#L249
[COLLATE]: ../../.github/workflows/staging-promotion.yml#L157
[GATE-TEST]: ../../tests/e2e/test_staging_promotion_gates.py#L265
[KQL]: ../../infra/observability/sli-kql.json#L76
[KQL-TEST]: ../../tests/contract/test_sli_kql_schema_v2.py#L66
[KQL-CANON]: ../../tests/contract/test_sli_kql_canonical_match.py#L1
[KQL-WALK]: ../../tests/contract/test_sli_kql_runtime_validity.py#L350
[SMOKE]: ../../.github/workflows/staging-promotion.yml#L285
[SMOKE-TEST]: ../../tests/contract/test_smoke_tenant_isolation.py#L240
[INFRA]: ../../infra/bicep/main.bicep#L546
[ROOT]: ../../azure.yaml#L8
[CD]: ../../.github/workflows/cd.yml#L225
[ALERT]: ../../infra/bicep/modules/simulation-app-insights-alerts.bicep#L92
[REGISTRY]: ../../infra/foundry/carveout-registry.schema.json#L24
[CARVEOUT]: ../../.github/workflows/foundry-carveout-review.yml#L3
[REGISTRY-TEST]: ../../tests/unit/test_foundry_carveout_registry.py#L99
[CI]: ../../.github/workflows/ci.yml#L131
[NEMA]: ../../apps/api/app/services/resource_governor.py#L45
[DEGRADED]: ../../apps/agents/simulation_telemetry_injection/degraded_mode.py#L14
[ERRORS]: ../../apps/api/app/middleware/error_handler.py#L163
[CONTRACT]: contracts/openapi-simulation.yaml#L209
[TASKS]: tasks.md#L91
[PLAN]: plan.md#L19
[SWEEP]: final-sweep-report.md#L60
[C5]: spec.md#L6473

## Functional Requirement Coverage

All73 FRs are represented once below. There are no separately numbered NFRs; nonfunctional, assumption, persona and unnumbered obligations are assessed in the later constraints table. Canonical FR definitions, not historical coverage-matrix labels, control these rows.

| Requirement | Status | Inspected evidence and assessment | Follow-up |
| --- | --- | --- | --- |
| [FR-001](spec.md#L2318) | PARTIAL | [INVOKER], [DISPATCH]: six adapters connect to role-prompt dispatcher, not operational handlers. | AUD-036-SIM-004 |
| [FR-002](spec.md#L2322) | IMPLEMENTED | [INVOKER], [DISPATCH]: old literal stub reply removed from active returns; different ungrounded fallback remains a separate FR-001 issue. | - |
| [FR-003](spec.md#L2325) | PARTIAL | [CHAT], [ADAPTER]: full HTTP responses, no partial sub-agent stream or one-second guarantee. | AUD-036-SIM-013 |
| [FR-004](spec.md#L2327) | PARTIAL | [CHAT]: model tool loop serialises calls and returns summary/citations; no guaranteed concurrent attributed aggregation. | AUD-036-SIM-005, AUD-036-SIM-013 |
| [FR-005](spec.md#L2329) | PARTIAL | [RECORD], [CHAT], [AUDIT]: record fields exist; active call lacks linked durable invocation/response/state chain. | AUD-036-SIM-004, AUD-036-SIM-008 |
| [FR-006](spec.md#L2335) | PARTIAL | [INVOKER]: hard timeout/cancellation exist; production callback absent and typed timeout audit/read budget incomplete. | AUD-036-SIM-004, AUD-036-SIM-013 |
| [FR-007](spec.md#L2338) | PARTIAL | [ADAPTER]: citations filtered/degraded; actual dispatcher emits no grounding, violation audit not connected. | AUD-036-SIM-002, AUD-036-SIM-004 |
| [FR-008](spec.md#L2344) | PARTIAL | [TOOLS], [CHAT], [INJECT]: named service/enum exists but tool execution and sequential multi-signal barrier absent. | AUD-036-SIM-005, AUD-036-SIM-006 |
| [FR-009](spec.md#L2357) | PARTIAL | [SIGNAL], [PIPE]: provenance/budget incomplete; producer acknowledgement is not consumption. Supersession conflicts recorded separately. | AUD-036-SIM-005, AUD-036-SIM-006 |
| [FR-010](spec.md#L2440) | PARTIAL | [INJECT]: pre-parse gate lacks category/confidence; five-category low-confidence refusal not enforced after parse. | AUD-036-SIM-006 |
| [FR-011](spec.md#L2461) | PARTIAL | [SIGNAL], [ROUTE]: correlation optional and not assigned to persisted candidate from route correlation. | AUD-036-SIM-006 |
| [FR-012](spec.md#L2463) | PARTIAL | [INJECT]: singleton outcome cannot represent multiple signals sharing one turn. | AUD-036-SIM-006 |
| [FR-013](spec.md#L2465) | PARTIAL | [ROUTE], [INJECT], [SIGNALS]: history loaded with generic600s/fallback empty; returned contradictions not persisted. | AUD-036-SIM-006 |
| [FR-014](spec.md#L2477) | PARTIAL | [SIGNAL], [MAP-PUBLISH]: freshness fields/helper exist; no connected stale consumption lifecycle. | AUD-036-SIM-006, AUD-036-SIM-012 |
| [FR-015](spec.md#L2479) | PARTIAL | [PIPE], [PIPE-TEST]: separate publication without actual subscriber/session-token barrier. | AUD-036-SIM-005 |
| [FR-016](spec.md#L2511) | PARTIAL | [INJECT] overwrites tenant fields, but [TENANT]/[AUTH] do not establish owner-bound context and downstream consumption. | AUD-036-SIM-002, AUD-036-SIM-005 |
| [FR-017](spec.md#L2516) | PARTIAL | [CHAT]: model-driven tool choice exists; deterministic intent/subscriber integration absent. | AUD-036-SIM-007 |
| [FR-018](spec.md#L2518) | PARTIAL | [PIPE], [CHAT]: Risk named in registry; not an automatically executed operational handler per hazard turn. | AUD-036-SIM-005, AUD-036-SIM-007 |
| [FR-019](spec.md#L2521) | PARTIAL | [CHAT], [TUPLES]: no enforced explicit-name precedence/authorised doctrinal routing path. | AUD-036-SIM-007 |
| [FR-020](spec.md#L2523) | PARTIAL | [CHAT], [TUPLES]: ambiguity helpers do not gate actual dispatch or produce guaranteed typed clarification. | AUD-036-SIM-007 |
| [FR-021](spec.md#L2526) | PARTIAL | [TUPLES], [TUPLE-TEST]: useful registry fixtures; missing active five-step location-aware resolution and agency disambiguation. | AUD-036-SIM-007 |
| [FR-022](spec.md#L2603) | PARTIAL | [CHAT]: six-role enum does not establish jurisdictional combat/control/support intent constraints. | AUD-036-SIM-007 |
| [FR-023](spec.md#L2605) | PARTIAL | [TUPLES], [TUPLE-TEST]: ACT names/hints exist; no active federal/territory intent discriminator. | AUD-036-SIM-007 |
| [FR-024](spec.md#L2607) | PARTIAL | [TUPLE-TEST]: medical-brand fixture exists but controller bypasses the tuple path. | AUD-036-SIM-007 |
| [FR-025](spec.md#L2610) | PARTIAL | [CHAT]: explicit NSW escalation-consent boundary not integrated with persona routing. | AUD-036-SIM-007 |
| [FR-026](spec.md#L2613) | PARTIAL | [PIPE], [CHAT]: Risk publish metadata exists; real hazard auto-invocation/dedup missing. | AUD-036-SIM-005 |
| [FR-027](spec.md#L2629) | PARTIAL | [LAYERS], [MAP-REDUCER], [MAP]: canonical16 supported; active feed, non-point visuals, unified palette/SIM styles incomplete. | AUD-036-SIM-001, AUD-036-SIM-012 |
| [FR-028](spec.md#L2672) | PARTIAL | [MAP-PAGE], [KQL]: no connected overlay feed or measured15s guarantee. | AUD-036-SIM-012, AUD-036-SIM-019 |
| [FR-029](spec.md#L2674) | PARTIAL | [MAP-PAGE], [KQL]: no connected weather/geohazard10s delivery evidence. | AUD-036-SIM-012, AUD-036-SIM-019 |
| [FR-030](spec.md#L2676) | PARTIAL | [MAP-REDUCER], [MAP]: stale state not preserved through complete active visual-layer path. | AUD-036-SIM-001, AUD-036-SIM-012 |
| [FR-031](spec.md#L2678) | PARTIAL | [AIIMS], [MAP]: canonical tags exist; map-bound properties drop complete attribution/SIM overlay styling. | AUD-036-SIM-001, AUD-036-SIM-012 |
| [FR-032](spec.md#L2680) | PARTIAL | [MAP-REDUCER], [MAP-PAGE]: layer vocabulary is not nonlinear TC category/zone computation and delivery. | AUD-036-SIM-012 |
| [FR-033](spec.md#L2682) | PARTIAL | [MATRIX], [CASCADE], [MAP-PAGE]: transport target set exists; route recomputation/map delivery disconnected. | AUD-036-SIM-011, AUD-036-SIM-012 |
| [FR-034](spec.md#L2685) | PARTIAL | [MAP], [MAP-PUBLISH]: shared point clustering exists; complete overlay overflow/indicator/audit preservation unproven. | AUD-036-SIM-001, AUD-036-SIM-012 |
| [FR-035](spec.md#L2691) | PARTIAL | [COMMS], [DISPATCH]: prefix helper does not guarantee exact prefixed active Communication receipt. | AUD-036-SIM-003, AUD-036-SIM-014 |
| [FR-036](spec.md#L2694) | PARTIAL | [COMMS], [AUDIT]: receipt schema exists, active response does not guarantee every required receipt field. | AUD-036-SIM-003 |
| [FR-037](spec.md#L2696) | PARTIAL | [COMMS]: inconsistent simulation predicate and unguarded publication/direct SDK boundary. | AUD-036-SIM-003 |
| [FR-038](spec.md#L2699) | PARTIAL | [PIPE], [AUDIT]: typed synthetic-delivery construction exists but active channel blocks/audits are not complete. | AUD-036-SIM-003, AUD-036-SIM-008 |
| [FR-039](spec.md#L2701) | PARTIAL | [WATERMARK], [LOCALES]: expanded catalog not consumed before all persistence/approval/render; bilingual coverage incomplete. | AUD-036-SIM-014 |
| [FR-040](spec.md#L2737) | PARTIAL | [COMMS], [WATERMARK]: channel-wide jurisdictional exact-prefix enforcement is incomplete. | AUD-036-SIM-003, AUD-036-SIM-014 |
| [FR-041](spec.md#L2744) | PARTIAL | [DEGRADED], [COMMS]: mode builder does not implement channel suppression/Triple Zero visibility on active calls. | AUD-036-SIM-022 |
| [FR-042](spec.md#L2747) | PARTIAL | [INJECT], [CHAT]: some real-action refusal exists, typed audit/egress coverage incomplete. | AUD-036-SIM-003, AUD-036-SIM-006 |
| [FR-043](spec.md#L2787) | PARTIAL | [MATRIX], [CASCADE]: utility targets encoded; hook/operational invocation/cap connection absent. | AUD-036-SIM-011 |
| [FR-044](spec.md#L2798) | PARTIAL | [MATRIX], [CASCADE]: transport targets encoded, not active rerouting within budget. | AUD-036-SIM-011, AUD-036-SIM-012 |
| [FR-045](spec.md#L2803) | PARTIAL | [DEGRADED], [CASCADE]: channel-state handling does not change live simulation Communication options. | AUD-036-SIM-022 |
| [FR-046](spec.md#L2805) | PARTIAL | [MATRIX], [CASCADE]: resource cascade model exists; actual fan-out disconnected. | AUD-036-SIM-011 |
| [FR-047](spec.md#L2808) | PARTIAL | [MATRIX], [CASCADE]: evacuation alias/targets exist; authoritative centre-to-agent/map mutation incomplete. | AUD-036-SIM-011, AUD-036-SIM-012 |
| [FR-048](spec.md#L2853) | PARTIAL | [SEQUENCE], [AUDIT]: allocation precedes validation/commit; memory DLQ and swallowed errors violate dense durable audit. | AUD-036-SIM-008 |
| [FR-049](spec.md#L2920) | PARTIAL | [EXPORT], [OUTCOME]: export builder exists, authorised durable reader/route and integrity warning path incomplete. | AUD-036-SIM-002, AUD-036-SIM-015 |
| [FR-050](spec.md#L2922) | PARTIAL | [TENANT], [SIGNALS]: syntactic tenant fields do not establish full bidirectional owner isolation. | AUD-036-SIM-002, AUD-036-SIM-005 |
| [FR-051](spec.md#L2925) | PARTIAL | [AUTH], [RBAC-TEST]: coordinator role deny exists; no authoritative simulation-owner lookup and read parity. | AUD-036-SIM-002 |
| [FR-052](spec.md#L2969) | PARTIAL | [CAP], [CASCADE]: local five-slot helper is not distributed active hazard-only enforcement. | AUD-036-SIM-011 |
| [FR-053](spec.md#L3002) | PARTIAL | [DEGRADED]: three modes have no operational bounded-window/recovery consumers. | AUD-036-SIM-022 |
| [FR-054](spec.md#L3191) | PARTIAL | [DRAFT], [LESSONS], [OUTCOME]: rich helper not persisted or lifecycle-queued; required content/index/read incomplete. | AUD-036-SIM-015 |
| [FR-055](spec.md#L3232) | PARTIAL | [LESSONS], [AAR-TEST]: generated_at differs; tests exclude it; WORM/index retry safety incomplete. | AUD-036-SIM-015 |
| [FR-056](spec.md#L3237) | PARTIAL | [NEMA], [CHAT]: metadata governor unconsumed by actual simulation work. | AUD-036-SIM-021 |
| [FR-057](spec.md#L3007) | PARTIAL | [LADDER], [CAP], [CASCADE]: deterministic helper supported, target-thread attachment/cap/audit integration not. | AUD-036-SIM-011 |
| [FR-058](spec.md#L2750) | PARTIAL | [LOCALES-TEST], [WATERMARK]: pointer reachability is not bilingual spoken-prefix or asset/review evidence. | AUD-036-SIM-014, AUD-036-SIM-024 |
| [FR-059](spec.md#L3105) | PARTIAL | [STATE], [CHAT], [ROUTE]: separate IDs/state, swallowed writes, unregistered cancellation and no abort queue. | AUD-036-SIM-010, AUD-036-SIM-015 |
| [FR-060](spec.md#L2952) | PARTIAL | [RECORD], [DISPATCH], [CHAT]: fingerprint returned but active durable invocation/aggregation drops provenance. | AUD-036-SIM-004, AUD-036-SIM-008 |
| [FR-061](spec.md#L3247) | PARTIAL | [AIIMS], [RECORD]: canonical primary/secondary model exists; active invocation/output attribution incomplete. | AUD-036-SIM-004, AUD-036-SIM-013 |
| [FR-062](spec.md#L3301) | PARTIAL | [REGISTRY], [CARVEOUT]: incompatible schema, empty seed, missing daily/PR marker enforcement. | AUD-036-SIM-026 |
| [FR-063](spec.md#L3323) | PARTIAL | [WORKFLOW], [GATE], [CD]: some Z6/Z7 checks, not full required evidence or production gate. | AUD-036-SIM-016, AUD-036-SIM-018, AUD-036-SIM-019 |
| [FR-064](spec.md#L3368) | PARTIAL | [LIVELOG], [MAP-PAGE], [LIVELOG-TEST]: isolated ARIA component, unmounted stream/locales/audits. | AUD-036-SIM-013 |
| [FR-065](spec.md#L3410) | PARTIAL | [AUDIT], [ROUTE]: optional hash-source and incomplete accepted/refused/fallback hash preimages. | AUD-036-SIM-006, AUD-036-SIM-008 |
| [FR-066](spec.md#L3447) | PARTIAL | [CACHE], [ROUTE]: capable result types/JCS exist but no route caller, invalid storage shape and replay races. | AUD-036-SIM-009 |
| [FR-067](spec.md#L3540) | PARTIAL | [PIPE], [ROUTE]: explicit degraded statuses exist, but publish-only ack and pre-persist202 violate accepted-dispatch meaning. | AUD-036-SIM-005, AUD-036-SIM-008, AUD-036-SIM-023 |
| [FR-068](spec.md#L3574) | PARTIAL | [MATRIX], [CASCADE]: canonical matrix/YAML removal supported; actual controller-to-subscriber round trip absent. | AUD-036-SIM-011 |
| [FR-069](spec.md#L3592) | PARTIAL | [AUDIT], [ROUTE]: shared JCS array construction supported; durable writes/true consumers and conflicting context enums unresolved. | AUD-036-SIM-005, AUD-036-SIM-008, AUD-036-SIM-023 |
| [FR-070](spec.md#L3604) | PARTIAL | [AIIMS], [AUDIT]: canonical names/migration helper exist; helper not wired into all historical read paths. | AUD-036-SIM-008, AUD-036-SIM-023 |
| [FR-071](spec.md#L3625) | PARTIAL | [WORKFLOW], [GATE]: helper invoked, but missing SLIs, invalid collation, non-durable refusals and CD bypass remain. | AUD-036-SIM-016, AUD-036-SIM-018 |
| [FR-072](spec.md#L3647) | PARTIAL | [SMOKE], [ROUTE]: actual POST/OIDC added; body and ID incompatible with accepting endpoint. | AUD-036-SIM-017 |
| [FR-073](spec.md#L3666) | PARTIAL | [KQL], [KQL-CANON], [KQL-WALK]: corrected queries/universal comparison exist; validity scope and downstream collation incomplete. | AUD-036-SIM-018, AUD-036-SIM-025 |

## Success Criterion Coverage

No new runtime, model, latency or outcome measurement was performed. Every criterion below remains UNVERIFIED as a measured result, even where deterministic supporting code exists. Historical SC-matrix statements use different meanings and cannot substitute for these canonical obligations.

| Criterion | Status | Required measurement and inspected limitation | Follow-up |
| --- | --- | --- | --- |
| [SC-001](spec.md#L3744) | UNVERIFIED | Actionable Risk reply within15s in95% of200 injections; [PIPE]/[DISPATCH] do not prove operational answers; [GATE] is not that200-injection experiment. | AUD-036-SIM-004, AUD-036-SIM-019, AUD-036-SIM-024 |
| [SC-002](spec.md#L3748) | UNVERIFIED | Warning lead-time median at most50% matched baseline over30 pairs; [SWEEP] contains no attributable paired result. | AUD-036-SIM-024 |
| [SC-003](spec.md#L3752) | UNVERIFIED | Evacuation recommendation at least24 scenario-hours earlier in80% of matched runs; no linked measurement receipt. | AUD-036-SIM-024 |
| [SC-004](spec.md#L3756) | UNVERIFIED | At least30% fewer reallocations in80% of matched exercises; [SWEEP] is not a baseline/intervention outcome dataset. | AUD-036-SIM-024 |
| [SC-005](spec.md#L3759) | UNVERIFIED | At least30% synthetic economic-loss reduction in70%; no attributable AIDR-profile experiment. | AUD-036-SIM-024 |
| [SC-006](spec.md#L3762) | UNVERIFIED | Continuous zero real egress across all channels, any violation SEV0; [COMMS] exposes a conditional predicate gap, no continuous trace evidence. | AUD-036-SIM-003, AUD-036-SIM-024 |
| [SC-007](spec.md#L3770) | UNVERIFIED | 100% typed/provenanced accepted signal or audited refusal; [SIGNAL]/[AUDIT] show concrete completeness gaps. | AUD-036-SIM-006, AUD-036-SIM-008, AUD-036-SIM-024 |
| [SC-008](spec.md#L3773) | UNVERIFIED | 100% exact complete synthetic receipts and every-PR sweep; [COMMS]/[CARVEOUT] and literal tests do not prove active channel-wide receipts. | AUD-036-SIM-003, AUD-036-SIM-014, AUD-036-SIM-024 |
| [SC-009](spec.md#L3777) | UNVERIFIED | 100% automatic Risk invocation over200 samples; [PIPE-TEST] checks publish-derived nonempty array, not agent invocation. | AUD-036-SIM-005, AUD-036-SIM-024 |
| [SC-010](spec.md#L3781) | UNVERIFIED | All major categories meet10/15s map budgets over100 observations; [MAP-PAGE] lacks feed and timing harness fabricates fixtures/skips live node. | AUD-036-SIM-012, AUD-036-SIM-019, AUD-036-SIM-024 |
| [SC-011](spec.md#L3784) | UNVERIFIED | Zero thread collapse/cross-contamination across30 multi-hazard exercises; [CAP]/[CASCADE] lack active distributed enforcement. | AUD-036-SIM-011, AUD-036-SIM-024 |
| [SC-012](spec.md#L3788) | UNVERIFIED | 100% outage-window behavior and recovery across at least50 injections; [DEGRADED] is a constructor, not measured consumer behavior. | AUD-036-SIM-022, AUD-036-SIM-024 |
| [SC-013](spec.md#L3791) | UNVERIFIED | Fresh trailing24h Z6/Z7 evidence, floor30 and canonical per-model/drift thresholds; [COLLATE]/[CD] expose gate gaps and no current promotion receipt. | AUD-036-SIM-016, AUD-036-SIM-018, AUD-036-SIM-024 |
| [SC-014](spec.md#L3804) | UNVERIFIED | Fixture red shapes must cause nonzero gate, one refusal and no promotion/deploy; [GATE-TEST] exercises helper but not actual CD boundary. | AUD-036-SIM-016, AUD-036-SIM-018, AUD-036-SIM-024 |

## Acceptance Scenario Coverage

All54 numbered user-story scenarios are individually assessed. `USnn-ASnn` is this report's stable key for the original story and scenario ordinal, not a new requirement. Timings and human/model outcomes remain unmeasured even where a row has source support.

| Scenario | Status | Expected behavior and inspected assessment | Follow-up |
| --- | --- | --- | --- |
| [US01-AS01](spec.md#L1794) | PARTIAL | Monitoring/Risk/Evacuation substantive tenant-grounded reply within30s: [DISPATCH] is short role prompts, [CHAT] lacks guaranteed aggregation. | AUD-036-SIM-004, AUD-036-SIM-013 |
| [US01-AS02](spec.md#L1799) | PARTIAL | NSW rural/urban exact combat agency: [TUPLES] is bypassed by [CHAT]. | AUD-036-SIM-007 |
| [US01-AS03](spec.md#L1803) | PARTIAL | Slow acknowledgement/partial output/correlated timeout: [INVOKER] has timeout but callback/audit/partial stream absent. | AUD-036-SIM-004, AUD-036-SIM-013 |
| [US01-AS04](spec.md#L1807) | PARTIAL | Turn->invocation->response->mutation correlation: [RECORD] not actively durably written by [CHAT]. | AUD-036-SIM-008 |
| [US01-AS05](spec.md#L1810) | PARTIAL | Injection first, fresh Risk state, one turn envelope: [TOOLS] registration lacks [CHAT] execution. | AUD-036-SIM-005 |
| [US02-AS01](spec.md#L1848) | PARTIAL | Exactly weather+fire signals with provenance/GPS: [INJECT] returns singleton and [SIGNAL] lacks required source/user. | AUD-036-SIM-006 |
| [US02-AS02](spec.md#L1852) | PARTIAL | Risk10s/Evacuation+Resource15s and aggregate: [PIPE] acknowledges publisher, not agents. | AUD-036-SIM-005, AUD-036-SIM-019 |
| [US02-AS03](spec.md#L1856) | PARTIAL | Uncertain input clarifies/audits without write: malformed fallback exists, low-confidence typed gate incomplete [INJECT]. | AUD-036-SIM-006 |
| [US02-AS04](spec.md#L1860) | PARTIAL | Disabled category refused with explanation: closed enum [SIGNAL] does not implement configured enabled-category policy. | AUD-036-SIM-006 |
| [US02-AS05](spec.md#L1863) | PARTIAL | Contradiction accepted/tagged, Risk reruns: [INJECT] returns separate IDs discarded by [ROUTE]. | AUD-036-SIM-006 |
| [US02-AS06](spec.md#L1866) | PARTIAL | Life-safety-low refused before write: [INJECT] passes no parsed category/confidence to gate. | AUD-036-SIM-006 |
| [US02-AS07](spec.md#L1871) | PARTIAL | Non-life-safety-low accepted best-effort: [INJECT] can accept, but provenance/downstream degradation not complete. | AUD-036-SIM-006, AUD-036-SIM-022 |
| [US03-AS01](spec.md#L1903) | PARTIAL | Located wind bearing/speed/AWS/SIM within15s: [MAP] renders marker/summary, not directional overlay; page has no feed. | AUD-036-SIM-001, AUD-036-SIM-012 |
| [US03-AS02](spec.md#L1907) | PARTIAL | Perimeter visually changes within15s: [MAP] filters polygons from rendered collection. | AUD-036-SIM-001 |
| [US03-AS03](spec.md#L1910) | PARTIAL | Centre capacity/status updates without reload: [MAP-PAGE] has no live overlay state. | AUD-036-SIM-012 |
| [US03-AS04](spec.md#L1913) | PARTIAL | Outage and dependent overlays within30s: [PIPE]/[CASCADE]/[MAP-PAGE] disconnected. | AUD-036-SIM-011, AUD-036-SIM-012 |
| [US03-AS05](spec.md#L1917) | PARTIAL | Visibly stale geometry: [MAP-REDUCER] supports states but [MAP] does not preserve complete styling path. | AUD-036-SIM-001, AUD-036-SIM-012 |
| [US04-AS01](spec.md#L1945) | PARTIAL | Wind automatically invokes Risk guidance: [CHAT]/[PIPE] do not invoke actual subscriber. | AUD-036-SIM-005 |
| [US04-AS02](spec.md#L1948) | PARTIAL | Gauge automatically invokes Monitoring/Risk/Evacuation: [PIPE] generic registry publication not exact operational targets. | AUD-036-SIM-005, AUD-036-SIM-007 |
| [US04-AS03](spec.md#L1951) | PARTIAL | Evacuate directive invokes Evacuation/Communication with receipt: [CHAT]/[COMMS] incomplete. | AUD-036-SIM-003, AUD-036-SIM-007 |
| [US04-AS04](spec.md#L1954) | PARTIAL | Explicit Planning wins with Planning only: no enforced server precedence [CHAT]. | AUD-036-SIM-007 |
| [US04-AS05](spec.md#L1957) | PARTIAL | Ambiguous intent clarifies/audits: routing helper not controlling [CHAT]. | AUD-036-SIM-007 |
| [US04-AS06](spec.md#L1960) | PARTIAL | Hazard update invokes Risk same turn: [PIPE-TEST] asserts list, not invocation. | AUD-036-SIM-005 |
| [US04-AS07](spec.md#L1964) | PARTIAL | Viewport inference records step3: [TUPLES]/ladder not used by [CHAT]. | AUD-036-SIM-007 |
| [US04-AS08](spec.md#L1969) | PARTIAL | Border/no history clarifies, no speculative fan-out: helper defaults can broaden selection [TUPLES]. | AUD-036-SIM-007 |
| [US04-AS09](spec.md#L1975) | PARTIAL | Server NSW overrides client VIC with mismatch audit: no active viewport routing decision [CHAT]. | AUD-036-SIM-007 |
| [US05-AS01](spec.md#L2014) | PARTIAL | Literal prefix and five receipt fields: [DISPATCH]/[COMMS] return no guaranteed complete receipt. | AUD-036-SIM-003 |
| [US05-AS02](spec.md#L2017) | PARTIAL | SMS blocked before network: shared HTTP guard exists, direct SDK predicate differs [COMMS]. | AUD-036-SIM-003 |
| [US05-AS03](spec.md#L2020) | PARTIAL | Watermark every rendering/language: [WATERMARK] not connected before actual persistence/approval. | AUD-036-SIM-014 |
| [US05-AS04](spec.md#L2023) | PARTIAL | Degraded channels/Triple Zero prominent: [DEGRADED] has no active consumer window. | AUD-036-SIM-022 |
| [US05-AS05](spec.md#L2027) | PARTIAL | Commonwealth action creates simulation artifacts only: [CHAT]/[COMMS] lack complete typed refusal/receipt boundary. | AUD-036-SIM-003 |
| [US05-AS06](spec.md#L2030) | PARTIAL | Curated English-first bilingual text, no model prefix translation: active small YAML differs from [LOCALES]. | AUD-036-SIM-014 |
| [US05-AS07](spec.md#L2036) | PARTIAL | Missing text locale English-only with audit: helper exists but connected artifact coverage incomplete [WATERMARK]. | AUD-036-SIM-014 |
| [US05-AS08](spec.md#L2040) | PARTIAL | English then curated locale spoken prefix: one-clip helper/catalog fixtures do not prove sequencing [LOCALES-TEST]. | AUD-036-SIM-014 |
| [US05-AS09](spec.md#L2047) | PARTIAL | Missing audio locale English-only/audit, no model fallback: pointers/tests not actual waveform or production path [LOCALES-TEST]. | AUD-036-SIM-014, AUD-036-SIM-024 |
| [US06-AS01](spec.md#L2077) | PARTIAL | Subscribed targets only/no contamination: [PIPE] publication not consumption, owner context incomplete [AUTH]. | AUD-036-SIM-002, AUD-036-SIM-005 |
| [US06-AS02](spec.md#L2080) | PARTIAL | Separate NSW rural fire/flood combat threads: [TUPLES]/[CAP] not controlling active dispatch. | AUD-036-SIM-007, AUD-036-SIM-011 |
| [US06-AS03](spec.md#L2083) | PARTIAL | Independent NTFRS/BushfiresNT resources: tuple membership only [TUPLE-TEST]. | AUD-036-SIM-007 |
| [US06-AS04](spec.md#L2086) | PARTIAL | Visible agency/jurisdiction attribution: [CHAT] output discards invocation details. | AUD-036-SIM-007, AUD-036-SIM-013 |
| [US06-AS05](spec.md#L2088) | PARTIAL | Sixth coordinator hazard hard-refused with split-sim guidance: [CAP] local and disconnected. | AUD-036-SIM-011 |
| [US06-AS06](spec.md#L2093) | PARTIAL | Sixth cascade attaches real annotation: [CASCADE] candidate API mismatch and no attachment. | AUD-036-SIM-011 |
| [US06-AS07](spec.md#L2100) | PARTIAL | Newest mutation selects ThreadB deterministically: [LADDER] supports ordering but active candidate/write connection absent. | AUD-036-SIM-011 |
| [US06-AS08](spec.md#L2111) | PARTIAL | Depth2 refusal, new explicit action/correlation, no transitive origin: helper [CASCADE] not reached from controller. | AUD-036-SIM-011 |
| [US07-AS01](spec.md#L2148) | PARTIAL | Utility Health/Comms/Transport/Resource within30s: [MATRIX] alias ambiguity and disconnected dispatch. | AUD-036-SIM-005, AUD-036-SIM-011 |
| [US07-AS02](spec.md#L2151) | PARTIAL | Road closure reroutes/updates map15s: [CASCADE]/[MAP-PAGE] not connected. | AUD-036-SIM-011, AUD-036-SIM-012 |
| [US07-AS03](spec.md#L2154) | PARTIAL | Degraded channel reflected next turn: [DEGRADED]/[COMMS] no active state consumer. | AUD-036-SIM-022 |
| [US08-AS01](spec.md#L2180) | PARTIAL | Blackout suppresses channels and expires automatically: [DEGRADED] constructs signal only. | AUD-036-SIM-022 |
| [US08-AS02](spec.md#L2183) | PARTIAL | Unavailable Risk supplies cached degraded state and recovers: [INVOKER] timeout text is not configured window behavior. | AUD-036-SIM-022 |
| [US08-AS03](spec.md#L2186) | PARTIAL | Partitioned group reports degradation: no partition-state consumer found [DEGRADED]. | AUD-036-SIM-022 |
| [US09-AS01](spec.md#L2211) | PARTIAL | Required outcome sections after end: [LESSONS] bypasses [DRAFT] and lifecycle queue. | AUD-036-SIM-015 |
| [US09-AS02](spec.md#L2214) | PARTIAL | Byte-identical regeneration: [AAR-TEST] excludes generated_at, [LESSONS] uses current time. | AUD-036-SIM-015 |
| [US09-AS03](spec.md#L2216) | PARTIAL | Retriable generation without loss: [WORM]/[OUTCOME] do not establish durable retry/index recovery. | AUD-036-SIM-015 |
| [US09-AS04](spec.md#L2218) | PARTIAL | Pause finishes existing steps, rejects new work, no replay on resume: [STATE]/[CHAT] separate pathways. | AUD-036-SIM-010 |
| [US09-AS05](spec.md#L2228) | PARTIAL | Abort cancels/audits/ends/queues lessons: [ROUTE] reports start with no enqueue, cancellation registry unpopulated by chat. | AUD-036-SIM-010, AUD-036-SIM-015 |

## Amendment Acceptance Coverage

The59 explicit acceptance bullets under Cycle2-Cycle5 amendment detail blocks are separately enumerated, including clarified bullets. Step8 A-S requirements and clarification decisions are additionally assessed in the constraints/supersession table. No numbered FR/SC is added by Cycles4/5.

| Clause | Status | Evidence and assessment | Follow-up |
| --- | --- | --- | --- |
| [A2-01-AC01](spec.md#L129) | PARTIAL | [PIPE]/[ROUTE] classify outcomes, but publish is not consumption; Q1 explicitly replaces acknowledged-only shape. | AUD-036-SIM-005 |
| [A2-01-AC02](spec.md#L130) | PARTIAL | [AUDIT] builds typed failure envelope, durability/exactly-one write not guaranteed. | AUD-036-SIM-008 |
| [A2-01-AC03](spec.md#L131) | CONFLICT | [ROUTE] suppresses success on total failure; canonical FR067 says durable-write success may still fire. Q1 resolves array shape, not this coexistence conflict. | AUD-036-SIM-023 |
| [A2-01-AC04](spec.md#L132) | PARTIAL | [CACHE] not called by routes; degraded replay not effective. | AUD-036-SIM-009 |
| [A2-02-AC01](spec.md#L144) | PARTIAL | [KQL] declares queries, named runtime producers absent. | AUD-036-SIM-019 |
| [A2-02-AC02](spec.md#L145) | PARTIAL | [GATE-TEST] covers helper breach, [CD] bypasses gate. | AUD-036-SIM-016 |
| [A2-02-AC03](spec.md#L146) | IMPLEMENTED | [KQL]/[KQL-TEST] contain Z6 SC001 and Z7 SC010 references. | - |
| [A2-02-AC04](spec.md#L147) | IMPLEMENTED | [KQL] preserves operational DLQ/RU/cascade definitions; runtime validity separate. | - |
| [A2-03-AC01](spec.md#L157) | IMPLEMENTED | [MATRIX]/[CASCADE] use Python canonical matrix; Q3 selected removal of YAML fan_out_rules. | - |
| [A2-03-AC02](spec.md#L158) | PARTIAL | Round-trip tests exercise helper/counts, not full actual subscriber set/latency [PIPE-TEST]. | AUD-036-SIM-011, AUD-036-SIM-024 |
| [A2-03-AC03](spec.md#L159) | CONFLICT | [MATRIX] uses Logistics where human utility row names Transport; canonical nine-name set has no Transport. | AUD-036-SIM-023 |
| [A2-04-AC01](spec.md#L169) | IMPLEMENTED | [Audit success schema](contracts/audit-envelope.md#L151) requires subscriber array. | - |
| [A2-04-AC02](spec.md#L170) | PARTIAL | [AUDIT] JCS helper supports byte equality; connected durability/status semantics incomplete. | AUD-036-SIM-005, AUD-036-SIM-008 |
| [A2-04-AC03](spec.md#L171) | PARTIAL | [EXPORT] can reconstruct supplied records; persisted source/actual outcomes incomplete. | AUD-036-SIM-015 |
| [A2-05-AC01](spec.md#L181) | IMPLEMENTED | [Error contract](contracts/error-responses.md#L194) explicitly narrows six-route surface. | - |
| [A2-05-AC02](spec.md#L182) | PARTIAL | [ERRORS] supports problem MIME but loses typed detail/extensions and headers. | AUD-036-SIM-023 |
| [A2-05-AC03](spec.md#L183) | IMPLEMENTED | [ERRORS] nonmatched path retains legacy envelope; execution unverified. | - |
| [A2-06-AC01](spec.md#L193) | IMPLEMENTED | [CASCADE] no caller-supplied depth-refusal sequence literal remains. | - |
| [A2-06-AC02](spec.md#L194) | PARTIAL | [AUDIT]/[SEQUENCE] delegate allocation; validation/persist gaps remain despite helper tests. | AUD-036-SIM-008 |
| [A2-06-AC03](spec.md#L195) | IMPLEMENTED | [AUDIT] removes supplied sequence with warning and allocates centrally. | - |
| [A2-07-AC01](spec.md#L205) | IMPLEMENTED | [Audit enum](contracts/audit-envelope.md#L149), [AIIMS] use nine PascalCase names. | - |
| [A2-07-AC02](spec.md#L206) | IMPLEMENTED | [Enum contract test](../../tests/contract/test_audit_envelope_sub_agent_enum_alignment.py#L1) asserts canonical alignment. | - |
| [A2-07-AC03](spec.md#L207) | IMPLEMENTED | [Migration ledger](contracts/openapi-changelog.md#L36) documents historical-read compatibility; actual reads remain partial. | - |
| [A3-01-AC01](spec.md#L286) | PARTIAL | [WORKFLOW] calls helper, but only selected SLIs/unsafe row collation reach it. | AUD-036-SIM-018 |
| [A3-01-AC02](spec.md#L287) | PARTIAL | [GATE-TEST] does not execute actual production/tagging eligibility. | AUD-036-SIM-016 |
| [A3-01-AC03](spec.md#L288) | IMPLEMENTED | [WORKFLOW] success logging follows threshold-helper return on its normal path. | - |
| [A3-02-AC01](spec.md#L298) | PARTIAL | [SMOKE] performs POST now, but schema/UUID invalid. | AUD-036-SIM-017 |
| [A3-02-AC02](spec.md#L299) | IMPLEMENTED | [SMOKE] asserts202/nondegraded response; achieving it remains blocked. | AUD-036-SIM-017 |
| [A3-02-AC03](spec.md#L300) | SUPERSEDED | [Cycle3 Q2](spec.md#L926) explicitly forbids long-lived SMOKE_TOKEN and selects per-run OIDC. | - |
| [A3-02-AC04](spec.md#L301) | PARTIAL | Pollution fixtures inspect YAML; no qualified emitted client metric rows [SMOKE]/[KQL]. | AUD-036-SIM-017, AUD-036-SIM-019 |
| [A3-03-AC01](spec.md#L311) | IMPLEMENTED | [ADR010](../../docs/aidr/decisions/ADR-036-010-cycle-2-amendment-cycle.md#L87) cites actual helper. | - |
| [A3-03-AC02](spec.md#L312) | IMPLEMENTED | [Changelog](../../CHANGELOG.md#L36) cites assert_sli_thresholds; other mislabelled IDs remain separate. | - |
| [A3-03-AC03](spec.md#L313) | IMPLEMENTED | [Citation tests](../../tests/docs/test_adr_036_010_symbol_citations.py#L1) contain symbol-resolution assertions; not run. | - |
| [A3-04-AC01](spec.md#L323) | IMPLEMENTED | [ADR010](../../docs/aidr/decisions/ADR-036-010-cycle-2-amendment-cycle.md#L83) quotes corrected model bands. | - |
| [A3-04-AC02](spec.md#L324) | IMPLEMENTED | [Changelog](../../CHANGELOG.md#L35) quotes corrected Z6 bands. | - |
| [A3-04-AC03](spec.md#L325) | IMPLEMENTED | [Drift test](../../tests/docs/test_adr_036_010_threshold_drift.py#L1) compares numeric thresholds with configuration. | - |
| [A3-05-AC01](spec.md#L335) | IMPLEMENTED | [KQL] current Z6 includes sub-agent/env and dimensional grouping. | - |
| [A3-05-AC02](spec.md#L336) | PARTIAL | [COLLATE]/[GATE] collapse to per-model series, potentially masking a slow agent. | AUD-036-SIM-018 |
| [A3-05-AC03](spec.md#L337) | IMPLEMENTED | [KQL-CANON] enumerates every declared SLI; later universal-scope clarification preserved. | - |
| [A3-06-AC01](spec.md#L349) | IMPLEMENTED | [KQL] current Z7 uses client_received minus server_emit and staging filter. | - |
| [A3-06-AC02](spec.md#L350) | IMPLEMENTED | [KQL]/[KQL-TEST] pin99.5 warning/99.0 breach. | - |
| [A3-06-AC03](spec.md#L351) | IMPLEMENTED | [KQL-CANON] covers Z7 as well as Z6. | - |
| [A4-01-AC01](spec.md#L3900) | IMPLEMENTED | [KQL] Z7 defines deployment before filtering/grouping. | - |
| [A4-01-AC02](spec.md#L3901) | IMPLEMENTED | [Canonical Z7](contracts/sli-thresholds.md#L276) contains symmetric definition. | - |
| [A4-01-AC03](spec.md#L3902) | UNVERIFIED | [KQL-CANON] assertions exist; no current executed seven-SLI result. | AUD-036-SIM-024 |
| [A4-01-AC04](spec.md#L3903) | PARTIAL | [KQL-WALK] implemented but forward bindings/removed columns still accepted. | AUD-036-SIM-025 |
| [A4-01-AC05](spec.md#L3904) | SUPERSEDED | [Count correction](spec.md#L4438) then [single3400](spec.md#L5774) explicitly replace3392 forecast; no execution proof. | AUD-036-SIM-024 |
| [A4-01-AC06](spec.md#L3905) | PARTIAL | [KQL-WALK] is lightweight/no Kusto dependency; actual in-scope discipline incomplete. | AUD-036-SIM-025 |
| [A4-02-AC01](spec.md#L3920) | IMPLEMENTED | [ADR011](../../docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md#L172) records database scope/compensating control/backlog. | - |
| [A4-02-AC02](spec.md#L3921) | IMPLEMENTED | [Explicit supersession](spec.md#L3907) preserves old mirror and changes authoritative wording. | - |
| [A4-02-AC03](spec.md#L3922) | PARTIAL | [SMOKE-TEST] checks text shape; actual root's conditional role not supplied, KQL filters not authorization. | AUD-036-SIM-020 |
| [A4-02-AC04](spec.md#L3923) | UNVERIFIED | [Changelog issue84](../../CHANGELOG.md#L15) is a local citation, not external creation/open-state proof. | AUD-036-SIM-024 |
| [A4-02-AC05](spec.md#L3924) | UNVERIFIED | [C5] count assertion cannot establish preserved zero-failure baseline. | AUD-036-SIM-024 |
| [A4-02-AC06](spec.md#L3925) | IMPLEMENTED | [ADR011](../../docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md#L172) contains both required documentary phrasings. | - |
| [A5-01-AC01](spec.md#L4968) | IMPLEMENTED | [Role block](../../infra/bicep/modules/cosmos-simulation-containers.bicep#L296), [SMOKE-TEST] retain database scope and corrected current wording. Historical byte equality unverified. | - |
| [A5-01-AC02](spec.md#L4969) | IMPLEMENTED | [Role block](../../infra/bicep/modules/cosmos-simulation-containers.bicep#L305) follows four-clause documentary order. Not proof of tenant authorization. | - |
| [A5-01-AC03](spec.md#L4970) | IMPLEMENTED | [SMOKE-TEST] has exactly the two lower()+in absence assertions selected by clarify. | - |
| [A5-01-AC04](spec.md#L4971) | UNVERIFIED | [Single3400 posture](spec.md#L5774) is binding forecast/disposition, not current test result. | AUD-036-SIM-024 |
| [A5-01-AC05](spec.md#L4972) | UNVERIFIED | [ADR011 status](../../docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md#L3) says Accepted; no attributable human/cohort approval records inspected. | AUD-036-SIM-024 |

## Original Task Coverage

The current task source has ZERO checkbox task lines. Every original state is therefore `none`; DONE, COMPLETE, DONE-PRIOR and NEW are narrative labels, not `[x]`. The289-row inventory comprises132 retained A-K tasks (expanding the explicit ranges and `T-F02a/b` into two suffixed IDs),96 L-Z tasks, and61 AA tasks. Repeated dependency/phase/renumbering references do not create tasks. No bare T-F02, speculative T-AB ID or other036 folder task is added.

Where the source collapsed several prior tasks into a generic range, this report preserves each ID but does not invent its lost allocation/acceptance text. `UNVERIFIED` there means the individual original obligation cannot be established from the retained source; the row still assesses the concrete nearby group implementation. Recovering that historical allocation belongs to AUD-036-SIM-023/024, not retrospective checkbox edits. Source searches for relocated models/repositories/tools covered API/agents/domain/scripts/tools/schema/config and relevant tests; infrastructure declarations were traced from the selected root before absence claims.

### Retained Foundation and Prior Phases

| Original task | Original state | Status | Inspected evidence and assessment | Follow-up |
| --- | --- | --- | --- | --- |
| T-A01 | none | PARTIAL | [SIGNAL]: unified hazard category model, unrestricted parameters and missing source/user provenance. | AUD-036-SIM-006 |
| T-A02 | none | PARTIAL | [SIGNAL]: resource category accepted, no specialised validated resource payload. | AUD-036-SIM-006 |
| T-A03 | none | PARTIAL | [SIGNAL]: channel-state category accepted, no specialised channel-state payload. | AUD-036-SIM-006 |
| T-A04 | none | PARTIAL | [STATE]/[AUDIT]: lifecycle state/audit schemas exist, distinct event contract and active common lifecycle incomplete. | AUD-036-SIM-010 |
| T-A05 | none | PARTIAL | [RECORD]: hash/latency/AIIMS model lacks full request/response/citation record and active writer. | AUD-036-SIM-004, AUD-036-SIM-008 |
| T-A06 | none | PARTIAL | [AUDIT]: amendment fields added, optional provenance and common schema26 parity incomplete. | AUD-036-SIM-008, AUD-036-SIM-023 |
| T-A07 | none | PARTIAL | [MAP-PUBLISH]: renamed OverlayChange validates layers, not full closed wire-event operation/payload. | AUD-036-SIM-012, AUD-036-SIM-023 |
| T-A08 | none | PARTIAL | [WATERMARK]: typed application/result helpers exist, pre-approval active coverage incomplete. | AUD-036-SIM-014 |
| T-A09 | none | PARTIAL | [Container declarations](../../infra/bicep/modules/cosmos-simulation-containers.bicep#L200) have counter/cache/DLQ values, raw resources and disconnected selected root. | AUD-036-SIM-020 |
| T-A10 | none | PARTIAL | [Consumer groups](../../infra/bicep/modules/eventhub-simulation-consumer-groups.bicep#L25) refer to existing hub; no complete selected-root hub/publisher connection. | AUD-036-SIM-020 |
| T-A11 | none | MISSING | Infrastructure Speech-resource/AAD search found only [TTS storage](../../infra/bicep/modules/tts-audio-storage.bicep#L22), not Speech provisioning. | AUD-036-SIM-020 |
| T-A12 | none | IMPLEMENTED | [Maps account](../../infra/modules/azure-maps.bicep#L26) and [selected-root call](../../infra/main.bicep#L439) implement account scaffolding; deployed state unverified. | - |
| T-A13 | none | PARTIAL | [RECORD] exports locally; [central export](../../packages/domain/src/index.ts#L14) does not aggregate simulation domain contracts. | AUD-036-SIM-023 |
| T-A14 | none | MISSING | Domain discriminator/union search found [SIGNAL] category Literal plus generic parameters, not a discriminated signal union. | AUD-036-SIM-006 |
| T-A15 | none | MISSING | Scripts/tools/domain/schema searches found [domain scripts](../../packages/domain/package.json#L19), not a simulation JSON-schema export pipeline. | AUD-036-SIM-023 |
| T-A16 | none | CONFLICT | [Domain audit test](../../packages/domain/tests/test_telemetry_injection_audit_entry.py#L28) asserts24 while [current test](../../tests/contract/test_audit_envelope_schema_2020_12.py#L37) asserts26. | AUD-036-SIM-023, AUD-036-SIM-024 |
| T-A17 | none | PARTIAL | [PIPE] derives trace strings, [adapter tracing contract](contracts/sub-agent-adapter.md#L165) not a connected simulation span schema/export. | AUD-036-SIM-019 |
| T-A18 | none | PARTIAL | [Common audit schema](contracts/audit-envelope.md#L16) exists but discriminator omits26th section. | AUD-036-SIM-023 |
| T-A19 | none | PARTIAL | [CONTRACT]/[ERRORS] provide routes/problem MIME but response/status/header/enum parity incomplete. | AUD-036-SIM-023 |
| T-A20 | none | PARTIAL | [Central changelog](../../CHANGELOG.md#L25) records later domain migration, not complete original foundation-model changelog. | AUD-036-SIM-023 |
| T-B01 | none | IMPLEMENTED | [SimulationRepository](../../apps/api/app/repositories/simulation_repository.py#L20) consumed by [creation service](../../apps/api/app/services/simulation_service.py#L40). | - |
| T-B02 | none | PARTIAL | [AUDIT] append branch exists, default storage/complete durable reader and DLQ incomplete. | AUD-036-SIM-008 |
| T-B03 | none | PARTIAL | [SIGNALS] replaces stub; stored id/simulationId/system fields fed to strict model on read; memory tests omit boundary. | AUD-036-SIM-006, AUD-036-SIM-020 |
| T-B04 | none | MISSING | API/agent/domain persistence-call search found [RECORD] and [container](../../infra/bicep/modules/cosmos-simulation-containers.bicep#L98), no invocation repository/writer. | AUD-036-SIM-004, AUD-036-SIM-008 |
| T-B05 | none | PARTIAL | [Outcome index](../../apps/api/app/services/simulation/lessons_capture_index.py#L35) is renamed storage; Cosmos upsert lacks memory path's differing-body protection. | AUD-036-SIM-015 |
| T-B06 | none | PARTIAL | [SEQUENCE]/[STATE] conditional-write code exists; patched tests do not establish SDK ETag transmission and atomic commit. | AUD-036-SIM-008, AUD-036-SIM-010 |
| T-B07 | none | MISSING | API simulation/domain repository bulk/batcher search found only single [SIGNALS] upserts; unrelated paired audit writes not a bulk batcher. | AUD-036-SIM-005, AUD-036-SIM-008 |
| T-B08 | none | SUPERSEDED | [PhaseO](tasks.md#L440) and [ADR009](../../docs/aidr/decisions/ADR-036-009-idempotency-cache-design.md#L36) explicitly replace pre-amendment stub; replacement [CACHE] remains partial. | AUD-036-SIM-009 |
| T-B09 | none | IMPLEMENTED | [AUDIT] delegates sequence to repository, [wire-up assertions](../../tests/unit/test_audit_writer_sequence_wireup_036.py#L45) support scoped local-counter replacement. | AUD-036-SIM-008 |
| T-B10 | none | IMPLEMENTED | [Repository assertions](../../tests/unit/test_synthetic_signals_repository_036.py#L51) and [sequence cases](../../tests/unit/test_simulation_sequence_repository_036.py#L34) are authored unit tests, not run proof. | - |
| T-B11 | none | PARTIAL | [Retry loop](../../apps/api/app/repositories/simulation_sequence_repository.py#L166) retries412; initial read/create/bootstrap failures outside retry protocol. | AUD-036-SIM-008 |
| T-B12 | none | PARTIAL | [ALERT] has RU query, no repository request-charge instrumentation; raw RU compared with percentage-like threshold. | AUD-036-SIM-019 |
| T-B13 | none | CONFLICT | [TTL contract](data-model.md#L11) says72h signals/30d routing; [signal TTL](../../infra/bicep/modules/cosmos-simulation-containers.bicep#L90) is-1. | AUD-036-SIM-020, AUD-036-SIM-023 |
| T-B14 | none | CONFLICT | [Partition contract](data-model.md#L11) uses snake case, [original containers](../../infra/bicep/modules/cosmos-simulation-containers.bicep#L68) camel case; cache document differs again. | AUD-036-SIM-020, AUD-036-SIM-023 |
| T-B15 | none | IMPLEMENTED | [Signal factory](../../tests/unit/test_synthetic_signals_repository_036.py#L31), [state reset/conflict fixture](../../tests/integration/test_lifecycle_state_persistence_036.py#L46) exist. | - |
| T-B16 | none | UNVERIFIED | [Quickstart emulator instructions](quickstart.md#L32), default repository fixtures not a faithful emulator configuration or attributable run. | AUD-036-SIM-024 |
| T-B17 | none | PARTIAL | [Changelog](../../CHANGELOG.md#L45) records later allocator changes, not original repository completion evidence. | AUD-036-SIM-023 |
| T-C01 | none | UNVERIFIED | Retained C01-C09 grouping lacks individual allocation; [ROUTE] scaffolding assessed, parser integration partial. | AUD-036-SIM-006, AUD-036-SIM-023 |
| T-C02 | none | UNVERIFIED | Individual grouped task detail unavailable; [SIGNAL] model validates enum but generic parameters. | AUD-036-SIM-006, AUD-036-SIM-023 |
| T-C03 | none | UNVERIFIED | Individual grouped task detail unavailable; [INJECT] PII scrub path exists, full provenance/control integration partial. | AUD-036-SIM-006, AUD-036-SIM-023 |
| T-C04 | none | UNVERIFIED | Individual grouped task detail unavailable; [SIGNALS] recent-history path does not enforce complete freshness contract. | AUD-036-SIM-006, AUD-036-SIM-023 |
| T-C05 | none | UNVERIFIED | Individual grouped task detail unavailable; [INJECT] strict parser callable unregistered in application startup. | AUD-036-SIM-006, AUD-036-SIM-023 |
| T-C06 | none | UNVERIFIED | Individual grouped task detail unavailable; [INJECT] single fallback candidate not multi-signal contract. | AUD-036-SIM-006, AUD-036-SIM-023 |
| T-C07 | none | UNVERIFIED | Individual grouped task detail unavailable; [INJECT] pre-parse safety path assessed, not accepted from reused code task labels. | AUD-036-SIM-006, AUD-036-SIM-023 |
| T-C08 | none | UNVERIFIED | Individual grouped task detail unavailable; [PIPE] no subscriber-consumption barrier. | AUD-036-SIM-005, AUD-036-SIM-023 |
| T-C09 | none | UNVERIFIED | Individual grouped task detail unavailable; [PIPE-TEST] memory/nonempty assertions not complete route delivery. | AUD-036-SIM-005, AUD-036-SIM-023 |
| T-C10 | none | PARTIAL | Explicit amendment: [ROUTE] calls [PIPE], but persistence/publish/real-consumption and recent-signal integration incomplete. | AUD-036-SIM-005, AUD-036-SIM-006 |
| T-C11 | none | UNVERIFIED | Retained error/telemetry/test grouping lacks individual criteria; [ERRORS] loses structured problem details. | AUD-036-SIM-023 |
| T-C12 | none | UNVERIFIED | Individual grouped allocation unavailable; [PIPE] trace metadata not active OTel instrumentation. | AUD-036-SIM-019, AUD-036-SIM-023 |
| T-C13 | none | UNVERIFIED | Individual grouped allocation unavailable; [DEGRADED] constructor not active outage consumer. | AUD-036-SIM-022, AUD-036-SIM-023 |
| T-C14 | none | UNVERIFIED | Individual grouped allocation unavailable; [PIPE-TEST] asserts list/persistence not all contract paths. | AUD-036-SIM-024 |
| T-C15 | none | UNVERIFIED | Individual grouped allocation unavailable; [CONTRACT]/[ROUTE] status and enum mismatch. | AUD-036-SIM-023 |
| T-D01 | none | IMPLEMENTED | [MATRIX] canonical cascade model and evacuation alias exist; active consumption assessed separately. | - |
| T-D02 | none | PARTIAL | Explicit amended counter: [CAP] process-local, not durable active_hazard_threads. | AUD-036-SIM-011 |
| T-D03 | none | PARTIAL | Explicit fan-out amendment: [CASCADE] optional cap/invalid candidate API and disconnected hook. | AUD-036-SIM-011 |
| T-D04 | none | UNVERIFIED | Retained annotation/affinity grouping lacks individual criteria; [LADDER] deterministic helper exists. | AUD-036-SIM-011, AUD-036-SIM-023 |
| T-D05 | none | UNVERIFIED | Grouped allocation unavailable; [CASCADE] does not persist attachment despite selection/audit. | AUD-036-SIM-011, AUD-036-SIM-023 |
| T-D06 | none | UNVERIFIED | Grouped allocation unavailable; [LADDER] tie-breaking source exists, execution not inferred. | AUD-036-SIM-024 |
| T-D07 | none | UNVERIFIED | Grouped allocation unavailable; [CASCADE] audit subtree/parent provenance incomplete on active path. | AUD-036-SIM-008, AUD-036-SIM-011 |
| T-D08 | none | UNVERIFIED | Grouped allocation unavailable; [CAP] local release not multi-replica guarantee. | AUD-036-SIM-011 |
| T-D09 | none | UNVERIFIED | Grouped allocation unavailable; [MATRIX] targets not actual subscriber invocation. | AUD-036-SIM-011 |
| T-D10 | none | UNVERIFIED | Grouped allocation unavailable; [CASCADE] depth-refusal helper not controller callback. | AUD-036-SIM-011 |
| T-D11 | none | PARTIAL | [MAP-PUBLISH]/[LAYERS] canonical vocabulary corrected, actual event feed absent. | AUD-036-SIM-012 |
| T-D12 | none | UNVERIFIED | Grouped cascade-test allocation unavailable; [round-trip assertions](../../tests/e2e/test_cascade_orchestrator_round_trip.py#L53) count mocked/helper dispatches. | AUD-036-SIM-011, AUD-036-SIM-024 |
| T-D13 | none | UNVERIFIED | Grouped cascade-test allocation unavailable; [cap assertions](../../tests/unit/test_cascade_thread_cap_036.py#L159) expect refusal not real annotation. | AUD-036-SIM-011, AUD-036-SIM-024 |
| T-E01 | none | PARTIAL | [STATE]/[ROUTE] pause amendment exists, persistence errors swallowed and chat work not gated. | AUD-036-SIM-010 |
| T-E02 | none | PARTIAL | Resume state update exists; [CACHE] unused, lifecycle IDs disconnected. | AUD-036-SIM-009, AUD-036-SIM-010 |
| T-E03 | none | PARTIAL | Abort state/cancel calls exist, no active task registration or lessons queue [ROUTE]. | AUD-036-SIM-010, AUD-036-SIM-015 |
| T-E04 | none | UNVERIFIED | Grouped lifecycle audit/OpenAPI/tests lack unique allocation; [AUDIT] incomplete fail-closed durability. | AUD-036-SIM-008, AUD-036-SIM-023 |
| T-E05 | none | UNVERIFIED | Grouped allocation unavailable; [CONTRACT] lifecycle declaration exists but response parity incomplete. | AUD-036-SIM-023 |
| T-E06 | none | UNVERIFIED | Grouped allocation unavailable; [lifecycle tests](../../apps/api/tests/test_lifecycle_endpoints.py#L88) manually register cancellation tasks. | AUD-036-SIM-010, AUD-036-SIM-024 |
| T-F01 | none | PARTIAL | [LOCALES] expanded catalog exists, active text/audio still use smaller tables. | AUD-036-SIM-014 |
| T-F02a | none | UNVERIFIED | Source grouped F02a/b Speech prerender; [LOCALES-TEST] pointer/fallback presence not actual MP3 render/upload. | AUD-036-SIM-014, AUD-036-SIM-024 |
| T-F02b | none | UNVERIFIED | Source grouped F02a/b preserved as separate suffix; audio availability/approval not established by [LOCALES]. | AUD-036-SIM-014, AUD-036-SIM-024 |
| T-F03 | none | UNVERIFIED | Grouped watermark/audit/tests allocation unavailable; [WATERMARK] repeated embedding loses body. | AUD-036-SIM-014 |
| T-F04 | none | UNVERIFIED | Grouped allocation unavailable; [COMMS] active predicate/receipt incomplete. | AUD-036-SIM-003 |
| T-F05 | none | UNVERIFIED | Grouped allocation unavailable; [WATERMARK] application audit not integrated before approval. | AUD-036-SIM-014 |
| T-F06 | none | UNVERIFIED | Grouped allocation unavailable; [LOCALES-TEST] does not measure waveform English-first guarantee. | AUD-036-SIM-014, AUD-036-SIM-024 |
| T-F07 | none | UNVERIFIED | Grouped allocation unavailable; [COMMS] direct SDK not covered by literal prefix helpers alone. | AUD-036-SIM-003 |
| T-F08 | none | UNVERIFIED | Grouped allocation unavailable; [CI]/[SWEEP] not current all-channel execution evidence. | AUD-036-SIM-024 |
| T-G01 | none | IMPLEMENTED | [TUPLES]/[TUPLE-TEST] current jurisdiction registry and loader exist. | - |
| T-G02 | none | PARTIAL | Tuple signature/data exists; location/intent/clarification and real controller callers incomplete [TUPLES]. | AUD-036-SIM-007 |
| T-G03 | none | UNVERIFIED | Grouped routing tests/changelog lack unique allocation; [TUPLE-TEST] WA membership supported. | AUD-036-SIM-023, AUD-036-SIM-024 |
| T-G04 | none | UNVERIFIED | Grouped allocation unavailable; [TUPLE-TEST] QFD naming supported, active selection not. | AUD-036-SIM-007, AUD-036-SIM-023 |
| T-G05 | none | UNVERIFIED | Grouped allocation unavailable; [TUPLE-TEST] explicit hints not boundary-aware routing. | AUD-036-SIM-007, AUD-036-SIM-023 |
| T-G06 | none | UNVERIFIED | Grouped allocation unavailable; [TUPLES] unmatched hint returns full tuple. | AUD-036-SIM-007, AUD-036-SIM-023 |
| T-G07 | none | UNVERIFIED | Grouped allocation unavailable; [CHAT] does not consume canonical jurisdiction ladder. | AUD-036-SIM-007, AUD-036-SIM-023 |
| T-G08 | none | UNVERIFIED | Grouped allocation unavailable; [TASKS] retained completion prose not routing execution evidence. | AUD-036-SIM-024 |
| T-H01 | none | PARTIAL | [LESSONS] job functions exist, active end/abort queue missing. | AUD-036-SIM-015 |
| T-H02 | none | PARTIAL | [DRAFT] rich helper exists, [LESSONS] persisted generator bypasses it. | AUD-036-SIM-015 |
| T-H03 | none | UNVERIFIED | Grouped storage/uploader/tests lack allocation; [WORM] logs retention failure and still returns URI. | AUD-036-SIM-015, AUD-036-SIM-023 |
| T-H04 | none | UNVERIFIED | Grouped allocation unavailable; [OUTCOME] no production populated default index. | AUD-036-SIM-015, AUD-036-SIM-023 |
| T-H05 | none | UNVERIFIED | Grouped allocation unavailable; [EXPORT] source helper not authorised live read/retention proof. | AUD-036-SIM-015, AUD-036-SIM-023 |
| T-H06 | none | UNVERIFIED | Grouped allocation unavailable; [AAR-TEST] excludes nondeterministic generated_at. | AUD-036-SIM-015, AUD-036-SIM-024 |
| T-I01 | none | UNVERIFIED | Grouped layout/SSE allocation unavailable; [MAP-PAGE] active layout exists, overlay/log wiring incomplete. | AUD-036-SIM-012, AUD-036-SIM-013 |
| T-I02 | none | UNVERIFIED | Grouped allocation unavailable; [CHAT] emits generic stream, dedicated agent events absent. | AUD-036-SIM-013 |
| T-I03 | none | UNVERIFIED | Grouped allocation unavailable; [MAP-PAGE] scenario cards not replayable overlay feed. | AUD-036-SIM-012 |
| T-I04 | none | PARTIAL | Explicit map amendment: [MAP] Point-only visual path; [MAP-TEST] summary assertions do not satisfy layers. | AUD-036-SIM-001 |
| T-I05 | none | UNVERIFIED | Grouped panel/chat/tests allocation unavailable; active agent attribution metadata dropped [CHAT]. | AUD-036-SIM-013, AUD-036-SIM-023 |
| T-I06 | none | UNVERIFIED | Grouped allocation unavailable; [LIVELOG] exists standalone, unmounted. | AUD-036-SIM-013, AUD-036-SIM-023 |
| T-I07 | none | UNVERIFIED | Grouped allocation unavailable; [LIVELOG-TEST] ARIA props not active-page axe/stream proof. | AUD-036-SIM-013, AUD-036-SIM-024 |
| T-I08 | none | UNVERIFIED | Grouped allocation unavailable; [MAP-TEST]/[CI] do not establish all simulation web tests run. | AUD-036-SIM-024 |
| T-J01 | none | UNVERIFIED | Retained module range lacks allocation; [INFRA] raw Cosmos declarations not selected-root AVM delivery. | AUD-036-SIM-020, AUD-036-SIM-023 |
| T-J02 | none | UNVERIFIED | Grouped allocation unavailable; [consumer groups](../../infra/bicep/modules/eventhub-simulation-consumer-groups.bicep#L25) require existing hub. | AUD-036-SIM-020, AUD-036-SIM-023 |
| T-J03 | none | UNVERIFIED | Grouped allocation unavailable; [retention declaration](../../infra/bicep/modules/lessons-capture-storage.bicep#L44) uses84*30 days, not seven calendar years. | AUD-036-SIM-015, AUD-036-SIM-020 |
| T-J04 | none | UNVERIFIED | Grouped allocation unavailable; [TTS storage](../../infra/bicep/modules/tts-audio-storage.bicep#L22) not Speech provisioning. | AUD-036-SIM-020 |
| T-J05 | none | UNVERIFIED | Grouped allocation unavailable; [Maps invocation](../../infra/main.bicep#L439) exists with global location, effective deployment unverified. | AUD-036-SIM-020, AUD-036-SIM-024 |
| T-J06 | none | UNVERIFIED | Grouped allocation unavailable; [scaling module](../../infra/bicep/modules/container-apps-scaling.bicep#L30) exists, alternate invocation commented. | AUD-036-SIM-020 |
| T-J07 | none | PARTIAL | Explicit alert amendment: [ALERT] gap query not gap invariant and incomplete selected-root binding. | AUD-036-SIM-019, AUD-036-SIM-020 |
| T-J08 | none | UNVERIFIED | Retained identity/RBAC range lacks allocation; [API identity](../../infra/main.bicep#L1011) declared. | AUD-036-SIM-023, AUD-036-SIM-024 |
| T-J09 | none | UNVERIFIED | Grouped allocation unavailable; [Cosmos grant](../../infra/main.bicep#L894) account-scoped, not append-only simulation-specific proof. | AUD-036-SIM-020, AUD-036-SIM-023 |
| T-J10 | none | UNVERIFIED | Grouped allocation unavailable; [Blob grant](../../infra/main.bicep#L546) account-scope, not complete simulation bindings. | AUD-036-SIM-020, AUD-036-SIM-023 |
| T-J11 | none | UNVERIFIED | Grouped allocation unavailable; [API environment](../../infra/main.bicep#L1037) partial service config exists. | AUD-036-SIM-020, AUD-036-SIM-023 |
| T-J12 | none | UNVERIFIED | Grouped allocation unavailable; [agents URL](../../infra/main.bicep#L1065) points dispatcher, not proof of operational agents. | AUD-036-SIM-004, AUD-036-SIM-023 |
| T-J13 | none | UNVERIFIED | Grouped allocation unavailable; [agent environment](../../infra/main.bicep#L1139) omits complete Speech/hub configuration. | AUD-036-SIM-020 |
| T-J14 | none | UNVERIFIED | Grouped allocation unavailable; selected-root search found [registry secret](../../infra/main.bicep#L1016), not feature-specific KeyVault refs. | AUD-036-SIM-020, AUD-036-SIM-023 |
| T-J15 | none | UNVERIFIED | Grouped allocation unavailable; [INFRA]/[ROOT] differing entry points defeat declaration-only proof. | AUD-036-SIM-020 |
| T-J16 | none | UNVERIFIED | Grouped allocation unavailable; [container outputs](../../infra/bicep/modules/cosmos-simulation-containers.bicep#L270) have no demonstrated selected-root consumers. | AUD-036-SIM-020 |
| T-J17 | none | UNVERIFIED | Grouped allocation unavailable; [Maps auth](../../infra/modules/azure-maps.bicep#L35) disables local auth outside dev; deployed state unverified. | AUD-036-SIM-024 |
| T-J18 | none | UNVERIFIED | Grouped allocation unavailable; [API scaling](../../infra/main.bicep#L1099) not separate simulation KEDA integration. | AUD-036-SIM-020 |
| T-J19 | none | UNVERIFIED | Grouped allocation unavailable; [conditional smoke grant](../../infra/bicep/modules/cosmos-simulation-containers.bicep#L296) caller omits principal. | AUD-036-SIM-020 |
| T-J20 | none | UNVERIFIED | Grouped allocation unavailable; [APIM/breaker ADR](../../docs/aidr/decisions/ADR-036-004-apim-token-bucket-circuit-breaker.md#L23) not active quota enforcement. | AUD-036-SIM-006, AUD-036-SIM-024 |
| T-J21 | none | UNVERIFIED | Grouped allocation unavailable; [NEMA] metadata control exists, active work guard absent; reused source annotations not task definitions. | AUD-036-SIM-021, AUD-036-SIM-023 |
| T-J22 | none | UNVERIFIED | Grouped allocation unavailable; [A4-02](spec.md#L3907) explicitly revises wording, not effective resource isolation. | AUD-036-SIM-020, AUD-036-SIM-024 |
| T-J23 | none | UNVERIFIED | Grouped allocation unavailable; [C5] test-posture revision does not prove original infrastructure completion. | AUD-036-SIM-024 |
| T-K01 | none | UNVERIFIED | Generic K summary has no per-ID allocation; [AUDIT] structured logging not complete event/span contract. | AUD-036-SIM-019, AUD-036-SIM-023 |
| T-K02 | none | UNVERIFIED | Generic allocation unavailable; [API exporter](../../apps/api/app/main.py#L12) exists, correlated exported observations unverified. | AUD-036-SIM-019, AUD-036-SIM-024 |
| T-K03 | none | UNVERIFIED | Generic allocation unavailable; runbook searches found [general procedures](../../docs/disaster-response-hub/operator-runbooks.md#L1), not dedicated cap/DLQ operations. | AUD-036-SIM-023, AUD-036-SIM-024 |
| T-K04 | none | UNVERIFIED | Generic allocation unavailable; [quickstart](quickstart.md#L91) substantive guidance, no separately identified role-play guide or run. | AUD-036-SIM-023, AUD-036-SIM-024 |
| T-K05 | none | UNVERIFIED | Generic allocation unavailable; [CARVEOUT] manual-only workflow not current simulation-extension README/review completion. | AUD-036-SIM-026, AUD-036-SIM-023 |
| T-K06 | none | UNVERIFIED | Generic allocation unavailable; [changelog](../../CHANGELOG.md#L7) authorship supported, not unique original task acceptance. | AUD-036-SIM-023 |
| T-K07 | none | UNVERIFIED | Generic allocation unavailable; [threat model](../../docs/aidr/threat-model.md#L51) says cross-user403 against authorised replay-plus-audit contract. | AUD-036-SIM-009, AUD-036-SIM-023 |

### Amendment Implementation Phases

| Original task | Original state | Status | Inspected evidence and assessment | Follow-up |
| --- | --- | --- | --- | --- |
| T-L01 | none | PARTIAL | [PIPE] persists/publishes, lacks actual subscriber invocation/turn barrier and structured replies. | AUD-036-SIM-005 |
| T-L02 | none | PARTIAL | [ROUTE] calls orchestrator, but publisher-only acknowledgement and pre-persist202 make wire-in incomplete. | AUD-036-SIM-005 |
| T-L03 | none | PARTIAL | [SIGNALS] relocated repository implemented; strict readback, bulk/retries, TTL/session guarantees incomplete. | AUD-036-SIM-006, AUD-036-SIM-020 |
| T-L04 | none | PARTIAL | [Publisher factory](../../apps/api/app/services/simulation/event_hub_publisher.py#L181) supports AAD producer; unset namespace selects memory and hub naming mismatches infra. | AUD-036-SIM-005, AUD-036-SIM-020 |
| T-L05 | none | IMPLEMENTED | [Subscriber registry](../../apps/api/app/services/simulation/subscriber_registry.py#L1) closed hazard/resource/channel sets, copy isolation/unknown-kind validation. | - |
| T-L06 | none | PARTIAL | [PIPE] per-subscriber publish not turn-barrier agent call/semaphore; dependency-added completion note is not this acceptance. | AUD-036-SIM-005 |
| T-L07 | none | PARTIAL | [ROUTE] structured list exists without real replies/AIIMS aggregation; recent-signals completion note addresses another obligation. | AUD-036-SIM-005, AUD-036-SIM-013 |
| T-L08 | none | PARTIAL | [AUDIT] JCS success-array helper supported; durable consumer outcome/hash integration incomplete. | AUD-036-SIM-005, AUD-036-SIM-008 |
| T-L09 | none | PARTIAL | [PIPE-TEST] uses memory/overridden principal and nonempty delivery assertion, not emulator plus four actual consumers/six required assertions. | AUD-036-SIM-005, AUD-036-SIM-024 |
| T-L10 | none | PARTIAL | [PIPE-TEST] benign hazard only/nonempty list; no connected three-kind Schemathesis proof. | AUD-036-SIM-005, AUD-036-SIM-023 |
| T-M01 | none | PARTIAL | [AUTH] role check exists, simulation-definition membership omitted. | AUD-036-SIM-002 |
| T-M02 | none | PARTIAL | [ROUTE] four Depends guards present, inherited membership/context/auth production boundary incomplete. | AUD-036-SIM-002 |
| T-M03 | none | PARTIAL | [AUTH] denial writer exists; durability swallowed and denial scope not isolated from requested foreign simulation. | AUD-036-SIM-002, AUD-036-SIM-008 |
| T-M04 | none | PARTIAL | [RBAC-TEST] claims injected, checks header mismatch not real foreign UUID ownership; no full24 owner/audit assertions. | AUD-036-SIM-002 |
| T-N01 | none | PARTIAL | [Counter container](../../infra/bicep/modules/cosmos-simulation-containers.bicep#L200) correct local values, selected-root/AVM/deployment proof absent. | AUD-036-SIM-020 |
| T-N02 | none | PARTIAL | [SEQUENCE]/[AUDIT] ETag-style allocation exists; actual commit atomicity and failure coverage incomplete. | AUD-036-SIM-008 |
| T-N03 | none | PARTIAL | [Retry loop](../../apps/api/app/repositories/simulation_sequence_repository.py#L166) five attempts/backoff/jitter; required counters/histogram not actual instrumentation. | AUD-036-SIM-008, AUD-036-SIM-019 |
| T-N04 | none | PARTIAL | [AUDIT] exhaustion sentinel/rethrow, memory-only DLQ and swallowed route errors defeat fail-closed end-to-end. | AUD-036-SIM-008 |
| T-N05 | none | PARTIAL | [DLQ declaration](../../infra/bicep/modules/cosmos-simulation-containers.bicep#L249) no TTL/400RU; not selected-root wired or actual writer. | AUD-036-SIM-008, AUD-036-SIM-020 |
| T-N06 | none | PARTIAL | [Sequence assertions](../../tests/unit/test_simulation_sequence_repository_036.py#L34) test local concurrency/fakes, not five replicas sharing real conditional store. | AUD-036-SIM-008, AUD-036-SIM-024 |
| T-N07 | none | UNVERIFIED | [ALERT]/[WORKFLOW] not a recorded seven-day50rps Locust gap-free nightly gate; bounded load/workflow inspection found no qualifying run. | AUD-036-SIM-019, AUD-036-SIM-024 |
| T-N08 | none | PARTIAL | [AUDIT] separate sentinel exists, downstream export/lessons integrity warning and all-schema acceptance incomplete. | AUD-036-SIM-008, AUD-036-SIM-015 |
| T-O01 | none | PARTIAL | [Cache container](../../infra/bicep/modules/cosmos-simulation-containers.bicep#L223) TTL/autoscale present, actual [CACHE] document partition/ID incompatible. | AUD-036-SIM-009, AUD-036-SIM-020 |
| T-O02 | none | PARTIAL | [CACHE] relocated implementation exists; not pure-async Cosmos I/O or safely atomic replay reservation; unused by routes. | AUD-036-SIM-009 |
| T-O03 | none | IMPLEMENTED | [JCS] uses maintained RFC8785 when installed, SHA256 canonical body; dependency present. Production fallback should be removed with integration. | AUD-036-SIM-009 |
| T-O04 | none | PARTIAL | [CACHE] distinct route namespaces, but raw slash-bearing Cosmos ID needs opaque encoding. | AUD-036-SIM-009 |
| T-O05 | none | PARTIAL | [CACHE] lifecycle replay table supported; route unused. Original422 changed explicitly to409 by [contract](contracts/error-responses.md#L154). | AUD-036-SIM-009 |
| T-O06 | none | PARTIAL | [CACHE] body conflict/cross-user result supported, active HTTP/audit absent; current contract uses422 not task title409. | AUD-036-SIM-009, AUD-036-SIM-023 |
| T-O07 | none | PARTIAL | [CACHE] lifecycle conflict result supported, no actual response integration; current contract409 explicitly supersedes422 wording. | AUD-036-SIM-009, AUD-036-SIM-023 |
| T-O08 | none | PARTIAL | [Cache tests](../../tests/unit/test_simulation_idempotency_repository_036.py#L1) not mounted-route replay/TTL/cross-user concurrency proof; source completion note concerns fail-closed helper only. | AUD-036-SIM-009 |
| T-O09 | none | IMPLEMENTED | [JCS tests](../../tests/contract/test_jcs_canonicalisation_036.py#L1) contain concrete numeric/key-order/reference assertions; execution unverified. | - |
| T-P01 | none | PARTIAL | [STATE] separate lifecycle document, sync Cosmos calls and all-error-as-missing fallback; not canonical atomic state augmentation. | AUD-036-SIM-010, AUD-036-SIM-020 |
| T-P02 | none | PARTIAL | [ROUTE] injection guard exists; [CHAT] new invocations not guarded and refusal lineage incomplete. | AUD-036-SIM-010 |
| T-P03 | none | PARTIAL | [STATE]/[ROUTE] update active but swallow storage failure; idempotency integration absent. | AUD-036-SIM-009, AUD-036-SIM-010 |
| T-P04 | none | PARTIAL | [ROUTE] abort claims lessons started but no queue; unrelated watermark completion note does not satisfy task. | AUD-036-SIM-015 |
| T-P05 | none | PARTIAL | [Lifecycle tests](../../tests/integration/test_lifecycle_state_persistence_036.py#L46) local fixture/ETag examples not route->queue/cancel six-assertion workflow. | AUD-036-SIM-010, AUD-036-SIM-015 |
| T-Q01 | none | PARTIAL | [CAP] local acquisition/release five-cap API, no shared ETag state mutation. | AUD-036-SIM-011 |
| T-Q02 | none | PARTIAL | [CAP] memory list is not durable simulation_state.active_hazard_threads schema/counter. | AUD-036-SIM-011 |
| T-Q03 | none | PARTIAL | [CASCADE] optional cap lacks controller injection, candidate API mismatch. | AUD-036-SIM-011 |
| T-Q04 | none | PARTIAL | [CASCADE] logs degradation shape without actual target attachment/complete candidate audit. | AUD-036-SIM-011 |
| T-Q05 | none | PARTIAL | [LADDER] deterministic helper, connected host selection not effective; task's abbreviated ladder differs from binding spec ranking. | AUD-036-SIM-011, AUD-036-SIM-023 |
| T-Q06 | none | PARTIAL | [Property tests](../../tests/integration/test_cascade_thread_cap.py#L1) cap/annotation/release properties, not exact N-5 attached annotations across replicas. | AUD-036-SIM-011 |
| T-R01 | none | IMPLEMENTED | [LAYERS]/[LAYERS-TEST] canonical16 enum and equality assertions supported. | - |
| T-R02 | none | IMPLEMENTED | [MAP-PUBLISH] canonical vocabulary and unknown-layer rejection implemented as scoped publisher change; feed separate. | AUD-036-SIM-012 |
| T-R03 | none | PARTIAL | [Codegen](../../scripts/codegen/generate_map_overlay_taxonomy_ts.py#L1) guards array, TS type remains independently declared rather than canonical imported generation. | AUD-036-SIM-023 |
| T-R04 | none | PARTIAL | [MAP] non-point summary is expressly prohibited substitute for visual lines/polygons. | AUD-036-SIM-001 |
| T-R05 | none | PARTIAL | [MAP] Advice yellow corrected; unknown falls red, constants not canonical shared AWS source for every overlay/render. | AUD-036-SIM-001 |
| T-R06 | none | IMPLEMENTED | [LAYERS-TEST]/[CI] source equality/codegen check exists, execution unverified. | - |
| T-R07 | none | PARTIAL | [MAP-TEST] mocks shared map/asserts text, not LineLayer/PolygonLayer construction. | AUD-036-SIM-001 |
| T-R08 | none | PARTIAL | [Palette test](../../tests/unit/test_aws_colour_palette_036.py#L1) checks source literals, not four rendered tiers on real overlay layers. | AUD-036-SIM-001 |
| T-S01 | none | PARTIAL | [DRAFT] six-section helper exists; [LESSONS] legacy generator still used for persistence. | AUD-036-SIM-015 |
| T-S02 | none | PARTIAL | [DRAFT] timeline helper interleaves supplied objects; full durable inputs/lifecycle queue absent. | AUD-036-SIM-015 |
| T-S03 | none | PARTIAL | [DRAFT] response projection drops substantive response/hash/citation data required for reconstruction. | AUD-036-SIM-015 |
| T-S04 | none | PARTIAL | [DRAFT] lifecycle-only decisions omit required approval/clarification/refusal evidence. | AUD-036-SIM-015 |
| T-S05 | none | PARTIAL | [DRAFT] gap filter omits DLQ and several timeout/cancel/depth/real-action failures. | AUD-036-SIM-015 |
| T-S06 | none | PARTIAL | [DRAFT] deterministic count paragraph not recommendation-output/rationale-derived lessons; persisted path bypasses it. | AUD-036-SIM-015 |
| T-S07 | none | IMPLEMENTED | [Lessons ordering helper](../../apps/api/app/services/simulation/lessons_capture.py#L76) deterministic sort implementation; whole-blob reproducibility remains separate. | AUD-036-SIM-015 |
| T-S08 | none | PARTIAL | [AAR-TEST] supplied snapshots/not30-minute live session; excludes generated_at from equality. | AUD-036-SIM-015, AUD-036-SIM-024 |
| T-S09 | none | PARTIAL | [WORM] uploader exists, fails open on policy errors; ADR006 policy7y not proven by docstring/reference. | AUD-036-SIM-015 |
| T-T01 | none | IMPLEMENTED | [AIIMS] nine canonical sub-agents, primary and secondary lookup exists; human Control exception explicit. | - |
| T-T02 | none | IMPLEMENTED | [RECORD] derives primary/secondary tags from legacy roles and validates cap/disjointness. | - |
| T-T03 | none | IMPLEMENTED | [AUDIT] accepts/propagates AIIMS fields with validation; active invocation callers separate. | AUD-036-SIM-004 |
| T-T04 | none | IMPLEMENTED | [DRAFT] ordering uses AIIMS ordinal; connected full outcome remains partial. | AUD-036-SIM-015 |
| T-T05 | none | PARTIAL | [AIIMS tests](../../tests/unit/test_aiims_mapping_036.py#L1) exclude human-only Control reachability, while original task says every function reachable; preserve doctrine, clarify task. | AUD-036-SIM-023 |
| T-U01 | none | IMPLEMENTED | [Registry seed](../../infra/foundry/carveout-registry.json#L1) version1/empty array exactly matches scoped seed task. | AUD-036-SIM-026 |
| T-U02 | none | CONFLICT | [REGISTRY]/[REGISTRY-TEST] implement original weak fields, conflict with FR062 mandatory tenant/deployment/evidence/approver. | AUD-036-SIM-026 |
| T-U03 | none | MISSING | Scoped workflow/registry search finds [CARVEOUT] manual-only alternate, not required daily03:00/PR evaluation for spec registry. | AUD-036-SIM-026 |
| T-U04 | none | MISSING | Workflows/tools/API/registry marker search found descriptions/tests only, no active empty-with-reference CI failure. | AUD-036-SIM-026 |
| T-U05 | none | CONFLICT | [PLAN] no current decision16/canonical registry cross-reference despite task assertion; registry exists but ownership/document mapping unresolved. | AUD-036-SIM-023, AUD-036-SIM-026 |
| T-V01 | none | PARTIAL | [LIVELOG] correctly labelled polite component exists; axe acceptance not established by attribute-only [LIVELOG-TEST]. | AUD-036-SIM-013 |
| T-V02 | none | PARTIAL | [LIVELOG] subscribes optional EventSource names different from active Controller feed; unmounted. | AUD-036-SIM-013 |
| T-V03 | none | PARTIAL | [LIVELOG] hardcoded whitelist/default, not shared locale priority and translated prefix. | AUD-036-SIM-013 |
| T-V04 | none | PARTIAL | [LIVELOG-TEST] asserts attributes/constructor/cleanup, not mounted-page axe.run zero violations. | AUD-036-SIM-013, AUD-036-SIM-024 |
| T-W01 | none | IMPLEMENTED | [LOCALES]37-locale metadata catalog includes six remote languages and fallback chains; not active translations. | AUD-036-SIM-014 |
| T-W02 | none | IMPLEMENTED | [Jurisdiction profiles](../../apps/api/app/services/simulation/jurisdiction_locale_priority.py#L1) and fixture implement priority lookup/fallback; active integration separate. | AUD-036-SIM-014 |
| T-W03 | none | UNVERIFIED | [Speech catalog](../../apps/api/app/services/simulation/data/speech_prerender_catalog.json#L1) pointers/backlog flags not real render/staging upload or human audio approval. | AUD-036-SIM-014, AUD-036-SIM-024 |
| T-W04 | none | PARTIAL | [LOCALES-TEST] structural catalog/fallback/flag assertions, no actual staging asset reachability. | AUD-036-SIM-014, AUD-036-SIM-024 |
| T-X01 | none | PARTIAL | [TUPLES] new signature exists; old caller path retained, no location-aware active controller integration. | AUD-036-SIM-007 |
| T-X02 | none | IMPLEMENTED | [TUPLE-TEST] WA fire/flood/storm DFES-only fixture asserts task's narrow data requirement. | - |
| T-X03 | none | IMPLEMENTED | [TUPLE-TEST] QFD and not-QFES assertions support naming fix. | - |
| T-X04 | none | PARTIAL | [TUPLES] both CFA/FRV and explicit hints, not rural/declared-area discriminator or ambiguity refusal. | AUD-036-SIM-007 |
| T-X05 | none | PARTIAL | [TUPLES] SACFS/SAMFS membership, no location-based rural/metro selection. | AUD-036-SIM-007 |
| T-X06 | none | PARTIAL | [TUPLE-TEST] NT dual names/cyclone exists; Darwin/Katherine structural/rural active disambiguation absent. | AUD-036-SIM-007 |
| T-X07 | none | PARTIAL | [TUPLES] ESA fire order/AFP names, ACT medical bypasses ESA and intent fallback incomplete. | AUD-036-SIM-007 |
| T-X08 | none | PARTIAL | [TUPLE-TEST] membership/smoke cases not all31 checklist integration obligations (locale/audit/tenant/concurrent tests). | AUD-036-SIM-007, AUD-036-SIM-024 |
| T-Y01 | none | CONFLICT | [MATRIX] utility uses Logistics; original task/human matrix names Transport, absent canonical nine-name enum. | AUD-036-SIM-023 |
| T-Y02 | none | IMPLEMENTED | [MATRIX] hydrology Risk/Evac/Comms/Resource declared; real consumer integration separate. | AUD-036-SIM-011 |
| T-Y03 | none | IMPLEMENTED | [MATRIX] transport Evac/Comms/Resource declared. | AUD-036-SIM-011 |
| T-Y04 | none | IMPLEMENTED | [MATRIX] evacuation-centre Planning/Evac/Resource plus explicit alias declared. | AUD-036-SIM-011 |
| T-Y05 | none | IMPLEMENTED | [MATRIX] geohazard Risk/Evac/Resource declared. | AUD-036-SIM-011 |
| T-Y06 | none | PARTIAL | [Matrix assertions](../../tests/integration/test_cascade_matrix_expansion.py#L1) inspect static set, not actual fan-out; FR068 added real round-trip obligation. | AUD-036-SIM-011 |
| T-Z01 | none | PARTIAL | [ALERT] five named rules, incorrect gap metric/RU interpretation and selected-root disconnection. | AUD-036-SIM-019, AUD-036-SIM-020 |
| T-Z02 | none | PARTIAL | [GATE-TEST] static/helper assertions not measured30-minute synthetic scenario/all required SLIs. | AUD-036-SIM-016, AUD-036-SIM-024 |
| T-Z03 | none | PARTIAL | [WORKFLOW]/[CD] no actual full-SLI production eligibility dependency. | AUD-036-SIM-016 |
| T-Z04 | none | PARTIAL | [KQL] current seven-query configuration exists; producer/actual numeric query results unverified. | AUD-036-SIM-019 |
| T-Z05 | none | PARTIAL | [WORKFLOW] manual gate/tag job, not deploy-staging->full validation->actual production gating. | AUD-036-SIM-016 |

### AA Tasks Across All Amendment Cycles

| Original task | Original state | Status | Inspected evidence and assessment | Follow-up |
| --- | --- | --- | --- | --- |
| T-AA01 | none | PARTIAL | [ROUTE] loads600s history, catches failures to empty; [INJECT] contradiction result discarded, other paths not integrated. | AUD-036-SIM-006 |
| T-AA02 | none | PARTIAL | [AUDIT] hash-source enum exists but optional and absent at many active writes; no required preimage enforcement. | AUD-036-SIM-006, AUD-036-SIM-008 |
| T-AA03 | none | PARTIAL | Structured filter helper exists, active [INJECT] still calls pre-parse life_safety_gate without parsed confidence/category. | AUD-036-SIM-006 |
| T-AA04 | none | PARTIAL | Fallback resource600s differs from other freshness sources; [ROUTE] hardcodes600 for all categories rather than canonical mapping. | AUD-036-SIM-006, AUD-036-SIM-023 |
| T-AA05 | none | PARTIAL | [Public guard](../../apps/api/app/services/simulation/public_artefact_guard.py#L1) helper not used on three actual artifact routes; outcome roles fail open. | AUD-036-SIM-002 |
| T-AA06 | none | PARTIAL | Six files inspected: [runner](../../tests/integration/test_simulation_runner.py#L64) remains count-floor, [evacuation](../../tests/unit/test_evacuation_router.py#L28) changes>0 to>=1, [warning](../../tests/unit/test_warning_compliance.py#L160) skips assertion if regex misses. Not six robust boundary migrations. | AUD-036-SIM-024 |
| T-AA07 | none | PARTIAL | [CONTRACT] v0.3 schema objects exist; HTTP200/required-array/parity and generated SDK migration incomplete. | AUD-036-SIM-023 |
| T-AA08 | none | IMPLEMENTED | [Ack model](../../apps/api/app/api/routes/simulations_036.py#L103) typed item array/always-present bool and [dispatch model](../../apps/api/app/services/simulation/dispatch_status.py#L1) statuses/5s constant. | - |
| T-AA09 | none | PARTIAL | [AUDIT] entry25 builder/JCS/split views present; exception PII only truncated and durable write/failure semantics incomplete. | AUD-036-SIM-008 |
| T-AA10 | none | PARTIAL | [AUDIT] Pascal mapping helper exists; not applied by every actual historical reader/export consumer. | AUD-036-SIM-008, AUD-036-SIM-023 |
| T-AA11 | none | PARTIAL | [Route allow-list](../../apps/api/app/middleware/spec_036_routes.py#L1) and [ERRORS] scope match exist, structured error types/headers lost. | AUD-036-SIM-023 |
| T-AA12 | none | PARTIAL | [Audit schema test](../../tests/contract/test_audit_envelope_schema_2020_12.py#L37) current26 check but common discriminator/strict OpenAPI response parity still incomplete. | AUD-036-SIM-023 |
| T-AA13 | none | PARTIAL | [PIPE] fresh per-edge UUID/derived hex fields, no actual child-span creation/session propagation or subscriber call. | AUD-036-SIM-005, AUD-036-SIM-019 |
| T-AA14 | none | PARTIAL | [ROUTE]/[PIPE] degraded flag/statuses implemented, but acknowledges publisher and returns202 for pre-persist failure; audit failures swallowed. | AUD-036-SIM-005, AUD-036-SIM-008 |
| T-AA15 | none | PARTIAL | [AUDIT] JCS shared-array helper, [CACHE] not integrated; no unchanged degraded replay. | AUD-036-SIM-009 |
| T-AA16 | none | PARTIAL | [KQL]/[KQL-TEST] current Z6/Z7 schemas/filter/counts exist, runtime event producers unlocated. | AUD-036-SIM-019 |
| T-AA17 | none | PARTIAL | [GATE]30-sample/ordinary breach checks; series/finite-number/fresh-evidence validation incomplete. | AUD-036-SIM-018 |
| T-AA18 | none | PARTIAL | [Observability declarations](../../infra/bicep/modules/observability-alerts.bicep#L45) and workbook exist; selected-root/promote-SLI integration incomplete. | AUD-036-SIM-019, AUD-036-SIM-020 |
| T-AA19 | none | PARTIAL | [SMOKE] loops POST requests now but invalid chat-text shape/slug, no actual qualified metric samples. | AUD-036-SIM-017 |
| T-AA20 | none | PARTIAL | [MATRIX]/[CASCADE] canonical targets, YAML removal, alias and static tests implemented; actual controller round-trip absent. | AUD-036-SIM-011 |
| T-AA21 | none | IMPLEMENTED | [AUDIT] caller sequence ignored with warning; depth-refusal placeholder removed. Dense persistence is separate FR048 defect. | AUD-036-SIM-008 |
| T-AA22 | none | PARTIAL | [Migration ledger](contracts/openapi-changelog.md#L12)/[changelog](../../CHANGELOG.md#L22) authored; mislabelled FR/enums and generated consumer migration evidence incomplete. | AUD-036-SIM-023, AUD-036-SIM-024 |
| T-AA23 | none | IMPLEMENTED | [ADR010](../../docs/aidr/decisions/ADR-036-010-cycle-2-amendment-cycle.md#L83)/[changelog](../../CHANGELOG.md#L35) correct Z6 bands/helper citation. | - |
| T-AA24 | none | IMPLEMENTED | [Threshold drift test](../../tests/docs/test_adr_036_010_threshold_drift.py#L1) contains numeric configuration/ADR comparison. | - |
| T-AA25 | none | IMPLEMENTED | [Symbol citation test](../../tests/docs/test_adr_036_010_symbol_citations.py#L1) contains importlib resolution assertions; not executed. | - |
| T-AA26 | none | PARTIAL | [Entry26 schema](contracts/audit-envelope.md#L672) and count updated, [common discriminator](contracts/audit-envelope.md#L31) omits entry26. | AUD-036-SIM-023 |
| T-AA27 | none | IMPLEMENTED | [Canonicalisation contract](contracts/sli-thresholds.md#L467) defines six steps/signatures/errors/universal scope. | - |
| T-AA28 | none | IMPLEMENTED | [Z6/Z7 canonical clauses](contracts/sli-thresholds.md#L230) include smoke-tenant/env filters. | - |
| T-AA29 | none | IMPLEMENTED | [FR071](spec.md#L3625), [FR072](spec.md#L3647), [FR073](spec.md#L3666), [SC014](spec.md#L3804) propagate required textual changes. | - |
| T-AA30 | none | IMPLEMENTED | [Canonicaliser](../../tests/contract/_kql_canonicaliser.py#L1) implements selected pure normalization/public helpers/path override; KQL semantics separate. | - |
| T-AA31 | none | IMPLEMENTED | [Golden fixtures](../../tests/contract/test_kql_canonicaliser_unit.py#L1) cover normalization/idempotence/determinism in source. | - |
| T-AA32 | none | IMPLEMENTED | [KQL-CANON] parametrises every declared SLI without required-surface skip/subset. | - |
| T-AA33 | none | IMPLEMENTED | [KQL-TEST] augments schema assertions with canonical comparison. | - |
| T-AA34 | none | PARTIAL | [KQL] Z6 dimensions/Z7 clocks/bands corrected; one-time audit/run not attributable and downstream gate loses dimensions. | AUD-036-SIM-018, AUD-036-SIM-024 |
| T-AA35 | none | PARTIAL | [WORKFLOW] calls helper and propagates failure, but only Z6/Z7 and unsafe collation; production not bound. | AUD-036-SIM-016, AUD-036-SIM-018 |
| T-AA36 | none | PARTIAL | [SMOKE] OIDC+POST replaces no-op loop; invalid endpoint body and simulation ID block useful traffic. | AUD-036-SIM-017 |
| T-AA37 | none | IMPLEMENTED | [Workflow](../../.github/workflows/staging-promotion.yml#L1) queues common workflow/ref runs with cancel-in-progress false. | - |
| T-AA38 | none | PARTIAL | [A4-02 supersession](spec.md#L3907) replaces exclusive partition scope; [INFRA] conditional role caller omits principal, posture parity not proven. | AUD-036-SIM-020 |
| T-AA39 | none | PARTIAL | [SMOKE-TEST] revised database-scope source assertions; not emitted full-root role list or effective isolation. | AUD-036-SIM-020 |
| T-AA40 | none | PARTIAL | [Gate sink](../../tests/staging_gates.py#L144) constructs/logs/local JSONL, not typed allocator-backed durable transport. | AUD-036-SIM-018 |
| T-AA41 | none | PARTIAL | [Concurrent tests](../../tests/integration/test_staging_promotion_concurrency.py#L66) distinct captured objects/UUIDs, not two durable envelopes/process failures. | AUD-036-SIM-018, AUD-036-SIM-024 |
| T-AA42 | none | PARTIAL | [GATE-TEST] four red helper fixtures, no actual CD/tagging boundary prevention proof. | AUD-036-SIM-016, AUD-036-SIM-018 |
| T-AA43 | none | IMPLEMENTED | [KQL] current Z7 extends model_deployment between tenant and staging filter as requested. | - |
| T-AA44 | none | IMPLEMENTED | [Canonical Z7](contracts/sli-thresholds.md#L276) contains symmetric definition. | - |
| T-AA45 | none | UNVERIFIED | [KQL-CANON] source asserts all-seven equality; verification-only task needs attributable current run. | AUD-036-SIM-024 |
| T-AA46 | none | IMPLEMENTED | [KQL-WALK] dynamic scaffold/base-table checks exist; interim NotImplementedError replaced by walker per T-AA47. | - |
| T-AA47 | none | PARTIAL | [KQL-WALK] implements lexer and union rejection, but forward-let/removed-column scope invalid. | AUD-036-SIM-025 |
| T-AA48 | none | UNVERIFIED | [KQL-WALK] seven parameters exist; verification-only GREEN task not established by static source. | AUD-036-SIM-024 |
| T-AA49 | none | IMPLEMENTED | [FR073](spec.md#L3666) includes author-time column-resolution requirement. | - |
| T-AA50 | none | IMPLEMENTED | [ADR011](../../docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md#L172) current wording corrects scope/cites control/backlog; approval separate. | - |
| T-AA51 | none | IMPLEMENTED | [Scope-string test](../../tests/contract/test_smoke_tenant_isolation.py#L174) locks database-level literal; not effective tenant isolation proof. | - |
| T-AA52 | none | IMPLEMENTED | [SMOKE-TEST] comment/control/backlog assertions exist; optional posture explicitly superseded by [Cycle5Q1](spec.md#L5496). | - |
| T-AA53 | none | IMPLEMENTED | [A4-02](spec.md#L3907) explicitly preserves/supersedes original exclusive-scope mirror; locked siblings not silently changed. | - |
| T-AA54 | none | IMPLEMENTED | [Changelog](../../CHANGELOG.md#L13) Cycle4 Added/Changed sections present; external issue existence unverified. | - |
| T-AA55 | none | UNVERIFIED | [Local issue84 citation](../../CHANGELOG.md#L15) and ADR link exist, no fetched issue/creation/label/open-state receipt. | AUD-036-SIM-024 |
| T-AA56 | none | UNVERIFIED | [Cycle4 status](tasks.md#L2509) claims full posture; current full-suite run unavailable; later counts explicitly supersede minimal option. | AUD-036-SIM-024 |
| T-AA57 | none | IMPLEMENTED | [Role comment](../../infra/bicep/modules/cosmos-simulation-containers.bicep#L305) current scope-first four-clause correction present; no scope edit by this audit. | - |
| T-AA58 | none | IMPLEMENTED | [SMOKE-TEST] two selected lower()+in absence assertions present, existing test reused. | - |
| T-AA59 | none | IMPLEMENTED | [Test header](../../tests/contract/test_smoke_tenant_isolation.py#L162)/[SMOKE-TEST] REQUIRED wording present without test marker change. | - |
| T-AA60 | none | IMPLEMENTED | [Changelog](../../CHANGELOG.md#L7) Cycle5 Added/Changed block and provenance present; plan Changed-only conflict separately noted. | AUD-036-SIM-023 |
| T-AA61 | none | UNVERIFIED | [C5] claims22 contract/3400 total/lint/scope equality; no attributable current outputs and no execution performed. | AUD-036-SIM-024 |

## Checklist Coverage

Each row preserves its file-scoped original ID/state. Checked items are reassessed, not accepted on checkbox authority. `IMPLEMENTED` with "definition" or "artifact" credits that requested authored surface only; corresponding FR/scenario rows still govern operational implementation. A test-source assertion is not a passing execution. All original checkboxes remain unchanged.

### Accessibility and CALD

| Item | Original state | Status | Assessment and evidence | Follow-up |
| --- | --- | --- | --- | --- |
| [CHK001](checklists/accessibility-and-cald.md#L15) | [x] | PARTIAL | Every text render: [WATERMARK] not pre-persistence/approval integrated. | AUD-036-SIM-014 |
| [CHK002](checklists/accessibility-and-cald.md#L16) | [x] | PARTIAL | English-first bilingual output absent on active smaller table path [LOCALES]. | AUD-036-SIM-014 |
| [CHK003](checklists/accessibility-and-cald.md#L17) | [x] | PARTIAL | English literal helper exists, every output not guaranteed [WATERMARK]. | AUD-036-SIM-014 |
| [CHK004](checklists/accessibility-and-cald.md#L18) | [x] | PARTIAL | Versioned table exists; required expanded curated text not used [LOCALES]. | AUD-036-SIM-014 |
| [CHK005](checklists/accessibility-and-cald.md#L19) | [x] | PARTIAL | Actual persistence precedes watermark handler [COMMS]. | AUD-036-SIM-014 |
| [CHK006](checklists/accessibility-and-cald.md#L20) | [x] | PARTIAL | Curated helper avoids model translation, disconnected active outputs [WATERMARK]. | AUD-036-SIM-014 |
| [CHK007](checklists/accessibility-and-cald.md#L24) | [x] | PARTIAL | Single supplied audio clip not guaranteed bilingual sequence [LOCALES-TEST]. | AUD-036-SIM-014 |
| [CHK008](checklists/accessibility-and-cald.md#L25) | [x] | PARTIAL | English then locale spoken ordering not active contract [LOCALES-TEST]. | AUD-036-SIM-014 |
| [CHK009](checklists/accessibility-and-cald.md#L26) | [x] | UNVERIFIED | Metadata text not byte/waveform proof of English spoken prefix [LOCALES-TEST]. | AUD-036-SIM-024 |
| [CHK010](checklists/accessibility-and-cald.md#L27) | [x] | PARTIAL | Versioned audio catalog exists, actual approved assets unverified [LOCALES]. | AUD-036-SIM-014, AUD-036-SIM-024 |
| [CHK011](checklists/accessibility-and-cald.md#L28) | [x] | PARTIAL | Active text/audio sets not both aligned to37-locale metadata [LOCALES]. | AUD-036-SIM-014 |
| [CHK012](checklists/accessibility-and-cald.md#L29) | [x] | PARTIAL | Helper path no model prefix generation, active lifecycle binding absent [WATERMARK]. | AUD-036-SIM-014 |
| [CHK013](checklists/accessibility-and-cald.md#L33) | [x] | PARTIAL | Missing-text fallback helper not enforced on every persisted artifact [WATERMARK]. | AUD-036-SIM-014 |
| [CHK014](checklists/accessibility-and-cald.md#L34) | [x] | PARTIAL | Missing-audio fallback metadata not active spoken output proof [LOCALES-TEST]. | AUD-036-SIM-014 |
| [CHK015](checklists/accessibility-and-cald.md#L35) | [x] | PARTIAL | Deterministic English helper preserved, full text/audio consumer integration lacking [WATERMARK]. | AUD-036-SIM-014 |
| [CHK016](checklists/accessibility-and-cald.md#L36) | [x] | PARTIAL | Channel discriminator schema exists, audit emit/combined correlation incomplete [AUDIT]. | AUD-036-SIM-014 |
| [CHK017](checklists/accessibility-and-cald.md#L40) | [x] | PARTIAL | 37 metadata locales not30 actual curated text/audio translations [LOCALES]. | AUD-036-SIM-014 |
| [CHK018](checklists/accessibility-and-cald.md#L41) | [x] | UNVERIFIED | Shared governance approval asserted, no attributable review/sign-off record [SWEEP]. | AUD-036-SIM-024 |
| [CHK019](checklists/accessibility-and-cald.md#L42) | [x] | PARTIAL | All render channels not routed through shared watermark [COMMS]/[WATERMARK]. | AUD-036-SIM-014 |
| [CHK020](checklists/accessibility-and-cald.md#L43) | [x] | PARTIAL | Git-pinned table/hash helper not per-artifact immutable version capture [AUDIT]. | AUD-036-SIM-014 |
| [CHK021](checklists/accessibility-and-cald.md#L44) | [x] | PARTIAL | Table hash/update helper not complete active typed audit flow [AUDIT]. | AUD-036-SIM-014 |
| [CHK022](checklists/accessibility-and-cald.md#L48) | [x] | PARTIAL | AWS names exist; all-jurisdiction active receipts/prefix incomplete [COMMS]. | AUD-036-SIM-003, AUD-036-SIM-014 |
| [CHK023](checklists/accessibility-and-cald.md#L49) | [x] | PARTIAL | Every tier/render locale unproven by helper [WATERMARK]. | AUD-036-SIM-014 |
| [CHK024](checklists/accessibility-and-cald.md#L50) | [x] | PARTIAL | All-channel prefix/safety missing at direct SDK predicate [COMMS]. | AUD-036-SIM-003 |
| [CHK025](checklists/accessibility-and-cald.md#L51) | [x] | PARTIAL | Directional wind/AWS overlay not actually rendered [MAP]. | AUD-036-SIM-001 |
| [CHK026](checklists/accessibility-and-cald.md#L55) | [x] | IMPLEMENTED | Named locale scenarios explicitly authored [US5](spec.md#L2030). | - |
| [CHK027](checklists/accessibility-and-cald.md#L56) | [x] | PARTIAL | Auslan narrative scope defined, active catalog/audio parity not established [LOCALES-TEST]. | AUD-036-SIM-014 |
| [CHK028](checklists/accessibility-and-cald.md#L57) | [x] | PARTIAL | Supported-locale English-first sequence not guaranteed [WATERMARK]. | AUD-036-SIM-014 |
| [CHK029](checklists/accessibility-and-cald.md#L58) | [x] | PARTIAL | Generic RTL preview is not connected simulation bilingual ordering [LIVELOG]. | AUD-036-SIM-013, AUD-036-SIM-014 |
| [CHK030](checklists/accessibility-and-cald.md#L59) | [x] | PARTIAL | ARIA helper metadata does not prove active PDF/live-log reading order [LIVELOG]. | AUD-036-SIM-013, AUD-036-SIM-014 |
| [CHK031](checklists/accessibility-and-cald.md#L60) | [ ] | UNVERIFIED | Explicit prosody QA deferral, no rendered asset/human evidence [LOCALES-TEST]. | AUD-036-SIM-024 |
| [CHK032](checklists/accessibility-and-cald.md#L64) | [x] | CONFLICT | Source resolution credits11-locale MVP for30-locale obligation; no supersession reducing target [LOCALES]. | AUD-036-SIM-014, AUD-036-SIM-023 |
| [CHK033](checklists/accessibility-and-cald.md#L65) | [x] | PARTIAL | Stub-literal sweep not byte-prefix checks on every real emitted artifact [COMMS]. | AUD-036-SIM-003, AUD-036-SIM-024 |
| [CHK034](checklists/accessibility-and-cald.md#L66) | [ ] | UNVERIFIED | Waveform/staging QA explicitly deferred; pointer metadata not rendered audio [LOCALES-TEST]. | AUD-036-SIM-024 |
| [CHK035](checklists/accessibility-and-cald.md#L67) | [x] | PARTIAL | Helper fallback tests not full active text/audio artifact audit coverage [WATERMARK]. | AUD-036-SIM-014 |
| [CHK036](checklists/accessibility-and-cald.md#L76) | [ ] | PARTIAL | Dedicated component exists but unmounted [LIVELOG]/[MAP-PAGE]. | AUD-036-SIM-013 |
| [CHK037](checklists/accessibility-and-cald.md#L79) | [ ] | PARTIAL | Both accessible surfaces not mounted simultaneously [MAP-PAGE]. | AUD-036-SIM-013 |
| [CHK038](checklists/accessibility-and-cald.md#L82) | [ ] | PARTIAL | Local whitelist not shared three-step locale resolver [LIVELOG]. | AUD-036-SIM-013 |
| [CHK039](checklists/accessibility-and-cald.md#L86) | [ ] | PARTIAL | No combined audio/live-log watermark audit correlation on active page [AUDIT]/[LIVELOG]. | AUD-036-SIM-013, AUD-036-SIM-014 |
| [CHK040](checklists/accessibility-and-cald.md#L91) | [ ] | PARTIAL | Client prepending is not server-side receipt/audit guard [LIVELOG]/[CHAT]. | AUD-036-SIM-003, AUD-036-SIM-013 |
| [CHK041](checklists/accessibility-and-cald.md#L95) | [ ] | PARTIAL | Attribute/constructor assertions not every-render mounted-page axe [LIVELOG-TEST]. | AUD-036-SIM-013 |
| [CHK042](checklists/accessibility-and-cald.md#L102) | [ ] | PARTIAL | 37 metadata locales not30 active text/audio table entries [LOCALES]. | AUD-036-SIM-014 |
| [CHK043](checklists/accessibility-and-cald.md#L106) | [ ] | PARTIAL | Six remote locales metadata/backlog only, missing approved assets [LOCALES-TEST]. | AUD-036-SIM-014 |
| [CHK044](checklists/accessibility-and-cald.md#L109) | [ ] | IMPLEMENTED | [Jurisdiction profile](../../apps/api/app/services/simulation/jurisdiction_locale_priority.py#L1) plus metadata covers all eight/NT priority. | - |
| [CHK045](checklists/accessibility-and-cald.md#L112) | [ ] | IMPLEMENTED | [Catalog flags](../../apps/api/app/services/simulation/data/speech_prerender_catalog.json#L1) explicitly mark blockers; not satisfied assets. | - |
| [CHK046](checklists/accessibility-and-cald.md#L118) | [ ] | PARTIAL | Advice corrected yellow, unknown falls red/not unified all-render palette [MAP]. | AUD-036-SIM-001 |
| [CHK047](checklists/accessibility-and-cald.md#L122) | [ ] | PARTIAL | Source palette tests not four rendered tier families across five layers [MAP-TEST]. | AUD-036-SIM-001 |

### Audit and Provenance

| Item | Original state | Status | Assessment and evidence | Follow-up |
| --- | --- | --- | --- | --- |
| [CHK001](checklists/audit-and-provenance.md#L14) | [x] | PARTIAL | Allocation-before-validation/create and memory fallback violate dense durable audit [AUDIT]. | AUD-036-SIM-008 |
| [CHK002](checklists/audit-and-provenance.md#L15) | [x] | PARTIAL | Export formatter exists, actual durable authorised reader absent [EXPORT]. | AUD-036-SIM-015 |
| [CHK003](checklists/audit-and-provenance.md#L16) | [x] | PARTIAL | Some refusals emitted, others swallowed/unlinked [ROUTE]/[AUDIT]. | AUD-036-SIM-008 |
| [CHK004](checklists/audit-and-provenance.md#L17) | [x] | UNVERIFIED | Schema-governance approval not established by current enum/source [SWEEP]. | AUD-036-SIM-024 |
| [CHK005](checklists/audit-and-provenance.md#L21) | [x] | PARTIAL | Active turn/invocation/state correlation incomplete [CHAT]/[PIPE]. | AUD-036-SIM-004, AUD-036-SIM-008 |
| [CHK006](checklists/audit-and-provenance.md#L22) | [x] | PARTIAL | Model omits full payload/citation fields and active writer [RECORD]. | AUD-036-SIM-004 |
| [CHK007](checklists/audit-and-provenance.md#L23) | [x] | PARTIAL | Timeout logs, no active typed audit/correlation [INVOKER]. | AUD-036-SIM-004 |
| [CHK008](checklists/audit-and-provenance.md#L24) | [x] | PARTIAL | Filtering/degraded flag present, typed violation audit absent [ADAPTER]. | AUD-036-SIM-004 |
| [CHK009](checklists/audit-and-provenance.md#L25) | [x] | PARTIAL | Routing helpers not producing actual controller decisions [CHAT]/[TUPLES]. | AUD-036-SIM-007 |
| [CHK010](checklists/audit-and-provenance.md#L26) | [x] | PARTIAL | Fingerprint returned, active persistence/aggregation discards it [DISPATCH]/[CHAT]. | AUD-036-SIM-004, AUD-036-SIM-008 |
| [CHK011](checklists/audit-and-provenance.md#L30) | [x] | PARTIAL | Missing injecting user/source, optional correlation/GPS validation [SIGNAL]. | AUD-036-SIM-006 |
| [CHK012](checklists/audit-and-provenance.md#L31) | [x] | PARTIAL | Refusal lacks post-parse class/confidence; raw-text rule conflicts with PII minimisation [INJECT]. | AUD-036-SIM-006, AUD-036-SIM-023 |
| [CHK013](checklists/audit-and-provenance.md#L32) | [x] | PARTIAL | Persisted candidate correlation not assigned from route [SIGNAL]/[ROUTE]. | AUD-036-SIM-006 |
| [CHK014](checklists/audit-and-provenance.md#L33) | [x] | PARTIAL | Singleton extraction cannot meet multi-signal shared-turn rule [INJECT]. | AUD-036-SIM-006 |
| [CHK015](checklists/audit-and-provenance.md#L34) | [x] | PARTIAL | Published event not observed consumption/stale lifecycle [PIPE]. | AUD-036-SIM-005, AUD-036-SIM-012 |
| [CHK016](checklists/audit-and-provenance.md#L35) | [x] | PARTIAL | Contradiction IDs separate from persisted signal [INJECT]/[ROUTE]. | AUD-036-SIM-006 |
| [CHK017](checklists/audit-and-provenance.md#L36) | [x] | PARTIAL | Freshness fields not active stale-state rendering/consumption [SIGNAL]/[MAP]. | AUD-036-SIM-006, AUD-036-SIM-012 |
| [CHK018](checklists/audit-and-provenance.md#L37) | [x] | PARTIAL | Handler scrubs text, other logs/exceptions/transcript paths not consistently redacted [INJECT]/[AUDIT]. | AUD-036-SIM-006 |
| [CHK019](checklists/audit-and-provenance.md#L38) | [x] | PARTIAL | REST supplies no circuit_probe [ROUTE]. | AUD-036-SIM-006 |
| [CHK020](checklists/audit-and-provenance.md#L39) | [x] | PARTIAL | Refusal enum/artifact exists, all required reasons/budgets not enforced [INJECT]. | AUD-036-SIM-006 |
| [CHK021](checklists/audit-and-provenance.md#L43) | [x] | PARTIAL | No controller injection branch/consumption barrier [CHAT]/[PIPE]. | AUD-036-SIM-005 |
| [CHK022](checklists/audit-and-provenance.md#L44) | [x] | PARTIAL | No singular ordered real invocation envelope [CHAT]. | AUD-036-SIM-005 |
| [CHK023](checklists/audit-and-provenance.md#L45) | [x] | CONFLICT | Strict controller-only wording versus explicitly allowed direct REST [TOOLS]/[ROUTE]; common service needed. | AUD-036-SIM-023 |
| [CHK024](checklists/audit-and-provenance.md#L49) | [x] | PARTIAL | Ambiguity audit helper disconnected from [CHAT]. | AUD-036-SIM-007 |
| [CHK025](checklists/audit-and-provenance.md#L50) | [x] | PARTIAL | No active step5 jurisdiction clarify audit [TUPLES]/[CHAT]. | AUD-036-SIM-007 |
| [CHK026](checklists/audit-and-provenance.md#L51) | [x] | PARTIAL | Inference step not carried through active routing [CHAT]. | AUD-036-SIM-007 |
| [CHK027](checklists/audit-and-provenance.md#L52) | [x] | PARTIAL | Client/server mismatch audit not integrated [CHAT]. | AUD-036-SIM-007 |
| [CHK028](checklists/audit-and-provenance.md#L53) | [x] | PARTIAL | Server-winning inference absent from active dispatch [TUPLES]. | AUD-036-SIM-007 |
| [CHK029](checklists/audit-and-provenance.md#L57) | [x] | PARTIAL | Cascade target-thread actual writes absent [CASCADE]. | AUD-036-SIM-011 |
| [CHK030](checklists/audit-and-provenance.md#L58) | [x] | PARTIAL | Origin field exists, actual parent/target subtree chain incomplete [SIGNAL]/[CASCADE]. | AUD-036-SIM-011 |
| [CHK031](checklists/audit-and-provenance.md#L59) | [x] | PARTIAL | Denial logs selection but no attachment/complete candidate back-pointer [CASCADE]. | AUD-036-SIM-011 |
| [CHK032](checklists/audit-and-provenance.md#L60) | [x] | PARTIAL | Persisted outcome bypasses complete target-thread evidence [LESSONS]. | AUD-036-SIM-015 |
| [CHK033](checklists/audit-and-provenance.md#L61) | [x] | PARTIAL | Deterministic helper [LADDER], no connected replay candidates/attachment. | AUD-036-SIM-011 |
| [CHK034](checklists/audit-and-provenance.md#L62) | [x] | PARTIAL | Candidate set/selected-host full audit not effective [CASCADE]. | AUD-036-SIM-011 |
| [CHK035](checklists/audit-and-provenance.md#L66) | [x] | PARTIAL | Local cap/refusal shape exists, no active shared counter [CAP]. | AUD-036-SIM-011 |
| [CHK036](checklists/audit-and-provenance.md#L67) | [x] | PARTIAL | No guaranteed sixth-thread active refusal/annotation [CAP]/[CASCADE]. | AUD-036-SIM-011 |
| [CHK037](checklists/audit-and-provenance.md#L68) | [x] | PARTIAL | Distinct typed categories exist, actual user/cascade handling incomplete [CASCADE]. | AUD-036-SIM-011 |
| [CHK038](checklists/audit-and-provenance.md#L72) | [x] | PARTIAL | Builder supplies receipt fields, real channel blocking/audits incomplete [COMMS]/[AUDIT]. | AUD-036-SIM-003 |
| [CHK039](checklists/audit-and-provenance.md#L73) | [x] | PARTIAL | Publication boundary/direct SDK not uniformly guarded/audited [COMMS]. | AUD-036-SIM-003 |
| [CHK040](checklists/audit-and-provenance.md#L74) | [x] | PARTIAL | Some text refusal, no all-federal-path typed record [CHAT]/[INJECT]. | AUD-036-SIM-003, AUD-036-SIM-006 |
| [CHK041](checklists/audit-and-provenance.md#L78) | [x] | PARTIAL | Helper path/channel fields exist, all actual text/audio fallbacks not audited [WATERMARK]. | AUD-036-SIM-014 |
| [CHK042](checklists/audit-and-provenance.md#L79) | [x] | PARTIAL | Locale/artifact metadata not guaranteed at active emission [WATERMARK]. | AUD-036-SIM-014 |
| [CHK043](checklists/audit-and-provenance.md#L80) | [x] | PARTIAL | Git version not per-artifact guaranteed translated bytes/hash [AUDIT]. | AUD-036-SIM-014 |
| [CHK044](checklists/audit-and-provenance.md#L81) | [x] | PARTIAL | Table update helper alone not durable governance audit [AUDIT]. | AUD-036-SIM-014 |
| [CHK045](checklists/audit-and-provenance.md#L85) | [x] | PARTIAL | generated_at/retention failure breaks full deterministic recovery [LESSONS]/[WORM]. | AUD-036-SIM-015 |
| [CHK046](checklists/audit-and-provenance.md#L86) | [x] | SUPERSEDED | Five-section definition strengthened to six by [AmendmentI](spec.md#L3200), participant summary added. | AUD-036-SIM-015 |
| [CHK047](checklists/audit-and-provenance.md#L87) | [x] | UNVERIFIED | Seven-year deployed retention not proven by helper/config; failure swallowed [WORM]. | AUD-036-SIM-015, AUD-036-SIM-024 |
| [CHK048](checklists/audit-and-provenance.md#L96) | [ ] | PARTIAL | Repository allocation exists, committed gap-free durable stream not [AUDIT]/[SEQUENCE]. | AUD-036-SIM-008 |
| [CHK049](checklists/audit-and-provenance.md#L101) | [ ] | PARTIAL | Five-step503/DLQ/cache/budget/integrity protocol not connected [AUDIT]/[CACHE]. | AUD-036-SIM-008, AUD-036-SIM-009 |
| [CHK050](checklists/audit-and-provenance.md#L110) | [ ] | PARTIAL | Separate sentinel buffer not complete typed uncertainty contract/store [AUDIT]. | AUD-036-SIM-008 |
| [CHK051](checklists/audit-and-provenance.md#L113) | [ ] | PARTIAL | Export/lessons do not merge durable DLQ integrity warning [EXPORT]/[LESSONS]. | AUD-036-SIM-015 |
| [CHK052](checklists/audit-and-provenance.md#L119) | [ ] | PARTIAL | Accepted/refused/fallback complete hash missing [ROUTE]/[AUDIT]. | AUD-036-SIM-006, AUD-036-SIM-008 |
| [CHK053](checklists/audit-and-provenance.md#L123) | [ ] | PARTIAL | hash-source optional on active writes [AUDIT]. | AUD-036-SIM-008 |
| [CHK054](checklists/audit-and-provenance.md#L127) | [ ] | PARTIAL | Required source-specific raw/canonical/system preimage not enforced [INJECT]/[AUDIT]. | AUD-036-SIM-006 |
| [CHK055](checklists/audit-and-provenance.md#L135) | [ ] | PARTIAL | 26 current variants require full provenance; optional common fields insufficient [AUDIT]. | AUD-036-SIM-008, AUD-036-SIM-023 |
| [CHK056](checklists/audit-and-provenance.md#L141) | [ ] | PARTIAL | No unified both-channel correlation at active emission [LIVELOG]/[WATERMARK]. | AUD-036-SIM-013, AUD-036-SIM-014 |
| [CHK057](checklists/audit-and-provenance.md#L146) | [ ] | IMPLEMENTED | [Watermark schema](../../packages/domain/src/domain/models/telemetry_injection_audit_entry.py#L323) has delivery_channel/resolved_locale. | - |
| [CHK058](checklists/audit-and-provenance.md#L152) | [ ] | PARTIAL | Pause/resume/abort writes omit consistent idempotency/request lineage [ROUTE]. | AUD-036-SIM-009, AUD-036-SIM-010 |
| [CHK059](checklists/audit-and-provenance.md#L156) | [ ] | PARTIAL | Injection refused, chat/sub-agent work bypasses guard [ROUTE]/[CHAT]. | AUD-036-SIM-010 |
| [CHK060](checklists/audit-and-provenance.md#L161) | [ ] | PARTIAL | Contract registered, [CACHE] result unused; [ERRORS] destroys specific detail. | AUD-036-SIM-009, AUD-036-SIM-023 |
| [CHK061](checklists/audit-and-provenance.md#L167) | [ ] | PARTIAL | Hazard-only local filter not durable typed thread-state document [CAP]. | AUD-036-SIM-011 |
| [CHK062](checklists/audit-and-provenance.md#L170) | [ ] | PARTIAL | Missing effective candidates/real annotation and provenance [CASCADE]. | AUD-036-SIM-011 |
| [CHK063](checklists/audit-and-provenance.md#L177) | [ ] | PARTIAL | RBAC incomplete and no cache caller before action [AUTH]/[CACHE]. | AUD-036-SIM-002, AUD-036-SIM-009 |
| [CHK064](checklists/audit-and-provenance.md#L181) | [ ] | PARTIAL | Helper BodyConflict not mounted422/problem+audit response [CACHE]. | AUD-036-SIM-009 |
| [CHK065](checklists/audit-and-provenance.md#L184) | [ ] | PARTIAL | No503 replay caching/exactly-once durable DLQ [CACHE]/[AUDIT]. | AUD-036-SIM-008, AUD-036-SIM-009 |

### Graceful Degradation

| Item | Original state | Status | Assessment and evidence | Follow-up |
| --- | --- | --- | --- | --- |
| [CHK001](checklists/graceful-degradation.md#L16) | [x] | PARTIAL | Sixth coordinator hazard not guarded by shared active cap [CAP]. | AUD-036-SIM-011 |
| [CHK002](checklists/graceful-degradation.md#L17) | [x] | PARTIAL | Cap/split-simulation response not emitted by active chat [CHAT]. | AUD-036-SIM-011 |
| [CHK003](checklists/graceful-degradation.md#L18) | [x] | PARTIAL | Denied cascade does not attach actual annotation [CASCADE]. | AUD-036-SIM-011 |
| [CHK004](checklists/graceful-degradation.md#L19) | [x] | PARTIAL | Disconnected cap allows ungoverned work rather than promised refusal [CAP]/[CHAT]. | AUD-036-SIM-011 |
| [CHK005](checklists/graceful-degradation.md#L20) | [x] | PARTIAL | No distributed creation-boundary cap [CAP]. | AUD-036-SIM-011 |
| [CHK006](checklists/graceful-degradation.md#L21) | [x] | PARTIAL | No real annotation/chat publisher after cap denial [CASCADE]. | AUD-036-SIM-011 |
| [CHK007](checklists/graceful-degradation.md#L22) | [x] | PARTIAL | Deterministic ladder helper, not actual replay attachment [LADDER]/[CASCADE]. | AUD-036-SIM-011 |
| [CHK008](checklists/graceful-degradation.md#L26) | [x] | IMPLEMENTED | Distinct attempt/success budget definitions [FR009](spec.md#L2357). | - |
| [CHK009](checklists/graceful-degradation.md#L27) | [x] | PARTIAL | Active route passes no attempt-breaker probe [ROUTE]. | AUD-036-SIM-006 |
| [CHK010](checklists/graceful-degradation.md#L28) | [x] | PARTIAL | Breaker/fallback/accepted budget not integrated [INJECT]. | AUD-036-SIM-006 |
| [CHK011](checklists/graceful-degradation.md#L29) | [x] | PARTIAL | Success-counted quota absent at connected ingestion [ROUTE]. | AUD-036-SIM-006 |
| [CHK012](checklists/graceful-degradation.md#L30) | [x] | IMPLEMENTED | [Breaker constants](../../apps/api/app/services/simulation/parse_attempt_circuit_breaker.py#L1) define60/60/60; actual use assessed separately. | AUD-036-SIM-006 |
| [CHK013](checklists/graceful-degradation.md#L34) | [x] | PARTIAL | Text fallback helper disconnected from all artifacts [WATERMARK]. | AUD-036-SIM-014 |
| [CHK014](checklists/graceful-degradation.md#L35) | [x] | PARTIAL | Audio fallback catalog not guaranteed spoken prefix [LOCALES-TEST]. | AUD-036-SIM-014 |
| [CHK015](checklists/graceful-degradation.md#L36) | [x] | PARTIAL | Deterministic helpers exist, active text/audio coverage incomplete [WATERMARK]. | AUD-036-SIM-014 |
| [CHK016](checklists/graceful-degradation.md#L37) | [x] | PARTIAL | Typed channel distinction not emitted for all active fallbacks [AUDIT]. | AUD-036-SIM-014 |
| [CHK017](checklists/graceful-degradation.md#L38) | [x] | PARTIAL | Literal prefix helper not continuous byte-matched egress proof [COMMS]. | AUD-036-SIM-003, AUD-036-SIM-014 |
| [CHK018](checklists/graceful-degradation.md#L42) | [x] | PARTIAL | Active routing lacks clarification barrier [CHAT]/[TUPLES]. | AUD-036-SIM-007 |
| [CHK019](checklists/graceful-degradation.md#L43) | [x] | PARTIAL | Jurisdiction ambiguity typed audit not active [CHAT]. | AUD-036-SIM-007 |
| [CHK020](checklists/graceful-degradation.md#L44) | [x] | PARTIAL | Similar-confidence intent clarification not enforced [CHAT]. | AUD-036-SIM-007 |
| [CHK021](checklists/graceful-degradation.md#L45) | [x] | PARTIAL | Viewport disagreement/server-win not integrated [TUPLES]. | AUD-036-SIM-007 |
| [CHK022](checklists/graceful-degradation.md#L46) | [x] | PARTIAL | No active rural/urban boundary ambiguity handling [TUPLES]. | AUD-036-SIM-007 |
| [CHK023](checklists/graceful-degradation.md#L50) | [x] | PARTIAL | 120s wrapper exists,30s read/working callback not fully wired [INVOKER]. | AUD-036-SIM-004, AUD-036-SIM-013 |
| [CHK024](checklists/graceful-degradation.md#L51) | [x] | PARTIAL | Timeout logger not typed correlated audit [INVOKER]. | AUD-036-SIM-004 |
| [CHK025](checklists/graceful-degradation.md#L52) | [x] | PARTIAL | Generic tool error not dedicated timeout timeline/provenance [CHAT]. | AUD-036-SIM-013 |
| [CHK026](checklists/graceful-degradation.md#L53) | [x] | PARTIAL | Nonstreaming HTTP adapter cannot preserve partial reply stream [ADAPTER]. | AUD-036-SIM-013 |
| [CHK027](checklists/graceful-degradation.md#L57) | [x] | PARTIAL | Citation filter/degraded flag present, typed audit missing [ADAPTER]. | AUD-036-SIM-004 |
| [CHK028](checklists/graceful-degradation.md#L58) | [x] | PARTIAL | Caller-forced tenant fields not authoritative bidirectional isolation [AUTH]/[TENANT]. | AUD-036-SIM-002 |
| [CHK029](checklists/graceful-degradation.md#L62) | [x] | PARTIAL | Blackout signal constructor has no channel-window consumer [DEGRADED]. | AUD-036-SIM-022 |
| [CHK030](checklists/graceful-degradation.md#L63) | [x] | PARTIAL | Unavailable-agent mode no cached-window consumer [DEGRADED]. | AUD-036-SIM-022 |
| [CHK031](checklists/graceful-degradation.md#L64) | [x] | PARTIAL | Partition mode no participant-scope behavior [DEGRADED]. | AUD-036-SIM-022 |
| [CHK032](checklists/graceful-degradation.md#L65) | [x] | PARTIAL | Automatic recovery/audit not operational [DEGRADED]. | AUD-036-SIM-022 |
| [CHK033](checklists/graceful-degradation.md#L66) | [x] | UNVERIFIED | No attributable50-injection100%-window experiment [SWEEP]. | AUD-036-SIM-024 |
| [CHK034](checklists/graceful-degradation.md#L67) | [x] | PARTIAL | Freshness expiry not deliberate outage recovery consumer/audit [MAP-PUBLISH]/[DEGRADED]. | AUD-036-SIM-022 |
| [CHK035](checklists/graceful-degradation.md#L68) | [x] | CONFLICT | Freshness defaults are not outage durations; resource1800 conflicts amended600 [INJECT]. | AUD-036-SIM-006, AUD-036-SIM-023 |
| [CHK036](checklists/graceful-degradation.md#L72) | [x] | PARTIAL | Telco cascade not consumed as current channel list [COMMS]/[DEGRADED]. | AUD-036-SIM-022 |
| [CHK037](checklists/graceful-degradation.md#L73) | [x] | PARTIAL | TripleZero loss not connected prominently to chat [CHAT]. | AUD-036-SIM-022 |
| [CHK038](checklists/graceful-degradation.md#L74) | [x] | PARTIAL | Stale reducer property not full rendered styling [MAP]. | AUD-036-SIM-012 |
| [CHK039](checklists/graceful-degradation.md#L75) | [x] | PARTIAL | Point clustering not full geometry overflow/audit guarantee [MAP]. | AUD-036-SIM-001, AUD-036-SIM-012 |
| [CHK040](checklists/graceful-degradation.md#L79) | [x] | PARTIAL | 30/min successful-only counting not active [ROUTE]. | AUD-036-SIM-006 |
| [CHK041](checklists/graceful-degradation.md#L80) | [x] | PARTIAL | Refusal budget exclusion not integrated with independent breaker [INJECT]. | AUD-036-SIM-006 |
| [CHK042](checklists/graceful-degradation.md#L84) | [x] | PARTIAL | New contradiction tag discarded [INJECT]/[ROUTE]. | AUD-036-SIM-006 |
| [CHK043](checklists/graceful-degradation.md#L85) | [x] | PARTIAL | Concurrent writes not a shared-turn/notification/rerun guarantee [SIGNALS]/[PIPE]. | AUD-036-SIM-005, AUD-036-SIM-006 |
| [CHK044](checklists/graceful-degradation.md#L86) | [x] | PARTIAL | Scrub counts not consistently surfaced to coordinator [INJECT]/[CHAT]. | AUD-036-SIM-006 |
| [CHK045](checklists/graceful-degradation.md#L90) | [x] | PARTIAL | Regex refusal exists, comprehensive typed real-action audit incomplete [INJECT]. | AUD-036-SIM-003, AUD-036-SIM-006 |
| [CHK046](checklists/graceful-degradation.md#L91) | [x] | PARTIAL | Four role denies exist, owner/context/UI observer capability incomplete [AUTH]. | AUD-036-SIM-002 |
| [CHK047](checklists/graceful-degradation.md#L92) | [x] | PARTIAL | Combat/control constraints not enforced before dispatch [CHAT]/[TUPLES]. | AUD-036-SIM-007 |
| [CHK048](checklists/graceful-degradation.md#L93) | [x] | PARTIAL | Tool/agent closed lists reject unknowns, typed refusal audit incomplete [TOOLS]/[INVOKER]. | AUD-036-SIM-008 |
| [CHK049](checklists/graceful-degradation.md#L97) | [x] | PARTIAL | NEMA metadata not actual work throttle [NEMA]/[CHAT]. | AUD-036-SIM-021 |
| [CHK050](checklists/graceful-degradation.md#L98) | [x] | UNVERIFIED | No actual activation/real-notification preservation experiment [NEMA]. | AUD-036-SIM-021, AUD-036-SIM-024 |
| [CHK051](checklists/graceful-degradation.md#L102) | [x] | PARTIAL | generated_at excluded by tests, full bytes differ [AAR-TEST]/[LESSONS]. | AUD-036-SIM-015 |
| [CHK052](checklists/graceful-degradation.md#L103) | [x] | PARTIAL | Upload/retention errors swallowed, retry/index recovery incomplete [WORM]. | AUD-036-SIM-015 |
| [CHK053](checklists/graceful-degradation.md#L104) | [x] | PARTIAL | Rich target-thread evidence not persisted [DRAFT]/[LESSONS]. | AUD-036-SIM-015 |
| [CHK054](checklists/graceful-degradation.md#L108) | [x] | PARTIAL | Typed failure-to-chat stream missing in several paths [AUDIT]/[CHAT]. | AUD-036-SIM-008, AUD-036-SIM-013 |
| [CHK055](checklists/graceful-degradation.md#L109) | [x] | PARTIAL | History exists, complete lifecycle/overlay authoritative snapshot disconnected [STATE]/[MAP-PAGE]. | AUD-036-SIM-010, AUD-036-SIM-012 |
| [CHK056](checklists/graceful-degradation.md#L113) | [x] | CONFLICT | Checklist depth<=2 prose differs binding depth1/refuse2; helper refusal not active [CASCADE]. | AUD-036-SIM-011, AUD-036-SIM-023 |
| [CHK057](checklists/graceful-degradation.md#L122) | [ ] | PARTIAL | Local non-hazard bypass exists, no durable hazard-only counter [CAP]. | AUD-036-SIM-011 |
| [CHK058](checklists/graceful-degradation.md#L125) | [ ] | PARTIAL | Five hazards plus real chronologically attached annotations not supported [CASCADE]. | AUD-036-SIM-011 |
| [CHK059](checklists/graceful-degradation.md#L130) | [ ] | PARTIAL | No ETag-backed cap accounting [CAP]. | AUD-036-SIM-011 |
| [CHK060](checklists/graceful-degradation.md#L133) | [ ] | PARTIAL | Cap optional/hook lacks injection; per-target integration absent [CASCADE]. | AUD-036-SIM-011 |
| [CHK061](checklists/graceful-degradation.md#L140) | [ ] | PARTIAL | Pure ranking supported, actual candidate method mismatch [LADDER]/[CASCADE]. | AUD-036-SIM-011 |
| [CHK062](checklists/graceful-degradation.md#L144) | [ ] | PARTIAL | Full candidate set and selected-host audit not effective [CASCADE]. | AUD-036-SIM-011 |
| [CHK063](checklists/graceful-degradation.md#L147) | [ ] | PARTIAL | Annotation not actually attached on denial [CASCADE]. | AUD-036-SIM-011 |
| [CHK064](checklists/graceful-degradation.md#L151) | [ ] | PARTIAL | Local hazard filter no shared state invariant [CAP]. | AUD-036-SIM-011 |
| [CHK065](checklists/graceful-degradation.md#L158) | [ ] | PARTIAL | Dedicated503 handler exists, route audit/state exceptions swallowed [AUDIT]/[ROUTE]. | AUD-036-SIM-008 |
| [CHK066](checklists/graceful-degradation.md#L162) | [ ] | PARTIAL | Sentinel DLQ buffered, not durable three-reason uncertainty record [AUDIT]. | AUD-036-SIM-008 |
| [CHK067](checklists/graceful-degradation.md#L166) | [ ] | PARTIAL | Separate budget charging not wired [PIPE]/[ROUTE]. | AUD-036-SIM-005, AUD-036-SIM-006 |
| [CHK068](checklists/graceful-degradation.md#L169) | [ ] | PARTIAL | Cache not active, repeated503 may re-execute/create gaps [CACHE]. | AUD-036-SIM-009 |
| [CHK069](checklists/graceful-degradation.md#L172) | [ ] | PARTIAL | Fail-open memory/warnings and incomplete export integrity [AUDIT]/[EXPORT]. | AUD-036-SIM-008, AUD-036-SIM-015 |
| [CHK070](checklists/graceful-degradation.md#L179) | [ ] | PARTIAL | Only injection checked, active chat/new work not refused [ROUTE]/[CHAT]. | AUD-036-SIM-010 |
| [CHK071](checklists/graceful-degradation.md#L184) | [ ] | PARTIAL | Replay-after-resume helper table unused by routes [CACHE]. | AUD-036-SIM-009 |

### Safety and Life Primacy

| Item | Original state | Status | Assessment and evidence | Follow-up |
| --- | --- | --- | --- | --- |
| [CHK001](checklists/safety-and-life-primacy.md#L13) | [x] | PARTIAL | Shared creation-boundary refusal absent [CAP]. | AUD-036-SIM-011 |
| [CHK002](checklists/safety-and-life-primacy.md#L14) | [x] | PARTIAL | No active cap/split-sim explanation [CHAT]. | AUD-036-SIM-011 |
| [CHK003](checklists/safety-and-life-primacy.md#L15) | [x] | PARTIAL | Some refusal text, not complete typed federal-action audit [INJECT]/[CHAT]. | AUD-036-SIM-003 |
| [CHK004](checklists/safety-and-life-primacy.md#L16) | [x] | PARTIAL | Observer route deny present, full owner/UI/context enforcement incomplete [AUTH]. | AUD-036-SIM-002 |
| [CHK005](checklists/safety-and-life-primacy.md#L17) | [x] | PARTIAL | Lifecycle routes authored, state/cancel/queue connection defective [ROUTE]. | AUD-036-SIM-010 |
| [CHK006](checklists/safety-and-life-primacy.md#L21) | [x] | IMPLEMENTED | Five life-safety categories explicitly defined [FR010](spec.md#L2440). | - |
| [CHK007](checklists/safety-and-life-primacy.md#L22) | [x] | PARTIAL | Active pre-parse gate lacks parsed low-confidence signal class [INJECT]. | AUD-036-SIM-006 |
| [CHK008](checklists/safety-and-life-primacy.md#L23) | [x] | IMPLEMENTED | Primacy-of-life rationale explicit [FR010](spec.md#L2440); documentary credit only. | - |
| [CHK009](checklists/safety-and-life-primacy.md#L24) | [x] | PARTIAL | Accepted low non-life signals not fully downstream tagged/degraded [SIGNAL]/[PIPE]. | AUD-036-SIM-006 |
| [CHK010](checklists/safety-and-life-primacy.md#L25) | [x] | PARTIAL | Gate mapping differs from five-class contract, not one active source [INJECT]. | AUD-036-SIM-006 |
| [CHK011](checklists/safety-and-life-primacy.md#L26) | [x] | PARTIAL | Refusal/success quota separation not connected [ROUTE]. | AUD-036-SIM-006 |
| [CHK012](checklists/safety-and-life-primacy.md#L27) | [x] | IMPLEMENTED | Explicit post-injection low-confidence preservation in [FR010](spec.md#L2440). | - |
| [CHK013](checklists/safety-and-life-primacy.md#L31) | [x] | PARTIAL | Actual Communication reply not exact complete receipt [DISPATCH]/[COMMS]. | AUD-036-SIM-003 |
| [CHK014](checklists/safety-and-life-primacy.md#L32) | [x] | PARTIAL | Publication and direct SDK boundaries not both guarded [COMMS]. | AUD-036-SIM-003 |
| [CHK015](checklists/safety-and-life-primacy.md#L33) | [x] | PARTIAL | Every blocked delivery not typed/audited durably [COMMS]/[AUDIT]. | AUD-036-SIM-003, AUD-036-SIM-008 |
| [CHK016](checklists/safety-and-life-primacy.md#L34) | [x] | PARTIAL | All-channel/jurisdiction guard coverage incomplete [COMMS]. | AUD-036-SIM-003 |
| [CHK017](checklists/safety-and-life-primacy.md#L35) | [x] | PARTIAL | All translated artifact paths not watermarked [WATERMARK]. | AUD-036-SIM-014 |
| [CHK018](checklists/safety-and-life-primacy.md#L36) | [x] | PARTIAL | Actual warning persistence bypasses pre-approval guard [COMMS]. | AUD-036-SIM-014 |
| [CHK019](checklists/safety-and-life-primacy.md#L37) | [x] | PARTIAL | Curated text helper exists, no guarantee on every active render [WATERMARK]. | AUD-036-SIM-014 |
| [CHK020](checklists/safety-and-life-primacy.md#L38) | [x] | PARTIAL | Audio catalog helper not connected bilingual-prefix enforcement [LOCALES-TEST]. | AUD-036-SIM-014 |
| [CHK021](checklists/safety-and-life-primacy.md#L39) | [x] | PARTIAL | Missing-text fallback helper lacks full artifact/audit connection [WATERMARK]. | AUD-036-SIM-014 |
| [CHK022](checklists/safety-and-life-primacy.md#L40) | [x] | PARTIAL | Missing-audio metadata not spoken waveform or full audit [LOCALES-TEST]. | AUD-036-SIM-014 |
| [CHK023](checklists/safety-and-life-primacy.md#L41) | [x] | UNVERIFIED | Continuous zero-egress/SEV0 experiment not in local evidence [SWEEP]. | AUD-036-SIM-024 |
| [CHK024](checklists/safety-and-life-primacy.md#L45) | [x] | PARTIAL | Every-hazard Risk publication not actual operational invocation [PIPE]. | AUD-036-SIM-005 |
| [CHK025](checklists/safety-and-life-primacy.md#L46) | [x] | PARTIAL | Ack callback/typed timeout audit absent on production invoker [INVOKER]. | AUD-036-SIM-004, AUD-036-SIM-013 |
| [CHK026](checklists/safety-and-life-primacy.md#L47) | [x] | PARTIAL | Routing ambiguity not controller gate [TUPLES]/[CHAT]. | AUD-036-SIM-007 |
| [CHK027](checklists/safety-and-life-primacy.md#L48) | [x] | PARTIAL | NSW escalation-consent enforcement not active [CHAT]. | AUD-036-SIM-007 |
| [CHK028](checklists/safety-and-life-primacy.md#L49) | [x] | PARTIAL | Combat/support split not resolved by generic six-role tools [TOOLS]. | AUD-036-SIM-007 |
| [CHK029](checklists/safety-and-life-primacy.md#L50) | [x] | PARTIAL | Citation filtering supported, typed violation audit absent [ADAPTER]. | AUD-036-SIM-004 |
| [CHK030](checklists/safety-and-life-primacy.md#L51) | [x] | PARTIAL | Owner/context failure can mix simulation/live routing [AUTH]/[TENANT]. | AUD-036-SIM-002 |
| [CHK031](checklists/safety-and-life-primacy.md#L55) | [x] | PARTIAL | Injection-first tool branch/turn barrier absent [CHAT]/[PIPE]. | AUD-036-SIM-005 |
| [CHK032](checklists/safety-and-life-primacy.md#L56) | [x] | PARTIAL | Optional signal correlation not bound by route [SIGNAL]/[ROUTE]. | AUD-036-SIM-006 |
| [CHK033](checklists/safety-and-life-primacy.md#L57) | [x] | PARTIAL | Singleton extraction, no multi-signal correlation [INJECT]. | AUD-036-SIM-006 |
| [CHK034](checklists/safety-and-life-primacy.md#L58) | [x] | PARTIAL | Target-thread cascade evidence not actually written [CASCADE]. | AUD-036-SIM-011 |
| [CHK035](checklists/safety-and-life-primacy.md#L59) | [x] | PARTIAL | No actual one-backpointer attached annotation [CASCADE]. | AUD-036-SIM-011 |
| [CHK036](checklists/safety-and-life-primacy.md#L60) | [x] | PARTIAL | Persisted lessons lacks full target-thread evidence [LESSONS]. | AUD-036-SIM-015 |
| [CHK037](checklists/safety-and-life-primacy.md#L61) | [x] | PARTIAL | Audit failures swallowed/memory fallback can lose refusals [AUDIT]. | AUD-036-SIM-008 |
| [CHK038](checklists/safety-and-life-primacy.md#L65) | [x] | IMPLEMENTED | [LADDER] pure deterministic helper with ranking/tie-break, active attachment separate. | AUD-036-SIM-011 |
| [CHK039](checklists/safety-and-life-primacy.md#L66) | [x] | PARTIAL | Existing jurisdiction ladder does not implement all binding steps [TUPLES]/[CHAT]. | AUD-036-SIM-007 |
| [CHK040](checklists/safety-and-life-primacy.md#L67) | [x] | PARTIAL | Active server-revalidated viewport routing missing [CHAT]. | AUD-036-SIM-007 |
| [CHK041](checklists/safety-and-life-primacy.md#L68) | [x] | PARTIAL | Versioned helper table not full active curated catalog [LOCALES]/[WATERMARK]. | AUD-036-SIM-014 |
| [CHK042](checklists/safety-and-life-primacy.md#L69) | [x] | PARTIAL | Versioned audio prefix metadata not active guaranteed waveform [LOCALES-TEST]. | AUD-036-SIM-014 |
| [CHK043](checklists/safety-and-life-primacy.md#L70) | [x] | IMPLEMENTED | [TOOLS]/[INVOKER]/[SIGNAL] closed lists reject unknown tool/role/category structurally; audit completeness separate. | AUD-036-SIM-008 |
| [CHK044](checklists/safety-and-life-primacy.md#L71) | [x] | PARTIAL | NEMA metadata not actual priority work/notification enforcement [NEMA]. | AUD-036-SIM-021 |

### Multi-Jurisdiction

| Item | Original state | Status | Assessment and evidence | Follow-up |
| --- | --- | --- | --- | --- |
| [CHK001](checklists/multi-jurisdiction.md#L18) | [ ] | IMPLEMENTED | Tuple routing explicitly mandated [FR021](spec.md#L2526), definition only. | - |
| [CHK002](checklists/multi-jurisdiction.md#L21) | [ ] | CONFLICT | Checklist substitutes ABS fallback for last-active-thread step; [FR021](spec.md#L2526) is binding ladder. | AUD-036-SIM-007, AUD-036-SIM-023 |
| [CHK003](checklists/multi-jurisdiction.md#L24) | [ ] | IMPLEMENTED | WA sole-DFES fixture defined and asserted [TUPLE-TEST]. | - |
| [CHK004](checklists/multi-jurisdiction.md#L27) | [ ] | PARTIAL | QFD naming supported, SES lead/secondary active intent unresolved [TUPLES]. | AUD-036-SIM-007 |
| [CHK005](checklists/multi-jurisdiction.md#L30) | [ ] | PARTIAL | CFA/FRV names not boundary-aware clarify selection [TUPLES]. | AUD-036-SIM-007 |
| [CHK006](checklists/multi-jurisdiction.md#L34) | [ ] | PARTIAL | SACFS/SAMFS names not rural/metro active route [TUPLES]. | AUD-036-SIM-007 |
| [CHK007](checklists/multi-jurisdiction.md#L37) | [ ] | IMPLEMENTED | TAS sole-TFS definition/data supported [TUPLE-TEST]. | - |
| [CHK008](checklists/multi-jurisdiction.md#L40) | [ ] | PARTIAL | NT dual names present, Darwin/Katherine subclass disambiguation absent [TUPLES]. | AUD-036-SIM-007 |
| [CHK009](checklists/multi-jurisdiction.md#L44) | [ ] | PARTIAL | NT cyclone registry row exists, full TC typed parameters/model/routing absent [SIGNAL]/[TUPLES]. | AUD-036-SIM-006, AUD-036-SIM-007 |
| [CHK010](checklists/multi-jurisdiction.md#L47) | [ ] | PARTIAL | ESA fire ordering present, ACT medical can bypass ESA [TUPLES]. | AUD-036-SIM-007 |
| [CHK011](checklists/multi-jurisdiction.md#L50) | [ ] | PARTIAL | AFP/ACTPolicing names/hints not actual intent-based selection [TUPLES]. | AUD-036-SIM-007 |
| [CHK012](checklists/multi-jurisdiction.md#L54) | [ ] | PARTIAL | Branded fixture data exists but controller bypasses it [TUPLE-TEST]/[CHAT]. | AUD-036-SIM-007 |
| [CHK013](checklists/multi-jurisdiction.md#L57) | [ ] | PARTIAL | SES fixture data not simultaneous distinct active combat threads [CAP]/[TUPLES]. | AUD-036-SIM-007, AUD-036-SIM-011 |
| [CHK014](checklists/multi-jurisdiction.md#L61) | [ ] | PARTIAL | Membership/unknown error tests not every tuple positive+audited clarify-negative [TUPLE-TEST]. | AUD-036-SIM-007 |
| [CHK015](checklists/multi-jurisdiction.md#L68) | [ ] | IMPLEMENTED | [AIIMS] primary mapping independent of jurisdiction; definition/model supported. | - |
| [CHK016](checklists/multi-jurisdiction.md#L74) | [ ] | PARTIAL | Domain tags not enforced per active invocation/route [CHAT]/[AIIMS]. | AUD-036-SIM-007 |
| [CHK017](checklists/multi-jurisdiction.md#L78) | [ ] | PARTIAL | Rich response/IC attribution not persisted [DRAFT]/[LESSONS]. | AUD-036-SIM-015 |
| [CHK018](checklists/multi-jurisdiction.md#L85) | [ ] | PARTIAL | Remote metadata present, actual text/audio prefixes absent [LOCALES-TEST]. | AUD-036-SIM-014 |
| [CHK019](checklists/multi-jurisdiction.md#L88) | [ ] | PARTIAL | Kriol/TorresStrait metadata not approved active assets [LOCALES]. | AUD-036-SIM-014 |
| [CHK020](checklists/multi-jurisdiction.md#L90) | [ ] | IMPLEMENTED | [Profiles](../../apps/api/app/services/simulation/jurisdiction_locale_priority.py#L1) cover jurisdictions/NT remote priorities. | - |
| [CHK021](checklists/multi-jurisdiction.md#L94) | [ ] | PARTIAL | Active live-log whitelist bypasses priority fallback [LIVELOG]. | AUD-036-SIM-013, AUD-036-SIM-014 |
| [CHK022](checklists/multi-jurisdiction.md#L99) | [ ] | PARTIAL | Helper profile tests not eight active simulation locale consumers [LOCALES-TEST]. | AUD-036-SIM-014 |
| [CHK023](checklists/multi-jurisdiction.md#L102) | [ ] | IMPLEMENTED | [Speech catalog](../../apps/api/app/services/simulation/data/speech_prerender_catalog.json#L1) has explicit backlog/blocker flags. | - |
| [CHK024](checklists/multi-jurisdiction.md#L109) | [ ] | IMPLEMENTED | Cross-live citation prohibition explicit [FR007](spec.md#L2338), definition only. | - |
| [CHK025](checklists/multi-jurisdiction.md#L112) | [ ] | PARTIAL | [ADAPTER] rejects bad citations/degrades but typed jurisdiction/resource audit missing. | AUD-036-SIM-004 |
| [CHK026](checklists/multi-jurisdiction.md#L115) | [ ] | PARTIAL | No eight-jurisdiction active real-reply typed-audit matrix established [ADAPTER]/[RBAC-TEST]. | AUD-036-SIM-004, AUD-036-SIM-024 |
| [CHK027](checklists/multi-jurisdiction.md#L121) | [ ] | PARTIAL | Generic role prompts not all sandboxed federal data-source consumers [DISPATCH]. | AUD-036-SIM-004, AUD-036-SIM-007 |
| [CHK028](checklists/multi-jurisdiction.md#L125) | [ ] | PARTIAL | Real-action refusal exists partially; full touchpoint-specific audit missing [INJECT]. | AUD-036-SIM-003 |
| [CHK029](checklists/multi-jurisdiction.md#L129) | [ ] | PARTIAL | MRNSW/BOM sandbox path not established by six generic roles [DISPATCH]. | AUD-036-SIM-007 |
| [CHK030](checklists/multi-jurisdiction.md#L135) | [ ] | PARTIAL | Five isolated parallel hazard threads/map/chat attribution not connected [CAP]/[CHAT]/[MAP]. | AUD-036-SIM-011, AUD-036-SIM-013 |
| [CHK031](checklists/multi-jurisdiction.md#L139) | [ ] | UNVERIFIED | No attributable four-jurisdiction concurrent exercise/assertion result [SWEEP]. | AUD-036-SIM-024 |

### Amendment Pass

| Item | Original state | Status | Assessment and evidence | Follow-up |
| --- | --- | --- | --- | --- |
| [CHK001](checklists/amendment-pass.md#L44) | [ ] | IMPLEMENTED | Canonical six-function/nine-agent definition [FR061](spec.md#L3247). | - |
| [CHK002](checklists/amendment-pass.md#L47) | [ ] | IMPLEMENTED | Single primary used for ordering explicitly defined [FR061](spec.md#L3271). | - |
| [CHK003](checklists/amendment-pass.md#L51) | [ ] | IMPLEMENTED | Secondary-tags max2 rule/data supported [AIIMS]/[RECORD]. | - |
| [CHK004](checklists/amendment-pass.md#L57) | [ ] | PARTIAL | [RECORD] fields added; full adapter/data-model/wire-schema parity incomplete. | AUD-036-SIM-023 |
| [CHK005](checklists/amendment-pass.md#L60) | [ ] | PARTIAL | Rich primary attribution not actual persisted lessons [DRAFT]/[LESSONS]. | AUD-036-SIM-015 |
| [CHK006](checklists/amendment-pass.md#L68) | [ ] | IMPLEMENTED | Mandatory visual16-layer definition explicit [FR027](spec.md#L2635). | - |
| [CHK007](checklists/amendment-pass.md#L71) | [ ] | PARTIAL | Prohibited Point-only filter remains [MAP]. | AUD-036-SIM-001 |
| [CHK008](checklists/amendment-pass.md#L75) | [ ] | PARTIAL | [MAP-TEST] summary/mock assertions not16 visible primitives. | AUD-036-SIM-001 |
| [CHK009](checklists/amendment-pass.md#L83) | [ ] | IMPLEMENTED | Persist/publish/consume-before-ack definition explicit [FR009](spec.md#L2372). | - |
| [CHK010](checklists/amendment-pass.md#L88) | [ ] | SUPERSEDED | Unqualified success-array rule refined by [Cycle2Q1](spec.md#L394) all-attempted/status semantics; active code still partial. | AUD-036-SIM-005 |
| [CHK011](checklists/amendment-pass.md#L92) | [ ] | CONFLICT | Older two-value enum versus current [data-model contexts](data-model.md#L1061); not silently treated equivalent. | AUD-036-SIM-023 |
| [CHK012](checklists/amendment-pass.md#L97) | [ ] | IMPLEMENTED | Exactly-once subscriber/intent definition explicit [FR009](spec.md#L2393). | - |
| [CHK013](checklists/amendment-pass.md#L102) | [ ] | CONFLICT | Strict two-value contract requirement differs current [CONTRACT]/[AUDIT] contexts. | AUD-036-SIM-023 |
| [CHK014](checklists/amendment-pass.md#L106) | [ ] | PARTIAL | Full transaction/rollback not [PIPE]; later degraded-dispatch intentionally changes post-write failure, not persist failure. | AUD-036-SIM-005, AUD-036-SIM-023 |
| [CHK015](checklists/amendment-pass.md#L110) | [ ] | PARTIAL | [PIPE-TEST] publication/nonempty assertions not observed subscriber-before-response. | AUD-036-SIM-005 |
| [CHK016](checklists/amendment-pass.md#L118) | [ ] | IMPLEMENTED | Distributed allocation choices explicitly defined [FR048](spec.md#L2857). | - |
| [CHK017](checklists/amendment-pass.md#L122) | [ ] | IMPLEMENTED | Five-step failure protocol authored [FR048](spec.md#L2853); runtime separate. | - |
| [CHK018](checklists/amendment-pass.md#L129) | [ ] | PARTIAL | Uncertainty sentinel contract and actual buffered type/three-reason schema not aligned [AUDIT]. | AUD-036-SIM-008, AUD-036-SIM-023 |
| [CHK019](checklists/amendment-pass.md#L132) | [ ] | PARTIAL | Allocator delegation supported, final fail-closed dense commit not [AUDIT]. | AUD-036-SIM-008 |
| [CHK020](checklists/amendment-pass.md#L136) | [ ] | PARTIAL | Container declaration exists, writer only buffers DLQ [AUDIT]/[INFRA]. | AUD-036-SIM-008, AUD-036-SIM-020 |
| [CHK021](checklists/amendment-pass.md#L139) | [ ] | UNVERIFIED | No attributable multi-replica zero-gap E2E run [SEQUENCE]/[SWEEP]. | AUD-036-SIM-024 |
| [CHK022](checklists/amendment-pass.md#L142) | [ ] | PARTIAL | Export/lessons durable DLQ integrity warnings absent [EXPORT]/[LESSONS]. | AUD-036-SIM-015 |
| [CHK023](checklists/amendment-pass.md#L150) | [ ] | IMPLEMENTED | JWT/app-role/member-before-audit definition explicit [FR051](spec.md#L2929). | - |
| [CHK024](checklists/amendment-pass.md#L154) | [ ] | IMPLEMENTED | RBAC-before-cache defined [idempotency contract](contracts/idempotency-cache.md#L1). | - |
| [CHK025](checklists/amendment-pass.md#L158) | [ ] | PARTIAL | Four dependencies exist, authoritative simulation member lookup absent [AUTH]. | AUD-036-SIM-002 |
| [CHK026](checklists/amendment-pass.md#L161) | [ ] | PARTIAL | Role denials/audit attempted, foreign-owner decision and durable audit incomplete [AUTH]/[AUDIT]. | AUD-036-SIM-002, AUD-036-SIM-008 |
| [CHK027](checklists/amendment-pass.md#L164) | [ ] | PARTIAL | [RBAC-TEST] header mismatch not actual cross-tenant simulation ownership. | AUD-036-SIM-002 |
| [CHK028](checklists/amendment-pass.md#L172) | [ ] | IMPLEMENTED | Durable pause/all-new-work refusal definition explicit [FR059](spec.md#L3132). | - |
| [CHK029](checklists/amendment-pass.md#L176) | [ ] | IMPLEMENTED | Queue-not-claim-start definition explicit [FR059](spec.md#L3132). | - |
| [CHK030](checklists/amendment-pass.md#L179) | [ ] | IMPLEMENTED | Replay/transition409/uncached refusal semantics authored [cache contract](contracts/idempotency-cache.md#L137). | - |
| [CHK031](checklists/amendment-pass.md#L184) | [ ] | IMPLEMENTED | Required lifecycle lineage defined [FR066](spec.md#L3506). | - |
| [CHK032](checklists/amendment-pass.md#L189) | [ ] | PARTIAL | Optional common fields not mandatory on every actual lifecycle event [AUDIT]/[ROUTE]. | AUD-036-SIM-008, AUD-036-SIM-023 |
| [CHK033](checklists/amendment-pass.md#L193) | [ ] | PARTIAL | Separate state and swallowed writes/chat bypass [STATE]/[CHAT]. | AUD-036-SIM-010 |
| [CHK034](checklists/amendment-pass.md#L197) | [ ] | PARTIAL | No mounted-route pause/replay/resume chain with cache [CACHE]/[ROUTE]. | AUD-036-SIM-009 |
| [CHK035](checklists/amendment-pass.md#L206) | [ ] | IMPLEMENTED | Every-path recent-signal definition explicit [FR013](spec.md#L2468). | - |
| [CHK036](checklists/amendment-pass.md#L210) | [ ] | PARTIAL | Fixed600 history/error-to-empty not per-category reliable input [ROUTE]/[SIGNALS]. | AUD-036-SIM-006 |
| [CHK037](checklists/amendment-pass.md#L214) | [ ] | PARTIAL | Local history tests not complete handler-input/persisted-contradiction flow [PIPE-TEST]. | AUD-036-SIM-006 |
| [CHK038](checklists/amendment-pass.md#L222) | [ ] | IMPLEMENTED | Canonical16 definition explicit [FR027](spec.md#L2647). | - |
| [CHK039](checklists/amendment-pass.md#L226) | [ ] | PARTIAL | [LAYERS] backend source, web array codegen but independent type declaration/import contract incomplete. | AUD-036-SIM-023 |
| [CHK040](checklists/amendment-pass.md#L230) | [ ] | IMPLEMENTED | [LAYERS-TEST] set/byte alignment assertions and codegen check authored. | - |
| [CHK041](checklists/amendment-pass.md#L238) | [ ] | IMPLEMENTED | Six named sections explicitly defined [FR054](spec.md#L3200). | - |
| [CHK042](checklists/amendment-pass.md#L241) | [ ] | IMPLEMENTED | Deterministic ordering rule/helper authored [DRAFT]. | - |
| [CHK043](checklists/amendment-pass.md#L243) | [ ] | PARTIAL | Persisted generator bypasses rich builder and full evidence [LESSONS]/[DRAFT]. | AUD-036-SIM-015 |
| [CHK044](checklists/amendment-pass.md#L248) | [ ] | PARTIAL | [AAR-TEST] excludes generated_at, no route-queued abort outcome. | AUD-036-SIM-015 |
| [CHK045](checklists/amendment-pass.md#L252) | [ ] | PARTIAL | Primary metadata helper not persisted complete IC/agent content [DRAFT]. | AUD-036-SIM-015 |
| [CHK046](checklists/amendment-pass.md#L260) | [ ] | IMPLEMENTED | Cap-before-dispatch definition explicit [FR057](spec.md#L3064). | - |
| [CHK047](checklists/amendment-pass.md#L263) | [ ] | IMPLEMENTED | Deterministic five-step definition/helper [LADDER]. | - |
| [CHK048](checklists/amendment-pass.md#L267) | [ ] | IMPLEMENTED | Hazard-only count/unbounded annotations defined [FR052](spec.md#L2980). | - |
| [CHK049](checklists/amendment-pass.md#L271) | [ ] | IMPLEMENTED | Four/five/six hazard edge semantics explicitly specified [FR052](spec.md#L2980). | - |
| [CHK050](checklists/amendment-pass.md#L275) | [ ] | PARTIAL | Optional cap, candidate API mismatch, no real annotation [CASCADE]. | AUD-036-SIM-011 |
| [CHK051](checklists/amendment-pass.md#L279) | [ ] | PARTIAL | Cap uses memory not shared ETag counter [CAP]. | AUD-036-SIM-011 |
| [CHK052](checklists/amendment-pass.md#L282) | [ ] | PARTIAL | Pure-helper properties not active attachment replay [LADDER]/[CASCADE]. | AUD-036-SIM-011 |
| [CHK053](checklists/amendment-pass.md#L290) | [ ] | IMPLEMENTED | Four AWS color families explicit [FR027](spec.md#L2656). | - |
| [CHK054](checklists/amendment-pass.md#L294) | [ ] | IMPLEMENTED | [MAP] known Advice/watch/emergency/not-applicable literals correct; unknown/unified palette separate. | AUD-036-SIM-001 |
| [CHK055](checklists/amendment-pass.md#L297) | [ ] | PARTIAL | Source palette tests not all rendered tiers/layers [MAP-TEST]. | AUD-036-SIM-001 |
| [CHK056](checklists/amendment-pass.md#L306) | [ ] | IMPLEMENTED | 30-plus text/audio locale requirement explicitly defined [FR039](spec.md#L2714). | - |
| [CHK057](checklists/amendment-pass.md#L310) | [ ] | IMPLEMENTED | Six remote languages explicitly named [FR039](spec.md#L2714). | - |
| [CHK058](checklists/amendment-pass.md#L313) | [ ] | IMPLEMENTED | Jurisdiction profile requirement/data supported [LOCALES]. | - |
| [CHK059](checklists/amendment-pass.md#L316) | [ ] | PARTIAL | Expanded metadata/backlog flags not actual30 active prefix tables/assets [LOCALES-TEST]. | AUD-036-SIM-014 |
| [CHK060](checklists/amendment-pass.md#L325) | [ ] | IMPLEMENTED | Tuple routing definition explicitly [FR021](spec.md#L2561). | - |
| [CHK061](checklists/amendment-pass.md#L328) | [ ] | IMPLEMENTED | Required jurisdiction-specific fixtures named [FR021](spec.md#L2561). | - |
| [CHK062](checklists/amendment-pass.md#L332) | [ ] | PARTIAL | API JSON registry not shared domain contract/active route [TUPLES]. | AUD-036-SIM-007 |
| [CHK063](checklists/amendment-pass.md#L336) | [ ] | PARTIAL | [TUPLE-TEST] positive membership/hint tests not audited negative clarify for every tuple. | AUD-036-SIM-007 |
| [CHK064](checklists/amendment-pass.md#L344) | [ ] | CONFLICT | Human utility Transport versus [MATRIX] Logistics; cannot call byte-aligned. | AUD-036-SIM-023 |
| [CHK065](checklists/amendment-pass.md#L350) | [ ] | PARTIAL | [MATRIX] canonical sets/ordering present, unresolved utility alias and actual callers. | AUD-036-SIM-011, AUD-036-SIM-023 |
| [CHK066](checklists/amendment-pass.md#L353) | [ ] | PARTIAL | Static set assertions not actual five-category consumer routing [PIPE-TEST]. | AUD-036-SIM-011 |
| [CHK067](checklists/amendment-pass.md#L355) | [ ] | PARTIAL | [MATRIX] orchestrator source, lessons identified-gap consumer not complete [DRAFT]. | AUD-036-SIM-015 |
| [CHK068](checklists/amendment-pass.md#L363) | [ ] | IMPLEMENTED | Mandatory six registry fields explicitly defined [FR062](spec.md#L3301). | - |
| [CHK069](checklists/amendment-pass.md#L366) | [ ] | PARTIAL | Empty canonical seed and incompatible alternative registry [REGISTRY]/[CARVEOUT]. | AUD-036-SIM-026 |
| [CHK070](checklists/amendment-pass.md#L369) | [ ] | MISSING | Scoped workflow searches find manual alternate review, no required PR field/expiry/reference gate [CARVEOUT]. | AUD-036-SIM-026 |
| [CHK071](checklists/amendment-pass.md#L373) | [ ] | MISSING | No active empty-registry-with-reference CI enforcement [REGISTRY]/[CARVEOUT]. | AUD-036-SIM-026 |
| [CHK072](checklists/amendment-pass.md#L376) | [ ] | PARTIAL | Constitutional provenance required but canonical seed/fields insufficient [REGISTRY]. | AUD-036-SIM-026 |
| [CHK073](checklists/amendment-pass.md#L384) | [ ] | IMPLEMENTED | Five plan SLI obligations explicit [FR063](spec.md#L3323); later runtime taxonomy not blanket retirement. | - |
| [CHK074](checklists/amendment-pass.md#L388) | [ ] | IMPLEMENTED | Fresh-evidence promotion refusal defined [FR063](spec.md#L3323). | - |
| [CHK075](checklists/amendment-pass.md#L391) | [ ] | UNVERIFIED | No attributable all-five E2E release run [SWEEP]/[GATE-TEST]. | AUD-036-SIM-024 |
| [CHK076](checklists/amendment-pass.md#L393) | [ ] | PARTIAL | Actual production consumes CI only, no full staging gate [CD]. | AUD-036-SIM-016 |
| [CHK077](checklists/amendment-pass.md#L395) | [ ] | PARTIAL | [KQL]/[GATE] configs partly align, omitted SLIs/load and unsafe collation. | AUD-036-SIM-018, AUD-036-SIM-019 |
| [CHK078](checklists/amendment-pass.md#L398) | [ ] | UNVERIFIED | No pinned fresh SHA/time/value/threshold promotion receipt [SWEEP]. | AUD-036-SIM-024 |
| [CHK079](checklists/amendment-pass.md#L406) | [ ] | IMPLEMENTED | Dedicated polite labelled log requirement explicit [FR064](spec.md#L3368). | - |
| [CHK080](checklists/amendment-pass.md#L409) | [ ] | IMPLEMENTED | Separate map digest/log requirement explicit [FR064](spec.md#L3368). | - |
| [CHK081](checklists/amendment-pass.md#L412) | [ ] | IMPLEMENTED | Shared three-step locale definition explicit [FR064](spec.md#L3368). | - |
| [CHK082](checklists/amendment-pass.md#L417) | [ ] | IMPLEMENTED | Both-channel single correlation/resolved-locale definition explicit [FR064](spec.md#L3368). | - |
| [CHK083](checklists/amendment-pass.md#L423) | [ ] | IMPLEMENTED | [Watermark schema](../../packages/domain/src/domain/models/telemetry_injection_audit_entry.py#L323) includes delivery/locale fields. | - |
| [CHK084](checklists/amendment-pass.md#L426) | [ ] | PARTIAL | [LIVELOG-TEST] ARIA props not mounted-page axe proof. | AUD-036-SIM-013 |
| [CHK085](checklists/amendment-pass.md#L430) | [ ] | PARTIAL | [LIVELOG] whitelist lacks shared priority rule; tests not actual SSE receipt. | AUD-036-SIM-013 |
| [CHK086](checklists/amendment-pass.md#L438) | [ ] | IMPLEMENTED | Every-path hash requirement explicit [FR065](spec.md#L3410). | - |
| [CHK087](checklists/amendment-pass.md#L442) | [ ] | IMPLEMENTED | Source enum/preimages explicitly defined [FR065](spec.md#L3424). | - |
| [CHK088](checklists/amendment-pass.md#L446) | [ ] | PARTIAL | Current26 schema/common fields do not guarantee required provenance at all paths [AUDIT]. | AUD-036-SIM-008, AUD-036-SIM-023 |
| [CHK089](checklists/amendment-pass.md#L449) | [ ] | PARTIAL | Actual attempts/success/refusal omit mandatory hash/source [ROUTE]/[AUDIT]. | AUD-036-SIM-006, AUD-036-SIM-008 |
| [CHK090](checklists/amendment-pass.md#L454) | [ ] | PARTIAL | [Hash-source tests](../../tests/unit/test_audit_envelope_prompt_hash_source.py#L1) enum cases not all active refusal/preimage paths. | AUD-036-SIM-006 |
| [CHK091](checklists/amendment-pass.md#L458) | [ ] | PARTIAL | Projection/export not full hash-source forensic content [DRAFT]/[EXPORT]. | AUD-036-SIM-015 |
| [CHK092](checklists/amendment-pass.md#L466) | [ ] | IMPLEMENTED | Four-endpoint24h replay rule explicitly [FR066](spec.md#L3447). | - |
| [CHK093](checklists/amendment-pass.md#L470) | [ ] | IMPLEMENTED | Route/verb/simulation uniqueness defined [FR066](spec.md#L3472). | - |
| [CHK094](checklists/amendment-pass.md#L475) | [ ] | IMPLEMENTED | 422 body-conflict rule explicitly defined [error contract](contracts/error-responses.md#L154). | - |
| [CHK095](checklists/amendment-pass.md#L479) | [ ] | IMPLEMENTED | 503 replay/no-repeat-DLQ requirement explicitly [cache contract](contracts/idempotency-cache.md#L137). | - |
| [CHK096](checklists/amendment-pass.md#L485) | [ ] | IMPLEMENTED | Tenant cache scoping explicitly defined [FR066](spec.md#L3447). | - |
| [CHK097](checklists/amendment-pass.md#L488) | [ ] | PARTIAL | Container declared, actual cache document PK/ID wrong and no route use [CACHE]. | AUD-036-SIM-009 |
| [CHK098](checklists/amendment-pass.md#L493) | [ ] | PARTIAL | Repository namespace assertions not real pause/abort request replay [CACHE]/[ROUTE]. | AUD-036-SIM-009 |
| [CHK099](checklists/amendment-pass.md#L497) | [ ] | PARTIAL | Body-conflict helper no connected422/problem response [CACHE]/[ERRORS]. | AUD-036-SIM-009, AUD-036-SIM-023 |
| [CHK100](checklists/amendment-pass.md#L505) | [ ] | IMPLEMENTED | Eight amendment Q/A definitions have explicit traceability rows in this checklist and [spec](spec.md#L3447); implementation assessed separately. | - |

### Integration and Test Coverage

| Item | Original state | Status | Assessment and evidence | Follow-up |
| --- | --- | --- | --- | --- |
| [CHK001](checklists/integration-and-test-coverage.md#L15) | [x] | IMPLEMENTED | Migration trip-wire literal explicitly quoted [FR002](spec.md#L2322). | - |
| [CHK002](checklists/integration-and-test-coverage.md#L16) | [x] | IMPLEMENTED | Explicit migration-test purpose retained [FR002](spec.md#L2322). | - |
| [CHK003](checklists/integration-and-test-coverage.md#L17) | [x] | IMPLEMENTED | Exact prefix including trailing ASCII space defined [FR035](spec.md#L2691). | - |
| [CHK004](checklists/integration-and-test-coverage.md#L18) | [x] | IMPLEMENTED | Canonical English watermark explicitly defined [FR039](spec.md#L2701). | - |
| [CHK005](checklists/integration-and-test-coverage.md#L22) | [x] | IMPLEMENTED | Nine signal categories explicit [SIGNAL]. | - |
| [CHK006](checklists/integration-and-test-coverage.md#L23) | [x] | IMPLEMENTED | Five/four safety-category definition explicit [FR010](spec.md#L2440). | - |
| [CHK007](checklists/integration-and-test-coverage.md#L24) | [x] | IMPLEMENTED | Three confidence values explicit [SIGNAL]. | - |
| [CHK008](checklists/integration-and-test-coverage.md#L25) | [x] | IMPLEMENTED | Six operational roles plus injection service explicitly enumerated [TOOLS]/[INVOKER]. | - |
| [CHK009](checklists/integration-and-test-coverage.md#L26) | [x] | IMPLEMENTED | Sixteen canonical map types enumerated [LAYERS]. | - |
| [CHK010](checklists/integration-and-test-coverage.md#L27) | [x] | IMPLEMENTED | Combat-agency per-jurisdiction definitions present [FR021](spec.md#L2561). | - |
| [CHK011](checklists/integration-and-test-coverage.md#L28) | [x] | IMPLEMENTED | Closed medical-brand set defined [FR024](spec.md#L2607). | - |
| [CHK012](checklists/integration-and-test-coverage.md#L29) | [x] | IMPLEMENTED | SES lead/QFD secondary definition explicit [FR021](spec.md#L2561). | - |
| [CHK013](checklists/integration-and-test-coverage.md#L30) | [x] | IMPLEMENTED | Egress channel/touchpoint sample space defined [SC006](spec.md#L3762). | - |
| [CHK014](checklists/integration-and-test-coverage.md#L31) | [x] | IMPLEMENTED | ACT policing intent distinction authored [FR021](spec.md#L2561). | - |
| [CHK015](checklists/integration-and-test-coverage.md#L35) | [x] | PARTIAL | Typed sections enumerated but common discriminator/current event names inconsistent [AUDIT]/[audit contract](contracts/audit-envelope.md#L31). | AUD-036-SIM-023 |
| [CHK016](checklists/integration-and-test-coverage.md#L36) | [x] | CONFLICT | Checklist calls30s soft; adapter specifies5s acknowledgement/30s read/120s hard [adapter contract](contracts/sub-agent-adapter.md#L208). | AUD-036-SIM-023 |
| [CHK017](checklists/integration-and-test-coverage.md#L40) | [x] | IMPLEMENTED | Five-step deterministic jurisdiction definition explicit [FR021](spec.md#L2526). | - |
| [CHK018](checklists/integration-and-test-coverage.md#L41) | [x] | IMPLEMENTED | Authoritative server lookup/fallback definition explicit [FR021](spec.md#L2526). | - |
| [CHK019](checklists/integration-and-test-coverage.md#L42) | [x] | IMPLEMENTED | Deterministic affinity requirement/helper explicit [LADDER]. | - |
| [CHK020](checklists/integration-and-test-coverage.md#L43) | [x] | IMPLEMENTED | Newest mutation/oldest creation tie-break specified [FR057](spec.md#L3007). | - |
| [CHK021](checklists/integration-and-test-coverage.md#L44) | [x] | PARTIAL | Definition clear but actual whole-outcome bytes nondeterministic [LESSONS]/[AAR-TEST]. | AUD-036-SIM-015 |
| [CHK022](checklists/integration-and-test-coverage.md#L48) | [x] | IMPLEMENTED | 10/15/30s category/cascade targets defined [FR028](spec.md#L2672)/[FR043](spec.md#L2787). | - |
| [CHK023](checklists/integration-and-test-coverage.md#L49) | [x] | IMPLEMENTED | Cascade trigger categories defined [MATRIX]/[FR043](spec.md#L2787). | - |
| [CHK024](checklists/integration-and-test-coverage.md#L50) | [x] | UNVERIFIED | 100 actual overlay observations unavailable; manufactured timing fixtures not measurement [SWEEP]. | AUD-036-SIM-024 |
| [CHK025](checklists/integration-and-test-coverage.md#L54) | [x] | PARTIAL | Current73 FR definitions/scenarios present, historical58-FR mapping not current full test coverage [TASKS]. | AUD-036-SIM-023, AUD-036-SIM-024 |
| [CHK026](checklists/integration-and-test-coverage.md#L55) | [x] | IMPLEMENTED | Sequential placement mirrored in [US01-AS05](spec.md#L1810). | - |
| [CHK027](checklists/integration-and-test-coverage.md#L56) | [x] | IMPLEMENTED | Hybrid confidence scenarios explicitly [US02-AS06](spec.md#L1866)/[US02-AS07](spec.md#L1871). | - |
| [CHK028](checklists/integration-and-test-coverage.md#L57) | [x] | IMPLEMENTED | Viewport/clarify/mismatch scenarios authored [US04-AS07](spec.md#L1964). | - |
| [CHK029](checklists/integration-and-test-coverage.md#L58) | [x] | IMPLEMENTED | Text bilingual/missing-locale scenarios authored [US05-AS06](spec.md#L2030). | - |
| [CHK030](checklists/integration-and-test-coverage.md#L59) | [x] | IMPLEMENTED | Audio bilingual/missing-locale scenarios authored [US05-AS08](spec.md#L2040). | - |
| [CHK031](checklists/integration-and-test-coverage.md#L60) | [x] | IMPLEMENTED | Sixth user-thread refusal scenario authored [US06-AS05](spec.md#L2088). | - |
| [CHK032](checklists/integration-and-test-coverage.md#L61) | [x] | IMPLEMENTED | Cascade annotation/tie scenarios authored [US06-AS06](spec.md#L2093). | - |
| [CHK033](checklists/integration-and-test-coverage.md#L62) | [x] | IMPLEMENTED | US1 independent-test trip-wire defined [US1](spec.md#L1768); not a current run. | - |
| [CHK034](checklists/integration-and-test-coverage.md#L63) | [x] | IMPLEMENTED | All nine story independent-test paragraphs read [US1](spec.md#L1768)/[US9](spec.md#L2192). | - |
| [CHK035](checklists/integration-and-test-coverage.md#L64) | [x] | IMPLEMENTED | US5 network-trace mock test requirement explicit [US5](spec.md#L1987). | - |
| [CHK036](checklists/integration-and-test-coverage.md#L65) | [x] | IMPLEMENTED | US3 wall-clock observation test requirement explicit [US3](spec.md#L1879). | - |
| [CHK037](checklists/integration-and-test-coverage.md#L69) | [x] | IMPLEMENTED | Original12 quantitative SCs plus2 later criteria defined [SC section](spec.md#L3742). | - |
| [CHK038](checklists/integration-and-test-coverage.md#L70) | [x] | IMPLEMENTED | Baseline disables new injection/auto-fan-out explicitly [A8](spec.md#L1682). | - |
| [CHK039](checklists/integration-and-test-coverage.md#L71) | [x] | IMPLEMENTED | Seed/jurisdiction/hazard/telemetry pairing defined [A8](spec.md#L1682). | - |
| [CHK040](checklists/integration-and-test-coverage.md#L72) | [x] | IMPLEMENTED | Synthetic AIDR economic profile/no real data defined [A9](spec.md#L1686). | - |
| [CHK041](checklists/integration-and-test-coverage.md#L73) | [x] | UNVERIFIED | Continuous all-channel zero-egress/SEV0 result not demonstrated [COMMS]/[SWEEP]. | AUD-036-SIM-024 |
| [CHK042](checklists/integration-and-test-coverage.md#L74) | [x] | PARTIAL | Literal migration sweep is not every-PR complete receipt/render egress assertion [CI]. | AUD-036-SIM-003, AUD-036-SIM-024 |
| [CHK043](checklists/integration-and-test-coverage.md#L75) | [x] | UNVERIFIED | 30 multi-hazard exercise/no-collapse measurements not attributable [SWEEP]. | AUD-036-SIM-024 |
| [CHK044](checklists/integration-and-test-coverage.md#L79) | [x] | IMPLEMENTED | [Breaker](../../apps/api/app/services/simulation/parse_attempt_circuit_breaker.py#L1) constants resolve threshold handoff; active invocation separate. | - |
| [CHK045](checklists/integration-and-test-coverage.md#L80) | [x] | PARTIAL | Boundary helper/fixtures exist but authoritative deployed dataset and controller use unverified [TUPLES]/[CHAT]. | AUD-036-SIM-007, AUD-036-SIM-024 |
| [CHK046](checklists/integration-and-test-coverage.md#L81) | [x] | CONFLICT | Resource1800 resolution differs T-AA04 amended600 and fixed600 REST lookup [ROUTE]. | AUD-036-SIM-006, AUD-036-SIM-023 |
| [CHK047](checklists/integration-and-test-coverage.md#L82) | [x] | PARTIAL | Table names/claimed delta threshold not actual ambiguity controller guard [CHAT]. | AUD-036-SIM-007 |
| [CHK048](checklists/integration-and-test-coverage.md#L83) | [x] | CONFLICT | 11-locale MVP cannot satisfy30-plus current requirement [LOCALES]/[WATERMARK]. | AUD-036-SIM-014, AUD-036-SIM-023 |
| [CHK049](checklists/integration-and-test-coverage.md#L84) | [x] | PARTIAL | Freshness config not actual outage-window consumer/recovery [DEGRADED]. | AUD-036-SIM-022 |
| [CHK050](checklists/integration-and-test-coverage.md#L85) | [x] | CONFLICT | Depth<=2 prose versus binding depth1/refuse2; helper not active [CASCADE]. | AUD-036-SIM-011, AUD-036-SIM-023 |
| [CHK051](checklists/integration-and-test-coverage.md#L89) | [x] | PARTIAL | Deterministic fixture catalog not actual30 active multi-hazard exercises [LADDER]/[SWEEP]. | AUD-036-SIM-024 |
| [CHK052](checklists/integration-and-test-coverage.md#L90) | [x] | PARTIAL | Different helper suites do not form active nine-category/three-confidence ingress matrix [PIPE-TEST]. | AUD-036-SIM-006 |
| [CHK053](checklists/integration-and-test-coverage.md#L91) | [x] | PARTIAL | Alert/HTTP-wrapper test not all direct SDK trace safety [COMMS]. | AUD-036-SIM-003 |
| [CHK054](checklists/integration-and-test-coverage.md#L92) | [x] | PARTIAL | Stub sweep cannot establish all-channel exact receipt CI gate [CI]. | AUD-036-SIM-024 |
| [CHK055](checklists/integration-and-test-coverage.md#L93) | [x] | PARTIAL | Helper/cassette replay not full actual cascade audit reconstruction [LADDER]/[LESSONS]. | AUD-036-SIM-011, AUD-036-SIM-015 |
| [CHK056](checklists/integration-and-test-coverage.md#L94) | [x] | PARTIAL | Registry membership tests not active location/intent/clarify routing [TUPLE-TEST]. | AUD-036-SIM-007 |
| [CHK057](checklists/integration-and-test-coverage.md#L95) | [x] | PARTIAL | Thread-cap concurrency and enum tests not persisted simultaneous contradiction/rerun assertions [INJECT]. | AUD-036-SIM-006 |
| [CHK058](checklists/integration-and-test-coverage.md#L96) | [x] | PARTIAL | Load CSV checker permits wrong/missing metrics, local cap not replicated five-thread enforcement [CAP]/[GATE]. | AUD-036-SIM-011, AUD-036-SIM-019 |

### Requirements Quality and Adapter Review

`REQ-ITEMnn` preserves the sixteen original unnumbered criteria in source order. `ADAPTER-ITEMnn` preserves the five unnumbered adapter acceptance bullets. The two `SPEC-QUOTE` rows are quoted CHK237 alternatives, not separate quality-checklist requirements.

| Item | Original state | Status | Assessment and evidence | Follow-up |
| --- | --- | --- | --- | --- |
| [REQ-ITEM01](checklists/requirements.md#L9) | [x] | CONFLICT | No implementation detail claim obsolete: [FR073](spec.md#L3666) names files/KQL/test algorithm. | AUD-036-SIM-023 |
| [REQ-ITEM02](checklists/requirements.md#L10) | [x] | IMPLEMENTED | Coordinator/operational value explicitly stated [US1](spec.md#L1768). | - |
| [REQ-ITEM03](checklists/requirements.md#L11) | [x] | PARTIAL | Story language accessible; extensive code/SDK/algorithm amendments technical [FR073](spec.md#L3666). | AUD-036-SIM-023 |
| [REQ-ITEM04](checklists/requirements.md#L12) | [x] | IMPLEMENTED | All mandatory spec sections present in complete [spec](spec.md#L1608). | - |
| [REQ-ITEM05](checklists/requirements.md#L16) | [x] | IMPLEMENTED | Current clarify decisions closed; historical quoted NEEDS markers are not unfilled current decisions [C5]. | - |
| [REQ-ITEM06](checklists/requirements.md#L17) | [x] | CONFLICT | Trigger-source/success coexistence/HTTP/SLI contradictions remain [CONTRACT]/[ERRORS]. | AUD-036-SIM-023 |
| [REQ-ITEM07](checklists/requirements.md#L18) | [x] | IMPLEMENTED | Quantitative thresholds/sample counts explicit [SC section](spec.md#L3742). | - |
| [REQ-ITEM08](checklists/requirements.md#L19) | [x] | CONFLICT | Technology-agnostic claim no longer true for model/gate-specific [SC013](spec.md#L3791). | AUD-036-SIM-023 |
| [REQ-ITEM09](checklists/requirements.md#L20) | [x] | IMPLEMENTED | 54 story scenarios and59 amendment acceptance bullets enumerated. [US1](spec.md#L1768). | - |
| [REQ-ITEM10](checklists/requirements.md#L21) | [x] | IMPLEMENTED | 21 explicit edges defined [edge section](spec.md#L2240). | - |
| [REQ-ITEM11](checklists/requirements.md#L22) | [x] | IMPLEMENTED | Additive feature/non-goals and cycle lock scopes defined [overview](spec.md#L1608). | - |
| [REQ-ITEM12](checklists/requirements.md#L23) | [x] | IMPLEMENTED | 12 assumptions and dependent surfaces explicit [A1](spec.md#L1660). | - |
| [REQ-ITEM13](checklists/requirements.md#L27) | [x] | PARTIAL | Current FRs have observable criteria, but unresolved contradictions weaken clarity [FR067](spec.md#L3540). | AUD-036-SIM-023 |
| [REQ-ITEM14](checklists/requirements.md#L28) | [x] | IMPLEMENTED | Nine stories cover main flows and P2/P3 obligations [US1](spec.md#L1768)/[US9](spec.md#L2192). | - |
| [REQ-ITEM15](checklists/requirements.md#L29) | [x] | UNVERIFIED | Mapping outcomes to SCs is not measured achievement [SWEEP]. | AUD-036-SIM-024 |
| [REQ-ITEM16](checklists/requirements.md#L30) | [x] | CONFLICT | Same obsolete no-implementation-details claim as ITEM01, later explicit Python/KQL contract [FR073](spec.md#L3666). | AUD-036-SIM-023 |
| [ADAPTER-ITEM01](contracts/sub-agent-adapter.md#L267) | [ ] | PARTIAL | [DISPATCH] role-prompt answer/unmarked fallback not real operational response. | AUD-036-SIM-004 |
| [ADAPTER-ITEM02](contracts/sub-agent-adapter.md#L268) | [ ] | PARTIAL | Filter exists but empty dispatcher citations do not prove tenant-grounded resource answers [ADAPTER]. | AUD-036-SIM-004 |
| [ADAPTER-ITEM03](contracts/sub-agent-adapter.md#L269) | [ ] | PARTIAL | Dispatcher hash returned, active provenance discarded/not persisted [DISPATCH]/[CHAT]. | AUD-036-SIM-004 |
| [ADAPTER-ITEM04](contracts/sub-agent-adapter.md#L270) | [ ] | PARTIAL | Dynamic deployment/registry mismatch and optional fallback value [DISPATCH]/[REGISTRY]. | AUD-036-SIM-026 |
| [ADAPTER-ITEM05](contracts/sub-agent-adapter.md#L271) | [ ] | IMPLEMENTED | Old trip-wire literal no longer active return [INVOKER]/[DISPATCH]; different stub-like fallback separate. | - |
| [SPEC-QUOTE01](spec.md#L6389) | [ ] | SUPERSEDED | Quoted shorter CHK237 proposal, not live checkbox; [close](spec.md#L6473) retains original locked checklist text. | - |
| [SPEC-QUOTE02](spec.md#L6410) | [ ] | UNVERIFIED | Proposed revised CHK237 wording not adopted by [close](spec.md#L6473); immutability claim requires historical bytes. | AUD-036-SIM-024 |

### Quality Across Cycles Two Through Five

| Item | Original state | Status | Assessment and evidence | Follow-up |
| --- | --- | --- | --- | --- |
| [CHK101](checklists/quality.md#L39) | [ ] | IMPLEMENTED | Eight A2 amendments enumerated in [amendment log](spec.md#L106). | - |
| [CHK102](checklists/quality.md#L42) | [ ] | IMPLEMENTED | Detail/acceptance blocks present; A2-08 explicitly folded into A2-01 [spec](spec.md#L119). | - |
| [CHK103](checklists/quality.md#L45) | [ ] | CONFLICT | FR067 specified but success-event coexistence/older subset prose conflict [FR067](spec.md#L3540). | AUD-036-SIM-023 |
| [CHK104](checklists/quality.md#L49) | [ ] | IMPLEMENTED | Canonical cascade/round-trip rule explicitly [FR068](spec.md#L3574). | - |
| [CHK105](checklists/quality.md#L52) | [ ] | PARTIAL | Required audit-array definition exists, contextual trigger-source contradictions remain [FR069](spec.md#L3592). | AUD-036-SIM-023 |
| [CHK106](checklists/quality.md#L55) | [ ] | IMPLEMENTED | Nine-name canonical/write/read compatibility rule explicit [FR070](spec.md#L3604). | - |
| [CHK107](checklists/quality.md#L58) | [ ] | IMPLEMENTED | Freshness/threshold/sample staging criterion explicitly [SC013](spec.md#L3791). | - |
| [CHK108](checklists/quality.md#L62) | [ ] | UNVERIFIED | Synthesis count/provenance claim not independently attributable [spec log](spec.md#L86). | AUD-036-SIM-024 |
| [CHK109](checklists/quality.md#L68) | [ ] | IMPLEMENTED | All-attempted body/audit Q1 supersession explicitly recorded [Cycle2Q1](spec.md#L394). | - |
| [CHK110](checklists/quality.md#L72) | [ ] | IMPLEMENTED | Trailing24h decision explicitly recorded [Cycle2 clarify](spec.md#L380). | - |
| [CHK111](checklists/quality.md#L75) | [ ] | IMPLEMENTED | YAML-removal/import/alias decision present [MATRIX]/[CASCADE]. | - |
| [CHK112](checklists/quality.md#L79) | [ ] | IMPLEMENTED | Per-subscriber UUID and lex ordering defined/constructed [PIPE]. | - |
| [CHK113](checklists/quality.md#L82) | [ ] | IMPLEMENTED | Explicit allow-list selected and [route constant](../../apps/api/app/middleware/spec_036_routes.py#L1) exists. | - |
| [CHK114](checklists/quality.md#L86) | [ ] | IMPLEMENTED | Three statuses/5s constant defined [dispatch status](../../apps/api/app/services/simulation/dispatch_status.py#L1). | - |
| [CHK115](checklists/quality.md#L90) | [ ] | IMPLEMENTED | Always-present false-default model [Ack](../../apps/api/app/api/routes/simulations_036.py#L103). | - |
| [CHK116](checklists/quality.md#L94) | [ ] | IMPLEMENTED | Hybrid trace-context/customDimensions decision authored [Cycle2P2](spec.md#L689); active span creation remains partial. | AUD-036-SIM-019 |
| [CHK117](checklists/quality.md#L97) | [ ] | IMPLEMENTED | Floor30 and sample_count rule defined [GATE]/[KQL]; actual samples unverified. | - |
| [CHK118](checklists/quality.md#L100) | [ ] | IMPLEMENTED | 4xx+5xx allow-list and2xx warning carve-out defined [error contract](contracts/error-responses.md#L194). | - |
| [CHK119](checklists/quality.md#L106) | [ ] | IMPLEMENTED | Current [audit success schema](contracts/audit-envelope.md#L151) includes required array/status; old readiness gap filled. | - |
| [CHK120](checklists/quality.md#L111) | [ ] | IMPLEMENTED | [Dispatch-failure schema](contracts/audit-envelope.md#L607) authored with required views/hash/error fields. | - |
| [CHK121](checklists/quality.md#L116) | [ ] | IMPLEMENTED | Canonical9 enum exists in [AIIMS]/[audit schema](contracts/audit-envelope.md#L149). | - |
| [CHK122](checklists/quality.md#L119) | [ ] | IMPLEMENTED | [Error contract](contracts/error-responses.md#L194) explicitly narrows scope; middleware behavior separate. | - |
| [CHK123](checklists/quality.md#L125) | [ ] | IMPLEMENTED | [SLI contract](contracts/sli-thresholds.md#L210) adds Z6/Z7/ref fields. | - |
| [CHK124](checklists/quality.md#L130) | [ ] | IMPLEMENTED | [KQL]/[KQL-TEST] include metric and sample_count columns. | - |
| [CHK125](checklists/quality.md#L137) | [ ] | IMPLEMENTED | Primacy-of-life gate rationale explicitly [SC013](spec.md#L3791). | - |
| [CHK126](checklists/quality.md#L141) | [ ] | IMPLEMENTED | Canonical AIIMS names/tags preserved [AIIMS]/[RECORD]. | - |
| [CHK127](checklists/quality.md#L145) | [ ] | IMPLEMENTED | No new AWS tier in Cycle2 definitions [FR027](spec.md#L2656). | - |
| [CHK128](checklists/quality.md#L149) | [ ] | UNVERIFIED | Data-plane residency/deployment not proven by design statement [ROOT]/[INFRA]. | AUD-036-SIM-020, AUD-036-SIM-024 |
| [CHK129](checklists/quality.md#L153) | [ ] | IMPLEMENTED | Amendment grants no autonomous real-action permission [FR067](spec.md#L3540); safety code gaps separate. | - |
| [CHK130](checklists/quality.md#L157) | [ ] | PARTIAL | Reuse declared, actual raw-resource composition/selected-root binding not AVM proof [INFRA]. | AUD-036-SIM-020 |
| [CHK131](checklists/quality.md#L160) | [ ] | IMPLEMENTED | No new config service required by YAML-removal decision [MATRIX]/[PLAN]. | - |
| [CHK132](checklists/quality.md#L164) | [ ] | IMPLEMENTED | Explicit degradation and bounded legacy error scope rationale authored [FR067](spec.md#L3540). | - |
| [CHK133](checklists/quality.md#L172) | [ ] | IMPLEMENTED | Unit/integration/contract targets identified [T-AA14](tasks.md#L1466); active proof separately partial. | - |
| [CHK134](checklists/quality.md#L177) | [ ] | IMPLEMENTED | Alias/YAML/round-trip targets identified [T-AA20](tasks.md#L1534). | - |
| [CHK135](checklists/quality.md#L182) | [ ] | IMPLEMENTED | Body/audit JCS test targets identified [T-AA15](tasks.md#L1476). | - |
| [CHK136](checklists/quality.md#L186) | [ ] | IMPLEMENTED | Enum/historical-read targets identified [T-AA10](tasks.md#L1422). | - |
| [CHK137](checklists/quality.md#L190) | [ ] | IMPLEMENTED | Gate/floor/schema test targets identified [T-AA17](tasks.md#L1500). | - |
| [CHK138](checklists/quality.md#L195) | [ ] | PARTIAL | Allow-list tests exist, full specific4xx/5xx headers/extensions not covered [ERRORS]. | AUD-036-SIM-023 |
| [CHK139](checklists/quality.md#L202) | [ ] | IMPLEMENTED | Breaking Ack field documented [changelog](../../CHANGELOG.md#L22)/[ledger](contracts/openapi-changelog.md#L12). | - |
| [CHK140](checklists/quality.md#L209) | [ ] | IMPLEMENTED | Structured item/per-edge migration documented [ledger](contracts/openapi-changelog.md#L12). | - |
| [CHK141](checklists/quality.md#L216) | [ ] | PARTIAL | Breaking enum documented, active historical readers not using shim [AUDIT]/[EXPORT]. | AUD-036-SIM-008 |
| [CHK142](checklists/quality.md#L221) | [ ] | IMPLEMENTED | Cycle2 declares shape changes, no new method/path requirement [ledger](contracts/openapi-changelog.md#L12). | - |
| [CHK143](checklists/quality.md#L229) | [ ] | PARTIAL | YAML removal migration note exists, historical quickstart/runbook references not fully reconciled [PLAN]/[TASKS]. | AUD-036-SIM-023 |
| [CHK144](checklists/quality.md#L233) | [ ] | PARTIAL | Migration helper not active export/lessons read path [AUDIT]/[EXPORT]. | AUD-036-SIM-008, AUD-036-SIM-015 |
| [CHK145](checklists/quality.md#L239) | [ ] | PARTIAL | Gate/floor docs exist; smoke invalid and operational evidence missing [SMOKE]/[WORKFLOW]. | AUD-036-SIM-017, AUD-036-SIM-024 |
| [CHK146](checklists/quality.md#L244) | [ ] | CONFLICT | Human utility Transport not canonical Logistics [MATRIX]/[human matrix](spec.md#L2817). | AUD-036-SIM-023 |
| [CHK147](checklists/quality.md#L251) | [ ] | PARTIAL | A2-01 specified, real subscriber/persist-failure semantics not complete [PIPE]/[ROUTE]. | AUD-036-SIM-005 |
| [CHK148](checklists/quality.md#L254) | [ ] | PARTIAL | A2-02 queries/helper exist, actual candidate gate/producers incomplete [WORKFLOW]/[CD]. | AUD-036-SIM-016, AUD-036-SIM-019 |
| [CHK149](checklists/quality.md#L257) | [ ] | PARTIAL | A2-03 matrix import/alias supported, actual round-trip targets incomplete [CASCADE]. | AUD-036-SIM-011 |
| [CHK150](checklists/quality.md#L260) | [ ] | PARTIAL | A2-04 JCS supported but durable outcome/audit integration deficient [AUDIT]. | AUD-036-SIM-008 |
| [CHK151](checklists/quality.md#L263) | [ ] | PARTIAL | A2-05 bounded MIME supported, specific error schemas lost [ERRORS]. | AUD-036-SIM-023 |
| [CHK152](checklists/quality.md#L266) | [ ] | IMPLEMENTED | A2-06 caller literal removed and warning guard implemented [AUDIT]. | - |
| [CHK153](checklists/quality.md#L269) | [ ] | PARTIAL | A2-07 enum/helper supported, active historical reader compatibility incomplete [AUDIT]. | AUD-036-SIM-008 |
| [CHK154](checklists/quality.md#L272) | [ ] | IMPLEMENTED | A2-08 explicitly folded into typed entry25, no duplicate FR [audit contract](contracts/audit-envelope.md#L607). | - |
| [CHK155](checklists/quality.md#L275) | [ ] | IMPLEMENTED | Deferred extra hazard/low findings recorded [reconciliation](spec.md#L222), not waiver of original FRs. | - |
| [CHK156](checklists/quality.md#L280) | [ ] | UNVERIFIED | Aggregate synthesis severity/approval convergence not independent source proof [spec log](spec.md#L86). | AUD-036-SIM-024 |
| [CHK157](checklists/quality.md#L304) | [ ] | PARTIAL | Helper now invoked, omitted SLIs/collation/CD bypass remain [WORKFLOW]/[GATE]. | AUD-036-SIM-016, AUD-036-SIM-018 |
| [CHK158](checklists/quality.md#L312) | [ ] | PARTIAL | POST/OIDC added but payload/UUID invalid [SMOKE]. | AUD-036-SIM-017 |
| [CHK159](checklists/quality.md#L318) | [ ] | IMPLEMENTED | Actual public helper citation corrected [ADR010](../../docs/aidr/decisions/ADR-036-010-cycle-2-amendment-cycle.md#L87). | - |
| [CHK160](checklists/quality.md#L322) | [ ] | IMPLEMENTED | Correct model bands in [ADR010](../../docs/aidr/decisions/ADR-036-010-cycle-2-amendment-cycle.md#L83)/[changelog](../../CHANGELOG.md#L35). | - |
| [CHK161](checklists/quality.md#L327) | [ ] | IMPLEMENTED | [KQL] current Z6 has required dimensions/filter; downstream collation separately defective. | - |
| [CHK162](checklists/quality.md#L334) | [ ] | IMPLEMENTED | [KQL] Z7 clock difference/filter and99.0 breach fixed. | - |
| [CHK163](checklists/quality.md#L341) | [ ] | IMPLEMENTED | Six A3 amendments enumerated [Cycle3 table](spec.md#L267). | - |
| [CHK164](checklists/quality.md#L345) | [ ] | IMPLEMENTED | SC014 nonzero/no-tag/no-deploy fixture rule explicitly defined [SC014](spec.md#L3804). | - |
| [CHK165](checklists/quality.md#L353) | [ ] | IMPLEMENTED | Six-step string canonicalisation/AST rejection explicitly [C3Q1](spec.md#L838). | - |
| [CHK166](checklists/quality.md#L360) | [ ] | SUPERSEDED | OIDC rule retained; exclusive smoke-partition wording explicitly superseded [A4-02](spec.md#L3907). | AUD-036-SIM-020 |
| [CHK167](checklists/quality.md#L369) | [ ] | IMPLEMENTED | Distinct refusal/before-raise rule explicitly [C3Q3](spec.md#L1016). | - |
| [CHK168](checklists/quality.md#L376) | [ ] | IMPLEMENTED | Fixture-only/four-red/four-invariant canary rule explicitly [C3Q4](spec.md#L1099). | - |
| [CHK169](checklists/quality.md#L386) | [ ] | IMPLEMENTED | All-seven universal canonicalisation scope explicitly [C3Q5](spec.md#L1183). | - |
| [CHK170](checklists/quality.md#L392) | [ ] | IMPLEMENTED | Slot3.26/count26/gap preservation explicitly [C3P2Q1](spec.md#L1308). | - |
| [CHK171](checklists/quality.md#L399) | [ ] | IMPLEMENTED | Canonicaliser API/path override/errors explicitly [C3P2Q2](spec.md#L1388). | - |
| [CHK172](checklists/quality.md#L410) | [ ] | IMPLEMENTED | Co-merge/preceding contracts definition explicit [C3P2Q3](spec.md#L1484); historical merge proof not inferred. | - |
| [CHK173](checklists/quality.md#L420) | [ ] | IMPLEMENTED | Eight refusal detail fields declared [entry26](contracts/audit-envelope.md#L672). | - |
| [CHK174](checklists/quality.md#L430) | [ ] | IMPLEMENTED | Entry26 local discriminator declared [schema](contracts/audit-envelope.md#L672); common enum omission separate. | - |
| [CHK175](checklists/quality.md#L435) | [ ] | IMPLEMENTED | Top-level correlation equality rule stated [schema](contracts/audit-envelope.md#L672). | - |
| [CHK176](checklists/quality.md#L440) | [ ] | PARTIAL | Narrative count26 updated, common discriminator still25 [audit contract](contracts/audit-envelope.md#L31). | AUD-036-SIM-023 |
| [CHK177](checklists/quality.md#L449) | [ ] | IMPLEMENTED | Contract3.20-3.24 gap retained before3.25/3.26 [audit contract](contracts/audit-envelope.md#L607). | - |
| [CHK178](checklists/quality.md#L453) | [ ] | IMPLEMENTED | No caller sequence1 literal required in entry26; allocator ownership defined [schema](contracts/audit-envelope.md#L672). | - |
| [CHK179](checklists/quality.md#L462) | [ ] | PARTIAL | [KQL-CANON] no skip/xfail, historical green-at-merge not attributable. | AUD-036-SIM-024 |
| [CHK180](checklists/quality.md#L468) | [ ] | IMPLEMENTED | [KQL-CANON] dynamically enumerates all SLIs. | - |
| [CHK181](checklists/quality.md#L476) | [ ] | PARTIAL | Four red fixtures exist, actual workflow/tagging and durable refusal invariants incomplete [GATE-TEST]. | AUD-036-SIM-016, AUD-036-SIM-018 |
| [CHK182](checklists/quality.md#L488) | [ ] | IMPLEMENTED | [Threshold regression](../../tests/docs/test_adr_036_010_threshold_drift.py#L1) authored numeric comparisons. | - |
| [CHK183](checklists/quality.md#L496) | [ ] | IMPLEMENTED | [Symbol regression](../../tests/docs/test_adr_036_010_symbol_citations.py#L1) authored resolution assertions. | - |
| [CHK184](checklists/quality.md#L505) | [ ] | IMPLEMENTED | [Canonicaliser](../../tests/contract/_kql_canonicaliser.py#L1) matches selected public normalization surface. | - |
| [CHK185](checklists/quality.md#L513) | [ ] | IMPLEMENTED | [Golden tests](../../tests/contract/test_kql_canonicaliser_unit.py#L1) cover six steps/determinism/idempotence source assertions. | - |
| [CHK186](checklists/quality.md#L518) | [ ] | PARTIAL | Concurrent captured envelopes/UUIDs not durable rows and two nonzero process exits [concurrency test](../../tests/integration/test_staging_promotion_concurrency.py#L66). | AUD-036-SIM-018 |
| [CHK187](checklists/quality.md#L524) | [ ] | SUPERSEDED | Exclusive-partition assertion replaced by database-scope evidence via [A4-02](spec.md#L3907); effective role still unverified. | AUD-036-SIM-020 |
| [CHK188](checklists/quality.md#L530) | [ ] | IMPLEMENTED | [Workflow concurrency](../../.github/workflows/staging-promotion.yml#L1) group/cancel-in-progress false present. | - |
| [CHK189](checklists/quality.md#L536) | [ ] | PARTIAL | Gate default logging/optional JSONL not allocator-backed durable writer [sink](../../tests/staging_gates.py#L144). | AUD-036-SIM-018 |
| [CHK190](checklists/quality.md#L542) | [ ] | IMPLEMENTED | [KQL]/[canonical contract](contracts/sli-thresholds.md#L230) include smoke tenant filters. | - |
| [CHK191](checklists/quality.md#L548) | [ ] | IMPLEMENTED | [Canonicalisation subsection](contracts/sli-thresholds.md#L467) documents API/errors/path resolution. | - |
| [CHK192](checklists/quality.md#L554) | [ ] | IMPLEMENTED | Relocated/numbered [ADR011](../../docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md#L155) records OIDC/co-merge choice, not approval proof. | - |
| [CHK193](checklists/quality.md#L563) | [ ] | IMPLEMENTED | [FR071](spec.md#L3625)/[FR072](spec.md#L3647)/[FR073](spec.md#L3666)/[SC014](spec.md#L3804) current wording propagated. | - |
| [CHK194](checklists/quality.md#L575) | [ ] | IMPLEMENTED | [Tasks co-merge block](tasks.md#L1839) defines preceding contract dependency; actual PR sequence unverified. | - |
| [CHK195](checklists/quality.md#L585) | [ ] | UNVERIFIED | Scope description supported, claimed six-defect closure not source-complete [WORKFLOW]/[SMOKE]. | AUD-036-SIM-024 |
| [CHK196](checklists/quality.md#L591) | [ ] | UNVERIFIED | Sentinel authorship present, original five-versus-six gate wording/history not runtime verification [C5]. | AUD-036-SIM-024 |
| [CHK197](checklists/quality.md#L622) | [ ] | IMPLEMENTED | [KQL] current Z7 deployment extend present in required position. | - |
| [CHK198](checklists/quality.md#L630) | [ ] | IMPLEMENTED | [Canonical Z7](contracts/sli-thresholds.md#L276) symmetric extend present. | - |
| [CHK199](checklists/quality.md#L637) | [ ] | UNVERIFIED | [KQL-CANON] assertions present; no current seven-SLI execution receipt. | AUD-036-SIM-024 |
| [CHK200](checklists/quality.md#L644) | [ ] | IMPLEMENTED | Two Cycle4 amendments and FR073 strengthening defined [A4 log](spec.md#L3842). | - |
| [CHK201](checklists/quality.md#L650) | [ ] | IMPLEMENTED | [ADR011 Cycle4](../../docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md#L610) appended with corrective decisions. | - |
| [CHK202](checklists/quality.md#L658) | [ ] | CONFLICT | Absolute no-rewrite wording conflicts same-cycle explicit in-place172 revision [A4-02](spec.md#L3907); permitted exception must stay explicit. | AUD-036-SIM-023 |
| [CHK203](checklists/quality.md#L666) | [ ] | IMPLEMENTED | [ADR011](../../docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md#L172) current three-clause acknowledgement authored. | - |
| [CHK204](checklists/quality.md#L678) | [ ] | UNVERIFIED | Accepted status authored, clean cohort timing/approval not evidenced [ADR status](../../docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md#L3). | AUD-036-SIM-024 |
| [CHK205](checklists/quality.md#L686) | [ ] | IMPLEMENTED | [A4-02](spec.md#L3907) expressly supersedes old mirror while preserving locked siblings. | - |
| [CHK206](checklists/quality.md#L696) | [ ] | UNVERIFIED | Local issue84 links not actual creation/body/label provenance [changelog](../../CHANGELOG.md#L15). | AUD-036-SIM-024 |
| [CHK207](checklists/quality.md#L711) | [ ] | IMPLEMENTED | [KQL-WALK] test parametrises declared SLI list, not fixed subset. | - |
| [CHK208](checklists/quality.md#L718) | [ ] | IMPLEMENTED | [KQL-WALK] consumes existing canonicaliser surface. | - |
| [CHK209](checklists/quality.md#L725) | [ ] | IMPLEMENTED | [KQL-WALK] static base-table map, no remote lookup. | - |
| [CHK210](checklists/quality.md#L732) | [ ] | PARTIAL | Walker precollects forward lets/retains projected-away columns [KQL-WALK]. | AUD-036-SIM-025 |
| [CHK211](checklists/quality.md#L742) | [ ] | IMPLEMENTED | [KQL-WALK] diagnostic includes SLI/name/line/query on recognised errors. | - |
| [CHK212](checklists/quality.md#L750) | [ ] | IMPLEMENTED | [KQL-WALK] union hard-fails rather than skip/pass. | - |
| [CHK213](checklists/quality.md#L760) | [ ] | PARTIAL | [Scope test](../../tests/contract/test_smoke_tenant_isolation.py#L174) regex searches whole Bicep for literal, not exclusive scope within specific emitted assignment. | AUD-036-SIM-020 |
| [CHK214](checklists/quality.md#L770) | [ ] | SUPERSEDED | OPTIONAL/minimal posture explicitly replaced by [Cycle5Q1](spec.md#L5496); current [SMOKE-TEST] required. | - |
| [CHK215](checklists/quality.md#L785) | [ ] | IMPLEMENTED | Lightweight lexer/no heavyweight parser decision defined [C4Q1](spec.md#L4008). | - |
| [CHK216](checklists/quality.md#L794) | [ ] | IMPLEMENTED | Dual wording/in-place ADR011 decision recorded [C4Q2](spec.md#L4094)/[C4Q5](spec.md#L4299). | - |
| [CHK217](checklists/quality.md#L805) | [ ] | IMPLEMENTED | GitHub-only/top-down/union-failure decisions defined [C4Q3](spec.md#L4170)/[C4Q4](spec.md#L4230). | - |
| [CHK218](checklists/quality.md#L815) | [ ] | SUPERSEDED | 3392/3398/minimal alternatives replaced by [single3400](spec.md#L5774); no execution credit. | AUD-036-SIM-024 |
| [CHK219](checklists/quality.md#L825) | [ ] | IMPLEMENTED | [Changelog](../../CHANGELOG.md#L13) grouped Cycle4 Added/Changed, no new Breaking section. | - |
| [CHK220](checklists/quality.md#L836) | [ ] | IMPLEMENTED | Review-gated/no-timed-auto-flip rule explicitly [C4Q3](spec.md#L4606); actual approval separate. | - |
| [CHK221](checklists/quality.md#L849) | [ ] | IMPLEMENTED | [KQL-WALK] no third-party Kusto parser/runtime dependency. | - |
| [CHK222](checklists/quality.md#L859) | [ ] | PARTIAL | No skip in [KQL-WALK], but green-at-merge/current validity not demonstrated. | AUD-036-SIM-025, AUD-036-SIM-024 |
| [CHK223](checklists/quality.md#L867) | [ ] | IMPLEMENTED | ADR directory bounded review found011 in-place and no012 replacement artifact [ADR011](../../docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md#L610). | - |
| [CHK224](checklists/quality.md#L875) | [ ] | UNVERIFIED | No alternative backlog artifact needed; historical PR side-effect absence not established from current tree [C5]. | AUD-036-SIM-024 |
| [CHK225](checklists/quality.md#L884) | [ ] | UNVERIFIED | External label inventory/mutation history not inspected [issue citation](../../CHANGELOG.md#L15). | AUD-036-SIM-024 |
| [CHK226](checklists/quality.md#L893) | [ ] | UNVERIFIED | Current preserved log alone not historical byte-immutability proof [A4 log](spec.md#L3842). | AUD-036-SIM-024 |
| [CHK227](checklists/quality.md#L908) | [ ] | PARTIAL | Corrected query/wording supported, gate/authorization outcomes not proven [KQL-WALK]/[GATE]/[AUTH]. | AUD-036-SIM-018, AUD-036-SIM-025 |
| [CHK228](checklists/quality.md#L922) | [ ] | SUPERSEDED | Prior obligations retained, minimal-count branch retired [Cycle5Q1](spec.md#L5496)/[single3400](spec.md#L5774). | AUD-036-SIM-024 |
| [CHK229](checklists/quality.md#L937) | [ ] | PARTIAL | Z7 undefined-column fixed, but refusal durability/other query failures still not complete [GATE]/[sink](../../tests/staging_gates.py#L144). | AUD-036-SIM-018 |
| [CHK230](checklists/quality.md#L953) | [ ] | UNVERIFIED | Sentinel chain recorded; execution/convergence not independently attributable [C5]. | AUD-036-SIM-024 |
| [CHK231](checklists/quality.md#L985) | [ ] | IMPLEMENTED | Current [role block](../../infra/bicep/modules/cosmos-simulation-containers.bicep#L305) corrected; historical byte-equality not certified. | - |
| [CHK232](checklists/quality.md#L997) | [ ] | PARTIAL | Four-clause order source-supported; qualitative cohort review not attributable [role block](../../infra/bicep/modules/cosmos-simulation-containers.bicep#L305). | AUD-036-SIM-024 |
| [CHK233](checklists/quality.md#L1013) | [ ] | IMPLEMENTED | [SMOKE-TEST]/[header](../../tests/contract/test_smoke_tenant_isolation.py#L162) REQUIRED without runtime marker. | - |
| [CHK234](checklists/quality.md#L1030) | [ ] | IMPLEMENTED | [SMOKE-TEST] exact two lower()+in absence assertions present. | - |
| [CHK235](checklists/quality.md#L1045) | [ ] | PARTIAL | Both presence assertions/helper remain [SMOKE-TEST]; historical byte-identical preservation not independently compared. | AUD-036-SIM-024 |
| [CHK236](checklists/quality.md#L1063) | [ ] | UNVERIFIED | Single3400/no-qualifier test posture defined, no current execution result [C5]. | AUD-036-SIM-024 |
| [CHK237](checklists/quality.md#L1080) | [ ] | UNVERIFIED | Quoted historical anchors/mirror bytes not revalidated against original commits; [close](spec.md#L6473) explicitly carries drift. | AUD-036-SIM-024 |
| [CHK238](checklists/quality.md#L1095) | [ ] | PARTIAL | [ADR011 Cycle5](../../docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md#L1066) exists, status-transition provenance not independently verified. | AUD-036-SIM-024 |
| [CHK239](checklists/quality.md#L1114) | [ ] | UNVERIFIED | Locked stale mirrors retained by explicit rule [A4-02](spec.md#L3907); historical byte preservation unverified. | AUD-036-SIM-024 |
| [CHK240](checklists/quality.md#L1124) | [ ] | IMPLEMENTED | [Changelog](../../CHANGELOG.md#L7) Cycle5 Added/Changed structure/provenance exists. | - |
| [CHK241](checklists/quality.md#L1137) | [ ] | UNVERIFIED | Issue84 cited locally, open state/label/history not fetched [changelog](../../CHANGELOG.md#L15). | AUD-036-SIM-024 |
| [CHK242](checklists/quality.md#L1148) | [ ] | UNVERIFIED | No ruff product/source execution in audit; historical claim not current result [C5]. | AUD-036-SIM-024 |
| [CHK243](checklists/quality.md#L1162) | [ ] | IMPLEMENTED | [SMOKE-TEST] current required test has no skip/xfail/skipif decorator. | - |
| [CHK244](checklists/quality.md#L1178) | [ ] | UNVERIFIED | Sentinel/Accepted statement present, clean three-cohort approval/change timing unavailable [ADR status](../../docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md#L3). | AUD-036-SIM-024 |

## Unnumbered Constraints and Assumptions

The following tables assess the remaining scope, persona, hypothesis, architecture, contract and edge obligations. These report-local keys do not create original tasks/requirements. Generic historical J/K task allocation remains UNVERIFIED, but their group surfaces and these independently specified obligations are still assessed. Technical details in later amendments do not silently retire original P2/P3 user stories.

| Constraint | Status | Assessment and evidence | Follow-up |
| --- | --- | --- | --- |
| [A1](spec.md#L1660) | PARTIAL | Provisioning inherited, but new UUID routes fail to resolve authenticated owning tenant [AUTH]/[TENANT]. | AUD-036-SIM-002 |
| [A2](spec.md#L1662) | UNVERIFIED | Shared AU model availability/actual deployment not proven; [DISPATCH] dynamically chooses deployment. | AUD-036-SIM-024, AUD-036-SIM-026 |
| [A3](spec.md#L1665) | PARTIAL | Coordinator-only invocation versus observer reads not consistently enforced on chat/outcome [AUTH]/[CHAT]. | AUD-036-SIM-002 |
| [A4](spec.md#L1669) | PARTIAL | Inherited public/HTTP dual guard assumption fails direct SDK predicate/publication boundary [COMMS]. | AUD-036-SIM-003 |
| [A5](spec.md#L1672) | PARTIAL | Base map exists; active tenant overlay stream and visual geometries missing [MAP-PAGE]/[MAP]. | AUD-036-SIM-001, AUD-036-SIM-012 |
| [A6](spec.md#L1676) | UNVERIFIED | Warp1 wall-clock measurement required; no executed timing evidence. Playback remains outside this audit's change scope. | AUD-036-SIM-024 |
| [A7](spec.md#L1679) | PARTIAL | Constitution read; life-safety, isolation, audit, egress and residency source gaps prevent blanket compliance [AUTH]/[AUDIT]/[COMMS]. | AUD-036-SIM-002, AUD-036-SIM-003, AUD-036-SIM-008 |
| [A8](spec.md#L1682) | UNVERIFIED | Matched baseline seed/jurisdiction/hazard/starting telemetry and disabled features defined, no attributable paired runs [SWEEP]. | AUD-036-SIM-024 |
| [A9](spec.md#L1686) | UNVERIFIED | Synthetic AIDR economic baseline/no real data rule defined; model outcome/privacy evidence not measured. | AUD-036-SIM-024 |
| [A10](spec.md#L1688) | PARTIAL | Five hazards plus sixth-user refusal/cascade annotation and three parallel sims are not effective through local [CAP]. | AUD-036-SIM-011 |
| [A11](spec.md#L1697) | PARTIAL | Curated bilingual text/audio,30 locales, deterministic fallback and no model prefixes incomplete [LOCALES]/[WATERMARK]. | AUD-036-SIM-014 |
| [A12](spec.md#L1714) | PARTIAL | One-hop/fresh-action rules implemented partly in helper, no actual controller cascade accounting [CASCADE]. | AUD-036-SIM-011 |
| [SCOPE-01](spec.md#L1608) | PARTIAL | Additive real agents/typed chat/routing/map goal unmet on active paths [DISPATCH]/[CHAT]/[MAP-PAGE]. | AUD-036-SIM-004, AUD-036-SIM-005, AUD-036-SIM-012 |
| [SCOPE-02](spec.md#L1638) | IMPLEMENTED | Non-goals: tenant provisioning, playback/time-warp, live base map and real-warning prohibition remain explicit; no such source modified in this audit. | - |
| [SCOPE-03](plan.md#L370) | UNVERIFIED | P1 together/P2 stretch/P3 later is phasing, not supersession; delivery of US6-US9 remains assessed and incomplete. | AUD-036-SIM-024 |
| [HYP-01](spec.md#L3748) | UNVERIFIED | 50% response/warning lead-time reduction hypothesis not demonstrated by role-prompt or fixture output. | AUD-036-SIM-024 |
| [HYP-02](spec.md#L3752) | UNVERIFIED | 24-hour earlier evacuation hypothesis needs paired scenario clock/control, not real-world prediction claim. | AUD-036-SIM-024 |
| [HYP-03](spec.md#L3756) | UNVERIFIED | 30% resource-efficiency/reallocation hypothesis unmeasured. | AUD-036-SIM-024 |
| [HYP-04](spec.md#L3759) | UNVERIFIED | 30% synthetic economic-loss reduction unmeasured; no real loss claim justified. | AUD-036-SIM-024 |
| [PERSONA-OPS](spec.md#L1653) | PARTIAL | Ten operational roles require unconditional IC/PIO/Extreme-risk approvals, primary AIIMS separation, progressive telemetry, full audit, scenario versioning and retriable AIDR. [CHAT]/[AUDIT]/[LESSONS] not complete; persona synthesis not human sign-off. | AUD-036-SIM-002, AUD-036-SIM-005, AUD-036-SIM-015 |
| [PERSONA-EAST](spec.md#L1654) | PARTIAL | Fifteen NSW/VIC/QLD roles: rural/urban split, SES leads, cyclone/sea telemetry, nonlinear surge, AWS/VICCodeRed/BOM, NSW explicit escalation, MRNSW/BOM and simultaneous agency threads. [TUPLES]/[MAP]/[CAP] only partial. Extra deferred hazard classes do not erase these original constraints. | AUD-036-SIM-007, AUD-036-SIM-011, AUD-036-SIM-012 |
| [PERSONA-OTHER](spec.md#L1655) | PARTIAL | Twenty-four SA/WA/TAS/NT/ACT roles: jurisdiction parity, DFES/TFS singles, dual fire, ESA-first, policing/medical brands and remote access. Registry data exists but active paths generic [TUPLES]/[DISPATCH]. | AUD-036-SIM-007 |
| [PERSONA-CROSS](spec.md#L1656) | PARTIAL | Nineteen cross-sector/federal roles require sandboxed BOM/GA, NEMA priority, simulation-only COMDISPLAN/DACC/channels, utility/transport/health effects, canonical centres, volunteer fatigue/resources and TripleZero. [CASCADE]/[NEMA]/[DEGRADED]/[COMMS] not connected. | AUD-036-SIM-003, AUD-036-SIM-011, AUD-036-SIM-021, AUD-036-SIM-022 |
| [PERSONA-TECH](spec.md#L237) | UNVERIFIED | Seventeen technical reviewer inputs are recorded in amendment rationale, not authenticated reviews. Their code/contract obligations are assessed individually above. | AUD-036-SIM-024 |
| [ARCH-01](research.md#L12) | PARTIAL | Bundle injection inside existing agent app, warm1/max3, no fourth app: sibling code exists but actual startup/selected-root deployment incomplete [DISPATCH]/[INFRA]. | AUD-036-SIM-020 |
| [ARCH-02](research.md#L43) | PARTIAL | Explicit correction selects API->agent async HTTP/pool50/20, imports only in agent runtime. HTTP adapters exist, dispatcher performs synchronous model call and operational handlers not used [ADAPTER]/[DISPATCH]. | AUD-036-SIM-004 |
| [ARCH-03](research.md#L54) | PARTIAL | Cosmos Session read-your-write and ordered EventHubs subscribers not supported by [PIPE] publish-only acknowledgements/session-token omission. | AUD-036-SIM-005, AUD-036-SIM-020 |
| [ARCH-04](research.md#L80) | PARTIAL | APIM/Redis plus60/min attempt/burst10/s/cooldown60 independent successful budget not active [INJECT]/[ROUTE]. | AUD-036-SIM-006 |
| [ARCH-05](research.md#L104) | PARTIAL | Registry then versioned ABS-SA4/STRtree boundary decision, deployed current-version data unverified and controller bypasses lookup [TUPLES]/[CHAT]. | AUD-036-SIM-007, AUD-036-SIM-024 |
| [ARCH-06](research.md#L125) | PARTIAL | Five retries/50ms exponential jitter for distributed cap versus actual local memory [CAP]. | AUD-036-SIM-011 |
| [ARCH-07](research.md#L164) | PARTIAL | Seven-year WORM/index/retriable deterministic versions not preserved by current [WORM]/[LESSONS]. | AUD-036-SIM-015 |
| [ARCH-08](research.md#L203) | PARTIAL | Abort direct-only, pause/resume tools share handler: registered tool names have no [CHAT] execution branch. | AUD-036-SIM-010 |
| [ARCH-09](research.md#L229) | CONFLICT | Category freshness table/resource30min differs T-AA04 ten-minute rule, no explicit comprehensive config alignment [ROUTE]. | AUD-036-SIM-006, AUD-036-SIM-023 |
| [ARCH-10](research.md#L259) | PARTIAL | Offline curated Speech prefixes/private5min audio URL requires actual approved assets and guarded runtime path [LOCALES-TEST]. | AUD-036-SIM-014, AUD-036-SIM-024 |
| [ARCH-11](research.md#L283) | UNVERIFIED | 150K/100K TPM, bounded retry,80%/95% thresholds and regional availability not demonstrated; [plan sizing](plan.md#L365) claims250K covers540K. | AUD-036-SIM-024, AUD-036-SIM-026 |
| [ARCH-12](research.md#L309) | PARTIAL | Per-role mini/full model split and strict injection JSON are not effective in shared dynamic [DISPATCH]/unregistered parser. | AUD-036-SIM-004, AUD-036-SIM-006 |
| [ARCH-13](research.md#L417) | PARTIAL | R13 distributed audit/50-allocator protocol not committed gap-free [AUDIT]/[SEQUENCE]. | AUD-036-SIM-008 |
| [ARCH-14](research.md#L443) | PARTIAL | R14 RFC9457 context-specific types/status/headers not preserved [ERRORS]. | AUD-036-SIM-023 |
| [ARCH-15](research.md#L466) | CONFLICT | R15 maintained canonical hashing supported [JCS], but proposed historical rehash conflicts append-only provenance/source-specific hashes. | AUD-036-SIM-008, AUD-036-SIM-023 |
| [ARCH-16](research.md#L482) | PARTIAL | R16 bounded dimensions/sampling/dashboard decisions exist, actual named boundary telemetry absent [KQL]/[PIPE]. | AUD-036-SIM-019 |
| [ARCH-17](research.md#L510) | PARTIAL | R17 polite live log/event-ID reconnect/shared locale/assertive priority banner incomplete [LIVELOG]. | AUD-036-SIM-013, AUD-036-SIM-021 |
| [ARCH-18](research.md#L534) | PARTIAL | R18 AIIMS doctrine data exists [AIIMS], active jurisdictional interpretation/approval remains incomplete. | AUD-036-SIM-007 |
| [RISK-REGISTER](research.md#L351) | PARTIAL | All12 risks read: consistency, hallucinated routing, TPM, depth2, watermark drift, geometry overflow, PII preimages, persist/publish repair, policy-version drift, fork bypass, SIGTERM cancellation and concurrent contradictions. Active outbox/recovery/isolation gaps remain [PIPE]/[AUDIT]/[CHAT]. | AUD-036-SIM-003, AUD-036-SIM-005, AUD-036-SIM-006, AUD-036-SIM-010 |
| [COST-ENVELOPE](research.md#L370) | UNVERIFIED | Historical AU$555 estimate/sizing, no current pricing/usage validation; linear-tripling arithmetic not supported. No pricing/cloud call made. | AUD-036-SIM-024 |
| [DATA-ENTITIES](spec.md#L3699) | PARTIAL | Six entities: signal, invocation, receipt, routing decision, overlay, outcome. Each has a schema/helper, but active provenance/consumer/storage completeness fails as assessed above. | AUD-036-SIM-004, AUD-036-SIM-006, AUD-036-SIM-012, AUD-036-SIM-015 |
| [CONTRACT-ADAPTER](contracts/sub-agent-adapter.md#L1) | PARTIAL | Existing callable preserved/three reply fields added; session token, timeout/audit/fingerprint and nonstub operational backend incomplete [ADAPTER]/[DISPATCH]. | AUD-036-SIM-004 |
| [CONTRACT-LLM](contracts/telemetry-injection-llm.md#L231) | PARTIAL | Strict-mode schema's optional/refusal properties violate stated all-required rule; no production parser callable, batch/provenance fields incomplete [INJECT]/[SIGNAL]. | AUD-036-SIM-006, AUD-036-SIM-023 |
| [CONTRACT-SSE](contracts/sse-map-overlay.md#L46) | CONFLICT | Six events/16layers/replay/snapshot defined, batch property absent from closed common schema; active endpoint/feed absent [MAP-PUBLISH]. | AUD-036-SIM-012, AUD-036-SIM-023 |
| [CONTRACT-CACHE](contracts/idempotency-cache.md#L1) | PARTIAL | OpaqueUTF8 length/RBAC-first/JCS/non-sliding24h/replay headers/lifecycle/crash window not connected to [CACHE]/[ROUTE]; extra model/spec charset conflicts unresolved. | AUD-036-SIM-009, AUD-036-SIM-023 |
| [CONTRACT-SLI](contracts/sli-thresholds.md#L113) | PARTIAL | 200 concurrent/P95<=3500ms/error<=1%, finite metrics/current candidate and target series not actual gate; query sampling/cardinality definitions need reconciliation [GATE]/[COLLATE]. | AUD-036-SIM-016, AUD-036-SIM-018, AUD-036-SIM-019 |
| [OPERATIONS-TESTING](plan.md#L403) | UNVERIFIED | Required unit/property/contract/integration/a11y/load/chaos CX036001-011 and human a11y evidence not established by historical counts [CI]/[SWEEP]. | AUD-036-SIM-024 |

### Edge Cases

| Edge | Status | Expected behavior and inspected assessment | Follow-up |
| --- | --- | --- | --- |
| [EDGE-01](spec.md#L2240) | PARTIAL | No parse -> clarify/audit/no write: fallback supports malformed refusal, full typed reason/provenance incomplete [INJECT]. | AUD-036-SIM-006 |
| [EDGE-02](spec.md#L2243) | PARTIAL | Low life-safety refuse versus non-life accept: no post-parse class/confidence gate [INJECT]. | AUD-036-SIM-006 |
| [EDGE-03](spec.md#L2248) | PARTIAL | Multiple signals individually written/shared correlation: singleton handler [INJECT]. | AUD-036-SIM-006 |
| [EDGE-04](spec.md#L2251) | PARTIAL | Sixth user hazard refuse/cascade annotate: local/disconnected [CAP]/[CASCADE]. | AUD-036-SIM-011 |
| [EDGE-05](spec.md#L2255) | PARTIAL | Missing jurisdiction resolves five steps or clarifies: active [CHAT] bypasses [TUPLES]. | AUD-036-SIM-007 |
| [EDGE-06](spec.md#L2259) | PARTIAL | Real-world action refuse/audit: regex/refusal text not every egress boundary [COMMS]/[INJECT]. | AUD-036-SIM-003 |
| [EDGE-07](spec.md#L2262) | PARTIAL | Hallucinated role/category refused: enums enforce structurally, typed audit incomplete [TOOLS]/[SIGNAL]. | AUD-036-SIM-008 |
| [EDGE-08](spec.md#L2264) | PARTIAL | NSW escalation explicit direction: not actual routing gate [CHAT]. | AUD-036-SIM-007 |
| [EDGE-09](spec.md#L2266) | PARTIAL | Contradiction accept/tag/rerun: returned IDs not persisted [INJECT]/[ROUTE]. | AUD-036-SIM-006 |
| [EDGE-10](spec.md#L2268) | PARTIAL | PII redaction/notification across transcript/payload/audit incomplete [INJECT]/[AUDIT]. | AUD-036-SIM-006 |
| [EDGE-11](spec.md#L2270) | PARTIAL | Live citation reject/degrade/audit: filter only partly implements full audit [ADAPTER]. | AUD-036-SIM-004 |
| [EDGE-12](spec.md#L2272) | PARTIAL | Large geometry/point overflow indicator with unmodified audit payload: no complete map feed/layers [MAP]. | AUD-036-SIM-012 |
| [EDGE-13](spec.md#L2275) | PARTIAL | RealLevel3 immediate priority/banner, no real suppression: governor unconsumed [NEMA]. | AUD-036-SIM-021 |
| [EDGE-14](spec.md#L2278) | PARTIAL | Observer UI hides writes/API refuses: role denial exists, owner/read/chat parity incomplete [AUTH]. | AUD-036-SIM-002 |
| [EDGE-15](spec.md#L2280) | PARTIAL | Concurrent contradictions both retained/notified/rerun: no reliable tag/consumption [SIGNALS]/[PIPE]. | AUD-036-SIM-006 |
| [EDGE-16](spec.md#L2283) | PARTIAL | Stale visual flag/Risk annotation: freshness helper not active update flow [MAP]/[PIPE]. | AUD-036-SIM-012 |
| [EDGE-17](spec.md#L2285) | PARTIAL | Browser close -> authoritative snapshot recovery: chat history exists, complete overlay/lifecycle replay absent [MAP-PAGE]/[STATE]. | AUD-036-SIM-010, AUD-036-SIM-012 |
| [EDGE-18](spec.md#L2287) | PARTIAL | Outside-role hazard refuse/audit: doctrinal tuple guard bypassed [CHAT]. | AUD-036-SIM-007 |
| [EDGE-19](spec.md#L2289) | PARTIAL | Parser flood separate breaker/no refusal quota spend: active probe/budget absent [ROUTE]. | AUD-036-SIM-006 |
| [EDGE-20](spec.md#L2296) | PARTIAL | Depth2 requires fresh action/correlation/accounting: helper refusal not controller-integrated [CASCADE]. | AUD-036-SIM-011 |
| [EDGE-21](spec.md#L2303) | PARTIAL | Mid-flight abort/cancel/lessons versus pause-step completion: unregistered calls/state split/no queue [CHAT]/[ROUTE]. | AUD-036-SIM-010, AUD-036-SIM-015 |

### Explicit Supersession and Clarification Ledger

No original task is waived merely because an amendment is narrower. Rows below record all clarification groups and their actual implementation assessment; individual later Q decisions are also covered by the exact quality checklist rows.

| Decision group | Status | Binding resolution and implementation assessment | Follow-up |
| --- | --- | --- | --- |
| [Original P1 Q1-Q5](spec.md#L1730) | PARTIAL | Cap/refusal-versus-annotation, English-first text, hybrid low-confidence, five-step jurisdiction and sequential injection first remain binding; [CAP]/[WATERMARK]/[INJECT]/[CHAT] not complete. | AUD-036-SIM-005, AUD-036-SIM-006, AUD-036-SIM-007, AUD-036-SIM-011, AUD-036-SIM-014 |
| [Original P2 Q1-Q5](spec.md#L1738) | PARTIAL | Bilingual audio, deterministic five-rank affinity, target-thread audit, server-winning viewport and successful-only quota remain binding; helpers not complete consumers. | AUD-036-SIM-006, AUD-036-SIM-007, AUD-036-SIM-011, AUD-036-SIM-014 |
| [Original P3 Q1-Q3](spec.md#L1746) | PARTIAL | Depth1/new action, lifecycle cancel/pause semantics and exact prompt fingerprint remain binding [CASCADE]/[CHAT]/[AUDIT]. | AUD-036-SIM-004, AUD-036-SIM-010, AUD-036-SIM-011 |
| [Step8 P1 Q1-Q5](spec.md#L1752) | PARTIAL | Dedup/shared turn; five-step503/DLQ; per-verb24h/JCS/body422; single AIIMS primary; three hash preimages. [AIIMS]/[JCS] supported, connected [PIPE]/[CACHE]/[AUDIT] incomplete. | AUD-036-SIM-005, AUD-036-SIM-008, AUD-036-SIM-009 |
| [Step8 P2 Q6-Q8](spec.md#L1760) | PARTIAL | Shared locale/audio/live-log combined audit; consumed lifecycle replay409/uncached paused409; hazard-only cap and unlimited annotations. [LIVELOG]/[CACHE]/[CAP] incomplete. | AUD-036-SIM-009, AUD-036-SIM-011, AUD-036-SIM-013 |
| [Cycle2 P1 Q1](spec.md#L371) | PARTIAL | Explicitly supersedes acknowledged-only/empty response with all attempted statuses/body-audit JCS equality. Source arrays supported; persist/consumer/audit semantics incomplete [PIPE]/[AUDIT]. | AUD-036-SIM-005, AUD-036-SIM-023 |
| [Cycle2 P1 Q2-Q5](spec.md#L402) | PARTIAL | 24h evidence; remove YAML fan_out_rules and evacuation alias; per-edge UUID sorted array; explicit error route allow-list. [MATRIX]/[PIPE] data helpers supported, effective errors/gate remain partial. | AUD-036-SIM-018, AUD-036-SIM-023 |
| [Cycle2 P2 Q1-Q5](spec.md#L566) | PARTIAL | 5s ack distinct from120s reply; bool always present; actual hybrid OTel; floor30;4xx+5xx scope. [ROUTE] bool/constant supported, trace/gate/errors not complete. | AUD-036-SIM-018, AUD-036-SIM-019, AUD-036-SIM-023 |
| [Cycle3 P1 Q1-Q5](spec.md#L838) | PARTIAL | Six-step pure canonicaliser; OIDC instead of long-lived SMOKE_TOKEN; two durable refused-run envelopes; four fixture red shapes; all-seven comparison. [KQL-CANON] supported, [SMOKE]/[GATE] incomplete. | AUD-036-SIM-017, AUD-036-SIM-018 |
| [Cycle3 P2 Q1-Q3](spec.md#L1308) | PARTIAL | Slot3.26/count26 preserves gap; two public canonicaliser functions/path override/errors; co-merge green after contracts. Code/artifacts present, common enum and historical merge execution incomplete. | AUD-036-SIM-023, AUD-036-SIM-024 |
| [Cycle4 A4-02](spec.md#L3907) | SUPERSEDED | Exclusive tenant-partition scope wording replaced by database-level scope plus described compensating controls/backlog. Locked siblings explicitly preserved; this is not proof KQL filters restrict Cosmos authorization. | AUD-036-SIM-002, AUD-036-SIM-020 |
| [Cycle4 P1 Q1-Q5](spec.md#L4008) | PARTIAL | Lightweight lexer/no AST; dual control/backlog wording; GitHub issue only/preexisting label; top-down symbol tracking/union hard-fail; ADR011 in-place/no012. Current documents/code mostly present, walker scope/issue evidence incomplete. | AUD-036-SIM-024, AUD-036-SIM-025 |
| [Cycle4 P2 Q1-Q4](spec.md#L4438) | SUPERSEDED | Count3392->3398->3399/3400 and optional comment assertion explicitly replaced by later single3400 REQUIRED posture; grouped changelog and no timed ADR flip still bind. | AUD-036-SIM-024 |
| [Cycle5 P1 Q1-Q3](spec.md#L5065) | IMPLEMENTED | Scope-first four-clause comment order; two selected forbidden substrings; existing resource-block extraction only. Current [SMOKE-TEST]/role comments implement this narrow change. | - |
| [Cycle5 P2 Q1-Q4](spec.md#L5496) | PARTIAL | REQUIRED prose, exact lower()+in and+0 count change supported; single3400 execution and review-gated same-close Accepted remain UNVERIFIED [C5]. | AUD-036-SIM-024 |
| [Error standard](research.md#L443) | SUPERSEDED | RFC9457 replaces RFC7807 claims; Cycle2 [six-route narrowing](contracts/error-responses.md#L194) explicitly preserves legacy non036 errors. | AUD-036-SIM-023 |
| [Transport/model migration](contracts/openapi-changelog.md#L12) | PARTIAL | v0.3 structured items/status/per-edge IDs/nine Pascal writes explicitly replace old wire shape; legacy reads retained. SDK/consumer migration not proven by documentation. | AUD-036-SIM-023, AUD-036-SIM-024 |
| [Posture conflict](spec.md#L6473) | CONFLICT | Latest sentinel3400/0 fails does not erase earlier reported environment errors, original FS obligations, or current24-versus26 domain assertion conflict. Do not force counts to imply success. | AUD-036-SIM-024 |

## Formal Review and Recorded Evidence

### Final-Sweep Gates

All37 gate IDs retained in the task file are assessed individually. None was executed during this audit. Older schema/test totals are explicitly superseded only where the later contract says so; required behavior and actual gate enforcement are not waived by historical GREEN/YELLOW labels.

| Gate | Status | Inspected evidence and current assessment | Follow-up |
| --- | --- | --- | --- |
| [FS1](final-sweep-report.md#L28) | UNVERIFIED | Historical51 round-trips lack current run; [AUDIT] common26 discriminator/validation failures remain. | AUD-036-SIM-023, AUD-036-SIM-024 |
| [FS2](final-sweep-report.md#L29) | UNVERIFIED | Historical9/10 builds exclude scaling module; alternate-root build not selected-root deployment proof [INFRA]/[ROOT]. | AUD-036-SIM-020, AUD-036-SIM-024 |
| [FS3](final-sweep-report.md#L30) | UNVERIFIED | Historical Spectral/Schemathesis v0.2 schema-load report, no current v0.3 actual HTTP conformance. | AUD-036-SIM-023, AUD-036-SIM-024 |
| [FS4](final-sweep-report.md#L31) | UNVERIFIED | Historical92 Vitest/15 a11y plus acknowledged ESLint failure; current active stream/layer assertions missing [MAP-TEST]/[LIVELOG-TEST]. | AUD-036-SIM-013, AUD-036-SIM-024 |
| [FS5](final-sweep-report.md#L32) | PARTIAL | File-existence/spot sampling of old66 rows not actual current73FR coverage [PIPE-TEST]. | AUD-036-SIM-024 |
| [FS6](final-sweep-report.md#L33) | PARTIAL | Payload correlation grep not actual two-scenario OTel span export [PIPE]. | AUD-036-SIM-019 |
| [FS7](final-sweep-report.md#L34) | PARTIAL | Claimed constitutional checks miss owner authorization/post-parse guard/egress/DLQ defects [AUTH]/[INJECT]/[COMMS]/[AUDIT]. | AUD-036-SIM-002, AUD-036-SIM-003, AUD-036-SIM-008 |
| [FS8](final-sweep-report.md#L35) | PARTIAL | [Threat model](../../docs/aidr/threat-model.md#L51) authored five deltas but cross-user403 conflicts replay contract and mitigated claims exceed source. | AUD-036-SIM-023 |
| [FS9](final-sweep-report.md#L36) | PARTIAL | 100 checklist IDs exist, implementation/operations items unresolved; current full table above. | AUD-036-SIM-024 |
| [FS10](final-sweep-report.md#L37) | SUPERSEDED | Old24-entry count replaced by [entry26 addition](tasks.md#L1759); complete26 implementation/schema tests still required. | AUD-036-SIM-023 |
| [FS11](final-sweep-report.md#L38) | PARTIAL | Operational five-query set not original five obligations; current mandatory Z1/Z2/Z6/Z7/load not actual gate [WORKFLOW]/[CD]. | AUD-036-SIM-016 |
| [FS12](final-sweep-report.md#L39) | PARTIAL | Header-mismatch test not simulation-owner membership and complete artifact-route authorization [RBAC-TEST]. | AUD-036-SIM-002 |
| [FS13](final-sweep-report.md#L40) | PARTIAL | Three raw container declarations not selected-root provisioned AVM resources [INFRA]/[ROOT]. | AUD-036-SIM-020 |
| [FS14](tasks.md#L1608) | PARTIAL | All56 Cycle2 checklist rows assessed; readiness definitions not actual closure [WORKFLOW]/[PIPE]. | AUD-036-SIM-024 |
| [FS15](tasks.md#L1609) | PARTIAL | Entry25 schema exists, common enum26/HTTP/fuzz parity incomplete [AUDIT]/[CONTRACT]. | AUD-036-SIM-023 |
| [FS16](tasks.md#L1610) | UNVERIFIED | No measured fresh Z6/Z7/floor run; [SMOKE] payload invalid and event producers absent. | AUD-036-SIM-017, AUD-036-SIM-019, AUD-036-SIM-024 |
| [FS17](tasks.md#L1611) | UNVERIFIED | Breaking documentation exists, same-PR consumer release/migration not attributable [ledger](contracts/openapi-changelog.md#L12). | AUD-036-SIM-024 |
| [FS18](tasks.md#L2042) | PARTIAL | Cycle3 definitions present, workflow/audit transport/canary source incomplete [GATE]/[CD]. | AUD-036-SIM-016, AUD-036-SIM-018 |
| [FS19](tasks.md#L2043) | PARTIAL | Entry26 local schema present, common discriminator/durable envelope transport not complete [AUDIT]/[GATE]. | AUD-036-SIM-018, AUD-036-SIM-023 |
| [FS20](tasks.md#L2044) | UNVERIFIED | All-seven canonical test source exists; no current executed result [KQL-CANON]. | AUD-036-SIM-024 |
| [FS21](tasks.md#L2045) | PARTIAL | OIDC/concurrency/check helper code exists, invalid smoke, wrong collation, missing durable refusal/CD binding. | AUD-036-SIM-016, AUD-036-SIM-017, AUD-036-SIM-018 |
| [FS22](tasks.md#L2409) | PARTIAL | [KQL-WALK] dynamically checks seven queries but scope tracking unsound; current run unverified. | AUD-036-SIM-025 |
| [FS23](tasks.md#L2410) | UNVERIFIED | Symmetric Z7 fix visible, no recorded current all-seven execution [KQL]. | AUD-036-SIM-024 |
| [FS24](tasks.md#L2411) | IMPLEMENTED | Database-scope literal/assertion exists [SMOKE-TEST]; this narrow source gate not deployed access proof. | - |
| [FS25](tasks.md#L2412) | PARTIAL | Corrected ADR wording present, review-gated Accepted transition unverified [ADR011](../../docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md#L3). | AUD-036-SIM-024 |
| [FS26](tasks.md#L2413) | IMPLEMENTED | Grouped Cycle4 [changelog](../../CHANGELOG.md#L13) present. | - |
| [FS27](tasks.md#L2414) | UNVERIFIED | Issue84 local citation not external creation/label/open status [changelog](../../CHANGELOG.md#L15). | AUD-036-SIM-024 |
| [FS28](tasks.md#L2665) | IMPLEMENTED | Corrected role-comment residue removed in current source [role block](../../infra/bicep/modules/cosmos-simulation-containers.bicep#L305). | - |
| [FS29](tasks.md#L2666) | UNVERIFIED | Current database scope matches required literal, historical before/after byte equality not independently established. | AUD-036-SIM-024 |
| [FS30](tasks.md#L2667) | IMPLEMENTED | [SMOKE-TEST] both presence/two absence assertions and no runtime skip marker present. | - |
| [FS31](tasks.md#L2668) | IMPLEMENTED | Header/docstring REQUIRED source present [test header](../../tests/contract/test_smoke_tenant_isolation.py#L162). | - |
| [FS32](tasks.md#L2669) | IMPLEMENTED | Grouped Cycle5 [changelog](../../CHANGELOG.md#L7) present. | - |
| [FS33](tasks.md#L2670) | UNVERIFIED | Exactly3400/zero-failure historical assertion not current execution [C5]. | AUD-036-SIM-024 |
| [FS34](tasks.md#L2671) | UNVERIFIED | No product ruff run; current report diagnostics only. | AUD-036-SIM-024 |
| [FS35](tasks.md#L2672) | UNVERIFIED | Review-dependent ADR status transition not established from status text alone [ADR011](../../docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md#L3). | AUD-036-SIM-024 |
| [FS36](tasks.md#L2673) | UNVERIFIED | External issue84 remains-open condition not observed; local refs preserved. | AUD-036-SIM-024 |
| [FS37](tasks.md#L2674) | UNVERIFIED | Current locked mirror text exists, prior-cycle byte identity not independently verified [C5]. | AUD-036-SIM-024 |

### Requirements Review History

The sixteen criteria in iterations1-4 are assessed once per current criterion in REQ-ITEM01-16 above, not counted again as new requirements. These six formal review iterations are separate authored records.

| Review | Status | Recorded result, attribution and limitation | Follow-up |
| --- | --- | --- | --- |
| [Iteration1](checklists/requirements.md#L38) | UNVERIFIED | 2026-05-08 initial16-criterion evidence; no SHA/tool output or independent human sign-off; original counts approximate. | AUD-036-SIM-024 |
| [Iteration2](checklists/requirements.md#L59) | UNVERIFIED | 2026-05-08 five clarify answers/57FR/18edges/all16 PASS claimed. Later technical amendments invalidate no-implementation-detail claim. | AUD-036-SIM-023, AUD-036-SIM-024 |
| [Iteration3](checklists/requirements.md#L93) | UNVERIFIED | 2026-05-08 five more answers/58FR/19edges/all16 PASS claimed; audio/viewport definitions not runtime proof. | AUD-036-SIM-024 |
| [Iteration4](checklists/requirements.md#L127) | UNVERIFIED | 2026-05-08 three answers/60FR/21edges/12assumptions/all16 PASS; no attributable executions. | AUD-036-SIM-024 |
| [Iteration5](checklists/requirements.md#L163) | PARTIAL | Plan/research/contracts authored; all-AVM/pinned versions19-envelope/AU/AAD compliance claims exceed [INFRA]/[AUTH] source. | AUD-036-SIM-020, AUD-036-SIM-023 |
| [Iteration6](checklists/requirements.md#L202) | UNVERIFIED | Step8 RE-LOOP:85 personas,18 critical/39 high/24 medium/4 low;0 endorse/30 reservations/55 object. Revalidation explicitly owed at [close](checklists/requirements.md#L259). No external session synthesis inspected. | AUD-036-SIM-024 |

### Analyze Findings and Recorded Closures

Pass1 is dated2026-05-09, pass2 dated2026-05-10. Both are document-consistency reviews, not product test runs. Pass2's truncated content hashes and old lengths2809/741/1698 do not pin current6477/816/2772 inputs. Historical labels below are not adopted as current findings without inspection.

| Review item | Status | Current assessment | Follow-up |
| --- | --- | --- | --- |
| [P1-HIGH-01](analyze-cycle2-pass1.md#L42) | PARTIAL | Empty-array versus all-attempted shape explicitly clarified; residual FR009/FR015 subset prose and real consumption gaps remain. | AUD-036-SIM-005, AUD-036-SIM-023 |
| [P1-HIGH-02](analyze-cycle2-pass1.md#L56) | IMPLEMENTED | Explicit Q1 supersession block present; original narrower shape not governing after it [spec](spec.md#L134). | - |
| [P1-HIGH-03](analyze-cycle2-pass1.md#L67) | CONFLICT | Context enum split documented, but success/failure arrays must sometimes coexist and active primary writes conflict with success enum. | AUD-036-SIM-023 |
| [P1-MED-01](analyze-cycle2-pass1.md#L85) | PARTIAL | Task renumbering map present, current plan decision references/individual compressed allocation incomplete. | AUD-036-SIM-023 |
| [P1-MED-02](analyze-cycle2-pass1.md#L91) | SUPERSEDED | Historical YAML range obsolete after explicit [T-AA20 removal](tasks.md#L1534); no absence claim from old line number. | - |
| [P1-LOW-01](analyze-cycle2-pass1.md#L99) | UNVERIFIED | Historical severity-count correction not independent reviewer-synthesis evidence. | AUD-036-SIM-024 |
| [P1-LOW-02](analyze-cycle2-pass1.md#L106) | IMPLEMENTED | Deferred-hazard reconciliation explicitly recorded [spec](spec.md#L222); not wholesale waiver of original maritime overlays. | - |
| [P2-HIGH-01-CLOSURE](analyze-cycle2-pass2.md#L119) | PARTIAL | Q1 propagation observed, current active publish/empty/persist-failure semantics still incomplete. | AUD-036-SIM-005 |
| [P2-HIGH-02-CLOSURE](analyze-cycle2-pass2.md#L132) | IMPLEMENTED | Explicit supersession text present; historical execution not claimed. | - |
| [P2-HIGH-03-CLOSURE](analyze-cycle2-pass2.md#L142) | CONFLICT | Closure assumes disjoint success/failure paths; partial dispatch can emit both and exposes enum contradiction. | AUD-036-SIM-023 |
| [P2-MED-01](analyze-cycle2-pass2.md#L52) | PARTIAL | Current tasks renumbered, plan/body references still not authoritative per-ID original allocation. | AUD-036-SIM-023 |
| [P2-MED-02](analyze-cycle2-pass2.md#L58) | SUPERSEDED | YAML fan_out_rules explicitly removed, old cited range not current missing-behavior proof. | - |
| [P2-LOW-01](analyze-cycle2-pass2.md#L157) | UNVERIFIED | Historical pointer drift is not a live behavior defect; exact current report anchors supplied independently. | AUD-036-SIM-024 |
| [P2-LOW-02](analyze-cycle2-pass2.md#L164) | IMPLEMENTED | Current CHK109 references corrected historical Q1 rather than the old pointer; no speculative re-fix needed. | - |
| [P2-LOW-03](analyze-cycle2-pass2.md#L170) | UNVERIFIED | Advisory task pointer drift not evidence of runtime failure; current linked obligation assessed separately. | AUD-036-SIM-024 |
| [P2-LOW-CARRY](analyze-cycle2-pass2.md#L176) | UNVERIFIED | Severity count carry-over needs attributable synthesis, not arithmetic on obsolete plan lines. | AUD-036-SIM-024 |
| [P2-BYTE-EQUALITY](analyze-cycle2-pass2.md#L183) | PARTIAL | Four textual sources mostly aligned for dispatch failure; active true outcomes/durable writes not established. | AUD-036-SIM-005, AUD-036-SIM-008 |
| [P2-SUCCESS-FAILURE](analyze-cycle2-pass2.md#L196) | CONFLICT | Claim that intersection is empty does not follow from suppressing success only on fully failed dispatch: partial failure permits both. | AUD-036-SIM-023 |
| [P2-ENUM-PARTITION](analyze-cycle2-pass2.md#L203) | CONFLICT | Disjoint-context enum explanation does not resolve byte-equal arrays on partial-failure coexistence. | AUD-036-SIM-023 |
| [P2-QUALITY-ALIGNMENT](analyze-cycle2-pass2.md#L210) | PARTIAL | Readiness targets exist; active schema/response mismatch remains. | AUD-036-SIM-023 |
| [P2-CONSTITUTION](analyze-cycle2-pass2.md#L217) | PARTIAL | Twelve definition-level invariants recorded; KQL tenant filter not Cosmos access proof and exception truncation not PII scrub. | AUD-036-SIM-002, AUD-036-SIM-006, AUD-036-SIM-020 |
| [P2-PATHS-PRIORITIES](analyze-cycle2-pass2.md#L250) | UNVERIFIED | PathsA/B/C and six entry priorities are future recommendations, not approved execution/merge evidence. | AUD-036-SIM-024 |
| [Cycle3 close](spec.md#L3840) | UNVERIFIED | 3391 passes/0 failures plus11 environment errors and missing-module errors explicitly recorded; not unconditional green current suite. | AUD-036-SIM-024 |
| [Cycle4 close](tasks.md#L2509) | UNVERIFIED | FULL3400 and issue84 claims authored; external issue/outputs not attributable in inspected local records. | AUD-036-SIM-024 |
| [Cycle5 analyze](spec.md#L6002) | PARTIAL | Local final analysis records four documentary findings; final close explicitly carries CHK237 drift, not silent resolution. | AUD-036-SIM-023 |
| [Cycle5 implement](spec.md#L6473) | UNVERIFIED | Claims3400/0/lint and retained mirrors; no raw run/candidate/environment receipt. | AUD-036-SIM-024 |
| [Cycle5 cohort](spec.md#L6475) | UNVERIFIED | Claims all-three-cohort convergence and Accepted flip. "174 active personas" does not match described10+58+17=85; not human signatures. | AUD-036-SIM-024 |

### ADR Evidence

All eleven local ADR036 documents were read completely in the bounded foundation review. Each records Accepted, with ADR011 additionally claiming Cycle5 cohort convergence. `Accepted` is an authored field, not proof of external approval, deployed state, historical scope equality or a passing run. Research's older ADR-number/title descriptions are not used to substitute unrelated documents.

| ADR | Status | Decision and actual implementation assessment | Follow-up |
| --- | --- | --- | --- |
| [ADR-036-001](../../docs/aidr/decisions/ADR-036-001-real-sub-agent-invocation.md#L20) | PARTIAL | Real adapters replace literal stubs; dispatcher uses role prompts, not operational handlers. | AUD-036-SIM-004 |
| [ADR-036-002](../../docs/aidr/decisions/ADR-036-002-direct-rest-lifecycle.md#L24) | PARTIAL | Direct abort/shared pause-resume decision; actual state/cancel/queue integration deficient. | AUD-036-SIM-010, AUD-036-SIM-015 |
| [ADR-036-003](../../docs/aidr/decisions/ADR-036-003-cosmos-session-consistency.md#L29) | PARTIAL | Session read-your-write decision, pipeline does not forward session tokens/observe real subscribers. | AUD-036-SIM-005 |
| [ADR-036-004](../../docs/aidr/decisions/ADR-036-004-apim-token-bucket-circuit-breaker.md#L23) | PARTIAL | Distinct APIM/attempt controls chosen, actual handler circuit/budget absent. | AUD-036-SIM-006 |
| [ADR-036-005](../../docs/aidr/decisions/ADR-036-005-cascade-etag-optimistic-concurrency.md#L27) | PARTIAL | Distributed cap ETag protocol, actual cap uses local memory. | AUD-036-SIM-011 |
| [ADR-036-006](../../docs/aidr/decisions/ADR-036-006-lessons-capture-blob-worm.md#L26) | PARTIAL | Blob WORM/Cosmos index chosen; actual generation/retention/retry incomplete. | AUD-036-SIM-015 |
| [ADR-036-007](../../docs/aidr/decisions/ADR-036-007-distributed-sequence-allocator.md#L66) | PARTIAL | Explicit local-counter replacement supported, committed gap-free/durable DLQ incomplete. | AUD-036-SIM-008 |
| [ADR-036-008](../../docs/aidr/decisions/ADR-036-008-sli-thresholds-rationale.md#L33) | PARTIAL | Threshold rationale exists, alert/gate/producer/throughput obligations not fully connected. | AUD-036-SIM-016, AUD-036-SIM-019 |
| [ADR-036-009](../../docs/aidr/decisions/ADR-036-009-idempotency-cache-design.md#L36) | PARTIAL | Durable JCS replay replaces stub, actual repository unused/wrong partition/concurrency. | AUD-036-SIM-009 |
| [ADR-036-010](../../docs/aidr/decisions/ADR-036-010-cycle-2-amendment-cycle.md#L56) | PARTIAL | Breaking v0.3/degraded dispatch/SLI changes authored; actual transport/trace/consumer migration incomplete. | AUD-036-SIM-005, AUD-036-SIM-023 |
| [ADR-036-011](../../docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md#L155) | PARTIAL | OIDC/canonicalisation/in-place scope/posture revisions supported in source; smoke/gate/isolation and Accepted approval not verified. | AUD-036-SIM-017, AUD-036-SIM-018, AUD-036-SIM-024 |

### Historical Measurement and Run Claims

| Recorded input | Status | Limit and current disposition | Follow-up |
| --- | --- | --- | --- |
| [Sweep attribution](final-sweep-report.md#L1) | UNVERIFIED | 2026-05-09 branch/agent author, no commit SHA or workflow-run ID. Windows errors and tool versions documented; not current revision evidence. | AUD-036-SIM-024 |
| [Sweep totals](final-sweep-report.md#L60) | UNVERIFIED | 3781 pytest passes/26 skips/39 failures-errors and107 web/a11y passes; wave-addition4436 differs executed3888 claim. Preserve these distinctions, no blanket clean-run inference. | AUD-036-SIM-024 |
| [Sweep failures](final-sweep-report.md#L86) | UNVERIFIED | Eight recorded groups: tmp-path errors, TenantContext drift, CD filter drift, unconfigured model, missing modules, speech/demo temp errors, isolation flakes, commented BCP120 module. No failures re-run or fixed here. | AUD-036-SIM-024 |
| [Sweep edits/signoff](final-sweep-report.md#L101) | UNVERIFIED | Four past edits and thirteen signoff assertions are author narrative; test/a11y/deployment/human approval still need attributable receipts. | AUD-036-SIM-024 |
| [Quickstart run](quickstart.md#L269) | UNVERIFIED | Claimed five-minute verification2026-05-08 lacks SHA/raw output; commands were read only. | AUD-036-SIM-024 |
| [FR matrix](fr-coverage-matrix.md#L9) | CONFLICT | 36 grouped historical rows/66FR prose and reused IDs not current73 behavior coverage; current full table replaces audit inference, not original file. | AUD-036-SIM-023 |
| [Historical SC-1](sc-measurement-matrix.md#L8) | UNVERIFIED | Old inject->audit5s claim, not canonical actionable-Risk15s SC001; staging-gated not measured evidence. | AUD-036-SIM-024 |
| [Historical SC-2](sc-measurement-matrix.md#L9) | UNVERIFIED | Old stub-sweep PASS, not canonical lead-time SC002; current literal removal separately supported. | AUD-036-SIM-024 |
| [Historical SC-3](sc-measurement-matrix.md#L10) | UNVERIFIED | Old gap-free PASS, not canonical evacuation SC003; actual dense-commit defect remains. | AUD-036-SIM-024 |
| [Historical SC-4](sc-measurement-matrix.md#L11) | UNVERIFIED | Old receipt-prefix PASS, not canonical resource SC004; active receipts incomplete. | AUD-036-SIM-024 |
| [Historical SC-5](sc-measurement-matrix.md#L12) | UNVERIFIED | Old watermark/economic harness conflation, no canonical economic-loss result. | AUD-036-SIM-024 |
| [Historical SC-6](sc-measurement-matrix.md#L13) | UNVERIFIED | Old citation-leak PASS not canonical all-channel zero-egress SC006. | AUD-036-SIM-024 |
| [Historical SC-7](sc-measurement-matrix.md#L14) | UNVERIFIED | Old cap PASS not canonical typed-ingestion SC007; local cap not distributed. | AUD-036-SIM-024 |
| [Historical SC-8](sc-measurement-matrix.md#L15) | UNVERIFIED | Old depth-refusal PASS not canonical receipts SC008. | AUD-036-SIM-024 |
| [Historical SC-9](sc-measurement-matrix.md#L16) | UNVERIFIED | Old affinity PASS not canonical auto-Risk SC009. | AUD-036-SIM-024 |
| [Historical SC-10](sc-measurement-matrix.md#L17) | UNVERIFIED | Old lessons-ID replay PASS not canonical map-latency SC010. | AUD-036-SIM-024 |
| [Historical SC-11](sc-measurement-matrix.md#L18) | UNVERIFIED | Old export-hash PASS not canonical thread-isolation SC011. | AUD-036-SIM-024 |
| [Historical SC-12](sc-measurement-matrix.md#L19) | UNVERIFIED | Old six-month registry PASS/CI-live claim not canonical degraded-window SC012; workflow manual-only. | AUD-036-SIM-024 |
| [Migration ledger](contracts/openapi-changelog.md#L105) | UNVERIFIED | v0.3 dated2026-05-22/v0.2 dated2026-04-30 and T+7/T+14/T+12month milestones do not prove SDK rollout or retained reader compatibility. | AUD-036-SIM-024 |

No Step8/Step8i/session-workspace synthesis or signed human approval was read from outside the repository. Bounded filename searches found no corresponding local synthesis files. External issue84 state, review labels, tenant deployments, model availability, Speech URLs, KQL ingestion and WORM policy remain UNVERIFIED. These are evidence limits, not permission to call external systems during this review.

## Static Validation Record

Completed on 2026-09-14 using read-only PowerShell text/regex/path checks and report diagnostics only. The checker was held in terminal memory; no helper file was created and no application module, product test, verifier, build, agent, model, browser, server, cloud resource, installation, deployment or approval workflow was executed.

| Check | Result |
| --- | --- |
| Revision | Read-only `git rev-parse HEAD` confirmed `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a` at start and end. |
| Write boundary | `git status --short --untracked-files=no` returned no tracked changes. The permitted report is a new untracked file. Only this report was manually written; no branch or commit was created. |
| Original tasks | Exact 289-ID set, one row per ID, including T-F02a/T-F02b; no dependency-note duplicates; all original states `none`, matching absence of source checkboxes. |
| Requirements and criteria | Exact source-defined FR-001 through FR-073 and SC-001 through SC-014 sets; annotated amendment headings included. No separately numbered NFRs. |
| Acceptance | Exact 54 story-scenario IDs and 59 explicit amendment acceptance IDs; 12 assumptions and 21 edges also checked. |
| Checklists | Exact file-scoped 576-item set and source anchors; 254 checked and 322 unchecked original states, X/x normalised equivalently. Five adapter items and two quoted alternatives separately checked. |
| Follow-ups | Exactly 26 unique unchecked AUD-036-SIM IDs, exact required checkbox-line shape; every referenced follow-up defined. |
| Review gates | All 37 FS IDs separately represented; formal analysis findings, six requirements iterations, eleven ADRs and historical measurement claims assessed. |
| Links | All 1,639 local inline/reference links resolved within the workspace across 190 existing files; every one-based line within bounds. Balanced-parenthesis parsing and percent decoding used, so parenthesized routes are not truncated. No other implementation-review report is linked as evidence. |
| Report diagnostics | `get_errors` reports no errors; Markdown table/reference/EOF diagnostics resolved without changing product files. |

The first combined text-check attempt missed annotated FR headings and a later attempt mishandled CRLF on task titles. Only the in-memory checker patterns were corrected; the complete rerun passed. These were report-validator defects, not product execution failures or evidence of implementation correctness.

**Remaining limits:** Some original prior-phase task details were collapsed into ranges and cannot be uniquely reconstructed from the retained local task text; each affected ID is explicitly UNVERIFIED rather than assigned invented criteria. Current source defects are documented in open tasks. Product execution, real-model/latency/outcome measurements, installed/deployed state, historical byte preservation, external issue status and human approvals require a separately authorised session and attributable evidence. The static audit itself is complete.

### 2026-09-18 Implementation Pass

This pass was performed as an isolated context for spec 036 only. Three parallel technical reviews examined simulation
auth/egress/idempotency, telemetry injection/subscriber consumption, and map/release/evidence gates. The cited direct
communication-egress predicate was checked and is already aligned with the shared live-tenant rule: non-live or unknown
tenant modes are routed to synthetic receipts before real delivery. No duplicate patch was applied.

Remaining open work includes authoritative simulation membership, direct-route idempotency, injection contradiction
provenance, real subscriber consumption, sequence/audit durability, non-point map rendering, accessible live logs,
candidate-bound staging gates, Foundry carve-out enforcement, deployment composition, performance, and human evidence.
