from typing import Any

BUSHFIRE_TEMPLATE: dict[str, Any] = {
    "name": "bushfire",
    "description": "Multi-phase bushfire scenario from detection through de-escalation",
    "phases": [
        {
            "name": "detection",
            "duration_seconds": 300,
            "sources": ["ga-sentinel-hotspots", "bom-warnings", "twitter-disaster"],
            "params": {"severity": "low", "alert_level": "Advice"},
        },
        {
            "name": "escalation",
            "duration_seconds": 600,
            "sources": ["nsw-rfs-fires-near-me", "bom-warnings", "epa-air-quality", "twitter-disaster"],
            "params": {"severity": "moderate", "alert_level": "Watch and Act"},
        },
        {
            "name": "peak",
            "duration_seconds": 900,
            "sources": [
                "nsw-rfs-fires-near-me",
                "bom-warnings",
                "epa-air-quality",
                "ga-sentinel-hotspots",
                "twitter-disaster",
            ],
            "params": {"severity": "extreme", "alert_level": "Emergency Warning"},
        },
        {
            "name": "de-escalation",
            "duration_seconds": 600,
            "sources": ["nsw-rfs-fires-near-me", "bom-warnings", "epa-air-quality"],
            "params": {"severity": "low", "alert_level": "Advice"},
        },
    ],
    "activated_sources": [
        "bom-warnings",
        "ga-sentinel-hotspots",
        "nsw-rfs-fires-near-me",
        "epa-air-quality",
        "twitter-disaster",
    ],
}

FLOOD_TEMPLATE: dict[str, Any] = {
    "name": "flood",
    "description": "Multi-phase flood scenario from warning through recession",
    "phases": [
        {
            "name": "warning",
            "duration_seconds": 600,
            "sources": ["bom-warnings", "bom-flood-warnings", "bom-river-gauges"],
            "params": {"severity": "minor", "water_level": 2.0},
        },
        {
            "name": "minor_flood",
            "duration_seconds": 600,
            "sources": ["bom-warnings", "bom-flood-warnings", "bom-river-gauges", "nsw-ses-flood"],
            "params": {"severity": "minor", "water_level": 4.0},
        },
        {
            "name": "major_flood",
            "duration_seconds": 900,
            "sources": ["bom-warnings", "bom-flood-warnings", "bom-river-gauges", "nsw-ses-flood", "twitter-disaster"],
            "params": {"severity": "major", "water_level": 7.0},
        },
        {
            "name": "peak",
            "duration_seconds": 600,
            "sources": ["bom-warnings", "bom-river-gauges", "nsw-ses-flood", "twitter-disaster"],
            "params": {"severity": "extreme", "water_level": 9.5},
        },
        {
            "name": "recession",
            "duration_seconds": 900,
            "sources": ["bom-river-gauges", "nsw-ses-flood"],
            "params": {"severity": "moderate", "water_level": 5.0},
        },
    ],
    "activated_sources": [
        "bom-warnings",
        "bom-flood-warnings",
        "bom-river-gauges",
        "nsw-ses-flood",
        "twitter-disaster",
    ],
}

CYCLONE_TEMPLATE: dict[str, Any] = {
    "name": "cyclone",
    "description": "Tropical cyclone scenario from watch through aftermath",
    "phases": [
        {
            "name": "watch",
            "duration_seconds": 600,
            "sources": ["bom-warnings", "himawari-satellite"],
            "params": {"severity": "watch", "category": 1, "wind_speed": 90},
        },
        {
            "name": "warning",
            "duration_seconds": 600,
            "sources": ["bom-warnings", "himawari-satellite", "bom-river-gauges", "twitter-disaster"],
            "params": {"severity": "warning", "category": 2, "wind_speed": 130},
        },
        {
            "name": "landfall",
            "duration_seconds": 900,
            "sources": ["bom-warnings", "himawari-satellite", "bom-river-gauges", "twitter-disaster"],
            "params": {"severity": "extreme", "category": 3, "wind_speed": 180},
        },
        {
            "name": "aftermath",
            "duration_seconds": 600,
            "sources": ["bom-warnings", "bom-river-gauges", "twitter-disaster"],
            "params": {"severity": "moderate", "category": 1, "wind_speed": 70},
        },
    ],
    "activated_sources": [
        "bom-warnings",
        "himawari-satellite",
        "bom-river-gauges",
        "twitter-disaster",
    ],
}

SEVERE_STORM_TEMPLATE: dict[str, Any] = {
    "name": "severe_storm",
    "description": "Severe thunderstorm scenario from warning through aftermath",
    "phases": [
        {
            "name": "warning",
            "duration_seconds": 300,
            "sources": ["bom-warnings", "bom-radar", "bom-observations"],
            "params": {"severity": "warning"},
        },
        {
            "name": "active",
            "duration_seconds": 600,
            "sources": ["bom-warnings", "bom-radar", "bom-observations", "twitter-disaster"],
            "params": {"severity": "severe"},
        },
        {
            "name": "aftermath",
            "duration_seconds": 300,
            "sources": ["bom-observations", "twitter-disaster"],
            "params": {"severity": "moderate"},
        },
    ],
    "activated_sources": [
        "bom-warnings",
        "bom-radar",
        "bom-observations",
        "twitter-disaster",
    ],
}

SCENARIO_TEMPLATES: dict[str, dict[str, Any]] = {
    "bushfire": BUSHFIRE_TEMPLATE,
    "flood": FLOOD_TEMPLATE,
    "cyclone": CYCLONE_TEMPLATE,
    "severe_storm": SEVERE_STORM_TEMPLATE,
}
