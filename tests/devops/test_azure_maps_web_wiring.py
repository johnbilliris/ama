from __future__ import annotations

from pathlib import Path

MAIN_BICEP = Path("infra/main.bicep")
MAPS_MODULE = Path("infra/modules/azure-maps.bicep")


def test_azure_maps_key_is_supplied_at_runtime_without_a_public_build_variable() -> None:
    main = MAIN_BICEP.read_text(encoding="utf-8")
    module = MAPS_MODULE.read_text(encoding="utf-8")

    assert "@secure()\noutput azureMapsPrimaryKey string = azureMaps.listKeys().primaryKey" in module
    assert "@secure()\noutput AZURE_MAPS_SUBSCRIPTION_KEY string = azureMaps.outputs.azureMapsPrimaryKey" in main
    assert "{ name: 'AZURE_MAPS_SUBSCRIPTION_KEY', value: azureMaps.outputs.azureMapsPrimaryKey }" in main
    assert "NEXT_PUBLIC_AZURE_MAPS_KEY" not in main


def test_azure_maps_cors_passes_the_frontend_origin_list_to_one_rule() -> None:
    main = MAIN_BICEP.read_text(encoding="utf-8")
    module = MAPS_MODULE.read_text(encoding="utf-8")

    assert "'https://${webAppName}.azurewebsites.net'" in main
    assert "'http://localhost:3000'" in main
    assert "corsAllowedOrigins: [" in main
    assert "corsRules: empty(corsAllowedOrigins) ? [] : [" in module
    assert "allowedOrigins: corsAllowedOrigins" in module
    assert "disableLocalAuth: environment != 'dev'" in module
