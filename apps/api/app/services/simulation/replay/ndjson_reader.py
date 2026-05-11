"""Spec-039 T075: NDJSON replay reader.

Yields one Python ``dict`` per non-empty NDJSON line. Raises
:class:`ReplayParseError` on the first malformed line so corruption is
caught loudly rather than silently filtered.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any


class ReplayParseError(ValueError):
    """Raised when an NDJSON line cannot be parsed as JSON."""


def read_ndjson(path: str | Path) -> Iterator[dict[str, Any]]:
    p = Path(path)
    with p.open("rb") as fh:
        for lineno, raw in enumerate(fh, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ReplayParseError(
                    f"{p}:{lineno}: invalid NDJSON line: {exc.msg}"
                ) from exc
            if not isinstance(obj, dict):
                raise ReplayParseError(
                    f"{p}:{lineno}: NDJSON line must be a JSON object"
                )
            yield obj


__all__ = ["ReplayParseError", "read_ndjson"]
