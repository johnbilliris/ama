from app.auth.rbac_registry import is_role_allowed_on_route


def test_system_administrator_can_read_incident_map() -> None:
    assert is_role_allowed_on_route("system-administrator", "/api/incidents/map")
