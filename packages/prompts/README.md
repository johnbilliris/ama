# `packages/prompts/` — Versioned Prompt Library

**Purpose**: versioned, signed prompt templates consumed by `apps/agents/`. Closes FR-AI05. Signed by `cosign` keyless per ADR-035.

## Layout

```
packages/prompts/
├── README.md                       # this file
├── cosign.manifest.yaml            # signing manifest (cd.yml verifier reads)
├── monitoring/
│   ├── triage_v1.0.0.yaml
│   └── triage_v1.0.0.yaml.sig      # cosign signature (produced by prompts-publish.yml)
├── risk_assessment/
│   ├── recommend_v1.2.0.yaml
│   └── ...
├── communication/
│   ├── alert_draft_v1.0.0.yaml
│   ├── multilingual_adapt_v1.0.0.yaml
│   └── ...
├── evacuation/
└── resource_allocation/
```

## Prompt template format

Each `.yaml` is:

```yaml
metadata:
  id: risk_assessment.recommend
  version: 1.2.0
  owner: "@johnbilliris/ama-spec-maintainers"
  review_due: 2026-10-30
  last_reviewed: 2026-04-30
templates:
  system: |
    You are the Risk Assessment Agent for the Disaster Response Coordination Hub...
  user: |
    Signal: {{signal_summary}}
    Jurisdiction: {{jurisdiction_code}}
    RAG sources: {{rag_sources}}
    ...
defaults:
  temperature: 0.2
  response_model: RiskRecommendation
```

## Versioning rules

- **Semver**. Any change to `system` or `user` text → at minimum a patch bump.
- Output schema breaking changes → major bump; consumer code updates required.
- Old versions are NEVER deleted; they are archived for audit replay (FR-AI02).

## Review cadence

- Quarterly review by AI/ML Engineer + Compliance Auditor.
- `review_due` field MUST be ≤ 6 months from the prior `last_reviewed`.
- A linter in CI flags overdue prompts.

## Signing + verification

See `cosign.manifest.yaml`. The `prompts-publish.yml` workflow signs every modified prompt; `cd.yml` verifies before deploy. Verification failure blocks the deploy and pages Security Engineer.

## Consumer pattern

Agents load prompts from this package, not from inline strings. The `prompt_sha` is computed from the rendered template (system+user with variables substituted) and stored in the recommendation record (FR-AI02).

```python
from prompts.loader import load_prompt
from prompts import compute_prompt_sha

artefact = load_prompt("risk_assessment.recommend", version="1.2.0")
rendered_system, rendered_user = artefact.render(signal_summary=..., jurisdiction_code=..., rag_sources=...)
sha = compute_prompt_sha(rendered_system, rendered_user)
```

## Migration plan

Stream 6 (T605) introduces this package; agent code in Stream 2 (T205) migrates from inline prompts during the LLM Strategy refactor.
