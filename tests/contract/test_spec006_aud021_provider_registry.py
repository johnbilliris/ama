from __future__ import annotations

import json
from pathlib import Path

from apps.ingestion.pipeline_configs import PIPELINE_CONFIGS
from apps.ingestion.pipeline_factory import _PIPELINE_BINDINGS

REGISTRY_PATH = Path("specs/006-data-ingestion-storage/evidence/provider-source-activation-registry.json")
CATALOGUE_PATH = Path("packages/domain/src/domain/seed/data_sources_australia.json")

REQUIRED_PIPELINES = {
    "bom-warnings",
    "bom-forecasts",
    "bom-flood-warnings",
    "bom-rss",
    "ga-earthquakes",
    "ga-tsunami",
    "ga-hotspots",
    "nsw-rfs-fire",
    "vic-cfa-fire",
    "qld-qfes-fire",
    "sa-cfs-fire",
    "wa-dfes-fire",
    "tas-tfs-fire",
    "act-esa-fire",
    "nt-pfes-fire",
    "nsw-ses-flood",
    "vic-ses-flood",
    "qld-ses-flood",
    "sentinel-satellite",
}


def _load_registry() -> dict[str, dict]:
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    records = payload.get("records", [])
    return {str(item["runtimePipelineId"]): item for item in records if isinstance(item, dict)}


def _catalogue_ids() -> set[str]:
    rows = json.loads(CATALOGUE_PATH.read_text(encoding="utf-8"))
    return {
        str(row.get("data_source_id", "")).strip()
        for row in rows
        if isinstance(row, dict) and str(row.get("data_source_id", "")).strip()
    }


def test_required_pipeline_coverage_exists_in_config_factory_and_registry() -> None:
    configured = {config.pipeline_id for config in PIPELINE_CONFIGS}
    registered = set(_PIPELINE_BINDINGS.keys())
    evidence = set(_load_registry().keys())

    assert REQUIRED_PIPELINES.issubset(configured)
    assert REQUIRED_PIPELINES.issubset(registered)
    assert REQUIRED_PIPELINES.issubset(evidence)


def test_every_configured_data_source_id_exists_in_catalogue_and_registry() -> None:
    catalogue_ids = _catalogue_ids()
    registry = _load_registry()

    for config in PIPELINE_CONFIGS:
        assert config.pipeline_id in registry, f"missing registry record for {config.pipeline_id}"
        assert config.data_source_ids, f"{config.pipeline_id} must include data source ids"
        for source_id in config.data_source_ids:
            assert source_id in catalogue_ids, f"unknown catalogue source id {source_id}"
            assert registry[config.pipeline_id]["catalogueDataSourceId"] == source_id


def test_enabled_runtime_identities_are_unique() -> None:
    enabled_ids = [config.pipeline_id for config in PIPELINE_CONFIGS if config.enabled]
    assert len(enabled_ids) == len(set(enabled_ids))


def test_disabled_configs_require_activation_blocker() -> None:
    for config in PIPELINE_CONFIGS:
        if not config.enabled:
            assert (config.activation_blocker or "").strip(), f"{config.pipeline_id} missing activation blocker"


def test_enabled_entries_require_verified_endpoint_and_access_fields() -> None:
    registry = _load_registry()
    for config in PIPELINE_CONFIGS:
        if not config.enabled:
            continue
        record = registry[config.pipeline_id]
        endpoint = record["endpoint"]
        access = record["access"]
        assert record["enabled"] is True
        assert str(endpoint.get("url", "")).strip()
        assert str(endpoint.get("owner", "")).strip()
        assert str(endpoint.get("format", "")).strip()
        assert access.get("accessStatus") in {"repo-validated", "externally-verified"}
        assert access.get("licenseStatus") in {"repo-validated", "externally-verified"}
        assert access.get("rateStatus") in {"repo-validated", "externally-verified"}


def test_usgs_substitution_is_truthful_and_not_mislabelled_as_ga_primary() -> None:
    record = _load_registry()["ga-earthquakes"]
    endpoint_url = str(record["endpoint"]["url"]).lower()
    assert "usgs.gov" in endpoint_url
    provider = record["providerAttribution"]
    substitution = record["approvedSubstitution"]
    assert "USGS" in str(provider["effectiveProvider"])
    assert provider["substitution"] != "none"
    assert str(substitution["status"]).startswith("approved")


def test_rss_deviation_and_sentinel_contract_are_explicitly_blocked() -> None:
    registry = _load_registry()

    rss = registry["bom-rss"]
    assert rss["enabled"] is False
    assert "deviation" in str(rss["providerAttribution"]["substitution"]).lower()
    assert "rss" in str(rss["activation_blocker"]).lower()

    sentinel = registry["sentinel-satellite"]
    assert sentinel["enabled"] is False
    assert "copernicus data space" in str(sentinel["activation_blocker"]).lower()
