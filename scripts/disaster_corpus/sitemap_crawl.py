"""From sitemaps, find likely-publication landing pages, then crawl them for PDFs."""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from typing import Iterable
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Keywords that suggest a page lists / contains a publication
RELEVANT_KW = (
    "doctrine", "publication", "plan", "arrangement", "framework",
    "guideline", "handbook", "policy", "manual", "procedure",
    "operational", "operations", "rescue", "incident", "emergency",
    "disaster", "hazard", "risk", "preparedness", "response", "recovery",
    "warning", "evacuation", "flood", "storm", "fire", "bushfire",
    "cyclone", "tsunami", "heatwave", "pandemic", "command", "control",
    "coordination", "training", "displan", "semp", "emplan",
    "tema", "stema", "stema",
    "ahmppi", "ausvet", "rediplan", "natplan", "natsar",
    "downloadable",
)


def is_candidate_page(url: str) -> bool:
    p = urlparse(url).path.lower()
    if any(p.endswith(e) for e in (".jpg", ".jpeg", ".png", ".gif", ".css", ".js")):
        return False
    return any(kw in p for kw in RELEVANT_KW)


def fetch(url: str, *, timeout: float = 30.0) -> str:
    r = requests.get(
        url,
        headers={"User-Agent": UA, "Accept": "*/*", "Accept-Language": "en-AU,en;q=0.9",
                 "From": "https://github.com/johnbilliris/ama"},
        timeout=timeout,
    )
    r.raise_for_status()
    return r.text


def parse_sitemap(xml: str) -> tuple[list[str], list[str]]:
    soup = BeautifulSoup(xml, "lxml-xml")
    subs = [s.find("loc").text.strip() for s in soup.find_all("sitemap") if s.find("loc")]
    urls = [u.find("loc").text.strip() for u in soup.find_all("url") if u.find("loc")]
    return subs, urls


def harvest_sitemap_urls(start: str, *, max_subs: int = 20) -> list[str]:
    visited: set[str] = set()
    queue: list[str] = [start]
    all_urls: list[str] = []
    sub_count = 0
    while queue and sub_count <= max_subs:
        u = queue.pop(0)
        if u in visited:
            continue
        visited.add(u)
        try:
            xml = fetch(u, timeout=45)
        except Exception as exc:
            print(f"  WARN sitemap fetch failed: {u}: {exc}", file=sys.stderr)
            continue
        subs, urls = parse_sitemap(xml)
        all_urls.extend(urls)
        for s in subs:
            if s not in visited:
                queue.append(s)
                sub_count += 1
        time.sleep(0.5)
    return all_urls


def find_pdfs_on_page(page_url: str) -> list[dict]:
    try:
        html = fetch(page_url, timeout=20)
    except Exception as exc:
        return [{"page": page_url, "error": str(exc)}]
    soup = BeautifulSoup(html, "lxml")
    out: list[dict] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith("#") or href.startswith("javascript:"):
            continue
        absu = urljoin(page_url, href)
        if not urlparse(absu).path.lower().endswith(".pdf"):
            continue
        if absu in seen:
            continue
        seen.add(absu)
        text = " ".join(a.get_text(" ", strip=True).split())[:200]
        out.append({"page": page_url, "pdf": absu, "text": text})
    return out


def run(sitemap_urls: Iterable[str], *, max_pages: int = 200) -> dict:
    summary: dict = {}
    for sm in sitemap_urls:
        print(f"=== {sm} ===", file=sys.stderr)
        try:
            urls = harvest_sitemap_urls(sm)
        except Exception as exc:
            summary[sm] = {"error": str(exc)}
            continue
        candidates = [u for u in urls if is_candidate_page(u)]
        print(f"  total urls={len(urls)}  candidate pages={len(candidates)}", file=sys.stderr)
        candidates = candidates[:max_pages]
        pdfs: list[dict] = []
        for i, c in enumerate(candidates, 1):
            pdfs.extend(find_pdfs_on_page(c))
            if i % 25 == 0:
                print(f"    crawled {i}/{len(candidates)}", file=sys.stderr)
            time.sleep(0.5)
        unique_pdfs = list({p["pdf"]: p for p in pdfs if "pdf" in p}.values())
        summary[sm] = {
            "candidate_count": len(candidates),
            "pdfs": unique_pdfs,
            "errors": [p for p in pdfs if "error" in p][:5],
        }
        print(f"  unique PDFs: {len(unique_pdfs)}", file=sys.stderr)
    return summary


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("sitemaps", nargs="+")
    p.add_argument("--max-pages-per-site", type=int, default=200)
    args = p.parse_args()
    out = run(args.sitemaps, max_pages=args.max_pages_per_site)
    json.dump(out, sys.stdout, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
