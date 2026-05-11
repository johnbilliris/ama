"""T064 — Entity test for ``Citation`` (Spec 036).

Pydantic-v2 round-trip; ``confidence ∈ [0.0, 1.0]``; forbids ``snippet`` when
``licence_mode == "metadata-only"`` and requires it when ``licence_mode ==
"full-text"`` (R-11).
"""

from __future__ import annotations

import pytest


def _domain():
    import importlib

    return importlib.import_module("ama_domain")


def _full_text_payload() -> dict:
    return {
        "jurisdiction": "nsw",
        "topic": "evacuation-planning",
        "page": 47,
        "source_url": "https://example.gov.au/evac.pdf",
        "rendered_url": "/docs/corpus/nsw/evacuation-planning/handbook.md#page-47",
        "sha256_of_chunk": "f" * 64,
        "licence_mode": "full-text",
        "confidence": 0.84,
        "snippet": "When the area is deemed safe…",
    }


def _metadata_only_payload() -> dict:
    return {
        "jurisdiction": "national",
        "topic": "aiims",
        "page": 12,
        "source_url": "https://example.gov.au/aiims.pdf",
        "rendered_url": "/docs/corpus/national/aiims/handbook.md#page-12",
        "sha256_of_chunk": "0" * 64,
        "licence_mode": "metadata-only",
        "confidence": 0.71,
    }


def test_full_text_round_trip() -> None:
    dom = _domain()
    payload = _full_text_payload()
    cit = dom.Citation.model_validate(payload)
    assert cit.licence_mode is dom.LicenceMode.FULL_TEXT
    assert cit.snippet == payload["snippet"]
    assert cit.confidence == 0.84


def test_metadata_only_round_trip() -> None:
    dom = _domain()
    payload = _metadata_only_payload()
    cit = dom.Citation.model_validate(payload)
    assert cit.licence_mode is dom.LicenceMode.METADATA_ONLY
    assert cit.snippet is None


def test_full_text_requires_snippet() -> None:
    dom = _domain()
    payload = _full_text_payload()
    payload.pop("snippet")
    with pytest.raises(Exception):  # noqa: B017,PT011
        dom.Citation.model_validate(payload)


def test_metadata_only_forbids_snippet() -> None:
    dom = _domain()
    payload = _metadata_only_payload()
    payload["snippet"] = "verboten"
    with pytest.raises(Exception):  # noqa: B017,PT011
        dom.Citation.model_validate(payload)


def test_excluded_licence_mode_rejected() -> None:
    """licence_mode == 'excluded' MUST never appear in a Citation."""
    dom = _domain()
    payload = _full_text_payload()
    payload["licence_mode"] = "excluded"
    payload.pop("snippet", None)
    with pytest.raises(Exception):  # noqa: B017,PT011
        dom.Citation.model_validate(payload)


def test_confidence_bounds() -> None:
    dom = _domain()
    payload = _full_text_payload()
    with pytest.raises(Exception):  # noqa: B017,PT011
        dom.Citation.model_validate({**payload, "confidence": -0.1})
    with pytest.raises(Exception):  # noqa: B017,PT011
        dom.Citation.model_validate({**payload, "confidence": 1.5})


def test_rendered_url_anchored_to_corpus_namespace() -> None:
    dom = _domain()
    payload = _full_text_payload()
    payload["rendered_url"] = "https://example.com/x"
    with pytest.raises(Exception):  # noqa: B017,PT011
        dom.Citation.model_validate(payload)


def test_sha256_must_be_hex() -> None:
    dom = _domain()
    payload = _full_text_payload()
    payload["sha256_of_chunk"] = "not-a-hash"
    with pytest.raises(Exception):  # noqa: B017,PT011
        dom.Citation.model_validate(payload)
