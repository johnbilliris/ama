"""Query Wayback CDX for current+recent PDFs under a domain.

Filters:
- statuscode 200
- mimetype application/pdf
- recency: >= 2018

Then HEAD each candidate against the live publisher to check it still exists.
"""
from __future__ import annotations

import argparse
import csv
import io
import sys
import time

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
HDRS = {"User-Agent": UA, "From": "ama-corpus@example.invalid"}

CDX = "https://web.archive.org/cdx/search/cdx"


def harvest(domain: str, *, since: str = "2018", limit: int = 5000, keyword: str | None = None) -> list[tuple[str, str]]:
    params = {
        "url": f"{domain}/*",
        "matchType": "domain",
        "filter": ["statuscode:200", "mimetype:application/pdf"],
        "from": since,
        "limit": str(limit),
        "fl": "timestamp,original",
        "collapse": "urlkey",
    }
    try:
        r = requests.get(CDX, params=params, headers=HDRS, timeout=120, verify=False)
    except Exception as e:
        print(f"ERR CDX {domain}: {e}", file=sys.stderr)
        return []
    if r.status_code != 200:
        print(f"  CDX status={r.status_code} for {domain}", file=sys.stderr)
        return []
    rows: list[tuple[str, str]] = []
    for line in r.text.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        ts, url = parts[0], parts[1]
        if keyword and keyword.lower() not in url.lower():
            continue
        rows.append((ts, url))
    return rows


def head_check(url: str) -> tuple[int, str]:
    try:
        r = requests.head(url, headers=HDRS, timeout=20, allow_redirects=True, verify=False)
        return r.status_code, r.headers.get("content-type", "").split(";")[0]
    except Exception as e:
        return 0, type(e).__name__


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("domain", help="e.g. www.qra.qld.gov.au")
    p.add_argument("--since", default="2018")
    p.add_argument("--limit", type=int, default=2000)
    p.add_argument("--keyword", help="case-insensitive substring filter on URL")
    p.add_argument("--check-live", action="store_true", help="HEAD each URL on live host")
    p.add_argument("--polite", type=float, default=0.6, help="seconds between live HEAD requests")
    args = p.parse_args()

    rows = harvest(args.domain, since=args.since, limit=args.limit, keyword=args.keyword)
    print(f"# {args.domain}: {len(rows)} archived PDFs", file=sys.stderr)
    seen: set[str] = set()
    for ts, url in sorted(rows, key=lambda r: r[0], reverse=True):
        if url in seen:
            continue
        seen.add(url)
        if args.check_live:
            sc, ct = head_check(url)
            print(f"{sc:>3} {ct:<24} {ts}  {url}")
            time.sleep(args.polite)
        else:
            print(f"{ts}  {url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
