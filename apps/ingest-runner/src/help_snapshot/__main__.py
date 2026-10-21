"""spec-038 — CLI entry: `python -m help_snapshot`."""

from __future__ import annotations

import argparse
import logging
import sys

from apps.console_logging import configure_console_logging

from . import alias_swinger, audit_emitters, embedder, pspf_guard, source_loaders

logger = logging.getLogger("help_snapshot")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="help_snapshot")
    p.add_argument("--manifest", required=True, help="Path to apps/ingest-runner/manifests/help-snapshot.yaml")
    p.add_argument("--snapshot-id", required=True)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)
    configure_console_logging()

    sources = source_loaders.load_sources(args.manifest)
    safe = pspf_guard.enforce_official_ceiling(sources)
    rejected = [s for s in sources if s not in safe]
    if rejected:
        audit_emitters.emit_admission_outcome(snapshot_id=args.snapshot_id, rejected=rejected)
    chunks = embedder.embed_chunks(safe, snapshot_id=args.snapshot_id, dry_run=args.dry_run)
    if args.dry_run:
        logger.info("dry-run: would index %d chunks under snap=%s", len(chunks), args.snapshot_id)
        return 0
    alias_swinger.swing_alias(snapshot_id=args.snapshot_id)
    audit_emitters.emit_admission_outcome(snapshot_id=args.snapshot_id, accepted=safe)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
