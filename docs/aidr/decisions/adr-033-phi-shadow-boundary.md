# ADR-033: Phi Shadow Boundary and Classification-Aware Filter

## Status

Proposed (target: Accepted upon merge of spec-032 Stream-2 + Stream-6 Phi tasks).

## Context

Spec 032 FR-AI03 introduces a **Phi (small-model) shadow path** alongside the production GPT-4o path so that cost and quality regressions can be measured without affecting user-facing recommendations. Phi-family deployments are typically only available in **non-AU Azure regions**, which intersects directly with **Constitution Non-Negotiable #2 (Data Sovereignty)**.

The constitution's §1.2.0 amendment carves out Microsoft Foundry model-hosting endpoints in non-AU regions **only when**:
- The endpoint is on a named, version-controlled carve-out list reviewed by security + compliance personas.
- **Regulated platform data** (incidents, alerts, recommendations, operator actions, audit, evidence, PII, PSPF-marked content) is **not stored or persistently logged outside Australian borders**.
- Prompts and responses traversing a non-AU model-hosting endpoint are subject to **data-minimisation controls at the platform's model gateway** so that personal information and PSPF-marked content are removed, masked, or denied transit unless an explicit, auditable use-case approval exists.

The rubber-duck critique on the spec-032 plan flagged two specific risks:
1. PII redaction alone is **narrower** than the constitution requires; PSPF-marked and sensitive operational content also need classification-aware handling.
2. The earlier ADR-031 simplification removed automated carve-out enforcement at deploy time; this must be restored before Phi shadow ships.

## Decision

We adopt a **deny-by-default** Phi shadow path with two enforcement layers:

### Layer 1 — Foundry carve-out registry (deploy-time gate)

A new `infra/parameters/foundry-carveout.yaml` lists every permitted non-AU model deployment with:

```yaml
- model_name: phi-3.5-mini
  region: eastus
  business_justification: "Spec 032 FR-AI03 — cost/quality shadow path for GPT-4o."
  approver_identities:
    - johnbilliris (project lead)
    - <security-engineer-handle>
    - <compliance-auditor-handle>
  review_date: 2026-10-30
```

A new OPA policy `infra/policies/foundry_carveout.rego` and a CD step `verify-carveout.ps1` REFUSE to deploy any Foundry model endpoint **not** present in the registry. If the registry is mutated without two approver signatures, the policy fails closed.

### Layer 2 — Classification-aware gateway filter (runtime gate)

A new module `apps/agents/common/safety/classification.py` implements three orthogonal classifiers run in series for every prompt about to traverse a non-AU endpoint:

1. **PII detector** — Microsoft Presidio (or equivalent) detects PII; default action **redact**, fall back to **deny** if confidence is high.
2. **PSPF marking detector** — regex + zero-shot classifier looks for `OFFICIAL: Sensitive`, `PROTECTED`, `SECRET` markings and Australian-government metadata patterns; **deny** transit.
3. **Sensitive operational content** — pattern set covering operator names + identifiers, ATSI community identifiers, victim/casualty identifiers, classified location coordinates; **deny** transit unless override-approved.

If any classifier denies transit, the gateway:
- Records a `shadow.classification.denied` event in the audit log with classifier name + redaction summary (no raw payload).
- Returns no Phi output for that turn.
- Does **not** fall through to a different non-AU model.

A documented one-time override (`X-Foundry-Carveout-Override: <case_id>` header) is permitted only when `case_id` matches an explicit approval record in Cosmos. Each override is page-routed to the Security Engineer.

### Layer 3 — AU-side persistence

All Phi outputs are persisted **only** in the AU-resident Cosmos `recommendations` container with `shadow=true` and `parent_recommendation_id=<prod_id>`. The User-facing UI suppresses `shadow=true` rows. Retention 7 years per spec-030 alignment (ISO/IEC 42001 + APP).

## Consequences

### Positive

- Restores Constitution NN-2 deploy-time enforcement that ADR-031 documented as lost.
- Provides defensible documentation when Compliance Auditor or NEMA reviews the carve-out posture.
- Enables cost/quality measurement (the original FR-AI03 driver) without weakening sovereignty.

### Negative / accepted

- Higher latency on shadow path (classification adds ~50–150 ms per prompt, but shadow is asynchronous/off-critical-path so user-facing latency is unaffected).
- Some legitimate prompts will be denied transit (false positives); operators can review denied events in the audit log; iterate classifier rules.

### Not pursued

- **Re-region Phi to AU East via dedicated Foundry deployment** — not currently available in AU East; revisit when Microsoft adds AU support.
- **Hash-only transit (one-way hash of the prompt)** — defeats the cost/quality comparison purpose of the shadow.

## Compliance mapping

| Constitution clause | Honoured how |
|---|---|
| NN-2 §1 (carve-out list) | `infra/parameters/foundry-carveout.yaml` + `verify-carveout.ps1` |
| NN-2 §2 (no regulated data persisted outside AU) | Layer 3 — outputs persist in AU Cosmos only |
| NN-2 §3 (data-minimisation at model gateway) | Layer 2 — three-classifier filter, deny-by-default |
| NN-2 §4 (auditable carve-out list) | Registry has `approver_identities[]` + `review_date`; OPA enforces; CD logs every Phi-bound deploy |

## References

- [Constitution Non-Negotiable #2](../../../.specify/memory/constitution.md)
- [Spec 030 — LLM Evaluation Framework](../../../specs/030-llm-eval-framework/spec.md)
- [Spec 032 FR-AI03, FR-AI03a](../../../specs/032-rubric-improvements/spec.md)
- Microsoft Presidio: <https://github.com/microsoft/presidio>
- Australian PSPF: <https://www.protectivesecurity.gov.au/>

---
*Author: Security Engineer + AI/ML Engineer personas via spec-032 Stream-0. Date: 2026-04-30.*
