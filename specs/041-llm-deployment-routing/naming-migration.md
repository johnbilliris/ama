# Controlled purpose-name migration (T046 / FR-016)

## Status and authority

This is an optional P2 procedure, not permission to execute it. Existing explicit
deployment names may remain indefinitely. No rename, model choice, resource
creation, traffic operation or deletion is automatic. Local tests/tabletop
provide procedure verification only; target P1 release readiness and SC-006
real P2 operational acceptance remain **pending / not executed**.

G0 authorises only explicitly scoped collection/validation. G1 is the approved
target baseline; G2 current inherited governance; G3 pinned AVM compatibility.
G4 independently controls P1 release stages. None grants P2 authority.

- **G5a** independently approves a P2 proposal and replacement provisioning:
  exact target, old/new identities, unchanged proposed models/protections,
  current governance, reviewed What-If, actual quota-pool coexistence headroom,
  retained corrected rollback pair and approved migration window.
  Uncreated replacements cannot have actual readiness evidence. Its absence
  blocks **G5b**, not otherwise valid G5a provisioning.
- Under separately scoped **G0**, post-provision metadata collection proves
  provisioning success, actual parity and readiness. This permits no inference.
- **G5b** separately approves each permitted canary, switch, forward and rollback
  stage against actual readiness, exact paired revisions, window and rollback
  scope. Provisioning or canary approval does not approve a switch.
- **G6** separately approves retirement, never implied by G5 or successful tests.

## State model (human decisions, not an executable state machine)

`proposed -> approved -> replacements_ready -> switched -> verified -> retained`

Any failed forward verification leads to the separately authorised
`rolled_back` branch: restore and reverify the old corrected pair; retain both
resource sets for investigation. Without valid rollback authority, stop and
escalate through existing safety controls rather than invent permission.

`retained -> retirement_approved -> retired` is an independent G6 path.
These labels are recording states, not automatic transitions. Approval does not
prove execution; readiness does not prove a traffic switch; a CLI pass does not
advance state. Record actual outcome and supporting references after each action.

## FR-016 procedure and evidence crosswalk

| Step | Required decision/evidence | Stop / recovery rule |
| --- | --- | --- |
| 1. Propose independently | Target tenant, subscription, resource group, account, endpoint, AU region and environment; old/new names per tier; unchanged model ID/version/format/SKU/capacity/upgrade settings; approver, window, rollback triggers, verification and observation/retention criteria | P1 approval is not P2 approval; missing target/approval means stop |
| 2. Prove coexistence | Authorised actual subscription/region/model/SKU pool evidence, quota limit, old plus new allocations, other allocations and approved operational margin; shared-model tiers aggregated into one actual pool | A deployment is not new quota; missing/insufficient headroom blocks provisioning; do not increase capacity or substitute models |
| 3. Check proposal and approve G5a | Effective RAI attachment/filter content, RBAC/identity/access/network/auth/diagnostics, AU residency, unchanged embedding; current inherited governance and reviewed What-If including collision checks and operation ordering; pinned approved AVM and reviewed IaC references | No default substitution or governance assumption; G1–G3 and normal build/lint/PSRule/carve-out requirements remain external gates |
| 4. Provision and collect actual readiness | Provision only through separately approved reviewed CI/CD under G5a; leave old resources intact. G0-authorised metadata reads then compare actual replacement model/version/SKU/capacity/effective policies/access against proposal and prove successful provisioning/readiness | No canary/switch until actual readiness passes; missing actual evidence does not retroactively invalidate otherwise valid proposal-only G5a |
| 5. Prepare paired candidates | Inactive API and agents immutable image digests, revisions and complete environment snapshots; cleaned tier CSV with embedding/unambiguous legacy lookup; common/MAF/controller/all-role dispatcher compatibility | Retain old corrected matched image/configuration pair and resources; old ambiguous pre-P1 CSV is not a safe strict-reader rollback |
| 6. G5b stage approval, switch and verify | Explicit stage/window/rollback scope, actual readiness and compatible paired revisions. Approved canary uses only authorised synthetic data/capacity. After approved paired switch verify identities, isolation, truthful provenance, streaming/chat/tools/citations, degradation and audit paths; capture routes/audits | Failed forward: separately approved rollback restores both old corrected API/agents pairs, reverify and retain both sets. Never route simulation to live capacity or replay ambiguous CSV |
| 7. Retain | Explicit approved observation criteria/period, retention decision, successful rollback rehearsal and retained resources/pairs, actual post-switch evidence | No invented universal duration or expiry; failed checks retain resources for investigation |
| 8. Retire independently | Separate G6 reference; prove no active revision, worker, eval consumer or rollback target depends on old names; update operational references/evidence after separately authorised retirement | No deletion from startup, cleanup or this checker; unresolved dependency blocks G6 execution |

## Freshness, invalidation and binding

Use the target's **approved** freshness policy ID/version, approver and current
approval. It supplies explicit observation-to-use windows (or explicit null
where that policy chooses no time limit), invalidation events and
recollect/reapprove actions. No production TTL is selected here.

Bind baseline, governance, AVM, What-If, pool quota, rollback and actual readiness
to target, observation timestamp, source revision, applicable compiled
IaC/parameter revision, configuration digest, immutable API/agents images and
paired service revisions. Migration evidence binds **both** old corrected and
new pairs plus the exact proposal digest. Pre-candidate evidence needs approved
reconciliation to the exact candidate; an old approved label is insufficient.

Destination/model/protection/embedding, policy/RBAC/network, image/config,
compiled-proposal, scope changes, expiry and drift invalidate dependent evidence
as defined by the approved policy. Stop the affected stage; recollect only under
G0 and obtain applicable fresh approvals. Never infer authority from timestamps.

## Offline comparison interface (T047)

The existing four-file P1 interface and exit codes remain unchanged. Optional
`--migration <absolute JSON path> --stage <stage>` adds a read-only P2 comparison
after the supplied P1 evidence passes. The P1 candidate is the **old corrected**
rollback pair, not a baseline claim that renaming is part of P1.

Stages are `provision`, `canary`, `switch`, `forward`, `rollback`, `retain`,
`retire`. All validate G5a/proposal prerequisites; traffic stages additionally
validate actual readiness and their own G5b approval. Forward/retain/retire need
successful new-pair verification. Rollback does **not** require forward success.
Retire additionally checks observation/rehearsal and dependency evidence plus G6.

Migration JSON:

- Top-level `proposal`: complete replacement snapshot using the existing P1
  snapshot shape, including both new services; `new_bindings`: the existing four
  binding fields for those services; `window`: timezone-aware `start`/`end`.
- `decisions`: nonempty `observation`, `retention`, `rollback_triggers`.
- Common evidence metadata: `synthetic`, `target`, `observed_at`,
  `source_revision`, `approval`, `policy_id`, `policy_version`, `invalidation`,
  `bindings`. Bindings contain `old`, `new`, `old_services`, `new_services`,
  `proposal_digest` (SHA-256 of canonical sorted compact ASCII JSON) and
  `procedure_digest` (the same digest over the object containing `window` and
  `decisions`, so changed operating windows/criteria require reapproval).
- `records`: `governance`, `what_if` with explicit `passed: true`; `quota` with
  `pools`; `rollback` with exact old `services`, `retained: true` and checks;
  actual `readiness` with full `snapshot`, `provisioning_succeeded: true`,
  `ready: true` and scoped `collection_authority`; `verification` with exact new
  services, `outcome: pass` and checks; `observation` with `criteria_met`,
  `rollback_rehearsal_passed`, `retain_old`; `dependencies` with `remaining: []`.
  Each required record has common metadata and a nonempty external `reference`.
- Each pool has exact `subscription`, `region`, `model_id`, `sku`, `limit`,
  `other_allocated`, `margin`, and `allocations` mapping every old/new name to
  its capacity. Pool limits must cover their summed coexistence allocations,
  other usage and margin; quota evidence is actual-pool evidence, not a guessed
  deployment-local allowance.
- Checks explicitly cover `common`, `maf`, `controller`, `dispatcher`, `chat`,
  `streaming`, `provenance`, `isolation`. These local flags do not authenticate
  externally recorded operational outcomes; retain detailed role/tool/citation,
  degradation and audit evidence behind references.
- `approvals` map exact stage to common metadata, `reference`, `stage`, `gate`
  (`G5a` for provision, `G5b` for traffic/retain, `G6` for retire).
  Stage approval metadata binds the exact old/new pair and proposal; top-level
  approval alone is not a stage approval. Actual readiness observation must
  follow G5a approval, and a later stage approval must follow readiness approval.
- The supplied approved baseline policy must explicitly cover each required
  migration record kind and `migration`, not just the four P1 kinds.

Missing evidence fails only the evaluated stage and its prerequisites.
`--at` is test-only and requires labelled synthetic inputs including all nested
migration records/approvals. Exit 0 means **supplied-evidence comparison only**;
exit 1 invalid evidence; exit 2 invalid usage. JSON flags/approver strings are
not authenticated signatures and cannot prove real collection, approval or
readiness. The checker never calls Azure, performs inference or writes evidence.

See [migration-rehearsal.md](migration-rehearsal.md) for reproducible synthetic
branches and [verification.md](verification.md) for actual local test results.
