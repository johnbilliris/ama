# Cultural-Authority Protocols Checklist: Microsoft Foundry-Based RAG Grounding

**Purpose**: Validate that the Constitution VI-C cultural-authority requirements (Indigenous corpus, Sacred Site protocols, ALT/APY consent, cultural-authority registry, NEMA/AFAC/Indigenous community sign-off) are specified to a level that a security/compliance reviewer plus an AIATSIS-aligned cultural advisor can verify before planning.
**Created**: 2026-05-09 (post R3 amend loop Sessions 3 + 4 + 5)
**Feature**: [spec.md](../spec.md)
**Cluster**: A2 (Cultural authority [HUMAN-IN-LOOP]) + Pass 1 Q-P1-01 (registry schema) + Pass 2 Q-P2-02 (gate placement) + Pass 2 Q-P2-08 (Locked-on flag class)
**Companion checklists**:
- [requirements.md](./requirements.md) — Spec quality fundamentals
- [migration.md](./migration.md) — Foundry cutover safety, test instrumentation, citation contract
- [compliance.md](./compliance.md) — Constitution alignment, data residency, opt-out audit, index lifecycle, offline cache
- [federal-compliance-mapping.md](./federal-compliance-mapping.md) — Privacy Act 1988 / ISM 2024 / PSPF / COMDISPLAN
- [audit-and-approval-workflow.md](./audit-and-approval-workflow.md) — AG-02 audit-shape extensions, FC offline boundaries

> **Scope of this file**: The five coverage areas where *Constitution VI-C* depends on the spec being unambiguous about cultural authority: **Planning Scope** (HUMAN-IN-LOOP delineation + named authorities), **Registry Schema & Persistence** (FR-RAG-CA-04 fields, `culturalAuthorityRegistry` Cosmos container), **Retrieval Gate Placement** (post-retrieval, in-process), **Fail-Closed Behaviour & Audit** (registry unreachable; non-protected chunks remain retrievable), **HUMAN-IN-LOOP Sign-off Gate** (FR-RAG-CA-05; NEMA + AFAC + ≥3 Indigenous community representatives), **Feature-Flag Class** (Locked-on in production; OPA-blocked at flag-flip time).

> **Item numbering**: Continues from `compliance.md` (CHK166+).

> **HUMAN-IN-LOOP markers**: Items prefixed `[HUMAN-IN-LOOP — <Authority>]` identify the responsible community / federal / standards authority whose sign-off the AI workflow cannot autonomously close. Authorities recognised in the spec's Assumption A9: **NEMA**, **AFAC**, **AIATSIS**, **ALT**, **APY**, **Land Councils**, **Indigenous community representatives**.

## Planning — Scope & Named Authorities

> **Authority**: Constitution VI-C (Vulnerable Populations) non-negotiable; R3 Cluster A2; Assumption A9.

- [ ] CHK166 Is FR-RAG-CA-01..05's HUMAN-IN-LOOP scope (corpus body authoring vs in-scope inventory / plumbing / consent-gating) explicitly delineated so reviewers know which artefacts the AI workflow produces vs. which require external community work? [Completeness, Spec §FR-RAG-CA-01..03 / §OOS-8]
- [ ] CHK167 Are the named external authorities for cultural-authority sign-off (**NEMA**, **AFAC**, **AIATSIS**, **ALT**, **APY**, **Land Councils**, **Indigenous community representatives**) consistently enumerated across FR-RAG-CA-02, FR-RAG-CA-03, FR-RAG-CA-05, US9.3, SC-014, and Assumption A9? [Consistency, cross-FR]
- [ ] CHK168 [HUMAN-IN-LOOP — AIATSIS / Land Councils] Is the Indigenous-language scope (Arrernte, Tiwi, Warlpiri, Pitjantjatjara, Torres Strait Islander languages) stable in both FR-RAG-CA-01 and US9 prose, with no language silently added or dropped? [Consistency, Spec §FR-RAG-CA-01 vs §US9]
- [ ] CHK169 Is the in-scope vs out-of-scope split — *plumbing in-scope, content authoring out-of-scope* — anchored to **OOS-8** so future contributors do not accidentally re-admit translation work into this feature? [Coverage, Spec §OOS-8 vs §FR-RAG-CA-01..03]

## Registry Schema & Persistence

> **Authority**: FR-RAG-CA-04 + Pass 1 Q-P1-01 + Constitution NN-2 (data residency) + FR-RAG-CV-04.

- [ ] CHK170 Are all cultural-authority registry fields (`operator_id`, `land_council_id`, `granted_at`, `expires_at`, `granted_by_authority`, `scope`, `signature`, `revocation_reason`) listed in FR-RAG-CA-04 with their types and nullability spelled out so a Cosmos schema is implementable from the spec alone? [Completeness, Spec §FR-RAG-CA-04]
- [ ] CHK171 Is the `scope` enum (`site|language|protocol|all`) defined narrowly enough that retrieval-time matching is unambiguous (no overlap, no unspecified values, no implicit `none`)? [Clarity, Spec §FR-RAG-CA-04]
- [ ] CHK172 Is the Cosmos container name `culturalAuthorityRegistry` and its Australia-East residency specified consistently in FR-RAG-CA-04 and FR-RAG-CV-04 (data residency carve-out)? [Consistency, Spec §FR-RAG-CA-04 vs §FR-RAG-CV-04]
- [ ] CHK173 Is the registry's empty-state at production deploy ("provisioned empty; population is HUMAN-IN-LOOP per FR-RAG-CA-05") visible from FR-RAG-CA-04 alone, without requiring a reader to consult Pass 2 Q-P2-01 / Assumption A10? [Clarity, Spec §FR-RAG-CA-04 vs §A10]
- [ ] CHK174 Are registry-write authority requirements specified — i.e., who can grant / revoke consent, and how the `signature` field is validated against the named `granted_by_authority` (cosign? age? Land Council attestation)? [Gap, Spec §FR-RAG-CA-04]

## Retrieval Gate Placement

> **Authority**: Pass 2 Q-P2-02; FR-RAG-AG-01 shared retrieval client; FR-RAG-CV-03 model-gateway in-process filter pattern; spec 014 `_generate_with_fallback` defensive-in-process pattern.

- [ ] CHK175 Is the gate's call-chain location ("post-retrieval, in-process inside the shared retrieval client between AI Search round-trip and Foundry inference call") cited inside FR-RAG-CA-04 — not just inside the Pass 2 Q-P2-02 narrative? [Clarity, Spec §FR-RAG-CA-04]
- [ ] CHK176 Are the rejected alternatives (pre-retrieval AI-Search-side filter; Foundry-orchestration-side filter) explicitly enumerated in FR-RAG-CA-04 so a future contributor cannot relocate the gate without re-opening the design discussion? [Coverage, Spec §FR-RAG-CA-04]
- [ ] CHK177 Is the gate's inheritance across all five grounded agents AND the Simulation Controller (FR-RAG-SIM-01) traceable to a single shared entry point (`apps/agents/common/retrieval_service.py`)? [Traceability, Spec §FR-RAG-CA-04 vs §FR-RAG-AG-01 / §FR-RAG-SIM-01]
- [ ] CHK178 Is the rationale for rejecting AI-Search-side filtering (per-operator filter would break FR-RAG-IDX-08 single-shared-index economics) preserved as a normative constraint, not just narrative? [Consistency, Spec §FR-RAG-CA-04 vs §FR-RAG-IDX-08]

## Fail-Closed Behaviour & Audit

> **Authority**: FR-RAG-CA-04 + Constitution Principle I (no-silencing) + Constitution Principle IV (provable provenance).

- [ ] CHK179 Is "**protected chunk**" defined unambiguously (Sacred Site location data + Indigenous cultural protocols) so a reviewer can tell which chunks the gate applies to without consulting an external glossary? [Clarity, Spec §FR-RAG-CA-04]
- [ ] CHK180 Is the `cultural_authority_registry_unavailable` audit-event shape (fields, when emitted, how it lands in `retrieved_chunks[]`) consistent between FR-RAG-CA-04 and FR-RAG-AG-02? [Consistency, Spec §FR-RAG-CA-04 vs §FR-RAG-AG-02]
- [ ] CHK181 Is the no-silencing invariant explicit — does the spec state that fail-closed for *protected* chunks does NOT cause the agent to refuse the entire prompt (non-protected chunks remain retrievable per Constitution Principle I)? [Coverage, Spec §FR-RAG-CA-04 vs Constitution §I]
- [ ] CHK182 Are revocation flows specified — when an operator's consent is revoked mid-session (registry update propagates), do active sessions re-evaluate, queue for next prompt, or grandfather the in-flight retrieval? [Edge Case, Gap, Spec §FR-RAG-CA-04]
- [ ] CHK183 Is the `cultural_authority_denied` (US9.1) vs `cultural_authority_granted` (US9.2) audit-event vocabulary reconciled with the `cultural_authority_registry_unavailable` fail-closed event so all three event types share a stable shape? [Consistency, Spec §US9.1 / §US9.2 vs §FR-RAG-CA-04]

## HUMAN-IN-LOOP Sign-off Gate

> **Authority**: FR-RAG-CA-05 + US9.3 + SC-014 + Assumption A9; pre-production governance gate distinct from FR-RAG-LS-01.

- [ ] CHK184 [HUMAN-IN-LOOP — NEMA + AFAC + Indigenous representatives] Is FR-RAG-CA-05's pre-production governance gate distinct from the general FR-RAG-LS-01 approval, and is the distinction motivated (separate authority chain; Constitution VI-C-specific)? [Clarity, Spec §FR-RAG-CA-05 vs §FR-RAG-LS-01]
- [ ] CHK185 [HUMAN-IN-LOOP — Indigenous community representatives] Is the cardinality "≥3 Indigenous community representatives" (US9.3, SC-014) consistent with FR-RAG-CA-05's wording AND tied to a CD-time check that fails the deploy if sign-offs are absent? [Consistency / Acceptance Criteria, Spec §US9.3 / §SC-014 / §FR-RAG-CA-05]

## Feature-Flag Class & Reversibility

> **Authority**: Pass 2 Q-P2-08; Assumption A12; spec 029 FR-008 (no-flip path for VI-C).

- [ ] CHK186 Is the `feature.cultural_authority_gate.enabled` flag's "**Locked-on in production**" semantics expressed unambiguously inside FR-RAG-CA-04 (not only inside A12 narrative) — including the OPA-blocked-at-flag-flip-time guarantee? [Clarity, Spec §FR-RAG-CA-04 / §A12]

## Notes

- **Item count (this file)**: 21 items across 6 sections (CHK166–CHK186).
- **Cross-references**: Items in this file frequently cite Constitution VI-C (`.specify/memory/constitution.md`), spec §FR-RAG-CA-01..05, §FR-RAG-AG-02, §FR-RAG-CV-04, §FR-RAG-IDX-08, §A9, §A10, §A12, §US9, §SC-014, §OOS-8, and Pass 1 Q-P1-01 / Pass 2 Q-P2-01 / Pass 2 Q-P2-02 / Pass 2 Q-P2-08.
- **Why this file is separate**: The cultural-authority surface is governed by an **independent authority chain** (NEMA + AFAC + AIATSIS + Land Councils + Indigenous community representatives) distinct from the federal-compliance authority chain (AGD + OAIC + ASD), so a single combined file would force one reviewer to clear two authority chains. Splitting them means an AIATSIS-aligned advisor can clear this file in one pass without context-switching to ISM/PSPF.
- **Plan-phase deliverable**: ADR `12-cultural-authority-gating.md` stub at `docs/decisions/036-foundry-rag-grounding/` (per Assumption A11).
