"""Factory that maps IngestionPipelineConfig to concrete pipeline instances."""

from __future__ import annotations

import logging
from typing import Any

from apps.ingestion.pipeline_config import IngestionPipelineConfig

logger = logging.getLogger(__name__)

# pipeline_id prefix → (module_path, class_name)
_PIPELINE_REGISTRY: dict[str, tuple[str, str]] = {
    "bom-warnings": ("apps.ingestion.pipelines.bom_warnings", "BomWarningsPipeline"),
    "bom-forecasts": ("apps.ingestion.pipelines.bom_warnings", "BomWarningsPipeline"),
    "bom-observations": ("apps.ingestion.pipelines.bom_observations", "BomObservationsPipeline"),
    "bom-observations-nsw": ("apps.ingestion.pipelines.bom_observations", "BomObservationsPipeline"),
    "bom-radar": ("apps.ingestion.pipelines.bom_radar", "BomRadarPipeline"),
    "bom-flood-warnings": ("apps.ingestion.pipelines.bom_warnings", "BomWarningsPipeline"),
    "bom-rss": ("apps.ingestion.pipelines.bom_rss", "BomRssPipeline"),
    "bom-aws-stations": ("apps.ingestion.pipelines.sensor_aws", "BomAwsSensorPipeline"),
    "bom-river-gauges": ("apps.ingestion.pipelines.sensor_river_gauge", "RiverGaugePipeline"),
    "ga-earthquakes": ("apps.ingestion.pipelines.ga_earthquakes", "GaEarthquakePipeline"),
    "ga-tsunami": ("apps.ingestion.pipelines.ga_tsunami", "GaTsunamiPipeline"),
    "ga-hotspots": ("apps.ingestion.pipelines.ga_hotspots", "GaHotspotPipeline"),
    "nsw-rfs-fire": ("apps.ingestion.pipelines.fire_service", "FireServicePipeline"),
    "vic-cfa-fire": ("apps.ingestion.pipelines.fire_service", "FireServicePipeline"),
    "qld-qfes-fire": ("apps.ingestion.pipelines.fire_service", "FireServicePipeline"),
    "nsw-ses-flood": ("apps.ingestion.pipelines.ses_flood", "SesFloodPipeline"),
    "epa-air-quality": ("apps.ingestion.pipelines.sensor_epa_air", "EpaAirQualityPipeline"),
    "sentinel-satellite": ("apps.ingestion.pipelines.satellite_sentinel", "SentinelSatellitePipeline"),
    "himawari-satellite": ("apps.ingestion.pipelines.satellite_himawari", "HimawariSatellitePipeline"),
    "twitter-disaster": ("apps.ingestion.pipelines.social_twitter", "TwitterPipeline"),
    "facebook-community": ("apps.ingestion.pipelines.social_facebook", "FacebookPipeline"),
    "reddit-australia": ("apps.ingestion.pipelines.social_reddit", "RedditPipeline"),
    "snap-send-solve": ("apps.ingestion.pipelines.community_snap", "SnapSendSolvePipeline"),
    "webeoc-ims": ("apps.ingestion.pipelines.ims_webeoc", "ImsWebEocPipeline"),
    "icon-ims": ("apps.ingestion.pipelines.ims_webeoc", "ImsWebEocPipeline"),
}

# Map pipeline_id to the state_code/state kwarg required by certain pipelines
_STATE_CODE_MAP: dict[str, str] = {
    "nsw-rfs-fire": "nsw",
    "vic-cfa-fire": "vic",
    "qld-qfes-fire": "qld",
    "nsw-ses-flood": "nsw",
}


def create_pipeline(config: IngestionPipelineConfig, **extra_kwargs: Any) -> Any:
    """Instantiate a concrete pipeline from its config."""
    entry = _PIPELINE_REGISTRY.get(config.pipeline_id)
    if entry is None:
        logger.warning("No pipeline class registered for %s", config.pipeline_id)
        return None

    module_path, class_name = entry
    from importlib import import_module
    mod = import_module(module_path)
    cls = getattr(mod, class_name)

    kwargs: dict[str, Any] = {
        "circuit_breaker_threshold": config.circuit_breaker_threshold,
        "circuit_breaker_backoff_initial": config.circuit_breaker_backoff_initial_seconds,
        "circuit_breaker_backoff_max": config.circuit_breaker_backoff_max_seconds,
        **extra_kwargs,
    }

    # Inject state_code / state for pipelines that require it
    state = _STATE_CODE_MAP.get(config.pipeline_id)
    if state is not None:
        # FireServicePipeline / SesFloodPipeline use 'state_code', BomObservationsPipeline uses 'state'
        if "state_code" in cls.__init__.__code__.co_varnames:
            kwargs["state_code"] = state
        else:
            kwargs["state"] = state

    # Pass endpoint URL for pipelines that accept it
    if config.endpoint_url and "endpoint_url" in cls.__init__.__code__.co_varnames:
        kwargs["endpoint_url"] = config.endpoint_url

    return cls(**kwargs)
