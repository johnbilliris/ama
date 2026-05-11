"""Parse XML sitemaps (regular and sitemap-index style) and emit PDF/DOCX URLs.

Sitemaps are the most reliable way to enumerate documents on AU government
SPAs. WordPress, Drupal, and SharePoint all auto-generate them.

Usage::

    python sitemap_pdfs.py --out site.json https://www.example.gov.au/sitemap.xml
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def fetch(url: str) -> str:
    r = requests.get(
        url,
        headers={"User-Agent": UA, "Accept": "*/*", "From": "https://github.com/johnbilliris/ama"},
        timeout=45,
    )
    r.raise_for_status()
    return r.text


def parse_sitemap(xml: str) -> tuple[list[str], list[str]]:
    """Return (sub_sitemaps, urls). Handles sitemap-index and url-set."""
    soup = BeautifulSoup(xml, "lxml-xml") if "<sitemapindex" in xml else BeautifulSoup(xml, "lxml-xml")
    subs: list[str] = []
    urls: list[str] = []
    for sm in soup.find_all("sitemap"):
        loc = sm.find("loc")
        if loc and loc.text:
            subs.append(loc.text.strip())
    for u in soup.find_all("url"):
        loc = u.find("loc")
        if loc and loc.text:
            urls.append(loc.text.strip())
    return subs, urls


def crawl(start: str, *, max_subs: int = 50, exts: tuple[str, ...] = (".pdf",)) -> list[dict]:
    visited: set[str] = set()
    queue: list[str] = [start]
    out: list[dict] = []
    sub_count = 0
    while queue and sub_count <= max_subs:
        url = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)
        try:
            xml = fetch(url)
        except Exception as exc:
            out.append({"url": url, "error": str(exc)})
            continue
        subs, urls = parse_sitemap(xml)
        for s in subs:
            if s not in visited:
                queue.append(s)
                sub_count += 1
        for u in urls:
            path = urlparse(u).path.lower()
            if any(path.endswith(e) for e in exts):
                out.append({"url": u})
        time.sleep(1)
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("sitemaps", nargs="+")
    p.add_argument("--ext", action="append", default=[])
    p.add_argument("--max-subs", type=int, default=50)
    args = p.parse_args()
    exts = tuple(args.ext) if args.ext else (".pdf",)

    all_results: dict[str, list[dict]] = {}
    for s in args.sitemaps:
        try:
            results = crawl(s, max_subs=args.max_subs, exts=exts)
        except Exception as exc:
            results = [{"error": str(exc)}]
        all_results[s] = results
        print(f"{s}: {sum(1 for r in results if 'url' in r)} PDFs, {sum(1 for r in results if 'error' in r)} errors", file=sys.stderr)
    json.dump(all_results, sys.stdout, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
