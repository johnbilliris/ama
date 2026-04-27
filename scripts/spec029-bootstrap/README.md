# scripts/spec029-bootstrap/

Idempotent operator scripts for the **external mutations** required by spec 029
(Progressive Delivery Pipeline). The implementation session deliberately does
**not** mutate Azure or GitHub — these scripts are run by the platform owner
after reviewing diffs.

| # | Script | Purpose | Tasks |
|---|--------|---------|-------|
| 01 | `01-invite-collaborator.ps1` | Invite a second collaborator (user-mode mitigation per ADR-029-01) | T000a |
| 02 | `02-create-federated-creds.ps1` | Create OIDC federated credentials per environment | T022 |
| 03 | `03-configure-gh-environments.ps1` | Create / configure GitHub Environments + reviewer rules | T023 |
| 04 | `04-create-entra-groups.ps1` | Create Entra ID security groups consumed by reviewer-sync | T024 |

All scripts are **idempotent** — re-runs are safe.

## Execution order

```pwsh
cd C:\code\ama
pwsh -ExecutionPolicy Bypass -File scripts\spec029-bootstrap\01-invite-collaborator.ps1 -Handle <github-handle>
pwsh -ExecutionPolicy Bypass -File scripts\spec029-bootstrap\04-create-entra-groups.ps1
# Update infra/IDENTITY.md `entra_groups:` with the printed object IDs.
pwsh -ExecutionPolicy Bypass -File scripts\spec029-bootstrap\02-create-federated-creds.ps1 -TenantId <tenant> -ResourceGroup <rg>
pwsh -ExecutionPolicy Bypass -File scripts\spec029-bootstrap\03-configure-gh-environments.ps1
```

## Pre-conditions

* `az login` against the spec-029 target tenant
* `gh auth login` with admin scope on `johnbilliris/ama`
* `infra/IDENTITY.md` reviewed and committed
