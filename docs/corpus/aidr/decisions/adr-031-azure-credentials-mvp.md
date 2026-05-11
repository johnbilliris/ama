# ADR-031: AZURE_CREDENTIALS JSON Secret as a Time-Bound MVP Deviation from OIDC

## Status

Accepted (time-bound)

## Context

Spec `029-progressive-delivery-pipeline` introduced OIDC federated credentials
for every environment, enforced through the composite action
`.github/actions/setup-oidc-azure` and the `infra/IDENTITY.md` topology
trust-root. That setup required, per environment:

- One Entra workload identity with a federated credential per workflow ref.
- A maintained `infra/IDENTITY.md` mapping subscription IDs to environment
  names, validated at deploy time by `infra/policy/rego/identity_consistency.rego`.
- A repository-level `permissions: id-token: write` grant on every workflow
  that touched Azure.
- A second-collaborator pre-flight (T000a in spec 029) plus the
  `@johnbilliris/ama-spec-maintainers` team ownership model.

For MVP delivery — onboarding a new contributor must be doable in under 30
minutes against a freshly cloned repo and a freshly created Azure subscription
— the OIDC plumbing was the dominant operator burden. Spec
`031-simplify-cicd-pipeline` collapses authentication to a single
`AZURE_CREDENTIALS` JSON secret stored per GitHub Environment, consumed via
`azure/login@v3 with: creds:`.

This is a deliberate, temporary departure from the previous OIDC standard.

## Decision

The repository will, for the duration of the MVP, authenticate to Azure
from GitHub Actions using a single per-environment GitHub Actions secret
named `AZURE_CREDENTIALS`. The secret holds the JSON object produced by
`az ad sp create-for-rbac --sdk-auth`, containing at minimum:

```json
{
  "clientId": "<uuid>",
  "clientSecret": "<long-lived secret>",
  "subscriptionId": "c8703ebc-bc5d-488d-9489-5883c9fde6c2",
  "tenantId": "b5e5570f-671d-4290-9a28-52c53214f03d",
  "activeDirectoryEndpointUrl": "https://login.microsoftonline.com",
  "resourceManagerEndpointUrl": "https://management.azure.com/",
  "activeDirectoryGraphResourceId": "https://graph.windows.net/",
  "sqlManagementEndpointUrl": "https://management.core.windows.net:8443/",
  "galleryEndpointUrl": "https://gallery.azure.com/",
  "managementEndpointUrl": "https://management.core.windows.net/"
}
```

The full schema and validation rules are pinned in
`specs/031-simplify-cicd-pipeline/contracts/azure-credentials.schema.json`.

The OIDC composite action (`setup-oidc-azure`), the IDENTITY trust-root
(`infra/IDENTITY.md`), and the per-workflow `id-token: write` permission are
removed as part of spec 031.

## Consequences

### (a) Long-lived `clientSecret` requires manual rotation

Each `clientSecret` is valid for 12 months by default. Spec 031's
`quickstart.md` documents a **90-day manual rotation cadence** per
environment. Until the OIDC migration (see Review trigger below) lands,
rotation discipline is enforced by operator process, not pipeline gate.

### (b) Loss of automated NN-2 Foundry-carve-out enforcement

Spec 029 added `infra/policy/foundry-carveout.yaml` and the
`posture-verifier` to enforce the Constitution Non-Negotiable #2 carve-out
permitting Microsoft Foundry model-hosting endpoints in non-AU regions.
Spec 031 deletes both, because they were uniquely consumed by the deleted
spec-029 workflows.

The **constitutional requirement is unchanged**. What is lost is the
*automated* check at deploy time. Until carve-out automation is
re-introduced (tracked as one of the three FR-020 recommendations
surfaced by spec 031), any PR introducing a Foundry model-hosting region
MUST be reviewed by the security and compliance personas per
Constitution NN-2 last paragraph (operator-driven control).

### (c) Easier operator onboarding

A new contributor configures one secret per environment instead of:
federated-credential creation in Entra, ID validation, IDENTITY.md
update, and OIDC permissions plumbing. Time-to-first-deploy reduces from
~2 hours to under 30 minutes.

## Trade-offs Accepted

| Trade-off | Impact | Acceptable because |
|---|---|---|
| Long-lived secret in GitHub | Larger blast radius on leak (clientSecret valid for months, not minutes) | Mitigated by 90-day rotation; secret is environment-scoped (not repo-scoped); GitHub masks it in logs |
| Manual rotation burden | Operator must remember 90-day cadence per environment (3 secrets total) | Acceptable for MVP scope; rotation runbook in `quickstart.md`; calendar reminder is the recommended control |
| Loss of identity-topology validation | A misconfigured SP (wrong subscription, wrong scope) deploys to the wrong place silently | Mitigated by the 1:1 branch-to-environment binding in spec 031 (the SP simply cannot reach a different subscription if it lacks the role); residual risk accepted for MVP |
| Loss of automated Foundry-carve-out enforcement | A PR could introduce a non-AU model-hosting region without the policy bot catching it | Mitigated by manual reviewer process per NN-2; surfaced as FR-020 Recommendation A so the maintainer can re-prioritise re-introduction explicitly |

## Review Trigger

This ADR is reviewed and re-evaluated when **any** of the following occurs,
whichever is first:

1. **Before public General Availability** of the disaster-response platform.
2. **At the next governance checkpoint** (next quarterly architecture review).
3. **Upon any production-secret leakage incident** (immediate review and
   acceleration of the OIDC migration regardless of cadence).
4. **Upon expansion** of the Foundry carve-out list to cover a new region
   (the loss of automated enforcement noted in Consequence (b) becomes
   higher-risk at that point).

When triggered, the review MUST decide one of: (a) re-introduce OIDC and
delete this ADR, (b) extend this ADR for a further bounded period with
revised review trigger, or (c) accept the deviation permanently with a
formal Constitution amendment.

## Owner

`johnbilliris` (repo owner) — to be re-confirmed and replaced with a team handle (`@johnbilliris/ama-spec-maintainers` or successor) when the dual-control governance team is provisioned (cross-reference: `.github/CODEOWNERS` interim-fallback comment lines 22-25).

Contact: as recorded against `johnbilliris` on github.com/johnbilliris.

## Links

- This decision was driven by [`specs/031-simplify-cicd-pipeline/spec.md`](../../../specs/031-simplify-cicd-pipeline/spec.md).
- Supersedes (operationally, not formally) the OIDC pattern documented in
  ADR-029-01 (referenced inside the now-deleted
  `.github/actions/setup-oidc-azure/action.yml` and the deleted
  `infra/IDENTITY.md`).
- Constitution clause referenced: NN-2 (Data sovereignty) and its
  Foundry-carve-out paragraph; see
  `.specify/memory/constitution.md` v1.2.0.
- Rotation runbook: [`specs/031-simplify-cicd-pipeline/quickstart.md`](../../../specs/031-simplify-cicd-pipeline/quickstart.md)
  §"Rotate `AZURE_CREDENTIALS` (every 90 days)".
- Schema for the secret payload: [`specs/031-simplify-cicd-pipeline/contracts/azure-credentials.schema.json`](../../../specs/031-simplify-cicd-pipeline/contracts/azure-credentials.schema.json).

---
*Created 2026-04-30 as part of spec 031.*
