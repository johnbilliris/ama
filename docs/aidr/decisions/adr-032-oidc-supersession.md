# ADR-032: OIDC Federated Workload Identity (supersedes ADR-031)

## Status

Proposed (target: Accepted upon merge of spec-032 Stream-4 Stage-1 work).

**Supersedes**: [ADR-031 — AZURE_CREDENTIALS JSON Secret as a Time-Bound MVP Deviation](./adr-031-azure-credentials-mvp.md)

## Context

ADR-031 explicitly captured the `AZURE_CREDENTIALS` JSON secret as a **time-bound MVP departure** from the OIDC federated-workload-identity model that spec-029 introduced. It listed three forms of debt that the simplification incurred:

1. **Loss of automated NN-2 (Foundry carve-out) enforcement** — manual review only.
2. **Long-lived secrets in GitHub** — full-blast-radius blast in case of leak.
3. **Loss of per-workflow least privilege** — every workflow that authenticates inherits the same Service Principal RBAC.

The MVP simplification served its purpose: spec-031 was merged, the dual-pipeline footprint (spec-029 + spec-030) was eliminated, and onboarding time fell to under 30 minutes. With spec-032 (Rubric Improvements) raising the security bar (CodeQL, Defender, Sentinel, CMK, Private Endpoints, classification-aware Foundry carve-out), the MVP shape is no longer adequate; the rubric explicitly grades OIDC absence as a P1 security regression.

## Decision

The repository will **re-introduce OIDC federated workload identity** for GitHub Actions deployment authentication, **inside the simplified pipeline shape from spec-031** (no return to the spec-029 progressive-delivery complexity).

The migration runs in two stages and three environments:

### Stage 1 — Land spec-031 (already executed by spec-031)

- `AZURE_CREDENTIALS` JSON secret per environment.
- 7 days of green CD on staging + production under the simplified flow before Stage 2 begins.

### Stage 2 — Re-introduce OIDC

- Per environment in order `dev → staging → production`, each gated by 7 days of green CD on the prior environment.
- Each environment retains a `dev`/`staging`/`production` GitHub Environment (no separate `*-oidc` shadow envs).
- Authentication uses `azure/login@<sha>` with `client-id`, `tenant-id`, `subscription-id` parameters and the `permissions: id-token: write` grant on the workflow.
- A federated credential per environment subject pattern `repo:johnbilliris/ama:environment:<env>` is created in the existing workload-identity Azure AD application (one app per env to preserve env-level RBAC).
- Naming: workload-identity object IDs MUST be Bicep-parameterised or Key-Vault-referenced; **no placeholder UUIDs** (`00000000-…`) permitted (FR-I05 guardrail).
- The legacy `AZURE_CREDENTIALS` secret stays in place during Stage 2 as a fallback **only** for the duration of each environment's 7-day soak; once soak passes, the secret is rotated to a single 24-hour grace-period value, then removed.

### Identity-naming convention (carries forward FR-I05)

- **Federated credentials**: `gh-oidc-<env>` per env, subject `repo:<org>/ama:environment:<env>`.
- **Workload-identity App Registration**: `wi-drh-<env>`.
- **Resource Group RBAC**: scoped to `rg-drh-<env>` only.
- An OPA policy (new in Stream 4) MUST reject any IDENTITY-related Bicep param that contains `00000000-0000-0000-0000-000000000000`.

## Consequences

### Positive

- Restores automated NN-2 carve-out enforcement (combined with the new `infra/parameters/foundry-carveout.yaml` registry — see ADR-033).
- Eliminates long-lived secrets in GitHub Environment stores.
- Re-establishes per-environment least-privilege RBAC.
- Fully aligns with the Microsoft "passwordless" guidance for GitHub Actions → Azure auth.

### Negative / accepted

- Adds two-stage migration overhead (estimated ~1 week per environment including soak).
- Requires every `azure/login` call site to switch parameters; partially mitigated by SHA-pinning sweep (FR-C03).
- Operators wiring a brand-new environment must perform an Azure-side identity creation step before the first deploy works; documented in `docs/operator-runbooks/onboard-environment.md` (added in Stream 4).

### Not pursued

- **Single workload-identity for all envs** — rejected; defeats per-env least privilege.
- **Re-introducing the spec-029 progressive-delivery workflows** — rejected; the simplification is preserved.
- **Vault-stored signing keys for cosign** (instead of keyless) — rejected by ADR-035; OIDC keyless reuse is preferred.

## Compliance

- **Constitution NN-1 (Human-in-the-loop)**: unchanged.
- **Constitution NN-2 (Data sovereignty)**: this ADR + ADR-033 (Phi shadow boundary) + the new Foundry carve-out registry restore the deploy-time enforcement that ADR-031 documented as lost.
- **Constitution NN-3 (Privacy)**: improved (no shared SP secret in CI logs).
- **Constitution NN-4 (Interoperability)**: unchanged.
- **Constitution NN-5 (Graceful degradation)**: a documented bypass (`--auth-bypass=incident-{id}` requiring Executive + Principal Engineer co-approval) handles the case where federated credentials are unavailable during a real incident.

## References

- [ADR-031 — AZURE_CREDENTIALS JSON Secret as a Time-Bound MVP Deviation](./adr-031-azure-credentials-mvp.md)
- [Spec 032 — AMA Rubric Improvements](../../../specs/032-rubric-improvements/spec.md) (FR-S02, FR-S02a, FR-S02b)
- [GitHub Actions OIDC + Azure docs](https://learn.microsoft.com/en-us/azure/developer/github/connect-from-azure-openid-connect)

---
*Author: Solution Architect persona via spec-032 Stream-0. Date: 2026-04-30.*
