# Pinned AVM deployment child

Unmodified child of published `avm/res/cognitive-services/account:0.18.0`.
This is not a separately published child registry module. Do not edit
`main.bicep`; update the verified pin and evidence together.
Narrow `.gitattributes` LF rules preserve the pinned source/license bytes on
Windows checkouts. Do not format or regenerate either upstream file.

- Commit: `f1070229a704c42897f07bdc19913cba26895bae`
- Source: <https://github.com/Azure/bicep-registry-modules/blob/f1070229a704c42897f07bdc19913cba26895bae/avm/res/cognitive-services/account/deployment/main.bicep>
- Parent OCI manifest: `46982b96fd9dd36089aaa6b6b440562d9a8ba0fc60b3002222201f630d8695b9`
- Published source archive: `dffcff2af477628e3ede3df9d3c76aa6ac7b143c6dc479a97caf6dae6e02c9ed`
- `main.bicep`: 1755 bytes, SHA256 `a0d007d0f61a143949c0d0acb771f59c9bc96f72db4d952fc03dc8a4d1834aa1`
- `LICENSE`: complete upstream MIT notice, SHA256 `c2cfccb812fe482101a8f04597dfc5a9991a6b2748266c47ac91b6a5aae15383`

See `specs/041-llm-deployment-routing/avm-compatibility.md` and its
`evidence/g3-avm/selected-proof.json` for registry/archive/commit checks.
The account is existing-only. The sole writable resource uses API `2026-05-01`;
upstream's BCP081 suppression and all upstream bytes are retained.
The wrapper explicitly supplies model, SKU, RAI and upgrade settings and
serializes all account child operations.
