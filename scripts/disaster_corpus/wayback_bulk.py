"""Bulk Wayback timestamp lookup: query CDX once per domain, then match URLs locally.

Reads URLs from stdin (one per line). Groups by host, makes ONE CDX call per host
to fetch all archived PDFs with timestamps, then for each input URL picks the most
recent timestamp whose `original` field matches.

Output (TSV): ``<timestamp_or_NONE>\t<original_url>\t<wayback_id_url_or_dash>``.
"""
from __future__ import annotations

import sys
import time
from collections import defaultdict
from urllib.parse import urlparse

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
HDRS = {"User-Agent": UA, "From": "ama-corpus@example.invalid"}


def cdx_domain(host: str, since: str = "2018", limit: int = 20000) -> list[tuple[str, str]]:
    params = {
        "url": f"{host}/*",
        "matchType": "domain",
        "filter": ["statuscode:200", "mimetype:application/pdf"],
        "from": since,
        "limit": str(limit),
        "fl": "timestamp,original",
    }
    for attempt in range(3):
        try:
            r = requests.get(
                "http://web.archive.org/cdx/search/cdx",
                params=params,
                headers=HDRS,
                timeout=240,
                verify=False,
            )
            if r.status_code == 200:
                rows = []
                for ln in r.text.splitlines():
                    parts = ln.split()
                    if len(parts) >= 2:
                        rows.append((parts[0], parts[1]))
                return rows
            time.sleep(5)
        except Exception as e:
            print(f"# CDX err {host}: {e}", file=sys.stderr)
            time.sleep(8)
    return []


def host_key(url: str) -> str:
    h = urlparse(url).hostname or ""
    return h.lower().lstrip("www.")


def normalise(url: str) -> str:
    return url.strip()


def main() -> int:
    urls: list[str] = []
    for ln in sys.stdin.read().splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        urls.append(ln)

    by_host: dict[str, list[str]] = defaultdict(list)
    for u in urls:
        by_host[host_key(u)].append(u)

    snapshots_by_host: dict[str, list[tuple[str, str]]] = {}
    for host in by_host:
        print(f"# CDX {host}", file=sys.stderr)
        snapshots_by_host[host] = cdx_domain(host)
        print(f"#   {len(snapshots_by_host[host])} archived PDFs", file=sys.stderr)
        time.sleep(1.0)

    for u in urls:
        host = host_key(u)
        rows = snapshots_by_host.get(host, [])
        target = u.lower()
        matches = [(ts, o) for ts, o in rows if o.lower() == target]
        if not matches:
            tail = u.rsplit("/", 1)[-1].lower()
            matches = [(ts, o) for ts, o in rows if o.lower().endswith("/" + tail)]
        if not matches:
            print(f"NONE\t{u}\t-")
            continue
        ts, orig = max(matches, key=lambda r: r[0])
        wb = f"https://web.archive.org/web/{ts}id_/{orig}"
        print(f"{ts}\t{u}\t{wb}")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
