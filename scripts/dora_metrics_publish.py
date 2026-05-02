"""Daily DORA metrics aggregator (spec-032 FR-C04, T814).

Reads GitHub workflow runs + issues for the past 30 days; computes:
  - deployment_frequency_per_day  (workflow_run completions of cd.yml / day)
  - lead_time_hours               (commit -> deploy delta)
  - change_failure_rate            (incidents within 24h / deployments)
  - mttr_minutes                  (issue close - issue open delta)

Posts as App Insights customMetrics via the OpenTelemetry SDK.
"""

from __future__ import annotations

import datetime as _dt
import os
import statistics
import urllib.error
import urllib.request
from collections.abc import Iterator, Sequence
from typing import Any

API = "https://api.github.com"


def _get(url: str, token: str) -> Any:
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "ama-dora-publisher/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
            import json

            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        print(f"::warning::GitHub API {url}: {exc}")
        return None


def _page_items(data: Any, item_key: str | None) -> Sequence[Any]:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if item_key and isinstance(data.get(item_key), list):
            return data[item_key]
        print(f"::warning::GitHub API response did not include expected list key: {item_key}")
        return []
    print(f"::warning::GitHub API response was not a list or object: {type(data).__name__}")
    return []


def _paged(url: str, token: str, item_key: str | None = None) -> Iterator[Any]:
    page = 1
    while True:
        sep = "&" if "?" in url else "?"
        data = _get(f"{url}{sep}per_page=100&page={page}", token)
        if not data:
            break
        items = _page_items(data, item_key)
        yield from items
        if len(items) < 100:
            break
        page += 1
        if page > 5:
            break


def collect(repo: str, token: str) -> dict[str, dict[str, float]]:
    now = _dt.datetime.now(_dt.UTC)
    cutoff = now - _dt.timedelta(days=30)
    runs_url = f"{API}/repos/{repo}/actions/workflows/cd.yml/runs?status=success&created=>{cutoff.date().isoformat()}"
    incidents_url = f"{API}/repos/{repo}/issues?labels=incident&state=all&since={cutoff.isoformat()}"

    deployments: dict[str, list[_dt.datetime]] = {"dev": [], "staging": [], "production": []}
    lead_times: dict[str, list[float]] = {"dev": [], "staging": [], "production": []}
    for run in _paged(runs_url, token, item_key="workflow_runs"):
        env = (run.get("head_branch") or "").lower()
        if env not in deployments:
            continue
        try:
            completed = _dt.datetime.fromisoformat(run["updated_at"].replace("Z", "+00:00"))
            head_commit_ts = _dt.datetime.fromisoformat(run["head_commit"]["timestamp"].replace("Z", "+00:00"))
            deployments[env].append(completed)
            lead_times[env].append((completed - head_commit_ts).total_seconds() / 3600.0)
        except (KeyError, ValueError):
            continue

    incidents: list[tuple[_dt.datetime, _dt.datetime | None]] = []
    for issue in _paged(incidents_url, token):
        try:
            opened = _dt.datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00"))
            closed_at_raw = issue.get("closed_at")
            closed = _dt.datetime.fromisoformat(closed_at_raw.replace("Z", "+00:00")) if closed_at_raw else None
            incidents.append((opened, closed))
        except (KeyError, ValueError):
            continue

    out: dict[str, dict[str, float]] = {}
    for env, times in deployments.items():
        deploy_freq = len(times) / 30.0
        env_lead_times = lead_times[env]
        avg_lead = statistics.mean(env_lead_times) if env_lead_times else 0.0
        # Change failure rate: incidents opened within 24h of any deploy / deploys.
        failures = 0
        for inc_opened, _ in incidents:
            for deploy_at in times:
                if 0 <= (inc_opened - deploy_at).total_seconds() <= 86400:
                    failures += 1
                    break
        cfr = (failures / len(times)) if times else 0.0

        # MTTR: mean (closed - opened) for closed incidents.
        ttrs = [(c - o).total_seconds() / 60.0 for o, c in incidents if c is not None]
        mttr = statistics.mean(ttrs) if ttrs else 0.0

        out[env] = {
            "dora.deployment_frequency_per_day": deploy_freq,
            "dora.lead_time_hours": avg_lead,
            "dora.change_failure_rate": cfr,
            "dora.mttr_minutes": mttr,
        }
    return out


def publish(metrics_by_env: dict[str, dict[str, float]]) -> None:
    cs = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if not cs:
        print("::warning::APPLICATIONINSIGHTS_CONNECTION_STRING not set; printing metrics only")
        for env, m in metrics_by_env.items():
            print(f"  {env}: {m}")
        return
    try:
        from azure.monitor.opentelemetry import configure_azure_monitor
        from opentelemetry import metrics as otel_metrics

        configure_azure_monitor(connection_string=cs)
        meter = otel_metrics.get_meter("ama.dora")
        instruments: dict[str, Any] = {}
        for env, m in metrics_by_env.items():
            for name, value in m.items():
                if name not in instruments:
                    instruments[name] = meter.create_up_down_counter(name)
                instruments[name].add(value, {"environment": env})
        # Force flush via the SDK
        try:
            from opentelemetry.sdk.metrics import MeterProvider

            provider = otel_metrics.get_meter_provider()
            if isinstance(provider, MeterProvider):
                provider.force_flush()
        except Exception as exc:
            print(f"flush warning: {exc}")
    except Exception as exc:  # noqa: BLE001
        print(f"::warning::publish failed (non-fatal): {exc}")


def main() -> int:
    repo = os.environ.get("REPO") or os.environ.get("GITHUB_REPOSITORY")
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not repo or not token:
        print("::error::REPO and GH_TOKEN env vars required")
        return 1
    metrics_by_env = collect(repo, token)
    print(f"DORA metrics computed for {len(metrics_by_env)} environments")
    publish(metrics_by_env)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
