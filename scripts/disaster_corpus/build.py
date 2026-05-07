"""Orchestrator: read sources.yaml, fetch + convert each entry, write manifest.

Re-runs are idempotent: if the upstream artifact's bytes are unchanged
(matching ``source.json`` sha256), the convert step is also skipped.

Usage::

    python -m disaster_corpus.build               # build everything
    python -m disaster_corpus.build --only NSW    # only ingest one jurisdiction
    python -m disaster_corpus.build --dry-run     # print plan only
"""
from __future__ import annotations

import argparse
import json
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import yaml

# Allow running as ``python build.py`` from inside scripts/disaster_corpus/
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from fetch import CorpusFetcher  # noqa: E402  (path-adjusted)
from pdf_to_md import convert as pdf_to_md_convert  # noqa: E402

REPO_ROOT = HERE.parent.parent  # scripts/disaster_corpus -> scripts -> repo
DOCS_ROOT = REPO_ROOT / "docs"
SOURCES_YAML = HERE / "sources.yaml"


@dataclass
class Source:
    jurisdiction: str
    topic: str
    title: str
    publisher: str
    url: str
    edition: Optional[str] = None
    licence: Optional[str] = None
    mode: str = "full-text"  # full-text | metadata-only | excluded
    filename: Optional[str] = None  # override download filename
    notes: Optional[str] = None

    @property
    def out_dir(self) -> Path:
        return DOCS_ROOT / self.jurisdiction / self.topic


def load_sources(path: Path = SOURCES_YAML) -> list[Source]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    out: list[Source] = []
    for entry in raw.get("sources", []):
        out.append(Source(**entry))
    return out


def _safe_pdf_filename(url: str, source: Source) -> str:
    if source.filename:
        return source.filename
    last = url.rsplit("/", 1)[-1].split("?", 1)[0]
    if not last.lower().endswith(".pdf"):
        last = (last or "document") + ".pdf"
    # Replace url-encoded chars to keep a clean local name
    from urllib.parse import unquote

    return unquote(last)


def process(
    sources: Iterable[Source],
    *,
    fetcher: Optional[CorpusFetcher] = None,
    only_jurisdiction: Optional[str] = None,
    dry_run: bool = False,
    limit: Optional[int] = None,
) -> list[dict]:
    fetcher = fetcher or CorpusFetcher()
    results: list[dict] = []
    count = 0
    for s in sources:
        if only_jurisdiction and s.jurisdiction.lower() != only_jurisdiction.lower():
            continue
        if limit is not None and count >= limit:
            break
        count += 1
        rec: dict = {
            "jurisdiction": s.jurisdiction,
            "topic": s.topic,
            "title": s.title,
            "url": s.url,
            "out_dir": str(s.out_dir),
            "mode": s.mode,
        }
        if dry_run:
            rec["status"] = "dry-run"
            results.append(rec)
            print(f"DRY-RUN  {s.jurisdiction:>8}/{s.topic:<40}  {s.title}")
            continue
        try:
            s.out_dir.mkdir(parents=True, exist_ok=True)
            fname = _safe_pdf_filename(s.url, s)
            fr = fetcher.fetch(s.url, s.out_dir, filename=fname)
            rec.update({"sha256": fr.sha256, "bytes": fr.bytes, "cached": fr.cached})

            if s.mode == "excluded":
                rec["status"] = "fetched-only (mode=excluded)"
                results.append(rec)
                continue

            cr = pdf_to_md_convert(
                fr.path,
                s.out_dir,
                title=s.title,
                publisher=s.publisher,
                url=s.url,
                edition=s.edition,
                licence=s.licence,
            )
            rec.update({
                "pages": cr.pages,
                "images": cr.images,
                "md": str(cr.md_path.relative_to(REPO_ROOT)),
                "status": "ok",
            })
            print(
                f"OK       {s.jurisdiction:>8}/{s.topic:<40}  pages={cr.pages:<4} imgs={cr.images:<4} cached={fr.cached}"
            )
        except Exception as exc:
            rec["status"] = f"error: {exc.__class__.__name__}: {exc}"
            rec["traceback"] = traceback.format_exc(limit=2)
            print(f"FAIL     {s.jurisdiction:>8}/{s.topic:<40}  {exc}")
        results.append(rec)
    return results


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--sources", type=Path, default=SOURCES_YAML)
    p.add_argument("--only", help="Only ingest this jurisdiction (case-insensitive)")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--report", type=Path, help="Write JSON run-report here")
    args = p.parse_args()

    sources = load_sources(args.sources)
    print(f"Loaded {len(sources)} source(s) from {args.sources}")
    results = process(
        sources,
        only_jurisdiction=args.only,
        dry_run=args.dry_run,
        limit=args.limit,
    )

    ok = sum(1 for r in results if r.get("status") == "ok")
    fail = sum(1 for r in results if r.get("status", "").startswith("error"))
    print(f"\nSummary: {ok} ok, {fail} failed, {len(results) - ok - fail} other")

    if args.report:
        args.report.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"Report -> {args.report}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
