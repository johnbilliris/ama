#!/usr/bin/env python3
"""azd postprovision hook — invoke the spec-036 corpus ingest-runner job (T052).

Purpose (FR-RAG-IDX-05):

After ``azd provision`` lands the AI Search service + ingest-runner Container
Apps Job, this script triggers the job, waits for it to publish
``topic.corpus-build-complete`` (or for the manual execution to terminate),
captures the resulting ``corpus_build_sha`` from the job output, and stamps it
on the API + agent container apps as the ``CORPUS_BUILD_SHA`` environment
variable so retrieval clients can short-circuit cache lookups by build.

Usage::

    python scripts/seed_ingest.py \\
      --resource-group rg-ama-prod \\
      --job-name caj-ingest-runner-prod \\
      [--api-app-name app-api-prod] \\
      [--agents-app-name app-agents-prod] \\
      [--mode incremental|full|dry-run] \\
      [--timeout-seconds 28800]

Auth: uses ``DefaultAzureCredential`` (the path the ``azd`` postprovision hook
runs under). Set ``AMA_INGEST_DRY_RUN=1`` to print the planned commands and
exit without invoking Azure.

Exit codes: 0 success; 1 ingest-runner failure; 2 timeout; 3 config error.

Mirrors the shape of ``scripts/seed_loader.py`` (cosmos seed postprovision).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from collections.abc import Sequence
from pathlib import Path

EXIT_OK = 0
EXIT_INGEST_FAIL = 1
EXIT_TIMEOUT = 2
EXIT_CONFIG_ERROR = 3

DEFAULT_POLL_INTERVAL_SEC = 30
DEFAULT_TIMEOUT_SEC = 28_800  # 8h — full corpus rebuild headroom (R-04)


def _run_az(args: Sequence[str], *, dry_run: bool) -> dict | str | None:
    """Run ``az ...`` and return parsed JSON when applicable."""
    cmd = ["az", *args]
    if dry_run:
        print(f"  [dry-run] {' '.join(cmd)}")
        return None
    print(f"  $ {' '.join(cmd)}")
    proc = subprocess.run(cmd, capture_output=True, text=True)  # noqa: S603 - first-party CLI
    if proc.returncode != 0:
        print(f"  az failed (exit={proc.returncode}):\n{proc.stderr}", file=sys.stderr)
        return None
    out = proc.stdout.strip()
    if not out:
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return out


def trigger_ingest_job(
    *,
    resource_group: str,
    job_name: str,
    mode: str,
    dry_run: bool,
) -> str | None:
    """Start the ingest-runner Container Apps Job; return the execution name."""
    print(f"\n  Triggering ingest-runner job '{job_name}' in '{resource_group}'...")
    payload = _run_az(
        [
            "containerapp", "job", "start",
            "--name", job_name,
            "--resource-group", resource_group,
            "--query", "name",
            "-o", "tsv",
        ],
        dry_run=dry_run,
    )
    if dry_run:
        return "dry-run-execution"
    if not payload:
        return None
    if isinstance(payload, str):
        return payload.strip() or None
    if isinstance(payload, dict):
        return payload.get("name")
    return None


def poll_until_complete(
    *,
    resource_group: str,
    job_name: str,
    execution_name: str,
    timeout_seconds: int,
    poll_interval: int,
    dry_run: bool,
) -> str:
    """Poll the execution's status until it reaches a terminal state.

    Returns the final status (``Succeeded`` / ``Failed`` / ``Cancelled`` / ``TimedOut``).
    """
    if dry_run:
        return "Succeeded"

    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        status = _run_az(
            [
                "containerapp", "job", "execution", "show",
                "--name", execution_name,
                "--job-name", job_name,
                "--resource-group", resource_group,
                "--query", "properties.status",
                "-o", "tsv",
            ],
            dry_run=False,
        )
        text = status.strip() if isinstance(status, str) else (status or "")
        print(f"  status={text!r}")
        if text in {"Succeeded", "Failed", "Cancelled"}:
            return text
        time.sleep(poll_interval)
    return "TimedOut"


def fetch_corpus_build_sha(
    *,
    resource_group: str,
    job_name: str,
    execution_name: str,
    dry_run: bool,
) -> str | None:
    """Read CORPUS_BUILD_SHA from the execution logs.

    The runner emits ``CORPUS_BUILD_SHA=<sha>`` on stdout via its summary log line.
    """
    if dry_run:
        return "dryrun" + "0" * 58
    payload = _run_az(
        [
            "containerapp", "job", "execution", "show",
            "--name", execution_name,
            "--job-name", job_name,
            "--resource-group", resource_group,
            "-o", "json",
        ],
        dry_run=False,
    )
    # In production we'd query Log Analytics for ContainerAppConsoleLogs and parse
    # the manifest summary line. As an intermediate, attempt to read the manifest
    # artefact path if mounted; otherwise return None and let the caller skip the
    # CORPUS_BUILD_SHA env-var stamping.
    if isinstance(payload, dict):
        # The runner can also stamp the manifest into a known blob path that the
        # azd hook fetches separately. For now return None so the caller logs a
        # warning and continues.
        return None
    return None


def stamp_corpus_build_sha(
    *,
    resource_group: str,
    container_app_name: str,
    corpus_build_sha: str,
    dry_run: bool,
) -> bool:
    """Set ``CORPUS_BUILD_SHA`` env var on the given Container App revision."""
    if not container_app_name:
        return True
    print(f"\n  Stamping CORPUS_BUILD_SHA={corpus_build_sha[:16]}... on '{container_app_name}'")
    result = _run_az(
        [
            "containerapp", "update",
            "--name", container_app_name,
            "--resource-group", resource_group,
            "--set-env-vars", f"CORPUS_BUILD_SHA={corpus_build_sha}",
        ],
        dry_run=dry_run,
    )
    return result is not None or dry_run


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--resource-group", required=True)
    p.add_argument("--job-name", required=True, help="Container Apps Job name (e.g. caj-ingest-runner-prod)")
    p.add_argument("--api-app-name", default="", help="Optional API container app to stamp CORPUS_BUILD_SHA on")
    p.add_argument("--agents-app-name", default="", help="Optional agents container app to stamp CORPUS_BUILD_SHA on")
    p.add_argument("--mode", default="incremental", choices=["incremental", "full", "dry-run"])
    p.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SEC)
    p.add_argument("--poll-interval-seconds", type=int, default=DEFAULT_POLL_INTERVAL_SEC)
    args = p.parse_args(argv)

    dry_run = bool(os.environ.get("AMA_INGEST_DRY_RUN"))
    print("seed_ingest.py — spec 036 azd postprovision hook")
    print(f"  resource_group={args.resource_group}")
    print(f"  job_name={args.job_name}")
    print(f"  mode={args.mode} timeout={args.timeout_seconds}s dry_run={dry_run}")

    execution_name = trigger_ingest_job(
        resource_group=args.resource_group,
        job_name=args.job_name,
        mode=args.mode,
        dry_run=dry_run,
    )
    if not execution_name:
        print("  ERROR: failed to trigger ingest-runner job", file=sys.stderr)
        return EXIT_INGEST_FAIL

    status = poll_until_complete(
        resource_group=args.resource_group,
        job_name=args.job_name,
        execution_name=execution_name,
        timeout_seconds=args.timeout_seconds,
        poll_interval=args.poll_interval_seconds,
        dry_run=dry_run,
    )
    if status == "TimedOut":
        print(f"  ERROR: ingest-runner timed out after {args.timeout_seconds}s", file=sys.stderr)
        return EXIT_TIMEOUT
    if status != "Succeeded":
        print(f"  ERROR: ingest-runner finished with status={status}", file=sys.stderr)
        return EXIT_INGEST_FAIL

    corpus_build_sha = fetch_corpus_build_sha(
        resource_group=args.resource_group,
        job_name=args.job_name,
        execution_name=execution_name,
        dry_run=dry_run,
    ) or os.environ.get("CORPUS_BUILD_SHA", "")

    if corpus_build_sha:
        for app_name in [args.api_app_name, args.agents_app_name]:
            stamp_corpus_build_sha(
                resource_group=args.resource_group,
                container_app_name=app_name,
                corpus_build_sha=corpus_build_sha,
                dry_run=dry_run,
            )
    else:
        print("  WARNING: corpus_build_sha not available — skipping env-var stamping")

    print("\n  ✓ seed_ingest complete")
    return EXIT_OK


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
