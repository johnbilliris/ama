# Sequence — Monitoring → Risk Assessment → Communication

**Purpose**: capture the multi-agent flow from signal ingestion through public alert publication, including dead-letter and recovery cycles. Closes FR-A04.

```mermaid
sequenceDiagram
  participant SRC as External Signal Source
  participant ING as Ingestion (apps/ingestion)
  participant SB as Service Bus
  participant MON as Monitoring Agent
  participant RISK as Risk Assessment Agent
  participant COMMS as Communication Agent
  participant CS as Content Safety
  participant API as Coordination API
  participant DB as Cosmos (audit + recs)
  participant OP as Operator

  SRC->>ING: Push signal (HTTPS / Event Hubs)
  ING->>DB: Persist raw signal
  ING->>SB: signals.queue
  SB-->>MON: Deliver

  alt Triage success
    MON->>MON: Classify hazard, score confidence
    MON->>API: Append timeline event (kind=signal_triaged)
    MON->>SB: handoffs.risk_assessment (with confidence ≥ 0.8 threshold)
  else Confidence < 0.8 OR triage error
    MON->>SB: handoffs.dead_letter
    MON->>API: Append timeline event (kind=dead_letter, reason=...)
    Note right of MON: Retry up to 3x within 300s window<br/>then permanent dead-letter
  end

  SB-->>RISK: Deliver
  RISK->>API: Read related signals + jurisdiction policy
  RISK->>RISK: Generate recommendation (LLM with RAG ground)
  RISK->>API: Persist recommendation (with prompt_sha, model_version, rag_sources)
  RISK->>SB: handoffs.communication (if action required)
  RISK->>SB: handoffs.evacuation (if life-safety threshold)
  RISK->>SB: handoffs.resource_allocation

  alt Recommendation requires public alert
    SB-->>COMMS: Deliver
    COMMS->>COMMS: Draft message (multi-language priorities from policy)
    COMMS->>CS: Output safety check
    CS-->>COMMS: Pass / Block / Suggest

    alt Pass
      COMMS->>API: Persist proposed alert (state=proposed)
      API-->>OP: Notify (operator console)
      OP->>API: Approve (state=approved)
      API->>API: Publish to channels (SMS/push/social/email/radio)
      API->>DB: Append timeline event (kind=publish, AWS level=...)
    else Block
      COMMS->>API: Append timeline event (kind=alert_blocked, reason=safety)
      COMMS->>SB: handoffs.dead_letter
      Note over COMMS,API: Operator reviews via dead-letter queue
    end
  end

  par Recovery + lessons capture (asynchronous)
    API->>SB: handoffs.recovery (post-incident)
    SB-->>API: Recovery agent processes (existing spec-030 flow)
    API->>SB: handoffs.lessons_capture
    SB-->>API: Lessons agent appends to AAR gap summary (FR-AG10)
  end

  Note over MON,COMMS: Per-handoff timeout enforced (FR-AG08)<br/>If handoff exceeds timeout: dead-letter + alert<br/>Kill-switch (FR-AG05) drops any agent to template-only fallback within ≤30s
```

## Notes

- **Confidence gating**: monitoring → risk requires confidence ≥ 0.8 (per existing risk-assessment thresholds). Below threshold → dead-letter.
- **Retry policy**: 3 attempts in a 300 s window per existing `handoff_retry` (Stream 2 will retain semantics; FR-P03 swap to `pybreaker` for the LLM call breaker).
- **Recovery + lessons** are asynchronous and do not block primary publication.
- **Approval workflow**: every public alert requires operator approval (Constitution NN-1).
- **Audit timeline**: every transition appends a typed event (`signal_triaged`, `dead_letter`, `recommendation_proposed`, `approved`, `publish`, `recovery`, `lessons`).

## Related

- Saga / Process Manager doc — `docs/agents/saga-approval-workflow.md` (T311)
- Decision-rights matrix — `docs/agents/decision-rights.md` (T027)
- Multi-agent state graph — `apps/agents/tools/render_state_graph.py` (T709) generates a state-graph rendering that consumes the same configuration this sequence reflects.
