from __future__ import annotations

from pathlib import Path

MAIN_BICEP = Path("infra/main.bicep")
ENTRA_MODULE = Path("infra/modules/entra-auth.bicep")
ENTRA_MSAL = Path("apps/web/src/lib/auth/entra-msal.ts")


def test_azd_outputs_supply_web_build_auth_configuration() -> None:
    main = MAIN_BICEP.read_text(encoding="utf-8")

    for name in (
        "NEXT_PUBLIC_AZURE_AD_CLIENT_ID",
        "NEXT_PUBLIC_AZURE_AD_TENANT_ID",
        "NEXT_PUBLIC_AZURE_AD_API_APP_ID",
        "NEXT_PUBLIC_AZURE_AD_API_AUDIENCE",
    ):
        assert f"output {name} string" in main
        assert f"name: '{name}'" in main
    assert "output NEXT_PUBLIC_ALLOW_ANONYMOUS_INCIDENT_MAP string" in main
    assert "name: 'NEXT_PUBLIC_ALLOW_ANONYMOUS_INCIDENT_MAP'" in main


def test_api_container_uses_dev_only_anonymous_map_configuration() -> None:
    main = MAIN_BICEP.read_text(encoding="utf-8")

    assert "var allowAnonymousIncidentMap = environmentTier == 'dev'" in main
    assert "var enableIncidentMapAuth = !allowAnonymousIncidentMap" in main
    assert "{ name: 'AMA_ALLOW_ANONYMOUS_INCIDENT_MAP', value: allowAnonymousIncidentMap ? '1' : '0' }" in main
    assert "{ name: 'AMA_ENABLE_INCIDENT_MAP_AUTH', value: enableIncidentMapAuth ? '1' : '0' }" in main
    assert "module entraAuth './modules/entra-auth.bicep' = if (enableIncidentMapAuth)" in main


def test_entra_module_provisions_spa_and_api_with_delegated_access() -> None:
    module = ENTRA_MODULE.read_text(encoding="utf-8")

    assert "Microsoft.Graph/applications@v1.0" in module
    assert "Microsoft.Graph/servicePrincipals@v1.0" in module
    assert "requiredResourceAccess" in module
    assert "access_as_user" in module
    assert "value: 'system-administrator'" in module
    assert "appRoleAssignmentRequired: false" in module


def test_msal_requests_the_provisioned_delegated_scope() -> None:
    msal = ENTRA_MSAL.read_text(encoding="utf-8")

    assert "NEXT_PUBLIC_AZURE_AD_API_AUDIENCE" in msal
    assert "/access_as_user`" in msal
