# Phase 1 — Data Model: Progressive Delivery Pipeline (029)

**Date**: 2026-04-26
**Status**: Complete

This document captures the entities introduced or evolved by feature 029. All entities are derived directly from `spec.md` § Key Entities and the FRs that reference them. Persistence locations and partition keys are decisions from `research.md`.

---

## Entity reference

| # | Entity                       | Persistence                                  | Lifetime / Retention |
|---|------------------------------|----------------------------------------------|----------------------|
| 1 | Artefact                     | Azure Container Registry + audit metadata    | ≥ 3 known-good digests retained per service (FR-021) |
| 2 | Canary Stage                 | `pipeline_state` Cosmos container            | Last 90 days hot, then audit-store summary |
| 3 | SLO Burn-Rate Window         | Application Insights / Azure Monitor (live)  | Per-window; outcomes summarised into audit |
| 4 | Evidence Pack                | Azure Blob Storage (immutable, AU)           | 7 years, legal hold (FR-014) |
| 5 | Audit Event                  | Existing append-only audit Cosmos store      | 7 years, append-only (FR-014, FR-015) |
| 6 | Change Freeze                | `pipeline_state` Cosmos container (singleton)| Active until lifted; transitions audited |
| 7 | Emergency Hotfix Approval    | Audit store + GitHub PR metadata             | 7 years (audit) |
| 8 | Drift Finding                | GitHub Issue (label `infrastructure-drift`) + audit entry | Issue lifetime; audit 7 years |
| 9 | CODEOWNERS Path              | `.github/CODEOWNERS`                          | Version-controlled |
| 10 | Pipeline Identity            | Entra ID workload identity + federated cred  | Lifecycle per env; rotation via IaC only |
| 11 | Environment Profile          | `infra/policy/posture-matrix.yaml` + Bicep params | Version-controlled |
| 12 | Posture Matrix               | `infra/policy/posture-matrix.yaml` (canonical) | Version-controlled, CODEOWNERS-gated |
| 13 | Posture Exception            | `infra/policy/posture-exceptions.yaml`        | ≤ 90 days; auto-removed on expiry (FR-033) |
| 14 | Developer API Key            | `kv-ama-dev/secrets/devkey-{alias}-{service}` | 24 hours (FR-030) |
| 15 | Foundry Carve-out Entry      | `infra/policy/foundry-carveout.yaml`          | Until next quarterly review |

---

## 1 Artefact

**Source**: spec.md § Key Entities, FR-004, FR-005, FR-008, FR-021

| Field                       | Type     | Notes |
|-----------------------------|----------|-------|
| `digest`                    | string   | OCI digest (`sha256:…`); primary key |
| `service`                   | string   | One of `api` / `agents` / `ingestion` / `web` |
| `build_run_id`              | string   | GitHub Actions run ID |
| `originating_commit`        | string   | Full commit SHA on `main` |
| `sbom_uri`                  | string   | Blob URI to SPDX SBOM |
| `signature_identity`        | string   | Cosign certificate subject (workload identity OIDC) |
| `provenance_attestation_uri`| string   | SLSA-3 provenance attestation URI |
| `linked_spec_ids`           | string[] | e.g., `["029-progressive-delivery-pipeline", "FR-004"]` |
| `last_known_good_at`        | datetime / null | Set when the artefact passes its 100 %-stage 60-min observation window without breach (Q3) |
| `superseded_by`             | digest / null | Set when a later artefact promotes to 100 % |
| `verification_status`       | enum     | `verified` / `signature_failed` / `sbom_failed` / `provenance_failed` |

**Lifecycle**:
1. Created on successful build job.
2. Verified at every deploy step (FR-005); deploy fails closed if verification fails.
3. Marked `last_known_good_at` when its 100 %-stage window completes clean (FR-008 known-good definition).
4. Marked `superseded_by` when a later artefact reaches 100 %.
5. Eligible for rollback as long as `verification_status == verified` AND `last_known_good_at != null` AND not subsequently rolled back.
6. Image bytes retained per ACR retention rule until at least the 3rd-most-recent known-good supersedes it (FR-021).

---

## 2 Canary Stage

**Source**: spec.md § Key Entities, FR-007, FR-009

| Field                       | Type     | Notes |
|-----------------------------|----------|-------|
| `id`                        | string   | `{service}/{digest}/{stage_pct}` |
| `service`                   | string   | |
| `digest`                    | string   | FK → Artefact |
| `stage_pct`                 | enum     | `5` / `25` / `50` / `100` |
| `entered_at`                | datetime | UTC |
| `observation_window_min`    | int      | `10` / `15` / `30` / `60` per Q1 |
| `min_sample_threshold`      | int      | Per-service config |
| `burn_rate_status`          | enum     | `healthy` / `slow_burn` / `fast_burn` / `insufficient_data` |
| `decision`                  | enum     | `advance` / `hold` / `rollback` / `rolled_back` |
| `decided_at`                | datetime / null | |
| `audit_event_id`            | string   | FK → Audit Event written for this decision |

**State transitions**:
```
entered → (advance) → next stage's "entered"
entered → (hold)    → stays at current stage; tracked issue opened (FR-009 slow-burn) or stalls (FR-024 missing telemetry)
entered → (rollback) → traffic shifted to known-good; stage marked rolled_back (FR-008)
```

---

## 3 SLO Burn-Rate Window (live)

Live computation; persisted only via summarised stage decisions and audit events.

| Field                  | Type     |
|------------------------|----------|
| `slo_name`             | enum     | `availability` / `api_latency_p95` / `dashboard_load_p95` / `signal_freshness` / `recommendation_correctness` |
| `target`               | float    |
| `measured_value`       | float    |
| `budget_consumed_pct`  | float    |
| `window_minutes`       | int      | `60` (slow-burn) or `60` rolling (fast-burn 1 h check) |
| `status`               | enum     | `healthy` / `slow_burn` / `fast_burn` |

---

## 4 Evidence Pack

**Source**: spec.md § Key Entities, FR-013, FR-014

| Field                       | Type     | Notes |
|-----------------------------|----------|-------|
| `pack_digest`               | string   | sha256 of pack manifest; primary key |
| `storage_uri`               | string   | `https://{evidencestoreau}.blob.core.windows.net/evidence/{yyyy}/{mm}/{dd}/{pack_digest}.zip` |
| `originating_artefact_digest`| string  | FK → Artefact |
| `target_environment`        | enum     | `dev` / `staging` / `production` |
| `outcome`                   | enum     | `success` / `rollback` / `freeze_pause` |
| `deploying_actor`           | string   | OIDC subject |
| `approver_identities`       | string[] | Empty for non-emergency; 2 entries for emergency-hotfix |
| `contents_inventory`        | object[] | List of `{filename, sha256, size}` |
| `linked_spec_ids`           | string[] | e.g., `["029", "FR-013", ...]` |
| `retention_class`           | enum     | `seven_years_legal_hold` |
| `created_at`                | datetime | |
| `audit_event_id`            | string   | FK → Audit Event |

**Pack contents** (mandatory): test results JSON, SBOM, image signature, vulnerability scan reports (SAST + SCA + container scan), Bicep What-If diff, accessibility audit report, IaC policy decisions (OPA output), posture-verifier output (FR-031), deploying actor record, approval log (where applicable), per-stage burn-rate window outcomes.

**Immutability**: time-based immutability policy of 7 years on every blob; legal hold enabled on the container.

---

## 5 Audit Event

**Source**: spec.md § Key Entities, FR-015

| Field           | Type     | Notes |
|-----------------|----------|-------|
| `id`            | string   | UUID |
| `actor`         | string   | OIDC subject or human Entra ID |
| `timestamp`     | datetime | UTC |
| `action`        | string   | e.g., `gate.decision`, `canary.advance`, `canary.rollback`, `freeze.activate`, `freeze.deactivate`, `evidence.write`, `devkey.issue`, `devkey.rotate`, `posture.violation`, `drift.detected` |
| `rationale`     | string   | Human-readable; required for human-initiated actions |
| `outcome`       | enum     | `success` / `failure` / `denied` |
| `evidence_uri`  | string / null | Set when an evidence pack was written |
| `digest`        | string / null | Hash of related artefact (evidence pack, image, IaC bundle) |
| `correlation_id`| string / null | Links to incident or PR |
| `service`       | string / null | Where applicable |
| `environment`   | enum / null | `dev` / `staging` / `production` |

**Schema discipline**: identical first five fields (`actor`, `timestamp`, `action`, `rationale`, `outcome`) as incident and operator events to preserve a single provenance chain (FR-015, SC-012).

**Partitioning**: existing audit Cosmos partition key `/{actor}_{date}` reused; deployment events do not require a new container.

---

## 6 Change Freeze (singleton)

**Source**: spec.md § Key Entities, FR-011

| Field                  | Type     |
|------------------------|----------|
| `id`                   | constant `"change_freeze"` |
| `state`                | enum     | `inactive` / `active` |
| `activator`            | string / null |
| `activated_at`         | datetime / null |
| `reason`               | string / null |
| `deactivated_at`       | datetime / null |
| `linked_incident_id`   | string / null |

**Authority**: state may only transition `inactive → active` if the actor's OIDC claims include `ama-oncall-sre` or `ama-incident-commander` group membership (FR-011). All transitions emit an Audit Event.

---

## 7 Emergency Hotfix Approval

**Source**: spec.md § Key Entities, FR-011a, FR-012

| Field                       | Type     | Notes |
|-----------------------------|----------|-------|
| `change_id`                 | string   | PR number |
| `approvers`                 | string[2]| Two distinct Entra IDs, both members of `ama-emergency-approver`, neither equal to PR author |
| `approver_timestamps`       | datetime[2] | |
| `deferred_gates`            | string[] | Subset of {`integration_full`, `simulation_replay`, `accessibility_full`, `load_smoke`, `chaos_lite`} |
| `evidence_pack_id`          | string   | FK → Evidence Pack |
| `reconciliation_due_at`     | datetime | `deployed_at + 24h` |
| `reconciliation_status`     | enum     | `pending` / `complete` / `breached` |

---

## 8 Drift Finding

**Source**: spec.md § Key Entities, FR-019, FR-029, FR-031

| Field                  | Type     |
|------------------------|----------|
| `resource_id`          | string   |
| `property`             | string   |
| `expected_value`       | string   |
| `observed_value`       | string   |
| `detection_timestamp`  | datetime |
| `detector`             | enum     | `nightly_drift` / `posture_verifier` / `cross_env_check` |
| `status`               | enum     | `open` / `resolved` |
| `github_issue_url`     | string   |
| `audit_event_id`       | string   |

---

## 9 CODEOWNERS Path

| Field             | Type     |
|-------------------|----------|
| `path_glob`       | string   |
| `required_personas`| string[] | Either GitHub team handles (e.g., `["@org/security-codeowners", "@org/compliance-codeowners"]`) on an org-owned repo, OR individual user handles (e.g., `["@johnbilliris"]`) on a user-owned repo. See ADR-029-01 in `research.md` §R17. |
| `classification`  | enum     | `safety_critical` / `infrastructure` / `policy` / `general` |

Stored in `.github/CODEOWNERS`; consumed by GitHub branch-protection.

---

## 10 Pipeline Identity

**Source**: FR-016, R12 (research)

| Field                   | Type     |
|-------------------------|----------|
| `name`                  | string   | e.g., `id-ama-pipeline-staging` |
| `federated_subject`     | string   | e.g., `repo:johnbilliris/ama:environment:staging` |
| `scope`                 | string   | RG resource ID |
| `permissions`           | string[] | Built-in role definition IDs |
| `entra_group_memberships`| string[]| For privileged actions (e.g., `ama-emergency-approver` for the emergency-hotfix workflow identity) |
| `last_used_at`          | datetime |

**Provisioning**: `infra/modules/pipeline-identity.bicep`; one identity per environment, no shared identity across `dev`/`staging`/`production`.

---

## 11 Environment Profile

**Source**: spec.md § Key Entities, FR-025

| Field                          | Type     |
|--------------------------------|----------|
| `name`                         | enum     | `dev` / `staging` / `production` |
| `regions`                      | string[] | Subset of `["australiaeast", "australiasoutheast"]` |
| `resource_group`               | string   | `rg-ama-{name}-{region}` |
| `required_tags`                | object   | `{environment: "{name}", ...}` |
| `naming_token`                 | string   | `*-{name}-*` |
| `permitted_network_modes`      | string[] | `dev`: `["public", "private"]`; `staging`/`production`: `["private"]` |
| `permitted_auth_modes`         | string[] | `dev`: `["managed_identity", "shared_key"]`; `staging`/`production`: `["managed_identity"]` |
| `secret_handling`              | enum     | `dev`: `key_vault_or_dev_keyvault_path`; `staging`/`production`: `key_vault_only` |
| `azure_policy_assignments`     | string[] | Generated from posture matrix |

---

## 12 Posture Matrix

**Source**: spec.md § Key Entities, FR-025; canonical at `infra/policy/posture-matrix.yaml`

```yaml
version: 1
last_reviewed: 2026-04-26
reviewing_personas: ["@johnbilliris"]  # user-owned repo per ADR-029-01; restore ["@org/security-codeowners", "@org/compliance-codeowners"] on org migration
environments:
  - name: dev | staging | production
    resource_types:
      - type: Microsoft.DocumentDB/databaseAccounts
        network: { public_access: allow|deny, private_endpoint_required: bool, ip_allow_list: cidr[] }
        identity: { managed_identity_required: bool, shared_key_disabled: bool, local_auth_disabled: bool }
        secret:   { plain_secret_allowed: bool, key_vault_reference_required: bool }
```

Loaded by:
- `infra/policy/rego/posture.rego` at PR time
- `infra/modules/posture-policy-set.bicep` (generator) → Azure Policy initiative scoped per environment **subscription** (Topology A) or per environment **resource group** (Topology B); see research.md §R16
- `tools/pipeline/posture_verifier.py` for FR-031 post-deploy sweep

---

## 13 Posture Exception

**Source**: spec.md § Key Entities, FR-033 (Q9 lifecycle)

```yaml
- name: cosmos-shared-key-legacy-tenant
  resource_id: /subscriptions/.../databaseAccounts/legacydb
  environment: production
  deviating_rule: identity.shared_key_disabled
  justification: "Legacy tenant client cannot rotate to MI before 2026-Q3"
  compensating_controls:
    - "Key held only in kv-ama-prod accessible to single MI id-ama-tenant-bridge"
    - "Defender for Cosmos enabled with high-severity alerting"
  owning_team: "@ama/integration"
  issued_at: 2026-04-26
  expires_at: 2026-07-25  # MUST be ≤ 90 days from issued_at
  dual_approvers: ["@security-owner-ghhandle", "@compliance-owner-ghhandle"]
  audit_pointer: "auditstore/devops/posture_exception/abc123"
```

**Workflow**:
- PR-only mutation; CODEOWNERS requires the security and compliance personas (under the current user-owned repo, this collapses to `@johnbilliris` per ADR-029-01 with branch-protection's "require 2 approving reviews" enforcing dual approval; on org migration this restores to both `@org/security-codeowners` AND `@org/compliance-codeowners`)
- Daily `posture-exception-sweep.yml` removes entries with `expires_at < today` and writes an audit event
- Renewal = fresh PR with new `issued_at`; silent extension prohibited (Q9)

---

## 14 Developer API Key

**Source**: spec.md § Key Entities, FR-026, FR-030 (Q6 issuance)

| Field                       | Type     | Notes |
|-----------------------------|----------|-------|
| `key_id`                    | string   | Azure-side key identifier |
| `owning_developer_entra_id` | string   | OID |
| `alias`                     | string   | Developer alias used in KV path |
| `service`                   | string   | e.g., `cosmos`, `storage`, `keyvault` |
| `key_vault_path`            | string   | `kv-ama-dev/secrets/devkey-{alias}-{service}` |
| `issued_at`                 | datetime | |
| `expires_at`                | datetime | `issued_at + 24h` (FR-030) |
| `issuing_workflow_run_id`   | string   | GitHub Actions run ID of `dev-key-issue.yml` |
| `last_used_at`              | datetime / null | Surface from data-plane logs |
| `revoked`                   | bool     |

**Constraints**:
- Scope limited to dev resources (`rg-ama-dev-*`); MUST never be valid against `staging` / `production` (FR-030, SC-017)
- Issued only via `dev-key-issue.yml` (Q6 — no standing right to mint)
- KV access policy grants read only to the developer's own Entra ID
- Cross-developer read attempt → security event (US8 acceptance #6)

---

## 15 Foundry Carve-out Entry

**Source**: FR-018, R13

```yaml
- model_name: gpt-4.1
  region: eastus2
  resource_id: /subscriptions/.../accounts/foundry-ama-eastus2
  business_justification: "Required model not available in australiaeast as of 2026-04"
  approver_identities:
    - "@johnbilliris"  # ADR-029-01; restore ["@org/security-codeowners", "@org/compliance-codeowners"] on org migration
  approved_at: 2026-04-26
  next_review_at: 2026-07-26
```

Consumed by `infra/policy/rego/au_region.rego` and the Azure Policy assignment generator (subscription-scope under Topology A, resource-group-scope under Topology B — see research.md §R16).
