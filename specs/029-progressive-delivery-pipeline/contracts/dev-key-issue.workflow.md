# Workflow contract: `dev-key-issue.yml`

**Source**: spec.md FR-030 (Q6 issuance mechanism). This contract pins the inputs, the OIDC verification rules, the side-effects, and the audit-event shape.

## Trigger

```yaml
on:
  workflow_dispatch:
    inputs:
      service:
        description: "Target dev service to issue/rotate a key for."
        type: choice
        required: true
        options: [cosmos, storage, keyvault, servicebus, eventgrid]
      reason:
        description: "Short business reason (logged to audit)."
        type: string
        required: true
      ttl_hours:
        description: "Key TTL (hours). Default 24, max 24."
        type: number
        required: false
        default: 24
```

## Identity & authority

- The workflow MUST run on `ubuntu-22.04` GitHub-hosted runner.
- The workflow MUST authenticate to Azure via the federated workload identity `id-ama-pipeline-dev-keyops` whose subject is `repo:johnbilliris/ama:environment:dev-keyops`.
- The triggering actor (`github.actor`) MUST be a member of the `ama-developers` Entra ID group; the workflow re-verifies this via Microsoft Graph and FAILS CLOSED otherwise.
- No human or service principal MAY hold a standing Cosmos/Storage/etc. key-management role outside this workflow's runtime — the dev key-management roles are PIM-eligible to `id-ama-pipeline-dev-keyops` only.

## Steps (contract)

1. Resolve developer alias from `github.actor` (Entra ID lookup).
2. Mint or rotate the requested key via the Azure SDK against the corresponding `dev` resource.
3. Write the key to `kv-ama-dev` at path `secrets/devkey-{alias}-{service}`, with `expires_on = now + ttl_hours` (capped at 24h).
4. Set Key Vault access policy on the new secret so that ONLY the developer's Entra ID has `get`.
5. Revoke any prior key for `{alias, service}`.
6. Emit an Audit Event (see schema):
   ```json
   {
     "actor": "{developer-entra-oid}",
     "timestamp": "<utc>",
     "action": "devkey.issue",
     "rationale": "{inputs.reason}",
     "outcome": "success|failure|denied",
     "service": "{inputs.service}",
     "environment": "dev",
     "digest": "{sha256-of-key-id}",
     "correlation_id": "{github-run-id}"
   }
   ```
7. The output of the workflow is ONLY the Key Vault path; the secret value is NEVER printed to logs.

## Failure modes

| Condition | Behaviour |
|---|---|
| Triggering actor is not in `ama-developers` group | FAIL CLOSED, emit audit event with `outcome=denied` |
| `ttl_hours > 24` | FAIL CLOSED, emit audit event with `outcome=denied` |
| Target service is not in the enum | FAIL CLOSED at workflow input validation |
| Azure SDK rotation fails | FAIL CLOSED, emit audit event with `outcome=failure`, leave prior key intact |

## Non-goals

- This workflow is NOT a path to issuing `staging` / `production` keys. Any attempt to extend it to those environments MUST be rejected at PR review and is a posture-matrix violation by definition.
