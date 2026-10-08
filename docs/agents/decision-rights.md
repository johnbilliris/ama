# Agent Decision-Rights Matrix

**Purpose**: explicit decide-vs-escalate rights per agent, satisfying FR-AG01. Pairs with the Saga workflow doc and the kill-switch + autonomy-dial controls.

> **Defaults** below assume `autonomy_level = standard`. The autonomy dial (FR-AG02) can constrain (`low`) or expand (`high`) these rights per environment + jurisdiction policy. Anything ranked **must escalate** is non-overridable: the operator-in-the-loop is constitutional (NN-1).

## Monitoring Agent

| Capability | Decide | Escalate | Notes |
|---|---|---|---|
| Triage signal hazard class | ✓ | | Confidence ≥ 0.8 to handoff |
| Append timeline event | ✓ | | Audit-only |
| Open new incident | | → Operations Officer | Operator-confirmed |
| Suppress repeat signals | ✓ (≤ 5 min) | → Planning Officer (> 5 min) | |

## Risk Assessment Agent

| Capability | Decide | Escalate | Notes |
|---|---|---|---|
| Generate recommendation | ✓ | | Always reviewable |
| Set risk tier (NERAG) | ✓ | | Always |
| Mark life-safety severity | | → Incident Commander | Constitution NN-1 |
| Trigger Evacuation Agent | ✓ if non-life-safety; → IC otherwise | | |
| Trigger Communication Agent | ✓ for proposed alert; publish requires IC approval | | |

## Evacuation Agent

| Capability | Decide | Escalate | Notes |
|---|---|---|---|
| Plan phased evacuation routes | ✓ | | Plan only |
| Recommend evacuation type | ✓ | | Directed/Recommended/Self-initiated draft |
| Issue evacuation order | | → IC + Public Information Officer | Constitution NN-1 |
| Update sheltering options | ✓ | | |
| Mark vulnerable populations priority | ✓ | | Constitution VI-C |

## Resource Allocation Agent

| Capability | Decide | Escalate | Notes |
|---|---|---|---|
| Allocate resources within delegated thresholds | ✓ | | Per Logistics Officer policy |
| Allocate cross-jurisdiction resources | | → IC + Logistics Officer | |
| Commit > 50% of any resource bucket | | → Executive Leader | |
| Escalate medical surge | | → Health sector + IC | |

## Communication Agent

| Capability | Decide | Escalate | Notes |
|---|---|---|---|
| Draft alert message | ✓ | | Always reviewable |
| Adapt to multilingual + accessibility | ✓ | | Per jurisdiction policy `language_priorities` |
| Pass output through Content Safety | ✓ | | Mandatory |
| **Publish** to channels (live) | | → IC | Constitution NN-1 + V (warnings); delegated drafting does not grant dispatch approval |
| Issue de-escalation / all-clear | | → IC | Constitution V-A |

## Dependency Notifier Agent

| Capability | Decide | Escalate | Notes |
|---|---|---|---|
| Detect upstream invalidation | ✓ | | |
| Notify affected operators | ✓ | | Information-only push |
| Open invalidation incident | | → IC | |

## Cross-cutting

- **Kill-switch toggle**: requires Entra `IncidentCommander` or `ExecutiveLeader` role + justification + dual-approval in production (FR-AG05a). Audit-logged.
- **Autonomy-dial change**: same governance as kill-switch.
- **Foundry carve-out registry mutation**: requires 2 approver signatures + OPA policy validation; deny-by-default if quorum missing.
- **Documented bypass workflows** (`--coverage-bypass`, `--eval-bypass`, `--cosign-bypass`, `--auth-bypass`): all require Executive + Principal Engineer co-approval, time-boxed, audit-logged, page-routed.
- **Rehearsal synthetic egress**: simulation outputs can be published only to synthetic channels and does not relax live IC approval for public dispatch.

## Review cadence

Quarterly by Solution Architect + Incident Commander persona; per-jurisdiction overrides reviewed when jurisdiction policy version increments.
