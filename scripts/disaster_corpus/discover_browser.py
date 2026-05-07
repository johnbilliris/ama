"""Crawl one or more landing pages with a browser UA and emit PDF/DOCX links.

Like ``discover.py`` but uses a browser-class User-Agent so it gets past
WAF / bot-detection that is configured to block plain ``python-requests``.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def discover(url: str, *, exts: tuple[str, ...] = (".pdf", ".docx", ".doc")) -> list[dict]:
    r = requests.get(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-AU,en;q=0.9",
            "From": "https://github.com/johnbilliris/ama",
        },
        timeout=45,
    )
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
            print(f"{u}: {len(results[u])} links", file=sys.stderr)
        except Exception as exc:
            results[u] = [{"error": str(exc)}]
            print(f"{u}: ERR {exc}", file=sys.stderr)
        time.sleep(2)
    json.dump(results, sys.stdout, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
