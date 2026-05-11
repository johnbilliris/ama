# Risk Register Index (spec-037 artefact 1)

> Source-of-truth: `risk-register.json` (JSON sidecar). This file is the
> human-readable roll-up sorted by residual-risk score (FR-013).

- Publication: `fe3ace7c-a2c5-5ced-aa98-529590aa33b9`
- Published: 2026-05-11T17:30:00Z
- Total rows: 21
- Manual rows: 21 (ratio 1.00; FR-038 cap 0.5)
- Auditor sign-off: Capstone Evidence Pack v1 Author

| Residual | Risk ID | Title | Category | Owner | Next review |
|---:|---|---|---|---|---|
| 8 | `RISK-NEW-012` | PH/JP/BD baseline data-sharing MoU not signed | Jurisdictional | Capstone Reviewer | 2026-11-11 |
| 6 | `RISK-NEW-001` | Container Apps revision saturation | Platform | Infrastructure/DevOps Lead | 2026-08-11 |
| 6 | `RISK-NEW-007` | Cross-jurisdiction span-of-control breach | Operational | Incident Commander | 2026-06-11 |
| 6 | `RISK-NEW-008` | Field connectivity loss during evacuation | Operational | Field Coordinator | 2026-08-11 |
| 6 | `RISK-NEW-009` | Resource scarcity under concurrent disaster activations | Operational | Logistics Officer | 2026-06-11 |
| 6 | `RISK-NEW-016` | Container image dependency CVE | Supply-chain | Security Engineer | 2026-06-11 |
| 4 | `RISK-AOAI-001` | AI Model Unavailability During Disaster Operations | AI | Platform Operations Lead | 2026-08-11 |
| 4 | `RISK-NEW-004` | LLM hallucination in Communication Agent public alerts | AI | Public Information Officer | 2026-06-11 |
| 4 | `RISK-NEW-011` | Commonwealth COMDISPLAN activation lag | Jurisdictional | Executive Leader | 2026-08-11 |
| 4 | `RISK-NEW-014` | PII leakage in audit log payloads | Data | Compliance Auditor | 2026-06-11 |
| 4 | `RISK-NEW-018` | Volunteer credentialing channel dependency | Supply-chain | Resilience Planner | 2026-08-11 |
| 3 | `RISK-NEW-002` | Cosmos partition hotspot under cross-jurisdiction surge | Platform | Data Engineer | 2026-08-11 |
| 3 | `RISK-NEW-003` | Foundry RAG carve-out endpoint unavailability | Platform | Solution Architect | 2026-08-11 |
| 3 | `RISK-NEW-006` | Confidence-threshold drift in Risk Assessment Agent | AI | AI/ML Engineer | 2026-08-11 |
| 3 | `RISK-NEW-010` | Conflicting jurisdiction lead-agency claims | Jurisdictional | Executive Leader | 2026-08-11 |
| 3 | `RISK-NEW-013` | Signal envelope schema drift breaks ingest contract | Data | Data Engineer | 2026-08-11 |
| 2 | `RISK-AOAI-002` | Token Quota Exhaustion Under Sustained Disaster Load | AI | Platform Operations Lead | 2026-06-11 |
| 2 | `RISK-AOAI-003` | Managed Identity Credential Propagation Delays | Operational | Platform Operations Lead | 2026-08-11 |
| 2 | `RISK-NEW-005` | Sim-agent idempotency replay under simulated disaster load | AI | AI/ML Engineer | 2026-08-11 |
| 2 | `RISK-NEW-015` | Corpus snapshot drift in Foundry RAG retrievals | Data | Data Engineer | 2026-08-11 |
| 2 | `RISK-NEW-017` | Foundry SDK breaking change at carve-out boundary | Supply-chain | AI/ML Engineer | 2026-11-11 |

## Cross-references

- Schema: `packages/schemas/spec_037/risk-register.schema.json`
- Existing AOAI risks preserved per FR-012 in `RISK-AOAI-001.md`
- ADR-037-04 (three-layer append-only) governs publication semantics
