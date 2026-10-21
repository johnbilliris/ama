from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

ScenarioId = Literal[
    "bushfire",
    "flood",
    "cyclone",
    "urban_fire",
    "mass_casualty",
    "hazmat",
    "marine_sar",
]
Provenance = Literal["auto", "manual"]

SCENARIO_ALIASES = {
    "urban-fire": "urban_fire",
    "mass-casualty": "mass_casualty",
    "marine-sar": "marine_sar",
}
MANDATORY_AUSLAN_SCENARIOS = frozenset({"cyclone", "bushfire", "flood"})
LANGUAGE_CHANNELS = (
    "en-AU",
    "zh-Hans",
    "ar",
    "vi",
    "yue",
    "pa",
    "auslan",
    "yolngu_matha",
)

_ENGLISH_CONTENT: dict[ScenarioId, str] = {
    "bushfire": (
        "Bushfire exercise. Watch official warnings. Leave early if emergency services tell you to go. "
        "If a life is in danger, call Triple Zero (000)."
    ),
    "flood": (
        "Flood exercise. Never walk, ride, or drive through floodwater. Follow official evacuation advice. "
        "If a life is in danger, call Triple Zero (000)."
    ),
    "cyclone": (
        "Cyclone exercise. Follow official warnings. Shelter or leave when emergency services tell you. "
        "If a life is in danger, call Triple Zero (000)."
    ),
    "urban_fire": (
        "Urban fire exercise. Move away from smoke and fire. Leave the area when emergency services tell you. "
        "If a life is in danger, call Triple Zero (000)."
    ),
    "mass_casualty": (
        "Emergency exercise. Keep roads and access points clear for responders. Follow official safety advice. "
        "If a life is in danger, call Triple Zero (000)."
    ),
    "hazmat": (
        "Hazardous materials exercise. Stay away from the affected area. Follow official shelter or evacuation advice. "
        "If a life is in danger, call Triple Zero (000)."
    ),
    "marine_sar": (
        "Marine rescue exercise. Follow official maritime safety advice and keep rescue routes clear. "
        "If a life is in danger, call Triple Zero (000)."
    ),
}

_TRANSLATED_SAFETY_TEXT = {
    "zh-Hans": "这是一次应急演练。请关注官方紧急服务通知。如果生命受到威胁，请拨打 000。",
    "ar": "هذا تمرين للطوارئ. اتبع تعليمات خدمات الطوارئ الرسمية. إذا كانت الحياة في خطر، اتصل بالرقم 000.",
    "vi": "Đây là một cuộc diễn tập khẩn cấp. Hãy làm theo thông báo chính thức. Nếu tính mạng bị đe dọa, hãy gọi 000.",
    "yue": "呢個係緊急事故演習。請留意緊急服務部門嘅官方通知。如生命有危險，請致電 000。",
    "pa": "ਇਹ ਐਮਰਜੈਂਸੀ ਅਭਿਆਸ ਹੈ। ਸਰਕਾਰੀ ਐਮਰਜੈਂਸੀ ਹਦਾਇਤਾਂ ਦੀ ਪਾਲਣਾ ਕਰੋ। ਜੇ ਜਾਨ ਨੂੰ ਖ਼ਤਰਾ ਹੋਵੇ ਤਾਂ 000 ਤੇ ਕਾਲ ਕਰੋ।",
}


class PublicInformationChannel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    language_code: str = Field(min_length=2, max_length=32)
    body: str = Field(min_length=1, max_length=2000)
    fk_grade: float | None = None
    provenance: Provenance = "auto"
    language_fallback_used: str | None = Field(
        default=None,
        pattern=r"^[A-Za-z_-]+→[A-Za-z-]+$",
    )


class AuslanAsset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    captioned_image_url: str
    transcript: str = Field(min_length=1)


class PublicInformationRender(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario_id: ScenarioId
    generated_at: AwareDatetime
    channels: list[PublicInformationChannel] = Field(min_length=8, max_length=8)
    auslan: AuslanAsset | None = None
    auslan_asset_missing: bool = False
    advisory_only: bool = True

    @model_validator(mode="after")
    def validate_auslan_state(self) -> PublicInformationRender:
        requires_asset = self.scenario_id in MANDATORY_AUSLAN_SCENARIOS
        if requires_asset and (self.auslan is None or self.auslan_asset_missing):
            raise ValueError("mandatory Auslan scenarios require a transcript asset")
        if not requires_asset and self.auslan is None and not self.auslan_asset_missing:
            raise ValueError("missing optional Auslan media must be disclosed")
        return self


def canonical_scenario_id(scenario_id: str) -> ScenarioId:
    candidate = SCENARIO_ALIASES.get(scenario_id, scenario_id)
    if candidate not in _ENGLISH_CONTENT:
        raise ValueError(f"unknown scenario_id={scenario_id}")
    return candidate


def render_public_information(
    scenario_id: str,
    *,
    requested_language: str = "en-AU",
) -> PublicInformationRender:
    canonical_id = canonical_scenario_id(scenario_id)
    english = _ENGLISH_CONTENT[canonical_id]
    channels = [
        PublicInformationChannel(
            language_code="en-AU",
            body=english,
            fk_grade=flesch_kincaid_grade(english),
        ),
        *(
            PublicInformationChannel(
                language_code=language_code,
                body=body,
            )
            for language_code, body in _TRANSLATED_SAFETY_TEXT.items()
        ),
        PublicInformationChannel(
            language_code="auslan",
            body=english,
            provenance="manual",
        ),
        PublicInformationChannel(
            language_code="yolngu_matha",
            body=english,
            provenance="manual",
            language_fallback_used="yolngu_matha→en-AU",
        ),
    ]

    if requested_language not in LANGUAGE_CHANNELS:
        channels[0] = channels[0].model_copy(update={"language_fallback_used": f"{requested_language}→en-AU"})

    if canonical_id in MANDATORY_AUSLAN_SCENARIOS:
        auslan = AuslanAsset(
            captioned_image_url=f"/evidence/auslan/{canonical_id}.svg",
            transcript=english,
        )
        missing = False
    else:
        auslan = None
        missing = True

    return PublicInformationRender(
        scenario_id=canonical_id,
        generated_at=datetime.now(UTC),
        channels=channels,
        auslan=auslan,
        auslan_asset_missing=missing,
    )


def flesch_kincaid_grade(text: str) -> float:
    words = re.findall(r"[A-Za-z]+", text)
    sentences = max(1, len(re.findall(r"[.!?]+", text)))
    syllables = sum(_count_syllables(word) for word in words)
    grade = 0.39 * (len(words) / sentences) + 11.8 * (syllables / max(1, len(words))) - 15.59
    return round(max(0.0, grade), 2)


def _count_syllables(word: str) -> int:
    cleaned = re.sub(r"[^a-z]", "", word.lower())
    if len(cleaned) <= 3:
        return 1
    without_silent_e = re.sub(r"e$", "", cleaned)
    return max(1, len(re.findall(r"[aeiouy]+", without_silent_e)))
