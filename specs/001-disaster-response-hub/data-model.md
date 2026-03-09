# Data Model: Autonomous Disaster Response Coordination Hub

## Organisation

**Purpose**: Represents an Australian agency, council, utility, community body, or volunteer group that participates in preparedness or incident response.

**Fields**:
- `organisationId`: string, immutable identifier
- `name`: string, unique within a jurisdictional scope
- `category`: enum (`commonwealth`, `state`, `territory`, `local_government`, `emergency_service`, `health`, `utility`, `transport`, `community`, `volunteer`, `other`)
- `jurisdictionIds`: array of jurisdiction references
- `operatingRole`: string
- `authorityLevel`: string
- `contactChannels`: array of structured contact records
- `participationConditions`: array of rule strings
- `status`: enum (`active`, `inactive`, `planned`)

**Relationships**:
- One organisation has many personas.
- One organisation participates in many incidents.
- One organisation can map to many framework assignments.

**Validation rules**:
- Must belong to at least one jurisdiction.
- `name` must be non-empty.
- `status` cannot be `inactive` if active incidents reference the organisation.

## Persona

**Purpose**: Represents a role a user performs within an organisation.

**Fields**:
- `personaId`: string
- `organisationId`: reference
- `title`: string
- `roleType`: enum (`incident_commander`, `operations`, `planning`, `logistics`, `public_information`, `field_coordinator`, `planner`, `executive`, `observer`, `other`)
- `decisionRights`: array of strings
- `informationNeeds`: array of strings
- `communicationPathways`: array of strings
- `permissionProfile`: string
- `status`: enum (`active`, `inactive`)

**Relationships**:
- Many personas belong to one organisation.
- Personas own tasks, approvals, and published alerts.

**Validation rules**:
- `organisationId` is required.
- `decisionRights` must not be empty for approval-capable personas.

## Jurisdiction

**Purpose**: Models Commonwealth, state, territory, regional, or local governance boundaries.

**Fields**:
- `jurisdictionId`: string
- `name`: string
- `level`: enum (`commonwealth`, `state`, `territory`, `regional`, `local`)
- `parentJurisdictionId`: optional reference
- `policySetId`: reference
- `geospatialBoundary`: GeoJSON polygon or multipolygon
- `status`: enum (`active`, `inactive`)

**Relationships**:
- One jurisdiction has many organisations.
- One jurisdiction has many framework assignments.
- Incidents can affect many jurisdictions.

**Validation rules**:
- `level` is required.
- `geospatialBoundary` is required for any jurisdiction below Commonwealth level.

## OperatingFramework

**Purpose**: Captures command, control, approval, and escalation models, including AIIMS-aligned function structures.

**Fields**:
- `frameworkId`: string
- `name`: string
- `frameworkType`: enum (`aiims`, `agency_specific`, `jurisdictional_policy`, `communications`, `other`)
- `principles`: array of strings
- `controlModel`: string
- `approvalRules`: array of structured rules
- `escalationRules`: array of structured rules
- `spanOfControlGuidance`: string
- `status`: enum (`active`, `retired`, `draft`)

**Relationships**:
- Frameworks apply to many jurisdictions and organisations via assignments.

**Validation rules**:
- `approvalRules` required when `frameworkType` affects safety-critical decisions.

## FrameworkAssignment

**Purpose**: Connects an organisation or jurisdiction to a framework with effective dates and rule overrides.

**Fields**:
- `assignmentId`: string
- `frameworkId`: reference
- `jurisdictionId`: optional reference
- `organisationId`: optional reference
- `effectiveFrom`: datetime
- `effectiveTo`: optional datetime
- `overrides`: object

**Validation rules**:
- At least one of `jurisdictionId` or `organisationId` is required.

## JurisdictionPolicy

**Purpose**: Encodes privacy, residency, visibility, and communication rules by jurisdiction.

**Fields**:
- `policySetId`: string
- `retentionRules`: array
- `allowedLocationPrecisionMeters`: integer
- `crossAgencySharingRules`: array
- `languageRequirements`: array of language codes
- `dataResidencyRegion`: string

**Validation rules**:
- `dataResidencyRegion` must be an Australian Azure region.

## Incident

**Purpose**: Represents a live disaster or rehearsal scenario.

**Fields**:
- `incidentId`: string
- `title`: string
- `incidentType`: enum (`bushfire`, `flood`, `cyclone`, `storm`, `earthquake`, `other`)
- `status`: enum (`monitoring`, `active`, `stabilising`, `recovery`, `closed`, `rehearsal`)
- `severity`: enum (`advisory`, `watch`, `warning`, `emergency`)
- `startedAt`: datetime
- `endedAt`: optional datetime
- `affectedJurisdictionIds`: array of references
- `participatingOrganisationIds`: array of references
- `currentObjectives`: array of strings
- `owningFrameworkIds`: array of references

**Relationships**:
- Incidents contain many signals, recommendations, tasks, approvals, alerts, and timeline events.

**Validation rules**:
- `affectedJurisdictionIds` cannot be empty.
- `endedAt` must be null unless `status` is `recovery` or `closed`.

## DataSource

**Purpose**: Describes the origin of a signal.

**Fields**:
- `dataSourceId`: string
- `name`: string
- `kind`: enum (`authoritative`, `sensor`, `iot`, `field_report`, `social`, `community`, `derived`)
- `provider`: string
- `collectionMethod`: string
- `authorityRank`: integer
- `status`: enum (`available`, `degraded`, `offline`)

**Validation rules**:
- `authorityRank` required for authoritative and derived sources.

## Signal

**Purpose**: Represents a normalized observation or alert input.

**Fields**:
- `signalId`: string
- `incidentId`: optional reference
- `dataSourceId`: reference
- `category`: enum (`weather`, `hydrology`, `fire`, `geohazard`, `infrastructure`, `community_report`, `social_report`, `resource_status`)
- `occurredAt`: datetime
- `receivedAt`: datetime
- `jurisdictionId`: optional reference
- `location`: GeoJSON object with precision metadata
- `payload`: object
- `confidenceScore`: float 0-1
- `freshnessScore`: float 0-1
- `validationStatus`: enum (`pending`, `validated`, `contradicted`, `rejected`, `escalated`)
- `provenance`: object with source URI, collector, and notes

**Relationships**:
- Signals can contribute to hazard assessments, recommendations, and alerts.

**Validation rules**:
- `receivedAt` must be greater than or equal to `occurredAt`.
- `confidenceScore` and `freshnessScore` must be within 0-1.

## HazardAssessment

**Purpose**: Versioned assessment produced from fused signals.

**Fields**:
- `hazardAssessmentId`: string
- `incidentId`: reference
- `assessmentType`: enum (`spread_prediction`, `impact_projection`, `route_risk`, `infrastructure_risk`, `community_impact`)
- `inputSignalIds`: array of references
- `version`: integer
- `generatedAt`: datetime
- `confidenceLevel`: enum (`low`, `medium`, `high`)
- `summary`: string
- `artifacts`: array of URIs

**Validation rules**:
- `inputSignalIds` cannot be empty.
- `version` increases monotonically per incident and assessment type.

## Recommendation

**Purpose**: Proposed action generated from current context.

**Fields**:
- `recommendationId`: string
- `incidentId`: reference
- `type`: enum (`evacuation`, `resource_allocation`, `coordination`, `public_alert`, `infrastructure_action`)
- `summary`: string
- `explanation`: string
- `supportingSignalIds`: array of references
- `requiredApprovalLevel`: string
- `confidenceLevel`: enum (`low`, `medium`, `high`)
- `status`: enum (`proposed`, `under_review`, `approved`, `rejected`, `escalated`, `executed`, `expired`)
- `proposedByAgent`: string

**Relationships**:
- Recommendations can spawn tasks and approvals.

**Validation rules**:
- `explanation` required.
- `status` cannot move to `executed` unless at least one approval exists when approval is required.

**State transitions**:
- `proposed -> under_review`
- `under_review -> approved | rejected | escalated`
- `approved -> executed | expired`
- `escalated -> under_review | rejected`

## ApprovalDecision

**Purpose**: Records human review outcomes for safety-critical outputs.

**Fields**:
- `approvalDecisionId`: string
- `recommendationId`: optional reference
- `publicAlertId`: optional reference
- `approverPersonaId`: reference
- `outcome`: enum (`approved`, `rejected`, `escalated`, `timed_out`)
- `rationale`: string
- `conditions`: array of strings
- `decidedAt`: datetime

**Validation rules**:
- Must reference at least one of `recommendationId` or `publicAlertId`.
- `rationale` required.

## CoordinationTask

**Purpose**: Tracks cross-agency operational work.

**Fields**:
- `taskId`: string
- `incidentId`: reference
- `summary`: string
- `priority`: enum (`critical`, `high`, `normal`, `low`)
- `status`: enum (`new`, `acknowledged`, `in_progress`, `blocked`, `completed`, `cancelled`)
- `ownerOrganisationId`: reference
- `ownerPersonaId`: optional reference
- `dependencyTaskIds`: array of references
- `dueAt`: optional datetime
- `blockingReason`: optional string

**Validation rules**:
- `ownerOrganisationId` required.
- `blockingReason` required when status is `blocked`.

## PublicAlert

**Purpose**: Community-facing message for approved communications.

**Fields**:
- `alertId`: string
- `incidentId`: reference
- `status`: enum (`draft`, `pending_approval`, `approved`, `published`, `superseded`, `cancelled`)
- `approvalMode`: enum (`human_approved`, `autonomous`, `escalated`)
- `audienceSegments`: array
- `languages`: array of language codes
- `accessibilityAttributes`: array
- `channelSet`: array of strings
- `contentBlocks`: object
- `publishedAt`: optional datetime

**Validation rules**:
- `languages` cannot be empty.
- `publishedAt` required when status is `published`.

**State transitions**:
- `draft -> pending_approval`
- `pending_approval -> approved | cancelled`
- `approved -> published | superseded`

## ScenarioRun

**Purpose**: Stores a rehearsal or replay execution.

**Fields**:
- `scenarioRunId`: string
- `incidentTemplateId`: string
- `requestedByPersonaId`: reference
- `scenarioType`: enum (`bushfire`, `flood`, `cyclone`, `storm`, `cross_jurisdiction`)
- `status`: enum (`queued`, `running`, `completed`, `failed`, `cancelled`)
- `startedAt`: optional datetime
- `completedAt`: optional datetime
- `resultSummary`: optional string
- `evidenceArtifactUris`: array of URIs

**Validation rules**:
- `resultSummary` required on `completed`.

## TimelineEvent

**Purpose**: Append-only audit and review record.

**Fields**:
- `timelineEventId`: string
- `incidentId`: reference
- `eventType`: string
- `actorType`: enum (`agent`, `persona`, `system`)
- `actorId`: string
- `occurredAt`: datetime
- `payload`: object

**Validation rules**:
- Timeline events are immutable after creation.