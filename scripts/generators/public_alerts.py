"""Spec-039 T115 — public alerts generator (FR-050, FR-070)."""

from __future__ import annotations

from typing import Any

from scripts.generators._generator_base import make_rng, run_cli, tag_record

GENERATOR_ID = "public_alerts"
GENERATOR_VERSION = "1.0.0"

# FR-070 6 MUST locales + accessibility-placeholder rows (A-9, A-10).
_LOCALES = ("en-AU", "ar", "el", "it", "vi", "zh-Hans",
            "indigenous-placeholder", "auslan-placeholder")
_TEMPLATES = ("bushfire-warning", "flood-evac", "cyclone-watch",
              "earthquake-aftershock", "heatwave-advisory")


def generate(seed: int, count: int) -> list[dict[str, Any]]:
    rng = make_rng(GENERATOR_ID, seed)
    out: list[dict[str, Any]] = []
    # Ensure at least 5 alert variants per locale (FR-070, SC-014) by sweeping.
    sweep = max(count, len(_LOCALES) * 5)
    for i in range(sweep):
        locale = _LOCALES[i % len(_LOCALES)]
        template = _TEMPLATES[(i // len(_LOCALES)) % len(_TEMPLATES)]
        body = {
            "template_id": template,
            "locale": locale,
            "audience": rng.choice(["public", "responders", "vulnerable-cohort"]),
            "channel": rng.choice(["broadcast", "sms", "social", "wireless-emergency"]),
            "headline": f"FICTITIOUS {template} ({locale}) — TEST — DO NOT BROADCAST",
            "body": "TEST — DO NOT BROADCAST: synthetic alert payload",
            "wcag_audio_description": "placeholder",
        }
        out.append(tag_record(
            body, generator_id=GENERATOR_ID, generator_version=GENERATOR_VERSION,
            record_id=f"alert-{template}-{locale}-{i:04d}",
        ))
    return out


def main(argv: list[str] | None = None) -> int:
    return run_cli(GENERATOR_ID, GENERATOR_VERSION, generate, default_count=40, argv=argv)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
