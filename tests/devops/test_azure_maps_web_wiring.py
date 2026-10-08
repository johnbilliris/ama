from __future__ import annotations

from pathlib import Path

MAIN_BICEP = Path("infra/main.bicep")
MAPS_MODULE = Path("infra/modules/azure-maps.bicep")


def test_azure_maps_key_is_supplied_to_azd_and_web_app() -> None:
    main = MAIN_BICEP.read_text(encoding="utf-8")
    module = MAPS_MODULE.read_text(encoding="utf-8")

    assert "@secure()\noutput azureMapsPrimaryKey string = azureMaps.listKeys().primaryKey" in module
    assert "@secure()\noutput NEXT_PUBLIC_AZURE_MAPS_KEY string = azureMaps.outputs.azureMapsPrimaryKey" in main
    assert "{ name: 'NEXT_PUBLIC_AZURE_MAPS_KEY', value: azureMaps.outputs.azureMapsPrimaryKey }" in main


def test_azure_maps_cors_allows_only_development_web_origins() -> None:
    main = MAIN_BICEP.read_text(encoding="utf-8")
    module = MAPS_MODULE.read_text(encoding="utf-8")

    assert "'https://${webAppName}.azurewebsites.net'" in main
    assert "'http://localhost:3000'" in main
    assert "corsAllowedOrigins: [" in main
    assert "allowedOrigins: [origin]" in module
