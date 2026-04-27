package posture

# T012 — Posture-matrix gate (FR-025, FR-027, FR-028).
# Consumes infra/policy/posture-matrix.yaml + posture-exceptions.yaml +
# the Bicep What-If JSON for the target environment. Per resource in the
# What-If, look up the matrix cell and emit deny[] for every property mismatch.
#
# Conftest invocation (PR gate):
#   conftest test --policy infra/policy/rego \
#     --data infra/policy/posture-matrix.yaml \
#     --data infra/policy/posture-exceptions.yaml \
#     <whatif.json>
#
# Input contract (the conftest driver passes data.posture_matrix and data.exceptions):
#   input.changes[i].resource_id, input.changes[i].after.type, .after.properties.*
#   input.environment      = "dev" | "staging" | "production"
#   data.posture_matrix    = parsed posture-matrix.yaml
#   data.exceptions        = parsed posture-exceptions.yaml

# Active exception lookup helper
exception_active(env, type, property_path) {
    e := data.exceptions.exceptions[_]
    e.environment == env
    e.resource_type == type
    e.property_path == property_path
    time.parse_rfc3339_ns(sprintf("%sT00:00:00Z", [e.expires_at])) > time.now_ns()
}

# Find the matrix cell for a (env, resource_type) tuple
cell(env, type) = c {
    e := data.posture_matrix.environments[_]
    e.name == env
    c := [r | r := e.resource_types[_]; r.type == type][0]
}

# Public-access mismatch
deny[msg] {
    change := input.changes[_]
    type := change.after.type
    rule := cell(input.environment, type)
    actual := change.after.properties.publicNetworkAccess
    actual == "Enabled"
    rule.network.public_access == "deny"
    not exception_active(input.environment, type, "network.public_access")
    msg := sprintf("posture[network.public_access]: %s allows public access in %s but matrix requires deny", [change.resource_id, input.environment])
}

# Private endpoint required but absent
deny[msg] {
    change := input.changes[_]
    type := change.after.type
    rule := cell(input.environment, type)
    rule.network.private_endpoint_required == true
    not change.after.properties.privateEndpointConnections
    not exception_active(input.environment, type, "network.private_endpoint_required")
    msg := sprintf("posture[network.private_endpoint_required]: %s missing private endpoint in %s", [change.resource_id, input.environment])
}

# Shared key disabled but enabled
deny[msg] {
    change := input.changes[_]
    type := change.after.type
    rule := cell(input.environment, type)
    rule.identity.shared_key_disabled == true
    change.after.properties.allowSharedKeyAccess == true
    not exception_active(input.environment, type, "identity.shared_key_disabled")
    msg := sprintf("posture[identity.shared_key_disabled]: %s permits shared keys in %s but matrix requires disabled", [change.resource_id, input.environment])
}

# Local auth must be disabled
deny[msg] {
    change := input.changes[_]
    type := change.after.type
    rule := cell(input.environment, type)
    rule.identity.local_auth_disabled == true
    change.after.properties.disableLocalAuth == false
    not exception_active(input.environment, type, "identity.local_auth_disabled")
    msg := sprintf("posture[identity.local_auth_disabled]: %s allows local auth in %s but matrix requires disabled", [change.resource_id, input.environment])
}
