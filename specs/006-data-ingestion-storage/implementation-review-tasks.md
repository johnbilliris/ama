# Implementation Review: 006 Data Ingestion and Storage

**Review date:** 2026-09-11  
**Source revision:** `5b44c249f00e0e4a13ea2579c8c33d06e2471d7a`  
**Disposition:** Implementation is incomplete; the checked original task list is not evidence of operational readiness.  
**Coverage:** 94/94 original tasks; 61/61 local FR/SC items; 1 explicitly inherited NFR; 26/26 acceptance scenarios;
7/7 edge cases; 23/23 specification-quality checklist items; 11/11 quickstart verification items.  
**Follow-ups:** 44 open, unexecuted remediation tasks. Original task checkboxes have not been changed.

## Scope and Limitations

This isolated, review-only assessment follows the central [Review Contract][contract]. HEAD matched the requested
revision, and the tracked worktree was clean at the initial baseline check. The complete [specification][spec],
[task list][tasks], [plan][plan], [research decisions][research], [data model][model], [OpenAPI contract][openapi],
[quickstart][quick], [requirements checklist][quality], [historical critique][critique], and its
[prompt][critique-prompt] were read, including the later capstone amendments. The prompt's historical request to
run agents was treated as evidence, not executed instructions. No other concurrent implementation-review report
was read. No delegation occurred.

Source tracing covered every ingestion adapter, normaliser, generator, the worker/factory/configuration,
shared and API signal repositories, raw/blob/audit writers, public signal routes, actual router registration,
tenant middleware, Monitoring processing, downstream stored-data retrieval methods, and active infrastructure.
Later simulation, seeding, warp scheduling, synthetic dispatch, and spec-039 feed implementations were inspected
where they could represent relocated behavior. Algorithmic business logic outside the ingestion/handoff boundary,
public alert delivery, and deferred non-Australian deployments remain outside this review.

Applied guidance: [repository review priorities][review-rule], [detailed review checklist][review-checks],
[commenting guidance][comments], [Bicep defaults][bicep-rule], [policy compliance][policy-rule], the current
[constitution][constitution], [Data Engineer responsibilities][data-engineer], and the
`python-fact-grounded-coding`, `cosmosdb-best-practices` and `azure-storage` skills. Runtime/Pylance execution was
not used. Official [Python 3.12 ElementTree documentation][python-et] and [jsonschema format documentation][jsonschema-faq]
were consulted only for library semantics. Google retrieval produced no usable evidence. No source-provider feed,
Azure resource, credential, deployment, or external approval was queried.

No application tests, builds, imports, benchmarks, linters, historical commands, migrations, or cloud operations
were executed. Only read-only repository/text/JSON inspection and report-document checks were used. Assertion
bodies are described as source evidence, never as passing test results. A configured endpoint does not prove
availability, licensing, consent, geographic accuracy, or production operation. Performance and human-review
claims remain UNVERIFIED without attributable checked-in records. Only this report was created; the index,
original specifications, tasks, evidence, and application sources were not edited.

### Evidence Statuses

| Status | Interpretation in this report |
| --- | --- |
| IMPLEMENTED | The exact scoped artifact or behavior is supported by inspected source; execution is not implied. |
| PARTIAL | A component or assertion exists, but a specific required behavior, wiring, or assertion is absent. |
| MISSING | No implementing behavior/assertion was found after the scoped call-path and relocation search described below. |
| CONFLICT | Current code, contracts, later decisions, or task wording disagree and need an explicit resolution. |
| UNVERIFIED | Execution, performance, approval, provider verification, or a deferred prerequisite cannot be established. |
| SUPERSEDED | An explicit replacement/authority statement exists; this does not certify its replacement implementation. |

### Negative-Search and Relocation Record

| Search | Scope and controlling evidence | Conclusion boundary |
| --- | --- | --- |
| NS-01 | Application/domain Python: `SignalRepository`, `save_with_fanout`, `associate_multi`, `update_incident_id`, `store_binary_asset`, `store_simulation_payload`; inspected [worker wiring][worker-wiring], [factory][factory], [base processing][pipeline], both [shared][repo] and [API repositories][api-repo]. | Optional helpers are not production persistence; no binary-download or fan-out caller was found in the 006 ingestion path. |
| NS-02 | All Python under tests and API tests, plus relevant domain tests: ingestion imports, normalisers, worker/factory, raw/blob calls, `simulationRunId`, field-officer identity, retrospective association, latency and throughput terms. All matched 006 test files were read. | Sensor/CAP/binary/worker/raw-audit/model contract coverage was not found; unrelated evidence-signal tests target a different API. |
| NS-03 | Application/agent sources: Tier-1 detector, CAP normaliser, Monitoring entry points, status registration, declaration and query calls; inspected [router][router], [Monitoring pipeline][monitor-pipe], [MAF wrapper][maf-monitor], [MAF workflow][maf-builder]. | No Tier-1 or status-register callers were found; newer workflow code does not connect the live polling worker to these consumers. |
| NS-04 | Later [simulation routes][sim-api], [036 injection][sim036], [synthetic dispatch][sim-dispatch], [publisher][sim-publish], [seeding][seed], [warp scheduler][warp], and [039 feed tests][feed-test]. | These are real adjacent implementations, not missing files; their different models/entry points do not demonstrate the required same-live-pipeline behavior. |
| NS-05 | Infrastructure Bicep and documentation searched for logical-partition storage usage, size/80%/20GB alarms, ingestion SLO and reconciliation records; active [deployment entry][azd] traced to [root infrastructure][activeinfra]. | No 006 logical-partition-size sampling/alert path or measured 006 SLO/reconciliation record was located. Broader service-health tooling is not equivalent evidence. |
| NS-06 | Local review records and linked feature-028 evidence searched for HYP-004, actor consultation, and relocation; [rubric baseline][rubric-baseline] and [risk treatment][risk-record] inspected. | The named HYP-HYP-004 evidence file was not found. Portfolio baseline prose and an intended risk treatment are not a per-spec measured uplift or test result. |

Workspace text search timed out and `rg` was unavailable; bounded PowerShell source searches were used instead.
No absence conclusion below rests solely on a historical filename being absent.

## Prioritized Findings and Remediation

P1 means **Critical / blocks implementation sign-off**: incorrect safety data, lost records, isolation failures,
or a required production path that cannot deliver its contract. P2 means **Important**: simulation fidelity,
operational completeness, test assurance, or unresolved evidence/contract obligations. Each task below is
deliberately unchecked. Future validation IDs refer to the commands and prerequisites near the end of this report.

### AUD-001: Production Worker Omits Mandatory Persistence Dependencies

- [x] AUD-001 (P1) Assemble a production ingestion path that cannot report success without durable signal storage.

**Affected:** T008, T012, T015, T016, T033; FR-001, FR-001a, FR-003, FR-017, FR-025, FR-028; SC-007.

**Expected vs observed / impact:** The [entry-point factory][worker-wiring] passes only blob storage and dedup.
[Base processing][pipeline] defaults schema, repository, audit writer, and association to `None`, skips their
operations, then records an ingestion and dedup key. Configured production polls can archive a transformed raw
payload and declare success without creating any signal or audit record. Supplying `COSMOS_ENDPOINT` does not wire it.

**Developer instructions:** Own the composition in [worker][worker-wiring] and [factory][factory]. Construct validated
clients, the agreed repository, schema validator, audit and incident services once; require them in production.
Allow explicit test/development substitutes, not silent optional production writes. Surface startup/dependency failure.

**Tester instructions:** Extend [pipeline integration tests][pipeline-test] using the real factory and one real adapter
with transport-only fakes. Positive: one input yields a retrievable signal/raw/audit triple. Negative: missing Cosmos
or audit dependency prevents readiness/success. Edge: restart and two workers preserve the same durable records.

**Dependencies / future validation:** AUD-004, AUD-006, AUD-007, AUD-009, AUD-023, AUD-026; V01, V02, V06.
**Acceptance:** Every success counter increment corresponds to a durable, schema-valid signal and required evidence;
production startup without mandatory services is visibly unavailable.

### AUD-002: Public and Manual Ingestion Bypass the Pipeline

- [x] AUD-002 (P1) Route API, field, volunteer, sensor, and community submissions through the canonical ingestion service.

**Affected:** T080, T081, T083; FR-001, FR-003, FR-011, FR-012, FR-017, FR-019a, FR-028; US7-AS1.

**Expected vs observed / impact:** [POST /signals][post] calls [AuthoritativeIngestionService][manualservice]; IoT and
community wrappers simply delegate to it. It writes [process-local state][state], creates an arbitrary active flood
incident (`incident-default` when absent), and trusts submitted confidence/provenance. No common schema, raw archive,
audit, dedup, or officer-identity derivation is invoked. An accepted HTTP response is not the specified durable ingestion.

**Developer instructions:** Replace the legacy delegation with the shared processing boundary, preserving the public
acknowledgement contract. Derive field-officer identity from authenticated claims, classify manual/volunteer sources
through the catalogue, and leave unmatched incidents null. Do not auto-declare a flood from an arbitrary submission.

**Tester instructions:** Extend [live API contract tests][live-api-test]. Positive: authenticated field and volunteer
reports persist with correct kind/tier/collector and raw/audit evidence. Negative: forged officer, malformed envelope,
and disallowed source are rejected or dead-lettered as specified. Edge: no incident, repeated submission, and later
declaration do not create phantom incidents or duplicate signals.

**Dependencies / future validation:** AUD-001, AUD-003, AUD-007, AUD-020; V01, V02, V05.
**Acceptance:** API-originated signals have the same validation/storage/audit guarantees as polled signals, with
trusted identity and no implicit incident creation.

### AUD-003: Signal APIs Do Not Enforce Tenant or Agency Scope

- [x] AUD-003 (P1) Enforce authorised tenant, jurisdiction, agency, and simulation boundaries on signal reads and writes.

**Affected:** T012, T013, T062, T063, T065, T080; FR-025, FR-029, FR-031, FR-037a; SC-009.

**Expected vs observed / impact:** [GET /signals][get] starts from every value in a global dictionary and applies only
caller-supplied filters. [Tenant middleware][tenant] sets a context but the route never consumes it. The Signal model
has no owning agency/scope, and POST does not bind a supplied simulation marker to an authorised run. Even an
authenticated caller reaching these routes is not constrained to its permitted records. The dashboard also uses
[unscoped state][dashboard]. Authentication alone does not repair this data-access boundary.

**Developer instructions:** Own route/service/repository scoping, not just UI filtering. Require authenticated scope
on every query and mutation; intersect optional jurisdiction filters with authorisation. Bind simulation provenance
to validated run membership and prohibit live-context writes masquerading as simulation, and vice versa.

**Tester instructions:** Extend [live API tests][live-api-test] and [storage tests][storage-test]. Positive: authorised
NSW/agency reads succeed. Negative: VIC, another NSW agency, or another run cannot read/write those records. Edge:
omit filters, request national scope, reuse an incident ID across scopes, and forge provenance; none bypass isolation.

**Dependencies / future validation:** AUD-004, AUD-005, AUD-042; V02, V05.
**Acceptance:** Authorisation-bound queries return zero records from disallowed agencies/jurisdictions/runs regardless
of query parameters, while explicitly authorised national fan-out remains discoverable.

### AUD-004: Cosmos Serialization Does Not Match the Hierarchical Key

- [x] AUD-004 (P1) Align serialized signal documents, partition routing, point reads, and fan-out identity.

**Affected:** T012, T020, T056, T060, T063; FR-025, FR-030, FR-031; SC-004, SC-009.

**Expected vs observed / impact:** [Cosmos save][repo] serializes snake_case `jurisdiction_id`/`data_source_id`, adds
`scope` and an unrelated `partitionKey` string, while [both deployed key definitions][activeinfra] use camelCase
`/jurisdictionId` and `/dataSourceId`. Prefix queries use the camelCase values. The [fan-out helper][repo-fanout]
reuses the same Cosmos `id`, so copies whose key components are undefined can overwrite one another instead of
occupying the intended partitions. [API repository][api-repo] is a second, incompatible writer.

**Developer instructions:** Define one wire-document contract and use it in all writers/readers; include actual HPK
properties and authorised ownership metadata. Give fan-out references deterministic identities and resolvable targets.
Plan explicit migration/backfill for existing documents; never silently change an existing container's partition key.

**Tester instructions:** Extend [storage tests][storage-test] beyond the in-memory fixture to a production-shaped
container contract/emulator. Positive: all three key values and a national primary plus NSW/VIC references survive.
Negative: snake/camel drift or an absent key is rejected before write. Edge: identical IDs in different scopes and
jurisdictions do not overwrite; source/incident/category/time filters return the correct records.

**Dependencies / future validation:** AUD-042; V02, V06, V07.
**Acceptance:** Actual persisted keys equal configured HPK values; all references remain readable; migration and
query/index compatibility are demonstrated without cross-tenant disclosure.

### AUD-005: In-Memory Queries Leak Simulation Data

- [x] AUD-005 (P1) Make development/test storage enforce the same complete scope contract as Cosmos.

**Affected:** T012, T020, T063, T065, T078; FR-025, FR-029, FR-037a; SC-009.

**Expected vs observed / impact:** [query_by_jurisdiction][repo-query] and [query_unassociated][repo-unassoc] ignore
`scope` in their dictionary branches. A `national` jurisdiction selects all jurisdictions. Saves use only signal ID
as the dictionary key, permitting cross-scope replacement. The [isolation test][storage-sim-test] checks only the
incident-query branch and discards the simulation query result, so it misses these concrete contamination paths.

**Developer instructions:** Key local storage by the full agreed identity, apply identical scope/authorisation
predicates in every query/update, and distinguish authorised national queries from implicit all-tenant access.
Reject inconsistent simulation provenance rather than relying on a caller's default `scope='live'`.

**Tester instructions:** Positive: live and three runs coexist under identical source/incident/signal IDs. Negative:
each jurisdiction, unassociated, incident, point-read and update operation is unable to cross scopes. Edge: national
fan-out, missing scope, run deletion, and ID reuse preserve isolation and local/Cosmos parity.

**Dependencies / future validation:** AUD-004, AUD-042; extend [storage tests][storage-test], V02, V04.
**Acceptance:** Both backends pass a bidirectional scope matrix; no query or update treats simulation records as live.

### AUD-006: Audit Writes Overwrite Earlier Entries

- [x] AUD-006 (P1) Implement append-only ingestion audit storage and truthful outcome records.

**Affected:** T003, T015, T064; FR-028; SC-007; US5-AS3.

**Expected vs observed / impact:** [AuditWriter.write_entry][audit] uploads one line to a date/hour path through
[BlobStorageService._upload][blobupload], which uses `overwrite=True`. A second entry replaces the first in both
the helper's local store and its Azure branch. The buffer masks this loss in memory. Entries lack an explicit
validation-status field, and [base processing][pipeline] labels a persisted range-rejected signal `success` without
carrying rejection details. This is not an immutable, complete ingestion ledger.

**Developer instructions:** Use protected append blobs or an equivalently approved immutable segment design;
implement concurrent append/retry semantics, complete status/outcome fields, and correlation to each persisted copy.
Do not count completion before required audit persistence; define recovery for audit-write failure after a signal write.

**Tester instructions:** Extend [storage tests][storage-test] with the real writer and blob adapter. Positive: multiple
same-hour entries are all retrievable. Negative: overwrite/delete and failed append cannot yield silent success.
Edge: concurrent workers, retry after ambiguous acknowledgement, hour rollover, rejected measurements, and fan-out.

**Dependencies / future validation:** Storage immutability policy coordination with AUD-039; V02, V07.
**Acceptance:** Audit is append-only under concurrency and restart; reconciliation finds every required signal/outcome,
with zero lost entries and no success declaration for incomplete audit persistence.

### AUD-007: Validation Failures Have No Durable Dead-Letter Path

- [x] AUD-007 (P1) Make schema validation unconditional and preserve recoverable failure evidence per payload.

**Affected:** T008, T033, T043, T044, T064, T080, T086; FR-002, FR-002a, FR-003, FR-017; SC-003, SC-007.

**Expected vs observed / impact:** [Validation][schema-validation] is optional and catches only schema validation
errors, then returns after optional audit. Normalisation failures return similarly; neither writes a dead-letter
record or the original raw payload. Later timestamp/model/blob/repository exceptions can terminate processing of
the remaining poll batch. `jsonschema.validate` is called without a format checker. Several normalisers emit
`jurisdictionId=null` although the [schema][schema] accepts only a string when present; association adds null
`incidentId` after validation despite its string-only schema.

**Developer instructions:** Compile the canonical schema with intended format checks; resolve optional/null and
simulation-marker rules explicitly. Preserve raw bytes and diagnostic field paths before rejection. Isolate errors
per item, create durable dead letters with retry state, and distinguish schema rejection from valid rejected sensor data.

**Tester instructions:** In [pipeline integration][pipeline-test] and [normaliser tests][bom-test], cover valid live and
sim envelopes, invalid namespace/schema/date/category/geometry, no jurisdiction/incident, malformed bytes, and a bad
first item followed by a good item. Assert exact dead-letter reason, raw reference, audit and no false persistence.

**Dependencies / future validation:** AUD-042 for schema compatibility; V01, V02.
**Acceptance:** No persistence bypasses validation; every failed item is diagnosable and recoverable, and one bad item
does not discard unrelated items in the same poll.

### AUD-008: Filename Caches Permanently Suppress Updated Products

- [x] AUD-008 (P1) Replace filename-only admission with version-aware, successfully committed product tracking.

**Affected:** T009, T026, T028, T030a, T030b, T042; FR-004, FR-005, FR-009, FR-018a; SC-001.

**Expected vs observed / impact:** [BoM warnings][bom-warn], [radar][radar], [RSS replacement][rss], [tsunami][tsunami]
and [Himawari][himawari] maintain `_known_files` indefinitely. Warnings use a filename-only canonical key. A revised
warning under the same product filename is never retrieved again, regardless of Redis expiry. Names are marked
seen before validation/storage, and a later FTP error can discard an already-marked partial batch. This loses
escalations and retries, not merely duplicate records.

**Developer instructions:** Track canonical product identity plus source issue/update or material-content version;
commit seen state only after the durable ingestion outcome. Use remote modification metadata where reliable and
do not permanently suppress filename reuse. Bound any local cache and preserve partial-fetch retryability.

**Tester instructions:** Use real adapters with a fake FTP transport in [pipeline integration][pipeline-test].
Positive: unchanged product is skipped. Negative: same filename with new issue/severity is ingested. Edge: failed
download midway through a batch, failed validation/storage, delete/recreate, and process restart recover every version.

**Dependencies / future validation:** AUD-009, AUD-011; V01, V02.
**Acceptance:** Every material update can reach storage once; transient failures and stable filenames cannot make it
permanently invisible.

### AUD-009: Deduplication Is Non-Atomic and Its Fallback Never Expires

- [x] AUD-009 (P1) Provide scope-aware, bounded and race-safe deduplication across workers and retries.

**Affected:** T008, T009, T018, T033, T059, T078; FR-018a, FR-037a; SC-002.

**Expected vs observed / impact:** [DedupService][dedup] separates `get` and `set`; two replicas can both miss and
write. Its dictionary fallback never expires and is not shared. [Base processing][pipeline] stores no configured
per-source TTL and does not namespace the hash by simulation scope. Canonical helpers are not the real BoM poller's
keys; hashes also miss material changes that leave an identifier unchanged. [Tests][dedup-test] only check local
membership and deterministic strings, not Redis, expiry, failover or contention.

**Developer instructions:** Adopt an atomic claim/commit or durable idempotency protocol with bounded expiry,
source/run namespacing, and recovery from abandoned claims. Honour effective per-source TTLs. Define a safe
Redis-outage policy and ensure storage uniqueness remains authoritative across replica races and cache resets.

**Tester instructions:** Positive: repeated unchanged versions produce one signal. Negative: concurrent claims and
replayed acknowledgements cannot duplicate writes. Edge: real Redis expiry, local expiry, cache failover/recovery,
two source IDs sharing a product ID, changed content and three simulations sharing a canonical identifier.

**Dependencies / future validation:** AUD-004, AUD-042; [dedup tests][dedup-test], [pipeline tests][pipeline-test], V02.
**Acceptance:** TTL and backend parity are asserted; no data is indefinitely suppressed or duplicated by a replica race.

### AUD-010: Native Source Timestamps Are Not Converted

- [x] AUD-010 (P1) Normalize timestamps from each source format before schema/model construction.

**Affected:** T023, T024, T025, T027, T028, T029, T038, T042, T043; FR-002, FR-004, FR-005, FR-008, FR-009.

**Expected vs observed / impact:** [Observations][obs] copy BoM `local_date_time_full` unchanged; [GeoJSON][geo]
copies `updated`/`pubDate` without converting epoch values or RSS-style dates. [Radar][radar] and [Himawari][himawari]
literally use filenames as timestamps. [Persistence][pipeline] calls `.replace`/`datetime.fromisoformat` on these
values. Wiring the missing repository exposes invalid strings or non-string timestamps instead of fixing ingestion.
Origin time and last-update time are also conflated for earthquakes.

**Developer instructions:** Add documented per-provider parsers with timezone/UTC handling, distinguish occurrence,
publication and update times, and reject unknown/invalid timestamps with diagnostics. Parse product timestamps from
documented metadata rather than accepting a filename or silently replacing missing occurrence time with now.

**Tester instructions:** Extend [BoM][bom-test], [GeoJSON][geo-test], and [pipeline tests][pipeline-test]. Positive:
UTC/local BoM, epoch milliseconds, RFC date and radar product time persist as valid UTC. Negative: malformed/missing
times dead-letter. Edge: timezone offsets, DST transitions, future clock drift and same-origin revised publication.

**Dependencies / future validation:** AUD-007; V01.
**Acceptance:** Every supported adapter produces valid, semantically correct UTC timestamps and cannot crash later
items during datetime conversion.

### AUD-011: XML/CAP Parsing Loses Namespaced Fields and Does Not Validate Products

- [x] AUD-011 (P1) Implement source-schema-aware XML/CAP parsing and wire the correct normaliser.

**Affected:** T021, T022, T026, T030a, T030b, T031; FR-002, FR-004, FR-005; US1-AS1.

**Expected vs observed / impact:** [BoM][bom] and [CAP find_text][cap] use `find(namespaced) or find(unqualified)`.
In the pinned Python 3.12 runtime, a found leaf with no children is falsey, so real namespaced timestamps/headlines
can be discarded. Only XML well-formedness is checked, not the documented product/AMOC structure. Missing fields
fall back to current time or a Canberra point and remain validated. Tsunami inherits the BoM normaliser rather than
CAP; CAP certainty is extracted but not scored. [BoM tests][bom-test] use unnamespaced simplified products.

**Developer instructions:** Use explicit `is None` fallback, supported namespaces/product types and required-field
validation; validate or faithfully enforce the documented XSD contract. Dispatch CAP products to CAP parsing;
handle all relevant info/area blocks and confidence inputs without fabricated geography or timestamps.

**Tester instructions:** Positive: licensed representative namespaced warnings, forecast and flood/tsunami CAP retain
issue ID/time, areas and severity/certainty. Negative: schema drift, unrelated XML and missing required fields reject.
Edge: multiple areas/info languages, cancel/update products, empty leaf text and both namespace variants.

**Dependencies / future validation:** AUD-007; [BoM tests][bom-test], [pipeline tests][pipeline-test], V01.
**Acceptance:** Actual-format fixtures normalize deterministically and survive the common schema path; no absent
source fact is silently fabricated as validated data.

### AUD-012: Live Signals Have No Traceable Event-to-Stored-Data Consumer Chain

- [x] AUD-012 (P1) Connect persisted signals to Monitoring and pass real stored references through downstream consumers.

**Affected:** T008, T033, T054, T061, T078; FR-018, FR-019, FR-020, FR-021, FR-022, FR-023, FR-024.

**Expected vs observed / impact:** [Base processing][pipeline] publishes no signal event. Its generated correlation
UUID is not attached by [enrichment][enrich] or stored in [Signal][signal-model]. [Monitoring handoffs][monitor]
contain a category/source-kind summary but no stored signal IDs. [Risk retrieval][risk-retrieve] expects those IDs,
reads with an incident-only key incompatible with the signal HPK, and fabricates synthetic entries when no store/IDs
are available. Downstream [evacuation][evac-retrieve], [resource][res-retrieve], and [communication][comm-retrieve]
retrieval surfaces exist, but do not establish an ingestion-originated stored-data chain. New [MAF execution][maf-builder]
starts from a supplied incident, not an event emitted by this worker.

**Developer instructions:** Add a reliable post-persistence event/outbox and a real first-stage Monitoring consumer.
Carry signal IDs, full storage/tenant scope and the original UUID into typed handoffs and downstream reads. Retrieve
actual related records; explicitly degrade when unavailable instead of representing fabricated inputs as retrieved facts.
Preserve spec-008 authority for communication implementation.

**Tester instructions:** Extend [pipeline integration][pipeline-test] and [consumer tests][monitor-test]. Positive:
poll to persisted signal to Monitoring to Risk reads exact stored payload/provenance. Negative: unavailable/mismatched
record cannot become a manufactured authoritative signal. Edge: fan-out and duplicate delivery preserve correlation;
live and simulation events never mix. Verify existing [downstream reference assertions][risk-handoff-test] too.

**Dependencies / future validation:** AUD-001, AUD-004, AUD-015, AUD-016, AUD-020, AUD-042; V01, V03, V04.
**Acceptance:** A persisted signal can be traced by one ingestion correlation UUID through real stored-data reads
and typed decisions, without direct external ingestion by downstream agents.

### AUD-013: Tier-1 Misinformation Detection Is Disconnected

- [x] AUD-013 (P1) Invoke the Tier-1 detector on social and community ingestion with persisted scope-local context.

**Affected:** T046, T047, T048, T049, T050, T054; FR-010a, FR-011; US4-AS3.

**Expected vs observed / impact:** [MisinformationDetector.detect][misinfo] exists, but NS-03 found no application
caller. [The base pipeline][pipeline] and social/community normalisers do not invoke it, load recent authoritative
signals, or persist returned flags. The downstream escalated-only LLM stage therefore cannot receive flags from
the specified ingestion heuristics. Helper tests do not establish a safety boundary.

**Developer instructions:** Integrate detection before final persistence, using recent social and authoritative/sensor
records constrained by tenant/run, hazard, location and time. Persist adjusted confidence/status and auditable reasons;
send flagged signals through the guarded Monitoring path. Define bounded state sharing across workers.

**Tester instructions:** In [pipeline integration][pipeline-test] and [misinformation tests][misinfo-test], ingest a
real-adapter burst and assert stored escalation. Negative: other tenant/run context cannot corroborate a signal.
Edge: late arrivals, community reports, missing context and worker restart still produce deterministic guarded results.

**Dependencies / future validation:** AUD-001, AUD-014, AUD-020; V01, V03.
**Acceptance:** Tests reach the detector through production composition, not direct helper calls alone, and inspect
the final stored status and consumer decision.

### AUD-014: Misinformation Rules Differ from Their Contract

- [x] AUD-014 (P1) Correct burst, contradiction, and duplicate-amplification semantics.

**Affected:** T046, T051, T052, T053; FR-010a; US4-AS3; EC-002.

**Expected vs observed / impact:** [Burst detection][burst] counts posts rather than distinct accounts, ignores the
authoritative-corroboration exclusion, and sorts timestamps without preserving their original indices. Later
qualifying windows can flag the wrong posts. [Amplification][duplicate] uses Jaccard instead of required cosine,
flags by list order rather than earliest timestamp, and keeps no cross-batch window. Contradiction handling assumes
Point coordinates, does not validate the provided corroborating source, and has no authoritative-versus-authoritative
conflict path. [Tests][misinfo-test] mostly use identical ordered point posts and broad count assertions.

**Developer instructions:** Implement explicit scoped windows with source/account identities and stable timestamp/index
mapping. Honour configured cosine/time thresholds and retain the earliest post; persist independent provenance for
contradictory authoritative observations and request human review without discarding either.

**Tester instructions:** Positive: 20 distinct uncorroborated accounts flag and confidence halves on contradiction.
Negative: one account repeated, authoritative corroboration, or dissimilar text does not flag. Edge: shuffled times,
invalid timestamps, exact thresholds, polygons, cross-poll windows, and duplicate lists supplied newest-first.

**Dependencies / future validation:** None for rule-unit repair; AUD-013 for integration; V03.
**Acceptance:** Exact flagged identities/statuses/confidence, not just nonzero counts, match the documented rules;
contradictory authoritative evidence remains independently retrievable.

### AUD-015: Tier-2 Decisions Are Not Persisted and Can Be Bypassed

- [x] AUD-015 (P1) Enforce one fail-closed classification decision across all Monitoring entry points.

**Affected:** T054, T055; FR-010a, FR-019, FR-037a; US4-AS3.

**Expected vs observed / impact:** [The later Monitoring pipeline][monitor-pipe] does stop on misinformation or
unavailable/timeout classifications, which is credited. It never updates the stored signal to rejected or stores
the required rationale in its provenance. [build_high_risk_handoff][monitor] itself ignores validation status, and
[the MAF wrapper][maf-monitor] calls it without Tier 2. [Classification][monitor-llm] uses substring checks, so a
non-contract response containing `credible` can be accepted. [The misinformation contract test][monitor-contract]
asserts a returned string and discards the handoff result, not non-forwarding or persistent rejection.

**Developer instructions:** Make the guarded decision the only dispatch-capable entry point; validate exact structured
classification output, persist status/rationale before forwarding, and preserve escalated state for unavailable LLM
or required human review. Carry tenant/run identity through legacy and MAF adapters.

**Tester instructions:** Positive: credible escalation is persisted before an allowed handoff. Negative: rejected,
misinformation, timeout/unavailable, malformed and adversarial responses never forward. Edge: direct facade use,
duplicate retries, storage failure and suspicious threshold cases maintain the same decision and audit trail.

**Dependencies / future validation:** AUD-013 for end-to-end flag generation; V03, V04.
**Acceptance:** Every public/worker/facade route enforces the same non-forwarding invariant and stored final decision;
tests assert delivery absence and stored provenance, not only classifier return values.

### AUD-016: Incident Association Uses Jurisdiction OR Approximate Geography

- [x] AUD-016 (P1) Associate by authorised jurisdiction and actual incident overlap, with full multi-incident fan-out.

**Affected:** T010, T019, T060; FR-019a, FR-025; US1-AS4, US5-AS1.

**Expected vs observed / impact:** [Matching][assoc] accepts every active incident sharing a jurisdiction before
checking geography; otherwise it uses coarse state bounding boxes, not incident affected areas, and only handles
Points. [The base calls associate][pipeline], which takes the first match, not [associate_multi][multi]. No call
automatically creates a national primary and affected-jurisdiction reference set. [Tests][association-test] create
incidents with no actual footprint, so jurisdiction-only matches look sufficient.

**Developer instructions:** Use stored active incident boundaries and jurisdiction/agency scope together; implement
Point/Polygon intersection and national coverage resolution. Persist one record per matching incident with distinct
record identity and shared correlation, plus resolvable jurisdiction references where required.

**Tester instructions:** Positive: inside one or two footprints creates exactly the corresponding records. Negative:
same-state but distant or closed incidents do not match. Edge: boundary touch, overlapping jurisdictions, national
polygons, absent geometry, zero matches and three simultaneous live/simulation scopes.

**Dependencies / future validation:** AUD-004, AUD-042; [association tests][association-test], V02.
**Acceptance:** No same-state false match; every genuine matching incident receives an independently queryable record,
and unmatched signals remain null without leaking across scope.

### AUD-017: Retrospective Association Has No Working Declaration-to-Storage Path

- [x] AUD-017 (P1) Wire incident declaration to audited, scoped retrospective association using a compatible repository.

**Affected:** T061; FR-019b; US6-AS5.

**Expected vs observed / impact:** [Monitoring retrospective_associate][monitor-retro] passes `tenant_id` to the
shared repository's `query_unassociated(..., scope=...)`; the API repository has no such method. [Cosmos updates][repo-update]
are `pass`. The helper uses jurisdiction/time but no incident footprint, and [incident declaration][declare] invokes
a resource governor, not association. The standalone Monitoring server constructs no repository. Its optional HTTP
association audit is not proof of an actual incident-declaration event binding or per-signal update evidence.

**Developer instructions:** Agree a repository interface, wire it into the real declaration handler/consumer, persist
conditional updates using full scope, and retain declaration event ID, timestamp, matched geometry and each association
outcome in audit. Keep the lookback configurable and retries idempotent.

**Tester instructions:** Extend [association][association-test] and [storage update tests][storage-update-test]. Positive:
new declaration associates matching null signals within 24 hours. Negative: old, other-jurisdiction/run, already-linked
or outside-footprint records stay unchanged. Edge: custom lookback, concurrent declarations, partial Cosmos failure
and replayed declaration events.

**Dependencies / future validation:** AUD-001, AUD-004, AUD-016; V02, V03, V05.
**Acceptance:** The production declaration path produces durable, geometry-correct and auditable associations without
signature errors, no-op updates, duplicate records or cross-scope modification.

### AUD-018: Constant Freshness Scores Hide Stale and Future Data

- [x] AUD-018 (P1) Compute freshness from real timestamps and configured source cadence on every ingestion.

**Affected:** T008, T024, T027, T038, T043; FR-014; SC-001; US3-AS1; EC-006.

**Expected vs observed / impact:** [Enrichment][enrich] computes freshness only when absent, but all the inspected
normalisers provide fixed values such as 0.85 or 0.9. Stale payloads therefore retain high freshness. The fallback
[freshness function][freshness] treats a negative time delta as 0.95 and does not flag future clock drift. A malformed
or mixed-timezone record can also escape its narrow exception handling. These scores influence handoff safety.

**Developer instructions:** Centralise cadence-aware freshness calculation after source-time normalization, explicitly
handle skew/missing time, and prevent adapters or untrusted API callers from overriding computed quality silently.
Record anomaly reasons and reconcile the freshness-adjusted routing contract rather than reverting it blindly.

**Tester instructions:** Add real observation-to-pipeline cases in [BoM tests][bom-test] and [pipeline tests][pipeline-test].
Positive: within cadence is at least 0.8. Negative: beyond three cadences is below 0.3; future-skewed data is flagged.
Edge: exact cadence/three-cadence boundary, zero/invalid config, timezone offsets and long source outages.

**Dependencies / future validation:** AUD-010, AUD-023; V01, V03.
**Acceptance:** Stored freshness is timestamp-derived for every adapter, and future or stale data cannot masquerade
as a fresh validated observation.

### AUD-019: Sensor Adapters Do Not Supply the Required Physical Measurements

- [x] AUD-019 (P1) Implement measurement, station, range, quality, and flood-threshold semantics for real sensor feeds.

**Affected:** T024, T038, T039, T040, T043, T044; FR-008, FR-013; US3-AS1, US3-AS2, US3-AS4.

**Expected vs observed / impact:** [River retrieval][river] emits `value`/`quality`, but [observation normalization][obs]
validates `water_level`/`flow_rate`; it never loads flood thresholds or elevates threshold-crossing confidence. Missing
coordinates default to Sydney. [EPA][epa] defaults to a site-details endpoint rather than measurement values. The
normaliser can mark a record with no recognized measurements validated and accepts NaN because comparisons do not
reject it. Network coverage is limited to one AWS station and a hardcoded small river discovery subset.

**Developer instructions:** Preserve source units/quality codes and station coordinates, normalize all specified AWS,
gauge and EPA fields, use configured per-gauge thresholds, reject non-finite/out-of-range values and incomplete
measurement records, and distinguish sensor metadata discovery from observation acquisition.

**Tester instructions:** Positive: AWS fields, rising gauge crossing minor/moderate/major and PM2.5/PM10/ozone normalize
with correct location/confidence. Negative: 150-degree temperature, negative wind, NaN/infinity, nonnumeric and empty
measurement records reject with reasons. Edge: null source readings, exact bounds, missing calibration and threshold data.

**Dependencies / future validation:** AUD-010, AUD-018, AUD-020; extend [BoM tests][bom-test], V01.
**Acceptance:** Stored signals contain validated physical readings and real station context; gauge threshold crossings
drive the documented Monitoring evaluation without invented measurements or geography.

### AUD-020: Source Trust and Provenance Are Not Preserved End to End

- [x] AUD-020 (P1) Bind source identity, collection method, quality, and provenance to the registry rather than caller defaults.

**Affected:** T008, T021, T023, T024, T047, T050, T079, T080, T081; FR-002, FR-013, FR-015, FR-018.

**Expected vs observed / impact:** [Base enrichment][enrich] fills only missing confidence/collector. Normalisers
hard-code scores/methods and do not consult the [catalogue][catalogue]; radar/observations conflict with catalogue
kind/tier. Social/IMS provenance omits source timestamps; field identity is not derived. [Signal][signal-model]
drops source name/kind and trust metadata, while [dashboard counting][dashboard] expects `provenance.sourceKind`,
which the canonical JSON schema disallows. GeoJSON uses generic fallbacks and truncates MultiPolygon geometry.
Road-closure Snap reports default to `community_report`, not `infrastructure`.

**Developer instructions:** Agree the registry-to-envelope-to-document mapping; preserve source identity and quality
facts in schema-approved fields, including original timestamp and authenticated collector. Validate source kind,
collection method, geometry and tier; keep unknown facts explicitly unknown. Correct community infrastructure mapping.

**Tester instructions:** Positive: representative sources round-trip name/kind/tier/time/collector and render correct
dashboard counts. Negative: forged authoritative tier or officer identity cannot increase trust. Edge: MultiPolygon,
unknown source, calibration unavailable, geotagged road closure and conflicting catalogue/adaptor metadata.

**Dependencies / future validation:** AUD-007, AUD-042; [BoM][bom-test], [GeoJSON][geo-test], [API tests][live-api-test], V01, V05.
**Acceptance:** Every persisted/queryable signal has honest, schema-compatible provenance and source-quality semantics;
downstream consumers need no incompatible provenance extension to identify its source.

### AUD-021: Required National Source Coverage and Provider Attribution Are Incomplete

- [x] AUD-021 (P1) Complete or formally resolve source coverage, provider verification, and approved substitutions.

**Affected:** T026, T027, T029, T030, T030a, T030b, T034, T035, T040, T041, T084; FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-022.

**Expected vs observed / impact:** [Configs][configs] contain 24 entries, ten disabled. Only NSW/VIC fire are enabled;
five other state fire instances and VIC/QLD SES instances are absent from the factory/config list, and NSW SES is
disabled. Forecasts instantiate the warnings class; no state-summary XML/individual-station cadence split exists.
[Earthquake polling][quake] fetches a magnitude-filtered USGS day feed but labels it GA. [RSS code][rss] explicitly
replaced RSS with FTP, contrary to the still-current RSS requirement. Sentinel uses a different API/product profile
than the specified Data Space GeoTIFF contract. These changes are not backed by checked-in provider validation records.

**Developer instructions:** Use the source matrix below to assign supported endpoints/formats/owners and activation
preconditions. Add missing required instances/adapters or obtain explicit scope changes. Preserve actual provider
attribution when substituting a source; never call a substitution verified GA data. Separate agreements from code readiness.

**Tester instructions:** Positive: each required state/product fixture selects its own adapter, cadence, ID and
provider. Negative: HTML/unsupported schemas and unapproved substitutes reject visibly. Edge: disabled/unavailable
sources show honest status; transport data required by downstream stored-data contracts has a traced ingestion path.

**Dependencies / future validation:** AUD-023, AUD-043; V01, V05, V07.
**Acceptance:** Every mandatory source/product has a documented, tested path or explicit approved deferral; no silent
national coverage gaps or falsely attributed upstream data remain.

### AUD-022: Fixed Feed Slices Starve Later Records

- [x] AUD-022 (P1) Process complete feed updates with bounded batching, continuation, and backpressure.

**Affected:** T027, T029, T030, T034, T035, T038, T039, T040, T041, T079; FR-004, FR-005, FR-006, FR-007, FR-008, FR-012, FR-018a.

**Expected vs observed / impact:** [Fire][fire] and [SES][ses] take the first 100 features; [GA earthquakes][quake]
takes the first 50 before geographic filtering. Other adapters repeatedly slice observations/products to 10/20/50
records without continuation. When unchanged leading records remain at the front, later new incidents never reach
dedup/normalization. A large feed is silently truncated during exactly the surge the specification targets.

**Developer instructions:** Separate bounded work-per-cycle from completeness: retain cursors/queues or drain the
full returned collection in resumable batches. Filter geographically before limiting when appropriate. Record
backlog/drop reasons and preserve newest relevant observations under supported rate-limit policy.

**Tester instructions:** Positive: feeds larger than every current slice eventually persist all eligible new items.
Negative: malformed one item cannot abandon later valid ones. Edge: unchanged leading pages, inserts/reordering,
restart between batches, national/non-AU mixtures and sustained growth beyond one poll capacity.

**Dependencies / future validation:** AUD-008, AUD-009; extend [pipeline integration][pipeline-test], V01, V07.
**Acceptance:** There is an explicit bounded-progress mechanism with no permanently starved eligible records and
observable backlog under surge.

### AUD-023: Factory Ignores Most Runtime Configuration

- [x] AUD-023 (P1) Apply configuration identity, intervals, formats, source IDs, TTLs and endpoints to constructed pipelines.

**Affected:** T006, T009, T011, T016, T026, T027, T030b, T079, T084; FR-001a, FR-004, FR-005, FR-018a.

**Expected vs observed / impact:** [create_pipeline][factory] forwards breaker settings and only certain explicit
constructor endpoint arguments. It ignores configured polling interval, pipeline ID, source IDs, endpoint format,
and effective dedup TTL. Forecast and warning entries become the same `bom-warnings` identity; ICON/WebEOC config
URLs are ignored because constructors use `webeoc_url`/`icon_url`. Unknown IDs return `None`, then worker startup
calls `.run()`. [NormaliserRegistry][normal-registry] is not registered or used by this composition.

**Developer instructions:** Define a typed construction contract and validate all config entries against supported
adapters/registry sources. Honour every supported setting or reject it explicitly. Load approved external configuration
without source edits; validate duplicate identities and unknown formats before starting tasks.

**Tester instructions:** Extend [pipeline integration][pipeline-test]. Positive: instantiate every declared config
and inspect effective ID, URL, interval, format and TTL. Negative: unknown/duplicate ID or unsupported override fails
startup clearly. Edge: disabled entries, separate forecast/tsunami instances, both IMS endpoints and customised states.

**Dependencies / future validation:** AUD-042; V01, V06.
**Acceptance:** Declared and effective runtime configuration agree; worker/factory tests use the real registry, not
a replacement mock factory.

### AUD-024: Blocking I/O and Health/Shutdown Logic Defeat Worker Isolation

- [x] AUD-024 (P1) Make polling nonblocking, health truthful, and shutdown drain in-progress work reliably.

**Affected:** T016, T059, T078, T087; FR-001a, FR-037a; SC-001, SC-002.

**Expected vs observed / impact:** Synchronous FTP in [BoM polling][bom-warn], synchronous blob upload in
[RawPayloadBlobStore][blobactual], and synchronous Redis operations run inside async methods on one event loop.
[Worker health flags][worker-health] never inspect failed tasks/dependencies; the entry-point HTTP handler returns healthy
unconditionally. [Stop][worker-stop] waits 30 seconds per task, while [pipeline loops][pipeline-loop] still sleep
their full polling interval and may be forcibly cancelled during work. No worker test body was located.

**Developer instructions:** Use asynchronous clients or bounded thread offloading, per-source supervision and
cancellation-aware waits. Readiness must reflect mandatory clients and active tasks; liveness must detect a stuck
worker. Drain started items within a documented deployment termination budget and close resources.

**Tester instructions:** Positive: a slow FTP/download does not prevent another pipeline or simulation from advancing.
Negative: dead task, missing dependency or blocked loop is not ready. Edge: shutdown during poll/upload, long idle
interval, repeated stop, disabled-only configuration, Windows signal support and restart after forced termination.

**Dependencies / future validation:** AUD-023; [pipeline integration][pipeline-test], V01, V04, V06.
**Acceptance:** Independent workers progress under one stalled source; probes reflect real state; shutdown neither
loses committed work nor requires cancelling normal idle sleeps.

### AUD-025: Breaker State Does Not Update Registry or Meet Recovery Bounds

- [x] AUD-025 (P1) Connect per-source breaker transitions to degraded status and reconcile recovery timing.

**Affected:** T008, T017, T082, T088; FR-016, FR-018b; SC-008; US1-AS5.

**Expected vs observed / impact:** [CircuitBreakerState][breaker] changes local state/logs but never updates the source
registry. `_poll_cycle` treats a returned empty list as success; [IMS][ims] catches both upstream failures and returns
empty, and river per-gauge failures are similarly swallowed. Half-open is considered only after the normal poll sleep;
long polling intervals and a 300-second backoff cannot guarantee recovery within one minute. The backoff trip count
never resets after a successful recovery. [Contract tests][breaker-test] manipulate deadlines and do not assert
registry changes, real timing, or exact backoff reset/cap.

**Developer instructions:** Track outcome and breaker state per actual source, emit structured transitions with IDs,
update degraded/recovered registry state, and schedule health probes independently of slow product cadence. Agree the
SC-008 versus maximum-backoff contract explicitly; preserve partial-source failure information.

**Tester instructions:** Positive: three failures degrade the correct source and a successful half-open recovers it.
Negative: both IMS endpoints failing is not success. Edge: partial source failure, 6-hour cadence, 300-second backoff,
repeated recovered outages and injected clocks at exact deadlines.

**Dependencies / future validation:** AUD-023, AUD-024, AUD-042; [breaker tests][breaker-test], V02, V07.
**Acceptance:** Source status and transition telemetry match actual outcomes; approved degradation/recovery bounds
are demonstrated for every cadence, not just a one-second mock pipeline.

### AUD-026: Raw Archival Is Neither Byte-Preserving Nor Simulation-Scoped

- [x] AUD-026 (P1) Preserve original payload bytes with correct format, paths, scope and durable references.

**Affected:** T008, T014, T064, T065; FR-017, FR-026, FR-029; SC-007.

**Expected vs observed / impact:** [Production archival][blobactual] JSON-serializes already parsed/mutated dictionaries
with `default=str` and stores dates as `YYYY/MM/DD`, not the contract's `YYYY-MM-DD`. XML was decoded with replacement
and wrapped; GeoJSON adapters mutate features before archival. [The alternate helper][blob] can store bytes and
simulation prefixes, but base processing always calls `store_raw_payload`, never `store_simulation_payload`, and
Signal retains no raw reference. Failed normalisations archive nothing.

**Developer instructions:** Carry original response/product bytes and content type separately from adapter metadata;
store content-addressable/versioned evidence under the agreed live or simulation prefix and preserve the exact URI
in a schema-compatible signal/audit link. Handle shared raw evidence for fan-out without losing per-record correlation.

**Tester instructions:** Positive: raw XML/JSON bytes including whitespace round-trip exactly at the specified path.
Negative: an encoding error or failed normalization still has diagnostic raw evidence. Edge: binary bytes, source
IDs needing safe path encoding, midnight UTC, multi-incident copies and simultaneous live/simulation submissions.

**Dependencies / future validation:** AUD-042; [storage][storage-test], [pipeline tests][pipeline-test], V02.
**Acceptance:** Every persisted record has retrievable byte-faithful raw evidence and audit correlation; simulation
raw payloads are never written to the live prefix.

### AUD-027: Full Imagery and On-Demand Retrieval Are Unimplemented

- [x] AUD-027 (P1) Implement the metadata-to-binary lifecycle, geographic scoping and corruption recovery.

**Affected:** T025, T028, T041, T042, T045, T045a, T045b; FR-009, FR-009a, FR-027; US3-AS3, US5-AS2; EC-003.

**Expected vs observed / impact:** [Radar][radar], [Sentinel][sentinel] and [Himawari][himawari] only create metadata.
They never intersect real coverage with incidents, download full imagery, or call [binary storage][binary-store].
The 50-km adjacency buffer, simulation-region activation, on-demand endpoint/service, expiry handling, integrity
checking and signal URI update were not found in NS-01/NS-03. Sentinel labels JP2 and uses a different catalogue shape;
Himawari labels every IDE product PNG and supplies a national coverage box rather than actual product metadata.

**Developer instructions:** Implement the owner path through existing adapters/blob/repository boundaries. A service
at `apps/api/app/services/ingestion/binary_retrieval.py` is a **proposed path, not existing evidence**. Validate allowed
source URIs, product format/coverage, source expiry, content integrity and atomic upload; update the signal only after
successful storage. Support the configured 50-km radar buffer and `_on-demand` path without granting arbitrary URL fetches.

**Tester instructions:** Positive: no incident means zero downloads; overlapping/adjacent incident or simulation
downloads once, stores the correct format/path and updates URI. Negative: unrelated region, expired product, forbidden
URL, truncated image and storage failure do not publish a bad blob. Edge: exact buffer boundary, multipart download,
retry, multiple incidents, concurrent on-demand requests and source deletion between lookup and fetch.

**Dependencies / future validation:** AUD-001, AUD-010, AUD-016, AUD-026; extend [storage][storage-test] and
[pipeline tests][pipeline-test], V01, V02.
**Acceptance:** All four FR-009a modes work through a reachable entry point; failed/corrupt binaries leave no accepted
asset, and every stored reference resolves to the correct scoped asset.

### AUD-028: Social and Community Polling Are Empty Stubs

- [x] AUD-028 (P1) Implement approved social/community transports and rate-limit behavior.

**Affected:** T047, T048, T049, T050; FR-010, FR-011; US4-AS1, US4-AS2; EC-005.

**Expected vs observed / impact:** [Twitter][twitter], [Facebook][facebook], [Reddit][reddit] and [Snap][snap] each
return an empty list from `poll_source`. Disabled configuration accurately acknowledges access prerequisites, but
adding credentials cannot activate absent streaming/polling implementations. No reconnect policy, official-account
filter, Meta call budget, Reddit active/idle switch, pagination or newest-first throttling is implemented.

**Developer instructions:** Build documented, injectable transports for authorised APIs; keep secrets outside source
and acquire agreements out of band. Enforce streaming reconnection/backoff, request budgets, active-event cadences,
and text-only scope. Emit blocked/unconfigured/rate-limited health instead of a false successful empty feed.

**Tester instructions:** Positive: controlled API fixtures produce posts/reports with correct source/tier/geotag.
Negative: missing credentials, 401/403 and 429 do not silently pass or expose secrets. Edge: Retry-After, reconnect,
duplicate batches, 200 calls/hour Meta budget, 60 requests/minute Reddit limit, and active-to-idle transition.

**Dependencies / future validation:** AUD-013, AUD-014, AUD-020, AUD-023, AUD-043; V01, V03.
**Acceptance:** Each enabled transport actually consumes its documented source under rate limits; configuration-only
or empty-stub behavior is not represented as operational ingestion.

### AUD-029: IMS Integration Lacks Source-Specific Connection and Mapping Contracts

- [x] AUD-029 (P1) Implement separate authenticated ICON/WebEOC connection, mapping and per-source failure semantics.

**Affected:** T079, T080, T081; FR-012, FR-015, FR-016; US7-AS1, US7-AS2.

**Expected vs observed / impact:** [IMS polling][ims] uses unauthenticated GETs to placeholder defaults and both
services on every instance. Factory endpoint settings do not reach its named constructor arguments. Both failures
are swallowed. [Mapping][ims-normalise] omits responding units, deployment/situation/board structure and authoritative
officer provenance, and uses fabricated location/time defaults. Base raw/audit metadata uses the first configured
source ID even for ICON records.

**Developer instructions:** Provide per-provider endpoint/authentication/schema adapters and per-source breaker/status;
map incident reference, units, resources, situation updates, identity, location and timestamps from approved contracts.
Audit the envelope's actual source ID, not the pipeline's first source. Preserve the API identity protections in AUD-002.

**Tester instructions:** Positive: representative ICON and WebEOC fixtures map all required fields and correct source
IDs. Negative: authentication failure, wrong board schema, and forged reporter identity reject visibly. Edge: one
provider down, both down, identical incident IDs across providers, missing coordinates and partial multi-record responses.

**Dependencies / future validation:** AUD-002, AUD-020, AUD-023, AUD-025, AUD-043; V01, V02, V05.
**Acceptance:** Actual configured endpoints can be tested without source edits; records and failures remain correctly
attributed, and required IMS fields/provenance survive durable ingestion.

### AUD-030: Simulation Runner Bypasses the Shared Pipeline and Correct Save Contract

- [x] AUD-030 (P1) Inject simulated source payloads through the real pipeline with explicit run isolation.

**Affected:** T066, T075, T078; FR-029, FR-032, FR-033, FR-037, FR-037a; SC-006, SC-009.

**Expected vs observed / impact:** [Runner phase processing][sim-phase] produces final envelope dictionaries and
calls `.save(dict)` without scope, whereas [the shared repository][repo] requires a Signal object and defaults to
live. Exceptions are logged per generator and the run can still complete. No shared normalisation, validation,
raw archive, dedup/association or agent delivery is involved. One `_generated_envelopes` list persists across starts
and is shared by concurrent runs. [Integration tests][sim-test] replace the repository with a permissive list.

**Developer instructions:** Introduce a simulation source-input boundary into the same supervised processing workers,
carrying validated run context. Convert/validate through production adapters, use the canonical repository interface,
partition raw/audit/handoffs, and keep per-run state separate. Failed persistence must affect run status/counts.

**Tester instructions:** Positive: same raw source fixture through live and simulation yields equivalent content except
markers/scope. Negative: dictionary/Signal interface mismatch and failed save cannot count as completion. Edge: reuse
one runner, three concurrent runs plus live, abort during a batch, and live declaration during simulation.

**Dependencies / future validation:** AUD-001, AUD-004, AUD-005, AUD-007, AUD-016; V02, V04.
**Acceptance:** Simulation exercises the actual pipeline and consumers; no run shares buffers, dedup state incorrectly,
or live storage. Counts reflect successfully processed/persisted records.

### AUD-031: Scenario Coverage and Native-Format Parity Are Not Established

- [x] AUD-031 (P2) Define source relevance and generate all required scenario source shapes through their adapters.

**Affected:** T067, T071, T072, T076; FR-032, FR-033, FR-038; SC-005, SC-006.

**Expected vs observed / impact:** [Templates][templates] hard-code four or five source IDs, omit required transport,
evacuation and some SES steps, and do not derive relevance from the 46-source catalogue. No production generator
registration is wired. SensorGenerator always labels AWS; other generators similarly emit a small fixed ID set rather
than each source's native XML/GeoJSON/JSON/binary-metadata shape. [039 feed coverage][feed-test] provides 13 later
synthetic shapes, but does not map them to the 006 catalogue denominator or the live adapters.

**Developer instructions:** Create an explicit scenario/source relevance matrix with justified exclusions for derived
and non-hazard catalogue entries. Register supported generators and format adapters, implement missing template
steps, and measure both activated sources and actual emitted source IDs. Do not substitute envelope-key similarity
for source-format parity.

**Tester instructions:** Positive: each of four scenarios emits at least 80% of its documented relevant sources through
the same schema/normalisers. Negative: missing registration, wrong emitted ID or missing mandatory phase fails the
coverage gate. Edge: non-NSW regions, all-source scenarios, zero relevant-source ambiguity and historical overlays.

**Dependencies / future validation:** AUD-030, AUD-033, AUD-042; [scenario tests][flood-test], [storm tests][storm-test], V04, V07.
**Acceptance:** A reproducible denominator and emitted-ID manifest establish SC-005; native-format fixtures and the
canonical schema establish parity rather than only common dictionary keys.

### AUD-032: Time Compression Changes Sleeps, Not Source Cadence

- [x] AUD-032 (P2) Schedule per-source recurring events on a configurable compressed scenario clock.

**Affected:** T066, T067, T077, T078a; FR-034, FR-039; SC-006.

**Expected vs observed / impact:** [The runner][sim-phase] emits one signal/batch per source per phase then divides
one phase sleep by the compression ratio. It does not repeatedly generate at the source cadence, consume phase
triggers, or update progress counters/current phase. [Hydrograph][flood] output is not used by the runner. Later
[warp scheduling][warp] and [warp tests][warp-test] demonstrate scheduled-record timing, but not the 006 parametric
source clock or the specified 24:1 cadence assertion.

**Developer instructions:** Reuse an agreed server-owned clock/scheduler, separate simulated time from wall time,
schedule each source at its documented cadence, and apply phase triggers/parameters. Support interruption without
waiting a long phase sleep and record effective timing/progress.

**Tester instructions:** Positive: a source at 24:1 emits at 24 times its normal wall-clock cadence with ordered source
timestamps. Negative: invalid/zero/negative ratio rejects. Edge: exact phase boundaries, partial last interval, pause,
abort, speed change and long events compressed to two hours; use injected clocks instead of real waits.

**Dependencies / future validation:** AUD-030; [simulation integration][sim-test], [flood tests][flood-test], V04.
**Acceptance:** Emission intervals, counts, timestamps and phase transitions match the configured clock for every source.

### AUD-033: Parametric Models Lack Required Calibration and Geographic Coherence

- [x] AUD-033 (P2) Implement and document calibrated scenario models and target-region constraints.

**Affected:** T068, T069, T070, T071, T072, T077, T078b; FR-033, FR-035; US6-AS1, US6-AS3.

**Expected vs observed / impact:** [Flood][flood] fixes rise/plateau fractions and does not use moderate/major thresholds
in generation. [Fire][fire-gen] calculates FFDI but not fuel-load-dependent spread/perimeter evolution. [Cyclone][cyclone]
uses a simple bearing/category progression, without central pressure/radius-of-maximum-wind or documented calibration.
Scenario target polygons do not constrain generation; default NSW locations and a fixed social bounding box are used.
Neither the original nor [later gauge feed][later-gauge] implements upstream/downstream network ordering.

**Developer instructions:** Use documented Australian calibration datasets/formulas, configurable hydrograph rise/peak/
recession and gauge topology, wind-directed fire growth/fuel inputs, and cyclone track/intensity parameters. Generate
inside validated target geometry and propagate common physical state to all source types. Record model version/assumptions.

**Tester instructions:** Positive: flood crosses named thresholds in order, upstream precedes downstream, fire expands
with wind and cyclone parameters change track/intensity. Negative: impossible inputs or outside-region positions reject.
Edge: non-NSW targets, polygon boundaries, extreme but plausible values, recession and overlapping hazards.

**Dependencies / future validation:** Calibration/owner evidence in AUD-043; [flood][flood-test], [fire][fire-test],
[cyclone tests][cyclone-test], V04.
**Acceptance:** Reproducible quantitative fixtures demonstrate the documented physical and geographic relationships,
not merely nonnegative FFDI or changing coordinates.

### AUD-034: Misinformation Ratio Override Is Ignored

- [x] AUD-034 (P2) Honour validated per-run social mix ratios and reproducible run-specific randomness.

**Affected:** T073, T066; FR-036, FR-039; US6-AS4.

**Expected vs observed / impact:** [generate_batch][social-gen] accepts `misinfo_ratio` but computes misinformation as
the remainder after accurate/duplicate counts; changing only the requested misinformation ratio has no effect.
The runner's dataclass carries no ratio, and randomness uses global state. Invalid ratios can produce inconsistent
totals; location is always near the Blue Mountains regardless of scenario target. No direct ratio assertion was found.

**Developer instructions:** Define ratio override/normalization and rounding rules, validate total/count bounds, pass
effective ratios from run configuration, and isolate randomness by run or persist the exact generated sequence.
Keep deliberate duplicates truly comparable and constrain geography to the target scenario.

**Tester instructions:** Positive: defaults produce the documented 70/15/15 mix and a changed ratio changes output.
Negative: invalid ratios/counts fail explicitly. Edge: counts 0/1/3, all-accurate/all-misinformation, rounding, two
concurrent runs, fixed-seed replay and non-NSW location targets.

**Dependencies / future validation:** AUD-030, AUD-032; extend [simulation integration][sim-test], V04.
**Acceptance:** Emitted type counts exactly follow documented rounding/override rules and are recorded for replay;
changing a supported run parameter has an observable, isolated effect.

### AUD-035: Historical Overlay Is Disconnected and Breaks the Schema

- [x] AUD-035 (P2) Integrate schema-compatible historical overlays with safe geometry/time/severity perturbations.

**Affected:** T074, T066; FR-033a, FR-037; SC-006; US6-AS5.

**Expected vs observed / impact:** [HistoricalOverlay][overlay] is not called by the runner or API configuration path.
It adds `provenance.historicalOverlay`, which [the schema][schema] forbids. Coordinate arithmetic only supports flat
Point arrays and fails on Polygon nesting; source timestamps are not shifted along with occurrence/receipt time.
Severity scaling has no plausibility validation. No overlay assertion bodies were located in NS-02.

**Developer instructions:** Resolve a safe simulation-assets reference, validate data/model versions, select overlay
instead of parametric generation when requested, and preserve provenance using approved fields. Transform supported
geometry recursively and validate all perturbed timestamps/values before common ingestion. Keep parametric-only operation valid.

**Tester instructions:** Positive: actual historical fixture replay with location/time/severity perturbation passes the
live schema path. Negative: invalid path, malformed file, extra provenance and out-of-range scaling reject. Edge:
Point/Polygon/MultiPolygon policy, empty dataset, timezone shifts and no-overlay run.

**Dependencies / future validation:** AUD-007, AUD-030; extend [simulation integration][sim-test], V04.
**Acceptance:** Overlay configuration reaches execution, replaces the intended source sequence, preserves provenance
consistency and cannot emit schema-invalid or implausible records silently.

### AUD-036: Simulation API and Domain Models Do Not Implement the Published Contract

- [x] AUD-036 (P2) Resolve and implement the scenario/run API contract with durable validated configuration.

**Affected:** T004, T005, T066, T075; FR-032, FR-039; contract operations `listScenarios`, `createScenario`, `startSimulationRun`, `getSimulationRun`, `abortSimulationRun`.

**Expected vs observed / impact:** [The published contract][openapi] exposes `/simulations/scenarios` and `/simulations/runs`.
[Registered routes][sim-api] instead manage tenants and later UUID-based simulation endpoints. No required scenario/run
handlers or wiring to the 006 runner were found. [Scenario model][scenario-model] does not validate Polygon shape or
catalogue IDs. [Domain SimulationRun][run-model] has transition rules but the runner uses a separate dataclass with
`pending`/`failed` states and different fields. [Contract tests][sim-api-test] build response dictionaries for the later API,
not HTTP assertions against the 006 OpenAPI.

**Developer instructions:** Obtain an explicit versioned compatibility/supersession decision before changing public APIs.
Wire a single validated scenario/run model, durable repository and execution path; validate source IDs, target geometry,
ratio bounds, creator/run authorisation and allowed transitions. Preserve existing tenant clients or provide documented migration.

**Tester instructions:** Positive: exercise each agreed HTTP operation and exact response schema/status. Negative:
unknown scenario/source, invalid Polygon/ratio and unauthorised run operations reject. Edge: duplicate start, restart,
abort before/during execution, terminal states and old-client compatibility.

**Dependencies / future validation:** AUD-030, AUD-042; [API contract][sim-api-test], [scenario tests][scenario-test], V04, V05.
**Acceptance:** The authoritative OpenAPI, routes, persisted models and transitions agree, and tests call real handlers
rather than validating handwritten response examples.

### AUD-037: Complete Run Replay Is Not Connected to Generated Signals and Decisions

- [x] AUD-037 (P2) Persist replayable run parameters, signal sequence and downstream decision references.

**Affected:** T005, T066, T074, T075; FR-039; US6-AS5.

**Expected vs observed / impact:** [The 006 runner][sim-runner] keeps envelopes only in a process list and records no
durable complete run configuration/agent decision timeline. Later [warp scheduling][warp] records deliveries, which
is partial replacement evidence. However, [seed_from_replay][seed-replay] ignores its `start`, `end` and compression
arguments, copies a bounded live query, and is not connected to original run-generation parameters/handoffs. Template
seeding constructs a service without a template Cosmos client, so its loader returns `None` in that composition.

**Developer instructions:** Persist run/scenario version, target region, activated sources, model/overlay version,
effective ratios/clock and exact generated ordering or sufficient deterministic inputs. Store scoped handoff/recommendation
references and rebuild replay after restart. Apply requested historical time bounds/compression and wire template retrieval.

**Tester instructions:** Positive: completed run replays identical ordered signals and linked decisions after restart.
Negative: wrong-run references and inaccessible history cannot contaminate replay. Edge: aborted/partial runs, empty
window, more than 10,000 records, overlapping run IDs, duplicate delivery and changed scenario templates.

**Dependencies / future validation:** AUD-030, AUD-032, AUD-035, AUD-036; [simulation][sim-test], [warp tests][warp-test], V04, V05.
**Acceptance:** A planner can reconstruct the full exercise with original parameters and scoped decisions, without
relying on a surviving Python object or ignoring requested replay bounds.

### AUD-038: Ingestion Status and Required Observability Are Not Operational

- [x] AUD-038 (P2) Publish truthful cross-process pipeline status, rolling metrics and partition-capacity alarms.

**Affected:** T008, T082, T085; FR-018b; SC-008; EC-007.

**Expected vs observed / impact:** [ingestion_status][status] is not imported/mounted in [the API router][router], and
its registration helper has no caller. It reads an empty process-local list and sums lifetime `signalsIngested` as
`totalSignalsLastHour`. [Metrics][metrics] retain all latency samples indefinitely and do not implement the required
five-minute dedup window, unresolved DLQ gauge, partition size/count sampling or timeout outcome. OTel counters/histograms
exist but do not correct these missing semantics. No per-logical-partition 80%-of-20GB alarm was found.

**Developer instructions:** Define a shared worker-to-API status source, register the route, bound metric memory, expose
all PipelineStatus fields with actual rolling windows, and export per-source outcomes/transitions. Sample the agreed
logical partition key combination every 15 minutes and route capacity alerts to an operational owner.

**Tester instructions:** Positive: actual worker updates become visible through HTTP and exported instruments.
Negative: stopped/unconfigured worker is not zero-throughput healthy. Edge: rolling-window expiry, empty histograms,
timeout, DLQ recovery, multiple replicas and partition sizes immediately below/at/above 16GB.

**Dependencies / future validation:** AUD-001, AUD-025; [pipeline tests][pipeline-test], V01, V05, V07.
**Acceptance:** Required metric names/units/windows and per-source states are asserted, status is reachable, and capacity
warnings precede the documented limit without unbounded process memory.

### AUD-039: Active and Historical Infrastructure Diverge from Required Operational Controls

- [ ] AUD-039 (P2) Align the authoritative IaC entry point with ingestion health, scaling, security and review gates.

GOVERNANCE-BLOCKED (2026-09-16): Non-Bicep evidence, static drift detection, and authoritative IaC path records are updated for spec-006; live Azure policy discovery parity and management-group inheritance validation are UNVERIFIED, so this AUD remains open until governance gate evidence is supplied.

**Affected:** T056, T057, T058, T059; FR-001a, FR-025, FR-030, FR-031.

**Expected vs observed / impact:** [azure.yaml][azd] selects root infrastructure, not the task's older Bicep entry.
The active worker has identity and CPU scaling (2-6 replicas) but no queue-depth rule or platform probes; ingress
was deliberately removed. The older worker uses `STORAGE_ACCOUNT` instead of `STORAGE_ACCOUNT_NAME` and its simulation
container requests 400 autoscale maximum RU rather than the active 1000. Storage encryption/private blob access and
AU primary location are supported in source, but tenant isolation is not a property of broad account RBAC. Raw
resources, baseline tags/shared-key posture and unbounded older location parameter need assessment against repo policy
and explicit approvals, not assumed deployment compliance.

**Developer instructions:** Select and document the authoritative template; preserve valid existing resources and plan
migrations explicitly. Add applicable probes/queue scaling and least-privilege data-plane controls; reconcile Redis
Entra configuration and worker requirements. Obtain checked-in policy/AVM exceptions or compliant module usage before
future IaC edits. Do not change policy to accommodate code or infer an AU exemption for data storage.

**Tester instructions:** Positive: compiled template has correct HPK/containers, AU restriction, identity, runtime
variables, probes and CPU/backlog scaling. Negative: non-AU location, missing policy tags or unauthorised data access
fail validation. Edge: old-template deployment/migration, maximum replicas and a failed worker behind a healthy container.

**Dependencies / future validation:** AUD-004, AUD-024, AUD-042, AUD-043; V06, then separately authorised V07.
**Acceptance:** Active IaC and runbooks agree; compilation, policy review and what-if evidence identify no unexplained
ingestion-resource drift. No cloud compliance or deployment is asserted by this static review.

### AUD-040: Existing Tests Can Pass Without the Promised Behavior

- [x] AUD-040 (P2) Replace tautological and disconnected assertions with production-path contract coverage.

**Affected:** T002, T003, T004, T005, T017, T018, T019, T020, T031, T032, T033, T037, T043, T044, T045, T045b, T051, T053, T055, T063, T064, T065, T076, T077, T078, T078a, T078b, T081, T085.

**Expected vs observed / impact:** [Pipeline tests][pipeline-test] assert `signals_ingested >= 0` and `dedup_hits >= 0`
without wiring storage/schema/audit. [Earthquake test][quake-test] assigns the expected category before asserting it.
[Generator schema tests][flood-schema-test] check selected keys, not JSON Schema. The [misinformation test][monitor-contract]
does not assert absence of a handoff, and storage tests never exercise Cosmos HPK documents. Worker, sensor, binary,
raw-audit reconciliation, original model validation and 24:1/upstream-downstream assertions were not found.

**Developer instructions:** Keep behavioral production fixes in their owning AUD tasks; make dependencies injectable
without replacing the controlling logic. Add schema/version fixtures and test hooks where needed, not alternate
test-only implementations of persistence or orchestration.

**Tester instructions:** Extend the cited existing suites and [scenario model tests][scenario-test]. Positive assertions
must name exact record IDs/values/calls. Negative fixtures must fail the real parser/writer/route. Edge cases come from
each AUD and the scenario/edge tables. Demonstrate that removing persistence, scope enforcement or validation makes
the corresponding tests fail; never mutate actual output to the expected result.

**Dependencies / future validation:** Pair tests with each owning remediation; V01-V06. CI [test selection][ci] must
include applicable simulation/unit suites, not only contract/integration and unrelated benchmarks.
**Acceptance:** Tests exercise real entry points/adapters and exact invariants, with transport/cloud boundaries alone
substituted where appropriate. No claimed contract test is satisfied by key presence or a nonnegative default counter.

### AUD-041: Quantitative Success Criteria Have No Trustworthy End-to-End Evidence

- [x] AUD-041 (P2) Add and record ingestion-specific correctness, load, latency and isolation acceptance measurements.

**Affected:** T020, T064, T078, T085, T086, T087, T088; SC-001, SC-002, SC-003, SC-004, SC-005, SC-006, SC-007, SC-008, SC-009; FR-030, FR-037a; inherited NFR-001.

**Expected vs observed / impact:** Named integration tests contain no 90-second/50,000-per-hour measurements or timed
registry recovery. [Locust ingestion][load] exercises the legacy POST with a noncanonical envelope; dashboard load
hits health, not single-incident aggregation. [Benchmarks][bench-pipeline] exercise agent helpers with fakes, not
source-publication-to-Cosmos ingestion. [Legacy baseline][baseline] explicitly says PLACEHOLDER. No checked-in
006 performance/reconciliation record was located. Static inspection cannot establish any measured success rate.

**Developer instructions:** Instrument publication/receipt/persistence correlation, real deduplicated counts and queried
partition identity; make the harness use repaired production composition and schema-valid fixtures. Keep artificial
waits or mocks out of the measured path while allowing controlled upstream fault injection.

**Tester instructions:** Positive: record 95th-percentile publication latency <=90s, sustained >=50,000 unique signals/hour,
single-incident query p95 <=500ms, validation >=95%, catalogue coverage >=80%, and 100% raw/audit reconciliation.
Negative: inject schema failures, throttling and source/storage outages. Edge: three simultaneous simulations plus live,
surge, multi-jurisdiction fan-out, restoration at worst backoff, and bidirectional zero-contamination queries.

**Dependencies / future validation:** Functional remediations and AUD-040, especially AUD-001, AUD-004, AUD-006, AUD-009,
AUD-018, AUD-024, AUD-025, AUD-030, AUD-031, AUD-038, AUD-039; V07.
**Acceptance:** Attributable checked-in records identify revision, commands, environment, fixtures, run duration,
denominators, raw measurements and thresholds; failures/unrun gates remain explicit. Governance lookup p95 <=50ms
is measured separately, not inferred from the signal container configuration.

### AUD-042: Contract and Authority Drift Requires Explicit Resolution

- [x] AUD-042 (P2) Reconcile conflicting requirements without silently weakening safety or widening scope.

**Affected:** T002, T004, T005, T012, T013, T030a, T056, T059, T061, T062, T075, T085; FR-002a, FR-016, FR-019a, FR-020, FR-024, FR-025, FR-028, FR-029, FR-034, FR-039; ASM-013, ASM-014, SCP-013, SCP-014.

**Expected vs observed / impact:** The spec alternates `simulation_run_id` and `simulationRunId`; [scope helpers][scope]
use `sim-` while FR-025 uses `sim_`; null incident/jurisdiction rules disagree with the schema. Research describes
both `scope=national` and `scope=live`, lightweight references and query-combiner/full-copy strategies. [Current
architecture guidance][partition-doc] says `/tenant_id`, unlike the active HPK. US5 asks for Cosmos audit while FR-028
says Blob JSONL. US1's 60-second acceptance and SC-001's 90-second p95 differ. FR-020 requires governance routing,
but both specs exclude agent refactoring; newer Monitoring uses freshness-adjusted confidence instead of the original
raw 0.8 threshold. Old constitutional principle names no longer match version 1.2.0.

**Developer instructions:** Have the designated architecture/product/security owners publish versioned resolutions
and compatibility/migration decisions. Preserve original IDs and amendment history; retain explicit [spec-008
communication authority][communication-authority] and non-AU deferrals. Do not unilaterally remove freshness protection,
change partition keys, interpret the Foundry carve-out as data-storage permission, or renumber old requirements.

**Tester instructions:** Positive: schema, OpenAPI, model, effective configuration and authoritative docs agree.
Negative: stale aliases/null cases or unsupported API versions fail a compatibility gate. Edge: historical records,
mixed clients, previously declared incidents and differing cadence/backoff limits. Review every affected acceptance
row against the agreed decision, not just textual replacement.

**Dependencies / future validation:** Owner approval before incompatible implementation changes; V05, V06 and document review.
**Acceptance:** Every conflict has a named owner, explicit chosen contract and migration/acceptance consequences;
unresolved decisions remain blockers rather than inferred SUPERSEDED statuses.

### AUD-043: Review, Verification and Amendment Evidence Is Incomplete

- [x] AUD-043 (P2) Replace unsupported completion claims with attributable evidence or explicit unverified/deferred state.

**Affected:** T085; FR-002a, source-document verification obligations, FR-CAP-006-001, FR-CAP-006-002, FR-CAP-006-003;
ASM-011, ASM-012, ASM-014, PER-010, PER-011, PER-012, HYP-004, SCP-012.

**Expected vs observed / impact:** [Quickstart verification][quick] is entirely unchecked while T085 is checked.
[Plan][plan] and [quality checklist][quality] declare PASS without execution records. [Critique][critique] claims
roughly 91 agent executions but is a general catalogue critique, not transcripts or current 006 sign-off. The named
HYP-HYP-004 evidence artifact is absent after NS-06; the [portfolio baseline][rubric-baseline] is not a per-spec
before/after assessment. [Risk treatment][risk-record] names a future schema/test treatment, not proof it exists.
Provider access, source documentation verification and deferred country prerequisites remain unverified.

**Developer instructions:** Preserve historic evidence and checkboxes in their original files until separately
authorised correction. Add attributable source-contract review records, architectural/schema review decisions and
an evidence manifest; mark unperformed validation plainly. Maintain PH/JP/BD prerequisite owners without implementing
those deferred feeds. A HYP-004 evidence file is a **proposed artifact**, not existing evidence.

**Tester instructions:** Positive: trace each claimed review/run to revision, method, actor/date and immutable artifact.
Negative: reject placeholders, prose-only PASS, generic portfolio scores and unrelated CI runs as closure. Edge:
later source API changes, expired approvals and a missing per-spec comparator. Document unresolved gates rather than
execute historical commands or manufacture approval records.

**Dependencies / future validation:** None to correct the evidence classification; actual closure depends on the
relevant future functional/measurement gates and authorised human reviews.
**Acceptance:** Every completion/consultation/provider/HYP claim is either backed by attributable checked-in evidence
or explicitly UNVERIFIED/DEFERRED; no retrospective success or approval is fabricated.

### AUD-044: Signal Query Validation and Result Limits Are Inconsistent

- [x] AUD-044 (P2) Enforce typed query constraints and actual result limits consistently across API and storage backends.

**Affected:** T012, T020, T062; FR-025, FR-030; SC-004; API-02.

**Expected vs observed / impact:** The [OpenAPI contract][openapi] limits signal queries to 1000 results and declares
date-time/validation-status types. [GET /signals][get] accepts unbounded limits and arbitrary status strings, silently
ignores malformed `since`, and can compare timezone-naive query dates with aware stored dates, raising TypeError.
The [Cosmos query branch][repo-query] passes `max_item_count=limit` but exhausts the entire asynchronous result
iterator; that SDK setting limits a page, not the total result. Memory and Cosmos therefore disagree on bounded
results, and clients can receive an unexpectedly broad, expensive query instead of a validation error.

**Developer instructions:** Own parameter validation in the public route and bounded pagination in the repositories.
Use typed status/date inputs with explicit UTC policy, enforce the documented maximum, and agree lower limit/offset
bounds with compatibility owners. Return a controlled client error for invalid values. Stop after the requested
number of results or expose an agreed continuation contract; do not mistake SDK page size for a total cap.

**Tester instructions:** Extend [live API tests][live-api-test] and [storage tests][storage-test]. Positive: valid
source/category/time/status combinations and paginated subsets return exact ordered IDs. Negative: malformed dates,
unknown status and limits above 1000 fail deterministically. Edge: naive/offset timestamps, equal-time records,
negative/zero bounds under the agreed policy, empty results and a fake/emulated Cosmos iterator with multiple pages.

**Dependencies / future validation:** AUD-003, AUD-004, AUD-042; V02, V05, V07.
**Acceptance:** Both backends return no more than the accepted requested limit, every filter is applied as documented,
and invalid input cannot silently widen a query or produce an unhandled server error.

## Task Coverage

Each row corresponds to exactly one original checkbox. All 94 original tasks are checked; statuses below describe
the inspected implementation, not the checkbox. A test-artifact task is PARTIAL when its assertion body does not
prove the specified contract, even if the file exists. Pure artifact creation can be IMPLEMENTED while its runtime
integration and missing tests remain follow-ups. All follow-up IDs denote unchecked tasks above.

| Original task | Original checkbox | Status | Implementation and assertion-body evidence | Follow-up |
| --- | --- | --- | --- | --- |
| T001 | [x] | IMPLEMENTED | Worker/pipeline/normaliser/simulation/generator package structure exists; [worker][worker] and [runner][sim-runner] implement named surfaces. Directory creation has no behavioral assertion requirement. | AUD-001, AUD-024 |
| T002 | [x] | IMPLEMENTED | [SignalEnvelope schema][schema] declares optional provenance `simulationRunId`; no with/without-marker JSON Schema regression assertions found in NS-02. | AUD-007, AUD-040, AUD-043 |
| T003 | [x] | IMPLEMENTED | [IngestionAuditEntry][audit-model] has every named field and success/rejected validators. No model validation assertion body located; audit integration is defective. | AUD-006, AUD-040 |
| T004 | [x] | PARTIAL | [Scenario model][scenario-model] has fields but lacks Polygon/catalogue-ID validation; [later scenario tests][scenario-test] validate a different ScenarioTemplate. | AUD-036, AUD-040 |
| T005 | [x] | IMPLEMENTED | [Domain run model][run-model] implements transition/timestamp checks and required fields. [Runner tests][sim-test] exercise another dataclass, not these rules. | AUD-036, AUD-037, AUD-040 |
| T006 | [x] | IMPLEMENTED | [Config model][config-model] declares named fields, constraints, and effective TTL; [factory][factory] does not apply most values. No config assertion body located. | AUD-023, AUD-040 |
| T007 | [x] | IMPLEMENTED | [Ingestion package metadata][ingestion-project] declares lxml, httpx and jsonschema. Installation/build/import success was not tested. | AUD-039 |
| T008 | [x] | PARTIAL | [Base lifecycle][pipeline-loop] and [processing][pipeline] exist; optional persistence/schema, no DLQ/event/registry integration. [Lifecycle assertions][pipeline-test] only require a nonnegative counter. | AUD-001, AUD-007, AUD-012, AUD-018, AUD-025, AUD-038 |
| T009 | [x] | PARTIAL | [Dedup][dedup] offers Redis calls/canonical helpers; no atomicity/local expiry/scoped identity. [Tests][dedup-test] assert local membership, not TTL/Redis behavior. | AUD-008, AUD-009 |
| T010 | [x] | PARTIAL | [Association][assoc] uses same-jurisdiction OR state bbox; [base][pipeline] selects only first match. [Tests][association-test] use no incident footprint. | AUD-016 |
| T011 | [x] | PARTIAL | [Registry][normal-registry] dispatches registered callables and rejects an unknown key; [factory][factory] never registers/uses it. No direct registry assertions located. | AUD-023 |
| T012 | [x] | PARTIAL | [Shared repository][repo] has CRUD/query helpers; HPK serialization, simulation queries and fan-out do not satisfy storage guarantees. [Tests][storage-test] instantiate no Cosmos client. | AUD-004, AUD-005, AUD-016 |
| T013 | [x] | CONFLICT | [Scope helpers][scope] exist but use `sim-` rather than the specified `sim_` and are not used by the 006 save path. | AUD-005, AUD-042 |
| T014 | [x] | PARTIAL | [Blob helper][blob] has specified path helpers; production uses [different archival][blobactual] and no simulation/binary caller. No raw-byte/path assertions located. | AUD-026, AUD-027 |
| T015 | [x] | PARTIAL | [Writer][audit] makes JSONL but [upload][blobupload] overwrites hourly contents. No append/reconciliation assertions located. | AUD-006 |
| T016 | [x] | PARTIAL | [Worker][worker] starts/stops tasks; configuration wiring, health and draining are incomplete. No real worker/factory assertion bodies located. | AUD-001, AUD-023, AUD-024 |
| T017 | [x] | IMPLEMENTED | [Breaker tests][breaker-test] explicitly assert closed/open/half-open/success/failure transitions; deadlines are manipulated and registry/SLO behavior is not tested. | AUD-025 |
| T018 | [x] | PARTIAL | [Dedup tests][dedup-test] assert canonical keys/hash/membership; no Redis TTL expiry or contention assertions. | AUD-009, AUD-040 |
| T019 | [x] | PARTIAL | [Association tests][association-test] assert null/closed/multiple same-state matches; no actual footprint, true national polygon or persisted fan-out assertion. | AUD-016, AUD-040 |
| T020 | [x] | PARTIAL | [Storage tests][storage-test] inspect dictionaries and incident queries, not real HPK values or p95 dashboard queries. | AUD-004, AUD-005, AUD-040, AUD-041 |
| T021 | [x] | PARTIAL | [BoM normaliser][bom] parses simplified XML; namespaced leaf/XSD/time/area behavior is incomplete. [BoM tests][bom-test] use unnamespaced samples. | AUD-010, AUD-011, AUD-020 |
| T022 | [x] | PARTIAL | [CAP parser][cap] exists but drops namespaced leaf values, ignores certainty in scoring and is not wired; no CAP test caller found. | AUD-011, AUD-040 |
| T023 | [x] | PARTIAL | [GeoJSON][geo] has collection/feature conversion; format/time/geometry/quality assumptions remain. [Tests][geo-test] cover selected fields, not all native representations. | AUD-010, AUD-020, AUD-022 |
| T024 | [x] | PARTIAL | [Observation normaliser][obs] has numeric range checks but no finite/missing-data/native-time/threshold contract. No direct observation assertion body found. | AUD-010, AUD-018, AUD-019 |
| T025 | [x] | PARTIAL | [Binary metadata][binary-meta] builds a metadata envelope; timestamps/coverage/format and full-ingestion switch are not proven or connected. | AUD-010, AUD-027 |
| T026 | [x] | PARTIAL | [BoM FTP poller][bom-warn] fetches XML at class-default 60s, but permanently caches filenames and omits durable pipeline dependencies. [Integration][pipeline-test] mocks the pipeline, not FTP. | AUD-001, AUD-008, AUD-011, AUD-023 |
| T027 | [x] | PARTIAL | [BoM observations][bom-obs] polls one representative station, not XML summaries plus 30-minute individual-station mode. No native observation tests. | AUD-010, AUD-018, AUD-021, AUD-022 |
| T028 | [x] | PARTIAL | [Radar][radar] lists metadata at 300s; filename timestamps and missing incident-triggered download violate task. No satellite/radar integration assertions. | AUD-008, AUD-010, AUD-027 |
| T029 | [x] | CONFLICT | [Earthquake adapter][quake] uses USGS but labels GA, truncates before geographic filtering and copies native update time. [GeoJSON test][geo-test] changes the category itself. | AUD-010, AUD-021, AUD-022, AUD-040 |
| T030 | [x] | PARTIAL | [Hotspot adapter][hotspots] fetches GeoJSON at class-default 900s; truncates first 50 and uses generic timestamp/confidence mapping. No adapter assertions located. | AUD-010, AUD-020, AUD-022, AUD-023 |
| T030a | [x] | CONFLICT | [BomRssPipeline][rss] explicitly replaces RSS with another FTP scan; no RSS/Atom notification-to-product fetch remains. No approved local requirement amendment or assertion. | AUD-008, AUD-011, AUD-021, AUD-042 |
| T030b | [x] | PARTIAL | [Tsunami subclass][tsunami] sets 30s but scans all XML and inherits non-CAP normalization/filename cache. No tsunami adapter assertion. | AUD-008, AUD-011, AUD-023 |
| T031 | [x] | PARTIAL | [BoM assertions][bom-test] check category, kind, score, issue time, ID, location and malformed XML; they do not validate the output against schema or real namespaced products. | AUD-011, AUD-040 |
| T032 | [x] | PARTIAL | [Earthquake assertion][quake-test] sets category to geohazard before checking it; Point coordinates are checked, not real adapter semantics/first-pass schema. | AUD-010, AUD-021, AUD-040 |
| T033 | [x] | PARTIAL | [MockPipeline test][pipeline-test] does not wire schema/blob/repository/audit or mocked FTP; `>= 0` cannot establish the described lifecycle. | AUD-001, AUD-007, AUD-040 |
| T034 | [x] | PARTIAL | [Fire adapter][fire] lists eight state configs and property maps but only NSW/VIC are enabled and five states are absent from factory/config. [Structural tests][geo-test] cover NSW/VIC helpers only. | AUD-020, AUD-021, AUD-022, AUD-023 |
| T035 | [x] | PARTIAL | [SES adapter][ses] has three state maps; NSW is disabled and VIC/QLD have no configured instances. JSON/RSS/schema variants and native fixture assertions are absent. | AUD-021, AUD-022, AUD-023 |
| T036 | [x] | IMPLEMENTED | [NSW GeoJSON tests][geo-test] assert fire category, 0.85 confidence, source ID and exact Point geometry; Polygon type is checked. Full pipeline/native-format risk remains. | AUD-020, AUD-040 |
| T037 | [x] | PARTIAL | [NSW/VIC structural assertion][geo-uniform-test] compares top-level/source key sets only, not mapped content/types/values or schema validation. | AUD-020, AUD-040 |
| T038 | [x] | PARTIAL | [AWS adapter][aws] calls [range helper][obs], but native dates, missing jurisdiction and incomplete validation persist. No sensor contract assertion body located. | AUD-010, AUD-018, AUD-019 |
| T039 | [x] | PARTIAL | [Gauge adapter][river] retrieves `value`/quality but never maps thresholds, flow or real coordinates; normaliser receives unrecognized measurement names. | AUD-019, AUD-022, AUD-025 |
| T040 | [x] | PARTIAL | [EPA adapter][epa] defaults to site details and only one state instance; no PM/ozone/AQI mapping assertion. | AUD-019, AUD-021, AUD-022 |
| T041 | [x] | PARTIAL | [Sentinel adapter][sentinel] uses a SciHub-shaped search/JP2 metadata, while config points to Data Space and is disabled; no binary download or fixture assertion. | AUD-021, AUD-027 |
| T042 | [x] | PARTIAL | [Himawari][himawari] lists IDE files with filename timestamps and PNG label, never downloads. No JPG/GeoTIFF/integrity assertion. | AUD-008, AUD-010, AUD-027 |
| T043 | [x] | MISSING | NS-02 found no valid-AWS/freshness assertion; [named BoM test][bom-test] contains XML cases only. | AUD-018, AUD-019, AUD-040 |
| T044 | [x] | MISSING | NS-02 found no 150-degree observation/rejection assertion in [BoM tests][bom-test] or relocated ingestion tests. | AUD-019, AUD-040 |
| T045 | [x] | MISSING | [Integration file][pipeline-test] has no satellite mode test; no relocated adapter/binary-download assertion found. | AUD-027, AUD-040 |
| T045a | [x] | MISSING | NS-01 found [binary path storage helper][binary-store] but no reachable on-demand fetch/update service. Proposed service path is named in AUD-027. | AUD-027 |
| T045b | [x] | MISSING | [Storage tests][storage-test] contain repository-only assertions, no on-demand download/blob/URI update assertions; NS-02 found no replacement. | AUD-027, AUD-040 |
| T046 | [x] | PARTIAL | [Detector][misinfo] exists but is disconnected and differs on distinct-account/window/cosine semantics; [unit-style tests][misinfo-test] exercise helpers only. | AUD-013, AUD-014 |
| T047 | [x] | PARTIAL | [Twitter normalisation][twitter] and keywords exist, but polling returns empty; no stream/rate-limit transport test. | AUD-020, AUD-028 |
| T048 | [x] | PARTIAL | [Facebook][facebook] returns empty from polling; hard-coded normalisation does not establish Graph API access/budget. | AUD-020, AUD-028 |
| T049 | [x] | PARTIAL | [Reddit][reddit] has subreddit constants but an empty poller and no active/idle cadence or rate-limit logic/assertions. | AUD-028 |
| T050 | [x] | PARTIAL | [Snap][snap] has report/geotag conversion but empty polling and no infrastructure-road-closure category; no transport fixture assertions. | AUD-020, AUD-028 |
| T051 | [x] | PARTIAL | [Burst test][misinfo-test] asserts at least 20 flagged indices, not distinct-account handling or stored `validationStatus=escalated`. | AUD-013, AUD-014, AUD-040 |
| T052 | [x] | IMPLEMENTED | [Contradiction test][contradiction-test] calls `detect` and asserts reduced confidence and reason; corroborated helper case asserts false contradiction. No live integration implied. | AUD-013, AUD-014 |
| T053 | [x] | PARTIAL | [Duplicate test][duplicate-test] asserts some indices and index zero retained; does not assert cosine, chronological earliest or escalated stored status. | AUD-014, AUD-040 |
| T054 | [x] | PARTIAL | [Monitoring LLM][monitor-llm] and [later fail-closed stage][monitor-pipe] exist, but persistent final status/rationale and all-entry-point guards are absent. | AUD-012, AUD-013, AUD-015 |
| T055 | [x] | PARTIAL | [Classifier test][monitor-contract] asserts `misinformation` but discards handoff return and never reads final stored status. | AUD-015, AUD-040 |
| T056 | [x] | CONFLICT | [Active HPK/index][activeinfra] and [older template][legacyinfra] exist; writer property names and authoritative partition documentation disagree. No Cosmos-key integration assertion. | AUD-004, AUD-039, AUD-042 |
| T057 | [x] | IMPLEMENTED | [Active simulation container][active-sim] has `/scenario_id` and 1000 autoscale max; older template's 400 setting remains divergent. No deployment execution established. | AUD-039 |
| T058 | [x] | IMPLEMENTED | [Active blob containers][activeblobs] declare all four named containers with no public blob access. Raw/audit usage and immutability are separate defects. | AUD-006, AUD-026, AUD-039 |
| T059 | [x] | PARTIAL | [Active worker IaC][activeworker] has identity and 2-6 CPU scaling, but no queue-depth scaling/probes and no ingress; older template differs. | AUD-024, AUD-039 |
| T060 | [x] | PARTIAL | [Shared fan-out helper][repo-fanout] exists, but no automatic geographic-coverage caller; [API repository][api-repo] lacks that behavior. [Fan-out test][fanout-test] is memory-only. | AUD-004, AUD-016 |
| T061 | [x] | PARTIAL | [Retrospective helper][monitor-retro] has lookback but incompatible keyword and no geographic/declaration binding; [Cosmos update][repo-update] is no-op. | AUD-017 |
| T062 | [x] | PARTIAL | [GET filters][get] include all names but lack scope/bounds/enums; malformed `since` is ignored and timezone-naive comparisons can fail. No filter contract assertions located. | AUD-003, AUD-004, AUD-040, AUD-042, AUD-044 |
| T063 | [x] | PARTIAL | [Jurisdiction test][jurisdiction-test] asserts NSW excludes VIC in memory but discards VIC results and never checks Cosmos/agency scope. | AUD-003, AUD-004, AUD-040 |
| T064 | [x] | MISSING | [Storage tests][storage-test] never create a raw blob or audit writer; NS-02 found no per-signal raw/audit reconciliation assertion. | AUD-006, AUD-026, AUD-040, AUD-041 |
| T065 | [x] | PARTIAL | [Simulation scope test][storage-sim-test] checks only live incident results in memory with explicitly supplied scope; reverse and jurisdiction/unassociated paths are unasserted. | AUD-005, AUD-030, AUD-040 |
| T066 | [x] | PARTIAL | [Runner][sim-runner] loops phases and tags envelopes, but bypasses pipeline/model, swallows generator failures and shares run buffers. [Tests][sim-test] use permissive list storage. | AUD-030, AUD-032, AUD-036, AUD-037 |
| T067 | [x] | PARTIAL | [Four templates][templates] exist with phase names/IDs, but omit source steps and are not registered for real generation. [Storm tests][storm-test] assert static lists. | AUD-031, AUD-032 |
| T068 | [x] | PARTIAL | [Flood model][flood] generates a curve; [tests][flood-test] assert rough shape and threshold crossing, not calibrated rise/peak/recession inputs or runtime gauge topology. | AUD-033 |
| T069 | [x] | PARTIAL | [Fire generator][fire-gen] computes an FFDI scalar; [tests][fire-test] check directional sensitivity, not fuel-load/perimeter spread. | AUD-033 |
| T070 | [x] | PARTIAL | [Cyclone generator][cyclone] makes a moving track; [tests][cyclone-test] check count/movement/valid bounds, not pressure/radius calibration. | AUD-033 |
| T071 | [x] | PARTIAL | [Weather generator][weather] chooses envelope title/category by parameter, not native BoM payload; runner does not consistently bind scenario type. [Storm tests][storm-test] call helper directly. | AUD-031, AUD-033 |
| T072 | [x] | PARTIAL | [Sensor generator][sensor-gen] clamps random values but emits generic AWS-shaped envelopes for all types; no direct sensor assertion body found. | AUD-031, AUD-033, AUD-040 |
| T073 | [x] | PARTIAL | [Social generator][social-gen] creates three classes, but ignores requested misinformation ratio and scenario geography; no ratio assertions found. | AUD-034 |
| T074 | [x] | PARTIAL | [Overlay helper][overlay] loads/transforms JSON but is uncalled, adds forbidden provenance and does not handle nested geometry. No overlay assertion found. | AUD-035, AUD-037 |
| T075 | [x] | CONFLICT | [Actual simulation API][sim-api] is tenant-based; [006 OpenAPI][openapi] scenario/run paths are not implemented. [Contract tests][sim-api-test] manually compose later-model responses. | AUD-036, AUD-042 |
| T076 | [x] | PARTIAL | [Flood schema test][flood-schema-test], [fire][fire-test], [cyclone][cyclone-test], [storm][storm-test] check keys/selected values, never the canonical JSON Schema/live normalisers. | AUD-031, AUD-040 |
| T077 | [x] | PARTIAL | [Runner integration][sim-test] asserts two generated envelopes; [hydrograph assertions][flood-test] are separate helper tests, not runtime crossings. | AUD-032, AUD-033, AUD-040 |
| T078 | [x] | MISSING | [Isolation-named runner test][sim-tag-test] checks tags only; no live+three-run storage/throughput assertion. Later [warp tests][warp-test] cover scheduling, not this combined requirement. | AUD-005, AUD-030, AUD-040, AUD-041 |
| T078a | [x] | PARTIAL | Original [runner tests][sim-test] set compression to 1000 without asserting cadence; later [warp tests][warp-test] check 10x/1x delays, not 24:1 source generation. | AUD-032, AUD-040 |
| T078b | [x] | MISSING | [Flood tests][flood-test] have no upstream/downstream gauge comparison; NS-04 inspected the later gauge feed, also without topology. | AUD-033, AUD-040 |
| T079 | [x] | PARTIAL | [IMS adapter][ims] polls both placeholder endpoints without auth, swallows failures and incompletely maps fields/source metadata. No provider/field contract assertions located. | AUD-023, AUD-025, AUD-029 |
| T080 | [x] | PARTIAL | [Field route selection][post] accepts field_report but calls unchanged [legacy ingestion][manualservice]; no pipeline, officer identity or tier enforcement. | AUD-002, AUD-003, AUD-020 |
| T081 | [x] | MISSING | [Existing API test][live-api-test] submits authoritative weather only; NS-02 found no POST field-report officer/kind/tier assertion. | AUD-002, AUD-029, AUD-040 |
| T082 | [x] | PARTIAL | [Status handler][status] exists but is unmounted and unpopulated, with lifetime totals and incomplete schema. No HTTP status assertions located. | AUD-038 |
| T083 | [x] | MISSING | [Authoritative service][manualservice] and IoT/community delegation remain legacy dictionary writes; no refactoring into IngestionPipelineBase is present. | AUD-002 |
| T084 | [x] | PARTIAL | [24 static configs][configs] include ten disabled entries; effective class settings differ, required state sources are unregistered, no validated external loader is wired. | AUD-021, AUD-023 |
| T085 | [x] | UNVERIFIED | [Quickstart][quick] has eleven unchecked verification boxes; [plan PASS claims][plan] and old general rehearsal tests are not A-I execution records. | AUD-040, AUD-041, AUD-043 |
| T086 | [x] | MISSING | [Named integration file][pipeline-test] has no publication-to-Cosmos <=90s assertion; [latency benchmarks][bench-latency] measure handoff retry instead. | AUD-041 |
| T087 | [x] | MISSING | No 50,000 unique signals/hour integration assertion found; [load script][load] targets the legacy API without durable/dedup measurement. | AUD-024, AUD-041 |
| T088 | [x] | MISSING | [Breaker unit][breaker-test] and [mock pipeline][pipeline-test] assert local state only; no timed degraded-registry/recovery integration was located. | AUD-025, AUD-041 |

## Requirement Coverage

The 61 local items comprise 49 functional requirements including letter-suffixed additions, three explicitly
deferred capstone FRs, and nine SCs. There is no local standalone NFR section. The explicit inherited NFR-001 is
recorded separately. Subclauses are covered in each row and the source/product, acceptance, edge and obligation
tables; none of the deferred countries is incorrectly classified as a missing currently required implementation.

| Requirement | Status | Required behavior, implementation and test-body assessment | Follow-up |
| --- | --- | --- | --- |
| FR-001 | PARTIAL | Classes exist for source families, but [worker composition][worker-wiring], [API delegation][manualservice] and empty [social polling][twitter] do not implement a common live path. [Mock integration][pipeline-test] is insufficient. | AUD-001, AUD-002, AUD-021, AUD-028, AUD-029 |
| FR-001a | PARTIAL | [Worker][worker] runs async tasks and [active IaC][activeworker] declares CPU scaling; independent progress, lifecycle, readiness/liveness and backlog scaling are incomplete. No worker assertions found. | AUD-023, AUD-024, AUD-039 |
| FR-002 | PARTIAL | [Normalisers][bom] produce selected envelope fields, but timestamp/null/source/geometry/enum semantics diverge. [BoM][bom-test] and [GeoJSON tests][geo-test] assert partial shapes, not universal canonical validity. | AUD-007, AUD-010, AUD-011, AUD-019, AUD-020 |
| FR-002a | PARTIAL | [Schema][schema] includes optional `simulationRunId`; live/marker consistency and backward-compatibility test bodies are absent, and claimed planning consultation is UNVERIFIED. | AUD-007, AUD-040, AUD-043 |
| FR-003 | MISSING | [Base validation][schema-validation] is optional and has no durable DLQ; [API validator][validator] is a weaker Pydantic shape. No actual schema-to-DLQ ingestion assertion found. | AUD-007 |
| FR-004 | PARTIAL | Warnings/forecast/observations/radar/flood/RSS subproducts are mapped in the product table; [warnings][bom-warn] and [observations][bom-obs] omit required cadence/format paths, RSS was replaced, imagery is metadata-only. [Tests][bom-test] cover simplified XML. | AUD-008, AUD-010, AUD-011, AUD-021, AUD-023, AUD-027 |
| FR-005 | CONFLICT | [Earthquake source][quake] is USGS mislabelled GA; [tsunami][tsunami] is not CAP-dispatched; [hotspots][hotspots] truncate/generic-map. [Earthquake test][geo-test] overwrites expected output. | AUD-008, AUD-010, AUD-011, AUD-021, AUD-022 |
| FR-006 | PARTIAL | [Eight fire state maps][fire] exist but only two enabled; JSON-only assumptions and slice limits remain. [NSW/VIC helper assertions][geo-uniform-test] do not establish all eight feeds. | AUD-020, AUD-021, AUD-022 |
| FR-007 | PARTIAL | [SES adapter][ses] has three mappings but no enabled required instance; JSON/GeoJSON/native flood/evacuation semantics lack fixture assertions. | AUD-021, AUD-022 |
| FR-008 | PARTIAL | [AWS][aws], [gauge][river], [EPA][epa] transports exist but full field/unit/range/threshold/station coverage is missing. No direct valid/invalid sensor assertion bodies found. | AUD-010, AUD-018, AUD-019 |
| FR-009 | PARTIAL | [Sentinel][sentinel] and [Himawari][himawari] list mismatched format/coverage metadata, with no full imagery retrieval. No binary integration assertions found. | AUD-010, AUD-021, AUD-027 |
| FR-009a | MISSING | Metadata creation exists, but [binary helper][binary-store] has no incident/buffer/simulation/on-demand caller; default/full/expiry/corruption modes are not implemented or asserted. | AUD-027 |
| FR-010 | MISSING | X streaming/keywords/accounts/reconnect, Facebook polling/budget and Reddit active/idle/throttling are absent from [empty pollers][twitter]. Normalisers alone do not implement APIs. | AUD-028 |
| FR-010a | PARTIAL | [Tier-1 helper][misinfo] is disconnected and semantically different; [Tier-2 stage][monitor-pipe] holds some failures but does not persist rejection and is bypassable. [Tests][misinfo-test] and [classification assertions][monitor-contract] omit end-to-end decisions. | AUD-013, AUD-014, AUD-015 |
| FR-011 | PARTIAL | [Snap conversion][snap] and generic manual API exist; no partner polling/road-closure mapping/trusted volunteer classification. No live community transport/identity assertions. | AUD-002, AUD-020, AUD-028 |
| FR-012 | PARTIAL | [Manual API][post] and [IMS][ims] exist, but authenticated officer provenance, full ICON/WebEOC mapping, configured auth/endpoints and processing pipeline are incomplete. | AUD-002, AUD-020, AUD-029 |
| FR-013 | PARTIAL | [Tier constants][enrich] and [alert-level mapping][geo] exist, but registry/quality factors and gauge threshold elevation are absent. [BoM score test][bom-test] proves a constant only. | AUD-019, AUD-020 |
| FR-014 | PARTIAL | [Fallback freshness][freshness] exists but adapters supply constants and future time is accepted as fresh; no cadence-boundary source test found. | AUD-018 |
| FR-015 | PARTIAL | [Normalisers][obs] preserve some metadata and [enrichment][enrich] adds collector; source timestamps, identity and registry-method parity are incomplete. Existing [BoM assertions][bom-test] cover one XML fixture. | AUD-010, AUD-020 |
| FR-016 | PARTIAL | [Breaker][breaker] changes local state but does not update registry and cannot meet all timing bounds; [tests][breaker-test] test only helper transitions. | AUD-025, AUD-042 |
| FR-017 | PARTIAL | [Production raw archive][blobactual] stores transformed JSON, not original bytes, and failures may archive nothing. No raw fidelity/reconciliation assertions found. | AUD-007, AUD-026 |
| FR-018 | PARTIAL | [Generated UUID][pipeline] reaches transient telemetry/optional audit but not stored signal or [handoff contract][handoffs]; newer workflow creates its own correlation. | AUD-012, AUD-020 |
| FR-018a | PARTIAL | [Dedup][dedup] provides lookups but not atomic scoped durable uniqueness/TTL; [BoM filename tracking][bom-warn] suppresses changed products. [Tests][dedup-test] are helper-only. | AUD-008, AUD-009 |
| FR-018b | PARTIAL | OTel counters/histograms exist, but [metrics/status][metrics] lack required windows, per-source transitions, timeout/DLQ/partition gauges and reachable status. No metric-contract assertions found. | AUD-025, AUD-038 |
| FR-019 | MISSING | [Worker/base][pipeline] emit no event to Monitoring; [new synthetic dispatcher][sim-dispatch] serves a different synthetic path. Direct [Monitoring tests][monitor-test] do not prove first-stage live consumption. | AUD-012 |
| FR-019a | PARTIAL | [Matching][assoc] is jurisdiction OR bbox, [first-match call][assoc-first] drops other incidents, null schema conflicts remain. [Tests][association-test] do not use real footprints/persisted copies. | AUD-007, AUD-016 |
| FR-019b | PARTIAL | [Retrospective helper][monitor-retro] has default lookback but incompatible repository call/no Cosmos mutation/no declaration trigger or geometry. Existing [update test][storage-update-test] checks a dictionary only. | AUD-017 |
| FR-020 | CONFLICT | [Monitoring][monitor] is hard-coded and freshness-adjusted; [governance lookup][governance] exists separately, with no agent caller. Both specs exclude runtime refactoring despite the MUST; [threshold tests][monitor-contract] encode the newer rule. | AUD-012, AUD-015, AUD-042 |
| FR-021 | PARTIAL | [Risk retrieval][risk-retrieve] has a stored-data branch but wrong signal PK/no related-query contract; no-ID/no-store fallback manufactures inputs. [Risk test][risk-test] accepts payload-based processing, not stored fidelity. | AUD-004, AUD-012 |
| FR-022 | PARTIAL | [Evacuation retrieval][evac-retrieve] consumes stored assessments and supports supplied road/population data; transport-ingestion linkage is absent. [Risk handoff tests][risk-handoff-test] assert IDs, not full feed-to-route flow. | AUD-012, AUD-021 |
| FR-023 | PARTIAL | [Resource retrieval][res-retrieve] uses assessment/summary payloads and inventory abstractions, not a traced stored coordination-task request from ingestion. [Demand tests][resource-test] exercise summary-derived demand. No direct raw ingestion found. | AUD-012 |
| FR-024 | SUPERSEDED | Contract pointer retained; [008 FR-CAP-008-004][communication-authority] explicitly supersedes warning-tier authoring/delivery. [Stored communication retrieval][comm-retrieve] and [handoff references][risk-handoff-test] were inspected; public delivery is not certified here. | AUD-012, AUD-042 |
| FR-025 | PARTIAL | [HPK IaC][activeinfra] exists but [serialization/fan-out][repo] and API/state isolation conflict. Query-by-source/category/time and national references are not complete; latency/deployed region remain unverified. | AUD-003, AUD-004, AUD-005, AUD-016, AUD-039, AUD-041, AUD-044 |
| FR-026 | PARTIAL | [Helper path][blob] matches, but [actual worker archive][blobactual] uses slash dates/transformed JSON and no per-signal reference. AU primary is source-configured, not deployed-state proof. | AUD-026, AUD-039 |
| FR-027 | MISSING | [Binary storage helper][binary-store] defines incident/_on-demand paths but no fetch/store/update caller exists in the required pipeline. No corresponding assertions found. | AUD-027 |
| FR-028 | PARTIAL | [Audit JSONL writer][audit] exists but overwrites hourly files, omits validation status and is unwired in production. No immutable append/reconciliation tests found. | AUD-006 |
| FR-029 | PARTIAL | [Scope helper][scope], repository scope arguments and [tag tests][sim-tag-test] exist; default live writes, unscoped dictionary queries and raw prefixes violate isolation. | AUD-003, AUD-005, AUD-026, AUD-030 |
| FR-030 | UNVERIFIED | [Signal container/index][activeinfra] and [governance lookup timing log][governance] are authored; no measured dashboard p95 <=500ms or lookup p95 <=50ms record. | AUD-004, AUD-039, AUD-041 |
| FR-031 | PARTIAL | Active root restricts AU primary and provisions private blob access/TLS/managed identities; [routes][get] and [repository][repo] do not enforce agency/tenant boundaries. External policy/deployed encryption/access checks were not run. | AUD-003, AUD-004, AUD-039 |
| FR-032 | PARTIAL | [Catalogue][catalogue] has 46 sources; [templates][templates] activate fixed small lists with no relevance/coverage mapping or production registrations. [Later 13-shape tests][feed-test] are not that denominator. | AUD-030, AUD-031 |
| FR-033 | PARTIAL | [Flood][flood], [fire][fire-gen], [cyclone][cyclone] and [sensor][sensor-gen] helpers exist, but native source-format parity and required calibrated parameters are absent. [Model tests][flood-test] assert limited qualitative behavior. | AUD-031, AUD-033 |
| FR-033a | PARTIAL | [Overlay helper][overlay] exists but is disconnected, schema-incompatible and Point-only. No actual historical-overlay test found; later replay ignores requested bounds. | AUD-035, AUD-037 |
| FR-034 | PARTIAL | [Runner sleeps][sim-phase] compress phases but not recurring source cadences. [Later warp tests][warp-test] provide partial clock evidence, not 006 generation/24:1 proof. | AUD-032 |
| FR-035 | MISSING | [Generators][social-gen] do not enforce scenario Polygon/topology; [flood][flood] has no upstream/downstream ordering and fire lacks directional perimeter. Later gauge feed does not close this. | AUD-033, AUD-034 |
| FR-036 | PARTIAL | [Social batches][social-gen] implement default counts, but per-run misinfo argument is ignored and no ratio assertion exists. | AUD-034 |
| FR-037 | MISSING | [Runner saves envelopes directly][sim-save]; it never submits native products to the live worker's normalisation/validation/handoff chain. [Fake-repository test][sim-test] cannot establish parity. | AUD-030 |
| FR-037a | PARTIAL | Later synthetic storage/dispatch separates a different model; original [runner][sim-runner], [repositories][repo-query] and worker do not implement shared-worker, three-run/live isolation and throughput. | AUD-005, AUD-012, AUD-024, AUD-030, AUD-041 |
| FR-038 | PARTIAL | [Four templates][templates] define some progression, but required transport/evacuation/emergency-service chains and true model wiring are incomplete. [Storm assertions][storm-test] check only the current shorter lists. | AUD-031, AUD-032, AUD-033 |
| FR-039 | PARTIAL | [Domain model][run-model], [later API][sim-api] and [warp recorder][warp] contain pieces; original runner lacks durable full parameters and linked replay, and [replay service][seed-replay] ignores bounds. | AUD-032, AUD-034, AUD-036, AUD-037 |
| SC-001 | UNVERIFIED | Required 95% publication-to-Cosmos <=90s outcome has no checked-in measurement. [Mock integration][pipeline-test] lacks timestamps/SLO assertion and real persistence. | AUD-001, AUD-008, AUD-010, AUD-024, AUD-041 |
| SC-002 | UNVERIFIED | No sustained 50,000 unique signals/hour evidence; [Locust][load] uses legacy acknowledgements, not deduplicated durable counts. | AUD-009, AUD-024, AUD-041 |
| SC-003 | UNVERIFIED | No first-attempt validation denominator or 95% rate measurement; [optional validation][schema-validation] and absent DLQ contradict prerequisites. | AUD-007, AUD-040, AUD-041 |
| SC-004 | UNVERIFIED | [Storage tests][storage-test] do not time actual incident aggregation; [dashboard][dashboard] is dictionary/seed-based, not the required Cosmos signal query. | AUD-004, AUD-041, AUD-044 |
| SC-005 | UNVERIFIED | No relevant-source denominator or >=80% emitted-ID manifest per scenario; [templates][templates] alone cannot establish coverage. | AUD-031, AUD-041 |
| SC-006 | PARTIAL | [Scenario tests][flood-schema-test] assert keys, not canonical validation/native cadence/ranges. Direct-envelope simulation bypasses the required common path. | AUD-030, AUD-031, AUD-032, AUD-035, AUD-040 |
| SC-007 | UNVERIFIED | No 100% reconciliation measurement; [unwired writes][worker-wiring], [overwrite audit][audit], and [raw conversion][blobactual] violate its preconditions. | AUD-001, AUD-006, AUD-026, AUD-041 |
| SC-008 | UNVERIFIED | [Helper transition tests][breaker-test] do not measure <=3-minute registry degradation or <=1-minute restoration. Long cadences/backoff contradict an unconditional bound. | AUD-025, AUD-041, AUD-042 |
| SC-009 | PARTIAL | [One-direction incident-query assertion][storage-sim-test] exists, but [jurisdiction/unassociated branches][repo-query] and runner writes leak/bypass scope. No full bidirectional runtime measurement. | AUD-003, AUD-005, AUD-030, AUD-041 |
| FR-CAP-006-001 | UNVERIFIED | Explicitly deferred PAGASA typhoon/flood candidate: DOST-PAGASA MoU, JSON/CAP validator and <=15-minute Jun-Nov SLO prerequisites are not evidenced. No current AU implementation deficit inferred. | AUD-043 |
| FR-CAP-006-002 | UNVERIFIED | Explicitly deferred JMA/JAXA/QZSS candidate: licensing, sub-second ingestion validator and 24x7 freshness SLO are open prerequisites, not achieved capabilities. | AUD-043 |
| FR-CAP-006-003 | UNVERIFIED | Explicitly deferred BWDB/FFWC flood candidate: arrangement, hydro-station validator and <=30-minute Apr-Sep SLO are not evidenced. No deferred implementation authorised here. | AUD-043 |

### Inherited NFR

| Dependency | Status | Evidence and obligation | Follow-up |
| --- | --- | --- | --- |
| NFR-001 (spec 005) | UNVERIFIED | [Governance specification][governance-nfr] requires single-chain lookup p95 <=50ms; [lookup service][governance] times a call, but no attributable measurement or live agent integration establishes the percentile. This is explicitly inherited by 006 FR-030. | AUD-012, AUD-041, AUD-042 |

## Source and Product Coverage

This matrix accounts for all 46 current catalogue IDs. **Configured** means a config/adapter exists, not that it
works or is deployed; AUD-001 applies to every polled source. **No mapping** means no 006 simulator registration
or source-specific emission contract was found. A generic helper assigned to a source name is not native-format
coverage. Sources outside the explicitly enumerated live feed requirements still require a scenario-relevance
decision for FR-032/SC-005; derived sources do not automatically require new external pollers.

| Source row | Catalogue ID | Live path inspected | Simulation evidence / remaining obligation | Follow-up |
| --- | --- | --- | --- | --- |
| SRC-001 | bom-warnings | [FTP warning adapter][bom-warn], broken version tracking/XML normalization. | [Weather helper][weather] emits final envelopes, not BoM XML. | AUD-008, AUD-011, AUD-031 |
| SRC-002 | bom-forecasts | [Factory][factory] aliases forecasts to warnings, wrong identity/effective cadence. | No forecast-native mapping. | AUD-021, AUD-023, AUD-031 |
| SRC-003 | bom-radar | [Metadata-only listing][radar]. | Template names it; no radar product generator/download. | AUD-010, AUD-027, AUD-031 |
| SRC-004 | bom-observations | [One-station JSON path][bom-obs], not full summary/station products. | Template names it; generic SensorGenerator labels another ID. | AUD-019, AUD-021, AUD-031 |
| SRC-005 | ga-earthquake-alerts | [USGS source labelled GA][quake]. | Later [039 tests][feed-test] cover an earthquake shape, not 006 source pipeline parity. | AUD-021, AUD-031 |
| SRC-006 | ga-tsunami-warnings | [BoM XML subclass][tsunami], no CAP dispatch. | Later 039 tsunami shape is separate. | AUD-011, AUD-021, AUD-031 |
| SRC-007 | ga-sentinel-hotspots | [GeoJSON hotspot adapter][hotspots], limited batch and generic quality. | Template names it; no hotspot-specific 006 generator binding. | AUD-020, AUD-022, AUD-031 |
| SRC-008 | nsw-rfs-fires-near-me | [Enabled NSW fire adapter][fire]. | [Fire helper][fire-gen] lacks native incident/perimeter payload. | AUD-020, AUD-031, AUD-033 |
| SRC-009 | vic-cfa | [Enabled VIC fire adapter][fire]. | No VIC-specific simulation mapping. | AUD-020, AUD-031 |
| SRC-010 | qld-qfes | Adapter map exists, [config disabled][configs]. | No QLD-specific 006 mapping. | AUD-021, AUD-031 |
| SRC-011 | sa-cfs | State map exists, no configured/factory instance. | No mapping. | AUD-021, AUD-023, AUD-031 |
| SRC-012 | wa-dfes | State map exists, no configured/factory instance. | No mapping. | AUD-021, AUD-023, AUD-031 |
| SRC-013 | tas-tfs | State map exists, no configured/factory instance. | No mapping. | AUD-021, AUD-023, AUD-031 |
| SRC-014 | act-esa | State map exists, no configured/factory instance. | No mapping. | AUD-021, AUD-023, AUD-031 |
| SRC-015 | nt-pfes | State map exists, no configured/factory instance. | No mapping. | AUD-021, AUD-023, AUD-031 |
| SRC-016 | bom-flood-warnings | [Dedicated config disabled][configs], warnings adapter does not prove CAP equivalence. | Template names it; WeatherGenerator still emits bom-warnings. | AUD-011, AUD-023, AUD-031 |
| SRC-017 | nsw-ses-flood | [SES map][ses], configured but disabled. | Template names it; no source-specific registered generator. | AUD-021, AUD-031 |
| SRC-018 | vic-ses-flood | Map exists, no config/factory instance. | No mapping. | AUD-021, AUD-031 |
| SRC-019 | qld-ses-flood | Map exists, no config/factory instance. | No mapping. | AUD-021, AUD-031 |
| SRC-020 | ema | No 006 source adapter/config located. | Explicit scenario-relevance decision needed; no mapping. | AUD-031, AUD-042 |
| SRC-021 | aidr | Later corpus ingestion is a different knowledge-ingestion path. | Define relevance; no 006 source-signal simulator mapping. | AUD-031, AUD-042 |
| SRC-022 | nsw-health | No 006 advisory adapter/config located. | Define relevance for smoke/flood/cyclone scenarios; no mapping. | AUD-031 |
| SRC-023 | vic-health | No 006 advisory adapter/config located. | Define relevance; no mapping. | AUD-031 |
| SRC-024 | qld-health | No 006 advisory adapter/config located. | Define relevance; no mapping. | AUD-031 |
| SRC-025 | tfnsw | No live road-status-to-signal adapter found in NS-04. | [Later fictitious road feed][later-traffic] is not the required live pipeline mapping. | AUD-012, AUD-021, AUD-031 |
| SRC-026 | vicroads | No live road-status-to-signal adapter found. | Later road shape exists; catalogue binding/parity unproven. | AUD-021, AUD-031 |
| SRC-027 | tmr-qld | No live road-status-to-signal adapter found. | Later generic road shape does not establish source mapping. | AUD-021, AUD-031 |
| SRC-028 | energy-networks-nsw | No 006 utility adapter/config located. | Later 039 utility shape exists; relevance/catalogue mapping unproven. | AUD-031 |
| SRC-029 | water-authorities-nsw | No 006 utility adapter/config located. | Define relevance and source-format mapping. | AUD-031 |
| SRC-030 | bom-aws-stations | [Single-station AWS adapter][aws]. | [Sensor helper][sensor-gen] emits generic envelope, not native observation shape. | AUD-019, AUD-031 |
| SRC-031 | bom-river-gauges | [Small Kisters subset][river], missing level/threshold mapping. | [Hydrograph helper][flood] disconnected; later gauge shape lacks topology. | AUD-019, AUD-032, AUD-033 |
| SRC-032 | epa-air-quality | [NSW site-details default][epa], not required multi-state observations. | Later PM2.5 shape exists; original template has no matching 006 generator ID. | AUD-019, AUD-031 |
| SRC-033 | sentinel-satellite | [Disabled, mismatched catalogue adapter][sentinel]. | No full binary/source-metadata simulation path. | AUD-021, AUD-027, AUD-031 |
| SRC-034 | himawari-satellite | [Metadata listing][himawari], filename timestamps and PNG label. | Named in cyclone template without imagery generation/downloading. | AUD-010, AUD-027, AUD-031 |
| SRC-035 | twitter-disaster | [Disabled empty poller][twitter]. | [Social generator][social-gen] exists with ratio/geography defects. | AUD-028, AUD-034 |
| SRC-036 | facebook-community | [Disabled empty poller][facebook]. | No platform-specific generator mapping. | AUD-028, AUD-031 |
| SRC-037 | reddit-australia | [Disabled empty poller][reddit]. | No subreddit/native-source mapping. | AUD-028, AUD-031 |
| SRC-038 | surf-life-saving | [Generic manual API][post] only. | No source-specific registered simulation mapping. | AUD-002, AUD-020, AUD-031 |
| SRC-039 | volunteer-bushfire-brigades | Generic manual API only. | No source-specific registered simulation mapping. | AUD-002, AUD-020, AUD-031 |
| SRC-040 | snap-send-solve | [Disabled empty poller][snap]. | No geotagged infrastructure-report simulation mapping. | AUD-020, AUD-028, AUD-031 |
| SRC-041 | field-officer-reports | [Legacy field route][post]; no trusted identity/audit pipeline. | No field-source simulator mapping. | AUD-002, AUD-020, AUD-031 |
| SRC-042 | icon-ims | [Disabled shared IMS instance][ims]; config URL ignored. | No ICON native-payload simulator mapping. | AUD-023, AUD-029, AUD-031 |
| SRC-043 | webeoc-ims | Disabled placeholder IMS instance; no authenticated board contract. | No WebEOC native-payload simulator mapping. | AUD-029, AUD-031 |
| SRC-044 | agent-risk-assessments | Internal derived source; [Risk stored-data boundary][risk-retrieve] inspected, not an external poller obligation. | Must be explicitly included/excluded and generated through real downstream decisions where relevant. | AUD-012, AUD-031 |
| SRC-045 | aggregated-risk-scores | Internal derived source, not automatically an external adapter requirement. | No catalogue-to-scenario relevance/derived emission accounting. | AUD-031 |
| SRC-046 | historical-incidents-db | [Replay/seeding][seed-replay] and seed dashboard access exist, not a 006 live poller. | Time-window/complete-run replay and denominator treatment remain partial. | AUD-031, AUD-037 |

### Product-Level Obligations

| Product obligation | Status | Specific gap or supported assertion |
| --- | --- | --- |
| BoM warnings, all warning classes, XSD/AMOC, event update, 60s | PARTIAL | [XML poller][bom-warn] fetches files but fixed filenames/unsupported namespaces/schema errors lose updates; [tests][bom-test] are simplified. |
| BoM forecasts, state precis/city/town/district/coastal/local waters, 15min | PARTIAL | Forecast config selects warnings identity/class at 60s effective cadence; no product-family/15-minute assertions. |
| BoM state summary XML, 5min and individual station products, 30min | PARTIAL | Only representative station JSON at 300s is implemented; no XML summary path or separate 30-minute mode. |
| BoM radar PNG/IDR, overlays/transparencies, 5min | PARTIAL | Listing/filter exists; no real timestamps/coverage, overlays, full download or integrity tests. |
| BoM flood CAP/XML, 60s | PARTIAL | Dedicated config disabled; generic warning handling is not evidence of CAP parity or correct source ID. |
| BoM RSS/Atom warning notifications to immediate full product fetch | CONFLICT | Explicit FTP replacement [in source][rss] without a matching local requirement revision. |
| GA earthquake magnitude/depth/location/origin/phase, 60s | CONFLICT | USGS magnitude-limited/day source misattributed GA; early slicing and generic time/quality conversion. |
| Joint tsunami CAP/XML, 30s | PARTIAL | Faster subclass exists; no CAP normaliser dispatch or test. |
| GA hotspots location/temperature/confidence/satellite/acquisition, 15min | PARTIAL | Generic GeoJSON mapping and fixed quality; source-specific acquisition/quality tests absent. |
| Eight state fire services, native GeoJSON/RSS/CAP variants, 60s | PARTIAL | Eight maps but only NSW/VIC enabled; JSON assumptions and no all-state native assertions. |
| NSW/VIC/QLD SES flood status/affected area/evacuation orders, 2min | PARTIAL | No enabled coverage; generic FeatureCollection assumption lacks explicit JSON/evacuation mapping tests. |
| AWS sensor fields and station network, 5min | PARTIAL | Numeric range helper present; missing finite/completeness/native-time/network tests and jurisdiction mapping. |
| River gauges level/flow/trend/thresholds, 5min | PARTIAL | Fetches value/quality but does not expose specified readings/threshold-derived confidence. |
| State EPA PM2.5/PM10/ozone/AQI, 30min | PARTIAL | Site metadata is not observation acquisition; only NSW default instance. |
| Sentinel Data Space GeoTIFF products/coverage, 6h | CONFLICT | SciHub-shaped query/JP2 metadata vs configured website/Data Space requirement; disabled and no full download. |
| Himawari JPG/GeoTIFF/IDE products, 10min | PARTIAL | Generic IDE listing declares PNG and filename timestamp; no image-format or region-specific test. |
| X stream, Meta public feed and Reddit active/idle API budgets | MISSING | Empty pollers; no request/reconnect/throttling or native-response assertion bodies. |
| Snap partner feed, volunteer and surf-life-saving submissions | PARTIAL | Snap transport absent; manual API bypasses source/tier/identity validation. |
| Officer, ICON and WebEOC reports/deployments/boards/units | PARTIAL | Legacy API and shared unauthenticated placeholder IMS mapping are not the required source contract. |

## Acceptance Scenario Coverage

IDs below are review labels preserving the original story/scenario order; all 26 scenarios are individually mapped.

| Scenario | Status | Expected behavior and actual implementation/assertion evidence | Follow-up |
| --- | --- | --- | --- |
| US1-AS1 | PARTIAL | NSW thunderstorm CAP/XML persisted within 60s with authoritative weather confidence: [BoM helper][bom] and [simplified assertions][bom-test] exist, but parsing/persistence/timing do not. | AUD-001, AUD-008, AUD-011, AUD-041 |
| US1-AS2 | PARTIAL | Ten-minute sensor observation with station/method/source timestamp: [observation helper][obs] creates fields but native time/cadence/freshness and real station coverage lack assertions. | AUD-010, AUD-018, AUD-019, AUD-020 |
| US1-AS3 | CONFLICT | GA earthquake GeoJSON/geohazard/Point/tier: [poller][quake] substitutes USGS; [test][geo-test] edits category before asserting. | AUD-010, AUD-020, AUD-021, AUD-040 |
| US1-AS4 | PARTIAL | Matching high-confidence fire/weather/hydrology creates typed Risk handoff: [direct Monitoring tests][monitor-test] assert delivery but no live ingestion trigger or correct stored references. | AUD-012, AUD-016, AUD-042 |
| US1-AS5 | PARTIAL | Three failures degrade registry/log/dashboard: [breaker tests][breaker-test] assert local state only; status/registry/timing linkage absent. | AUD-025, AUD-038 |
| US2-AS1 | PARTIAL | Every NSW RFS feature maps alert/geometry/source: [NSW assertions][geo-test] cover selected fields; [poller][fire] caps records and production path is unwired. | AUD-001, AUD-020, AUD-022 |
| US2-AS2 | PARTIAL | SES event becomes hydrology with correct jurisdiction/tier: [SES mapping][ses] exists but no enabled instance or provider fixture assertion. | AUD-020, AUD-021 |
| US2-AS3 | PARTIAL | States with different fields normalize uniformly: [key-set assertion][geo-uniform-test] omits mapped values/types and real schema/native variants. | AUD-020, AUD-040 |
| US3-AS1 | PARTIAL | AWS ranges and timestamp-derived freshness: [normaliser][obs] checks selected numeric ranges but constants/native times/missing fields undermine contract; no direct sensor test found. | AUD-010, AUD-018, AUD-019 |
| US3-AS2 | MISSING | Gauge minor threshold elevates confidence and reaches Monitoring: [gauge adapter][river] never loads/compares thresholds and emits unrecognized value field. | AUD-012, AUD-019 |
| US3-AS3 | PARTIAL | Overlapping Himawari imagery downloads under incident; otherwise metadata only: [metadata-only adapter][himawari] exists, no overlap/full-download path or test. | AUD-010, AUD-027 |
| US3-AS4 | PARTIAL | Temperature 150 rejects at low confidence with reason: [range code][obs] does this helper branch, but no required assertion body/integrated rejection audit exists. | AUD-006, AUD-019, AUD-040 |
| US4-AS1 | PARTIAL | Tweet yields social/tier6/pending inferred hazard: [normaliser][twitter] has that basic output; stream and registry-backed trust are absent. | AUD-020, AUD-028 |
| US4-AS2 | PARTIAL | Snap road-closure photo/geotag becomes infrastructure/tier5: [mapping][snap] retains image reference/location but classifies road closure as community_report; polling absent. | AUD-020, AUD-028 |
| US4-AS3 | PARTIAL | Unverified burst escalates/reduces confidence and holds for review: [rules][misinfo] uncalled; [Tier 2][monitor-pipe] is partial and bypassable; helper tests do not prove stored non-forwarding. | AUD-013, AUD-014, AUD-015 |
| US5-AS1 | PARTIAL | NSW stored with tenant/agency isolation and invisible to VIC/QLD: [memory test][jurisdiction-test] covers one direction only; HPK, API and agency enforcement are defective. | AUD-003, AUD-004, AUD-005 |
| US5-AS2 | MISSING | Radar binary stored at incident/source/timestamp PNG path and referenced: [helper][binary-store] exists with no required caller/test. | AUD-027 |
| US5-AS3 | CONFLICT | Immutable per-ingestion audit with correlation/status: story says Cosmos audit container, FR-028 says Blob; [writer][audit] overwrites and lacks status. | AUD-006, AUD-012, AUD-042 |
| US5-AS4 | UNVERIFIED | Actual incident aggregation p95 <=500ms: [storage test][storage-test] has no latency assertion, [dashboard][dashboard] does not query required Cosmos signals. | AUD-004, AUD-041 |
| US6-AS1 | PARTIAL | Blue Mountains bushfire source progression: [template][templates] and [FFDI tests][fire-test] exist, but full source generators/physics/pipeline are unbound. | AUD-030, AUD-031, AUD-033 |
| US6-AS2 | PARTIAL | Every simulated signal has run provenance and isolated storage: [tag assertion][sim-tag-test] proves tags only; dict saves/default scope/raw prefixes remain incorrect. | AUD-005, AUD-026, AUD-030 |
| US6-AS3 | PARTIAL | Brisbane hydrograph crosses thresholds at realistic intervals: [curve tests][flood-test] assert thresholds/shape, not Brisbane parameters/cadence/topology via runner. | AUD-032, AUD-033 |
| US6-AS4 | PARTIAL | Social mix adjustable with misinformation/duplicates: [generator][social-gen] ignores misinfo override and has no ratio tests. | AUD-034 |
| US6-AS5 | PARTIAL | Full signal/handoff/recommendation replay: [later warp][warp] records some deliveries; original runner has no durable complete timeline and [replay][seed-replay] ignores bounds. | AUD-012, AUD-035, AUD-037 |
| US7-AS1 | PARTIAL | POST field report has tier4/kind/authenticated officer: [route][post] dispatches by submitted kind to legacy service; [API test][live-api-test] covers authoritative weather only. | AUD-002, AUD-020, AUD-040 |
| US7-AS2 | PARTIAL | ICON update preserves incident/type/status/location/units: [IMS mapping][ims-normalise] omits units and trusted identity/time/location, endpoint configuration/auth absent. | AUD-023, AUD-029 |

## Edge Case Coverage

| Edge case | Status | Implementation and assertion evidence | Follow-up |
| --- | --- | --- | --- |
| EC-001 | PARTIAL | Undocumented source schema change: [XML malformed-input tests][bom-test] exist, but well-formed incompatible XML/JSON is often defaulted to validated; no XSD/DLQ/operator alert path. | AUD-007, AUD-011, AUD-021 |
| EC-002 | MISSING | Contradictory authoritative sources: both could be stored independently after wiring, but [social helper][misinfo] has no authoritative-authoritative conflict/human-review implementation or assertion. | AUD-014, AUD-020 |
| EC-003 | MISSING | Truncated imagery discard/retry: no full binary ingestion/integrity/cleanup path in [adapters][himawari] or associated tests. | AUD-027 |
| EC-004 | PARTIAL | Real incident starts during simulation: [separate synthetic paths][sim036] exist, but original worker/repository scope guarantees and three-run/live test do not. | AUD-003, AUD-005, AUD-030, AUD-041 |
| EC-005 | MISSING | Social rate limit/newest-priority/structured throttling: [pollers][twitter] return empty and contain no actual request budget/backoff path. | AUD-028 |
| EC-006 | MISSING | Future sensor timestamp: [freshness][freshness] treats negative delta as fresh; observation normalisers prefill constants and do not flag skew. | AUD-010, AUD-018 |
| EC-007 | MISSING | Alert before 20GB logical partition limit: NS-05 found no sampler or 80% alarm; [metrics][metrics] lack storage size/count signals. | AUD-038 |

## Review and Checklist Obligations

### Specification Quality Checklist

Original checkboxes below are copied as evidence of authored assertions, not endorsed. All 23 items are mapped.

| Quality item | Original checkbox | Status | Obligation and assessment | Follow-up |
| --- | --- | --- | --- | --- |
| QC-001 | [x] | CONFLICT | No implementation detail except mandated Azure/domain formats: spec explicitly names ACA workers, Redis/Cosmos design and LLMCallMixin. Exemption needs a consistent documented scope. | AUD-042 |
| QC-002 | [x] | IMPLEMENTED | User value/business needs: all seven stories state operator/agent/planner outcomes. Authored quality, not delivery evidence. | - |
| QC-003 | [x] | PARTIAL | Nontechnical stakeholder readability: source detail is justified, but contradictory names/units/ownership impede interpretation. | AUD-042 |
| QC-004 | [x] | PARTIAL | Mandatory sections exist; checklist says 39 FRs, while amended spec has 49 local functional IDs plus three deferred capstone FRs. | AUD-042 |
| QC-005 | [x] | IMPLEMENTED | No NEEDS CLARIFICATION marker remains in the complete local specification. This does not settle documented conflicts. | AUD-042 |
| QC-006 | [x] | CONFLICT | Testable/unambiguous requirements: scope/null/schema/latency/backoff/authority and source-relevance conflicts remain. | AUD-042 |
| QC-007 | [x] | IMPLEMENTED | Nine SCs name quantitative thresholds; measurement and relevance denominator are not established. | AUD-031, AUD-041 |
| QC-008 | [x] | PARTIAL | Technology-agnostic criteria with Azure exception: SC-001 explicitly measures Cosmos persistence; requirement/exception wording needs consistency. | AUD-042 |
| QC-009 | [x] | IMPLEMENTED | All seven stories and 26 acceptance scenarios are present and individually assessed above. | - |
| QC-010 | [x] | IMPLEMENTED | Seven explicit edge cases are present; their unimplemented handling is recorded above. | AUD-007, AUD-014, AUD-027, AUD-028, AUD-038 |
| QC-011 | [x] | CONFLICT | Clear scope: two out-of-scope sections are present, but required governance consumption and schema/authority boundaries are inconsistent. | AUD-042 |
| QC-012 | [x] | PARTIAL | Eight original assumptions and later ASM items exist; API/licensing/data-sharing/provider and actor-review assertions are unverified. | AUD-043 |
| QC-013 | [x] | PARTIAL | All FRs have clear acceptance criteria: coarse stories do not resolve per-source relevance, native formats or all amended clauses. Report tables expose gaps. | AUD-031, AUD-042 |
| QC-014 | [x] | IMPLEMENTED | Seven primary user flows are authored. Runtime coverage is separately PARTIAL/MISSING, not inferred from this box. | - |
| QC-015 | [x] | UNVERIFIED | Feature meets measurable outcomes: neither prose PASS nor original task checks establish SC measurements. | AUD-041, AUD-043 |
| QC-016 | [x] | CONFLICT | No programming/framework/code-pattern leakage: names such as LLMCallMixin and worker deployment contradict the blanket assertion. | AUD-042 |
| QC-017 | [x] | PARTIAL | Life-safety cross-reference: local breaker exists, but registry feedback and safe misinformation paths are incomplete; constitutional numbering changed. | AUD-015, AUD-025, AUD-042 |
| QC-018 | [x] | PARTIAL | Multi-agent role/handoff cross-reference: consumer surfaces exist, live ingestion linkage does not. | AUD-012 |
| QC-019 | [x] | PARTIAL | Trust/provenance/freshness/raw cross-reference: constants, dropped fields and transformed raw records contradict it. | AUD-018, AUD-020, AUD-026 |
| QC-020 | [x] | PARTIAL | Privacy/security cross-reference: AU/TLS/private blobs configured; tenant/agency enforcement incomplete. No live compliance proof. | AUD-003, AUD-039 |
| QC-021 | [x] | PARTIAL | Cloud-platform cross-reference: Azure resources exist in active IaC, but older Principle VI reference now names evacuation. | AUD-039, AUD-042 |
| QC-022 | [x] | CONFLICT | Spec-005 dependency/schema stability: governance lookup is not consumed and both specs defer the runtime change. | AUD-012, AUD-042 |
| QC-023 | [x] | PARTIAL | Seed catalogue alignment: 46 records exist, but no 006 scenario relevance/activation/emission denominator. | AUD-021, AUD-031 |

The checklist's additional claim that BoM/RFS/GA/Himawari documentation was verified is **UNVERIFIED**: no
attributable provider-review record was located. Data-engineer involvement is an obligation, not proof of a
performed consultation (AUD-043).

### Quickstart Verification Checklist

| Verification item | Original checkbox | Status | Evidence and missing assertion/outcome | Follow-up |
| --- | --- | --- | --- | --- |
| QV-001 | [ ] | UNVERIFIED | Existing tests pass/no schema regression: none were run; no with/without simulation-marker schema test found. | AUD-007, AUD-040, AUD-043 |
| QV-002 | [ ] | PARTIAL | BoM XML/CAP XSD v1.7: simplified XML tests only; namespace/CAP dispatch gaps. | AUD-011 |
| QV-003 | [ ] | PARTIAL | NSW properties: helper fields asserted; native feed/complete geometry/schema not. | AUD-020, AUD-040 |
| QV-004 | [ ] | PARTIAL | Three-failure/half-open recovery: state tests exist, registry/timing untested. | AUD-025 |
| QV-005 | [ ] | PARTIAL | Unchanged warning dedup across 60s polls: helper tests only; filename update loss remains. | AUD-008, AUD-009 |
| QV-006 | [ ] | PARTIAL | National discoverability: memory fan-out helper test, no Cosmos automatic path. | AUD-004, AUD-016 |
| QV-007 | [ ] | PARTIAL | Simulation isolation: one incident-query assertion/tag-only tests miss other branches. | AUD-005, AUD-030 |
| QV-008 | [ ] | MISSING | Every simulated signal through same schema validation: direct-envelope bypass and key-only tests. | AUD-030, AUD-031, AUD-040 |
| QV-009 | [ ] | UNVERIFIED | 100% raw/audit correlation: no reconciliation assertion/run, audit overwrites. | AUD-006, AUD-026, AUD-041 |
| QV-010 | [ ] | PARTIAL | Tier-1 burst/contradiction/amplification: helper tests cover limited ordered samples, not wired rules. | AUD-013, AUD-014 |
| QV-011 | [ ] | PARTIAL | Tier-2 evaluation before forwarding: guarded pipeline exists, but persistence and facade bypass remain. | AUD-015 |

### Quickstart A-I Action Coverage

All 31 action groups are explicitly assessed; their implementation and test steps map to individual original tasks
above. These rows are not assertions that any phase was executed.

| Action group | Status | Numbered action obligations and source/test mapping | Follow-up |
| --- | --- | --- | --- |
| QA-A1 | PARTIAL | Add schema marker; with-marker, without-marker and regression checks: T002 artifact exists, test bodies/execution absent. | AUD-007, AUD-040, AUD-043 |
| QA-A2 | PARTIAL | Three domain models and validation/state tests: T003/T004/T005 models inspected; runner uses different model, tests absent. | AUD-036, AUD-040 |
| QA-B1 | PARTIAL | Worker/base plus polling, breaker, dedup, raw/schema/association/audit/metrics and integration assertions: T008/T016/T017/T033 incomplete. | AUD-001, AUD-007, AUD-024, AUD-038 |
| QA-B2 | PARTIAL | Redis hash hit/miss/store/TTL/expiry tests: T009/T018 local membership is not Redis expiry. | AUD-009 |
| QA-B3 | PARTIAL | Match footprint, null outside, national multi-record association: T010/T019 same-state helper only. | AUD-016 |
| QA-C1 | PARTIAL | BoM XSD warning and forecast normalization/field tests: T021/T031 simplified fixtures miss real namespaced products. | AUD-011 |
| QA-C2 | PARTIAL | RFS category/confidence/geometry plus GA Point/geohazard: T023/T032/T036/T037 partial assertions. | AUD-010, AUD-020, AUD-040 |
| QA-C3 | PARTIAL | AWS plausible readings and flood-threshold confidence tests: T024/T039/T043/T044 incomplete/missing. | AUD-019, AUD-040 |
| QA-C4 | PARTIAL | CAP conversion and flood/urgency test: T022 helper uncalled and untested. | AUD-011, AUD-040 |
| QA-C5 | PARTIAL | Metadata default and overlap-triggered full download tests: T025/T045 no full path/assertion. | AUD-027 |
| QA-D1 | PARTIAL | BoM warnings/observations/radar and GA quake/hotspot adapters plus transport-faked integration per source: classes exist, tests not concrete adapters. | AUD-001, AUD-021, AUD-040 |
| QA-D2 | PARTIAL | Eight fire/three SES feeds with state-specific fixtures: maps exist but instances/formats/assertions are incomplete. | AUD-021, AUD-022 |
| QA-D3 | PARTIAL | AWS/gauge/EPA ingestion and valid/implausible/anomalous tests: no direct physical-observation assertion located. | AUD-018, AUD-019 |
| QA-D4 | PARTIAL | Sentinel/Himawari plus both metadata/download integration modes: listing only. | AUD-027 |
| QA-D5 | PARTIAL | X/Meta/Reddit/Snap transports and tier/confidence tests: transport stubs remain. | AUD-020, AUD-028 |
| QA-D6 | PARTIAL | ICON/WebEOC and field-report POST contract: source/identity/auth/persistence requirements incomplete. | AUD-002, AUD-029 |
| QA-E1 | PARTIAL | Tier-1 detector and three rule assertions: helpers differ from documented algorithms and are unconnected. | AUD-013, AUD-014 |
| QA-E2 | PARTIAL | Escalated-signal LLM, misinformation block and unavailable-LLM hold tests: return classifications tested, stored decision/all-entrypoint behavior not. | AUD-015, AUD-040 |
| QA-F1 | PARTIAL | Cosmos CRUD/HPK/national fan-out/sim isolation/p95: in-memory tests cannot validate actual storage contract. | AUD-004, AUD-005, AUD-041 |
| QA-F2 | PARTIAL | Raw/binary paths, append JSONL and 100% evidence correlation: helpers exist, usage/append/assertions do not. | AUD-006, AUD-026, AUD-027 |
| QA-F3 | PARTIAL | Declaration-triggered scan, geometry update and configurable 24-hour lookback test: helper signature/no-op storage/no trigger. | AUD-017 |
| QA-G1 | PARTIAL | Runner/four templates and all-activated-sources integration: no production registrations or complete source coverage. | AUD-030, AUD-031 |
| QA-G2 | PARTIAL | Six parameterized model families with canonical schema tests: qualitative helpers/key assertions only. | AUD-031, AUD-033, AUD-034, AUD-040 |
| QA-G3 | PARTIAL | Historical overlay loader/perturbations and shifted replay integration: utility uncalled and schema-invalid. | AUD-035 |
| QA-G4 | MISSING | Concurrent live+simulation and three-run 50,000/hour tests: no combined runtime assertion or record located. | AUD-030, AUD-041 |
| QA-H1 | CONFLICT | Five scenario/run operations and OpenAPI HTTP contracts: current routes/tests use different tenant APIs. | AUD-036, AUD-042 |
| QA-H2 | PARTIAL | Reachable aggregated status and contract assertions: handler unmounted and unpopulated. | AUD-038 |
| QA-H3 | PARTIAL | Extended signal filters and correct subsets: parameter names exist but constraints/scope/negative tests do not. | AUD-003, AUD-040 |
| QA-I1 | PARTIAL | Signals HPK and simulation container: active resources exist; writer/key/old-template drift and no deployment evidence. | AUD-004, AUD-039 |
| QA-I2 | PARTIAL | Worker internal connectivity, managed identity, 1-6 scaling, CPU/backlog rules: active source has headless 2-6 CPU-only worker and no probes. | AUD-024, AUD-039 |
| QA-I3 | IMPLEMENTED | Four named private blob containers are authored in active infrastructure; deployment and correct use not implied. | AUD-006, AUD-026, AUD-039 |

### Plan Gates and Historical Review

| Review obligation | Status | Evidence assessment | Follow-up |
| --- | --- | --- | --- |
| PG-01 Pre-research life safety | PARTIAL | Breaker/fallback intent exists; no complete degraded-registry or misinformation boundary. | AUD-015, AUD-025 |
| PG-02 Pre-research agent roles | PARTIAL | Role separation is authored; first consumer/stored-reference chain is unconnected. | AUD-012 |
| PG-03 Pre-research trust/provenance/freshness | PARTIAL | Metadata fields exist, but constant freshness and transformed raw evidence violate claims. | AUD-018, AUD-020, AUD-026 |
| PG-04 Pre-research privacy/security | PARTIAL | Azure settings exist; scope/agency enforcement and no-PII claim are not established. | AUD-003, AUD-020, AUD-039 |
| PG-05 Pre-research multilingual boundary | IMPLEMENTED | Feature defers alert authoring/delivery to Communication; no new public-alert delivery is assessed here. | AUD-042 |
| PG-06 Pre-research cloud platform | PARTIAL | Azure infrastructure is authored; live state/policy compliance unverified. | AUD-039, AUD-043 |
| PG-07 Pre-research readiness | UNVERIFIED | Simulation/metrics/test plan exists, no quality-gate execution evidence. | AUD-040, AUD-041, AUD-043 |
| PG-08 Post-design life safety | PARTIAL | Plan asserts immutable audit/rejection guarantees contradicted by actual writer and dispatch paths. | AUD-006, AUD-007, AUD-015 |
| PG-09 Post-design agent roles | PARTIAL | Claimed event triggers and retrospective backfill are absent/incompatible. | AUD-012, AUD-017 |
| PG-10 Post-design trust/provenance/freshness | PARTIAL | Claimed source-derived freshness/confidence and content dedup differ from source. | AUD-008, AUD-009, AUD-018, AUD-020 |
| PG-11 Post-design privacy/security | PARTIAL | HPK alone is not tenant/agency authorization; simulation raw/query paths violate isolation. | AUD-003, AUD-004, AUD-005, AUD-026 |
| PG-12 Post-design multilingual boundary | IMPLEMENTED | Explicit no-alert-authoring scope is consistent with later spec-008 authority. | AUD-042 |
| PG-13 Post-design cloud platform | PARTIAL | Separate worker/identity is authored; active/legacy template differences and deployment proof unresolved. | AUD-039 |
| PG-14 Post-design readiness | UNVERIFIED | Four scenario helpers and A-I prose are not calibrated simulations, measured SCs, or verified gates. | AUD-031, AUD-033, AUD-040, AUD-041 |
| RR-01 Research architecture consultation | UNVERIFIED | Cosmos/polyglot/partition decisions are authored, but attributable data-engineer review/approval record was not found. | AUD-042, AUD-043 |
| RR-02 Schema backward-compatibility consultation | UNVERIFIED | Marker is added; no recorded review or both-mode schema assertion demonstrates the claimed approval. | AUD-007, AUD-040, AUD-043 |
| RR-03 Critique execution method | UNVERIFIED | Entire catalogue critique read; claims of sequential agent execution have no linked execution record/current-revision sign-off. Historical prompt not executed. | AUD-043 |
| RR-04 Critique Data Engineer O1/O2/O5 | PARTIAL | Partition/dedup/resilience concerns remain independently supported by current code, despite some now-existing helpers. | AUD-004, AUD-008, AUD-009, AUD-025 |
| RR-05 Critique Data Engineer O3/O4 | CONFLICT | Retention enforcement is explicitly out of 006 scope; polyglot evaluation is authored in research, contrary to historical 'not happened' prose. No unnecessary archival feature proposed. | AUD-042, AUD-043 |
| RR-06 Critique security/API/observer concerns | PARTIAL | Source-backed isolation, input-validation, immutable audit and handoff concerns are scoped into this report; broader unrelated agent claims are not imported as new requirements. | AUD-003, AUD-006, AUD-007, AUD-012, AUD-015 |
| RR-07 Critique QA/DevOps/SRE concerns | UNVERIFIED | Test files and CI now exist, so historical blanket absence is not accepted; measured load, probes, complete storage and readiness still lack evidence. | AUD-024, AUD-039, AUD-040, AUD-041 |
| RR-08 Remaining catalogue critiques | UNVERIFIED | Assessed as historical commentary about agent-catalogue design, not current 006 acceptance obligations. No new cross-spec implementation scope or resolution of those objections is inferred; their current closure is outside this review. | AUD-043 |

The RR-08 status does not assert that the catalogue objections have been fixed or formally superseded.
No agent-catalogue implementation was changed or certified.

### Data-Model and Contract Obligations

| Model/contract obligation | Status | Source and assertion assessment | Follow-up |
| --- | --- | --- | --- |
| DM-01 CamelCase wire / snake_case Python convention | CONFLICT | [Model document][model], [schema][schema] and [Cosmos save][repo] do not form a compatible HPK/document contract. | AUD-004, AUD-042 |
| DM-02 Simulation marker optional only for simulation, requires isolated storage | PARTIAL | Marker exists but conditional validation and save-scope derivation/authorisation are missing. | AUD-005, AUD-007, AUD-030 |
| DM-03 Pipeline config fields, valid source IDs, positive intervals/backoff/TTL | PARTIAL | [Config model][config-model] has field constraints/effective TTL, but source-ID validity and actual construction do not enforce them. | AUD-023 |
| DM-04 Audit required correlation/time and success/rejected invariant | PARTIAL | [Model][audit-model] checks success/rejected fields; writer omits validation status and overwrites evidence, UUID correlation is not stored on signal. | AUD-006, AUD-012 |
| DM-05 Breaker state/transitions and safe restart | PARTIAL | [Helper][breaker] and [tests][breaker-test] cover states; registry, reset and actual cadence bounds do not. | AUD-025 |
| DM-06 Dedup nonempty key/positive TTL/source-specific identity | PARTIAL | Helper accepts arbitrary hash and local cache ignores expiry; runtime TTL/source/run identity differs from model design. | AUD-009 |
| DM-07 Scenario Polygon/catalogue IDs/phases/ratio validation | PARTIAL | [Scenario model][scenario-model] constrains list length/ratios but not real geometry or catalogue membership. | AUD-036 |
| DM-08 Run scenario reference/transitions/source counts/effective parameters | PARTIAL | [Domain transition model][run-model] is disconnected from [runner dataclass][sim-runner]; no durable reference/count validation. | AUD-030, AUD-036, AUD-037 |
| DM-09 Signals indexes/no TTL and simulation `/scenario_id` resource settings | CONFLICT | Active resources exist; camelCase key vs snake_case writer and older 400 autoscale request need reconciliation. Performance is unverified. | AUD-004, AUD-039, AUD-041 |
| DM-10 Raw/binary/audit/simulation container paths and retention boundaries | PARTIAL | [Helpers][blob] define paths; actual raw path differs, audit overwrites, binary path uncalled. On-demand 30-day TTL conflicts with deferred retention enforcement and needs ownership decision. | AUD-006, AUD-026, AUD-027, AUD-042 |
| API-01 POST /signals ack and 422 diagnostic DLQ response | PARTIAL | [Route][post] returns accepted for legacy writes; weaker Pydantic errors do not implement specified diagnostic DLQ ID/details. | AUD-002, AUD-007 |
| API-02 GET /signals filters/items/total/limit<=1000/offset/since | PARTIAL | [Handler][get] has names/items/total but no max/negative bounds, enum/date enforcement or mandatory scope; Cosmos limits use page size rather than a result cap. | AUD-003, AUD-004, AUD-040, AUD-044 |
| API-03 Scenario list/create operations and ScenarioInput/Scenario schemas | CONFLICT | Published paths/schemas are not the current tenant API; [handwritten contract tests][sim-api-test] target later models. | AUD-036, AUD-042 |
| API-04 Run start/get/abort operations and creator/override/run status fields | CONFLICT | Actual routes and dataclass differ from required five operations and status enum. | AUD-036, AUD-042 |
| API-05 GET ingestion status and all PipelineStatus fields | PARTIAL | [Handler][status] unmounted/unpopulated; lacks sourceClass/IDs/last poll/rolling count/DLQ contract. | AUD-038 |
| API-06 SignalEnvelope source/location/provenance/enums and Signal response | PARTIAL | Schema/DTO/domain model diverge; source metadata dropped and invalid dates/geometry reach later conversion. | AUD-007, AUD-010, AUD-020 |

### Amendments, Assumptions and Scope Boundaries

| Amendment item | Status | Assessment and boundary | Follow-up |
| --- | --- | --- | --- |
| ASM-011 | IMPLEMENTED | AU-v1 baseline and PH/JP/BD deferral are explicit; country rollout is not claimed. Actual AU deployment remains unverified. | AUD-039, AUD-043 |
| ASM-012 | UNVERIFIED | Named data-engineer/bom-national/ga-national consultation is claimed, not demonstrated by per-change records. No agent was invoked in this audit. | AUD-043 |
| ASM-013 | PARTIAL | Identifier/persona conventions are referenced; schema/contract drift and validation claims remain unresolved. | AUD-042 |
| ASM-014 | UNVERIFIED | AU/Asia sovereignty tension is explicitly open; current bounded model-hosting carve-out does not permit non-AU data storage. | AUD-039, AUD-043 |
| PER-010 | UNVERIFIED | AU AIIMS persona references exist, but the label 'validated' has no local stakeholder-validation evidence. | AUD-043 |
| PER-011 | UNVERIFIED | Technical actor catalogue is referenced; authored actors do not prove the declared consultation/validation. | AUD-043 |
| PER-012 | UNVERIFIED | PH/JP/BD personas are explicitly placeholders pending reinterpretation and SME validation; no implementation mandated here. | AUD-043 |
| HYP-004 | UNVERIFIED | Required per-spec uplift/falsification evidence is absent; named HYP-HYP-004 artifact not found, portfolio [baseline][rubric-baseline] is insufficient. | AUD-043 |
| SCP-012 | IMPLEMENTED | Deferred country prerequisites are explicit and retained; this review does not implement those variants. | AUD-043 |
| SCP-013 | IMPLEMENTED | Constitution amendments remain outside feature authority; contradictions are recorded rather than resolved by this report. | AUD-042 |
| SCP-014 | IMPLEMENTED | Cross-spec arbitration and 018/008 deferrals are explicit; [008 reciprocal authority][communication-authority] verified in source. | AUD-042 |
| Original source-access assumptions | UNVERIFIED | BoM availability/XSD, state feed access/licensing, social API terms, GA endpoints, IMS agreements and Copernicus fair use were not verified by checked-in attributable records. | AUD-021, AUD-028, AUD-029, AUD-043 |
| Original simulation assumption | PARTIAL | Synthetic data is marked by helpers, but identical validation and isolation are not actually enforced. | AUD-007, AUD-030 |
| Original schema-compatibility assumption | PARTIAL | `incidentId` and `simulationRunId` exist, but null/marker/serialization compatibility and asserted agent validation are not proven. | AUD-007, AUD-042, AUD-043 |
| Original out-of-scope exclusions | IMPLEMENTED | Access negotiations, external API modification, new third-party APIs, model training, public alerting, downstream algorithms, archival enforcement, governance workflows and agent registry refactoring are not silently added to this review's implementation scope. The FR-020 conflict is explicitly routed for arbitration. | AUD-042 |

### Applicable Repository Review Gates

| Gate family | Status | Obligations assessed and limitations | Follow-up |
| --- | --- | --- | --- |
| Correctness/error handling | PARTIAL | Real entry points, dropped batches, no-op writes, false-success counts, unsupported values and silent failures traced; root cause tasks specify error outcomes. | AUD-001, AUD-006, AUD-007, AUD-008, AUD-025 |
| Security | PARTIAL | Input validation, authentication-bound authorisation, scope, raw/PII provenance, parameterized queries and data-region policy inspected. Query parameters are used in Cosmos SQL, but authorization is absent in key paths. No secret or dependency-vulnerability scan executed. | AUD-003, AUD-004, AUD-007, AUD-020, AUD-039 |
| Test quality | PARTIAL | Names, exact assertions, independence, fixtures, positive/negative/edge cases and mock boundaries inspected; key-only/tautological/mutated-result tests identified. No tests run. | AUD-040 |
| Performance/resource management | PARTIAL | Blocking calls, persistent caches/lists, eager unbounded reads, fixed slices, SDK client lifetime and pagination risks inspected. SDK `max_item_count` is not a total-result limit. No performance outcome inferred. | AUD-009, AUD-022, AUD-024, AUD-038, AUD-041, AUD-044 |
| Architecture/import boundaries | CONFLICT | Repository [import-linter rules][workspace-project] forbid ingestion depending on API, while production adapters import API pipeline_base and the Dockerfile copies API internals. Remediation must move/reuse a shared processing boundary, not add more cross-app dependencies. | AUD-001, AUD-023, AUD-039 |
| Documentation/maintainability | PARTIAL | Public contract, source-specific assumptions, comments vs actual behavior, model/schema changes and ownership reviewed. Blanket PASS claims and competing authoritative descriptions are tracked. No unrelated style cleanup proposed. | AUD-042, AUD-043 |
| Constitutional quality gates | UNVERIFIED | Automated lint/unit/integration, IaC what-if/plan review, human review for public dissemination and lessons support require future attributable evidence. This audit did none of those executions or approvals. | AUD-037, AUD-039, AUD-041, AUD-043 |

## Future Validation

**Everything in this section is FUTURE work, not executed in this review.** Do not replay historical commands from
the source documents. Run only after the corresponding repairs and separate authorisation for implementation/testing.

Common prerequisites: Python 3.12; a clean isolated environment with the repository's compatible API, agent,
ingestion and test dependencies; [test import-path setup][test-config]; canonical schema and licensed/redacted native
fixtures; injected clock/transport clients for deterministic checks. Disable ambient cloud/LLM telemetry credentials
for hermetic tests. Use explicit disposable Cosmos/Redis/Blob test resources or emulators when backend parity is
required, never silently fall back to memory. No installation, test-resource creation or environment modification
was performed during this review. Proposed new implementation/test paths must be approved and created before any
command referring to them can be treated as runnable.

| Future validation | Command or procedure | Additional prerequisites and objective result |
| --- | --- | --- |
| V01 | `python -m pytest tests/contract/test_bom_normaliser.py tests/contract/test_geojson_normaliser.py tests/integration/test_ingestion_pipeline.py -q` | Extend existing files for all native adapter/schema/error/worker cases. Real factory and processing logic; transport-only fakes. Exact persisted fields, source IDs, UTC times, raw evidence and DLQ outcomes asserted. |
| V02 | `python -m pytest tests/contract/test_circuit_breaker.py tests/contract/test_dedup_service.py tests/contract/test_incident_association.py tests/contract/test_signal_storage.py -q` | Add explicit Redis/Azure-adapter/emulator parity cases. Assert true TTL/atomicity, all HPK properties, bidirectional scopes, geometry fan-out, append-only audit and raw-byte reconciliation. Fake-only runs cannot close durable-storage gates. |
| V03 | `python -m pytest tests/contract/test_misinformation_detector.py tests/contract/test_monitoring_escalation.py tests/unit/test_monitoring_pipeline.py -q` | Test deterministic rule windows, exact model responses, persisted classifications and every facade/consumer. Assert exact flags, final status/rationale and no handoff for rejected/held inputs. No live LLM needed for contract cases. |
| V04 | `python -m pytest tests/integration/test_simulation_runner.py tests/simulation/test_flood_scenario.py tests/simulation/test_bushfire_scenario.py tests/simulation/test_cyclone_scenario.py tests/simulation/test_storm_scenario.py tests/unit/test_warp_scheduler.py -q` | Add canonical schema/native-format, 24:1 cadence, calibrated topology, ratio/overlay/replay and three-run/live isolation cases. Inject clocks rather than shortening away the obligation. Exact output counts/order/scopes must be asserted. |
| V05 | `python -m pytest tests/contract/test_live_incident_contract.py tests/contract/test_simulation_api_contract.py tests/unit/test_scenario_seeding.py -q` | Extend suites to call actual current application routers and agreed versioned OpenAPI. Assert field identity, authorised filters, HTTP 422/DLQ, status registration, scenario/run transitions and restart behavior. |
| V06 | `lint-imports --config pyproject.toml` and `ruff check apps/ingestion apps/api/app/services/ingestion packages/domain/src/domain/repositories tests/contract tests/integration tests/simulation` | First resolve current shared-boundary design; run focused type/format checks required by CI. Separately, an authorised IaC owner must compile the authoritative template and inspect policy/AVM/what-if evidence. No cloud command or compilation ran here. |
| V07 | After repairing the harness: `python -m locust -f tests/load/locustfile.py BurstIngestionUser DashboardUser --headless -u 20 -r 5 -t 1h --host http://127.0.0.1:8000` plus backend reconciliation and source-publication timing probes. | Disposable representative environment; valid unique source fixtures; actual durable storage; three concurrent simulations; fault injection; real incident queries instead of health requests. User count is a starting load parameter, not proof of 50k/hour. Capture all SC thresholds and inherited lookup percentile with revision, dataset, duration, raw measurements and denominator. Any Azure-backed run needs separate explicit authorisation. |

Additional proposed test coverage may stay in the existing suites above. The historical
`tests/integration/test_circuit_breaker.py` path is **proposed if used**; it is not existing test evidence in this
revision. HYP/provider/architecture/policy approvals require attributable human/evidence review, not a passing unit test.

### Objective Closure Gates

1. Every enabled input reaches one agreed pipeline and a durable schema-valid outcome, with actual source attribution.
2. Failed inputs retain raw evidence and a diagnostic dead letter; failure cannot discard unrelated batch items.
3. All reads, writes, updates, fan-out, raw objects and handoffs enforce authorised live/run/jurisdiction/agency scope.
4. Native source versions, quality, time and geometry survive normalization; updated products are not suppressed.
5. Misinformation gating is invoked and fail-closed at every dispatch entry; final decisions/provenance are stored.
6. Simulation uses the live processing path, calibrated models, verified source relevance and reproducible full replay.
7. Quantitative SC/NFR outcomes are demonstrated with non-placeholder records, including three runs alongside live.
8. Contracts and authority conflicts have explicit decisions; deferred geography and unaudited approvals remain labelled.
9. Only after these gates may authorised owners reconsider the historical task/quickstart completion claims.

## Report-Only Validation Boundary

The immediate post-write checks for this artifact are: one-row-per-original-task coverage and checkbox fidelity;
complete local FR/SC, acceptance, edge and checklist identifiers; every remediation remains unchecked;
relative source/test link existence and valid 1-based line anchors; final newline; and editor diagnostics for this
Markdown file only. These are document checks, not application tests, a build, performance evidence, or approval
of any remediation. Results are reported with this artifact's completion response; original evidence remains untouched.

## Evidence Links

[contract]: ../001-spec-implementation-audit/README.md#L10
[spec]: spec.md#L1
[tasks]: tasks.md#L1
[plan]: plan.md#L8
[research]: research.md#L1
[model]: data-model.md#L1
[openapi]: contracts/openapi-ingestion.yaml#L1
[quick]: quickstart.md#L1
[quality]: checklists/requirements.md#L1
[critique]: critique.md#L1
[critique-prompt]: prompts/critique.prompt.md#L1
[constitution]: ../../.specify/memory/constitution.md#L1
[review-rule]: ../../.github/instructions/code-review.instructions.md#L1
[review-checks]: ../../.github/instructions/references/code-review-checklists.md#L1
[comments]: ../../.github/instructions/code-commenting.instructions.md#L1
[bicep-rule]: ../../.github/instructions/bicep-code-best-practices.instructions.md#L1
[policy-rule]: ../../.github/instructions/bicep-policy-compliance.instructions.md#L1
[data-engineer]: ../../.github/agents/technical/data-engineer.agent.md#L1
[worker]: ../../apps/ingestion/worker.py#L38
[worker-wiring]: ../../apps/ingestion/worker.py#L208
[worker-health]: ../../apps/ingestion/worker.py#L84
[worker-stop]: ../../apps/ingestion/worker.py#L62
[factory]: ../../apps/ingestion/pipeline_factory.py#L50
[configs]: ../../apps/ingestion/pipeline_configs.py#L5
[config-model]: ../../apps/ingestion/pipeline_config.py#L6
[ingestion-project]: ../../apps/ingestion/pyproject.toml#L10
[pipeline]: ../../apps/api/app/services/ingestion/pipeline_base.py#L191
[pipeline-loop]: ../../apps/api/app/services/ingestion/pipeline_base.py#L135
[schema-validation]: ../../apps/api/app/services/ingestion/pipeline_base.py#L236
[enrich]: ../../apps/api/app/services/ingestion/pipeline_base.py#L304
[freshness]: ../../apps/api/app/services/ingestion/pipeline_base.py#L322
[metrics]: ../../apps/api/app/services/ingestion/pipeline_base.py#L337
[breaker]: ../../apps/api/app/services/ingestion/pipeline_base.py#L29
[dedup]: ../../apps/api/app/services/ingestion/dedup_service.py#L22
[repo]: ../../packages/domain/src/domain/repositories/signal_repository.py#L30
[repo-query]: ../../packages/domain/src/domain/repositories/signal_repository.py#L83
[repo-unassoc]: ../../packages/domain/src/domain/repositories/signal_repository.py#L120
[repo-update]: ../../packages/domain/src/domain/repositories/signal_repository.py#L148
[repo-fanout]: ../../packages/domain/src/domain/repositories/signal_repository.py#L45
[api-repo]: ../../apps/api/app/repositories/signal_repository.py#L51
[scope]: ../../apps/api/app/repositories/cosmos_scope.py#L12
[blob]: ../../apps/api/app/services/ingestion/blob_storage.py#L17
[blobupload]: ../../apps/api/app/services/ingestion/blob_storage.py#L59
[blobactual]: ../../apps/ingestion/blob_store.py#L28
[binary-store]: ../../apps/api/app/services/ingestion/blob_storage.py#L32
[audit]: ../../apps/api/app/services/ingestion/audit_writer.py#L18
[schema]: ../../packages/schemas/signal-envelope.schema.json#L1
[signal-model]: ../../packages/domain/src/domain/models/signal.py#L7
[audit-model]: ../../packages/domain/src/domain/models/ingestion_audit.py#L7
[scenario-model]: ../../packages/domain/src/domain/models/simulation_scenario.py#L16
[run-model]: ../../packages/domain/src/domain/models/simulation_run.py#L15
[normal-registry]: ../../apps/api/app/services/ingestion/normaliser_registry.py#L17
[assoc]: ../../apps/api/app/services/ingestion/incident_association.py#L45
[assoc-first]: ../../apps/api/app/services/ingestion/incident_association.py#L17
[multi]: ../../apps/api/app/services/ingestion/incident_association.py#L29
[bom]: ../../apps/ingestion/normalisers/bom_xml_normaliser.py#L21
[cap]: ../../apps/ingestion/normalisers/cap_normaliser.py#L53
[geo]: ../../apps/ingestion/normalisers/geojson_normaliser.py#L56
[obs]: ../../apps/ingestion/normalisers/json_observation_normaliser.py#L30
[binary-meta]: ../../apps/ingestion/normalisers/binary_metadata_normaliser.py#L8
[bom-warn]: ../../apps/ingestion/pipelines/bom_warnings.py#L35
[bom-obs]: ../../apps/ingestion/pipelines/bom_observations.py#L42
[radar]: ../../apps/ingestion/pipelines/bom_radar.py#L25
[rss]: ../../apps/ingestion/pipelines/bom_rss.py#L30
[quake]: ../../apps/ingestion/pipelines/ga_earthquakes.py#L28
[hotspots]: ../../apps/ingestion/pipelines/ga_hotspots.py#L27
[tsunami]: ../../apps/ingestion/pipelines/ga_tsunami.py#L24
[fire]: ../../apps/ingestion/pipelines/fire_service.py#L84
[ses]: ../../apps/ingestion/pipelines/ses_flood.py#L54
[aws]: ../../apps/ingestion/pipelines/sensor_aws.py#L28
[river]: ../../apps/ingestion/pipelines/sensor_river_gauge.py#L40
[epa]: ../../apps/ingestion/pipelines/sensor_epa_air.py#L32
[sentinel]: ../../apps/ingestion/pipelines/satellite_sentinel.py#L29
[himawari]: ../../apps/ingestion/pipelines/satellite_himawari.py#L31
[twitter]: ../../apps/ingestion/pipelines/social_twitter.py#L27
[facebook]: ../../apps/ingestion/pipelines/social_facebook.py#L24
[reddit]: ../../apps/ingestion/pipelines/social_reddit.py#L39
[snap]: ../../apps/ingestion/pipelines/community_snap.py#L24
[ims]: ../../apps/ingestion/pipelines/ims_webeoc.py#L30
[ims-normalise]: ../../apps/ingestion/pipelines/ims_webeoc.py#L61
[misinfo]: ../../apps/api/app/services/ingestion/misinformation_detector.py#L149
[burst]: ../../apps/api/app/services/ingestion/misinformation_detector.py#L11
[duplicate]: ../../apps/api/app/services/ingestion/misinformation_detector.py#L101
[monitor]: ../../apps/agents/monitoring/agent.py#L89
[monitor-llm]: ../../apps/agents/monitoring/agent.py#L126
[monitor-retro]: ../../apps/agents/monitoring/agent.py#L185
[monitor-pipe]: ../../apps/agents/monitoring/pipeline.py#L168
[maf-monitor]: ../../apps/agents/maf_runtime/agents/monitoring_agent.py#L25
[maf-builder]: ../../apps/agents/maf_runtime/workflow/builder.py#L90
[risk-retrieve]: ../../apps/agents/risk_assessment/pipeline.py#L169
[evac-retrieve]: ../../apps/agents/evacuation/pipeline.py#L448
[res-retrieve]: ../../apps/agents/resource_allocation/pipeline.py#L232
[comm-retrieve]: ../../apps/agents/communication/pipeline.py#L225
[handoffs]: ../../apps/agents/common/handoffs.py#L27
[post]: ../../apps/api/app/api/routes/signals.py#L14
[get]: ../../apps/api/app/api/routes/signals.py#L29
[manualservice]: ../../apps/api/app/services/ingestion/authoritative_ingestion.py#L12
[state]: ../../apps/api/app/services/state_store.py#L17
[validator]: ../../apps/api/app/validators/signal_envelope.py#L24
[tenant]: ../../apps/api/app/middleware/tenant_middleware.py#L19
[router]: ../../apps/api/app/api/router.py#L57
[dashboard]: ../../apps/api/app/services/dashboard_service.py#L49
[declare]: ../../apps/api/app/api/routes/incidents.py#L20
[status]: ../../apps/api/app/api/routes/ingestion_status.py#L8
[sim-runner]: ../../apps/ingestion/simulation/simulation_runner.py#L47
[sim-phase]: ../../apps/ingestion/simulation/simulation_runner.py#L81
[sim-save]: ../../apps/ingestion/simulation/simulation_runner.py#L133
[templates]: ../../apps/ingestion/simulation/scenario_templates.py#L1
[flood]: ../../apps/ingestion/simulation/generators/flood_generator.py#L9
[fire-gen]: ../../apps/ingestion/simulation/generators/fire_generator.py#L9
[cyclone]: ../../apps/ingestion/simulation/generators/cyclone_generator.py#L9
[weather]: ../../apps/ingestion/simulation/generators/weather_generator.py#L8
[sensor-gen]: ../../apps/ingestion/simulation/generators/sensor_generator.py#L21
[social-gen]: ../../apps/ingestion/simulation/generators/social_generator.py#L29
[overlay]: ../../apps/ingestion/simulation/generators/historical_overlay.py#L22
[sim-api]: ../../apps/api/app/api/routes/simulations.py#L27
[seed]: ../../apps/api/app/services/scenario_seeding_service.py#L30
[seed-replay]: ../../apps/api/app/services/scenario_seeding_service.py#L83
[warp]: ../../apps/api/app/services/warp_scheduler.py#L132
[sim036]: ../../apps/api/app/api/routes/simulations_036.py#L1
[sim-dispatch]: ../../apps/api/app/services/simulation/signal_pipeline_orchestrator.py#L238
[sim-publish]: ../../apps/api/app/services/simulation/event_hub_publisher.py#L84
[later-gauge]: ../../apps/api/app/services/simulation/feeds/bom_flood_gauge.py#L30
[later-traffic]: ../../apps/api/app/services/simulation/feeds/traffic_road_closure.py#L18
[catalogue]: ../../packages/domain/src/domain/seed/data_sources_australia.json#L1
[azd]: ../../azure.yaml#L9
[activeinfra]: ../../infra/main.bicep#L609
[active-sim]: ../../infra/main.bicep#L635
[activeblobs]: ../../infra/main.bicep#L525
[activeworker]: ../../infra/main.bicep#L1189
[legacyinfra]: ../../infra/bicep/main.bicep#L109
[partition-doc]: ../../docs/architecture/deployment/cosmos-partitioning.md#L23
[governance]: ../../apps/api/app/services/governance_registry.py#L1
[governance-nfr]: ../005-data-source-governance/spec.md#L155
[communication-authority]: ../008-communication-agent/spec.md#L367
[rubric-baseline]: ../028-capstone-alignment/evidence/rubric-baseline.md#L1
[risk-record]: ../../docs/risk-register/RISK-NEW-013.md#L9
[ci]: ../../.github/workflows/ci.yml#L133
[workspace-project]: ../../pyproject.toml#L1
[test-config]: ../../tests/conftest.py#L1
[bom-test]: ../../tests/contract/test_bom_normaliser.py#L39
[geo-test]: ../../tests/contract/test_geojson_normaliser.py#L65
[quake-test]: ../../tests/contract/test_geojson_normaliser.py#L92
[geo-uniform-test]: ../../tests/contract/test_geojson_normaliser.py#L127
[storage-test]: ../../tests/contract/test_signal_storage.py#L23
[storage-sim-test]: ../../tests/contract/test_signal_storage.py#L72
[storage-update-test]: ../../tests/contract/test_signal_storage.py#L106
[jurisdiction-test]: ../../tests/contract/test_signal_storage.py#L60
[fanout-test]: ../../tests/contract/test_signal_storage.py#L86
[breaker-test]: ../../tests/contract/test_circuit_breaker.py#L6
[dedup-test]: ../../tests/contract/test_dedup_service.py#L6
[association-test]: ../../tests/contract/test_incident_association.py#L50
[misinfo-test]: ../../tests/contract/test_misinformation_detector.py#L53
[contradiction-test]: ../../tests/contract/test_misinformation_detector.py#L71
[duplicate-test]: ../../tests/contract/test_misinformation_detector.py#L90
[pipeline-test]: ../../tests/integration/test_ingestion_pipeline.py#L43
[sim-test]: ../../tests/integration/test_simulation_runner.py#L19
[sim-tag-test]: ../../tests/integration/test_simulation_runner.py#L64
[flood-test]: ../../tests/simulation/test_flood_scenario.py#L21
[flood-schema-test]: ../../tests/simulation/test_flood_scenario.py#L77
[fire-test]: ../../tests/simulation/test_bushfire_scenario.py#L21
[cyclone-test]: ../../tests/simulation/test_cyclone_scenario.py#L21
[storm-test]: ../../tests/simulation/test_storm_scenario.py#L21
[monitor-test]: ../../tests/unit/test_monitoring_pipeline.py#L65
[monitor-contract]: ../../tests/contract/test_monitoring_escalation.py#L61
[risk-test]: ../../tests/unit/test_risk_assessment_pipeline.py#L91
[resource-test]: ../../tests/unit/test_resource_allocation_pipeline.py#L127
[risk-handoff-test]: ../../tests/contract/test_risk_assessment_escalation.py#L47
[live-api-test]: ../../tests/contract/test_live_incident_contract.py#L44
[sim-api-test]: ../../tests/contract/test_simulation_api_contract.py#L14
[scenario-test]: ../../tests/unit/test_scenario_seeding.py#L9
[warp-test]: ../../tests/unit/test_warp_scheduler.py#L91
[feed-test]: ../../tests/unit/spec039/test_feed_seed_contract.py#L41
[load]: ../../tests/load/locustfile.py#L31
[baseline]: ../../tests/load/baselines/legacy_baseline.json#L1
[bench-pipeline]: ../../tests/benchmark/test_pipeline_performance.py#L180
[bench-latency]: ../../tests/benchmark/test_pipeline_latency.py#L32
[python-et]: https://docs.python.org/3.12/library/xml.etree.elementtree.html#element-objects
[jsonschema-faq]: https://python-jsonschema.readthedocs.io/en/stable/faq/#my-schema-specifies-format-validation-why-do-invalid-instances-seem-valid

### 2026-09-18 Implementation Pass

This pass was performed as an isolated context for spec 006 only. Three parallel technical reviews examined worker
composition/storage, API scope/schema contracts, and simulation/operations. The first source slice normalized the
pipeline constructor contract used by the worker/factory and tests, including `dedup_ttl_seconds`, explicit
`schema_validator`, misinformation-detector injection, and explicit simulation-scope authorization. Processing now
uses atomic `try_claim`/`commit` when available and releases claims on validation or persistence failure, while
retaining compatibility with older test doubles.

| Area | Result | Evidence / remaining limitation |
| --- | --- | --- |
| AUD-001 / AUD-009 / AUD-023 | Partial source repair. | `apps/api/app/services/ingestion/pipeline_base.py` accepts the factory dependency contract and uses configured dedup TTL/claim lifecycle; production mandatory dependency/readiness and durable storage gates remain open. |
| Focused ingestion validation | Partial pass. | `python -m pytest tests/integration/test_ingestion_pipeline.py -q` reached 9 passed / 7 failed. Remaining failures cover governance eligibility, durable DLQ/raw-byte handling, incident association fan-out, and misinformation detector invocation. |
| AUD-002–AUD-008 / AUD-014–AUD-044 | Open or evidence-gated. | API scope, schema/dead-letter durability, append-only audit, Cosmos parity, provider verification, simulation fidelity, performance, Azure policy, and external source/legal evidence require subsequent isolated slices and authorized environments. |

No deployment, provider, Cosmos, Blob, load, calibration, or human/SME evidence was created. The pass improves a
local composition boundary but does not claim ingestion readiness or operational acceptance.

### 2026-09-19 Continuation Pass

The missing `IngestionProcessingResult` contract was repaired by exposing the existing `Signal` result type, accepting
the configured governance registry, and removing invalid awaits around the synchronous authoritative ingestion service.
The remaining focused ingestion failures were then repaired in the base orchestration: governance eligibility now runs
before normalization/deduplication, rejected payloads retain raw references and enter the DLQ, multi-incident matches
persist one signal per incident, and social/community payloads apply scope-bounded Tier-1 misinformation detection before
fan-out. Validation: `python -m pytest tests/integration/test_ingestion_pipeline.py -q` returned `16 passed`.

Durable production dependency readiness, live Cosmos/Blob behavior, broader API tenant authorization, provider evidence,
and performance/human evidence remain open.
