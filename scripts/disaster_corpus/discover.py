"""Crawl one or more index/landing pages and emit the PDF/DOCX links found.

Used to seed the corpus catalogue: given a publication index page, list every
candidate document so a human can curate which ones go into ``sources.yaml``.
"""
from __future__ import annotations

import argparse
import json
import sys
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

UA = "ama-disaster-corpus/1.0 (link-discovery)"


def discover(url: str, *, exts: tuple[str, ...] = (".pdf", ".docx", ".doc")) -> list[dict]:
    r = requests.get(url, headers={"User-Agent": UA}, timeout=45)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")
    out: list[dict] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith("#") or href.startswith("javascript:"):
            continue
        absu = urljoin(url, href)
        path = urlparse(absu).path.lower()
        if not any(path.endswith(e) for e in exts):
            continue
        if absu in seen:
            continue
        seen.add(absu)
        text = " ".join(a.get_text(" ", strip=True).split())
        out.append({"url": absu, "text": text or ""})
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("urls", nargs="+")
    p.add_argument("--ext", action="append", default=[])
    args = p.parse_args()
    exts = tuple(args.ext) if args.ext else (".pdf", ".docx", ".doc")
    results: dict[str, list[dict]] = {}
    for u in args.urls:
        try:
            results[u] = discover(u, exts=exts)
        except Exception as exc:  # pragma: no cover
            results[u] = [{"error": str(exc)}]
    json.dump(results, sys.stdout, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
