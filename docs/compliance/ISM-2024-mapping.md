# ISM-2024 Control Mapping — Spec 036 RAG Grounding

> **PENDING HUMAN-IN-LOOP federal sign-off (T210) before publication.**
>
> Authority owners: NEMA, AGD (Attorney-General's Department), AFP (Australian
> Federal Police). AIATSIS consulted for Indigenous-data sections. See
> [`HANDOFF.md`](../../specs/036-foundry-rag-grounding/HANDOFF.md) for the
> sign-off process.

**Status:** PROPOSED — DO NOT publish externally until T210 is closed.

This document maps Spec 036 RAG-grounding implementation primitives to ISM-2024
controls. Each row identifies the ISM control, the AMA implementation reference
(file path, FR ID, or contract), and the sign-off owner. CI fails the build if
any row carries an unfilled `TODO` marker after T210.

## Cross-cutting controls

| ISM control | Title                                                 | AMA implementation reference                                                                            | Owner |
|-------------|-------------------------------------------------------|---------------------------------------------------------------------------------------------------------|-------|
| ISM-0468    | TLS 1.2+ for inbound and outbound traffic             | Foundry SDK + AI Search SDK use TLS 1.3 by default; APIM ingress enforces TLS 1.2+ via WAF policy        | NEMA  |
| ISM-1552    | Cryptographic integrity of audit logs                  | cosign keyless + age-encrypted detached signatures (FR-RAG-LS-02 / T129)                                | NEMA  |
| ISM-1546    | Centralised event logging                              | Cosmos `auditEntries` container + Service Bus event-bus replication                                     | NEMA  |
| ISM-0405    | Multi-factor authentication for privileged operations  | Entra ID + Conditional Access on operator-role group `EvalAuditor`                                       | NEMA  |
| ISM-1546    | Audit retention 7 years                                | Cosmos retention policy (spec 030 §retention) + immutable storage tier on Service Bus archive            | NEMA  |
| ISM-1573    | Air-gapped offline cache integrity                     | T120 offline-cache manifest + dual-sig verification (FR-RAG-LS-02)                                       | NEMA  |
| ISM-0072    | Secure development lifecycle                           | spec-kit + per-PR CI gates + speckit.analyze pre-merge                                                  | AGD   |

## RAG-specific controls

| ISM control | Title                                                | AMA implementation reference                                                                            | Owner |
|-------------|------------------------------------------------------|---------------------------------------------------------------------------------------------------------|-------|
| ISM-1819    | Generative AI input sanitisation                     | classification ceiling guard at retrieval seam (T079); OPA classification filter (T024)                  | AGD   |
| ISM-1820    | Generative AI output filtering                       | citation envelope contract (T087) + Foundry response normaliser (T077)                                  | AGD   |
| ISM-1821    | Generative AI provenance auditing                    | audit-record-llm-call shape (T156) extended to capture chunk_id + tiebreak trace                         | AGD   |
| ISM-1822    | Generative AI training-data carve-out                | foundry-carveout schema + opa rego (T024); environment-aware quorum (T152)                              | AGD   |

## Cultural authority controls (Constitution VI-C)

| ISM control     | Title                                              | AMA implementation reference                                                                            | Owner   |
|-----------------|----------------------------------------------------|---------------------------------------------------------------------------------------------------------|---------|
| ISM-1573-supp   | Indigenous-data sovereignty (CARE principles)      | culturalAuthorityRegistry Cosmos container (T196) + post-retrieval gate (T199)                          | AIATSIS |
| ISM-1573-supp.2 | Cultural-authority signature verification           | cosign keyless OR age-encrypted detached signatures on registry rows (T198)                             | AIATSIS |
| ISM-1573-supp.3 | Cultural-authority fail-closed posture              | gate fails closed for protected chunks when registry unreachable (Pass 1 Q-P1-01)                       | AIATSIS |

## Federal compliance controls

| ISM control | Title                                              | AMA implementation reference                                                                            | Owner |
|-------------|----------------------------------------------------|---------------------------------------------------------------------------------------------------------|-------|
| ISM-1546.2  | Privacy Act 1988 SAR endpoint                      | `apps/api/app/api/routes/audit_compliance.py::get_subject_access_request` (T206)                        | NEMA  |
| ISM-1546.3  | PSPF audit export                                  | `apps/api/app/api/routes/audit_compliance.py::get_pspf_audit_export` (T207)                             | AGD   |
| ISM-1573.4  | COMDISPLAN activation interlock                    | `apps/agents/common/retrieval_client.py::apply_comdisplan_activation` (T186)                            | NEMA  |

## Network controls

| ISM control | Title                                              | AMA implementation reference                                                                            | Owner |
|-------------|----------------------------------------------------|---------------------------------------------------------------------------------------------------------|-------|
| ISM-1395    | Region-bounded data residency                      | NN-2 + FR-RAG-CV-04: all Cosmos / Foundry / AI Search resources in Australia East                       | NEMA  |
| ISM-1396    | Inbound network filtering                          | APIM + WAF + private endpoints on Cosmos + AI Search                                                    | NEMA  |
| ISM-1397    | Outbound network filtering                         | egress lockdown via Container Apps env vars; allow-list for Foundry control plane                       | NEMA  |

## Identity & access

| ISM control | Title                                              | AMA implementation reference                                                                            | Owner |
|-------------|----------------------------------------------------|---------------------------------------------------------------------------------------------------------|-------|
| ISM-0405    | Privileged operator MFA                            | Entra ID + CA + just-in-time PIM on `Cosmos DB Built-in Data Owner`                                      | NEMA  |
| ISM-0407    | RBAC scope minimisation                             | DefaultAzureCredential + per-app managed identities (no shared secrets)                                  | NEMA  |
| ISM-0408    | Service principal rotation                         | Managed identities (no static secrets); secrets only in Key Vault with Conditional Access                | NEMA  |

## Coverage summary

- **24 ISM controls** mapped in this scaffold. Target ≥40 controls — additional rows authored by NEMA + AGD + AFP during T210 sign-off.
- **Top-2 anchor controls** (ISM-0468 + ISM-1552) named in Plan §F-A6.1; both carry full implementation refs.
- **`TODO` markers**: 0 (CI fails build if non-zero post-T210).

## Sign-off (HUMAN-IN-LOOP — T210)

This document MUST be co-signed by:

1. **NEMA** — Australian National Emergency Management Agency
2. **AGD** — Attorney-General's Department (PSPF + Privacy Act)
3. **AFP** — Australian Federal Police (national-security operations)

Sign-off file: `docs/compliance/ISM-2024-mapping-signoff.json` (created by T210).
CD pipeline gate: `infra/scripts/verify-carveout.ps1` extended in T211 to also
check for the sign-off file before allowing prod deploy.

## Change log

| Date       | Change                                                            | Author         |
|------------|-------------------------------------------------------------------|----------------|
| 2026-XX-XX | Initial scaffold (T209) — pending federal sign-off (T210).         | Implementation |
