#!/usr/bin/env python3
"""spec-038 — One-off help_articles re-seed (uses scripts.seed_loader).

The canonical help-corpus seeding path is ``scripts/seed_loader.py`` invoked
by the azd postprovision hook (see ``azure.yaml`` → ``hooks.postprovision``).
This thin wrapper exists for manual workstation re-seeds that want to
target ``help_articles`` in isolation without re-running the entire seed
pipeline.

Auth: ``DefaultAzureCredential`` by default; set ``COSMOS_KEY`` for
key-based fallback.

Usage:
    python tools/help/seed_help_articles_cosmos.py \\
        --cosmos-endpoint https://cosmos-ama-zo6bb5.documents.azure.com:443/ \\
        --cosmos-database disaster-hub
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.seed_loader import (  # noqa: E402
    HELP_CONTENT_ROOT,
    load_help_articles,
    seed_help_articles,
)

logger = logging.getLogger("seed_help_articles_cosmos")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--content-root", default=str(HELP_CONTENT_ROOT))
    p.add_argument("--cosmos-endpoint", default=os.environ.get("COSMOS_ENDPOINT", ""))
    p.add_argument("--cosmos-database", default=os.environ.get("COSMOS_DATABASE", "disaster-hub"))
    p.add_argument(
        "--snapshot-id",
        default=os.environ.get("HELP_SNAPSHOT_ID") or f"snap-{datetime.now(UTC):%Y%m%dT%H%M%SZ}",
    )
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

    rows = load_help_articles(content_root=Path(args.content_root), snapshot_id=args.snapshot_id)
    if not rows:
        return 0
    if args.dry_run:
        logger.info("[dry-run] would upsert %d rows to help_articles (snapshot=%s)", len(rows), args.snapshot_id)
        return 0
    if not args.cosmos_endpoint:
        logger.error("--cosmos-endpoint required (or set COSMOS_ENDPOINT)")
        return 2
    seed_help_articles(args.cosmos_endpoint, args.cosmos_database, rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
