# Progressive Delivery — AMA CI/CD

**Purpose**: gate matrix for the simplified pipeline (spec 031 + spec-032 FR-C02 + T815).

## Branch model (recap from spec 031)

```
main ──▶ dev ──▶ staging ──▶ production
        (CI+CD) (CI+CD)     (CI+CD)
```

PRs land on `main`. Promotion to `dev`/`staging`/`production` is by merging the corresponding environment branch (manual fast-forward).

## Gate matrix

| Gate | dev | staging | production |
|---|:-:|:-:|:-:|
| `ci.yml` quality (lint, format, mypy, import-linter, unit + integration + contract, web build, benchmark) | ✓ | ✓ | ✓ |
| Coverage ratchet (Phase A no-regression) | ✓ | ✓ | ✓ |
| `codeql.yml` (Python + JS/TS) | ✓ | ✓ | ✓ |
| `security-scan.yml` (gitleaks + PSRule + Trivy fs) | ✓ | ✓ | ✓ |
| `eval-pr-gate.yml` (LLM eval baseline) | ✓ (PR check) | ✓ | ✓ |
| `prompts-publish.yml` (cosign signing of prompt artefacts) | ✓ | ✓ | ✓ |
| `cd.yml` deploy + cosign verify | ✓ | ✓ | ✓ |
| `cd.yml` health checks + auto-rollback | — | ✓ | ✓ |
| `cd.yml` foundry carve-out registry validation | ✓ | ✓ | ✓ |
| dora-metrics.yml daily aggregator | — | — | ✓ |

## Per-environment authentication

- **Stage 1 (current)**: `AZURE_CREDENTIALS` JSON secret per GitHub Environment (per ADR-031 — time-bound MVP).
- **Stage 2 (planned)**: OIDC federated workload identity (per ADR-032). Per environment in order `dev → staging → production`, each gated by 7-day green soak.

## Soak gates

After any `cd.yml` deploy:

| Soak metric | Window | Threshold | Action on breach |
|---|---|---|---|
| `recommendation.created_total` rate | 1 h | within ±20% of baseline | rollback |
| `agent.handoff.success_total` ratio | 1 h | ≥ 99% | rollback |
| `audit.integrity_check.failures_total` | 5 min | 0 | rollback + page Observer-Auditor |
| App Insights availability tests | 30 min | ≥ 4/5 locations green | rollback if 5/5 fail |
| `llm.cost.aud_micros` rate | 1 h | within ±50% of baseline | investigate (no auto-rollback for cost spikes) |

`cd.yml` runs the auto-rollback procedure when any rollback-tagged metric breaches in `staging` or `production`. `dev` does NOT auto-rollback (failed deploys leave the env in the failed state per ADR-031).

## Promotion procedure

1. Verify `main` is green (CI on `main` after merge of all relevant PRs).
2. Open a fast-forward PR `main → dev` (no review required for trivial promotions; one reviewer for material changes).
3. After CI + CD on `dev` succeed and 24 h soak passes → repeat for `staging`.
4. After 7 days of green `staging` → repeat for `production`.

## Emergency hotfix

Critical security or life-safety hotfix path:
1. Cherry-pick the fix onto each env branch in order `production`, then merge back to `main` for traceability.
2. CD runs immediately on each env branch.
3. Document in CHANGELOG with `[hotfix]` tag and link the issue.

## Cross-references

- Spec-031 (simplified pipeline source).
- Spec-032 FR-C01 (land 031), FR-C02 (this doc), FR-C03 (SHA-pinned actions), FR-C04 (DORA metrics).
- ADR-031 (current AZURE_CREDENTIALS), ADR-032 (planned OIDC supersession).
