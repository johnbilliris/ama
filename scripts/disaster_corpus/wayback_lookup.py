"""Look up the most recent Wayback Machine snapshot timestamp for each URL.

Reads URLs from stdin (one per line, `#` comments allowed) and writes
``<timestamp>\t<original-url>\t<wayback-id-url>`` to stdout. If a URL has
no archived snapshot (all PDF or any), prints ``NONE\t<url>\t-``.

We use the CDX server directly (http only — https aborts in some networks)
and ask for the most recent successful PDF capture per URL.
"""
from __future__ import annotations

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


def latest_pdf_snapshot(url: str) -> tuple[str, str] | None:
    params = {
        "url": url,
        "filter": ["statuscode:200", "mimetype:application/pdf"],
        "fl": "timestamp,original",
        "limit": "-1",  # most recent capture
    }
    for attempt in range(3):
        try:
            r = requests.get(
                "http://web.archive.org/cdx/search/cdx",
                params=params,
                headers=HDRS,
                timeout=60,
                verify=False,
            )
            if r.status_code == 200:
                lines = [ln for ln in r.text.splitlines() if ln.strip()]
                if not lines:
                    return None
                parts = lines[-1].split()
                if len(parts) < 2:
                    return None
                return parts[0], parts[1]
            time.sleep(3)
        except Exception:
            time.sleep(5)
    return None


def main() -> int:
    sleep = float(sys.argv[1]) if len(sys.argv) > 1 else 0.6
    urls = []
    for ln in sys.stdin.read().splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        urls.append(ln)
    for u in urls:
        snap = latest_pdf_snapshot(u)
        if snap is None:
            print(f"NONE\t{u}\t-")
        else:
            ts, orig = snap
            wb = f"https://web.archive.org/web/{ts}id_/{orig}"
            print(f"{ts}\t{u}\t{wb}")
        sys.stdout.flush()
        time.sleep(sleep)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
