"""PDF -> high-fidelity Markdown converter for the AU disaster-management corpus.

Produces output compatible with the existing ``docs/aidr/<topic>/handbook.md``
samples so that any downstream RAG chunker that already understands those
files keeps working unchanged:

  * H1 title
  * Source/URL block-quote
  * ``---`` separator before each page
  * ``## Page N`` heading
  * Page text (line-by-line, as extracted by PyMuPDF)
  * One ``![Image from page N](./images/page_N_img_M.<ext>)`` line per image
  * All raster images extracted to ``images/`` next to the markdown file

The function is intentionally pure-stdout-and-disk so it can be called from
the orchestrator (``build.py``) or directly from a one-off script.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF


@dataclass
class ConvertResult:
    pages: int
    images: int
    md_path: Path
    images_dir: Path
    sha256: str


def _sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _front_matter(
    *,
    title: str,
    publisher: str,
    url: str,
    edition: Optional[str],
    licence: Optional[str],
    sha256: str,
    retrieved_at: str,
) -> str:
    """Header block that mirrors the AIDR exemplars exactly."""
    edition_str = f" ({edition})" if edition else ""
    lines = [
        f"# {title}{edition_str}",
        "",
        f"> **Source**: {publisher}",
        f"> **URL**: {url}",
    ]
    if licence:
        lines.append(f"> **Licence**: {licence}")
    lines.extend(
        [
            f"> **Retrieved**: {retrieved_at}",
            f"> **SHA-256**: `{sha256}`",
            "> *Converted from PDF to Markdown format.*",
            "",
            "",
        ]
    )
    return "\n".join(lines)


def convert(
    pdf_path: Path,
    out_dir: Path,
    *,
    title: str,
    publisher: str,
    url: str,
    edition: Optional[str] = None,
    licence: Optional[str] = None,
    md_filename: str = "handbook.md",
    min_image_bytes: int = 0,
) -> ConvertResult:
    """Convert ``pdf_path`` into ``out_dir/handbook.md`` + ``out_dir/images/``.

    Parameters mirror the AIDR-style front matter. ``min_image_bytes`` lets a
    caller drop trivially small (likely-noise) images; default 0 keeps the
    AIDR-faithful behaviour of extracting everything so RAG output is stable.
    """
    pdf_path = Path(pdf_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    images_dir = out_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    sha = _sha256_of(pdf_path)
    retrieved_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    md_parts: list[str] = [
        _front_matter(
            title=title,
            publisher=publisher,
            url=url,
            edition=edition,
            licence=licence,
            sha256=sha,
            retrieved_at=retrieved_at,
        )
    ]

    image_count = 0
    with fitz.open(pdf_path) as doc:
        for page_index in range(doc.page_count):
            page_no = page_index + 1
            page = doc.load_page(page_index)

            md_parts.append("---\n")
            md_parts.append(f"## Page {page_no}\n\n")

            text = page.get_text("text") or ""
            text = text.replace("\r\n", "\n").rstrip() + "\n"
            md_parts.append(text)
            md_parts.append("\n")

            seen_xrefs: set[int] = set()
            page_image_index = 0
            for img in page.get_images(full=True):
                xref = img[0]
                if xref in seen_xrefs:
                    continue
                seen_xrefs.add(xref)
                try:
                    info = doc.extract_image(xref)
                except Exception:  # pragma: no cover - PyMuPDF edge cases
                    continue
                img_bytes = info.get("image")
                ext = info.get("ext") or "png"
                if not img_bytes:
                    continue
                if len(img_bytes) < min_image_bytes:
                    continue
                page_image_index += 1
                image_count += 1
                fname = f"page_{page_no}_img_{page_image_index}.{ext}"
                (images_dir / fname).write_bytes(img_bytes)
                md_parts.append(f"![Image from page {page_no}](./images/{fname})\n\n")

    md_path = out_dir / md_filename
    md_path.write_text("".join(md_parts), encoding="utf-8")

    # Provenance side-car (machine-readable; the orchestrator augments this)
    src_json = out_dir / "source.json"
    existing: dict = {}
    if src_json.exists():
        try:
            existing = json.loads(src_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}
    existing.update(
        {
            "title": title,
            "publisher": publisher,
            "url": url,
            "edition": edition,
            "licence": licence,
            "sha256": sha,
            "retrieved_at": retrieved_at,
            "pdf_filename": pdf_path.name,
            "pages": doc.page_count if False else None,  # set below
            "image_count": image_count,
        }
    )
    # doc is already closed; re-open just for page count would be wasteful: track during loop
    # (we wrote page_count after the loop closed; recompute from len of seen page indices)
    # Simpler: open briefly.
    with fitz.open(pdf_path) as doc2:
        existing["pages"] = doc2.page_count
    src_json.write_text(json.dumps(existing, indent=2, sort_keys=True), encoding="utf-8")

    return ConvertResult(
        pages=existing["pages"],
        images=image_count,
        md_path=md_path,
        images_dir=images_dir,
        sha256=sha,
    )


def _cli() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("pdf", type=Path)
    p.add_argument("out_dir", type=Path)
    p.add_argument("--title", required=True)
    p.add_argument("--publisher", required=True)
    p.add_argument("--url", required=True)
    p.add_argument("--edition", default=None)
    p.add_argument("--licence", default=None)
    p.add_argument("--md-filename", default="handbook.md")
    p.add_argument("--min-image-bytes", type=int, default=0)
    args = p.parse_args()

    r = convert(
        args.pdf,
        args.out_dir,
        title=args.title,
        publisher=args.publisher,
        url=args.url,
        edition=args.edition,
        licence=args.licence,
        md_filename=args.md_filename,
        min_image_bytes=args.min_image_bytes,
    )
    print(
        json.dumps(
            {
                "pages": r.pages,
                "images": r.images,
                "md": str(r.md_path),
                "sha256": r.sha256,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    _cli()
