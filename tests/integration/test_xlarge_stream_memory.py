"""Spec-038 T124 — xlarge stream peak memory ≤ 50 MB (Edge "Large-volume").

Verifies the streaming xlarge generator produces 10 000 records without
materialising them — peak ``tracemalloc`` allocation MUST stay under
50 MB even after writing all records to disk.
"""

from __future__ import annotations

import sys
import tracemalloc
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.generators._xlarge_stream import (  # noqa: E402
    DEFAULT_VOLUME,
    write_ndjson_streaming,
)


def test_xlarge_stream_peak_memory(tmp_path: Path) -> None:
    out = tmp_path / "xlarge.ndjson"
    tracemalloc.start()
    digest = write_ndjson_streaming(out, seed=42, volume=DEFAULT_VOLUME)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    # 50 MB hard ceiling per spec edge case.
    assert peak <= 50 * 1024 * 1024, f"peak memory {peak} > 50MB"
    assert out.exists()
    assert len(digest) == 64
    # File must contain header + 10 000 records.
    n = sum(1 for _ in out.open("r", encoding="utf-8"))
    assert n == DEFAULT_VOLUME + 1
