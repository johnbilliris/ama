# Data Model: Data Source Governance

## DataSourceRegistryEntry (extends DataSource)

**Purpose**: A catalogued data source with full governance metadata, constitutional compliance profile, and agent assignments. Extends the existing DataSource model from spec 001.

**Fields**:
- `data_source_id`: string, immutable identifier (inherited)
- `name`: string, human-readable source name (inherited)
- `kind`: enum (`authoritative`, `sensor`, `iot`, `field_report`, `social`, `community`, `derived`) (inherited)
- `sub_category`: string, granular classification within kind (e.g., `weather_climate`, `geohazard`, `emergency_services`, `health`, `transport_infrastructure`, `utilities`, `gov_commonwealth`, `gov_state`, `gov_territory`, `gov_local`, `air_quality`, `satellite`, `river_gauge`, `weather_station`, `social_twitter`, `social_facebook`, `social_reddit`, `volunteer_rescue`, `community_reporting`, `incident_management`, `agent_generated`, `aggregated_risk`, `historical`)
- `provider`: string, owning or providing organisation name
- `collection_method`: string, how data is collected (e.g., `api_pull`, `push_webhook`, `manual_entry`, `satellite_downlink`, `sensor_network`)
- `data_type`: string, primary data format or content type (e.g., `geojson`, `cap_alert`, `json_observations`, `text_report`, `image_raster`)
- `update_frequency`: string, expected update cadence (e.g., `real_time`, `5_minutes`, `hourly`, `daily`, `event_driven`, `manual`)
- `geographic_coverage`: string, spatial scope (e.g., `national`, `nsw`, `vic`, `qld`, `sa`, `wa`, `tas`, `nt`, `act`, `regional`, `local`)
- `trust_tier`: enum (`tier_1_authoritative_government`, `tier_2_verified_institutional`, `tier_3_operational_sensor`, `tier_4_field_reports`, `tier_5_community_volunteer`, `tier_6_social_unverified`, `tier_7_derived_computed`)
- `authority_rank`: integer 1–7, numeric mapping of trust_tier (inherited, reinterpreted)
- `status`: enum (`available`, `degraded`, `offline`, `deactivated`) (inherited, extended with `deactivated`)
- `compliance_status`: enum (`unassessed`, `compliant`, `partially_compliant`, `non_compliant`, `compliance_lapsed`), derived from constitutional assessments
- `governance_status`: enum (`unassigned`, `assigned`, `fully_governed`), derived from agent assignments and handoff chains
- `grace_period_start`: optional datetime, when compliance-lapsed grace period began (FR-012b)
- `grace_period_end`: optional datetime, when auto-blocking will occur (FR-012b)
- `deactivated_at`: optional datetime, when source was deactivated
- `created_at`: datetime
- `updated_at`: datetime

**Relationships**:
- One data source has many ConstitutionalAssessments (one per principle).
- One data source has one or more AgentGovernanceAssignments (primary + secondary).
- One data source has one HandoffChainDefinition.
- One data source has many GovernanceAuditEntries.
- One data source references zero or more FunctionalDomainPrecedence records.
- Referenced by Signal.dataSourceId in the signal ingestion path.

**Validation rules**:
- `name` must be non-empty.
- `kind` must be one of the 7 defined values.
- `sub_category` must be a valid value for the given `kind`.
- `trust_tier` and `authority_rank` must be consistent (tier_1 = rank 1, tier_7 = rank 7).
- `status` cannot transition to `deactivated` if source has active handoff chains in use during an active incident.
- `compliance_status` cannot be `compliant` if any ConstitutionalAssessment is `non_compliant`.
- `governance_status` is `fully_governed` only when source has at least one agent assignment AND a valid handoff chain AND compliance_status is `compliant` or `partially_compliant`.

**State transitions** (status):
- `available -> degraded | offline | deactivated`
- `degraded -> available | offline | deactivated`
- `offline -> available | degraded | deactivated`
- `deactivated` is terminal (history retained)

**State transitions** (compliance_status):
- `unassessed -> compliant | partially_compliant | non_compliant`
- `compliant -> compliance_lapsed` (when re-review fails, FR-012b)
- `partially_compliant -> compliant | non_compliant | compliance_lapsed`
- `non_compliant -> compliant | partially_compliant` (after remediation)
- `compliance_lapsed -> compliant | partially_compliant | non_compliant` (after re-assessment)
- `compliance_lapsed -> non_compliant` (automatic, when grace period expires)

## ConstitutionalAssessment

**Purpose**: A structured review of a single data source against one constitutional principle, recording compliance status, rationale, and governance metadata.

**Fields**:
- `assessment_id`: string, immutable identifier
- `data_source_id`: reference to DataSourceRegistryEntry
- `principle`: enum (`life_safety_first`, `multi_agent_coordination`, `data_trust_provenance_freshness`, `privacy_security_regional_policy`, `multilingual_accessible_actionable`, `cloud_platform`)
- `compliance_status`: enum (`compliant`, `partially_compliant`, `non_compliant`, `not_applicable`)
- `explanation`: string, assessor rationale for the compliance determination
- `conditions`: array of strings, required mitigations or conditions for conditional compliance
- `gaps`: array of strings, specific gaps identified (e.g., "missing freshness metadata", "no contradiction detection")
- `assessor_id`: string, identity of the governance or safety lead who performed the assessment
- `assessed_at`: datetime
- `superseded_by`: optional reference to a newer assessment_id (for re-reviews)
- `is_current`: boolean, true for the latest assessment per source+principle
- `triggered_by`: enum (`initial_review`, `source_change`, `constitution_amendment`), reason for assessment

**Relationships**:
- Many assessments belong to one DataSourceRegistryEntry.
- Each source should have at most one current assessment per principle.
- Superseded assessments form a linked chain for audit history.

**Validation rules**:
- `explanation` is required (non-empty).
- `assessor_id` is required.
- `conditions` is required when `compliance_status` is `partially_compliant`.
- `gaps` is required when `compliance_status` is `partially_compliant` or `non_compliant`.
- Only one assessment per source+principle can have `is_current = true`.

## AgentGovernanceAssignment

**Purpose**: The assignment of a responsible agent to a data source, including role and operational scope.

**Fields**:
- `assignment_id`: string, immutable identifier
- `data_source_id`: reference to DataSourceRegistryEntry
- `agent_name`: enum (`monitoring`, `risk_assessment`, `evacuation`, `resource_allocation`, `communication`), validated against spec 004 agent catalogue
- `role`: enum (`primary`, `secondary`)
- `scope_of_responsibility`: string, description of what the agent does with this source
- `operational_conditions`: array of strings, conditions under which the assignment applies
- `assigned_by`: string, identity of the architect or planner
- `assigned_at`: datetime
- `status`: enum (`active`, `revoked`)

**Relationships**:
- Many assignments belong to one DataSourceRegistryEntry (one primary, zero or more secondary).
- Agent name references the agent catalogue from spec 004.

**Validation rules**:
- `agent_name` must exist in the agent catalogue (FR-009c).
- Each data source must have exactly one `primary` assignment before `governance_status` can be `assigned` or `fully_governed`.
- `scope_of_responsibility` is required.
- Cannot create a new assignment for a source with `compliance_status` = `non_compliant` (FR-006).

## HandoffChainDefinition

**Purpose**: The defined sequence of agent-to-agent handoffs for signals originating from a data source.

**Fields**:
- `chain_id`: string, immutable identifier
- `data_source_id`: reference to DataSourceRegistryEntry
- `steps`: array of HandoffStep objects (ordered)
- `created_by`: string, identity of the architect
- `created_at`: datetime
- `updated_at`: datetime
- `status`: enum (`active`, `draft`, `deprecated`)

**HandoffStep** (embedded object):
- `step_order`: integer, 1-based position in the chain
- `source_agent`: string, agent sending the signal
- `target_agent`: string, agent receiving the signal
- `confidence_threshold`: optional float 0–1, minimum confidence to forward
- `category_filter`: optional array of signal category enums, restricts which categories this step handles
- `payload_contract_ref`: optional string, reference to the expected payload schema

**Relationships**:
- One chain belongs to one DataSourceRegistryEntry.
- Steps reference agent names validated against the agent catalogue.

**Validation rules**:
- `steps` must contain at least one step.
- Each step's `source_agent` and `target_agent` must exist in the agent catalogue (FR-009c).
- Steps must be ordered: step N's `target_agent` must equal step N+1's `source_agent` (chain continuity).
- First step's `source_agent` must match the `agent_name` of the primary AgentGovernanceAssignment for this data source.
- `confidence_threshold` must be between 0 and 1 if specified.
- `category_filter` values must match the signal category enum.

## FunctionalDomainPrecedence

**Purpose**: Records which data source is authoritative for a given hazard type within a jurisdiction, supporting contradictory signal resolution (FR-010a).

**Fields**:
- `precedence_id`: string, immutable identifier
- `hazard_type`: enum (`weather`, `hydrology`, `fire`, `geohazard`, `infrastructure`, `community_report`, `social_report`, `resource_status`), matches signal category enum
- `jurisdiction_id`: optional reference, null for national defaults
- `primary_data_source_id`: reference to DataSourceRegistryEntry, the authoritative source
- `rationale`: string, why this source has precedence
- `created_by`: string
- `created_at`: datetime

**Relationships**:
- References one DataSourceRegistryEntry as the authoritative source.
- Optionally scoped to a jurisdiction; null jurisdiction_id indicates national default.

**Validation rules**:
- `primary_data_source_id` must reference an active, constitutionally approved source.
- At most one national default per `hazard_type`.
- At most one entry per `hazard_type` + `jurisdiction_id` combination.
- When resolving precedence: check jurisdiction-specific override first, then fall back to national default.

## GovernanceAuditEntry

**Purpose**: Immutable record of a governance action for the complete audit trail (FR-013).

**Fields**:
- `audit_entry_id`: string, immutable identifier
- `data_source_id`: reference to DataSourceRegistryEntry
- `action`: enum (`registered`, `updated`, `deactivated`, `assessment_created`, `assessment_superseded`, `approved`, `conditionally_approved`, `rejected`, `agent_assigned`, `agent_revoked`, `handoff_defined`, `handoff_updated`, `handoff_deprecated`, `rereview_triggered`, `grace_period_started`, `grace_period_extended`, `grace_period_expired`, `auto_blocked`, `precedence_set`)
- `actor_id`: string, identity of the user or system performing the action
- `timestamp`: datetime
- `details`: object, action-specific payload (e.g., old and new values, assessment summary, assignment details)
- `related_entity_id`: optional string, reference to the specific assessment, assignment, or chain affected

**Relationships**:
- Many audit entries belong to one DataSourceRegistryEntry.
- Append-only: entries are never modified or deleted.

**Validation rules**:
- `actor_id` is required.
- `timestamp` is required.
- `details` must contain sufficient context to reconstruct the governance state change.
- Entries are immutable after creation.

## Entity Relationship Summary

```
DataSourceRegistryEntry (1) ──── (0..*) ConstitutionalAssessment
DataSourceRegistryEntry (1) ──── (0..*) AgentGovernanceAssignment
DataSourceRegistryEntry (1) ──── (0..1) HandoffChainDefinition
DataSourceRegistryEntry (1) ──── (0..*) GovernanceAuditEntry
DataSourceRegistryEntry (1) ──── (0..*) FunctionalDomainPrecedence
DataSourceRegistryEntry (1) ──── (0..*) Signal [existing, via dataSourceId]
FunctionalDomainPrecedence (0..1) ──── (0..1) Jurisdiction [existing]
AgentGovernanceAssignment ── validates against ── AgentCatalogue [spec 004]
HandoffChainDefinition.steps ── validates against ── AgentCatalogue [spec 004]
```

## Reconciliation with Existing Models

The spec 001 data model defines `DataSource` with 7 fields (`dataSourceId`, `name`, `kind`, `provider`, `collectionMethod`, `authorityRank`, `status`). The current implementation in `packages/domain/src/domain/models/data_source.py` has 5 fields (`data_source_id`, `name`, `kind`, `authority_rank`, `status`). This spec reconciles as follows:

| Field | Spec 001 | Current Code | Spec 005 Action |
|-------|----------|--------------|-----------------|
| `data_source_id` | `dataSourceId` | `data_source_id` | Keep (Python naming) |
| `name` | ✅ | ✅ | Keep |
| `kind` | ✅ | ✅ | Keep |
| `provider` | ✅ | ❌ (missing) | Add |
| `collection_method` | `collectionMethod` | ❌ (missing) | Add |
| `authority_rank` | `authorityRank` | ✅ | Keep, map to trust_tier |
| `status` | ✅ | ✅ | Extend with `deactivated` |
| `sub_category` | — | — | Add (new in 005) |
| `trust_tier` | — | — | Add (new in 005, maps to authority_rank) |
| `data_type` | — | — | Add (new in 005) |
| `update_frequency` | — | — | Add (new in 005) |
| `geographic_coverage` | — | — | Add (new in 005) |
| Governance fields | — | — | Add (compliance_status, governance_status, grace period) |
