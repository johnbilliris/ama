# T027 — Surviving-workflow review + T028 — three FR-020 recommendations

This file is the binding output of FR-019 (review every remaining workflow) and FR-020 (present three concrete recommendations with structure: proposed change / reason / trade-off, requesting individual accept/reject/modify response). Per the maintainer's standing directive ("adopt your recommended option if still not resolved after consulting Constitution and specs"), each recommendation here also carries an **implementation default** that takes effect unless overridden at PR review time.

---

## T027 — Workflow review notes (one paragraph per surviving workflow)

| File | Touches Azure? | Auth path | Action versions pinned correctly? | Verdict |
|---|---|---|---|---|
| `.github/workflows/ci.yml` | No | n/a | `actions/checkout@v5`, `actions/setup-python@v6`, `actions/setup-node@v5`, `pnpm/action-setup@v5`, `actions/upload-artifact@v6` — all current majors. ✓ | **RELEVANT** — no change beyond the branches list edit (T013). |
| `.github/workflows/cd.yml` | Yes | `azure/login@v3` with `creds: ${{ secrets.AZURE_CREDENTIALS }}` ✓ | `actions/checkout@v5`, `Azure/setup-azd@v2`, `azure/login@v3` ✓ | **RELEVANT** — fully rewritten in T014/T017 to the spec-031 contract. |
| `.github/workflows/drift-detection.yml` | Yes | `azure/login@v3` with `creds: ${{ secrets.AZURE_CREDENTIALS }}` ✓ | `actions/checkout@v5`, `azure/login@v3` ✓ | **RELEVANT** — matrix scope `[staging, production]` pinned via FR-011 annotation; `id-token: write` dropped. |
| `.github/workflows/eval-pr-gate.yml` | Yes | `azure/login@v3` with `creds: ${{ secrets.AZURE_CREDENTIALS }}`; `environment: dev` ✓ | `actions/checkout@v5`, `actions/setup-python@v6`, `azure/login@v3`, `actions/github-script@v7` ✓ | **RELEVANT** — migrated per FR-019a; resolves auth from the `dev` GitHub Environment. |
| `.github/workflows/eval-publish-dataset.yml` | Not yet (commented Azure block) | When activated: `azure/login@v3` with `creds:` (per FR-019b rewrite) | `actions/checkout@v5`, `actions/setup-python@v6`, `actions/upload-artifact@v6` ✓ | **RELEVANT** — commented block now correct; `id-token: write` dropped at workflow level (T020 + cleanup). Activation note added directing the operator to set the `environment:` key. |

**No workflow flagged DEPRECATE.** All five remaining files are aligned with spec 031 and pin a current major for every action they consume.

---

## T028 — Three FR-020 recommendations

### Recommendation A: Re-introduce automated NN-2 Foundry-carve-out enforcement

**Proposed change**
Re-author a minimal Azure Policy + GitHub Actions check that evaluates any new model-hosting endpoint introduced in Bicep against a version-controlled carve-out list (the prior `infra/policy/foundry-carveout.yaml` was deleted in T009 because its only consumer was the spec-029 `posture-verifier`). Implementation candidates:
1. **Azure Policy assignment** (definitive): a `deny` policy at the subscription scope that blocks any `Microsoft.MachineLearningServices/workspaces` or `Microsoft.CognitiveServices/accounts` deployment outside Australia regions unless the resource carries a tag `carve-out-approved=<id>` that matches a row in a small `infra/policy/foundry-carveout.yaml` (re-added). Enforced in Azure, not GitHub.
2. **GitHub Actions check** (lighter): a job in `ci.yml` that runs `bicep build` and greps the IL output for `Microsoft.CognitiveServices/accounts.*location: ` lines whose location is not in `[australiaeast, australiasoutheast]`, fails the build unless an `infra/policy/foundry-carveout.yaml` row authorises it.

**Reason**
Constitution NN-2 requires this enforcement. Spec 031 deletes the spec-029 implementation but the principle remains binding (see ADR-031 Consequence (b)). Until reinstated, the control is operator review, which is a known-soft control.

**Trade-off / cost**
Option 1 (Azure Policy) is the right architectural answer but requires Owner-level policy deployment and a few days of Bicep authoring. Option 2 (CI gate) is ~half a day of work, lower assurance (can be bypassed by force-pushing past CI), but materially better than the current "manual review" baseline.

**Implementation default if no override**: Adopt Option 2 in a follow-up PR (~half-day estimate); track Option 1 as a longer-term item in the same ADR-031 review trigger queue.

**Owner** (recommended): `compliance-auditor` agent + `azure-principal-architect` review.

---

### Recommendation B: Plan and execute the OIDC migration that supersedes `AZURE_CREDENTIALS`

**Proposed change**
File a follow-up spec (e.g., `032-restore-oidc`) that replaces the per-environment `AZURE_CREDENTIALS` JSON secret with OIDC federated credentials per environment, removing the long-lived `clientSecret` from GitHub. Pull only the parts of the spec-029 OIDC machinery that are net additive (the `azure/login@v3 with: client-id/tenant-id/subscription-id` form plus the federated-credential bootstrap script), without re-introducing the `setup-oidc-azure` composite action's IDENTITY-topology assertion (that was over-engineered for a single-tenant repo).

**Reason**
ADR-031 is **explicitly time-bound**. The four review triggers it lists (pre-GA, governance checkpoint, secret leakage, carve-out expansion) all point to OIDC migration as the resolution. Filing the spec now prevents the "technical debt entry that no-one schedules" failure mode.

**Trade-off / cost**
~1–2 days to author the spec; ~half a day per environment to provision federated credentials in Entra; ~half a day of workflow YAML edits. Total ~3–4 days. Risk of regression is low because OIDC is an additive change to the same `azure/login` action.

**Implementation default if no override**: File the spec stub (`specs/032-restore-oidc/spec.md`) within 30 days of merging spec 031. Do not block spec 031 on this.

**Owner** (recommended): `security-engineer` agent + `infrastructure-devops` for execution.

---

### Recommendation C: Add `actionlint` as a CI gate for workflow files

**Proposed change**
Add a new step in `ci.yml` (and/or pre-commit hook) that runs [`rhysd/actionlint`](https://github.com/rhysd/actionlint) over `.github/workflows/*.yml`. Fail the job on any error; warn-only on style issues. Pin the action version to a current SHA.

**Reason**
This spec discovered a non-trivial number of latent issues in the workflow YAML during human review (stale branch list in `ci.yml`, dangling `id-token: write` permissions, version drift between `azure/login@v2` and `@v3`). `actionlint` catches the structural class of these issues before merge. Plan §Testing already lists this as "available locally; not added as a gate" — promoting it to a gate is the natural next step.

**Trade-off / cost**
Adds ~5 seconds to every CI run. May surface false positives in shellcheck rules embedded in `run:` blocks (manageable via `# actionlint disable` annotations). One-time effort: ~1 hour to add and tune. Ongoing: zero.

**Implementation default if no override**: Add the gate in the same PR as spec 031, OR in an immediate follow-up if the maintainer prefers a smaller spec-031 PR diff.

**Owner** (recommended): `infrastructure-devops` agent + `qa-test-engineer` review.

---

## Maintainer sign-off (to be filled at PR review)

For each recommendation, the maintainer responds with one of: **ACCEPT** (proceed with the implementation default in a follow-up issue), **REJECT** (record rationale), or **MODIFY** (specify the change).

| Rec | Disposition | Notes |
|---|---|---|
| A — Re-introduce NN-2 carve-out enforcement | _(awaiting maintainer)_ | |
| B — Plan OIDC migration (spec 032) | _(awaiting maintainer)_ | |
| C — Add `actionlint` CI gate | _(awaiting maintainer)_ | |

Until the dispositions are filled, the implementation defaults above apply.
