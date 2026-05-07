"""Polite, cache-aware downloader for the AU disaster-management corpus.

Design
------
* Single ``requests.Session`` per host, descriptive User-Agent identifying
  the project and providing a contact email.
* Conditional GET via ``If-None-Match`` / ``If-Modified-Since`` recorded in a
  side-car ``source.json`` next to the cached file. Re-runs are O(1) when the
  upstream artifact is unchanged.
* Exponential back-off on 5xx / connection errors (max 5 attempts).
* Per-host token bucket: at most one request every ``host_min_interval``
  seconds (default 2 s) — well under any reasonable rate limit.
* SHA-256 of the bytes captured for provenance.
* Refuses to download URLs that are not on an explicit allow-list of hosts so
  a typo cannot exfiltrate to an unintended domain.

The ``source.json`` written alongside each artifact is the same file the
``pdf_to_md.py`` converter merges into — together they form the
single per-folder provenance record used by the orchestrator and manifest.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36 "
    "ama-disaster-corpus/1.0"
)
# RFC 9110 §10.1.2 ``From`` header — identifying contact info, visible in
# server logs to webmasters who want to confirm the bot's intent.
CONTACT_FROM = "https://github.com/johnbilliris/ama (issues)"

# Hosts we are willing to fetch from. Adding a host here is a deliberate act.
DEFAULT_ALLOW_HOSTS: tuple[str, ...] = (
    "knowledge.aidr.org.au",
    "www.aidr.org.au",
    "aidr.org.au",
    "www.nema.gov.au",
    "nema.gov.au",
    "www.homeaffairs.gov.au",
    "www.pmc.gov.au",
    "www.bom.gov.au",
    "media.bom.gov.au",
    "www.ga.gov.au",
    "www.afac.com.au",
    "knowledge.afac.com.au",
    "www.health.gov.au",
    "www.redcross.org.au",
    "www.animalhealthaustralia.com.au",
    "animalhealthaustralia.com.au",
    "www.planthealthaustralia.com.au",
    "www.amsa.gov.au",
    "www.arpansa.gov.au",
    "www.ntc.gov.au",
    "ntc.gov.au",
    # NSW
    "www.nsw.gov.au",
    "www.ses.nsw.gov.au",
    "www.rfs.nsw.gov.au",
    "www.fire.nsw.gov.au",
    "www.police.nsw.gov.au",
    "www.health.nsw.gov.au",
    "www.emergency.nsw.gov.au",
    # VIC
    "www.emv.vic.gov.au",
    "files.emv.vic.gov.au",
    "www.ses.vic.gov.au",
    "www.cfa.vic.gov.au",
    "www.frv.vic.gov.au",
    "www.police.vic.gov.au",
    # QLD
    "www.disaster.qld.gov.au",
    "www.qfes.qld.gov.au",
    "www.fire.qld.gov.au",
    "www.police.qld.gov.au",
    "www.qra.qld.gov.au",
    "www.igem.qld.gov.au",
    # SA
    "www.dpc.sa.gov.au",
    "www.ses.sa.gov.au",
    "www.cfs.sa.gov.au",
    "www.mfs.sa.gov.au",
    "www.police.sa.gov.au",
    # WA
    "www.dfes.wa.gov.au",
    "www.semc.wa.gov.au",
    "www.police.wa.gov.au",
    # TAS
    "www.ses.tas.gov.au",
    "www.fire.tas.gov.au",
    "www.dpfem.tas.gov.au",
    # NT
    "pfes.nt.gov.au",
    "www.pfes.nt.gov.au",
    "securent.nt.gov.au",
    # ACT
    "esa.act.gov.au",
    "www.esa.act.gov.au",
    "www.justice.act.gov.au",
)


@dataclass
class FetchResult:
    path: Path
    sha256: str
    bytes: int
    cached: bool
    url: str
    retrieved_at: str
    content_type: str


class _HostThrottle:
    """Tiny per-host minimum-interval throttle (process-local, single-threaded)."""

    def __init__(self, min_interval: float) -> None:
        self.min_interval = min_interval
        self._last: dict[str, float] = {}

    def wait(self, host: str) -> None:
        now = time.monotonic()
        nxt = self._last.get(host, 0.0) + self.min_interval
        if now < nxt:
            time.sleep(nxt - now)
        self._last[host] = time.monotonic()


def _sha256_stream(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class CorpusFetcher:
    """Fetches one artifact per call, polite by default."""

    def __init__(
        self,
        *,
        allow_hosts: tuple[str, ...] = DEFAULT_ALLOW_HOSTS,
        host_min_interval: float = 2.0,
        timeout: float = 60.0,
    ) -> None:
        self.allow_hosts = set(allow_hosts)
        self.timeout = timeout
        self.throttle = _HostThrottle(host_min_interval)
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Accept": "*/*",
                "From": CONTACT_FROM,
                "Accept-Language": "en-AU,en;q=0.9",
            }
        )

    def _check_host(self, url: str) -> str:
        host = urlparse(url).hostname or ""
        if host not in self.allow_hosts:
            raise PermissionError(
                f"Host {host!r} not in allow-list. Add it to DEFAULT_ALLOW_HOSTS in fetch.py "
                "if you intend to fetch from it."
            )
        return host

    def fetch(
        self,
        url: str,
        out_dir: Path,
        *,
        filename: Optional[str] = None,
    ) -> FetchResult:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        host = self._check_host(url)
        if filename is None:
            filename = os.path.basename(urlparse(url).path) or "artifact.bin"
        target = out_dir / filename
        meta_path = out_dir / "source.json"
        meta: dict = {}
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                meta = {}

        # Conditional GET headers from prior fetch
        headers = {}
        if target.exists():
            etag = meta.get("etag")
            last_mod = meta.get("last_modified")
            if etag:
                headers["If-None-Match"] = etag
            if last_mod:
                headers["If-Modified-Since"] = last_mod

        attempt = 0
        while True:
            attempt += 1
            self.throttle.wait(host)
            try:
                with self.session.get(
                    url, headers=headers, timeout=self.timeout, stream=True, allow_redirects=True
                ) as r:
                    if r.status_code == 304 and target.exists():
                        sha = meta.get("sha256") or _sha256_stream(target)
                        return FetchResult(
                            path=target,
                            sha256=sha,
                            bytes=target.stat().st_size,
                            cached=True,
                            url=url,
                            retrieved_at=meta.get("retrieved_at", ""),
                            content_type=meta.get("content_type", ""),
                        )
                    if r.status_code >= 500 and attempt < 5:
                        time.sleep(2 ** attempt)
                        continue
                    r.raise_for_status()
                    tmp = target.with_suffix(target.suffix + ".part")
                    h = hashlib.sha256()
                    total = 0
                    with tmp.open("wb") as f:
                        for chunk in r.iter_content(1 << 16):
                            if not chunk:
                                continue
                            f.write(chunk)
                            h.update(chunk)
                            total += len(chunk)
                    tmp.replace(target)
                    sha = h.hexdigest()
                    retrieved_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                    meta.update(
                        {
                            "url": url,
                            "filename": filename,
                            "sha256": sha,
                            "bytes": total,
                            "etag": r.headers.get("ETag"),
                            "last_modified": r.headers.get("Last-Modified"),
                            "content_type": r.headers.get("Content-Type", ""),
                            "retrieved_at": retrieved_at,
                        }
                    )
                    meta_path.write_text(
                        json.dumps(meta, indent=2, sort_keys=True), encoding="utf-8"
                    )
                    return FetchResult(
                        path=target,
                        sha256=sha,
                        bytes=total,
                        cached=False,
                        url=url,
                        retrieved_at=retrieved_at,
                        content_type=meta["content_type"],
                    )
            except (requests.ConnectionError, requests.Timeout):
                if attempt >= 5:
                    raise
                time.sleep(2 ** attempt)


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("url")
    p.add_argument("out_dir", type=Path)
    p.add_argument("--filename")
    args = p.parse_args()
    f = CorpusFetcher()
    r = f.fetch(args.url, args.out_dir, filename=args.filename)
    print(json.dumps(r.__dict__, indent=2, default=str))
