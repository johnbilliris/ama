# Quickstart — Progressive Delivery Pipeline (029)

This quickstart covers the four operator/developer flows introduced or evolved by feature 029. Read top-to-bottom for the first time; thereafter, jump to the section you need.

---

## 1. Issue a `dev` API key for local development (FR-030 / Q6)

```bash
gh workflow run dev-key-issue.yml \
    -f service=cosmos \
    -f reason="local debugging of incident-ingest pipeline" \
    -f ttl_hours=24

# Wait for the run to complete, then resolve the secret path:
SECRET_PATH="kv-ama-dev/secrets/devkey-${USER}-cosmos"

# Use Azure CLI to fetch the value (only your own Entra ID has 'get' on this secret):
az keyvault secret show --vault-name kv-ama-dev --name "devkey-${USER}-cosmos" --query value -o tsv
```

Notes:
- TTL is capped at 24 h. Re-run the workflow at most once a day; old keys for the same `{alias, service}` are automatically revoked.
- The secret MUST NEVER be committed; the PR-gate secret-scan blocks merges that contain it.
- This workflow is the ONLY supported path to a `dev` key. Direct portal key reads will be denied (no standing key-read RBAC on `dev` data-plane resources).

---

## 2. Reach a `staging` or `production` backend from your laptop (FR-027 / Q5)

There is no point-to-site VPN, no public endpoint, and no shared key. The supported pattern is Bastion + jump-host + Entra PIM:

```bash
# 1. Activate the role (default 1h, max 8h) via PIM.
az role assignment create \
  --role "AMA Staging Jump Host User" \
  --assignee "${UPN}" \
  --scope "/subscriptions/.../rg-ama-staging-australiaeast/providers/Microsoft.Compute/virtualMachines/vm-ama-jump-staging-ae" \
  --condition "PIM-activated"  # placeholder; PIM activation is via portal or 'az ad role'

# 2. Connect via Bastion (browser SSH or 'az network bastion ssh').
az network bastion ssh \
  --name bastion-ama-staging-ae \
  --resource-group rg-ama-staging-australiaeast \
  --target-resource-id "/subscriptions/.../vm-ama-jump-staging-ae" \
  --auth-type AAD

# 3. From inside the jump host, hit the backend with Managed Identity (no keys, ever):
DefaultAzureCredential().get_token("https://cosmos.azure.com/.default")
```

If you find yourself reaching for a shared key on `staging` / `production`, you have hit a posture rule and the IaC policy gate WILL block the change (FR-028).

---

## 3. Activate / deactivate the Incident-Mode Change Freeze (FR-011)

```bash
# Activate (only members of ama-oncall-sre OR ama-incident-commander succeed):
gh workflow run change-freeze.yml \
    -f action=activate \
    -f reason="SEV-1 in incident workspace; pausing all non-emergency promotions"

# Deactivate (same authority required):
gh workflow run change-freeze.yml \
    -f action=deactivate \
    -f reason="SEV-1 closed; resuming auto-promotion"
```

While the freeze is active:
- All in-flight non-emergency canaries hold at their current % (no advance, no rollback unless fast-burn fires).
- All subsequent merges queue without deploying to production.
- The `emergency-hotfix` lane remains open with the 2-person rule (see § 4).
- Activation and deactivation are written to the audit store with `actor`, `timestamp`, `reason`.

---

## 4. Land an emergency hotfix during freeze (FR-011a, FR-012)

1. Open a PR labelled `emergency-hotfix` and reference the open incident in the description.
2. Run the full PR gate set; `lint`, `typecheck`, `unit`, `contract`, `SAST`, `secret_scan`, `dependency_audit`, `container_scan`, `iac_policy`, `signature/SBOM/provenance verification`, and (when infra is touched) `bicep_whatif` MUST all pass. Posture-matrix gate is NON-skippable (FR-028).
3. Two distinct members of `ama-emergency-approver`, neither equal to the PR author, MUST review the PR. The pipeline verifies group membership at merge time.
4. Merge → `emergency-hotfix.yml` deploys directly to production canary, skipping ONLY: `integration_full`, `simulation_replay`, `accessibility_full`, `load_smoke`, `chaos_lite`.
5. Within 24 h of deploy, the deferred gates MUST be reconciled and the evidence pack updated; `evidence-pack.yml` runs a follow-up reconciliation pass and opens a tracked critical issue if any gate fails.

---

## 5. Add a posture-matrix exception (FR-033 / Q9)

1. Open a PR adding a single entry to `infra/policy/posture-exceptions.yaml`:
   ```yaml
   - name: cosmos-shared-key-legacy-tenant
     resource_id: /subscriptions/.../databaseAccounts/legacydb
     environment: production
     deviating_rule: identity.shared_key_disabled
     justification: "Legacy tenant client cannot rotate to MI before 2026-Q3."
     compensating_controls:
       - "Key held only in kv-ama-prod accessible to single MI id-ama-tenant-bridge"
       - "Defender for Cosmos enabled with high-severity alerting"
     owning_team: "@ama/integration"
     issued_at: 2026-04-26
     expires_at: 2026-07-25  # MUST be ≤ 90 days after issued_at
     dual_approvers: ["@security-owner-gh", "@compliance-owner-gh"]  # Per ADR-029-01 (research.md §R17): under user-owned mode, this field MUST list the two distinct GitHub accounts that actually approved the PR (e.g., `@johnbilliris` and the second collaborator from T000a). The `@security-owner-gh`/`@compliance-owner-gh` placeholders shown here are restored verbatim once the repository migrates into a GitHub organisation.
     audit_pointer: "auditstore/devops/posture_exception/cosmos-shared-key-legacy-tenant"
   ```
2. CODEOWNERS requires the security and compliance personas to approve. **Per ADR-029-01 (research.md §R17), under the current user-owned repository the CODEOWNERS handle is `@johnbilliris` and dual approval is enforced via branch protection's "require 2 approving reviews"; on org migration this restores to BOTH `@org/security-codeowners` AND `@org/compliance-codeowners`.**
3. Merge → entry is honoured by the OPA gate, the runtime Azure Policy initiative, and the post-deploy posture verifier (FR-031).
4. The daily `posture-exception-sweep.yml` workflow auto-removes the entry on `expires_at`. To renew, open a fresh PR with a new `issued_at` — silent extension is prohibited.

---

## 6. Retrieve an evidence pack for a production change (FR-013 / SC-012)

```bash
# Look up the audit event for the promotion (SC-012: < 15 min end-to-end):
az cosmosdb sql query \
  --account-name "${AUDIT_COSMOS}" \
  --database-name audit \
  --container-name events \
  --query-text "SELECT TOP 1 * FROM c WHERE c.action = 'evidence.write' AND c.correlation_id = '${PR_NUMBER}' ORDER BY c.timestamp DESC"

# Result includes evidence_uri; download the pack:
az storage blob download \
  --account-name "${EVIDENCE_STORE_AU}" \
  --container-name evidence \
  --name "${pack_path}" \
  --file ./evidence.zip \
  --auth-mode login

# Inspect the manifest (validates against contracts/evidence-pack.schema.json):
unzip -p evidence.zip manifest.json | jq .
```

Attempts to modify or delete an evidence pack within its 7-year retention window are denied by the storage immutability policy and recorded as security events.

---

## 7. Add a Foundry carve-out entry (FR-018 / Constitution v1.2.0)

Only when a required model is unavailable in `australiaeast`:

1. Add to `infra/policy/foundry-carveout.yaml`:
   ```yaml
   - model_name: gpt-4.1
     region: eastus2
     resource_id: /subscriptions/.../accounts/foundry-ama-eastus2
     business_justification: "Required model not available in australiaeast as of 2026-04."
     approver_identities: ["@johnbilliris"]  # ADR-029-01; restore ["@org/security-codeowners", "@org/compliance-codeowners"] on org migration
     approved_at: 2026-04-26
     next_review_at: 2026-07-26
   ```
2. CODEOWNERS requires both security and compliance approval (under user-owned-repo mode this collapses to `@johnbilliris` plus branch-protection's 2-reviewer rule per ADR-029-01).
3. The OPA `au_region.rego` rule uses this list as the SOLE exception path; every other non-AU resource is denied at PR gate AND at Azure Policy runtime.
4. The platform's model gateway routes traffic to the carve-out endpoint with mandatory data-minimisation (PSPF strip + PII redact) before transit.

---

## Operational dashboards

- **Lead time / change failure rate / MTTR** (FR-020): Azure Monitor workbook `ama-pipeline-dora`.
- **Posture drift open / age** (FR-019): GitHub project board filtered on `infrastructure-drift` + `posture-violation` labels.
- **Posture exceptions** (FR-033): GitHub project board derived from `posture-exceptions.yaml`; auto-updated by `posture-exception-sweep.yml`.
- **Foundry carve-out review** (FR-018): quarterly review issue auto-opened against the security and compliance personas.
