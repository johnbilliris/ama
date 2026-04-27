package cross_env

# T013 — FR-029 cross-environment reference detection (PR-time layer).
# Dual-mode: under Topology A scope = subscription IDs; under Topology B scope = RG names.
# Reads input.identity.subscription_topology to decide which scope check to apply.

target_env := input.environment
topology := input.identity.subscription_topology

# Token map for the static scan
token_for("dev") = "-dev-"
token_for("staging") = "-staging-"
token_for("production") = "-prod-"

# Topology B: deny if any resource ID references a RG whose token does not match the target env
deny[msg] {
    topology == "B"
    change := input.changes[_]
    rid := lower(change.resource_id)
    other := ["dev", "staging", "production"][_]
    other != target_env
    contains(rid, token_for(other))
    msg := sprintf("cross_env[topology_B]: resource %s references %s-environment scope while deploying to %s", [change.resource_id, other, target_env])
}

# Topology A: deny if any resource ID's subscription GUID does not match the target subscription
deny[msg] {
    topology == "A"
    change := input.changes[_]
    expected_sub := input.identity.topology_subscription_ids[target_env]
    sub := regex.find_n(`/subscriptions/([0-9a-f-]+)/`, change.resource_id, 1)[0]
    sub_id := substring(sub, len("/subscriptions/"), len(sub) - len(sub) + 36)
    sub_id != expected_sub
    msg := sprintf("cross_env[topology_A]: resource %s lives in subscription %s but %s targets subscription %s", [change.resource_id, sub_id, target_env, expected_sub])
}

# Role assignment scope crosses environments (both topologies)
deny[msg] {
    change := input.changes[_]
    change.after.type == "Microsoft.Authorization/roleAssignments"
    scope := lower(change.after.properties.scope)
    other := ["dev", "staging", "production"][_]
    other != target_env
    contains(scope, token_for(other))
    msg := sprintf("cross_env[role_assignment]: role assignment %s scopes into %s while deploying to %s", [change.resource_id, other, target_env])
}
