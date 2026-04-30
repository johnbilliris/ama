# Spec 032 — FR-I05 status note

**FR-I05** required resolution of placeholder Entra group object IDs (`00000000-…`) in `IDENTITY.md`, `setup-oidc-azure.yml`, and `identity_consistency.rego`.

**Current state on the working branch (032-rubric-improvements ← cfa52d4 main)**:

```
$ Get-ChildItem -Recurse -Filter "IDENTITY.md"          # → no results
$ Get-ChildItem -Recurse -Filter "identity_consistency*" # → no results
$ Get-ChildItem .github/actions/setup-oidc-azure        # → no results
```

These files were **removed by spec 031** (simplify CI/CD) which deleted the spec-029 progressive-delivery footprint, including:
- `infra/IDENTITY.md`
- `infra/policy/rego/identity_consistency.rego`
- `.github/actions/setup-oidc-azure/`

The "placeholder UUIDs" rubric finding therefore no longer has live targets on this branch. **FR-I05 is satisfied by the spec-031 deletion**, with the caveat that spec-032 FR-S02b (OIDC re-introduction Stage 2) MUST author new identity wiring without re-introducing placeholder UUIDs.

**Action items carried forward into Stream 4 (T413–T415)**:
1. ADR-032 (T011) MUST capture identity-naming conventions (no placeholders allowed).
2. Stage-2 OIDC rollout MUST resolve real Entra group + workload-identity object IDs at deploy time via Bicep parameters or a Key Vault reference; the values MUST NOT be hard-coded in YAML/.rego.
3. A new `identity_consistency.rego` (if re-introduced) MUST validate that `00000000-0000-0000-0000-000000000000` is rejected.

**T008 status**: ✅ Resolved (deletion already executed by spec 031; downstream guardrails captured for the OIDC re-introduction).
