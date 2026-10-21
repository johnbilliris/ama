# Extension List Validation Handoff

## Current Disposition

All external platform, sovereign CI/release, qualifying evidence, and human-study outcomes remain **pending-external**. Local fake transport tests validate contract behavior only. They do not provision infrastructure, contact Azure, perform DNS or Blob operations, request or verify a live JWS, collect participant data, or establish an external success claim. No repository status JSON represents external completion.

Normal non-synthetic CLI use remains sovereign-only. Local synthetic sessions cannot be promoted into sovereign or release evidence.

## Local Synthetic Lifecycle

Local development requires no Azure resource.

1. Run the protected-state self-check green once.
2. Run the dispatcher/root-regression self-check green once.
3. Start a `local-synthetic` daemon session and retain its emitted session UUID only as routing metadata.
4. Route every data-bearing child through the peer-authenticated dispatcher with `SPEC001_TEST_MODE=synthetic`, a marker-bound owner-only temporary fixture or no project root, frozen uv execution, and pytest cache-provider denial where applicable.
5. Use the shared action intent/result transaction around every source, test, schema, documentation, or workflow mutation.
6. Finalize the session through the dispatcher. Finalization appends its linked intent/result pair and deletes the owner-only ephemeral journal and temporary payloads. This is logical deletion, not a physical secure-erasure claim.

A lost local daemon ends that non-evidentiary segment. Development may start a new explicitly discontinuous local segment from the current worktree, but segments are never resumed, combined, or promoted.

## Post-Implementation Sovereign Lifecycle

Each real CI/release, qualifying evidence, collect, or finalize operation owns a complete lifecycle. Do not repeat an implementation-time expected-red step.

1. Run the protected-state self-check green once.
2. Run the dispatcher/root-regression self-check green once.
3. Perform signed sovereign preflight against the reviewed owner-only trust bundle.
4. Start a verified sovereign daemon session on an eligible standalone AU VM.
5. Route each guarded child through peer-authenticated IPC with offline authorized-AU-mirror packaging.
6. Finalize the sovereign session and retain its immutable AU audit chain.

Preflight and runtime verification must fail closed on incomplete ARM, IMDS, private endpoint, private DNS, encrypted volume, immutable ledger, offline cache, or role enumeration. Catalog reads use the shared role-parameterized Storage Blob Data Reader evaluator. External collect and finalize use the same shared evaluator parameterized for exact container-scoped Storage Blob Data Contributor. Broader, eligible, inherited, ambiguous, unresolved, or additional Blob data-plane access blocks the operation.

The control plane and signing Key Vault must match the reviewed package pins, be in an allowed Australian region, disable public network access, use approved private endpoints and private-only DNS, and expose an enabled, unexpired exact versioned signing key. The pre-write request is one bounded, no-redirect, no-retry private HTTPS POST. Every fragment and final write requires a fresh verified ES256 attestation, JTI, and 256-bit nonce. Its immutable replay marker is conditionally created and locked for at least one day before the associated create-if-absent Blob write. Existing markers or target blobs reject replay or overwrite.

Collect runs once on an eligible Windows x64 VM and once on an eligible Ubuntu x64 VM for one shared validation UUID. Finalize uses its own complete verified daemon session, validates exact fragment agreement and cardinality, and records only a pseudonymous reviewer identifier, closed reviewer role, approved/rejected decision, and matching closed reason code.

## Privacy And Residency

External evidence and review remain in authorized Australian stores with encryption in transit and at rest, managed identity, least privilege, immutable access audit, retention, deletion, withdrawal, and incident controls aligned to the Privacy Act. Recruitment or re-identification records are separated from evidence. Direct identifiers, names, contact details, medical details, and free-text participant fields are prohibited. Accommodation data uses closed generic category codes.

A valid external record may document a rejected review or failed study threshold. Lifecycle completion never implies outcome success.

## Human Source-Control Handoff After T134

Implementation performs no Git stage, commit, push, stash, reset, restore, revert, or pull-request operation. After T134 and only after reviewing the intended change set, a human maintainer must:

1. Review the intended source, documentation, schemas, tests, workflow, and `tools/specify-cli/uv.lock`.
2. Run the required affected local validation again if any file changes during review or hooks.
3. Stage and commit only the reviewed intended files.
4. Push the reviewed branch and open a pull request.
5. Run all required sovereign and pull-request gates; keep external platform and human-study claims pending until their separately authorized AU workflows complete.

Unscoped pre-commit Ruff, formatter, and end-of-file hooks may change bytes outside the intended scope. Stop and review any such mutation, then rerun every affected local validation before commit. Secret scanners, gitleaks, and private-key hooks will scan `tools/specify-cli/src/specify_cli/trusted_attestation_keys.json`; the reviewed file must contain public JWK material and synthetic contract pins only, never credentials, tokens, SAS values, or a private `d` member. Any scanner finding requires human review and resolution before staging or commit.
