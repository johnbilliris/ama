"""Use the Internet Archive Wayback CDX API to enumerate PDFs/DOCXs by host.

Wayback indexes most public-web PDFs and is permissive about machine queries.
This is the most reliable way to discover candidate documents on AU-gov hosts
that block scrapers or render their library through heavy JS.

Output: JSON list of {url, mime, timestamp, host} per host.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from urllib.parse import quote

import requests

UA = "ama-disaster-corpus/1.0 (link-discovery via Wayback CDX)"

CDX = "https://web.archive.org/cdx/search/cdx"


def cdx(host: str, *, mime: str = "application/pdf", limit: int = 1000) -> list[dict]:
    params = {
        "url": f"{host}/*",
        "filter": f"mimetype:{mime}",
        "output": "json",
        "limit": str(limit),
        "collapse": "urlkey",
    }
    qs = "&".join(f"{k}={quote(v)}" for k, v in params.items())
    url = f"{CDX}?{qs}"
    r = requests.get(url, headers={"User-Agent": UA}, timeout=120)
    r.raise_for_status()
    data = r.json()
    if not data:
        return []
    header, *rows = data
    idx_orig = header.index("original")
    idx_ts = header.index("timestamp")
    idx_status = header.index("statuscode")
    out = []
    for row in rows:
        if row[idx_status] != "200":
            continue
        out.append(
            {"url": row[idx_orig], "timestamp": row[idx_ts], "host": host, "mime": mime}
        )
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("hosts", nargs="+")
    p.add_argument("--limit", type=int, default=1500)
    p.add_argument("--mime", default="application/pdf")
    p.add_argument("--filter-keywords", action="append", default=[],
                   help="Only keep URLs whose path matches one of these (case-insensitive)")
    args = p.parse_args()

    all_results: dict[str, list[dict]] = {}
    for h in args.hosts:
        try:
            rows = cdx(h, mime=args.mime, limit=args.limit)
        except Exception as exc:
            rows = [{"error": str(exc), "host": h}]
        if args.filter_keywords:
            kws = [k.lower() for k in args.filter_keywords]
            rows = [r for r in rows if "url" in r and any(k in r["url"].lower() for k in kws)]
        all_results[h] = rows
        print(f"{h}: {len(rows)} hits", file=sys.stderr)
        time.sleep(2)
    json.dump(all_results, sys.stdout, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
