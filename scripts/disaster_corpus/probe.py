"""Probe a list of candidate PDF URLs and report live status.

Uses GET with ``Range: bytes=0-1023`` (most servers honour it; if not the
response is still abandoned at ~1 KB) so we don't pull entire PDFs to test.
"""
from __future__ import annotations

import json
import sys
import time
from typing import Iterable

import requests

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def probe(urls: Iterable[str]) -> list[dict]:
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept": "*/*", "Accept-Language": "en-AU,en;q=0.9",
                       "From": "https://github.com/johnbilliris/ama"})
    out: list[dict] = []
    for u in urls:
        rec: dict = {"url": u}
        try:
            r = s.get(u, headers={"Range": "bytes=0-1023"}, timeout=25, stream=True, allow_redirects=True)
            ct = r.headers.get("Content-Type", "")
            cl = r.headers.get("Content-Length") or r.headers.get("Content-Range") or ""
            data = next(r.iter_content(2048), b"")
            r.close()
            rec.update({
                "status": r.status_code,
                "ct": ct,
                "len": cl,
                "is_pdf": data.startswith(b"%PDF") or "pdf" in ct.lower(),
                "final_url": r.url,
            })
        except Exception as exc:
            rec.update({"status": None, "error": f"{exc.__class__.__name__}: {str(exc)[:120]}"})
        out.append(rec)
        time.sleep(0.6)
    return out


def main() -> int:
    urls = [u.strip() for u in sys.stdin.read().splitlines() if u.strip() and not u.startswith("#")]
    out = probe(urls)
    json.dump(out, sys.stdout, indent=2)
    print(f"  alive PDFs: {sum(1 for x in out if x.get('is_pdf'))}/{len(out)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
