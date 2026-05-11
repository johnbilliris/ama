"""CLI for emitting the offline-cache bundle manifest (Spec 036 T136).

Wraps :mod:`ama_ingest.offline_bundle.build_offline_bundle` so the
``corpus-ingest.yml`` workflow can produce the dual-signed
``manifest.json`` artefact deterministically from the existing
``corpus_build.manifest.json`` produced by the ingest job.

Usage::

    python -m ama_ingest.offline_bundle_cli \\
        --chunks-manifest artifacts/corpus_build.manifest.json \\
        --corpus-build-sha <sha> \\
        --embedding-model-id text-embedding-3-large \\
        --output artifacts/offline-cache/manifest.json

The CLI does NOT sign — signatures are attached by the surrounding workflow
step using cosign keyless + age (FR-RAG-LS-02 / R-07).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ama_ingest.offline_bundle import build_offline_bundle


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument(
        "--chunks-manifest",
        type=Path,
        required=True,
        help="Path to the corpus build manifest produced by the ingest job.",
    )
    p.add_argument("--corpus-build-sha", required=True)
    p.add_argument("--embedding-model-id", required=True)
    p.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Where to write the offline-cache manifest JSON.",
    )
    p.add_argument(
        "--cosign-placeholder",
        default="<pending-cosign-keyless-signature>",
        help="Placeholder for the cosign signature (workflow attaches real one).",
    )
    p.add_argument(
        "--age-placeholder",
        default="<pending-age-detached>",
        help="Placeholder for the age detached signature.",
    )
    args = p.parse_args(argv)

    if not args.chunks_manifest.exists():
        sys.stderr.write(f"chunks manifest not found: {args.chunks_manifest}\n")
        return 1

    payload = json.loads(args.chunks_manifest.read_text(encoding="utf-8"))
    chunks = payload.get("chunks") or payload.get("entries") or []
    if not chunks:
        sys.stderr.write("chunks manifest contains no chunks\n")
        return 1

    manifest = build_offline_bundle(
        chunks=chunks,
        corpus_build_sha=args.corpus_build_sha,
        embedding_model_id=args.embedding_model_id,
        cosign_keyless=args.cosign_placeholder,
        age_detached=args.age_placeholder,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(manifest.to_json() + "\n", encoding="utf-8")
    sys.stdout.write(
        f"[offline_bundle_cli] wrote {args.output} "
        f"({len(manifest.entries)} entries, {manifest.size_bytes_total} bytes)\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
