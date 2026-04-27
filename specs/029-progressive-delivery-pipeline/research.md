# Phase 0 — Research: Progressive Delivery Pipeline (029)

**Date**: 2026-04-26
**Status**: Complete (all NEEDS CLARIFICATION resolved during `/speckit.clarify`)

This document records the design research that backs the Technical Context and the Phase 1 contracts. Every decision below is traceable to a clarification answer, an FR, or an SC in `spec.md`.

---

## R1 — IaC policy-as-code engine for the PR-time posture gate

- **Decision**: Open Policy Agent (OPA) + `conftest` consuming a single Rego ruleset under `infra/policy/rego/`, evaluated against the rendered Bicep What-If JSON for the target environment.
- **Rationale**:
  - Rego rules can read `infra/policy/posture-matrix.yaml` and `infra/policy/posture-exceptions.yaml` directly (the canonical artefacts FR-025 and FR-033 require), so the same matrix file drives PR-time *and* runtime gates with no translation step.
  - `conftest` runs in < 30 s for the typical PR diff, fitting the FR-002 / SC-002 10-minute median budget alongside the rest of the gate set.
  - Output is structured (per-rule decision + offending resource + property) which directly satisfies FR-023's "actionable, link-rich failure report" requirement.
- **Alternatives considered**:
  - **Checkov** — broad coverage but rules are opinionated and not posture-matrix-driven; harder to enforce *our* exact dev/staging/prod asymmetry.
  - **Pure Azure Policy at PR time** — Azure Policy only evaluates at deploy time; using it for PR feedback would require a `what-if` round-trip per rule and is far slower than OPA.
  - **Hand-rolled Python validator** — would re-implement a policy engine; rejected to avoid maintenance burden.
- **Spec cross-refs**: FR-001, FR-025, FR-028, FR-029, FR-032, FR-033

## R2 — Build-once, sign, SBOM, provenance

- **Decision**: Single image build per merge to `main` via `cd.yml` build job → Cosign signs the image with a workload-identity-issued certificate → Syft generates SPDX-format SBOM → GitHub-native SLSA-3 provenance attestation. The same digest is referenced by every downstream stage; deploy steps verify signature + SBOM + provenance before applying any deployment.
- **Rationale**:
  - Cosign + Syft + SLSA-3 are all GitHub-Actions-native, run on `ubuntu-22.04`, and integrate cleanly with OIDC (no static keys) — keeping FR-016 / SC-007 ("zero long-lived cloud credentials") intact.
  - SLSA-3 is the level explicitly named in FR-004 and represents the highest level achievable on hosted runners without bespoke infrastructure.
- **Alternatives considered**:
  - **Notary v2** — viable but ecosystem support is thinner; Cosign is the de-facto OCI signing tool.
  - **Per-environment rebuild** — would invalidate every downstream gate's relevance to production (US2's "what is verified in test is bit-for-bit what runs in production"); explicitly rejected by the spec.
- **Spec cross-refs**: FR-004, FR-005, US2

## R3 — Canary mechanism per service tier

- **Decision**:
  - **Container Apps services** (`api`, `agents`, `ingestion`): native revision-based traffic splitting at 5 / 25 / 50 / 100 %.
  - **Web tier** (Next.js on App Service): deployment-slot swap with Application Gateway / Front Door traffic-shift at the same stages (FR-010).
  - Stage advancement is driven by the `canary_controller.py` tool which polls SLO burn-rate over the per-stage observation window (10 / 15 / 30 / 60 min — Q1) and writes its decision to the `pipeline_state` Cosmos container plus the audit store.
- **Rationale**: Both mechanisms are Azure-native, in `australiaeast`, and already part of the platform's deployment surface (per Assumption in spec); no new external traffic-management layer is introduced.
- **Alternatives considered**:
  - **Azure Front Door weighted routing for all tiers** — would centralise traffic decisions but moves the decision out of the platform-native deploy primitive and complicates rollback (FR-008 needs a < 5 min restore time).
  - **Service mesh (e.g., Linkerd / Istio on AKS)** — overkill; the platform is not on AKS for the canary-eligible workloads.
- **Spec cross-refs**: FR-007, FR-008, FR-010, US4

## R4 — SLO burn-rate signal

- **Decision**: Application Insights / Azure Monitor with five SLOs already named in FR-007 (availability, p95 API latency, p95 dashboard load, signal freshness, recommendation correctness). `canary_controller.py` queries `metrics` + `logs` via the Azure Monitor Query SDK, computes fast-burn (5 % budget in 1 h) and slow-burn (10 % budget in 6 h), and emits structured stage decisions to the audit store.
- **Rationale**: Reuses existing telemetry per Assumption #1 in the spec; no new instrumentation introduced.
- **Spec cross-refs**: FR-007, FR-008, FR-009, FR-024, US4

## R5 — Cross-environment reference detection (FR-029)

- **Decision**: Two-layer detection per Q7 clarification.
  - **Layer 1 (PR time)**: `cross_env.rego` evaluates the Bicep What-If JSON, matching every resource ID / role-assignment scope / Key Vault reference against the canonical naming token (`-dev-`, `-staging-`, `-prod-`) and the target environment's RG name.
  - **Layer 2 (deploy time)**: `tools/pipeline/cross_env_check.py` issues an Azure Resource Graph query asserting every resource ID referenced by the deployment lives in the target RG.
- **Rationale**: The static layer catches the common case at PR time with sub-second feedback; the deploy-time layer catches dynamic / parameter-driven references that the static layer cannot. Together they close the gap without forcing every parameter to be statically resolved at PR time.
- **Spec cross-refs**: FR-029

## R6 — Post-deploy posture verification scope (FR-031)

- **Decision**: Full sweep on every deploy per Q8 clarification. `tools/pipeline/posture_verifier.py` issues a single Resource Graph query enumerating every resource in the target RG, joins to `posture-matrix.yaml`, and reports per-resource compliance. Failure on `staging` / `production` triggers FR-008 rollback; failure on `dev` raises a tracked issue without blocking.
- **Rationale**: Delta-only verification would let pre-existing out-of-band drift persist undetected between deploys (defeats the FR-019 nightly drift baseline). A full RG sweep is bounded (~15 resource types × small per-RG inventory) and completes well within the 5-minute evidence-pack window (FR-013, SC-005).
- **Spec cross-refs**: FR-031, FR-008, FR-019

## R7 — Posture-matrix exception lifecycle (FR-033)

- **Decision**: Per Q9, dual approval (security + compliance CODEOWNER) on a PR to `infra/policy/posture-exceptions.yaml`; mandatory `expires_at` ≤ 90 days; daily `posture-exception-sweep.yml` workflow auto-removes expired entries; renewal requires a fresh dual-approver PR (no silent extension).
- **Rationale**: Bounds exception lifetime mechanically (the historical failure mode of named exceptions is unbounded accumulation). 90 days is short enough to force regular re-justification but long enough to absorb planned remediation cycles.
- **Spec cross-refs**: FR-033, SC-018

## R8 — Dev anomaly detection (FR-026)

- **Decision**: Per Q10, rely on **Microsoft Defender for Cloud** (data-plane threat protection plans on Cosmos DB, Storage, Key Vault, AKS, Foundry where supported) plus **Microsoft Entra ID Protection** (risky sign-in / risky user signals). Both are enabled at the scope that covers the dev environment via `defender-baseline.bicep` — i.e. the dev subscription under Topology A, or the single shared subscription under Topology B (which transitively covers `staging` and `production` as well; that overlap is acceptable). Alerts route to the on-call security channel and persist to the central audit store. No bespoke thresholds in this feature.
- **Rationale**: Vendor-managed detection avoids re-implementing ML/heuristic anomaly detection and gives the security CODEOWNER a familiar console for tuning. Aligns with the platform's "Azure-native services preferred" constitutional principle (VIII).
- **Alternatives considered**:
  - **Bespoke Log Analytics KQL with custom thresholds** — fine-grained but unowned, would drift, and duplicates Defender's heuristics.
  - **Defer to manual review** — incompatible with FR-026's "MUST raise a security event".
- **Spec cross-refs**: FR-026

## R9 — Dev API key issuance and rotation (FR-030)

- **Decision**: Per Q6, exclusive `gh workflow dispatch` workflow `dev-key-issue.yml` running under the pipeline's federated OIDC workload identity. Workflow authenticates the requesting developer (`workflow_dispatch` actor claim → Entra ID lookup), mints/rotates a scoped data-plane key via the Azure SDK, writes it to `kv-ama-dev/secrets/devkey-{alias}-{service}` with a 24-hour expiry, revokes the prior key for that `{alias, service}` pair, and emits an append-only audit entry.
- **Rationale**: Removes any standing right to mint dev keys (preserves FR-016 end-to-end), produces a uniform audit trail, and forces rotation by design.
- **Spec cross-refs**: FR-030, FR-016, US8

## R10 — Evidence pack store

- **Decision**: Azure Blob Storage container in `australiaeast`, per-blob time-based immutability policy of 7 years with legal hold enabled. Hash of every pack written to the central audit store as `evidence_uri` + `digest` (FR-015 schema fields).
- **Rationale**: Native Azure capability, AU region, deny-modify, deny-delete during retention window — meets FR-014 directly. Hash-in-audit gives independent tamper-evidence even if the blob store is ever compromised.
- **Spec cross-refs**: FR-013, FR-014, SC-005, SC-012

## R11 — Pipeline state store

- **Decision**: A new `pipeline_state` Cosmos DB container co-located in the existing audit Cosmos account (same region, same identity, same retention class). Holds: canary stage cursors per service, the `change_freeze` document, the `last_known_good_at` index per service.
- **Rationale**: Avoids introducing a new data-store dependency, automatically inherits AU residency and the audit account's network/identity posture, and keeps FR-008's known-good lookup co-located with the audit events that prove the known-good status.
- **Spec cross-refs**: FR-008, FR-011, FR-021

## R12 — Identity and authority enforcement (FR-011, FR-011a)

- **Decision**: Authority for freeze invocation and emergency-hotfix approval is enforced via membership in three Entra ID groups (`ama-oncall-sre`, `ama-incident-commander`, `ama-emergency-approver`). The pipeline's OIDC token carries group claims (`groups` claim opt-in via Entra app manifest); workflows verify required claims at dispatch time AND the audit emitter independently re-verifies before writing the event. Group membership changes are themselves audited.
- **Rationale**: Two-point verification (dispatch + audit emitter) prevents a single workflow misconfiguration from bypassing authority. Per Q4 clarification.
- **Spec cross-refs**: FR-011, FR-011a, US6

## R13 — Foundry carve-out enforcement (FR-018)

- **Decision**: Named YAML at `infra/policy/foundry-carveout.yaml` lists every permitted non-AU Foundry deployment with: model name, region, justification, approver identities, review date. The OPA `au_region.rego` rule consults this file as the *only* exception path; Azure Policy assignments generate from the same file at **subscription scope under Topology A** or at **resource-group scope under Topology B** (per the environment-isolation clarification). Every other resource type targeting a non-AU region is denied at both layers.
- **Rationale**: Single source of truth (mirrors the posture-matrix pattern), auditable per SC-006, and structurally prevents the carve-out from widening through interpretation (only listed model-hosting resources pass).
- **Spec cross-refs**: FR-018, SC-006, Constitution v1.2.0 carve-out

## R14 — Foundry model-gateway data-minimisation (NN-2 carve-out condition)

- **Decision**: Inbound prompts to a non-AU Foundry endpoint MUST traverse the platform's existing model-gateway, which (a) strips PSPF-marked content via the existing classifier, (b) masks PII via the existing redactor, and (c) denies any prompt that fails either control. This control is mandatory whenever the target endpoint is on the carve-out list.
- **Rationale**: The constitution carve-out is conditional on data-minimisation at the gateway. Gateway already exists; this feature only wires the routing rule and the corresponding audit entry.
- **Spec cross-refs**: FR-018, Constitution v1.2.0 NN-2

## R15 — Staging / production developer JIT access

- **Decision**: Per Q5, Azure Bastion + hardened jump-host VM per `staging` and `production` VNet, role activation via Entra PIM (1 h default, 8 h max), Managed-Identity-only auth from the jump-host onward, full session/audit logging.
- **Rationale**: No point-to-site VPN, no public endpoints, no shared keys — preserves FR-027 posture even during incident triage. Bastion gives auditable session ingress; PIM gives time-bounded role activation.
- **Spec cross-refs**: FR-027, US8 Edge Cases

## R16 — Azure subscription topology (dual-mode)

- **Decision**: The pipeline supports **two Azure subscription topologies**, selectable per deployment and recorded in `infra/IDENTITY.md` as `subscription_topology: A | B`:
  - **Topology A (preferred for production tenants)**: one subscription per environment (`sub-ama-dev`, `sub-ama-staging`, `sub-ama-prod`), each containing exactly one resource group `rg-ama-{env}-{region}`. Azure Policy assignments (AU-region, posture matrix, deny-public-endpoint for non-`dev`) are scoped at **subscription** level. Defender for Cloud and Entra ID Protection are enabled per subscription, so cost and signal volume scale with environment criticality.
  - **Topology B (sandbox / single-subscription tenants)**: one shared subscription containing three resource groups `rg-ama-dev-{region}`, `rg-ama-staging-{region}`, `rg-ama-prod-{region}`. Azure Policy assignments are scoped at **resource-group** level. Defender / EIP enablement at the subscription transitively covers all three RGs (acceptable; the cost/signal overlap is the trade-off for using one sub).
- **Rationale**: The platform is being built first against a personal MCAP subscription where multi-subscription governance is not available; we cannot make Topology A a hard prerequisite without blocking initial delivery. Topology A remains the recommended target for any tenant that can grant the three subscriptions, because subscription boundaries provide blast-radius isolation that resource groups cannot (cross-RG role assignments are denied by IaC policy in both topologies, but cross-sub role assignments require Entra-tenant-level escalation under Topology A — a stronger control). Both topologies satisfy FR-025–FR-029 because the IaC policy gate (FR-029) enforces cross-environment-scope blocks regardless of whether "scope" resolves to a subscription or an RG.
- **Alternatives considered**:
  - **Topology A only**: rejected — would block any deployment on a single-subscription tenant; would have made the personal-MCAP build path infeasible.
  - **Topology B only**: rejected — gives up the strongest available platform-level isolation control for tenants that *can* afford three subscriptions; would limit the solution's suitability for genuine multi-environment regulated workloads.
  - **Hybrid (e.g., dev in shared sub, staging+prod in dedicated subs)**: rejected — increases operational complexity (two policy-assignment scopes, two Defender enablement modes, two CI/CD code paths) for marginal isolation benefit between staging and prod; and it makes the IaC policy enforcement of "no cross-environment role assignments" harder to express uniformly. The clarification mandates uniform topology across all three environments.
- **Implementation impact**:
  - The Bicep root MUST accept a `subscriptionTopology` parameter (`'A' | 'B'`, default `'B'` for backwards compatibility) and switch the policy-assignment scope accordingly (owned by T019a).
  - The OPA policy gate MUST validate that `infra/IDENTITY.md` declares the chosen topology and that the actual deploy targets match (no Topology A workflow targeting Topology B subscription, and vice versa).
  - The audit emitter MUST stamp each `deploy.*` event with `subscription_topology` for evidence-pack completeness.
  - Under Topology A, the cross-environment Rego rule (T015) MUST evaluate at **subscription scope** (full ARM IDs, not RG-name string match alone); under Topology B it evaluates at **resource-group scope**. T017 contract tests MUST include at least one Topology-A fixture (different subscription IDs across `dev`/`staging`/`prod` parameter files).
- **Cost / signal trade-off (Defender for Cloud, Entra ID Protection)**:
  - **Topology A**: Defender / EIP enabled per subscription means tenants can disable Defender plans on the `dev` subscription and only pay for `staging` + `production` plans — typically **~2× the per-subscription Defender SKU cost** (2 of 3 subs at full plan).
  - **Topology B**: a single shared subscription means enabling Defender / EIP at the subscription level transitively monitors all three RGs at **~1× the per-subscription Defender SKU cost**, but there is no plan-level isolation between dev workloads and prod (the same Defender plan watches both, and `dev`-only signals raise prod-grade alerts unless suppression rules are added). For tenants who chose Topology B specifically for cost reasons this is the expected outcome; tenants concerned with signal hygiene should choose Topology A.
- **Spec cross-refs**: spec.md §Clarifications Q (environment isolation), FR-025, FR-028, FR-029, ADR-029-01

## R17 — CODEOWNERS reviewer identities (ADR-029-01)

- **Status**: **Architecture decision — recorded as ADR-029-01.**
- **Decision**: CODEOWNERS entries MAY use **either** GitHub team handles (e.g., `@org/security-codeowners`) **or** individual GitHub user handles (e.g., `@johnbilliris`). Both forms are valid for satisfying FR-003 (CODEOWNERS-driven required reviews) and FR-033 (dual-approver gate on posture-matrix changes). The dual-approver requirement is enforced at branch-protection level via "require approval from at least N reviewers" combined with the CODEOWNERS pattern; whether the reviewers come from a team or are listed individually does not change the protection guarantee.
- **Context**: GitHub teams (`@org/<team>` syntax) are only available on GitHub organisation-owned repositories. The current repository (`johnbilliris/ama`) is **user-owned**, not organisation-owned, so team-scoped CODEOWNERS handles cannot be created or referenced. Migrating the repository into a GitHub organisation is out of scope for this feature; that migration is tracked separately.
- **Resolution under user-owned repo**: All CODEOWNERS entries that would otherwise reference `@org/security-codeowners`, `@org/compliance-codeowners`, `@org/sre-codeowners`, `@org/incident-domain-codeowners`, `@org/infrastructure-codeowners`, `@ama/security`, or `@ama/compliance` MUST be replaced with the repository owner's individual handle (`@johnbilliris`). The dual-approver semantics for FR-033 are then enforced solely through branch protection's "require N approving reviews" setting (set to 2 for posture-matrix paths). When the repository migrates to an organisation, the team handles in the table below MUST be substituted back in (one-line edit per CODEOWNERS row), and branch protection can additionally require approval *per CODEOWNERS team* (a stronger guarantee than user-level).
- **Future-state team mapping (apply on org migration, do not create until then)**:
  | Persona / domain | Team handle to restore | Files / paths |
  |---|---|---|
  | Security CODEOWNER | `@org/security-codeowners` | `infra/policy/posture-matrix.yaml`, `infra/policy/posture-exceptions.yaml`, label `posture-failure` |
  | Compliance CODEOWNER | `@org/compliance-codeowners` | `infra/policy/posture-matrix.yaml`, `infra/policy/posture-exceptions.yaml`, label `evidence-pack-reconciliation-failed` |
  | SRE CODEOWNER | `@org/sre-codeowners` | labels `slow-burn-pause`, `telemetry-unavailable`, `pipeline-budget-breach` |
  | Infrastructure CODEOWNER | `@org/infrastructure-codeowners` | `infra/**` |
  | Incident-domain CODEOWNER | `@org/incident-domain-codeowners` | `apps/api/app/api/routes/incident*`, `apps/agents/incident*`, `apps/web/src/app/incidents/**` |
- **Trade-offs accepted under user-owned mode**:
  - **Single point of failure**: a single user handle means no inherent redundancy if that user is unavailable. Mitigation: the emergency-hotfix lane (FR-012) and the change-freeze invocation (FR-011) still require Entra-group-backed approvers (the Entra groups exist independently of GitHub teams), so the break-glass paths remain operative. Routine non-emergency changes simply queue, which is consistent with FR-024's hold-on-missing-input posture.
  - **No "team" pull-request review-assignment automation**: with a user handle, GitHub will not auto-rotate review assignments across team members; the single handle is always assigned. Acceptable while there is one human maintainer.
  - **Dual-approver enforcement on posture changes**: branch protection's "require 2 approving reviews" still applies, but both approvals must come from non-author humans with write access; under user-owned mode that means the owner cannot approve their own PR but a second human collaborator must be added to the repo to satisfy FR-033 for posture-matrix changes. Until a second collaborator is granted write access, posture-matrix PRs will be blocked — this is a desired safety property, not a defect. **The second-collaborator onboarding is a one-time pre-flight step, owned by T000a; the second collaborator's GitHub identity MUST be recorded in `infra/IDENTITY.md` alongside the topology and CODEOWNERS-mode declarations.**
  - **GitHub Environments reviewer-list cap**: under user-owned mode, T024 places each member of `ama-oncall-sre` + `ama-incident-commander` + `ama-emergency-approver` as an **individual** reviewer on the `production` environment. **GitHub Environments hard-caps required reviewers at 6 distinct identities per environment**; the reviewer-sync reconciler (`tools/pipeline/src/pipeline_tools/reviewer_sync.py`) MUST therefore assert `len(union(group_members)) ≤ 6` and fail loudly when exceeded, recommending immediate migration to organisation mode. This constraint does not apply under organisation mode because team membership is gated by the team itself, not by the environment reviewer list. Until org migration, the union of the three Entra groups MUST be kept ≤ 6 distinct people; this is a documented operational constraint of ADR-029-01, not a permanent platform limit.
- **Reversibility**: The rollback path is mechanical — replace the user handles in `.github/CODEOWNERS`, the routing snippets in `tasks.md` T087, the `posture-exceptions` audit consumers in T067, and the documentation references in `data-model.md` and `quickstart.md`. No code change is required; only YAML/Markdown text substitution. The entire ADR-029-01 fallback is therefore a non-blocking, reversible accommodation, not an architectural simplification.
- **Spec cross-refs**: FR-003, FR-011, FR-011a, FR-012, FR-033, US3, US6

---

## Open / Deferred (low-impact, suitable for `/speckit.plan` follow-on or `/speckit.tasks`)

- Naming-token enforcement helper for staging/prod equivalents to dev's `*-dev-*` token — covered implicitly by CAF naming standard; will be explicit in `tasks.md`.
- Drift remediation SLA per posture violation severity tier — operational runbook; not a clarification blocker, will live in `quickstart.md` ops section.
