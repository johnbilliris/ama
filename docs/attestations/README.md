# AU-Residency Attestation per Release (FR-018 · SC-011 · CHK128 · CHK181)

For every help release (snapshot publish or backend deploy), run:

```pwsh
python tools/help/au_residency_attestation.py --release <release-tag> \
    > docs/attestations/help-<release>.json
```

The script:
1. Enumerates every Azure resource referenced by the help feature
   (Cosmos, AI Search, Storage, App Insights, Foundry agent, Container
   Apps, Key Vault).
2. Asserts `location in {'australiaeast', 'australiasoutheast'}`.
3. Emits a JSON attestation with `release`, `timestamp`, `resources[]`,
   `operator`, `pass: true|false`.
4. Emits `audit.help_au_residency_attestation_passed|failed`.

The attestation JSON MUST be committed under `docs/attestations/` and
referenced from the release notes.
