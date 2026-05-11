# spec-038 — Help infrastructure overview

This document explains what the Help surface adds to the platform infra.
The Bicep module sources live under `infra/bicep/modules/`; all are gated by
the `enableSpec038Help` feature flag in `infra/main.bicep`.

## New Cosmos containers (under existing account, database `disaster-hub`)

| Container | Partition key | TTL | Notes |
|---|---|---|---|
| `help_articles` | `/tenant_id` | none | composite indexes on `(persona_tags, surface_tags)` and `(snapshot_id, status)` |
| `screenshot_registry` | `/tenant_id` | none | unique key on `(tenant_id, screen_id)` |
| `chat_sessions` | `/tenant_id` | 30 days | FR-029 / AR-001 |
| `chat_audit_log` | `/tenant_id` | 7 years | FR-020 / Privacy Act APP 11 |
| `snapshot_records` | `/tenant_id` | none (immutable) | Cosmos analytics store enabled |
| `support_handoff_config` | `/tenant_id` | none | one root doc per tenant |
| `content_review_backlog` | `/tenant_id` | 7 years | mirrors audit retention |

All seven containers use autoscale RU 400→4000 at launch. Append-only at the
application layer is enforced by `apps/api/app/repositories/help_repositories.py`
(`APPEND_ONLY = {chat_audit_log, snapshot_records}`); a custom Cosmos data-
plane RBAC role (see T-AA020 in `infra/bicep/modules/cosmos-help-rbac.bicep`,
when added) denies UPDATE / DELETE for the FastAPI managed identity on those
two containers.

## Blob container `help-screenshots`

Stored under the existing AU East storage account with:

- private endpoint inherited from account configuration
- 30-day immutability policy (WORM)
- 90-day soft-delete (account-level)
- customer-managed key reuse

Authoring identity has `Storage Blob Data Contributor`; the web app's
SystemAssigned identity has `Storage Blob Data Reader`.

## AI Search index alias semantics

One immutable index per snapshot, named `help-corpus-{snapshot_id}`. The
alias `help-corpus-active` is bound to exactly one index at any time.
Publication and rollback are alias swings, completing within the FR-011c
5-min SLO. The `help-search-index-pair.bicep` module emits a deployment-
script wrapper around the canonical tool at
`tools/help/bootstrap_search_index.py` so the schema definition lives in
one place.

## App Insights workbook

`help-slis` workbook charts seven SLIs:

- chat first-byte p95 (SC-007)
- refusal rate (FR-013)
- fabrication-audit hits (SC-003)
- snapshot publish duration (FR-011c)
- snapshot rollback duration (R6)
- screenshot staleness backlog age (SC-012)
- support-handoff acknowledgement latency (FR-023b)

Metric alerts authored in `infra/bicep/modules/cosmos-help-containers.bicep`
companion alert module (T-AA023, follow-up) fire to the existing on-call
action group at warning + critical thresholds.

## Foundry agent + carve-out registry

The `help_assistant` agent (definition: `infra/parameters/foundry-agents/
help_assistant.yaml`) is registered in `infra/parameters/foundry-agents.yaml`
with `foundry_carveout: false` — the §NN-2 carve-out is NOT invoked because
the assistant operates fully inside the existing AU East Foundry footprint
and consumes the already-registered `gpt-4o-mini` deployment.

## AU-residency attestation

`tools/help/attest_au_residency.py` walks every Help-related Azure resource
in the deployment group and asserts `location ∈ {australiaeast,
australiasoutheast}`. Output JSON is archived per release under
`docs/attestations/help-{release}.json` (T-AA218).
