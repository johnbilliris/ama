# ama-eval-core

Shared library for the LLM Evaluation Framework (feature 030). Imported by `apps/api`, `apps/eval-runner`, `packages/eval-dataset`.

## Contents

- `schemas/` — JSON Schemas (case, dataset-manifest, metric-definition, judge, run, scorecard, audit-event, provisioning-policy)
- `models.py` — Pydantic v2 models matching `specs/030-llm-eval-framework/data-model.md`
- `audit.py` — AuditAction enum, AuditEmitter protocol, in-memory test double
- `policy.py` — pure ProvisioningPolicy evaluator (no I/O)
- `registries/models-v1.json` — v1 evaluable Foundry model set (FR-013, SC-010)
