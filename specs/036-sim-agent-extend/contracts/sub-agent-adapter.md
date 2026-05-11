# Contract: `SubAgentFn` Interface (Real Sub-Agent Adapters)

**Feature**: 036 — Real Sub-Agent Invocation & Telemetry-Injection Agent
**Spec FRs**: FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-060
**Owning module**: `apps/api/app/services/simulation/sub_agent_invoker.py` (existing) + `apps/api/app/services/simulation/sub_agents/` (NEW)

This contract defines the interface every real sub-agent adapter MUST implement, the production registry factory, the timeout / error semantics, and the `prompt_hash` requirement.

---

## 1. Interface Definition

The existing type alias in `sub_agent_invoker.py` is **unchanged**:

```python
# apps/api/app/services/simulation/sub_agent_invoker.py
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

@dataclass
class SubAgentReply:
    sub_agent: str
    summary: str
    citations: list[str]
    degraded: bool = False
    error: str | None = None
    # NEW for feature 036 (FR-060):
    prompt_hash: str | None = None  # sha256 over canonical LLM prompt; None for non-LLM-bearing
    model_deployment: str | None = None  # e.g. 'gpt-4o-mini-australiaeast'
    sub_agent_invocation_id: str | None = None  # UUID — links to sub_agent_invocation_records doc

SubAgentFn = Callable[[str, str], Awaitable[SubAgentReply]]
# Signature: (tenant_id: str, question: str) -> Awaitable[SubAgentReply]
```

**Interface is unchanged** at the call-site level. The `SubAgentReply` dataclass gains 3 optional fields (`prompt_hash`, `model_deployment`, `sub_agent_invocation_id`) — backward compatible because they default to `None`.

---

## 2. Production Adapters (FR-001)

Each of the 6 real sub-agent adapters is a standalone async function in its own module under `apps/api/app/services/simulation/sub_agents/`:

| Adapter module | Sub-agent | LLM model | Citation source |
|---|---|---|---|
| `monitoring_adapter.py` | `monitoring` | `gpt-4o-mini` | Sim-tenant signal pipeline state |
| `planning_adapter.py` | `planning` | `gpt-4o-mini` | AIIMS IAP template + sim audit |
| `risk_assessment_adapter.py` | `risk-assessment` | `gpt-4o` | Sim-tenant signals + AIDR risk register |
| `communication_adapter.py` | `communication` | `gpt-4o-mini` | AWS warning templates + sim watermark tables |
| `evacuation_adapter.py` | `evacuation` | `gpt-4o` | Sim-tenant evacuation routes + jurisdiction registry |
| `resource_allocation_adapter.py` | `resource-allocation` | `gpt-4o-mini` | Sim-tenant resource state |

Each module exports exactly **one** function:

```python
# apps/api/app/services/simulation/sub_agents/risk_assessment_adapter.py
import httpx
from apps.api.app.services.simulation.sub_agent_invoker import SubAgentReply
from apps.agents.common.llm_mixin import compute_prompt_hash

async def invoke(tenant_id: str, question: str, *, http_client: httpx.AsyncClient) -> SubAgentReply:
    """Real Risk Assessment adapter (FR-001).
    
    Calls the agents Container App over async HTTP, captures prompt_hash from the
    sub-agent's reply (or computes it locally if the sub-agent does not supply it),
    enforces tenant-isolation on returned citations (FR-007), and returns a typed
    SubAgentReply.
    
    Raises asyncio.TimeoutError on FR-006 hard timeout (120s default).
    """
    started = monotonic()
    try:
        resp = await http_client.post(
            f"{AGENTS_BASE_URL}/risk-assessment/invoke",
            json={"tenant_id": tenant_id, "question": question, "session_token": _current_session_token()},
            timeout=httpx.Timeout(connect=5.0, read=120.0, write=5.0, pool=5.0),
            headers={"X-Sim-Tenant-Context": tenant_id, "traceparent": _current_traceparent()},
        )
        resp.raise_for_status()
        body = resp.json()
        # Tenant isolation per FR-007:
        bad = [c for c in body.get("citations", []) if not _is_sim_tenant_citation(c, tenant_id)]
        if bad:
            await audit.write("tenant_isolation.violation", violation_kind="citation_to_live_tenant", offending_resource_id=bad[0])
            return SubAgentReply(
                sub_agent="risk-assessment",
                summary=body.get("summary", ""),
                citations=[c for c in body.get("citations", []) if c not in bad],
                degraded=True,
                error="tenant_isolation_violation_filtered",
                prompt_hash=body.get("prompt_hash"),
                model_deployment=body.get("model_deployment"),
                sub_agent_invocation_id=body.get("invocation_id"),
            )
        return SubAgentReply(
            sub_agent="risk-assessment",
            summary=body["summary"],
            citations=body["citations"],
            prompt_hash=body["prompt_hash"],          # FR-060
            model_deployment=body["model_deployment"],
            sub_agent_invocation_id=body["invocation_id"],
        )
    except httpx.TimeoutException:
        raise asyncio.TimeoutError() from None
```

---

## 3. Production Invoker Factory

`sub_agent_invoker.py` exposes two factories:

```python
# apps/api/app/services/simulation/sub_agent_invoker.py

def default_invoker() -> SubAgentInvoker:
    """Stub adapters for offline/test mode. Used when SIM_CONTROLLER_MODE=stub."""
    inv = SubAgentInvoker()
    inv.register("monitoring", _stub("monitoring"))
    # ... 6 stub registrations using the literal trip-wire string until FR-002 migration removes them
    return inv

def production_invoker(http_client: httpx.AsyncClient) -> SubAgentInvoker:
    """Production adapters for live and simulation tenants. Used when SIM_CONTROLLER_MODE=production.
    
    Each adapter is wired to the corresponding agent service via async HTTP.
    """
    from apps.api.app.services.simulation.sub_agents import (
        monitoring_adapter, planning_adapter, risk_assessment_adapter,
        communication_adapter, evacuation_adapter, resource_allocation_adapter,
    )
    inv = SubAgentInvoker()
    inv.register("monitoring", lambda t, q: monitoring_adapter.invoke(t, q, http_client=http_client))
    inv.register("planning", lambda t, q: planning_adapter.invoke(t, q, http_client=http_client))
    inv.register("risk-assessment", lambda t, q: risk_assessment_adapter.invoke(t, q, http_client=http_client))
    inv.register("communication", lambda t, q: communication_adapter.invoke(t, q, http_client=http_client))
    inv.register("evacuation", lambda t, q: evacuation_adapter.invoke(t, q, http_client=http_client))
    inv.register("resource-allocation", lambda t, q: resource_allocation_adapter.invoke(t, q, http_client=http_client))
    return inv
```

Selection driven by env var `SIM_CONTROLLER_MODE` ∈ {`stub`, `production`}. Default is `stub` until the FR-002 migration ships (see [plan.md §Migration Plan](../plan.md#migration-plan-removing-the-fr-002-stub-string-trip-wire)).

---

## 4. Input Shape

```python
# (tenant_id: str, question: str) -> Awaitable[SubAgentReply]
#
# tenant_id: opaque string identifying the simulation tenant. ALWAYS a sim tenant
#            in this code path (live tenants never reach the production_invoker —
#            the Controller's tool-loop is sim-only by spec 024 inheritance).
# question:  the natural-language sub-agent question, prepared by the Controller
#            from the chat turn or from the FR-026 signal-driven fan-out.
```

The HTTP body sent to the agent Container App also includes:

| Field | Source | Required | Purpose |
|---|---|---|---|
| `tenant_id` | Controller | yes | Tenant scoping |
| `question` | Controller | yes | Substantive question |
| `session_token` | Cosmos session token captured from the Telemetry-Injection write (FR-015) | yes (when invocation follows an injection in the same turn) | Read-your-own-write barrier |
| `traceparent` | Active OpenTelemetry context | yes | Distributed tracing across cascade |
| `correlation_id` | Controller | yes | Logged on the sub_agent_invocation_records document |
| `triggering_signal_id` | FR-026 signal-driven path only | conditional | Used by Risk Assessment's `handle_signal_event` entry |

---

## 5. Output Shape

```python
@dataclass
class SubAgentReply:
    sub_agent: str                     # canonical name (e.g. 'risk-assessment')
    summary: str                       # natural-language answer streamed to chat
    citations: list[str]               # sim-tenant resource IDs only — FR-007
    degraded: bool = False             # set on partial-output / cached-state / tenant-violation paths
    error: str | None = None           # error code from the sub-agent
    prompt_hash: str | None = None     # sha256 — FR-060; None for non-LLM-bearing
    model_deployment: str | None = None
    sub_agent_invocation_id: str | None = None
```

The Controller turns this dataclass into:

1. SSE deltas streamed to the chat pane (≤ 1 s first delta, FR-003).
2. A `sub_agent_invocation_records` Cosmos document (append-only) with the same `prompt_hash` field (FR-060).
3. An aggregated chat reply with each contribution attributed (FR-004).

---

## 6. Error Semantics

| Adapter exception | Reply outcome | Audit entry |
|---|---|---|
| `httpx.TimeoutException` | `asyncio.TimeoutError` propagates; SubAgentInvoker catches and returns `SubAgentReply(degraded=True, error="timeout")` | `sub_agent.timeout` (per FR-006) |
| `httpx.HTTPStatusError(503)` | `SubAgentReply(degraded=True, error="service_unavailable")` | `sub_agent.degraded` |
| Tenant-isolation violation | `SubAgentReply(degraded=True, error="tenant_isolation_violation_filtered")` | `tenant_isolation.violation` (FR-007) |
| `asyncio.CancelledError` (abort/pause) | Re-raised; caller writes `sub_agent.cancel` | `sub_agent.cancel` (FR-059) |
| Azure OpenAI 429 (rate-limit) after retries exhausted | `SubAgentReply(degraded=True, error="rate_limit_exhausted")` | `sub_agent.degraded` |
| Citation resolves to live-tenant resource | filtered from reply; `degraded=True` | `tenant_isolation.violation` (FR-007) |
| Adapter not registered for unknown sub_agent | `SubAgentReply(error=f"Unknown sub-agent {sub_agent!r}")` (existing behaviour) | `routing.ambiguous` if Controller LLM hallucinated the name |

---

## 7. Timeout behaviour (FR-006)

| Threshold | Action |
|---|---|
| Soft ack at `T+5s` | Controller emits SSE delta `{"type": "ack.working", "sub_agent": "<name>"}` |
| Default per-call read timeout | 30 s (configurable per sub-agent) |
| Hard timeout | 120 s — beyond this, `asyncio.wait_for` raises `TimeoutError`, adapter returns degraded reply, audit writes `sub_agent.timeout` |

Implemented at the SubAgentInvoker layer:

```python
async def invoke(self, sub_agent: str, question: str, *, tenant_id: str, timeout_s: float = 30.0, hard_timeout_s: float = 120.0) -> SubAgentReply:
    fn = self._adapters.get(sub_agent)
    if fn is None: ...
    soft_ack_task = asyncio.create_task(self._emit_soft_ack_after(5.0, sub_agent))
    try:
        return await asyncio.wait_for(fn(tenant_id, question), timeout=hard_timeout_s)
    except asyncio.TimeoutError:
        await audit.write("sub_agent.timeout", sub_agent=sub_agent, timeout_seconds=hard_timeout_s, soft_ack_emitted=soft_ack_task.done())
        return SubAgentReply(sub_agent=sub_agent, summary="(timed out)", citations=[], degraded=True, error="timeout")
    finally:
        soft_ack_task.cancel()
```

---

## 8. `prompt_hash` requirement (FR-060)

Every LLM-bearing adapter MUST populate `SubAgentReply.prompt_hash` with the sha256 over the canonical prompt the sub-agent's LLM actually saw. Computed by `apps/agents/common/llm_mixin.py:compute_prompt_hash()`:

```python
import hashlib, json

def compute_prompt_hash(system_prompt: str, user_payload: str, tool_schemas: list[dict]) -> str:
    canonical = json.dumps({
        "system": system_prompt,
        "user": user_payload,
        "tools": tool_schemas,
    }, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
```

The hash is computed and persisted **before** the LLM call returns (per AI/ML cohort §3 — "prevent hash loss on exception"). The sub-agent service writes the hash to its own `sub_agent_invocation_records` document and includes it in the HTTP response body so the adapter can populate `SubAgentReply.prompt_hash`.

For non-LLM-bearing sub-agents (deterministic stubs in test mode), `prompt_hash = None`.

---

## 9. Migration & FR-002 trip-wire

Until the FR-002 migration removes the literal stub strings (per [plan.md §Migration Plan](../plan.md#migration-plan-removing-the-fr-002-stub-string-trip-wire)), the `default_invoker()` continues to register stubs. Once the production adapters are wired in staging and load-tested:

1. Flip `SIM_CONTROLLER_MODE = production` in staging.
2. Remove stub strings from `sub_agent_invoker.py`.
3. Promote the `simulation-stub-sweep` CI step from informational to a hard gate.
4. The contract test `tests/contract/test_no_stub_string.py` asserts that no production adapter ever returns the literal string `"simulated reply (no data source wired in this environment)"` for any sim tenant.

Production adapters MUST NEVER return the stub trip-wire string. Adapter-author checklist:

- [ ] `summary` is a real natural-language sub-agent answer (not a placeholder).
- [ ] `citations[]` contains only sim-tenant resource IDs.
- [ ] `prompt_hash` is non-None for LLM-bearing adapters.
- [ ] `model_deployment` matches the Foundry carve-out registry.
- [ ] No use of `"simulated reply"`, `"no data source"`, or any spec-024 stub string.

---

*Sub-Agent Adapter contract complete 2026-05-08. Interface unchanged at type level; FR-060 prompt_hash field added; FR-002 migration plan committed.*
