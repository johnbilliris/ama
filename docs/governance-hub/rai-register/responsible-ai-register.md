# Responsible AI Register (spec-037 artefact 4)

- Publication: `355d3561-2bff-5532-847a-c647d4dd5040`
- Published: 2026-05-11T17:30:00Z
- Manual-row ratio: 1.00
- Auditor sign-off: Capstone Evidence Pack v1 Author

**PD-037-05 rationale**: per spec-037 Clarification 2, the simulation
telemetry-injection agent (`036-sim-agent-extend`) is treated as a full
production AI component. The simulation watermark / `[SIMULATION]`
chat-receipt prefix do NOT reduce RAI obligations because the agent is
deployed to the same Container Apps revisions as production sub-agents
and `036-sim-agent-extend` FR-066 mandates production-grade idempotency +
append-only audit on `/inject-telemetry`.

## Components × frameworks × principles

Each component row carries **4 frameworks × 8 principles = 32 cells**, all
populated per FR-027 (no blanks). Posture summary cites spec-030 evaluation
outputs (FR-028 — register cites; does NOT trigger evaluation).

Total component rows: 8 (≥1 per AI/agentic component).
Total cells populated: 256 (= rows × 32).

| Component | Kind | Spec(s) | Posture summary |
|---|---|---|---|
| `agent.communication` | sub-agent | 008-communication-agent | spec-008 mandates PIO approval (NN-1); spec-030 provides grounding-faithfulness eval; spec-032 PII guards; spec-035 audit timeline. |
| `agent.evacuation` | sub-agent | 009-evacuation-agent | spec-009 evacuation recommendations subject to IC approval; conservative life-safety defaults preserved per Constitution. |
| `agent.monitoring` | sub-agent | 010-monitoring-agent | spec-010 confidence/provenance carried in signal envelope; planning officer reviews fused signals; spec-005 governance. |
| `agent.resource-allocation` | sub-agent | 011-resource-allocation-agent | spec-011 allocations subject to logistics-officer review; mutual-aid escalations require executive approval. |
| `agent.risk-assessment` | sub-agent | 012-risk-assessment-agent | spec-012 confidence-band threshold 0.7; quarterly re-calibration via spec-030; risk-manager review of treatments. |
| `sim.telemetry-injection` | simulation-agent | 036-sim-agent-extend | Per spec-037 PD-037-05 + Clarification 2: full production AI component (simulation watermark does NOT reduce RAI obligations); spec-036-sim-agent-extend FR-066 production-grade idempotency; append-onl… |
| `eval.llm-framework` | evaluation-framework | 030-llm-eval-framework | spec-030 itself: dataset versioning in Cosmos eval_datasets; 7-year immutability on eval_audit; spec-030 SC-CAP-030 measurable outcomes. |
| `client.foundry-rag` | rag-client | 036-foundry-rag-grounding, parameters | spec-036 RAG citations envelope; corpus_build_sha tagging; offline-cache bundles for Field Coordinator; Foundry carve-out per Constitution NN-1 — see infra/parameters/foundry-carveout.yaml as the carv… |

## Schema

- `packages/schemas/spec_037/responsible-ai-register.schema.json`
- 4 framework columns: AU 8 AI Ethics Principles, ISO/IEC 42001, ISO/IEC 23894,
  NIST AI RMF (Govern/Map/Measure/Manage)
- 8 principle dimensions: human_oversight, fairness, accountability,
  transparency, privacy, safety, contestability, reliability
