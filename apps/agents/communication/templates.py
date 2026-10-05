"""Template loader and fallback text generators for multilingual alert templates.

Loads pre-approved JSON template files from ``data/alert-templates/{language_code}.json``
at startup. Templates use ``{placeholder}`` syntax for dynamic values.

Per CHK005: placeholders are sanitised before interpolation.
Per CHK006: missing placeholder values are replaced with ``[unknown]``.
Per CHK008: missing template file for a language falls back to en-AU with
``[Translation unavailable]`` suffix.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import NotRequired, TypedDict

logger = logging.getLogger(__name__)

_PLACEHOLDER_RE = re.compile(r"\{(\w+)\}")

# Default template directory relative to repo root
# __file__ is communication/templates.py → parents[3] is the repo root (ama/)
_DEFAULT_TEMPLATE_DIR = Path(__file__).resolve().parents[3] / "data" / "alert-templates"
_REQUIRED_LANGUAGES = ("en-AU", "zh-Hans", "ar", "vi", "el", "it")
_REQUIRED_HAZARDS = ("bushfire", "flood", "cyclone", "storm", "earthquake", "tsunami", "general")
_REQUIRED_ALERT_TYPES = ("evacuation", "shelter_in_place", "general_warning", "all_clear")
_FALLBACK_ALIAS = {
    "evacuation": ("general", "evacuation", "severe"),
    "shelter_in_place": ("general", "shelter_in_place", "severe"),
    "general_warning": ("general", "general_warning", "moderate"),
    "all_clear": ("general", "all_clear", "severe"),
}


class AlertTemplate(TypedDict):
    template_id: str
    hazard_type: str
    severity: str
    alert_type: str
    language_code: str
    title_template: str
    body_template: str
    action_items_template: str
    _operational_fallback: NotRequired[bool]
    _translation_unavailable: NotRequired[bool]


class TemplateLoader:
    """Loads and interpolates pre-approved alert templates."""

    def __init__(self, template_dir: str | Path | None = None) -> None:
        self._template_dir = Path(template_dir) if template_dir else _DEFAULT_TEMPLATE_DIR
        self._templates: dict[str, list[AlertTemplate]] = {}
        self._load_all()

    def _load_all(self) -> None:
        """Load all template files at startup. Fail-fast on malformed JSON."""
        if not self._template_dir.exists():
            raise FileNotFoundError(f"Template directory does not exist: {self._template_dir}")

        json_files = list(self._template_dir.glob("*.json"))
        if not json_files:
            raise FileNotFoundError(f"No template files found in: {self._template_dir}")

        for file_path in json_files:
            lang_code = file_path.stem  # e.g., "en-AU" from "en-AU.json"
            try:
                with open(file_path, encoding="utf-8") as f:
                    templates = json.load(f)
                if not isinstance(templates, list):
                    raise ValueError(f"Expected JSON array in {file_path}")
                self._templates[lang_code] = templates
                logger.info("Loaded %d templates for language %s", len(templates), lang_code)
            except (json.JSONDecodeError, ValueError) as exc:
                raise ValueError(f"Malformed template file {file_path}: {exc}") from exc

        # en-AU must exist
        if "en-AU" not in self._templates:
            raise FileNotFoundError("Required en-AU template file is missing")
        missing_languages = sorted(set(_REQUIRED_LANGUAGES) - set(self._templates))
        if missing_languages:
            raise FileNotFoundError(f"Required template languages are missing: {', '.join(missing_languages)}")
        self._validate_operational_matrix()

    def _validate_operational_matrix(self) -> None:
        required_fields = {
            "template_id",
            "hazard_type",
            "severity",
            "alert_type",
            "language_code",
            "title_template",
            "body_template",
            "action_items_template",
        }
        for language, templates in self._templates.items():
            for template in templates:
                missing_fields = required_fields - set(template)
                if missing_fields:
                    raise ValueError(
                        f"Template {template.get('template_id', '<unknown>')} in {language} is missing "
                        f"{', '.join(sorted(missing_fields))}"
                    )
            combinations = {(item["hazard_type"], item["alert_type"]) for item in templates}
            for hazard in _REQUIRED_HAZARDS:
                for alert_type in _REQUIRED_ALERT_TYPES:
                    if (hazard, alert_type) in combinations:
                        continue
                    alias_hazard, alias_type, alias_severity = _FALLBACK_ALIAS[alert_type]
                    if not any(
                        item["hazard_type"] == alias_hazard
                        and item["alert_type"] == alias_type
                        and item["severity"] == alias_severity
                        for item in templates
                    ):
                        raise ValueError(
                            f"No approved template or operational fallback for {language}/{hazard}/{alert_type}"
                        )

    def get_template(
        self,
        hazard_type: str,
        severity: str,
        alert_type: str,
        language_code: str,
    ) -> AlertTemplate | None:
        """Find a matching template for the given criteria.

        Returns None if no exact match found.
        """
        templates = self._templates.get(language_code, [])
        template = self._find_template(templates, hazard_type, severity, alert_type)
        if template is not None:
            return template

        alias_hazard, alias_type, alias_severity = _FALLBACK_ALIAS.get(
            alert_type,
            ("general", "general_warning", "moderate"),
        )
        template = self._find_template(templates, alias_hazard, alias_severity, alias_type)
        if template is not None:
            fallback: AlertTemplate = {**template, "_operational_fallback": True}
            return fallback

        # Try en-AU fallback per CHK008 if language not found
        if language_code != "en-AU":
            logger.warning(
                "No template for %s/%s/%s in %s, falling back to en-AU (CHK008)",
                hazard_type,
                severity,
                alert_type,
                language_code,
            )
            return self._get_en_au_fallback(hazard_type, severity, alert_type)

        return None

    def _get_en_au_fallback(self, hazard_type: str, severity: str, alert_type: str) -> AlertTemplate | None:
        """Get en-AU template as fallback with [Translation unavailable] suffix."""
        for tmpl in self._templates.get("en-AU", []):
            if (
                tmpl.get("hazard_type") == hazard_type
                and tmpl.get("severity") == severity
                and tmpl.get("alert_type") == alert_type
            ):
                # Return a copy with [Translation unavailable] annotation
                fallback: AlertTemplate = {**tmpl, "_translation_unavailable": True}
                return fallback
        return None

    @staticmethod
    def _find_template(
        templates: list[AlertTemplate],
        hazard_type: str,
        severity: str,
        alert_type: str,
    ) -> AlertTemplate | None:
        exact = next(
            (
                template
                for template in templates
                if template.get("hazard_type") == hazard_type
                and template.get("severity") == severity
                and template.get("alert_type") == alert_type
            ),
            None,
        )
        if exact is not None:
            return exact
        return next(
            (
                template
                for template in templates
                if template.get("hazard_type") == hazard_type and template.get("alert_type") == alert_type
            ),
            None,
        )

    @staticmethod
    def interpolate(template_text: str, values: dict[str, str]) -> str:
        """Substitute ``{placeholder}`` values with sanitisation per CHK005.

        Missing placeholder values are replaced with ``[unknown]`` per CHK006.
        """

        def _replace(match: re.Match[str]) -> str:
            key = match.group(1)
            value = values.get(key)
            if value is None:
                logger.warning("Missing placeholder value for '{%s}', using [unknown]", key)
                return "[unknown]"
            # Sanitise per CHK005 — strip control characters and HTML
            sanitised = re.sub(r"[<>&]", "", str(value))
            sanitised = re.sub(r"[\x00-\x1f]", "", sanitised)
            return sanitised

        return _PLACEHOLDER_RE.sub(_replace, template_text)

    def get_template_text(
        self,
        hazard_type: str,
        severity: str,
        alert_type: str,
        language_code: str,
        values: dict[str, str],
    ) -> tuple[str, str, str, bool]:
        """Convenience method: find template and interpolate.

        Returns (title, body, action_items, translation_unavailable).
        """
        tmpl = self.get_template(hazard_type, severity, alert_type, language_code)
        if tmpl is None:
            # Ultimate fallback — generic warning
            return (
                f"EMERGENCY ALERT — {values.get('location', '[unknown]')}",
                "An emergency situation exists. Follow emergency services directions.",
                "Call 000 for emergencies.",
                language_code != "en-AU",
            )

        translation_unavailable = tmpl.get("_translation_unavailable", False)
        title = self.interpolate(tmpl.get("title_template", ""), values)
        body = self.interpolate(tmpl.get("body_template", ""), values)
        action_items = self.interpolate(tmpl.get("action_items_template", ""), values)

        if translation_unavailable:
            title += " [Translation unavailable]"
        if tmpl.get("_operational_fallback"):
            title += " [Hazard-specific template unavailable]"

        return title, body, action_items, translation_unavailable

    @property
    def loaded_languages(self) -> list[str]:
        """Return list of languages with loaded templates."""
        return list(self._templates.keys())

    def has_language(self, language_code: str) -> bool:
        """Check if templates are loaded for a specific language."""
        return language_code in self._templates

    def has_operational_template(self, hazard_type: str, alert_type: str, language_code: str) -> bool:
        return self.get_template(hazard_type, "severe", alert_type, language_code) is not None
