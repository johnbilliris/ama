# ADR-F02: Async-to-Sync Bridge for Pipeline Callers

## Status

Accepted

## Context

Compliance audit finding F02 identified synchronous `time.sleep()` calls in
handoff delivery and OCC version assignment as blocking the event loop.
Converting these to `async def` with `asyncio.sleep()` was required.

However, all five agent pipelines (monitoring, risk_assessment, evacuation,
resource_allocation, communication) are synchronous 500–1000 line orchestrators
with deep call stacks. Full async conversion would require rewriting every
pipeline method and all callers, risking regressions across the entire system.

## Decision

We convert the leaf functions (`deliver_handoff_with_retry`, `assign_version`,
`deliver_alert`) to async, and introduce a lightweight `run_async()` bridge
(`common/async_bridge.py`) that synchronous pipeline stages use to await these
coroutines.

The bridge detects whether an event loop is already running:

- **No loop**: Uses `asyncio.run()` (zero overhead).
- **Running loop**: Offloads to a single-threaded `ThreadPoolExecutor` to avoid
  nested-loop errors.

## Consequences

### Positive

- All blocking `time.sleep()` calls eliminated (finding F02 resolved).
- Pipeline code remains synchronous — minimal diff, low regression risk.
- Future migration to fully async pipelines is unblocked; callers already
  invoke async functions.

### Negative

- Thread-pool path adds ~1 ms overhead per call when run inside an existing
  event loop (e.g., under FastAPI). This is negligible compared to the 2-second
  delivery timeout.
- Two calling patterns coexist (direct `await` in new code, `run_async()` in
  legacy pipelines). Documentation and code comments mitigate confusion.

## Alternatives Considered

1. **Full async pipeline rewrite**: Rejected — too large a change surface for
   the compliance remediation scope.
2. **Keep sync with `time.sleep()` in a thread**: Rejected — does not address
   the audit finding.
3. **`nest_asyncio` monkey-patch**: Rejected — fragile, not recommended for
   production systems.
