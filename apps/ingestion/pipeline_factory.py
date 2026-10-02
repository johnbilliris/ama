"""Factory that maps IngestionPipelineConfig to concrete pipeline instances."""

from __future__ import annotations

import inspect
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from apps.ingestion.pipeline_config import IngestionPipelineConfig

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AdapterSpec:
    module_path: str
    class_name: str
    source_class: str
    supported_formats: set[str]


@dataclass(frozen=True)
class PipelineBinding:
    adapter_key: str
    endpoint_kwarg: str | None = "endpoint_url"
    static_kwargs: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PipelineValidationReport:
    errors: list[str]
    warnings: list[str]


_ADAPTER_SPECS: dict[str, AdapterSpec] = {
    "bom_warnings": AdapterSpec(
        module_path="apps.ingestion.pipelines.bom_warnings",
        class_name="BomWarningsPipeline",
        source_class="authoritative",
        supported_formats={"xml_bom", "cap_xml"},
    ),
    "bom_observations": AdapterSpec(
        module_path="apps.ingestion.pipelines.bom_observations",
        class_name="BomObservationsPipeline",
        source_class="sensor",
        supported_formats={"json"},
    ),
    "bom_radar": AdapterSpec(
        module_path="apps.ingestion.pipelines.bom_radar",
        class_name="BomRadarPipeline",
        source_class="satellite",
        supported_formats={"png"},
    ),
    "bom_rss": AdapterSpec(
        module_path="apps.ingestion.pipelines.bom_rss",
        class_name="BomRssPipeline",
        source_class="authoritative",
        supported_formats={"rss"},
    ),
    "bom_aws": AdapterSpec(
        module_path="apps.ingestion.pipelines.sensor_aws",
        class_name="BomAwsSensorPipeline",
        source_class="sensor",
        supported_formats={"json"},
    ),
    "river_gauges": AdapterSpec(
        module_path="apps.ingestion.pipelines.sensor_river_gauge",
        class_name="RiverGaugePipeline",
        source_class="sensor",
        supported_formats={"json"},
    ),
    "ga_earthquakes": AdapterSpec(
        module_path="apps.ingestion.pipelines.ga_earthquakes",
        class_name="GaEarthquakePipeline",
        source_class="authoritative",
        supported_formats={"geojson"},
    ),
    "ga_tsunami": AdapterSpec(
        module_path="apps.ingestion.pipelines.ga_tsunami",
        class_name="GaTsunamiPipeline",
        source_class="authoritative",
        supported_formats={"cap_xml"},
    ),
    "ga_hotspots": AdapterSpec(
        module_path="apps.ingestion.pipelines.ga_hotspots",
        class_name="GaHotspotPipeline",
        source_class="authoritative",
        supported_formats={"geojson"},
    ),
    "fire_service": AdapterSpec(
        module_path="apps.ingestion.pipelines.fire_service",
        class_name="FireServicePipeline",
        source_class="authoritative",
        supported_formats={"geojson"},
    ),
    "ses_flood": AdapterSpec(
        module_path="apps.ingestion.pipelines.ses_flood",
        class_name="SesFloodPipeline",
        source_class="authoritative",
        supported_formats={"geojson"},
    ),
    "epa_air": AdapterSpec(
        module_path="apps.ingestion.pipelines.sensor_epa_air",
        class_name="EpaAirQualityPipeline",
        source_class="sensor",
        supported_formats={"json"},
    ),
    "sentinel": AdapterSpec(
        module_path="apps.ingestion.pipelines.satellite_sentinel",
        class_name="SentinelSatellitePipeline",
        source_class="satellite",
        supported_formats={"geotiff"},
    ),
    "himawari": AdapterSpec(
        module_path="apps.ingestion.pipelines.satellite_himawari",
        class_name="HimawariSatellitePipeline",
        source_class="satellite",
        supported_formats={"geotiff", "png"},
    ),
    "twitter": AdapterSpec(
        module_path="apps.ingestion.pipelines.social_twitter",
        class_name="TwitterPipeline",
        source_class="social",
        supported_formats={"json"},
    ),
    "facebook": AdapterSpec(
        module_path="apps.ingestion.pipelines.social_facebook",
        class_name="FacebookPipeline",
        source_class="social",
        supported_formats={"json"},
    ),
    "reddit": AdapterSpec(
        module_path="apps.ingestion.pipelines.social_reddit",
        class_name="RedditPipeline",
        source_class="social",
        supported_formats={"json"},
    ),
    "snap": AdapterSpec(
        module_path="apps.ingestion.pipelines.community_snap",
        class_name="SnapSendSolvePipeline",
        source_class="community",
        supported_formats={"json"},
    ),
    "ims_webeoc": AdapterSpec(
        module_path="apps.ingestion.pipelines.ims_webeoc",
        class_name="WebEocPipeline",
        source_class="ims",
        supported_formats={"json"},
    ),
    "ims_icon": AdapterSpec(
        module_path="apps.ingestion.pipelines.ims_webeoc",
        class_name="IconPipeline",
        source_class="ims",
        supported_formats={"json"},
    ),
}

_PIPELINE_BINDINGS: dict[str, PipelineBinding] = {
    "bom-warnings": PipelineBinding(adapter_key="bom_warnings"),
    "bom-forecasts": PipelineBinding(adapter_key="bom_warnings"),
    "bom-observations": PipelineBinding(adapter_key="bom_observations"),
    "bom-observations-nsw": PipelineBinding(adapter_key="bom_observations", static_kwargs={"state": "nsw"}),
    "bom-radar": PipelineBinding(adapter_key="bom_radar"),
    "bom-flood-warnings": PipelineBinding(adapter_key="bom_warnings"),
    "bom-rss": PipelineBinding(adapter_key="bom_rss"),
    "bom-aws-stations": PipelineBinding(adapter_key="bom_aws"),
    "bom-river-gauges": PipelineBinding(adapter_key="river_gauges"),
    "ga-earthquakes": PipelineBinding(adapter_key="ga_earthquakes"),
    "ga-tsunami": PipelineBinding(adapter_key="ga_tsunami"),
    "ga-hotspots": PipelineBinding(adapter_key="ga_hotspots"),
    "nsw-rfs-fire": PipelineBinding(adapter_key="fire_service", static_kwargs={"state_code": "nsw"}),
    "vic-cfa-fire": PipelineBinding(adapter_key="fire_service", static_kwargs={"state_code": "vic"}),
    "qld-qfes-fire": PipelineBinding(adapter_key="fire_service", static_kwargs={"state_code": "qld"}),
    "sa-cfs-fire": PipelineBinding(adapter_key="fire_service", static_kwargs={"state_code": "sa"}),
    "wa-dfes-fire": PipelineBinding(adapter_key="fire_service", static_kwargs={"state_code": "wa"}),
    "tas-tfs-fire": PipelineBinding(adapter_key="fire_service", static_kwargs={"state_code": "tas"}),
    "act-esa-fire": PipelineBinding(adapter_key="fire_service", static_kwargs={"state_code": "act"}),
    "nt-pfes-fire": PipelineBinding(adapter_key="fire_service", static_kwargs={"state_code": "nt"}),
    "nsw-ses-flood": PipelineBinding(adapter_key="ses_flood", static_kwargs={"state_code": "nsw"}),
    "vic-ses-flood": PipelineBinding(adapter_key="ses_flood", static_kwargs={"state_code": "vic"}),
    "qld-ses-flood": PipelineBinding(adapter_key="ses_flood", static_kwargs={"state_code": "qld"}),
    "epa-air-quality": PipelineBinding(adapter_key="epa_air"),
    "sentinel-satellite": PipelineBinding(adapter_key="sentinel"),
    "himawari-satellite": PipelineBinding(adapter_key="himawari"),
    "twitter-disaster": PipelineBinding(adapter_key="twitter"),
    "facebook-community": PipelineBinding(adapter_key="facebook"),
    "reddit-australia": PipelineBinding(adapter_key="reddit"),
    "snap-send-solve": PipelineBinding(adapter_key="snap"),
    "webeoc-ims": PipelineBinding(adapter_key="ims_webeoc"),
    "icon-ims": PipelineBinding(adapter_key="ims_icon"),
}

_DEFAULT_SCHEMA_VALIDATOR: Draft202012Validator | None = None


def _default_schema_validator() -> Draft202012Validator:
    global _DEFAULT_SCHEMA_VALIDATOR
    if _DEFAULT_SCHEMA_VALIDATOR is None:
        schema_path = Path("packages/schemas/signal-envelope.schema.json")
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        _DEFAULT_SCHEMA_VALIDATOR = Draft202012Validator(schema=schema, format_checker=FormatChecker())
    return _DEFAULT_SCHEMA_VALIDATOR


def validate_pipeline_configs(configs: list[IngestionPipelineConfig]) -> PipelineValidationReport:
    errors: list[str] = []
    warnings: list[str] = []
    seen_pipeline_ids: set[str] = set()

    for config in configs:
        pipeline_id = str(config.pipeline_id).strip()

        if not pipeline_id:
            errors.append("pipeline_id cannot be empty")
            continue

        if config.enabled and pipeline_id in seen_pipeline_ids:
            errors.append(f"duplicate enabled pipeline_id: {pipeline_id}")
            continue

        if config.enabled:
            seen_pipeline_ids.add(pipeline_id)
            binding = _PIPELINE_BINDINGS.get(pipeline_id)
            if binding is None:
                errors.append(f"unregistered enabled pipeline_id: {pipeline_id}")
                continue

            spec = _ADAPTER_SPECS[binding.adapter_key]
            if config.source_class != spec.source_class:
                errors.append(
                    f"source_class mismatch for {pipeline_id}: configured={config.source_class} expected={spec.source_class}"  # noqa: E501
                )

            if config.endpoint_format not in spec.supported_formats:
                errors.append(
                    f"unsupported endpoint_format for {pipeline_id}: {config.endpoint_format} not in {sorted(spec.supported_formats)}"  # noqa: E501
                )

            if any(not str(data_source_id).strip() for data_source_id in config.data_source_ids):
                errors.append(f"{pipeline_id} has falsy data_source_id")
            elif len(set(config.data_source_ids)) != len(config.data_source_ids):
                errors.append(f"{pipeline_id} has duplicate data_source_ids")

        elif not config.activation_blocker:
            warnings.append(f"disabled pipeline {pipeline_id} has no activation_blocker")

    return PipelineValidationReport(errors=errors, warnings=warnings)


def create_pipeline(config: IngestionPipelineConfig, **extra_kwargs: Any) -> Any:
    """Instantiate a concrete pipeline from its config."""
    binding = _PIPELINE_BINDINGS.get(config.pipeline_id)
    if binding is None:
        raise ValueError(f"No pipeline class registered for {config.pipeline_id}")

    spec = _ADAPTER_SPECS[binding.adapter_key]
    if config.endpoint_format not in spec.supported_formats:
        raise ValueError(
            f"Unsupported endpoint_format {config.endpoint_format} for {config.pipeline_id}; "
            f"supported: {sorted(spec.supported_formats)}"
        )

    from importlib import import_module

    mod = import_module(spec.module_path)
    cls = getattr(mod, spec.class_name)

    kwargs: dict[str, Any] = {
        "circuit_breaker_threshold": config.circuit_breaker_threshold,
        "circuit_breaker_backoff_initial": config.circuit_breaker_backoff_initial_seconds,
        "circuit_breaker_backoff_max": config.circuit_breaker_backoff_max_seconds,
        "dedup_ttl_seconds": config.effective_dedup_ttl(),
        "scope": config.scope,
        **binding.static_kwargs,
        **extra_kwargs,
    }

    if "schema_validator" not in kwargs and "schema" not in kwargs:
        kwargs["schema_validator"] = _default_schema_validator()

    if config.endpoint_url and binding.endpoint_kwarg:
        init_signature = inspect.signature(cls.__init__)
        if binding.endpoint_kwarg in init_signature.parameters:
            kwargs[binding.endpoint_kwarg] = config.endpoint_url

    pipeline = cls(**kwargs)
    pipeline.pipeline_id = config.pipeline_id
    pipeline.data_source_ids = list(config.data_source_ids)
    pipeline.poll_interval_seconds = int(config.poll_interval_seconds)
    pipeline.expected_update_seconds = int(config.poll_interval_seconds)
    pipeline.dedup_ttl_seconds = config.effective_dedup_ttl()
    pipeline.source_class = str(config.source_class)
    pipeline.endpoint_format = config.endpoint_format
    pipeline.config_identity = config.pipeline_id
    pipeline.max_records_per_cycle = int(config.max_records_per_cycle)
    return pipeline
