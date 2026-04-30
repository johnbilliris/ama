# DORA Metrics

**Purpose**: how the platform measures + publishes the four DORA metrics (Deployment Frequency, Lead Time, Change Failure Rate, MTTR). Closes spec-032 FR-C04 + T816.

## The four metrics

| Metric | Definition | Source data | Computed by |
|---|---|---|---|
| **Deployment Frequency** | Successful CD runs per environment per day | GitHub Actions `cd.yml` workflow runs | `scripts/dora_metrics_publish.py` |
| **Lead Time for Changes** | Time from commit (head_commit.timestamp) to deploy (workflow_run.updated_at) | GitHub Actions `cd.yml` workflow runs | `scripts/dora_metrics_publish.py` |
| **Change Failure Rate** | % of deploys followed by an `incident`-labelled GitHub Issue within 24 h | GitHub Actions + GitHub Issues | `scripts/dora_metrics_publish.py` |
| **Mean Time to Recover (MTTR)** | Mean (issue.closed_at − issue.created_at) for `incident`-labelled issues | GitHub Issues | `scripts/dora_metrics_publish.py` |

## Publication path

Daily aggregator (`.github/workflows/dora-metrics.yml`):
1. Cron 06:00 UTC.
2. Pulls last 30 days of CD runs + `incident`-labelled issues from the GitHub API.
3. Computes the four metrics per environment (dev/staging/production).
4. Posts as App Insights customMetrics:
   - `dora.deployment_frequency_per_day` (gauge)
   - `dora.lead_time_hours` (histogram)
   - `dora.change_failure_rate` (gauge)
   - `dora.mttr_minutes` (histogram)

## Workbook

A dedicated DORA workbook (`infra/modules/workbooks/dora-metrics.json` — to be authored as a follow-up to T816) renders trend lines for all four metrics with the published Microsoft DORA performance bands:

| Band | Deploy Freq | Lead Time | CFR | MTTR |
|---|---|---|---|---|
| **Elite** | Multiple per day | < 1 h | 0–15% | < 1 h |
| **High** | Daily–weekly | 1 day–1 week | 0–15% | < 1 day |
| **Medium** | Weekly–monthly | 1 week–1 month | 16–30% | 1 day–1 week |
| **Low** | < monthly | > 1 month | 16–30%+ | > 1 week |

## Targets (production)

- Deployment Frequency: ≥ 0.5 / day (3+ deploys per week).
- Lead Time: ≤ 24 h (commit → production).
- Change Failure Rate: ≤ 15%.
- MTTR: ≤ 60 min (matches RTO target for life-safety system).

## Caveats

- The aggregator counts an incident as "linked to a deploy" if the issue opens within 24 h of any successful CD run. Some incidents are unrelated to the latest deploy — manual triage may adjust the report.
- "Lead time" measures commit → deploy on the env branch; PR review time is captured separately under "Lead Time for PRs" (future enhancement).
- DORA metrics are **lagging indicators**. Use SLO burn-rate alerts (FR-O06) for real-time decisions.

## Cross-references

- Spec-032 FR-C04 (this doc), T814 (publisher workflow), T816 (this doc).
- Spec-031 simplified pipeline (the basis for the deploy timestamps).
- Capacity model (`docs/architecture/capacity-model.md`) — provisioning constraints DORA helps tune.
