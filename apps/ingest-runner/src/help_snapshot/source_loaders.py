"""spec-038 — load help source documents based on a manifest.

The manifest (``apps/ingest-runner/manifests/help-snapshot.yaml``) lists
corpus globs and the spec-status gate ("Active|Implemented"). Sources whose
front-matter ``status`` is not in the allow-list are excluded by
:func:`load_sources` rather than at admission.
"""

from __future__ import annotations

import glob
import logging
import os
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


def load_sources(manifest_path: str) -> list[dict[str, Any]]:
    """Walk every glob from the manifest, return one source dict per file.

    Each source dict carries: ``path``, ``body``, ``classification`` (from
    front-matter or ``OFFICIAL`` default), ``status``, ``tenant_id`` (or
    ``__global__``), and ``source_id`` = relative path.
    """
    if yaml is None:
        raise RuntimeError("PyYAML not installed — required for help_snapshot.source_loaders")
    manifest = yaml.safe_load(Path(manifest_path).read_text(encoding="utf-8"))
    allow_status = set(manifest.get("allowed_status", ["Active", "Implemented"]))
    root = Path(manifest.get("root", ".")).resolve()
    sources: list[dict[str, Any]] = []
    for pattern in manifest.get("globs", []):
        for p in glob.glob(str(root / pattern), recursive=True):
            sp = Path(p)
            if not sp.is_file():
                continue
            body = sp.read_text(encoding="utf-8", errors="replace")
            meta = _parse_frontmatter(body)
            if meta.get("status") and meta["status"] not in allow_status:
                logger.info("skip non-active source: %s status=%s", p, meta["status"])
                continue
            sources.append(
                {
                    "source_id": os.path.relpath(p, root).replace("\\", "/"),
                    "path": p,
                    "body": body,
                    "classification": meta.get("classification", "OFFICIAL"),
                    "status": meta.get("status", "Active"),
                    "tenant_id": meta.get("tenant_id", "__global__"),
                    "personas": meta.get("personas", []),
                    "title": meta.get("title", sp.stem),
                }
            )
    return sources


def _parse_frontmatter(body: str) -> dict[str, Any]:
    if not body.startswith("---"):
        return {}
    end = body.find("\n---", 3)
    if end < 0:
        return {}
    if yaml is None:
        return {}
    try:
        return yaml.safe_load(body[3:end]) or {}
    except Exception:  # noqa: BLE001
        return {}


__all__ = ["load_sources"]
