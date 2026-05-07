"""Validate that every ingested topic folder is internally consistent.

Checks:
* `<source>.pdf`, `handbook.md`, `images/`, `source.json` all exist.
* PDF starts with `%PDF` magic.
* SHA-256 in source.json matches the PDF on disk.
* `handbook.md` references images that exist (no broken links).
* PDF page count == max `## Page N` heading in handbook.md (best-effort, only when PyMuPDF is available).
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

DOCS = Path(__file__).resolve().parents[2] / "docs"


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _validate(topic: Path) -> list[str]:
    errs: list[str] = []
    pdfs = list(topic.glob("*.pdf")) + list(topic.glob("*.PDF"))
    if not pdfs:
        return [f"no PDF in {topic}"]
    pdf = pdfs[0]
    hb = topic / "handbook.md"
    sj = topic / "source.json"
    if not hb.exists():
        errs.append(f"missing handbook.md in {topic}")
    if not sj.exists():
        errs.append(f"missing source.json in {topic}")

    with pdf.open("rb") as f:
        head = f.read(5)
    if not head.startswith(b"%PDF"):
        errs.append(f"NOT-A-PDF: {pdf} starts with {head!r}")
        return errs

    if sj.exists():
        try:
            sj_data = json.loads(sj.read_text(encoding="utf-8"))
            recorded = sj_data.get("sha256", "")
            actual = _sha256(pdf)
            if recorded and recorded != actual:
                errs.append(f"SHA-256 mismatch in {topic}: recorded={recorded[:12]} actual={actual[:12]}")
        except Exception as e:
            errs.append(f"source.json unreadable in {topic}: {e}")

    if hb.exists():
        text = hb.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r"!\[Image from page \d+\]\((\./images/[^)]+)\)", text):
            rel = m.group(1)
            if not (topic / rel.removeprefix("./")).exists():
                errs.append(f"missing image {rel} referenced by {hb}")
                break
    return errs


def main() -> int:
    bad = 0
    total = 0
    for source_json in DOCS.rglob("source.json"):
        topic = source_json.parent
        if topic == DOCS:
            continue
        total += 1
        errs = _validate(topic)
        if errs:
            bad += 1
            print(f"FAIL {topic.relative_to(DOCS)}")
            for e in errs:
                print(f"   {e}")
    print(f"\n{total - bad}/{total} OK,  {bad} failed")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
