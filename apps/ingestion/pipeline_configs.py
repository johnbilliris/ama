"""Default pipeline configurations for all 20+ ingestion pipeline instances."""

from apps.ingestion.pipeline_config import IngestionPipelineConfig

PIPELINE_CONFIGS: list[IngestionPipelineConfig] = [
    # --- BoM authoritative (FTP-based, event-driven warnings) ---
    IngestionPipelineConfig(
        pipeline_id="bom-warnings",
        source_class="authoritative",
        data_source_ids=["bom-warnings"],
        poll_interval_seconds=120,  # event-driven; FTP files persist 8h+
        endpoint_url="ftp://ftp.bom.gov.au/anon/gen/fwo/",
        endpoint_format="xml_bom",
        dedup_ttl_seconds=28800,  # 8h — match FTP file retention
    ),
    IngestionPipelineConfig(
        pipeline_id="bom-forecasts",
        source_class="authoritative",
        data_source_ids=["bom-forecasts"],
        poll_interval_seconds=1800,  # published hourly; poll every 30min
        endpoint_url="ftp://ftp.bom.gov.au/anon/gen/fwo/",
        endpoint_format="xml_bom",
        dedup_ttl_seconds=7200,  # 2h
    ),
    IngestionPipelineConfig(
        pipeline_id="bom-observations-nsw",
        source_class="sensor",
        data_source_ids=["bom-observations"],
        poll_interval_seconds=600,  # published ~10min; poll every 10min
        endpoint_url="http://www.bom.gov.au/fwo/IDN60901/IDN60901.94768.json",
        endpoint_format="json",
        dedup_ttl_seconds=1200,  # 20min
    ),
    IngestionPipelineConfig(
        pipeline_id="bom-radar",
        source_class="satellite",
        data_source_ids=["bom-radar"],
        poll_interval_seconds=300,  # published every 5min; poll matches
        endpoint_url="ftp://ftp.bom.gov.au/anon/gen/radar/",
        endpoint_format="png",
        dedup_ttl_seconds=600,  # 10min
    ),
    IngestionPipelineConfig(
        pipeline_id="bom-flood-warnings",
        source_class="authoritative",
        data_source_ids=["bom-flood-warnings"],
        poll_interval_seconds=120,
        endpoint_url="ftp://ftp.bom.gov.au/anon/gen/fwo/",
        endpoint_format="cap_xml",
        dedup_ttl_seconds=28800,
        enabled=False,  # bom-warnings already ingests all XML from the same FTP path
        activation_blocker="Handled by bom-warnings FTP pipeline until dedicated CAP split is approved",
    ),
    IngestionPipelineConfig(
        pipeline_id="bom-rss",
        source_class="authoritative",
        data_source_ids=["bom-warnings"],
        poll_interval_seconds=120,  # event-driven; same as bom-warnings
        endpoint_url="ftp://ftp.bom.gov.au/anon/gen/fwo/",
        endpoint_format="rss",
        dedup_ttl_seconds=28800,  # 8h
        enabled=False,
        activation_blocker="RSS/Atom notification path is not implemented; FTP replacement requires approved deviation evidence",  # noqa: E501
    ),
    # --- Geoscience Australia ---
    IngestionPipelineConfig(
        pipeline_id="ga-earthquakes",
        source_class="authoritative",
        data_source_ids=["ga-earthquake-alerts"],
        poll_interval_seconds=300,  # USGS feed updates ~5min
        endpoint_url="https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson",
        endpoint_format="geojson",
        dedup_ttl_seconds=86400,  # 24h — day feed
    ),
    IngestionPipelineConfig(
        pipeline_id="ga-tsunami",
        source_class="authoritative",
        data_source_ids=["ga-tsunami-warnings"],
        poll_interval_seconds=120,  # event-driven; poll every 2min
        endpoint_url="ftp://ftp.bom.gov.au/anon/gen/fwo/",
        endpoint_format="cap_xml",
        dedup_ttl_seconds=28800,  # 8h
    ),
    IngestionPipelineConfig(
        pipeline_id="ga-hotspots",
        source_class="authoritative",
        data_source_ids=["ga-sentinel-hotspots"],
        poll_interval_seconds=3600,  # published hourly; poll matches
        endpoint_url="https://hotspots.dea.ga.gov.au/data/recent-hotspots.json",
        endpoint_format="geojson",
        dedup_ttl_seconds=7200,  # 2h
    ),
    # --- State fire services ---
    IngestionPipelineConfig(
        pipeline_id="nsw-rfs-fire",
        source_class="authoritative",
        data_source_ids=["nsw-rfs-fires-near-me"],
        poll_interval_seconds=300,  # published ~5min; poll matches
        endpoint_url="https://www.rfs.nsw.gov.au/feeds/majorIncidents.json",
        endpoint_format="geojson",
        dedup_ttl_seconds=600,  # 10min
    ),
    IngestionPipelineConfig(
        pipeline_id="vic-cfa-fire",
        source_class="authoritative",
        data_source_ids=["vic-cfa"],
        poll_interval_seconds=300,  # published ~5min
        endpoint_url="https://www.emergency.vic.gov.au/public/osom-geojson.json",
        endpoint_format="geojson",
        dedup_ttl_seconds=600,  # 10min
    ),
    IngestionPipelineConfig(
        pipeline_id="qld-qfes-fire",
        source_class="authoritative",
        data_source_ids=["qld-qfes"],
        poll_interval_seconds=300,
        endpoint_url="https://www.fire.qld.gov.au/current-incidents",
        endpoint_format="geojson",
        dedup_ttl_seconds=600,
        enabled=False,  # QLD QFES endpoint returns HTML (JS app), no public JSON feed
        activation_blocker="Public QLD endpoint is HTML application content; machine-readable incident feed contract not evidenced in-repo",  # noqa: E501
    ),
    IngestionPipelineConfig(
        pipeline_id="sa-cfs-fire",
        source_class="authoritative",
        data_source_ids=["sa-cfs"],
        poll_interval_seconds=300,
        endpoint_url="https://data.cfs.sa.gov.au/incidents.json",
        endpoint_format="geojson",
        dedup_ttl_seconds=600,
        enabled=False,
        activation_blocker="Endpoint ownership, auth/access, license, and rate-limit evidence are not verified in-repo",
    ),
    IngestionPipelineConfig(
        pipeline_id="wa-dfes-fire",
        source_class="authoritative",
        data_source_ids=["wa-dfes"],
        poll_interval_seconds=300,
        endpoint_url="https://www.dfes.wa.gov.au/data/incidents.json",
        endpoint_format="geojson",
        dedup_ttl_seconds=600,
        enabled=False,
        activation_blocker="Endpoint ownership, auth/access, license, and rate-limit evidence are not verified in-repo",
    ),
    IngestionPipelineConfig(
        pipeline_id="tas-tfs-fire",
        source_class="authoritative",
        data_source_ids=["tas-tfs"],
        poll_interval_seconds=300,
        endpoint_url="https://www.fire.tas.gov.au/data/incidents.json",
        endpoint_format="geojson",
        dedup_ttl_seconds=600,
        enabled=False,
        activation_blocker="Endpoint ownership, auth/access, license, and rate-limit evidence are not verified in-repo",
    ),
    IngestionPipelineConfig(
        pipeline_id="act-esa-fire",
        source_class="authoritative",
        data_source_ids=["act-esa"],
        poll_interval_seconds=300,
        endpoint_url="https://www.esa.act.gov.au/data/incidents.json",
        endpoint_format="geojson",
        dedup_ttl_seconds=600,
        enabled=False,
        activation_blocker="Endpoint ownership, auth/access, license, and rate-limit evidence are not verified in-repo",
    ),
    IngestionPipelineConfig(
        pipeline_id="nt-pfes-fire",
        source_class="authoritative",
        data_source_ids=["nt-pfes"],
        poll_interval_seconds=300,
        endpoint_url="https://www.pfes.nt.gov.au/data/incidents.json",
        endpoint_format="geojson",
        dedup_ttl_seconds=600,
        enabled=False,
        activation_blocker="Endpoint ownership, auth/access, license, and rate-limit evidence are not verified in-repo",
    ),
    IngestionPipelineConfig(
        pipeline_id="nsw-ses-flood",
        source_class="authoritative",
        data_source_ids=["nsw-ses-flood"],
        poll_interval_seconds=300,
        endpoint_url="https://www.ses.nsw.gov.au/api/flood/current",
        endpoint_format="geojson",
        dedup_ttl_seconds=600,
        enabled=False,
        activation_blocker="NSW SES machine-readable flood endpoint availability and contractual access are not verified in-repo",  # noqa: E501
    ),
    IngestionPipelineConfig(
        pipeline_id="vic-ses-flood",
        source_class="authoritative",
        data_source_ids=["vic-ses-flood"],
        poll_interval_seconds=300,
        endpoint_url="https://www.ses.vic.gov.au/data/flood-incidents.json",
        endpoint_format="geojson",
        dedup_ttl_seconds=600,
        enabled=False,
        activation_blocker="Endpoint ownership, auth/access, license, and rate-limit evidence are not verified in-repo",
    ),
    IngestionPipelineConfig(
        pipeline_id="qld-ses-flood",
        source_class="authoritative",
        data_source_ids=["qld-ses-flood"],
        poll_interval_seconds=300,
        endpoint_url="https://www.ses.qld.gov.au/data/flood-incidents.json",
        endpoint_format="geojson",
        dedup_ttl_seconds=600,
        enabled=False,
        activation_blocker="Endpoint ownership, auth/access, license, and rate-limit evidence are not verified in-repo",
    ),
    # --- Sensors ---
    IngestionPipelineConfig(
        pipeline_id="bom-aws-stations",
        source_class="sensor",
        data_source_ids=["bom-aws-stations"],
        poll_interval_seconds=300,  # published every 5min; poll matches
        endpoint_url="http://www.bom.gov.au/fwo/IDN60901/IDN60901.94767.json",
        endpoint_format="json",
        dedup_ttl_seconds=600,  # 10min
    ),
    IngestionPipelineConfig(
        pipeline_id="bom-river-gauges",
        source_class="sensor",
        data_source_ids=["bom-river-gauges"],
        poll_interval_seconds=900,  # published ~15min; poll every 15min
        endpoint_url="http://www.bom.gov.au/waterdata/services",
        endpoint_format="json",
        dedup_ttl_seconds=1800,  # 30min
    ),
    IngestionPipelineConfig(
        pipeline_id="epa-air-quality",
        source_class="sensor",
        data_source_ids=["epa-air-quality"],
        poll_interval_seconds=3600,  # published hourly; poll matches
        endpoint_url="https://data.airquality.nsw.gov.au/api/Data/get_Observations",
        endpoint_format="json",
        dedup_ttl_seconds=7200,  # 2h
    ),
    # --- Satellite ---
    IngestionPipelineConfig(
        pipeline_id="sentinel-satellite",
        source_class="satellite",
        data_source_ids=["sentinel-satellite"],
        poll_interval_seconds=21600,  # published daily; poll every 6h
        endpoint_url="https://dataspace.copernicus.eu/",
        endpoint_format="geotiff",
        dedup_ttl_seconds=86400,  # 24h
        enabled=False,  # Copernicus Data Space requires OAuth2 registration
        activation_blocker="Copernicus Data Space OAuth2 registration not configured for runtime",
    ),
    IngestionPipelineConfig(
        pipeline_id="himawari-satellite",
        source_class="satellite",
        data_source_ids=["himawari-satellite"],
        poll_interval_seconds=600,  # published every 10min; poll matches
        endpoint_url="ftp://ftp.bom.gov.au/anon/gen/gms/",
        endpoint_format="geotiff",
        dedup_ttl_seconds=1200,  # 20min
    ),
    # --- Social (stubs — require API keys / OAuth, disabled until configured) ---
    IngestionPipelineConfig(
        pipeline_id="twitter-disaster",
        source_class="social",
        data_source_ids=["twitter-disaster"],
        poll_interval_seconds=60,
        endpoint_url="https://api.twitter.com/2/tweets/search/stream",
        endpoint_format="json",
        dedup_ttl_seconds=3600,
        enabled=False,  # Requires OAuth2 bearer token
        activation_blocker="X API OAuth2 bearer credentials and access tier approval are required",
    ),
    IngestionPipelineConfig(
        pipeline_id="facebook-community",
        source_class="social",
        data_source_ids=["facebook-community"],
        poll_interval_seconds=300,
        endpoint_url="https://graph.facebook.com/v19.0/",
        endpoint_format="json",
        dedup_ttl_seconds=3600,
        enabled=False,  # Requires Graph API access token
        activation_blocker="Meta Graph API token/app review approval is required",
    ),
    IngestionPipelineConfig(
        pipeline_id="reddit-australia",
        source_class="social",
        data_source_ids=["reddit-australia"],
        poll_interval_seconds=120,
        endpoint_url="https://www.reddit.com/r/australia.json",
        endpoint_format="json",
        dedup_ttl_seconds=3600,
        enabled=False,  # Reddit blocks automated access (403)
        activation_blocker="Reddit API client credentials and approved rate-limit policy are required",
    ),
    # --- Community (requires API key, disabled until configured) ---
    IngestionPipelineConfig(
        pipeline_id="snap-send-solve",
        source_class="community",
        data_source_ids=["snap-send-solve"],
        poll_interval_seconds=300,
        endpoint_url="https://api.snapsendsolve.com/v1/reports",
        endpoint_format="json",
        dedup_ttl_seconds=3600,
        enabled=False,  # Requires API key
        activation_blocker="Snap Send Solve partner API key and agreement are required",
    ),
    # --- IMS (placeholder — requires org-specific endpoints) ---
    IngestionPipelineConfig(
        pipeline_id="webeoc-ims",
        source_class="ims",
        data_source_ids=["webeoc-ims"],
        poll_interval_seconds=120,
        endpoint_url="https://webeoc.example.com/api/boards",
        endpoint_format="json",
        dedup_ttl_seconds=600,
        enabled=False,  # Placeholder — requires org-specific WebEOC instance URL
        activation_blocker="WebEOC endpoint and credentials are tenant-specific and not yet provisioned",
    ),
    IngestionPipelineConfig(
        pipeline_id="icon-ims",
        source_class="ims",
        data_source_ids=["icon-ims"],
        poll_interval_seconds=120,
        endpoint_url="https://icon.example.com/api/incidents",
        endpoint_format="json",
        dedup_ttl_seconds=600,
        enabled=False,  # Placeholder — requires org-specific ICON instance URL
        activation_blocker="ICON endpoint and credentials are tenant-specific and not yet provisioned",
    ),
]

