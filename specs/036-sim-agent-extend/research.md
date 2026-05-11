# Research Notes: Real Sub-Agent Invocation & Simulation Telemetry-Injection Agent

**Spec**: [`spec.md`](./spec.md) · **Plan**: [`plan.md`](./plan.md) · **Date**: 2026-05-08
**Cohort input**: `cohort-tech-arch-ai.md` (8 personas) + `cohort-tech-qsoi.md` (9 personas).

This document records the research that resolved every NEEDS CLARIFICATION the cohorts surfaced, the 12 open trade-offs, the constitutional ADRs, the existing-pattern reuse analysis, the risk register with mitigations, and a rough cost envelope.

---

## 1. Decisions on the 12 Open Trade-Offs

### 1.1 — Container App topology for `simulation-telemetry-injection`

**Decision**: **Bundled** as a Python sibling module `apps/agents/simulation_telemetry_injection/` inside the existing `apps/agents` Container App. NOT a fourth Container App.

**Rationale**:

- The platform constitution caps runtime projects at **3 Container Apps**: `apps/api`, `apps/agents`, `apps/ingest`. A 4th Container App would require a documented constitutional exception with explicit project-lead approval.
- Architecture cohort (Solution Architect, Principal Engineer, AI/ML Engineer, Software Developer) gives **strong consensus** for bundling — the new agent is functionally a sibling of `monitoring/`, `risk_assessment/`, etc. and shares the same `apps/agents/Dockerfile` base.
- QSOI cohort (Infra/DevOps, Docker) raised the scaling-isolation argument for separation — addressed by KEDA HTTP scaler on the shared Container App with `minReplicas: 1` (warm), `maxReplicas: 3` (5 concurrent sims × 5 threads upper bound) and HTTP-concurrency-based scale-out on the SSE endpoint. Independent scaling is not needed at MVP load.
- Bundling preserves the FR-008 sequential-write-then-fan-out invariant inside one runtime, enabling clean Cosmos session-token propagation and one OpenTelemetry trace per turn.

**Alternatives considered**:

- *Separate Container App for `simulation-telemetry-injection`* — provides scaling isolation; rejected because (a) the 3-project cap; (b) HTTP overhead on the synchronous FR-008 first step would erode the ≤ 5 s parse-to-pipeline budget; (c) inter-Container-App auth via Managed Identity would add complexity for no measurable benefit.
- *Separate process inside `apps/agents` with its own Dockerfile target* — possible but adds an internal split with no scaling benefit when both targets share the same Container App spec.

**Cost impact**: Zero net new Container App resource cost. Existing `apps/agents` Container App scaling band increases (max replicas 3 vs. current 2 documented in `infra/bicep/container-apps-scaling.bicep`). At ~AU$60/replica/month for Dedicated workload, max delta ~AU$60/month at peak.

---

### 1.2 — Sub-agent adapter deployment model

**Decision**: **Direct Python imports** inside the `apps/agents` Container App. Each adapter under `apps/api/app/services/simulation/sub_agents/<name>_adapter.py` imports the sibling agent module's handler from `apps/agents.<name>.handler` and awaits it directly.

**Rationale**:

- Both agents and API run inside their own Container Apps in the existing topology (`apps/api` has the Controller; `apps/agents` has the 6 sub-agent handlers). Cohorts converged that **`apps/api` calls `apps/agents` over HTTP** is the existing pattern (see `httpx.AsyncClient` usage in current Controller code).
- However, for the **synchronous FR-008 inject-then-dispatch invariant** within a single Controller turn, the architecture cohort's recommendation stands: bundle the new injection module into `apps/agents` and call sub-agent handlers via async HTTP from `apps/api` using `httpx.AsyncClient` with a **shared in-process connection pool** (`max_connections=50`, `max_keepalive_connections=20` per Docker cohort sizing).
- The `SubAgentFn` type alias `Callable[[str, str], Awaitable[SubAgentReply]]` already exists in `apps/api/app/services/simulation/sub_agent_invoker.py`. The `production_invoker()` factory will register HTTP-bound implementations of the 6 adapters; the existing `default_invoker()` stays for offline/test mode (selected by env var `SIM_CONTROLLER_MODE`).
- Direct Python imports are explicitly NOT used cross-Container-App because that would require co-locating runtimes and break the existing `apps/api` ↔ `apps/agents` deployment-isolation contract.

**Clarification on plan.md wording**: The plan diagram shows "direct Python imports" inside the agents Container App. The accurate statement is: **`apps/api` → `apps/agents` over async HTTP** with `httpx.AsyncClient`; **inside `apps/agents`** the new injection module and the 6 sub-agents are siblings sharing a Python process. The Controller in `apps/api` calls each sub-agent via HTTP; sub-agents themselves do not call each other directly (they react to signals via Event Hubs consumer groups).

**Alternatives considered**:

- *Service Bus commands for sub-agent fan-out* — adds queue latency on the synchronous Controller-driven fan-out path; rejected. Service Bus is reserved for cross-feature command dispatch in spec 028 patterns.
- *Direct in-process Python imports across `apps/api` ↔ `apps/agents`* — would require collapsing the two Container Apps, breaking existing deployment isolation. Rejected.

**Cost impact**: Zero net new resource cost.

---

### 1.3 — FR-015 read-your-own-write mechanism

**Decision**: **Cosmos DB Session consistency** on the new `simulation_synthetic_signals` container, with **explicit session-token propagation** from `TelemetryInjectionService.write_signal()` → `ControllerService.dispatch_substantive_agents()` → adapter Cosmos read calls. Codified in **ADR-036-001**.

For the FR-026 Risk-Assessment auto-fan-out (signal-driven, not Controller-driven), the Event Hubs consumer group pattern provides at-least-once delivery with monotonic ordering per `simulation_id` partition key — Risk Assessment's `handle_signal_event()` observes the freshly-written signal in monotonic order without needing a session token (the producer flushes the signal to Event Hubs before returning the session token to the Controller).

**Rationale**:

- Account default is `Consistent-Prefix` (per existing `infra/bicep/cosmos-workflow.bicep`). `Consistent-Prefix` does NOT guarantee that a write performed by one operation is visible to a subsequent read in a different operation in the same session.
- `Session` consistency guarantees: monotonic reads within a session, read-your-own-writes within a session. Cost: zero — Session is *cheaper* than `Strong` and not measurably more expensive than `Consistent-Prefix` at MVP write rates. AU East single-region deployment means no cross-region latency penalty.
- Architecture cohort (Azure Principal Architect, Data Engineer) and QSOI (Infra/DevOps) all named Session consistency as the MVP recommendation.
- Redis pub/sub confirmation was considered as an alternative; deferred to post-MVP. It would add a Redis round-trip + new code path; Session consistency is zero-new-infra and reuses the Cosmos SDK natively.

**Alternatives considered**:

- *Bounded staleness* — provides a stronger guarantee but at higher RU cost; not needed.
- *Strong consistency* — too expensive; would also require a multi-region account upgrade for cross-region reads (we are AU East single-region).
- *Redis pub/sub on `sim:{sim_id}:signal:{signal_id}` key* — viable post-MVP if multi-Container-App-instance coordination becomes a bottleneck. Adds Redis as a second source of truth.
- *Service Bus sessions* — adds session-state overhead and changes the signal-pipeline pattern from Event Hubs (existing); rejected.

**Cost impact**: Marginal. Session consistency is at most a few percent more RU than Consistent-Prefix at observed write rates (~1 K writes/sim/hour upper bound). Estimated +AU$5/month.

**ADR-036-001**: Documented in `docs/adr/ADR-036-001-cosmos-session-consistency.md` (created at task time). Reviewed by Solution Architect; reviewed by Compliance Auditor (no audit-trail implication — change feed is unaffected).

---

### 1.4 — FR-009 parse-attempt circuit-breaker placement and threshold

**Decision**: **Two-layer enforcement** — Azure API Management `rate-limit-by-key` policy on the `sub` JWT claim as the primary tamper-resistant outer ring, plus an in-process `ParseAttemptCircuitBreaker` (asyncio token-bucket backed by Azure Cache for Redis) as defence-in-depth. **Threshold: 60 parse-attempts / minute / user, with a 10/sec burst allowance.** Threshold value stored in Azure App Configuration so it can be re-tuned without redeploying.

**Rationale**:

- Security cohort: APIM `rate-limit-by-key` is tamper-resistant and cannot be bypassed by direct Container Apps ingress (provided ingress is restricted to APIM via VNET). In-process middleware can be bypassed if ingress is reachable directly.
- Architecture cohort + SRE: in-process is faster fallback when APIM has a local outage and adds an audit-friendly hook (the `injection.circuit_open` typed audit entry per FR-009).
- Threshold rationale: FR-009 sets the success-counted budget at 30 injections/min/user. The parse-attempt circuit-breaker is for **abusive flooding** of un-parseable text. **2× the success budget** (60/min) gives legitimate refused-and-clarified workflows headroom (FR-010 life-safety low-confidence refuse-and-clarify can produce up to 2 refused parses per minute under exercise pressure). Burst of 10/sec accommodates one chat turn that contains a long paragraph of noisy text the LLM legitimately tries hard to parse before refusing.
- Both layers write a typed `injection.circuit_open` audit entry on trip; the breaker auto-closes after a 1-minute cooldown.

**Configurable values** (`infra/bicep/modules/apim-policies.bicep` parameters → Azure App Configuration entries `simulation/parseAttempt/perMinute` = 60, `simulation/parseAttempt/burst` = 10, `simulation/parseAttempt/cooldownSeconds` = 60).

**Alternatives considered**:

- *In-process only* — bypassable; rejected.
- *APIM only* — single point of failure; rejected.
- *Per-tenant rather than per-user* — does not protect against a buggy user client floods within the same tenant; rejected.
- *50/min* — cohort suggested order-of-magnitude ~60; 50 leaves no headroom for the FR-010 hybrid gate.

**Cost impact**: APIM `rate-limit-by-key` policy adds zero new resource cost (existing APIM SKU). Redis token-bucket usage is sub-1 % of existing Standard C1 capacity.

---

### 1.5 — FR-021 jurisdiction-boundary dataset

**Decision**: **Platform jurisdiction registry (preferred) → ABS Statistical Areas Level 4 (fallback)**, hosted as versioned GeoJSON in Blob Storage container `jurisdiction-boundaries/v{N}.geojson` (LRS, AU East, no WORM). Loaded into an in-memory STRtree (R-tree, `rtree` Python library) at Container App startup for O(log n) point-in-polygon viewport revalidation.

**Rationale**:

- Architecture cohort (Solution Architect): the platform jurisdiction registry is preferred because it is internal-controlled (governance via PR approval) and version-controlled. ABS-SA4 boundaries are stable, public, and well-known but lack platform-specific distinctions (e.g. SES/RFS jurisdictional overlays).
- Composite approach: registry is authoritative; ABS-SA4 fills any gap. Version field on each GeoJSON file (`v1`, `v2`, etc.) lets the registry evolve without breaking running Container Apps — startup loads the highest-numbered version.
- STRtree spatial index is the industry-standard Python pattern (`shapely` 2.0 + `rtree` 1.3); load time ~100 ms at startup for 8 state/territory polygons; query time <1 ms for a viewport centroid.
- The dataset is hosted in Blob Storage (`australiaeast`, LRS — no GZRS needed since the data is small and re-deployable from Git history). RBAC: `Storage Blob Data Reader` for the API Container App's Managed Identity. Versioning via SemVer tag in the blob name; a `current` version pointer stored in App Configuration so the active version can be flipped without redeploy.

**Alternatives considered**:

- *PostGIS database* — overkill and breaks the all-Azure data-plane preference; rejected.
- *In-memory hard-coded polygons* — not version-controllable; rejected.
- *Azure Maps geo-fences* — vendor-specific, costs per call, and depends on Azure Maps for what is effectively a static dataset; rejected.

**Cost impact**: Negligible — Blob Storage LRS for ~5 MB of GeoJSON costs <AU$1/month.

---

### 1.6 — FR-052 thread-cap atomic enforcement

**Decision**: **Cosmos DB ETag optimistic concurrency** on a per-simulation document `simulation_threads/{sim_id}` containing `{thread_count, version, threads[]}`. Conditional update via `If-Match: <etag>`; **5 retries with 50 ms exponential backoff + jitter** on `412 Precondition Failed` responses.

**Rationale**:

- Spec 007 caps concurrent coordinators per sim at 3, so realistic concurrent-thread-create contention is bounded. ETag retry loop converges quickly.
- ETag is stateless and avoids Redis as a second source of truth (which a distributed lock would introduce).
- `tenacity` already exists in the dependency list; reuse for the retry loop.
- Principal Engineer concern (race condition between thread-count read and conditional write) is addressed by the conditional update being **atomic at the Cosmos server**: the entire read-modify-write is wrapped in a single `replace_item` call with `if_match=etag` — no time-of-check-to-time-of-use gap.

**Concurrency model**:

```python
async def increment_thread_count(sim_id: str, proposed_thread: HazardThread) -> bool:
    for attempt in range(5):
        doc, etag = await thread_repo.read_with_etag(sim_id)
        if doc.thread_count >= 5:
            await audit.write("thread.cap_exceeded", sim_id=sim_id, proposed=proposed_thread)
            return False
        doc.threads.append(proposed_thread)
        doc.thread_count += 1
        try:
            await thread_repo.replace_item(doc, etag=etag)
            return True
        except CosmosAccessConditionFailedError:
            await asyncio.sleep(0.05 * (2 ** attempt) + random.uniform(0, 0.05))
    raise ThreadCapContention(sim_id)
```

**Alternatives considered**:

- *Redis distributed lock (`SET NX EX`)* — works but adds a second source of truth and introduces lock-TTL/refresh complexity; rejected.
- *Single-writer queue (Service Bus session)* — overkill for ≤ 3 coordinators; serialises writes unnecessarily; rejected.

**Cost impact**: Zero new resources.

---

### 1.7 — Exercise Outcome Record (FR-054) storage

**Decision**: **Azure Blob Storage WORM** (LRS, AU East, time-based 7-year immutable retention policy) for the primary record at `exercise-outcome-records/{sim_id}/v{generation_seq}.json`, plus a **Cosmos DB `exercise_outcome_index` container** for queryable metadata.

**Schema** (Cosmos `exercise_outcome_index` document):

```json
{
  "id": "<uuid>",
  "simulation_id": "<sim_id>",
  "generation_seq": 1,
  "blob_uri": "https://<storage>.blob.core.windows.net/exercise-outcome-records/{sim_id}/v1.json",
  "blob_etag": "...",
  "sections_hash": ["<sha256-timeline>", "<sha256-agent-responses>", "<sha256-ic-decisions>", "<sha256-gaps>", "<sha256-lessons-identified>"],
  "size_bytes": 4823104,
  "generation_timestamp": "2026-05-08T03:14:22Z",
  "generation_user_id": "<coordinator>",
  "aidr_schema_version": "2026.1",
  "_partitionKey": "<sim_id>"
}
```

Idempotency (FR-055): regeneration with the same input audit subtree produces a byte-identical blob at the same `v{N}` path. `generation_seq` increments **only on data changes** (e.g., a follow-up audit entry was appended after the first generation). Failed generations (FR-055) are retriable: the failed `v{N}` blob is overwritten on retry until success, then `generation_seq` is committed to Cosmos.

**Rationale**:

- Compliance cohort: 7-year retention per state records legislation (NSW State Records Act 1998, Public Office GDA23 archival authority). Blob immutable storage with time-based policy is the strongest compliance posture.
- Data Engineer cohort: multi-hour exercises can produce 10–50 MB Exercise Outcome Records (timeline + all sub-agent invocations + cascade audit). Cosmos's 2 MB document limit is insufficient.
- Separation of concerns: Cosmos for queryable metadata; Blob for immutable archival.

**Alternatives considered**:

- *All-Cosmos* — fails on 2 MB doc limit; rejected.
- *All-Blob (no index)* — non-queryable; cannot answer "list all exercises completed last week"; rejected.

**Cost impact**: Blob WORM LRS at AU$0.02/GB/month + immutable storage policy fee (no additional charge in AU East). Cosmos `exercise_outcome_index` low-RU (fixed 400 RU/s) ~AU$25/month.

---

### 1.8 — FR-059 `abort` verb surface

**Decision**: **Direct REST endpoint `POST /api/simulations/{simId}/abort`** bypassing the LLM tool-loop. `pause` / `resume` are exposed both as `TOOL_SCHEMAS` entries (LLM-accessible for chat-flow ergonomics) AND as direct REST endpoints (for UI button surface). Codified in **ADR-036-002**.

**Rationale**:

- Architecture cohort (Solution Architect, API Architect, Principal Engineer): `abort` is a coordinator override surface that must be **immune to LLM jailbreak or confusion** (Constitution I — primacy of life). A direct REST endpoint is the simplest way to guarantee that.
- `pause` / `resume` are reversible; if the LLM mistakenly issues `pause`, the coordinator can `resume`. So LLM-tool exposure is acceptable — and ergonomic for chat-driven workflows.
- The direct REST endpoint enables immediate `asyncio.Task.cancel()` on stored task references, writes `sub_agent.cancel` audit entries for each in-flight invocation, transitions the sim to `ended` with `end_reason: aborted`, and triggers FR-054 lessons-capture automatically.
- Both REST and tool-schema paths converge to the same server-side handler for `pause` / `resume` so behaviour is identical regardless of caller.

**Endpoint contract** (full schema in [contracts/openapi-simulation.yaml](./contracts/openapi-simulation.yaml)):

```yaml
POST /api/simulations/{simId}/abort
  auth: AAD JWT, Simulation.Coordinator role required
  request: { reason?: string }
  response 200: { aborted: true, cancelled_invocations: integer, lessons_capture_started: true }
  response 403: Problem Details — role required
  response 409: Problem Details — sim not in cancellable state
```

**ADR-036-002**: Documented in `docs/adr/ADR-036-002-abort-direct-rest.md`. Reviewed by Solution Architect, API Architect, Security Engineer.

---

### 1.9 — Signal freshness windows per category

**Decision**: Defined in `apps/api/app/config/signal_freshness.py` as a single Pydantic `Settings` object (also drives Cosmos TTL hint and computed `stale` flag):

| Category | Freshness window | FR-028/029 SLA target | Window-to-SLA ratio |
|---|---|---|---|
| `weather` | **5 min** | ≤ 10 s | 30× |
| `fire-behaviour` | **5 min** | ≤ 15 s | 20× |
| `hydrology` | **10 min** | ≤ 15 s | 40× |
| `geohazard` | **5 min** | ≤ 10 s | 30× |
| `utility` | **15 min** | ≤ 15 s (cascade ≤ 30 s) | 60× |
| `transport` | **15 min** | ≤ 15 s (cascade ≤ 15 s) | 60× |
| `evacuation` | **10 min** | ≤ 15 s | 40× |
| `resource` | **30 min** | ≤ 15 s | 120× |
| `comms-channel-state` | **10 min** | ≤ 10 s (cascade ≤ 10 s) | 60× |

**Rationale**:

- Window must be substantially larger than the SLA so that overlay-update SLA misses don't trigger immediate staleness flags.
- Life-safety categories (`weather`, `fire-behaviour`, `geohazard`) get the tightest 5-minute windows because their downstream Risk-Assessment fan-out is most sensitive to staleness.
- Resource signals get the longest 30-minute window because resource availability changes more slowly in real exercises.
- Cosmos TTL hint = freshness_window × 6 (e.g. 30 min for weather, 90 min for resource) — enough headroom for replay scenarios; final retention controlled by container-level TTL of 72 h (per Data Engineer cohort).

**Alternatives considered**:

- *Single window for all categories* — too coarse; rejected.
- *Configurable per-tenant* — complexity not warranted for MVP; deferred to post-MVP if cohort demand emerges.

---

### 1.10 — FR-058 audio rendering surface

**Decision**: **Azure AI Speech Services TTS** in AU East (no Foundry carve-out invoked) renders the body of the warning artefact at the **time the warning is composed** by the Communication agent. The bilingual spoken prefix (`SIMULATION — DO NOT DISTRIBUTE` in English, then locale spoken prefix) is **pre-rendered offline** for each supported locale, with the static MP3s stored in a version-controlled `audio-prefix-table` Blob (`tts-audio-artefacts/audio-prefix/{locale}.mp3`). At runtime the Communication agent concatenates the pre-rendered English prefix MP3 + the pre-rendered locale prefix MP3 + the body MP3 into a single artefact stored in `tts-audio-artefacts/sim/{sim_id}/{warning_id}.mp3`. Web client plays via `<audio controls>` element backed by a signed-URL through Web Audio API.

**Rationale**:

- FR-058 explicitly forbids LLM-generated TTS of LLM-translated strings (zero translation drift on the audio pathway). The pre-rendered prefix store is the only compliant pattern.
- Azure AI Speech Services in AU East has neural voices for ~30 CALD languages relevant to AU emergency communications (Vietnamese, Mandarin, Arabic, Auslan-narrative voice-over, etc.) — covers the spec 024 watermark-governance scope.
- No Foundry carve-out needed: Speech Services is available in AU East.
- Signed-URL pattern keeps audio artefacts inside the simulation tenant scope (the URL is generated with a 5-minute TTL by the API on demand and is keyed to the requesting coordinator's token).
- Accessibility cohort: `<audio controls>` element is screen-reader-friendly with NVDA/VoiceOver; the bilingual prefix is also surfaced as a transcript on the warning preview UI.

**Static asset governance**: The 30 prefix MP3s are committed to `data/audio-prefix-table/` as part of the watermark-governance PR process. Each entry: locale code, voice ID, source string (canonical English or locale string), MP3 file. Adding/changing entries requires Communication-agent owner + Compliance Auditor approval per spec 024 watermark governance.

**Alternatives considered**:

- *Runtime LLM TTS for prefix + body* — forbidden by FR-058; rejected.
- *Runtime Speech Services TTS for prefix and body* — works for body but the prefix must be pre-rendered (audio-prefix-table is the spec mandate); we use Speech for body only and pre-render prefixes.
- *Inline `<audio src="data:audio/mp3;base64,...">`* — bloats the HTML payload; rejected.

**Cost impact**: Speech Services in AU East at AU$25/M characters; estimated <AU$10/month at MVP load. Blob storage for pre-rendered prefixes ~5 MB per locale × 30 locales = 150 MB total at AU$0.02/GB/month → <AU$1/month.

---

### 1.11 — Azure OpenAI TPM quota sizing

**Decision**:

| Deployment | Region (preferred → carve-out fallback) | TPM quota requested | Worst-case load |
|---|---|---|---|
| `gpt-4o-mini` | `australiaeast` → `eastus2` | **150K TPM** | 5 sub-agents (Telemetry-Inj, Comms, Planning, Resource Allocation, Monitoring) × 5 threads × 3 sims × 1.5K input + 500 output tokens / 30s = ~85 K TPM peak; 30 % headroom = 110 K → request 150K |
| `gpt-4o` | `australiaeast` → `eastus2` | **100K TPM** | 2 sub-agents (Risk Assessment, Evacuation) × 5 threads × 3 sims × 2K input + 1K output / 30s = ~75 K TPM; 30 % headroom = 100 K |

**Rationale**:

- Worst case: 3 concurrent simulations per tenant × 5 hazard threads × 6 sub-agents = 90 concurrent LLM calls per tenant. Multi-tenant scenario at MVP is up to 3 tenants concurrently → 270 concurrent LLM calls peak.
- Typical input: 1.5 K tokens (spec 024 prompt + signal context); output: 500 tokens (`gpt-4o-mini`) or 1 K tokens (`gpt-4o`).
- Per-deployment 429 monitoring + circuit-breaker on `RateLimitError` → degrade to FR-053 `degraded` reply tag (Constitution V graceful degradation).
- Foundry carve-out: AU East quota for `gpt-4o` is historically constrained at peak; if AU TPM cannot be obtained at 100K, fallback to `eastus2` is documented in `infra/foundry-carve-out-registry.yml` per Constitution v1.2.0 §Non-Negotiable #2. Only the model endpoint moves; all data persistence (audit, signals, exercise outcome) stays in AU East.

**Throttling / degradation behaviour**:

1. `429` from Azure OpenAI → `tenacity` retries with exponential backoff (existing pattern) up to 3 attempts.
2. After 3 failed retries → sub-agent reply is marked `degraded=True` with `error="rate_limit_exhausted"`; chat reply attributes degradation to the affected sub-agent.
3. SRE alert fires at 80 % TPM utilisation for 5 minutes (warning) and 95 % for 1 minute (SEV-3).

**ADR-036-003**: Foundry carve-out registry entry documented in `infra/foundry-carve-out-registry.yml`. Reviewed by Solution Architect + Security Engineer.

---

### 1.12 — Sub-agent LLM models

**Decision**: per architecture cohort strong consensus.

| Sub-agent | Model | Rationale |
|---|---|---|
| `simulation-telemetry-injection` | **`gpt-4o-mini`** with Azure OpenAI `response_format: {"type": "json_schema", "json_schema": {…, "strict": true}}` | Bounded structured output; 9 known signal categories; cost-effective at ~10× cheaper than gpt-4o; latency advantage critical for ≤ 5 s parse-to-pipeline target. |
| `risk-assessment` | **`gpt-4o`** | Complex multi-factor reasoning (cascading-consequence modelling, impact prediction, hazard minimisation across multi-hazard threads). |
| `evacuation` | **`gpt-4o`** | Geographic reasoning (route re-planning, shelter capacity allocation). |
| `communication` | **`gpt-4o-mini`** | Template-heavy; AWS warning composition is structured. |
| `planning` | **`gpt-4o-mini`** | IAP drafting follows AIIMS template. |
| `resource-allocation` | **`gpt-4o-mini`** | Optimisation logic is deterministic; LLM only for natural-language explanation. |
| `monitoring` | **`gpt-4o-mini`** | Summarisation of signal pipeline state. |

`json_schema` strict mode for telemetry injection guarantees the Pydantic `SyntheticSignalBatch` model validates without surprises. See [contracts/telemetry-injection-llm.md](./contracts/telemetry-injection-llm.md).

---

## 2. Existing-Pattern Reuse Analysis

| Component | Existing pattern reused | Net new code |
|---|---|---|
| **Sub-agent invocation glue** | `apps/api/app/services/simulation/sub_agent_invoker.py` `SubAgentFn`, `SubAgentReply`, `SubAgentInvoker.register()` interface — **interface unchanged** | `production_invoker()` factory + 6 adapter modules |
| **Controller orchestration** | `apps/api/app/services/simulation/controller_service.py` — Tool-loop, `_execute_tool`, SSE streaming via `_stream_from_azure` | Add `inject_telemetry` tool handler; extend audit-writer dependency injection; add session-token propagation |
| **Tool schema + allow-list** | `apps/api/app/services/simulation/controller_tools.py` — `TOOL_SCHEMAS`, `ALLOW_LIST` | Add `inject_telemetry` tool; add `pause`, `resume`, `abort` to allow-list (also direct REST) |
| **Rate limiter** | `apps/api/app/services/simulation/rate_limiter.py` — existing 30-injections/min budget | Modify to count **only successful** injections (FR-009); new `ParseAttemptCircuitBreaker` class as sibling |
| **Signal envelope schema** | `packages/schemas/signal-envelope.schema.json` — existing live-tenant schema | Extend with `simulation` block (FR-009 provenance fields) |
| **Synthetic delivery** | `apps/api/app/services/simulation/synthetic_delivery_service.py` — existing `[SIMULATION] ` prefix scaffolding | Extend receipt envelope (FR-036 fields); wire bilingual watermark + audio prefix |
| **Audit infrastructure** | spec-024 audit pipeline (Cosmos change feed → Blob immutable archive) | Add 11+ new typed audit entry schemas; extend with `prompt_hash` field for LLM-bearing records |
| **Sub-agent runtime modules** | `apps/agents/{monitoring,planning,risk_assessment,communication,evacuation,resource_allocation}/` — existing runtimes | Add `simulation_telemetry_injection/` sibling; extend `risk_assessment/` with `handle_signal_event()` for FR-026 fan-out |
| **OPA tenant isolation** | `infra/policies/tenant-isolation.rego` — existing | Extend rules to cover sim-injection citation checks and sim-partition isolation |
| **Foundry carve-out registry** | spec 024 / spec 029 carve-out list precedent | Add 2 model deployments + 1 review-date entry |
| **AVM Bicep modules** | Existing pattern: pinned versions, modules under `infra/bicep/modules/` | Add 5 new modules; modify `main.bicep` to wire them |
| **CI quality gates** | `.github/workflows/ci.yml` — existing lint/test/integration gates | Add `simulation-stub-sweep`, `simulation-egress-sweep` hard gates; add on-demand `simulation-load-test.yml` |
| **Map overlay rendering** | `apps/web/src/components/simulation-map.tsx` — existing GeoJSON layer rendering | Add SSE event handlers for `map.overlay.*`; add SIM-badge / stale-badge / cluster overlay visuals |
| **Chat pane rendering** | `apps/web/src/components/simulation-chat-pane.tsx` — existing chat surface | Add `[SIMULATION] ` badge component; add `InjectionConfirmCard` / `InjectionRefusalCard` rendering |
| **Domain models** | `packages/domain/src/domain/models/` — existing Pydantic v2 patterns | 6 new models (Synthetic Signal, Sub-Agent Invocation Record, Synthetic Delivery Receipt, Routing Decision, Exercise Outcome Record, Telemetry-Injection Audit Entry) |

**Net new code estimate**: ~3 K Python LOC (backend), ~600 TypeScript LOC (frontend), ~600 Bicep LOC (infra), ~1.5 K test LOC. Plus 1 ADR file × 4 = 4 ADRs.

---

## 3. Risk Register

| # | Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|---|
| 1 | Cosmos `Consistent-Prefix` default fails FR-015 read-your-own-write under high concurrency | High | Medium | ADR-036-001 escalates to Session consistency; integration test `test_inject_then_fanout.py`; fallback Redis pub/sub design is documented for post-MVP if needed |
| 2 | LLM hallucinated agent name routes to non-existent sub-agent | High | Medium | Server-side `ALLOW_LIST` in `controller_tools.py`; unknown-agent refusal recorded in audit; static `agent-routing-table.yaml` (LLM never selects combat agency) |
| 3 | Foundry carve-out region exhausts model TPM quota at peak load | Medium | Low | TPM headroom 30 %; per-deployment 429 monitoring → degrade to `degraded` reply tag (FR-053); both regions registered in carve-out registry |
| 4 | Cascade depth-2 silently propagates and blows the FR-052 thread cap | Medium | Low | `CascadeOrchestrator` enforces depth-1 ceiling at the source; `origin_cascade_id` is non-transitive; integration test asserts depth-2 attempts produce a typed audit refusal |
| 5 | Bilingual watermark drift on a missing locale (LLM fallback) breaks SC-006 byte-match | High | Low | Hard-coded server-side guard rejects any watermark string produced via an LLM endpoint; missing-locale falls back to English-only + `audit.watermark.locale_missing` (text + audio variants) |
| 6 | Map overlay capacity overflow (very large polygons) silently drops geometry | Medium | Medium | FR-034 enforces clustering / down-sampling for render; underlying signal payload preserved in audit; cluster indicator visually rendered |
| 7 | PII leaks into `prompt_hash` pre-image audit records | High | Medium | Azure AI Content Safety + rule-based PII scrubber pre-LLM; audit-export pathway access-controlled to `Simulation.Coordinator` or `Auditor` Entra ID role only |
| 8 | Race condition: Telemetry-Injection writes to Cosmos but Event Hubs publish fails | Medium | Low | Outbox pattern: write to Cosmos with `published: false`, then publish to Event Hubs, then update `published: true`. Repair worker reconciles unpublished entries. (Existing pattern from spec 028.) |
| 9 | OPA policy bundle desynchronised from app deployment (citation checks bypass) | High | Low | OPA policy bundle versioned in same repo, deployed via same CI/CD as Container Apps; CI gate `opa test infra/policies/` blocks merges with policy errors |
| 10 | `simulation-stub-sweep` CI gate is skipped due to fork-PR permissions | Medium | Low | Required workflow check enforced via repo settings; cannot be bypassed by fork PRs |
| 11 | Container App SIGTERM during `abort` mid-cascade orphans sub-agent invocations | Medium | Low | `terminationGracePeriodSeconds: 150` (≥ FR-006 hard timeout); `uvicorn --graceful-timeout 120`; `httpx.AsyncClient` per-call cancellation on SIGTERM with `sub_agent.cancel` audit entry |
| 12 | Multi-coordinator concurrent injection of contradicting signals leaves an unresolved contradiction tag | Low | Medium | FR-013 requires `contradicts: <prior_signal_id>` tag; downstream sub-agents re-run on each; coordinators are notified — no silent resolution |

---

## 4. Cost Envelope (rough monthly estimate, AU$, MVP load)

| Resource | SKU / sizing | Monthly cost (AU$) |
|---|---|---|
| Azure OpenAI `gpt-4o-mini` (150K TPM, AU East, ~5M tokens/month MVP load) | Standard tier | ~$120 |
| Azure OpenAI `gpt-4o` (100K TPM, AU East, ~2M tokens/month MVP load) | Standard tier | ~$200 |
| Azure AI Speech Services TTS (AU East, ~5 min audio/month) | Neural voice, pay-as-you-go | <$10 |
| Azure AI Content Safety (AU East, ~10K text scans/month) | Standard, pay-as-you-go | <$30 |
| Cosmos DB containers (3 new): `simulation_synthetic_signals` (autoscale 400–4000 RU/s avg ~800), `sub_agent_invocation_records` (autoscale 400–4000 avg ~600), `exercise_outcome_index` (fixed 400 RU/s) + `simulation_threads` doc-per-sim | Existing account; autoscale on the two new containers | ~$120 |
| Azure Event Hubs Standard, 4 new consumer groups | Existing namespace; consumer groups are free | $0 |
| Azure Blob Storage (3 new containers) — `exercise-outcome-records` (LRS, WORM, ~10 GB at MVP), `jurisdiction-boundaries` (~5 MB), `tts-audio-artefacts` (LRS, ~500 MB at MVP) | Existing storage account; cost is hot-tier $0.02/GB | ~$5 |
| Container App scaling delta (`apps/agents` max replicas 2 → 3) | Dedicated workload, marginal | ~$60 |
| Application Insights custom metrics (3 new SLIs) + alerts | Existing workspace; usage-based | <$10 |
| Azure Cache for Redis (existing C1, additional namespace usage) | Existing | $0 |
| Azure API Management policy update | Existing instance; policy update is free | $0 |
| **Total marginal cost** | — | **~$555 / month** |

**Notes**:

- LLM cost is the dominant marginal driver (~58 % of total). Foundry carve-out fallback to `eastus2` would not change the AUD cost materially.
- Cost scales linearly with simulation volume; MVP assumes ~10 simulation hours/month per tenant × 3 active tenants. Tripling load → ~$1100/month.
- Compliance overhead (WORM, immutable storage policy) adds <$5/month.

---

## 5. ADRs (full list)

| ADR | Title | Status | Approver |
|---|---|---|---|
| **ADR-036-001** | Cosmos DB Session consistency on `simulation_synthetic_signals` (escalation from `Consistent-Prefix`) | Accepted | Solution Architect + Compliance Auditor |
| **ADR-036-002** | Direct REST endpoint for `abort` (bypassing LLM tool-loop) | Accepted | Solution Architect + API Architect + Security Engineer |
| **ADR-036-003** | Azure OpenAI Foundry carve-out registry — 2 new model deployments | Accepted | Solution Architect + Security Engineer |
| **ADR-036-004** | PSPF classification for simulation exercise records (default OFFICIAL; OFFICIAL:Sensitive on personnel data) | Accepted | Compliance Auditor + Security Engineer |
| **ADR-036-005** | Cascade ETag optimistic concurrency for `simulation_threads` thread-cap | Accepted | Data Architect + Backend Engineer |
| **ADR-036-006** | Lessons-capture Blob WORM (7-y immutability, time-based retention) | Accepted | Compliance Auditor + Solution Architect |
| **ADR-036-007** *(NEW — amendment cycle)* | Distributed gap-free audit sequence allocator (Cosmos ETag conditional replace) | Accepted | Solution Architect + Data Engineer + Compliance Auditor + Principal Engineer |
| **ADR-036-008** *(NEW — amendment cycle)* | SLI threshold rationale and measurement methodology | Accepted | SRE Engineer + Solution Architect + QA/Test Engineer + Principal Engineer |
| **ADR-036-009** *(NEW — amendment cycle)* | Idempotency-cache design (Cosmos + RFC 8785 body hashing) | Accepted | API Architect + Solution Architect + Security Engineer + Compliance Auditor |

ADR files live under `docs/aidr/decisions/` (the spec-036 amendment cycle confirmed this canonical location, sibling to existing AIDR exercise summaries; the earlier-draft `docs/adr/` reference has been corrected).

---

## 6. Amendment-cycle research (Step 8 cohort review, 2026-05-08)

The Step 8 cross-cohort review (85 personas) returned **RE-LOOP** with 19 amendments (A–S, see `spec.md` § "Step 8 Amendment Log"). The amendments introduced six implementation-trade-off topics that did not appear in the original 12 trade-offs above. This section records the research that resolved those new topics. Each subsection corresponds to one or more new plan-decisions (numbered 13–20) in `plan.md`.

### R-13 — Distributed sequence allocator analysis (decision 13 / FR-048 / Amendment D)

**Question**: Which mechanism is production-safe for `sequence_number` allocation across multiple `apps/api` Container App replicas, given that the Step 8 review confirmed the current allocator is a process-local Python dict (`audit_writer.py:44-47, 75-81`) and is therefore unsafe under `minReplicas: 1, maxReplicas: 3` scaling?

**Options analysed**:

- **(A) Cosmos ETag conditional replace** on a per-simulation counter document (`simulation_audit_sequence_counter/{sim_id}` in NEW container `simulation_audit_sequence_counters`).
- **(B) Cosmos stored procedure** (server-side JavaScript transaction).
- **(C) Single-writer constraint with replica-affinity routing** (Container Apps revision pin or KEDA-anchored partition).

**Pros / cons**:

| Option | Pros | Cons | Cosmos consistency interaction |
|---|---|---|---|
| (A) ETag conditional replace | Native Cosmos pattern; reuses ADR-036-005 ETag design (one allocator concept); pure Python implementation; deploys with the app code | One extra round-trip (read counter + conditional replace) per audit write (~5 ms) | Works correctly under any consistency level (Consistent-Prefix is sufficient because the ETag is the atomic guarantee, not the read consistency) |
| (B) Stored procedure | Atomic in one round-trip | Out-of-band deploy; no Python typing; ops liability; sproc max 5 s | Sproc transactions are scoped to a single partition — same partition key as ETag option |
| (C) Replica-affinity routing | Zero per-write overhead | Conflicts with KEDA HTTP scaler even-distribution; brittle on revision rollover; spec-required regression test would have to prove affinity holds under traffic re-balance | Bypasses Cosmos consistency entirely (single writer guarantees it) |

**Decision**: **Option (A)**. Codified as **ADR-036-007**. Rationale: reuse of ADR-036-005's ETag pattern means the team has one atomic-counter concept to operate; rejecting (B) avoids out-of-band Cosmos deploys; rejecting (C) avoids fighting KEDA's scheduling.

**Cosmos consistency-model interaction note**: The counter document is read with the account default (Consistent-Prefix) but written with `If-Match: <etag>`. Two replicas reading the same `_etag` simultaneously will both compute the same `proposed = current_sequence + 1`, but only one `replace_item` succeeds; the other receives `412 Precondition Failed` and retries with a fresh read. Worst-case retry budget under this ADR is **5 attempts × 50 ms exponential back-off + jitter ≈ 1.55 s**, bounded so it does not exceed FR-009's 5 s parse-to-pipeline budget. On retry exhaustion the writer fails closed (HTTP 503 + dead-letter to `simulation_audit_dlq` per the SC-001 fail-closed protocol).

**Test approach**: property-based concurrency test (`tests/contract/test_audit_sequence_etag_concurrency.py`) launches 50 concurrent allocators against an in-memory Cosmos emulator and asserts (a) every returned sequence number is unique, (b) the set is dense `[1..50]` (no gaps), (c) the total wall-clock time is bounded by the retry envelope.

---

### R-14 — RFC 9457 problem-detail patterns (decisions 13 + 15 / FR-066 / Amendment S)

**Question**: How should the four direct-REST lifecycle endpoints surface the new `lifecycle-state-conflict`, `idempotency-key-conflict`, `injection-refused`, and `evidence-integrity-warning` error families in a way that is consistent with FastAPI conventions and discoverable to non-Python clients?

**Resolution**:

- **Standard adopted**: **RFC 9457** (the 2024-published successor to RFC 7807; supersedes RFC 7807 with extension fields and ABNF clarifications). The platform's earlier `application/problem+json` MIME type is unchanged.
- **Type URI convention**: `https://api.platform.example.gov.au/problems/<error-name>` — stable URIs that resolve to the human-readable error catalogue (one Markdown page per `type` under `docs/disaster-response-hub/error-catalogue/`). The URI is the canonical discriminator across all clients.
- **Status mapping**:
  | `type` URI | HTTP status | Where raised |
  |---|---|---|
  | `lifecycle-state-conflict` | 409 | FR-066 idempotency cache hit + state-machine consumption mismatch (decision 15) |
  | `idempotency-key-conflict` | 422 | FR-066 same-key + same-route + DIFFERENT body-hash (decision 15) |
  | `injection-refused` | 400 / 429 | FR-009 / FR-010 / FR-052 / FR-057 refusals (existing) |
  | `evidence-integrity-warning` | n/a (warning header on 200/2xx) | FR-049 / FR-054 export pathways when `sequence_number = -1` DLQ entries are detected (decision 13 fail-closed) |
- **FastAPI integration**: a single `ProblemDetailException(status_code, type_uri, title, detail, instance, **extensions)` exception class is registered with FastAPI's `app.exception_handler(ProblemDetailException)` to render `application/problem+json` responses. The handler also sets the OpenTelemetry `exception.type` attribute to the URI for trace correlation. RFC-9457-compliant extensions (`reason`, `category`, `confidence`, `idempotency_key`, `body_hash_attempted`) are flat top-level fields per RFC § 3.2.
- **OpenAPI advertisement**: `contracts/openapi-simulation.yaml` references `#/components/schemas/ProblemDetails` on every error response (already present); the new `lifecycle-state-conflict`, `idempotency-key-conflict`, and `evidence-integrity-warning` types are advertised in NEW `contracts/error-responses.md` (this amendment cycle).
- **Content negotiation**: clients that send `Accept: application/json` (not `Accept: application/problem+json`) still receive `application/problem+json` per RFC 9457 § 4 (the more-specific media type wins). The body shape is unchanged.

**Backwards compatibility**: Existing 4xx responses returning bare JSON (e.g. simulator scaffolding endpoints not in scope for FR-066) continue to work; the new RFC 9457 surfaces are limited to the four FR-066 lifecycle endpoints + the FR-049 export.

---

### R-15 — RFC 8785 JSON Canonicalisation Scheme (decision 15 / FR-066 / FR-060)

**Question**: Which canonicalisation algorithm should compute the body hash for FR-066 idempotency-key conflict detection, given that the `prompt_hash` (FR-060) already uses Python `hashlib.sha256` over `json.dumps(..., sort_keys=True, separators=(",", ":"))`? Can the same canonicaliser be used for both?

**Resolution**:

- **Standard chosen**: **RFC 8785 — JSON Canonicalisation Scheme (JCS)**. RFC 8785 is an IETF Standards-Track RFC published 2020 and is the only published canonicaliser that has reference implementations in multiple languages (`canonicaljson` in Python, `@truestamp/canonify` in TypeScript, `jcs` in Go), enabling external auditors to verify `prompt_hash` and `body_hash` byte-for-byte.
- **Implementation choice**: `canonicaljson` (PyPI) — pure-Python, RFC 8785 conformance test suite passes (verified locally during research). Frozen-dependency entry to be added in `pyproject.toml` at task time.
- **Rejected alternative**: stdlib `json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)`. It is **not** RFC 8785 conformant for floating-point numbers: stdlib emits `1.0` for `1.0`, but RFC 8785 mandates `1` (ECMAScript `ToString(Number)` → `"1"`); stdlib emits `1.5e-10`, RFC 8785 mandates `0.00000000015`. Because FR-066 body hashing must be conflict-detecting across heterogeneous clients (TypeScript, Go, Python), stdlib's float divergence would produce false 422s. The same RFC 8785 canonicaliser is therefore back-ported to FR-060 `prompt_hash` to keep one canonicaliser concept across all hashes.
- **Test vectors**: `tests/contract/test_rfc8785_canonical_json.py` (NEW) verifies all RFC 8785 § 3.2 test vectors — empty object, trailing zeros in numbers, nested arrays, unicode escapes (BMP and supplementary planes), boolean/null literals, embedded surrogates.
- **Migration note**: existing `prompt_hash` values written under the stdlib canonicaliser MUST be re-hashed at the FR-060 amendment cut-over. The migration script (`tools/rehash_prompt_hashes.py`, NEW) reads the canonical pre-image from the `request_payload` field on `sub_agent_invocation_records` and re-emits the hash via `canonicaljson`. This is gated by a feature flag `PROMPT_HASH_CANONICALISER=rfc8785` (default `legacy` until the flag flip).

**Performance**: `canonicaljson` benchmarks at ~50 µs / kB on the Sub-Agent Invocation Record payload sizes observed in `apps/api/tests/test_compute_prompt_hash.py` — negligible relative to the LLM call itself.

---

### R-16 — SLI measurement methodology (decision 14 / FR-063 / Amendment P)

**Question**: How should the five FR-063 SLIs be measured in Application Insights / Log Analytics without dimensional explosion or biased life-safety sampling?

**Resolution**:

- **Custom-events backbone**: every SLI emits a typed `customEvents` row at the boundary that defines its observable. Names (one per SLI):
  - `inject_telemetry.fan_out_complete` (SLI-1)
  - `audit.sequence_number.allocated` + scheduled gap-detector (SLI-2)
  - Locust load-test exporter (SLI-3 — not Application Insights; see ADR-036-008)
  - `sse.map_overlay.delivered` (SLI-4)
  - `sub_agent.invocation.complete` (SLI-5; reuses an existing event from spec 024)
- **KQL query templates**: one per SLI, embedded in `contracts/sli-thresholds.md` (NEW) and ADR-036-008. Bound by **`bin(timestamp, …)` time aggregation** to avoid scanning the full table on every alert evaluation.
- **Dimension cardinality control**:
  - SLI-1 / SLI-4 / SLI-5 split by `tenant_id` (cap 50) and `sub_agent` / `model_deployment` only. **`sim_id` is intentionally NOT a split dimension** — at MVP load (3 active sims × 3 tenants) it is bounded, but at scale it would explode App Insights cost. SLO breach drill-downs query the underlying events in 5-minute hot windows.
  - SLI-2 has no split dimension (it is a sim-level invariant; one alert per simulation_id when a gap is detected).
  - SLI-3 dimensions are the Locust user class and signal category (cardinality 9 categories × 1 user class).
- **Sample rate**:
  - **100 % server-side** for all five SLIs (no sampling — life-safety relevance).
  - **10 % client-side telemetry** for SLI-4 (only the `client_received_ms` source, which is an opportunistic measurement). Server-side `server_emit_ms` is 100 %.
  - The Application Insights `samplingPercentage` on the resource is set to **100** (overrides the workspace default of 5) for the `simulation-*` operation names, configured in `infra/bicep/modules/observability-alerts.bicep`.
- **Bias avoidance for life-safety observations**: since 100 % sampling is in effect for all five SLIs, there is no risk of life-safety chat turns being dropped from the observable population.
- **Alert rules**: ARM template referenced from `infra/bicep/modules/observability-alerts.bicep` defines five `Microsoft.Insights/scheduledQueryRules` (one per SLI) with the warn/breach thresholds from ADR-036-008. PagerDuty integration via existing Action Group `ag-sim-sre-prod`.

**Open question deferred to tasks phase**: whether to use **Azure Monitor Workbooks** for SLI dashboards (single workspace, no extra cost) or **Grafana Managed Service** (richer visuals, ~AU$15/month). Defaulting to Workbooks; revisit if SRE cohort requests Grafana.

---

### R-17 — ARIA live-region patterns for SSE (decision 18 / FR-064 / Amendment Q)

**Question**: What is the correct ARIA pattern for an SSE-driven live log such that screen-reader users receive parity with sighted exercise control, without double-announcement and without interrupting urgent banner alerts?

**Resolution** (cross-referenced with WAI-ARIA Authoring Practices Guide § 4.6 and W3C ARIA 1.2 Recommendation):

- **Container element**: `<section role="log" aria-live="polite" aria-relevant="additions" aria-atomic="false" aria-labelledby="simulation-live-log-heading">`. The `role="log"` is the canonical landmark for chronological updates (chat, console output, progress logs); it implies `aria-live="polite"` by default but the explicit attribute is included for browsers with imperfect implicit support.
- **`aria-live="polite"` over `assertive`**: assertive is reserved for urgent, time-critical alerts (e.g. AWS Emergency Warning banner — handled separately by `apps/web/src/components/simulation-banner.tsx` with `role="alert"`, already present). `polite` waits for the screen reader to finish its current utterance, avoiding interruption of coordinator navigation.
- **`aria-relevant="additions"`**: announces only newly-added DOM nodes; the existing transcript is NOT re-announced when re-rendered. Critical for double-announcement avoidance.
- **`aria-atomic="false"`**: only the changed subtree is announced, not the entire log.
- **Visually-hidden landmark heading**: `<h2 id="simulation-live-log-heading" class="sr-only">Simulation chat live log</h2>` — gives screen-reader landmark navigation and a programmatic name.
- **De-duplication**: the SSE handler keys appended log entries by SSE event id. Re-deliveries on reconnect skip already-rendered entries (the React component memoises by event id). Without this, reconnect-on-network-flap would announce the same content twice.
- **Locale resolution**: the same `packages/domain/src/domain/sim_locale_table.json` consumed by the FR-058 audio-prefix pathway. 3-step fallback `request_locale → jurisdiction_priority_locale → en_AU`.
- **`[SIMULATION]` prefix**: rendered as the leading text node in every log entry, present in BOTH the visible content and the announced text (so screen-reader users hear "SIMULATION" prefix on every entry, matching the visible visual treatment).
- **Polite-vs-assertive selection rubric**: the live log is `polite`. The simulation banner (which fires on AWS Emergency Warning tier signals) is `assertive`. There is exactly one assertive region per page at any time, per WAI-ARIA APG.

**Test obligations** (covered in `apps/web/tests/a11y/`):

- `vitest` unit test verifying the `role="log"` + `aria-live="polite"` + `aria-relevant="additions"` attribute set is correct.
- `@axe-core/playwright` integration test verifying NO axe-core landmark violations and NO duplicated-id violations.
- Manual NVDA/VoiceOver smoke test in the Step 7 implementation phase (recorded in QA cohort sign-off).

---

### R-18 — AIIMS doctrine references (decision 17 / FR-061 / Amendment A)

**Question**: What is the authoritative source for the canonical AIIMS function-to-sub-agent mapping codified in `packages/domain/src/domain/aiims_mapping.py`?

**Resolution**:

- **Primary source**: **Australasian Inter-service Incident Management System (AIIMS) 4th Edition (2017)** — published by the Australasian Fire and Emergency Service Authorities Council (AFAC). Specifically:
  - § Function Roles: defines the six core functions — **Control, Operations, Logistics, Intelligence, Planning, Public Information**.
  - § Functional Diamond (the AIIMS functional structure diagram).
  - § "Public Information" (responsible for **external community warnings** + **public-facing communications**) — drives the Communication-agent → Public Information primary mapping.
  - § "Operations" (responsible for **internal tactical comms** + **on-scene coordination**) — drives the Communication-agent secondary `Operations` tag.
- **Secondary source — state Emergency Management Acts** (used to confirm jurisdiction-specific doctrine alignment):
  - NSW: *State Emergency and Rescue Management Act 1989*.
  - VIC: *Emergency Management Act 2013*.
  - QLD: *Disaster Management Act 2003*.
  - WA: *Emergency Management Act 2005*.
  - SA: *Emergency Management Act 2004*.
  - TAS: *Emergency Management Act 2006*.
  - NT: *Disaster Management Act 2010*.
  - ACT: *Emergencies Act 2004*.
- **Cross-reference into `aiims_mapping.py`**: the module's docstring cites both AIIMS 4 (2017) § "Function Roles" AND each state Act § "Functional Roles" (where present). The mapping resolves doctrine + jurisdiction-specific naming variations (e.g. NSW's "Emergency Operations" maps to AIIMS Operations; QLD's "Public Information & Warnings" maps to AIIMS Public Information).
- **Resolution of dual-AIIMS sub-agents** (per Step 8 amendment pass 1 Q4):
  | Sub-agent | Primary AIIMS function | Secondary tags | AIIMS doctrine basis |
  |---|---|---|---|
  | Communication | Public Information | [Operations] | AIIMS § "Public Information" owns external warnings; § "Operations" owns internal tactical comms |
  | Resource Allocation | Logistics | [Operations] | AIIMS § "Logistics" owns resource provisioning; § "Operations" owns tactical deployment |
  | Risk Assessment | Intelligence | [Planning] | AIIMS § "Intelligence" owns threat/risk assessment; § "Planning" owns forward planning |
  | Evacuation | Operations | [Public Information] | AIIMS § "Operations" owns evacuation execution; § "Public Information" owns evacuation messaging |
  | Monitoring | Intelligence | [] | AIIMS § "Intelligence" owns situational awareness |
  | Planning | Planning | [] | AIIMS § "Planning" — direct mapping |
  | Telemetry-Injection | Intelligence | [] | AIIMS § "Intelligence" — synthetic-signal classification is a form of situational-awareness intelligence |
- **Single-valued primary** preserves the FR-054 lessons-capture deterministic ordering invariant.

---

## 7. Outstanding NEEDS CLARIFICATION

✅ **None**. Spec's 21 Q→A clarifications across 5 sessions (3 original + 2 amendment passes — see `spec.md` § "Clarifications") resolved every architectural ambiguity. The original 12 plan-phase trade-offs and the 8 amendment-cycle decisions (decisions 13 → 20 in `plan.md`) are decisively committed. Phase-2 task generation can proceed via `/speckit.tasks`.

---

*Research notes complete 2026-05-08. Inputs: `cohort-tech-arch-ai.md` + `cohort-tech-qsoi.md` (original 12 trade-offs) + Step 8 cross-cohort review synthesis (`step8-synthesis.md`, 85 personas, amendments A–S, decisions 13–20). Reviewed against Constitution v1.2.0.*
