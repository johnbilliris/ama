# Spec 033 — Audit container immutability (T010, FR-012a, ADR-033-02)
package main

audit_container_name := "audit_entries"

deny_audit_delete[msg] {
    resource := input.resources[_]
    resource.type == "Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments"
    actions := resource.properties.permissions[_].dataActions[_]
    contains(lower(actions), "items/delete")
    contains(lower(resource.properties.scope), audit_container_name)
    msg := sprintf("FR-012a violation: role assignment %v grants delete on container %v.", [resource.name, audit_container_name])
}

deny_audit_delete[msg] {
    resource := input.resources[_]
    resource.type == "Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers"
    contains(lower(resource.name), audit_container_name)
    resource.properties.resource.defaultTtl > 0
    msg := sprintf("FR-012a violation: container %v has positive defaultTtl=%v.", [resource.name, resource.properties.resource.defaultTtl])
}
