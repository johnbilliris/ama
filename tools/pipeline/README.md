# pipeline-tools

Spec 029 (Progressive Delivery Pipeline) — Python utilities consumed by the
`.github/workflows/` reusable composite actions and reusable workflows.

| CLI | Module | FR coverage |
|---|---|---|
| `posture-verifier` | `pipeline_tools.posture_verifier` | FR-031 (post-deploy posture sweep) |
| `canary-controller` | `pipeline_tools.canary_controller` | FR-007 / FR-008 (canary advance/rollback) |
| `evidence-packer` | `pipeline_tools.evidence_pack_builder` | FR-013 / FR-014 (evidence pack assembly) |
| `audit-emitter` | `pipeline_tools.audit_emitter` | FR-015 (audit-store writes) |
| `freeze-controller` | `pipeline_tools.freeze_controller` | FR-011 (Incident-Mode Change Freeze) |
| `cross-env-check` | `pipeline_tools.cross_env_check` | FR-029 (cross-env reference detection — runtime layer) |
| `known-good-index` | `pipeline_tools.known_good_index` | FR-008 (known-good index for rollback target) |
| `reviewer-sync` | `pipeline_tools.reviewer_sync` | FR-011 / ADR-029-01 (reviewer-list reconciliation) |

Install: `pip install -e .[dev]`.

See `CONTRIBUTING.md` for local development workflow.
