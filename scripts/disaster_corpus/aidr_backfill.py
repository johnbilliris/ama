"""Backfill source.json sidecars for AIDR handbooks that pre-date the pipeline.

Reads each `docs/aidr/<topic>/handbook.md` front-matter blockquote, finds the
matching PDF, computes its sha256 + size, and writes a `source.json` so the
manifest generator picks them up uniformly.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

DOCS = Path(__file__).resolve().parents[2] / "docs" / "corpus" / "aidr"


def _front_matter(md_text: str) -> dict:
    out: dict = {}
    m = re.match(r"^# (.+?)\n", md_text)
    if m:
        out["title"] = m.group(1).strip()
    for key in ("Source", "URL", "Edition", "Licence"):
        m = re.search(rf"^>\s+\*\*{key}\*\*:\s*(.+)$", md_text, flags=re.MULTILINE)
        if m:
            out[key.lower()] = m.group(1).strip()
    return out


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    written = 0
    for topic in sorted(DOCS.iterdir()):
        if not topic.is_dir():
            continue
        hb = topic / "handbook.md"
        if not hb.exists():
            continue
        pdfs = list(topic.glob("*.pdf")) + list(topic.glob("*.PDF"))
        if not pdfs:
            continue
        pdf = pdfs[0]
        meta = _front_matter(hb.read_text(encoding="utf-8", errors="ignore"))
        sj = {
            "url": meta.get("url", ""),
            "filename": pdf.name,
            "sha256": _sha256(pdf),
            "bytes": pdf.stat().st_size,
            "publisher": meta.get("source", "Australian Institute for Disaster Resilience (AIDR)"),
            "title": meta.get("title", topic.name),
            "licence": "AIDR — practitioner use; cite source",
            "mode": "metadata-only",
            "retrieved_at": datetime.fromtimestamp(pdf.stat().st_mtime, tz=timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
            "content_type": "application/pdf",
            "ingested_via": "backfill from pre-pipeline AIDR sample",
        }
        out = topic / "source.json"
        out.write_text(json.dumps(sj, indent=2, sort_keys=True), encoding="utf-8")
        written += 1
        print(f"wrote {out.relative_to(DOCS.parents[1])}")
    print(f"\n{written} AIDR sidecars written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
