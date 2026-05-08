# Compliance & Runtime-Integrity Checklist: Microsoft Foundry-Based RAG Grounding

**Purpose**: Validate that the spec satisfies the Constitution carve-outs, residency pins, opt-out audit trails, blue-green index lifecycle, and offline cache integrity to a level a security/compliance reviewer can verify before planning.
**Created**: 2026-05-08
**Feature**: [spec.md](../spec.md)
**Companion checklists**:
- [requirements.md](./requirements.md) — Spec quality fundamentals
- [migration.md](./migration.md) — Migration safety, test seam, citation contract

> **Scope of this file**: The five coverage areas where *constitutional, residency, and operational integrity* depend on the spec being unambiguous: **Constitution Alignment** (Coverage Area 1), **No-RAG Opt-Out Audit Trail** (Coverage Area 4), **Index Lifecycle** (Coverage Area 6), **Data Residency** (Coverage Area 7), **Offline Cache Integrity** (Coverage Area 8).

> **Item numbering**: Continues from `migration.md` (CHK114+).

## Constitution Alignment *(Coverage Area 1)*

> **Authority**: User input bullet 1 — "every Foundry data-flow has a §NN-2 carve-out registry entry pointer; every life-safety decision (Principle I) carries a citation hook; every degraded-mode behaviour is auditable (Principle IV)."

- [x] CHK114 Constitution Non-Negotiable #2 (Data Sovereignty + Microsoft Foundry carve-out, Amendment 1.2.0) is cited and used as the governing policy for FR-RAG-CV-01..04. [Traceability, Spec §FR-RAG-CV-01..04 vs `.specify/memory/constitution.md` §NN-2]
- [x] CHK115 Constitution Principle I (Primacy of Life) is cited as the basis for FR-RAG-LS-01..03 and the no-silencing invariant of FR-RAG-FM-06. [Traceability, Spec §FR-RAG-LS-* / §FR-RAG-FM-06]
- [x] CHK116 Constitution Principle IV (Transparency & Auditability) is cited as the basis for FR-RAG-AG-02 and FR-RAG-SIM-04. [Traceability, Spec §FR-RAG-AG-02 / §FR-RAG-SIM-04]
- [x] CHK117 Constitution Principle V (Warning and Public Information) is cited for FR-RAG-AG-06 and FR-RAG-SIM-05. [Traceability, Spec §FR-RAG-AG-06 / §FR-RAG-SIM-05]
- [x] CHK118 Constitution VI-C (Vulnerable Populations) is cited for User Story 8 / FR-RAG-AG-06. [Traceability, Spec §US8 / §FR-RAG-AG-06]
- [ ] CHK119 Does **every** Foundry data-flow FR (FR-RAG-FM-01..07 plus any non-AU traffic permitted under FR-RAG-CV-03) include an explicit pointer to the §NN-2 **carve-out registry entry** (`infra/parameters/foundry-carveout.yaml`) that authorises its model-hosting region? [Constitution, Coverage Area 1, Spec §FR-RAG-FM-* / §FR-RAG-CV-01]
- [ ] CHK120 Does **every life-safety FR** (FR-RAG-LS-01..03, plus AG-01, AG-03, AG-05, AG-06, SIM-02..04) carry a **citation hook** requirement traceable to Constitution Principle I — i.e., the operator can always see "what doctrine grounded this life-safety decision"? [Constitution, Coverage Area 1, Spec §FR-RAG-LS-* / §FR-RAG-AG-* / §FR-RAG-SIM-*]
- [ ] CHK121 Does **every degraded-mode behaviour** (offline cache answer, fallback chain activation, alias-flip rollback, gateway deny, queued-then-reconciled audit) emit an **auditable event** per Constitution Principle IV — i.e., no silent degradation? [Constitution, Coverage Area 1, Spec §FR-RAG-LS-02 / §FR-RAG-FM-06 / §FR-RAG-IDX-04 / §FR-RAG-CV-03]
- [ ] CHK122 Is the **carve-out registry's required schema** (`model_name`, `region`, `business_justification`, `approver_identities[]`, `review_date`) mirrored across FR-RAG-CV-01 and Constitution §NN-2 without divergence? [Consistency, Spec §FR-RAG-CV-01 vs Constitution §NN-2]
- [ ] CHK123 Does FR-RAG-CV-04's **regional pin list** (Cosmos, Storage, Service Bus, Event Grid, Application Insights, Log Analytics, Key Vault, ACR, audit, evidence) match Constitution §NN-2's enumerated data-persistence services exactly (no service silently omitted, no service silently added)? [Consistency, Spec §FR-RAG-CV-04 vs Constitution §NN-2]
- [ ] CHK124 Does the spec note that the §NN-2 carve-out **MUST NOT be widened by interpretation** — i.e., is there an explicit guard against future contributors expanding the inference exemption to data-persisting services? [Constitution, Spec §FR-RAG-CV-* vs Constitution §NN-2]
- [ ] CHK125 Are the **Quality Gates** at Constitution §Quality Gates (PR linting, unit + integration tests, What-If/Plan review, public-output review) referenced as the gating mechanism for FR-RAG-LS-03's draft-vs-final audit chain? [Constitution, Spec §FR-RAG-LS-03 vs Constitution §Quality Gates]

## Data Residency *(Coverage Area 7)*

> **Authority**: User input bullet 7 — "AI Search index pinned to `australiaeast`, private endpoint enforced, no cross-region replication; Foundry inference may transit non-AU under §NN-2 only with carve-out registry entry."

- [ ] CHK126 Is the AI Search index region pinned to `australiaeast` **explicitly** (not "Australia East / Australia Southeast" — the spec narrows the FR-RAG-CV-04 region pair to a single region for the index)? [Clarity, Spec §FR-RAG-IDX-06]
- [ ] CHK127 Is the **private-endpoint-only** requirement on AI Search enforced at deploy time (CD failure if public network access is on) and not just stated as a target? [Acceptance Criteria, Spec §FR-RAG-IDX-06]
- [ ] CHK128 Is "**no cross-region replication**" expressed as a deployable contract (e.g., a Bicep parameter, a PSRule, or a CD assertion) rather than prose-only — so a reviewer can prove the property from inspection? [Measurability, Spec §FR-RAG-IDX-06]
- [ ] CHK129 Does FR-RAG-CV-03 enforce that **only a current carve-out registry entry** (matching `model_name` and `region`, with non-expired `review_date`) permits Foundry-inference traversal of a non-AU region? [Coverage, Spec §FR-RAG-CV-03 vs §FR-RAG-CV-01..02]
- [ ] CHK130 Are PII / PSPF redaction or denial behaviours specified per **egress direction** (request prompt going to non-AU AND response payload coming back from non-AU)? [Clarity, Spec §FR-RAG-CV-03]
- [ ] CHK131 Is the gateway `deny` event's required audit shape specified end-to-end (`region`, `carveout_entry_id`, `policy_decision`, `gateway.deny.reason`) and consistent across FR-RAG-CV-03 and the corresponding Edge Case bullet? [Acceptance Criteria, Spec §FR-RAG-CV-03 vs §Edge Cases]
- [ ] CHK132 Are **regulated-data classes** (incidents, alerts, recommendations, operator actions, audit, evidence, PII, PSPF-marked content) explicitly enumerated as MUST-stay-in-AU per Constitution §NN-2's bullet on persistence? [Coverage, Spec §FR-RAG-CV-04 vs Constitution §NN-2]
- [ ] CHK133 Is there a stated requirement that **CD fails before resource creation** (not after) when a data-plane resource resolves to a non-AU region (per User Story 2 acceptance scenario 4)? [Acceptance Criteria, Spec §US2.4 / §FR-RAG-CV-04]

## No-RAG Opt-Out Audit Trail *(Coverage Area 4)*

> **Authority**: User input bullet 4 — "every FR-RAG-NS-* clause has an ADR pointer + a code comment lint anchor (`# RAG-OPTOUT [FR-RAG-NS-NN]`) + an audit-log shape."

- [ ] CHK134 Does **each** FR-RAG-NS-01..09 clause name an **ADR file path** under `docs/decisions/036-foundry-rag-grounding/<NN>-rag-optout-<topic>.md`? [Traceability, Spec §FR-RAG-NS-01..09]
- [ ] CHK135 Does **each** FR-RAG-NS-01..09 clause specify the **exact code-comment lint anchor** format `# RAG-OPTOUT [FR-RAG-NS-NN]: <reason>` so the FR-RAG-NS-08 lint can match it? [Clarity, Spec §FR-RAG-NS-01..09]
- [ ] CHK136 Does **each** FR-RAG-NS-01..09 clause specify the **audit-log shape** (`rag_used=false`, `rag_optout_reason="<value>"`) consistently — including the named string for `rag_optout_reason`? [Clarity, Spec §FR-RAG-NS-01..09]
- [ ] CHK137 Is the **FR-RAG-NS-08 CI-lint matcher pattern** explicit enough (pattern-based on `[FR-RAG-NS-NN]`) to validate that the Pass-2-added FR-RAG-NS-09 is covered without a code change? [Consistency, Spec §FR-RAG-NS-08 / §FR-RAG-NS-09]
- [ ] CHK138 Are the ADR files named in FR-RAG-NS-01..09 **enumerated with stable filenames** (`01-…` through `09-…`) so a future renumbering would break the spec — making renumbering visibly unsafe? [Traceability, Spec §FR-RAG-NS-01..09]
- [ ] CHK139 Does the **Observer-Auditor opt-out (FR-RAG-NS-09)** clearly enumerate *which* paths are opted out (read-only inspection, audit replay, integrity verification, dashboard recomputation against historical decisions)? [Clarity, Spec §FR-RAG-NS-09]
- [ ] CHK140 Are **persona-memo citations** included for each FR-RAG-NS-01..09 rationale so reviewers can trace the carve-out back to the originating persona memo (e.g., NS-09 → `personas-input/operational.md` Observer-Auditor "non-decision" carve-out)? [Traceability, Spec §FR-RAG-NS-* vs persona memos]
- [ ] CHK141 Does FR-RAG-NS-09 explicitly state that **re-grounding on replay would (a) inflate cost, (b) pollute the audit chain, (c) introduce a hallucination surface absent from the original decision** — closing the rationale loop? [Completeness, Spec §FR-RAG-NS-09]
- [ ] CHK142 Is the **CI-lint anchor stability** explicitly preserved by Pass 2 — i.e., the spec notes that the lint clause's ID stayed at FR-RAG-NS-08 even after FR-RAG-NS-09 was added, so existing `# RAG-OPTOUT [FR-RAG-NS-NN]` code comments remain valid? [Consistency, Spec §FR-RAG-NS-08 vs §FR-RAG-NS-09 vs §Clarifications Pass 2]
- [ ] CHK143 Are the **opt-out audit fields** (`rag_used`, `rag_optout_reason`) part of the AuditRecord Key Entity definition so they survive any future audit-schema review? [Consistency, Spec §Key Entities `AuditRecord (LLM-call)` vs §FR-RAG-NS-*]
- [ ] CHK144 Is there a stated requirement that **a future contributor introducing a new agent without a RAG-OPTOUT comment OR an ADR fails CI** (per User Story 5 acceptance scenario 5) — locking the trail going forward? [Acceptance Criteria, Spec §US5.5 / §FR-RAG-NS-08]

## Index Lifecycle *(Coverage Area 6)*

> **Authority**: User input bullet 6 — "FR-RAG-IDX-04 blue-green rebuild ≤ 24h cold + < 60s alias flip + 7-day rollback retention is validated."

- [ ] CHK145 Does FR-RAG-IDX-04 specify the **blue-green rebuild as the only mechanism** for embedding-model changes (no in-place mutation, no joint partition keys, no co-existence within a single index)? [Clarity, Spec §FR-RAG-IDX-04]
- [ ] CHK146 Is the **cold-rebuild SLA (≤ 24h)** bound to a measurement methodology (which step counts toward the 24h, when the clock starts/stops, what happens if the corpus is mid-update during rebuild)? [Measurability, Spec §FR-RAG-IDX-04]
- [ ] CHK147 Is the **alias flip SLA (< 60s)** bound to an atomicity guarantee (no partial reads, no double-served traffic, no "split brain" where some agents query the new index and others query the old)? [Acceptance Criteria, Spec §FR-RAG-IDX-04]
- [ ] CHK148 Is the **7-day rollback retention** enforced by an automated sweep, or is the spec silent on cleanup (which would risk indefinite cost accrual or premature deletion)? [Coverage, Gap, Spec §FR-RAG-IDX-04]
- [ ] CHK149 Is the **parity gate** that authorises the alias flip defined (which signals MUST pass: ingest count, sampling parity vs old index, retrieval-quality delta, hallucinated-citation rate)? [Clarity, Spec §FR-RAG-IDX-04]
- [ ] CHK150 Does the `(corpus_build_sha, embedding_model_id)` provenance pair on every chunk (FR-RAG-IDX-03) **survive the alias flip** so historical audit reconstruction (SC-011) works across the boundary? [Consistency, Spec §FR-RAG-IDX-03 / §FR-RAG-IDX-04 / §SC-011]
- [ ] CHK151 Are requirements defined for **AI Search service capacity scaling during a blue-green window** (two indexes coexist transiently — does the SKU need to step up?) and integrated with the FR-RAG-IDX-08 70%-capacity autoscale alert? [Gap, Spec §FR-RAG-IDX-04 vs §FR-RAG-IDX-08]
- [ ] CHK152 Is the **rollback procedure** specified — within the 7-day retention window, how is a flip-back triggered (manual operator action? automated regression detection?), and which audit event records the rollback? [Recovery, Gap, Spec §FR-RAG-IDX-04]
- [ ] CHK153 Is the **idempotent-ingest** requirement (FR-RAG-IDX-04 first sentence) consistent with the **blue-green** requirement (same FR's later sentences) — i.e., idempotency applies within an index version, while blue-green applies across embedding-model changes? [Consistency, Spec §FR-RAG-IDX-04 internal]
- [ ] CHK154 Is the per-index **single-embedding-model invariant** ("each index hosts exactly one embedding-model id, so old and new vectors never coexist within a single index") explicit and enforceable (e.g., a deploy-time check that rejects mixed embedding-model ids)? [Acceptance Criteria, Spec §FR-RAG-IDX-04]

## Offline Cache Integrity *(Coverage Area 8)*

> **Authority**: User input bullet 8 — "≤ 500 MB cap + dual signature (cosign keyless + age) + 14-day TTL + audit-logged refresh."

- [ ] CHK155 Is the offline cache **size cap (≤ 500 MB per device)** measurable both at build time (cache bundle size) and at device sync time (on-disk footprint), with a stated behaviour when the cap would be exceeded? [Measurability, Spec §FR-RAG-LS-02]
- [ ] CHK156 Are **both signature mechanisms** specified concretely: (a) cosign keyless via Sigstore + GitHub OIDC for the master `corpus_build.sha256` manifest (per spec-032 FR-AI09); (b) age-encrypted detached signature via the tenant's offline public-key set on the cache bundle? [Clarity, Spec §FR-RAG-LS-02 vs `specs/032-rubric-improvements/spec.md` FR-AI09]
- [ ] CHK157 Is the **14-day TTL behaviour** specified for **both** expiry (refusing answers OR surfacing a "cache stale" badge per Edge Case bullet) AND the **audit-logged refresh** on next online sync? [Coverage, Spec §FR-RAG-LS-02 / §Edge Cases]
- [ ] CHK158 Is the **cache content scope** specified (hazard thresholds, safety-escalation criteria, sector boundaries, AIIMS span-of-control, evacuation centre setup checklists) and enforceable against silent expansion (e.g., the manifest is the closed-set authority)? [Clarity, Spec §FR-RAG-LS-02]
- [ ] CHK159 Is the **offline-decision audit reconciliation** flow specified end-to-end (queued entries on the device, original timestamps preserved, `sync_lag_seconds` value captured, central audit store target named)? [Acceptance Criteria, Spec §US6 / §FR-RAG-LS-02]
- [ ] CHK160 Are requirements defined for **cache provisioning** — who creates the manifest, how the tenant key is rotated, where the age public keys are stored, who approves a manifest version? [Gap, Spec §FR-RAG-LS-02]
- [ ] CHK161 Is the "**stale cache** badge" requirement (per Edge Case bullet) wired to a measurable threshold separate from the 14-day hard TTL — i.e., is there a soft warning before the hard refusal, or are they intentionally the same threshold? [Consistency, Spec §Edge Cases vs §FR-RAG-LS-02]
- [ ] CHK162 Is the requirement that **agents refuse to extend beyond cached topics** while offline testable — i.e., the spec defines the rejection behaviour AND the audit shape for a query the offline cache cannot answer? [Acceptance Criteria, Spec §FR-RAG-LS-02 / §US6]
- [ ] CHK163 Is the **dual-signature verification chain** specified to fail-closed if either signature is invalid (e.g., cosign succeeds but age fails, or vice versa) — and is the audit-event shape for each failure mode named? [Recovery, Gap, Spec §FR-RAG-LS-02]
- [ ] CHK164 Is the **`OfflineCacheManifest` Key Entity** field set (`version, generated_at, corpus_build_sha, signature, entries[]`) consistent with the dual-signature requirement (does `signature` mean both signatures, or just one)? [Consistency, Spec §Key Entities `OfflineCacheManifest` vs §FR-RAG-LS-02]
- [ ] CHK165 Is there a stated requirement for **what happens when the master manifest's cosign signature has expired** but the on-device age signature is still valid (or vice versa)? [Edge Case, Gap, Spec §FR-RAG-LS-02]

## Notes

- **Item count (this file)**: 52 items across 5 sections (CHK114-CHK165).
- **Cross-references**: Items in this file frequently cite the Constitution (`.specify/memory/constitution.md` Principle I, IV, V, VI-C, NN-2 Amendment 1.2.0), spec-032 FR-AI03a / FR-AI06 / FR-AI09, and the corpus README licence model (`docs/corpus/README.md`).
- **Why these five areas live together**: All five are *constitutional or runtime-integrity invariants* whose violations would breach the Constitution or the §NN-2 carve-out. Reviewing them in one file lets a single security/compliance reviewer (Compliance Auditor + Security Engineer personas) clear them in one pass before `/speckit.plan`.
- **Total checklist surface**: 165 items across the three files (`requirements.md` 1-82, `migration.md` 83-113, `compliance.md` 114-165).
