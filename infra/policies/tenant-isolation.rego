# Tenant isolation policy
# Enforced by OPA/Gatekeeper to prevent cross-agency and cross-region data leakage.

package drh.tenant_isolation

import rego.v1

# ── Cross-agency data access denied ──

deny contains msg if {
    input.action == "read"
    input.resource.organisation_id != input.principal.organisation_id
    not input.principal.role in {"incident_commander", "planning_officer"}
    msg := sprintf(
        "Cross-agency read denied: principal org '%s' cannot access resource org '%s'.",
        [input.principal.organisation_id, input.resource.organisation_id],
    )
}

deny contains msg if {
    input.action == "write"
    input.resource.organisation_id != input.principal.organisation_id
    msg := sprintf(
        "Cross-agency write denied: principal org '%s' cannot mutate resource org '%s'.",
        [input.principal.organisation_id, input.resource.organisation_id],
    )
}

# ── Cross-region partition access denied ──

deny contains msg if {
    input.resource.jurisdiction_id
    input.principal.jurisdiction_id
    input.resource.jurisdiction_id != input.principal.jurisdiction_id
    not input.principal.role in {"incident_commander", "planning_officer"}
    msg := sprintf(
        "Cross-region access denied: principal jurisdiction '%s' cannot access '%s'.",
        [input.principal.jurisdiction_id, input.resource.jurisdiction_id],
    )
}

# ── Cosmos DB partition key must match tenant scope ──

deny contains msg if {
    input.action in {"read", "write"}
    input.storage.partition_key
    input.storage.partition_key != input.principal.tenant_scope
    msg := "Storage partition key must match the principal's tenant scope."
}

# ── Redis cache namespace must be scoped ──

deny contains msg if {
    input.action == "cache_read"
    input.cache.namespace
    not startswith(input.cache.namespace, input.principal.tenant_scope)
    msg := "Cache namespace must be scoped to the tenant."
}

# ── Event bus channel must be tenant-scoped ──

deny contains msg if {
    input.action == "publish_event"
    input.event.channel
    not startswith(input.event.channel, input.principal.tenant_scope)
    msg := "Event channel must be scoped to the tenant."
}

# ── Spec 036 — Simulation Cosmos containers whitelist (FR-016, FR-050) ──
#
# These containers are tenant-scoped via `/simulationId` partition keys; their
# names appear here so cross-container reads/writes that miss the partition
# check fall through to the standard tenant-isolation deny rules.

simulation_cosmos_containers := {
    "simulation_synthetic_signals",
    "sub_agent_invocation_records",
    "simulation_threads",
    "exercise_outcome_index",
    "routing_decisions",
    "simulation_audit_entries",
    "simulation_audit_max_seq",
}

deny contains msg if {
    input.action in {"read", "write"}
    input.storage.container in simulation_cosmos_containers
    input.storage.partition_key
    input.storage.partition_key != input.principal.simulation_id
    msg := sprintf(
        "Simulation container '%s' partition key must equal principal.simulation_id (got '%s' vs '%s').",
        [input.storage.container, input.storage.partition_key, input.principal.simulation_id],
    )
}
