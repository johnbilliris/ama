"""CDX-only harvest (no live HEAD) - faster batch discovery."""
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

RELEVANT_KW = (
    "framework", "doctrine", "handbook", "manual",
    "guideline", "strategy", "standing-order", "standing_order",
    "sub-plan", "subplan", "service-spec", "service_spec",
    "service-description", "service_description",
    "preparedness", "betterment", "ausvetplan", "plantplan",
    "search-and-rescue", "national-plan", "national_plan",
    "evacuation", "tsunami", "biosecurity", "radiation",
    "policy-register", "operational-protocol", "operating-procedure",
    "concept-of-operations", "conops", "warning-system",
    "state-emergency", "state_emergency",
    "emergency-management-plan", "emergency_management_plan",
    "disaster-management-plan", "disaster_management_plan",
    "emergency-plan", "emergency_plan",
    "shp-", "_shp_", "/shp", "hazard-plan", "hazard_plan",
)

EXCLUDE_KW = (
    "annual-report", "annual_report", "minutes", "agenda", "ceo-",
    "ceo_", "monthly-report", "monthly_report", "media-release",
    "media_release", "newsletter", "presentation", "fact-sheet",
    "factsheet", "submission", "form", "application-form", "agm",
    "tender", "rfq", "rfp", "audit-report", "financial-statement",
    "budget", "activation-summary", "activation_summary",
    "month-report", "month_report",
    "quarterly-report", "newsletters",
    "/wp-content/uploads/202",  # exclude noisy WP timestamped uploads (still keep below in dedup)
)


def cdx(domain: str, since: str = "2018", limit: int = 5000) -> list[str]:
    params = {
        "url": f"{domain}/*",
        "matchType": "domain",
        "filter": ["statuscode:200", "mimetype:application/pdf"],
        "from": since,
        "limit": str(limit),
        "fl": "timestamp,original",
        "collapse": "urlkey",
    }
    for attempt in range(3):
        try:
            r = requests.get(
                "http://web.archive.org/cdx/search/cdx",
                params=params,
                headers=HDRS,
                timeout=180,
                verify=False,
            )
            if r.status_code == 200:
                rows = []
                for ln in r.text.splitlines():
                    parts = ln.split()
                    if len(parts) >= 2:
                        rows.append((parts[0], parts[1]))
                rows.sort(key=lambda r: r[0], reverse=True)
                seen, urls = set(), []
                for ts, u in rows:
                    if u in seen:
                        continue
                    seen.add(u)
                    urls.append(u)
                return urls
        except Exception as e:
            print(f"  CDX err {type(e).__name__}: {e}", file=sys.stderr)
            time.sleep(5)
    return []


def relevant(url: str) -> bool:
    low = url.lower()
    if any(k in low for k in EXCLUDE_KW):
        # but still allow if it matches strong relevance markers
        pass
    return any(k in low for k in RELEVANT_KW)


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: cdx_only.py <out.tsv> <domain> ...", file=sys.stderr)
        return 2
    out_path = sys.argv[1]
    domains = sys.argv[2:]
    out_lines = ["domain\turl"]
    for d in domains:
        print(f"\n# {d}", file=sys.stderr)
        urls = cdx(d)
        print(f"  {len(urls)} archived PDFs", file=sys.stderr)
        kept = [u for u in urls if relevant(u)]
        print(f"  {len(kept)} after relevance filter", file=sys.stderr)
        for u in kept:
            out_lines.append(f"{d}\t{u}")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines) + "\n")
    print(f"\nWrote {out_path} ({len(out_lines)-1} rows)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
