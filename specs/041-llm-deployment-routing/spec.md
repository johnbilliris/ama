# Feature Specification: Unambiguous LLM Deployment Configuration and Routing

**Feature Branch**: `model-upgrade-chat-sumlation`

**Feature Directory**: `specs/041-llm-deployment-routing`

**Created**: 2026-10-18

**Status**: Draft — specification quality validated; ready for planning

**Input**: User-provided requirements for "Unambiguous LLM Deployment Configuration and Routing", preserving FR-001–FR-016, US1–US4, acceptance scenarios, and exclusions. This checkpoint authorises specification creation only, not implementation, provisioning, model changes, deployment retirement, or commits.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Correct tier routing (US1, Priority: P1)

As an operator, I need reasoning, drafting, and simulation requests to use their designated deployments so that workloads remain isolated even when they share the same underlying model.

**Why this priority**: Deterministic routing protects live-incident capacity from simulation traffic and prevents configuration order from changing the destination.

**Independent Test**: Exercise each production inference path with three distinct deployments sharing one model and version, including MAF clients, the simulation controller, and the simulation sub-agent dispatcher. Verify designated destinations and explicit rejection of invalid configuration without needing resource migration.

**Acceptance Scenarios**:

1. **Shared model, separate deployments** — **Given** reasoning, drafting, and simulation use the same model and version but different deployment names, **When** each production client resolves its requested tier, **Then** it selects that tier's designated deployment regardless of mapping order.
2. **Simulation isolation** — **Given** both simulation and reasoning deployments are configured, **When** the controller or a simulation sub-agent makes an inference request, **Then** the request targets the simulation deployment.
3. **Missing simulation configuration** — **Given** the simulation deployment configuration is missing, **When** a simulation inference path is invoked, **Then** the application reports a configuration error rather than using reasoning capacity, and sends no inference request.
4. **MAF compatibility** — **Given** explicit reasoning and drafting deployment settings, **When** MAF creates clients for those tiers, **Then** both resolve successfully without requiring duplicate tier aliases in a legacy model-key map.
5. **Ambiguous legacy mapping** — **Given** one legacy routing key maps to different deployment names, **When** that mapping is validated, **Then** validation fails with an error identifying the conflicting key and deployments.
6. **Explicit precedence and compatible legacy use** — **Given** a valid explicit tier configuration and an unambiguous legacy model-key mapping designate different deployments, **When** the tier is resolved, **Then** the explicit tier configuration wins; **Given** no explicit setting and an unambiguous legacy mapping for a supported non-simulation inference path, **When** that path resolves configuration, **Then** legacy resolution remains supported without order-dependent selection.
7. **Invalid required configuration** — **Given** a required value is missing, empty, unsupported, or ambiguous, **When** the affected inference path is used, **Then** it reports an actionable error using existing logging and API error conventions before sending any inference request.

---

### User Story 2 - Safe infrastructure configuration (US2, Priority: P1)

As a platform engineer, I need deployment names and model selections configured independently so that a naming correction cannot unintentionally change the model or replace an existing deployment.

**Why this priority**: Correcting a configuration contract must not become an unauthorised model change or disruptive resource operation.

**Independent Test**: Compare the resolved configuration and a proposed change review against an environment's approved deployment baseline. Confirm all tier selections are explicit and existing resources and protections remain unchanged. No live provisioning is required for this specification checkpoint.

**Acceptance Scenarios**:

1. **Safe initial rollout** — **Given** an environment has approved existing deployments, **When** the initial configuration and routing fix is applied, **Then** it does not rename, replace, delete, or upgrade those deployments.
2. **Independent selections** — **Given** tier-specific deployment names, models, and versions, **When** top-level infrastructure configuration is evaluated, **Then** it passes through every selection explicitly, including identical model/version selections across different deployments, without hidden child-module defaults changing the result.
3. **Preserved operating baseline** — **Given** approved deployment names, model selections, versions, deployment SKUs, capacities, content-filter policies, and access controls, **When** initial-rollout changes are reviewed, **Then** all remain unchanged; any repository/live discrepancy is surfaced and reconciled before provisioning.
4. **Verified metadata** — **Given** outputs identify a tier's configured model and version, **When** deployment preflight compares them with Azure deployment properties, **Then** agreement is verified and any mismatch prevents provisioning until reconciled.
5. **Purpose-based defaults without forced rename** — **Given** configuration for a new deployment uses naming defaults, **When** a name is supplied by default, **Then** it describes operational purpose and environment without asserting model identity or size; **Given** an existing explicit deployment name, **Then** that name remains a valid value.

---

### User Story 3 - Trustworthy inference records (US3, Priority: P1)

As an auditor, I need inference records to distinguish the actual model from the deployment used so that model usage and failures can be investigated accurately.

**Why this priority**: Truthful provenance is required for operational investigations and constitutional transparency, including failures and degraded responses.

**Independent Test**: Inspect records for successful inference, attempted-but-failed inference, and responses produced without inference. Compare identities with configured and verified deployment metadata, and confirm historical records are unchanged.

**Acceptance Scenarios**:

1. **Truthful audit identity** — **Given** a deployment named `gpt-5.4-mini-dev` actually hosts `gpt-5.4`, **When** inference is recorded, **Then** the audit identifies the model as `gpt-5.4`, records the model version separately, and records the deployment name separately.
2. **No fabricated invocation** — **Given** inference was not attempted, **When** a failure or degraded response is recorded, **Then** the record does not fabricate a model invocation or claim a deployment was invoked.
3. **Unavailable identity** — **Given** identity information is unavailable, **When** a record is produced, **Then** it represents that information explicitly using repository audit conventions instead of substituting a deployment alias or obsolete hardcoded GPT-4o label.
4. **Preserved history** — **Given** historical audit and usage records exist, **When** corrected records are introduced, **Then** historical records remain unchanged.

---

### User Story 4 - Controlled naming migration (US4, Priority: P2)

As a platform engineer, I need to migrate misleading deployment names without an unplanned outage, model upgrade, or loss of rollback capability.

**Why this priority**: Purpose-based naming is useful but must be a later, opt-in resource migration, not a prerequisite for the P1 configuration and routing corrections.

**Independent Test**: Rehearse the migration procedure against an approved baseline, verifying replacement readiness, configuration switching, verification, rollback, and separately approved retirement while keeping model selection unchanged.

**Acceptance Scenarios**:

1. **Controlled naming migration** — **Given** replacement purpose-named deployments have been provisioned and verified, **When** application configuration switches to them, **Then** traffic uses the replacements and the previous configuration remains available for rollback until retirement is approved.
2. **Independent opt-in approval** — **Given** the initial rollout is complete and migration has not been approved, **When** the application operates, **Then** it continues to use existing explicit deployment names without replacement provisioning or retirement.
3. **Rollback and retirement control** — **Given** migration verification fails, **When** the operator executes rollback, **Then** traffic returns to the previous configured deployments with unchanged model selections; obsolete deployments are not deleted automatically and retirement requires separate approval.

### Edge Cases

- Three tiers share one model/version: tier identity, not the shared model key or insertion order, determines the destination.
- A legacy key names two different deployments: reject the conflict even if a different entry would otherwise win; do not choose the first or last entry.
- An explicit tier setting conflicts with an otherwise unambiguous legacy mapping: explicit tier configuration takes precedence. Precedence does not make an internally conflicting legacy mapping valid.
- Simulation configuration is absent or empty while live-incident deployment settings exist: fail before inference rather than falling back to reasoning or drafting.
- A selected path requires an unsupported tier or incomplete identity information: report required-configuration errors before inference; do not invent defaults. Unavailable audit identity still follows existing audit conventions.
- Repository configuration and verified live properties differ: require environment-specific reconciliation before provisioning rather than copying a dev observation into every environment.
- A request fails after inference was attempted: distinguish the attempted request from a response generated without inference; do not claim successful model execution solely because configuration was resolved.
- Replacement verification fails or a switch must be reversed: retain old deployment configuration and resources until rollback verification and separately approved retirement.
- Existing misleading names remain in use during the initial rollout: truthful audit metadata must not depend on renaming them.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001** The configuration contract shall represent each tier's operational purpose, deployment name, model identifier, and model version as distinct values.
- **FR-002** Reasoning, drafting, and simulation shall support independently configured deployment names, models, and versions, including multiple deployments sharing an identical model and version.
- **FR-003** The top-level infrastructure configuration shall expose and pass through these selections explicitly rather than relying on hidden child-module defaults.
- **FR-004** The initial rollout shall preserve each environment's approved existing deployment names, model selections, versions, deployment SKUs, capacity allocations, content-filter policies, and access controls. Repository/live discrepancies shall be surfaced and reconciled before provisioning.
- **FR-005** New deployment naming defaults shall describe operational purpose and environment without implying an underlying model or model size. Existing deployment names shall remain valid explicit configuration values.
- **FR-006** Runtime clients shall consistently honour the explicit AZURE_AI_REASONING_DEPLOYMENT, AZURE_AI_DRAFTING_DEPLOYMENT, and AZURE_AI_SIMULATION_DEPLOYMENT settings for tier-based requests.
- **FR-007** The simulation controller and simulation sub-agent dispatcher shall select the simulation deployment. They shall not silently fall back to reasoning or drafting deployments.
- **FR-008** MAF and other production inference clients shall resolve tier configuration consistently, including when all tiers share one model identifier and version.
- **FR-009** A conflicting mapping that associates one routing key with multiple deployment names shall be rejected with an actionable configuration error. Mapping order shall not determine routing.
- **FR-010** Legacy model-key mappings may remain supported only when resolution is unambiguous. Explicit tier configuration shall take precedence.
- **FR-011** Missing, empty, unsupported, or ambiguous configuration required by an inference path shall fail explicitly before that path sends an inference request. Existing logging and API error conventions shall be followed.
- **FR-012** Infrastructure outputs shall supply the model and version metadata associated with each tier's configured deployment. Deployment preflight checks shall verify that this metadata agrees with Azure deployment properties.
- **FR-013** Inference audit records shall distinguish model_id, model_version, and deployment_alias. A deployment alias shall not be substituted for a model identifier.
- **FR-014** Failure and degraded-response records shall not claim that a model or deployment was invoked when no inference request occurred. Unavailable identity information shall be represented explicitly using the repository's audit conventions.
- **FR-015** Model usage records shall not fall back to obsolete hardcoded GPT-4o deployment labels. Historical records shall remain unchanged.
- **FR-016** The implementation shall provide a controlled migration procedure covering replacement provisioning, configuration switching, verification, rollback, and separately approved retirement of obsolete deployments.

### Project-wide Local Image Build Requirement - 2026-10-20

- ALL local image builds shall target only `linux/arm64`, including preparation,
  application, job, test and Dev Container images. No local AMD64, emulated
  AMD64 or multi-platform build is permitted.
- Compose, Bake, Dev Container and manual local build commands shall explicitly
  select ARM64. A deployment target's architecture shall not override this rule.
- Container Apps AMD64 deployment artifacts shall be built remotely in ACR or
  native hosted CI, with `remoteBuild: true` retained. Local ARM64 output is
  not valid Container Apps deployment evidence.
- Prior local AMD64 observations remain historical evidence, not executable
  instructions for future work. This amendment does not authorise a rebuild,
  image replacement, cloud mutation or traffic promotion.

### Key Entities *(include if feature involves data)*

- **Operational tier**: The requested purpose — reasoning, drafting, or simulation — independent of model identity.
- **Tier configuration**: Association of an operational tier with a deployment name, model identifier, and model version for an environment.
- **Deployment identity**: The named inference deployment, independently associated with its approved model, version, SKU, capacity, content-filter policy, and access controls.
- **Model identity**: Underlying model identifier and version; multiple deployments and tiers may share this identity without becoming interchangeable.
- **Legacy routing mapping**: Compatibility association from a routing key to a deployment; valid only when unambiguous and subordinate to explicit tier selection.
- **Inference audit/usage record**: Provenance of an actual inference attempt or an explicitly non-inference outcome, distinguishing model_id, model_version, and deployment_alias with truthful availability and invocation status.
- **Approved environment baseline**: Reviewed existing deployment properties and protections, reconciled with live properties before provisioning; not inferred from deployment names.
- **Migration record/procedure**: Approved replacement and previous configurations, readiness verification, switch results, rollback evidence, and a separate retirement decision.

### Scope, Constraints, and Exclusions

- Initial rollout changes configuration clarity, routing correctness, validation, and provenance only while preserving approved existing deployment identities and operating selections. It does not execute resource migration.
- Later purpose-based naming is a separately controlled, opt-in resource migration. Treat deployment renaming as resource migration, not an in-place rename.
- No model upgrade or downgrade is authorised by this feature.
- Do not select a mini model merely to match an existing misleading name.
- Preserve authentication, content safety, Australian residency controls, and applicable Azure Policy requirements.
- Preserve existing chat behaviour, streaming contracts, and simulation functionality except for the specified routing and error-handling corrections.
- Do not automatically delete old Azure deployments or rewrite historical audit records.
- Regenerate checked-in ARM templates from Bicep; do not maintain divergent handwritten copies.
- Changes to Help chat enablement, model evaluation strategy, and general cost optimisation are outside scope.
- Constitutional human authorisation, privacy, auditability, and data sovereignty controls remain in force. This feature does not introduce or expand a non-Australian model-hosting exception.
- This Phase 1 checkpoint creates only this specification, its normal specification-quality checklist, and the local feature pointer. It does not authorise code or infrastructure changes, live checks/provisioning, later phases, model selection, deployment deletion, or commits.

### Requirement Acceptance Coverage

| Requirement | Story and verification coverage |
| --- | --- |
| FR-001 | US2 scenarios 2 and 4; US3 scenario 1 |
| FR-002 | US1 scenario 1; US2 scenario 2 |
| FR-003 | US2 scenario 2 |
| FR-004 | US2 scenarios 1 and 3 |
| FR-005 | US2 scenario 5; US4 scenarios 1 and 2 |
| FR-006 | US1 scenarios 1, 4, and 6 |
| FR-007 | US1 scenarios 2 and 3 |
| FR-008 | US1 scenarios 1 and 4 |
| FR-009 | US1 scenarios 1 and 5 |
| FR-010 | US1 scenarios 5 and 6 |
| FR-011 | US1 scenarios 3 and 7 |
| FR-012 | US2 scenario 4 |
| FR-013 | US3 scenario 1 |
| FR-014 | US3 scenarios 2 and 3; attempted-failure edge case |
| FR-015 | US3 scenarios 3 and 4 |
| FR-016 | US4 scenarios 1–3 |

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Across 100% of inventoried production inference paths and all six orderings of three distinct tier mappings sharing one model/version, each request selects its designated tier deployment. Operators receive consistent tier behaviour regardless of client or mapping order.
- **SC-002**: In simulation controller and sub-agent acceptance cases, 100% of attempted simulation requests target the configured simulation deployment; missing or empty simulation settings result in zero inference requests and zero silent use of live-incident deployments.
- **SC-003**: 100% of acceptance cases containing missing, empty, unsupported, ambiguous, or conflicting required routing configuration produce an actionable configuration error before inference; conflict errors identify the key and conflicting deployments.
- **SC-004**: In 100% of sampled acceptance records for successful, failed, and non-inference outcomes, auditors can distinguish the underlying model and version from the deployment used, or see explicitly unavailable identity. There are zero fabricated invocations, zero deployment-alias substitutions for model identity, and zero new obsolete hardcoded GPT-4o fallback labels.
- **SC-005**: For every environment included in initial-rollout verification, comparison with the approved baseline shows zero deployment renames, replacements, deletions, model/version changes, SKU/capacity changes, content-filter changes, or access-control changes. All identified repository/live discrepancies are reconciled before provisioning.
- **SC-006**: A separately approved naming-migration rehearsal completes replacement readiness verification, traffic switching, post-switch verification, and rollback to the previous configuration without model changes or loss of the existing chat/streaming contracts. Both forward and rollback checks pass; zero old deployments are retired without separate approval.
- **SC-007**: Existing chat and simulation acceptance flows pass in full except for the explicitly corrected routing/error outcomes, and comparison of historical audit records before and after the change shows zero modifications.

## Assumptions

- **Context, not universal defaults**: The supplied investigation reports three AMA dev deployments using GPT-5.4 version `2026-03-05`, including a drafting deployment misleadingly labelled mini, while repository Bicep defaults reference GPT-5.6. These are supplied dev-context observations, not live checks performed in this phase, approved target selections, or defaults for other environments. No model upgrade, downgrade, or mini-model substitution is inferred.
- **Environment baseline dependency**: Before any future provisioning, an authorised platform engineer will establish and reconcile each environment's approved existing deployment properties. Neither repository defaults nor the dev observation alone is authoritative for every environment. An unresolved discrepancy blocks provisioning.
- **Compatibility boundary**: Legacy compatibility cannot override explicit tiers or the simulation-isolation requirement. Missing explicit simulation deployment configuration is an error even if a shared legacy model key could resolve to a live deployment.
- **Validation boundary**: Required configuration is validated before the affected path sends inference, not necessarily at application startup. This permits unrelated functionality to retain the constitution's graceful-degradation behaviour without hiding configuration failures.
- **Identity dependency**: Verified deployment metadata and existing audit/error conventions will be available to subsequent planning. Unknown identity uses those conventions; this specification does not invent a new sentinel format or fabricate invocation data.
- **Naming boundary**: New defaults encode purpose and environment; exact spelling and any existing uniqueness constraints are deferred to planning without changing explicit existing names or underlying models.
- **Migration approval dependency**: Replacement provisioning and temporary capacity require separate authorisation and environment-specific readiness checks. Documentation of migration is required; executing it is neither automatic nor part of the initial rollout.
- **Acceptance evidence boundary**: The production-path inventory and existing chat/streaming acceptance baseline will be established during later authorised work. Success percentages measure the complete inventoried acceptance set, not an invented performance or model-quality target.
