"""Spec-039 T075/T076/T077: replay reader, writer, and digest sidecar."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest


def test_writer_creates_ndjson_and_sha256_sidecar(tmp_path: Path) -> None:
    from app.services.simulation.replay.ndjson_writer import write_ndjson

    records = [
        {
            "simulated": True,
            "fictitious": True,
            "residency": "AU",
            "scenario_id": "scn",
            "seed": 1,
            "source_shape": "synthetic.fallback.v1",
            "timestamp": "2026-01-01T00:00:00.000001Z",
            "feed_version": "v1",
            "correlation_id": "0" * 32,
            "body": {"k": "v"},
        }
    ]
    path = tmp_path / "scn.ndjson"
    digest = write_ndjson(records, path)
    sidecar = path.with_suffix(".ndjson.sha256")
    assert sidecar.exists()
    assert sidecar.read_text("utf-8").strip().split()[0] == digest
    assert digest == hashlib.sha256(path.read_bytes()).hexdigest()


def test_reader_yields_dicts(tmp_path: Path) -> None:
    from app.services.simulation.replay.ndjson_reader import read_ndjson
    from app.services.simulation.replay.ndjson_writer import write_ndjson

    rec = {
        "simulated": True,
        "fictitious": True,
        "residency": "AU",
        "scenario_id": "scn",
        "seed": 1,
        "source_shape": "synthetic.fallback.v1",
        "timestamp": "2026-01-01T00:00:00.000001Z",
        "feed_version": "v1",
        "correlation_id": "a" * 32,
        "body": {"x": 1},
    }
    p = tmp_path / "scn.ndjson"
    write_ndjson([rec], p)
    out = list(read_ndjson(p))
    assert out == [rec]


def test_digest_mismatch_raises_loudly(tmp_path: Path) -> None:
    from app.services.simulation.replay.digest import (
        DigestMismatchError,
        verify_sidecar,
    )
    from app.services.simulation.replay.ndjson_writer import write_ndjson

    p = tmp_path / "scn.ndjson"
    write_ndjson([{"simulated": True, "x": 1}], p)
    sidecar = p.with_suffix(".ndjson.sha256")
    sidecar.write_text("0" * 64 + "  scn.ndjson\n", encoding="utf-8")
    with pytest.raises(DigestMismatchError):
        verify_sidecar(p)


def test_digest_match_passes(tmp_path: Path) -> None:
    from app.services.simulation.replay.digest import verify_sidecar
    from app.services.simulation.replay.ndjson_writer import write_ndjson

    p = tmp_path / "scn.ndjson"
    write_ndjson([{"simulated": True, "x": 1}], p)
    # write_ndjson already committed the sidecar; verify must pass.
    verify_sidecar(p)


def test_reader_rejects_nonjson_line(tmp_path: Path) -> None:
    from app.services.simulation.replay.ndjson_reader import (
        ReplayParseError,
        read_ndjson,
    )

    p = tmp_path / "broken.ndjson"
    p.write_bytes(b"{\"a\":1}\nnot-json\n")
    with pytest.raises(ReplayParseError):
        list(read_ndjson(p))
