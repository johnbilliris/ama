# HANDOFF — Spec 036 Phase F human-in-loop tasks

This document identifies the 4 Phase F tasks that **cannot be autonomously
completed** by the implementation agent and the human authorities responsible
for closing them out before production go-live.

| Task    | Description                                                              | Authority owners                                                                                                     | Status |
|---------|--------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------|--------|
| T202    | **Cultural authority registry seeding** (Cosmos `culturalAuthorityRegistry` rows) | NEMA + AFAC + ≥3 Indigenous community representatives + AIATSIS Ethics Committee                                      | `[~]`  |
| T203    | **Indigenous-language corpus body authoring** (translations + protocols)   | NEMA + AFAC + Land Councils (NLC, CLC, ALT, APY) + AIATSIS Ethics Committee + ≥3 Indigenous community representatives | `[~]`  |
| T210    | **Federal compliance attestation** (Privacy Act, ISM-2024, PSPF mappings)  | OAIC + ASD ACSC + AGD PSPF Branch + AMA federal compliance owner                                                      | `[~]`  |
| T247    | **ADR-15 body publication** (federal compliance posture)                   | OAIC + ASD ACSC + AGD PSPF Branch + AMA federal compliance owner                                                      | `[~]`  |

## What the AI agent has done (scaffolding)

For each task above, the implementation agent has created the **scaffolding**
that the human authorities will need:

### T202 — registry seeding scaffold

- Empty Cosmos container provisioned via `infra/bicep/modules/cosmos-cultural-authority.bicep` (T196).
- Empty seeder script hook in `apps/agents/common/cultural_authority_registry.py::seed_registry_from_signoff_file` — **raises `NotImplementedError`** with a pointer back to this HANDOFF.md.
- CD pipeline gate location identified: `infra/parameters/cultural-authority-signoff.json` (file does NOT yet exist; CD must verify presence + signature on every pre-prod release).
- OPA flag lockdown rego at `infra/policy/rego/cultural_authority_flag.rego` (T201) prevents disabling the gate in `prod` regardless of registry contents.

**To complete T202**: NEMA + AFAC + ≥3 Indigenous community reps + AIATSIS
Ethics Committee co-author the `cultural-authority-signoff.json` file
(detached signatures, cosign keyless OR age-encrypted), commit to a
**protected branch only the federal compliance owner can merge into**, and
open a deploy ticket. The seeder script then runs as part of CD post-deploy.

### T203 — Indigenous-language corpus scaffold

- Chunker fields `cultural_classification` + `cultural_authority_required`
  added in T200 (`apps/ingest-runner/src/ama_ingest/chunker.py`).
- AI Search index schema includes both fields
  (`infra/scripts/aisearch-schema.json`, post-T200).
- Cultural classification enum: `public | indigenous-language | sacred-site | land-governance` per spec contract.
- Ingest-time lint (`validate_chunk_metadata`) refuses to publish a chunk with `cultural_classification != "public"` AND `cultural_authority_required = false` (chunk-metadata.schema.json `allOf` invariant 3).

**To complete T203**: Land Councils + AIATSIS Ethics Committee author the
translated corpus bodies (Arrernte, Tiwi, Warlpiri, Pitjantjatjara, Torres
Strait Islander), assign `cultural_classification` + `cultural_authority_required`
per chunk, and submit through the standard corpus-build pipeline. The
blue-green rebuild orchestration (T188) will pick them up on the next flip.

### T210 — federal compliance attestation scaffold

- `docs/compliance/ISM-2024-mapping.md` scaffold (T209) — ≥40 ISM controls
  mapped to AMA implementation refs; **lines 1–N annotated with TODO
  cross-references** for the federal compliance owner to fill in.
- Privacy Act subject-access endpoint `apps/api/app/routes/privacy_subject_access.py`
  (T204) implemented with audit emission.
- PSPF export endpoint `apps/api/app/routes/pspf_export.py` (T207) implemented.

**To complete T210**: OAIC + ASD ACSC + AGD PSPF Branch sign off on the
ISM-2024 mapping document, register the PSPF export endpoint with the
Australian Cyber Security Centre, and amend the federal compliance posture
ADR (T247 / ADR-15).

### T247 — ADR-15 body deferred

- ADR-15 stub exists at `docs/decisions/036-foundry-rag-grounding/15-federal-compliance-posture.md`
  with frontmatter + Status: Proposed.
- **Body deferred** to federal sign-off (per the same authorities that close T210).

**To complete T247**: ADR-15 body authored by the federal compliance owner
once T210 is signed off; commit message must reference the OAIC + ASD ACSC
sign-off ticket IDs.

## CD pipeline integration

The CD pipeline MUST refuse to deploy to `prod` if any of:

- `infra/parameters/cultural-authority-signoff.json` is absent or signatures invalid (T202)
- `cultural_authority_required = true` chunks exist but the registry container is empty (T203)
- `docs/compliance/ISM-2024-mapping.md` contains unfilled `TODO` markers (T210)
- ADR-15 (`docs/decisions/036-foundry-rag-grounding/15-federal-compliance-posture.md`) is in `Status: Proposed` (T247)

These gates are wired in T211 (federal compliance attestation CD step).

## Cross-references

- Constitution Principle VI-C — cultural authority non-negotiable.
- Constitution Principle IV — audit-trail anchor.
- FR-RAG-CA-01..05 — Cultural authority requirements.
- FR-RAG-COMP-01..04 — Federal compliance requirements.
- SC-014 — Cultural authority go-live readiness.
- SC-016 — Federal compliance go-live readiness.
- ADR-12 (cultural authority gate), ADR-15 (federal compliance posture),
  ADR-16 (blue-green retention).
