---
# AMA Progressive Delivery Pipeline — Identity Trust Root (spec 029)
# Parsed at runtime by .github/workflows/_reusable/setup-oidc-azure.yml (T005)
# Validated statically by infra/policy/rego/identity_consistency.rego (T008b)
subscription_topology: B   # 'A' = sub-per-env, 'B' = single-sub-RG-per-env
codeowners_handle_mode: user   # 'team' (org-owned) or 'user' (user-owned, current)
second_collaborator: null   # GitHub handle of second human; populate via T000a script
entra_groups:
  - name: ama-oncall-sre
    object_id: 00000000-0000-0000-0000-000000000000   # populate via T024 bootstrap script
  - name: ama-incident-commander
    object_id: 00000000-0000-0000-0000-000000000000
  - name: ama-emergency-approver
    object_id: 00000000-0000-0000-0000-000000000000
production_reviewers_mode: individual_union   # 'scim_team' (org) | 'individual_union' (user-owned)
migration_trigger: |
  Repository migrates from user-owned (johnbilliris/ama) into a GitHub
  organisation. On migration, flip codeowners_handle_mode -> team,
  production_reviewers_mode -> scim_team, restore @org/<team> handles per
  research.md §R17 future-state mapping table.
topology_subscription_ids:
  dev: c8703ebc-bc5d-488d-9489-5883c9fde6c2
  staging: c8703ebc-bc5d-488d-9489-5883c9fde6c2
  production: c8703ebc-bc5d-488d-9489-5883c9fde6c2
---

# IDENTITY.md — Trust Root for the Progressive Delivery Pipeline

This file is the **single canonical source of truth** for pipeline identity
decisions. It is referenced by:

- `T005` reusable OIDC action — runtime topology assertion
- `T008b` `identity_consistency.rego` — static counterpart
- `T008` `.github/CODEOWNERS` — handle mode declaration
- `T019a` Bicep `subscriptionTopology` parameter — policy assignment scope
- `T023` GitHub Environments configuration — `AZURE_SUBSCRIPTION_ID` per env
- `T024` Entra group provisioning + `reviewer_sync.py` — reviewer list source
- `T044` emergency-hotfix workflow — second-collaborator gate
- `T084` quickstart — operator onboarding section

## Schema (front-matter keys)

| Key | Type | Allowed values | Description |
|---|---|---|---|
| `subscription_topology` | string | `A` \| `B` | A = subscription-per-env (recommended); B = single-sub, RG-per-env (sandbox/MCAP) |
| `codeowners_handle_mode` | string | `team` \| `user` | `team` requires org-owned repo; `user` is the ADR-029-01 fallback |
| `second_collaborator` | string \| null | GitHub handle | Required under `user` mode for FR-033 dual-approver; null until T000a runs |
| `entra_groups` | array | `{name, object_id}` | Three Entra groups: `ama-oncall-sre`, `ama-incident-commander`, `ama-emergency-approver` |
| `production_reviewers_mode` | string | `scim_team` \| `individual_union` | `scim_team` = SCIM-synced GitHub teams (org); `individual_union` = each member as individual reviewer (user-owned) |
| `migration_trigger` | string | free text | The condition under which the user-mode fallback reverts |
| `topology_subscription_ids` | object | `{dev, staging, production}` → GUID | Under Topology B all three values are identical |

## Worked examples

### Topology A + organisation-owned repo (recommended target)

```yaml
subscription_topology: A
codeowners_handle_mode: team
second_collaborator: null   # not required under team mode
entra_groups:
  - name: ama-oncall-sre
    object_id: 11111111-1111-1111-1111-111111111111
  - name: ama-incident-commander
    object_id: 22222222-2222-2222-2222-222222222222
  - name: ama-emergency-approver
    object_id: 33333333-3333-3333-3333-333333333333
production_reviewers_mode: scim_team
migration_trigger: "n/a — already migrated"
topology_subscription_ids:
  dev:        aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa
  staging:    bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb
  production: cccccccc-cccc-cccc-cccc-cccccccccccc
```

### Topology B + user-owned repo (current)

See the front-matter at the top of this file.

## Runtime-vs-static consistency model

- **Runtime** (T005): `setup-oidc-azure.yml` parses this front-matter on every
  workflow run, asserts `AZURE_SUBSCRIPTION_ID == topology_subscription_ids[$env]`,
  exports `AMA_SUBSCRIPTION_TOPOLOGY` for downstream audit-event stamping, and
  emits an audit `gate.decision` / `denied` on mismatch.
- **Static** (T008b): `identity_consistency.rego` cross-checks this file against
  `infra/parameters/{dev,staging,production}.bicepparam`, `.github/CODEOWNERS`,
  and the runtime `production_reviewers_mode` cap (≤ 6 under `individual_union`).
  Run as a `conftest` job in CI.

## CODEOWNERS handle mode

The current value `codeowners_handle_mode: user` reflects ADR-029-01 (research.md
§R17). All `.github/CODEOWNERS` entries use the individual handle `@johnbilliris`.
The dual-approver requirement (FR-033) is enforced by branch protection's
"require 2 approving reviews" plus the second-collaborator pre-flight (T000a).

To migrate to `team` mode after org migration:
1. Edit this file: `codeowners_handle_mode: team`, `production_reviewers_mode: scim_team`.
2. Substitute `@johnbilliris` with team handles per research.md §R17 table.
3. Re-run `T008b` Rego — it will re-validate the new handle pattern.
