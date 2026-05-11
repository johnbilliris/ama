# spec-035 — Middleware stack & offline-replay flow

> Spec-035 T079. Captures the production-reachable middleware order and the
> offline reconnect-replay sequence so reviewers can audit precedence + the
> closed-set audit-outcome surface added in this spec.

## Middleware stack diagram

The diagram below shows the request path through the API middleware after
spec-035 closure. Order is significant — it is enforced by the activation-mutex
build gate ([scripts/verify-activation-mutex.ps1](../../scripts/verify-activation-mutex.ps1)).

```mermaid
flowchart LR
    Client[Operator browser]
    SovBanner[SovereigntyBanner<br/>T069]
    SW[Offline service worker<br/>T040 / T072]
    API[FastAPI app]

    subgraph Middleware
        direction TB
        AuthZ[Identity + RBAC<br/>auth/]
        Cors[CORS]
        Audit[Audit row append<br/>+ ama.audit.outcome span<br/>T078]
        Classifier[Classifier mask<br/>T046]
        CulturalSafety[Cultural-safety driver<br/>T053]
        Carveout[Carve-out registry guard<br/>T070]
    end

    Client --> SovBanner --> SW -->|navigator.onLine| API
    API --> AuthZ --> Cors --> Audit --> Classifier --> CulturalSafety --> Carveout
    Carveout --> Domain[(Domain repositories)]
    Audit -. emits .-> AppInsights[(Azure Monitor<br/>span ama.audit.outcome)]
```

### Middleware ordering rationale

| Stage | Why this order |
|------|----------------|
| AuthZ first | All downstream stages assume an authenticated principal; spec-035 NN-1 / NN-2 closed-set role identity. |
| Audit second | Every request that reaches handlers must produce an audit row; positioning Audit before mutating logic guarantees the audit row exists *before* the closed-set outcome is finalised. T078 enriches the active OTEL span with `ama.audit.outcome` at this stage. |
| Classifier third | T046 mask runs *after* audit so the masked-field count is captured in the audit row. |
| Cultural-safety fourth | T053 routes drafts to elders + materialises `cultural_safety_timeout_override` / `cultural_safety_held` outcomes (closed set). The decision feeds back into the audit row before downstream domain handlers run. |
| Carve-out registry fifth | T070 surfaces stale-review entries to the SovereigntyBanner. The 90-day CI gate enforces this stays current. |

## Offline replay flow

```mermaid
sequenceDiagram
    autonumber
    participant Field as Field operator (offline)
    participant SW as Offline service worker (T040)
    participant Queue as IndexedDB queue (T034)
    participant API as FastAPI middleware
    participant Audit as Audit log + OTEL

    Field->>SW: Submit IC approval (offline)
    SW->>Queue: Enqueue request<br/>(cap = NEXT_PUBLIC_OFFLINE_QUEUE_CAP)
    Note over SW,Queue: 80% utilisation warning surfaced<br/>via FieldCoordinatorOffline panel (T041)

    Field-->>SW: Reconnect detected
    SW->>API: Replay queued requests in order
    API->>Audit: Emit row with closed-set outcome
    Audit-->>SW: 200 + audit_id
    SW-->>Field: Replay banner (drained N, failed M)
```

## See also

- [spec-035 plan.md](../../specs/035-webapp-capstone-closure/plan.md)
- [spec-035 research.md § R-011](../../specs/035-webapp-capstone-closure/research.md)
- [Cultural-safety contract](../../specs/035-webapp-capstone-closure/contracts/cultural-safety.contract.md)
- [Audit-event schema](../../contracts/audit-event.schema.json)
