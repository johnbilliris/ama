"""From the wayback1.json dump, filter for relevant titles and test which
URLs still resolve at the original live host. Outputs a curated list
ready for sources.yaml."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


# Domain-specific keyword filters: {host_substring: [keyword, ...]}
RELEVANT = {
    "afac.com.au": [
        "aiims", "doctrine", "incident_management", "command", "control", "coordination",
        "emergency", "fire-management", "warning", "evacuation",
        "Climate", "rescue", "interoperability", "land-management",
    ],
    "amsa.gov.au": [
        "search-and-rescue", "search_and_rescue", "casualty", "natplan", "rescue", "natsar",
    ],
    "redcross.org.au": [
        "rediplan", "emergency", "preparedness", "household", "recovery", "psychological",
        "first-aid", "fact-sheet", "after-the-emergency", "preparing", "resilience",
        "community", "evacuation",
    ],
    "animalhealthaustralia.com.au": [
        "ausvetplan", "biosecurity", "anemis", "field-guide", "manual", "operational",
        "response", "outbreak", "veterinary", "control",
    ],
    "health.gov.au": [
        "ahmppi", "pandemic", "emergency", "health-protection", "plan",
        "displan", "disaster", "outbreak", "respiratory", "viral",
    ],
    "arpansa.gov.au": [
        "radiation", "radiological", "emergency", "nuclear", "incident",
        "response", "preparedness", "rps", "safety",
    ],
    "ga.gov.au": [
        "earthquake", "tsunami", "hazard", "risk", "natural-disaster",
        "tropical-cyclone", "flood",
    ],
}

NEGATIVE = {
    "freedom-of-information", "annual-report", "ips", "regulatory-plan",
    "minutes", "agenda", "code-of-conduct", "mar.pdf",
    "register", "submission", "consultation", "discussion-paper",
    "media-release", "statement", "factsheet-mark", "advert",
    "vacancy", "tender", "rfq", "rfp", "appointment", "policy.pdf",
}


def relevant(url: str) -> bool:
    u = url.lower()
    p = urlparse(u)
    host = p.netloc
    path = p.path
    # Strip www.
    matched_kw = False
    for host_key, kws in RELEVANT.items():
        if host_key in host:
            if any(kw in path for kw in kws):
                matched_kw = True
                break
    if not matched_kw:
        return False
    for n in NEGATIVE:
        if n in path:
            return False
    return True


def normalise(url: str) -> str:
    """Wayback often returns http:// + port. Force https + drop ports."""
    p = urlparse(url)
    netloc = (p.hostname or "").lower()
    new = f"https://{netloc}{p.path}"
    if p.query:
        new += "?" + p.query
    return new


def main() -> int:
    src = Path(sys.argv[1])
    data = json.loads(src.read_text(encoding="utf-8"))
    candidates: list[dict] = []
    seen: set[str] = set()
    for host, rows in data.items():
        for r in rows:
            u = r.get("url")
            if not u:
                continue
            if not relevant(u):
                continue
            n = normalise(u)
            if n in seen:
                continue
            seen.add(n)
            candidates.append({"original": u, "normalised": n, "host": host, "ts": r.get("timestamp")})

    print(f"# {len(candidates)} candidates after filtering", file=sys.stderr)

    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept": "*/*", "From": "https://github.com/johnbilliris/ama"})
    out: list[dict] = []
    for i, c in enumerate(candidates, 1):
        try:
            r = s.head(c["normalised"], timeout=20, allow_redirects=True)
            ct = r.headers.get("Content-Type", "")
            cl = r.headers.get("Content-Length", "")
            ok = r.status_code == 200 and "pdf" in ct.lower()
        except Exception as exc:
            r = None
            ct = f"ERR {exc.__class__.__name__}"
            cl = ""
            ok = False
        c["live_status"] = (r.status_code if r is not None else None)
        c["live_ct"] = ct
        c["live_cl"] = cl
        c["live_ok"] = ok
        out.append(c)
        if i % 20 == 0:
            print(f"  ...checked {i}/{len(candidates)} (live={sum(1 for x in out if x['live_ok'])})", file=sys.stderr)
        time.sleep(0.5)

    json.dump(out, sys.stdout, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
