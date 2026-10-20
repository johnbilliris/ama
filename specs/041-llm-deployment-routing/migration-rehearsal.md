# P2 local migration tabletop (T047–T048)

## Evidence classification

**Synthetic / offline only.** The fixture uses `https://synthetic.invalid`,
invented identities, labelled synthetic approvers and a fixed 2040 evaluation
clock. These are not real target observations, approvals, quota or readiness.
No Azure read/write, inference, infrastructure/configuration change, switch,
rollback or deletion occurs. **SC-006 real operational acceptance: pending /
not executed.** Target P1 release readiness is not established.

The CLI reads supplied JSON, compares it and prints local status. It neither
authenticates those assertions nor performs the action named by `--stage`.
An exit 0 grants no G0/G4/G5/G6 authority. Old resources and corrected pairs are
asserted retained in the synthetic fixtures, not provisioned or queried.

## Reproduction

From `C:\code\ama`, using the already installed locked environment:

```powershell
uv run --no-sync pytest tests/unit/test_llm_deployment_migration_preflight.py -q --tb=line
uv run --no-sync pytest tests/unit/test_llm_deployment_migration_preflight.py tests/unit/test_llm_deployment_preflight.py tests/contract/test_llm_deployment_configuration.py -q --tb=line
```

`migration_bundle()` in the migration test module creates explicit old/new
snapshots, corrected API/agents pairs, approved-policy metadata, actual-pool
shaped quota evidence and independent stage approvals, all labelled synthetic.
`run_migration()` writes only pytest temporary JSON inputs, invokes the actual
CLI in a subprocess and verifies those inputs and the directory are unchanged.
Additional in-process checks replace socket creation with a failing guard for
every stage. The checker cannot silently call Azure or inference.

To reproduce the named tabletop branches directly (temporary inputs only):

```powershell
@'
import copy
import json
import tempfile
from pathlib import Path
from tests.unit.test_llm_deployment_migration_preflight import migration_bundle, run_migration

bundle, pristine = migration_bundle()
cases = []
for stage in ("provision", "canary", "switch", "forward", "rollback", "retain", "retire"):
    cases.append(("supplied-" + stage, copy.deepcopy(pristine), stage, 0))
no_readiness = copy.deepcopy(pristine)
del no_readiness["records"]["readiness"]
cases.extend([
    ("uncreated-replacements-G5a", no_readiness, "provision", 0),
    ("missing-actual-readiness-G5b", no_readiness, "switch", 1),
])
failed = copy.deepcopy(pristine)
failed["records"]["verification"]["outcome"] = "failed"
failed["records"]["verification"]["checks"]["streaming"] = False
cases.extend([("failed-forward", failed, "forward", 1), ("approved-rollback", failed, "rollback", 0)])
for stage in ("provision", "switch", "rollback", "retire"):
    absent = copy.deepcopy(pristine)
    del absent["approvals"][stage]
    cases.append(("no-approval-" + stage, absent, stage, 1))
for name, evidence, stage, expected in cases:
    with tempfile.TemporaryDirectory() as directory:
        result = run_migration(Path(directory), bundle, evidence, stage)
    assert result.returncode == expected, (name, result.stderr)
    detail = json.loads(result.stdout) if result.stdout else result.stderr.strip()
    print(name, "exit=" + str(result.returncode), detail)
'@ | uv run --no-sync python -
```

## Expected branch outcomes (not operational state changes)

| Synthetic branch | CLI result | Procedure interpretation |
| --- | --- | --- |
| Complete proposed provisioning evidence + independent G5a | 0, `provision` comparison passes | Proposal prerequisites can be evaluated before resources exist |
| Same proposal without actual replacement readiness | 0 at `provision`, 1 at `switch` | Missing readiness blocks G5b, not valid G5a |
| Complete readiness + separate canary/switch/forward approvals | 0 at each explicitly evaluated stage | Supplied comparisons pass, no inference/traffic actually occurs |
| Failed new-pair streaming/forward evidence | 1 at `forward` | Do not promote; use only separately approved rollback scope |
| Failed-forward record + valid independent rollback approval + verified retained old corrected pair | 0 at `rollback` | Old pair remains compatible; no successful forward assertion needed to compare rollback |
| Missing provisioning/switch/rollback approval | 1 at each affected stage | No approval is inferred from P1 or another P2 stage |
| Successful supplied verification, observation criteria and rollback rehearsal | 0 at `retain` | Retention explicitly recorded, no automatic retirement |
| Complete retention/dependency evidence plus separate G6 | 0 at `retire` | Retirement comparison only, no deletion performed |
| Missing G6, failed observation/rehearsal or remaining old dependency | 1 at `retire` | Keep old resources/pair; no inferred retirement permission |
| Wrong/absent quota pool, missing old/new allocation or insufficient combined headroom | 1 | Separate deployments do not create quota |
| Shared model in one quota pool | 0 with aggregate headroom, 1 when exhausted | Sum all old/new allocations with other usage and margin |
| Changed model/protection/embedding/control or incompatible raw routing | 1 | No model substitution or protection relaxation |
| Missing/stale/unbound/invalidated evidence or wrong target/policy/stage | 1 | Recollect under G0 and reapprove affected stage, no default substitution |

Every successful migration JSON response retains `target_readiness:
"not established"` and adds `operational_authority: "not granted"`.
Failure emits stderr and no success JSON.

## FR-016 cross-check and remaining gates

The eight numbered rows in [naming-migration.md](naming-migration.md) map the
contract's entire P2 procedure: independent proposal; coexistence quota; proposed
policy/access + G5a; approved provisioning and actual G0 readiness; paired
candidates and old corrected rollback pair; stage-specific G5b switch/verification/
rollback; observation/retention; independent G6 and zero old dependencies.
The state labels distinguish `proposed`, `approved`, `replacements_ready`,
`switched`, `verified`, `retained`, `rolled_back`, `retirement_approved`, `retired`.
The tabletop records comparisons, not transitions through real target states.

Actual target baseline (G1), current inherited governance (G2), pinned AVM
compatibility (G3), G0-scoped collection/validation and G4 release decisions
remain external. T024–T027/T030 remain blocked; no IaC authoring/build or target
collection was done. G5a proposal approval/provisioning, actual post-provision
parity/readiness, individual G5b canary/switch/forward/rollback approvals and
execution, real observation/retention and independent G6 retirement remain
pending. T049–T052 are outside this checkpoint.

Exact executed local commands/results and preservation checks are appended to
[verification.md](verification.md). Neither this tabletop nor passing tests
satisfy SC-006's real authorised readiness/switch/forward/rollback requirement.
