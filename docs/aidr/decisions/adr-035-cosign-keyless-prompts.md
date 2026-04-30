# ADR-035: Cosign Keyless Signing for Prompt Artifacts

## Status

Proposed (target: Accepted upon merge of spec-032 Stream-6 task T606/T607).

## Context

Spec 032 FR-AI09 requires that prompt-template artifacts be **signed and verified before deploy** as a supply-chain hardening measure. The rubric notes this gap explicitly under "Model Selection & Deployment" item 10.4.

Two patterns were considered:

1. **GPG with rotated keys** — operationally heavy: signing key generation, rotation, secure storage, revocation lists, dev-laptop tooling. Adds a new long-lived secret to the org.
2. **Sigstore `cosign` keyless** — uses ephemeral certificates issued by Fulcio against an OIDC identity (in our case GitHub Actions OIDC). No long-lived signing keys to manage. Verification reads Rekor for transparency. Aligns with ADR-032 (re-introducing OIDC for Azure auth — same identity surface).

## Decision

Adopt **Sigstore `cosign` keyless signing using GitHub OIDC identity tokens** for all prompt artifacts shipped under `packages/prompts/`.

### Producer side

A new workflow `.github/workflows/prompts-publish.yml` runs on changes to `packages/prompts/` on `main` or `production` and:

```yaml
permissions:
  id-token: write       # OIDC for keyless cosign
  contents: read

steps:
  - uses: sigstore/cosign-installer@<sha>
  - run: |
      for f in $(find packages/prompts -name '*.yaml'); do
        cosign sign-blob --yes \
          --output-signature "${f}.sig" \
          --output-certificate "${f}.crt" \
          "${f}"
      done
```

### Verifier side

`cd.yml` runs the verifier before any deployment that ships prompts:

```pwsh
cosign verify-blob `
  --certificate-identity-regexp "^https://github.com/<org>/ama/.github/workflows/prompts-publish.yml@refs/heads/(main|production)$" `
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" `
  "${prompt_path}.sig" "${prompt_path}"
```

If verification fails for **any** artifact, the deploy is blocked and a `prompt.cosign_verify_failed` event pages the Security Engineer.

### Manifest

The cosign-side manifest is documented in `specs/032-rubric-improvements/contracts/cosign-signing.yaml` (already authored in Step 4).

## Consequences

### Positive

- Zero long-lived signing keys.
- Reuses GitHub OIDC identity surface (same as ADR-032).
- Public Rekor transparency log provides external auditability.
- `cosign` itself is pinned to a SHA in the workflows (FR-C03).

### Negative / accepted

- Sigstore is an external service; if Sigstore is unavailable, prompt deploys are blocked. Mitigation: a documented `--cosign-bypass=incident-{id}` requiring Security Engineer + Principal Engineer co-approval covers the rare bypass case (audit-logged).
- Verification uses Fulcio identity matching, which means the prompt-publish workflow file path is now part of the trust contract; renaming it requires a registry update.

### Not pursued

- **GPG long-lived keys** — rejected (key management toil).
- **Hardware security modules (HSM) signing** — overkill for prompt text artifacts; reserved for code-signing surfaces.

## Compliance

- **NN-1 (Human-in-the-loop)**: improved — operators see a verifiable audit trail for every prompt change.
- **NN-3 (Privacy)**: unchanged.
- **NN-5 (Graceful degradation)**: documented bypass preserves life-safety operations during Sigstore outages.

## References

- Sigstore cosign: <https://docs.sigstore.dev/signing/quickstart/>
- Spec 032 FR-AI09 + `contracts/cosign-signing.yaml`.
- ADR-032 — OIDC supersession (same identity model).

---
*Author: Security Engineer + AI/ML Engineer personas via spec-032 Stream-0. Date: 2026-04-30.*
