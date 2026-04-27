package secret_hygiene

# T014 — FR-027 / FR-016 — no plain-text secrets in Bicep What-If output.
# Heuristic patterns based on common Azure resource property shapes.

# Account keys / connection strings as literal strings in properties
deny[msg] {
    change := input.changes[_]
    val := walk_value(change.after.properties)
    is_string(val)
    re_match(`(?i)(AccountKey|SharedAccessKey)=[A-Za-z0-9+/=]{40,}`, val)
    msg := sprintf("secret_hygiene: literal account/SAS key in %s — must use Key Vault reference", [change.resource_id])
}

# Bare passwords
deny[msg] {
    change := input.changes[_]
    pw := change.after.properties.adminPassword
    is_string(pw)
    pw != ""
    not startswith(pw, "@Microsoft.KeyVault(")
    msg := sprintf("secret_hygiene: literal adminPassword in %s — must use Key Vault reference @Microsoft.KeyVault(...)", [change.resource_id])
}

# Storage account: requireInfrastructureEncryption must be true in non-dev
deny[msg] {
    change := input.changes[_]
    change.after.type == "Microsoft.Storage/storageAccounts"
    input.environment != "dev"
    not change.after.properties.encryption.requireInfrastructureEncryption
    msg := sprintf("secret_hygiene: %s missing requireInfrastructureEncryption in %s", [change.resource_id, input.environment])
}

# Walk a nested object yielding scalar leaves for inspection
walk_value(x) = x { not is_object(x); not is_array(x) }
walk_value(x) = v { is_object(x); v := walk_value(x[_]) }
walk_value(x) = v { is_array(x); v := walk_value(x[_]) }
