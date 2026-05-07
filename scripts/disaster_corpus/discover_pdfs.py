"""Fetch a publisher landing page and harvest .pdf hrefs (absolute + relative).

Usage:
  python scripts/disaster_corpus/discover_pdfs.py <url>
  python scripts/disaster_corpus/discover_pdfs.py --batch <file>   # one URL per line
"""
from __future__ import annotations

import argparse
import re
import sys
from urllib.parse import urljoin, urldefrag, urlparse

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
HDRS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-AU,en;q=0.9",
    "From": "ama-corpus@example.invalid",
}

PDF_RE = re.compile(r'href=["\']([^"\']+\.pdf[^"\']*)["\']', re.IGNORECASE)
ANCHOR_RE = re.compile(
    r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)


def discover(url: str, *, host_filter: str | None = None) -> list[tuple[str, str]]:
    try:
        r = requests.get(url, headers=HDRS, timeout=30, verify=False, allow_redirects=True)
    except Exception as e:
        print(f"ERR fetching {url}: {e}", file=sys.stderr)
        return []
    if r.status_code != 200 or "text/html" not in r.headers.get("content-type", ""):
        print(f"  status={r.status_code} ct={r.headers.get('content-type','')}", file=sys.stderr)
        return []
    html = r.text
    found: dict[str, str] = {}
    for m in ANCHOR_RE.finditer(html):
        href, text = m.group(1), m.group(2)
        if ".pdf" not in href.lower():
            continue
        absurl = urldefrag(urljoin(r.url, href))[0]
        if host_filter and host_filter not in urlparse(absurl).netloc:
            continue
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()[:120]
        if absurl not in found:
            found[absurl] = text
    for href in PDF_RE.findall(html):
        absurl = urldefrag(urljoin(r.url, href))[0]
        if host_filter and host_filter not in urlparse(absurl).netloc:
            continue
        found.setdefault(absurl, "")
    return sorted(found.items())


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("urls", nargs="*")
    p.add_argument("--batch", help="File with one URL per line")
    p.add_argument("--host-filter", help="Restrict to URLs containing this host")
    args = p.parse_args()

    urls: list[str] = list(args.urls)
    if args.batch:
        for ln in open(args.batch, encoding="utf-8"):
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                urls.append(ln)
    if not urls:
        p.error("provide URLs or --batch")

    for u in urls:
        print(f"\n# {u}")
        for href, text in discover(u, host_filter=args.host_filter):
            print(f"  {href}  ::  {text}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
