package au_region

# T015 — Constitution NN-2 (data sovereignty). Every resource MUST live in
# australiaeast or australiasoutheast except Foundry endpoints listed in
# infra/policy/foundry-carveout.yaml (FR-018).

allowed_regions := {"australiaeast", "australiasoutheast"}

is_carveout(rid) {
    co := data.foundry_carveout.carveouts[_]
    lower(co.foundry_resource_id) == lower(rid)
}

deny[msg] {
    change := input.changes[_]
    loc := lower(change.after.location)
    not allowed_regions[loc]
    not is_carveout(change.resource_id)
    msg := sprintf("au_region: %s located in %s — must be in australiaeast or australiasoutheast (or appear in foundry-carveout.yaml)", [change.resource_id, loc])
}
