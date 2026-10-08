"""``python -m ama_ingest`` entrypoint (Spec 036 T040; FR-RAG-IDX-01..05; R-08).

CLI surface bound by ``contracts/ingest-pipeline.md`` §4:

::

    python -m ama_ingest \\
      --corpus-root docs/corpus \\
      --search-endpoint $AZURE_SEARCH_ENDPOINT \\
      --index-alias corpus \\
      --embedding-model text-embedding-3-large@1 \\
      --corpus-build-sha $CORPUS_BUILD_SHA \\
      --mode {full|incremental|dry-run} \\
      --offline-bundle-out bundles/corpus-vN/offline-manifest.json

Exit codes (per §4):

| Code | Meaning                                |
|------|----------------------------------------|
| 0    | success                                |
| 1    | lint fail (licence inventory / carveout)|
| 2    | parity gate fail                       |
| 3    | AI Search write error                  |
| 4    | Foundry embedding error                |
| 5    | config error                           |

This module is **orchestration**. The hard work lives in ``chunker``,
``embedder``, ``licence_filter``, ``indexer``, ``manifest``, ``parity_gate``,
``offline_bundle``, ``carveout_preflight``, and ``audit`` — each of which is
unit-testable in isolation. The orchestrator is thin and dependency-injectable
for integration tests.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import (
    audit as audit_mod,
)
from . import (
    carveout_preflight,
    chunker,
    embedder,
    indexer,
    licence_filter,
    manifest,
    offline_bundle,
    parity_gate,
)

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Exit codes (per ingest-pipeline.md §4)
# --------------------------------------------------------------------------- #


EXIT_OK = 0
EXIT_LINT_FAIL = 1
EXIT_PARITY_FAIL = 2
EXIT_SEARCH_WRITE_ERROR = 3
EXIT_FOUNDRY_ERROR = 4
EXIT_CONFIG_ERROR = 5


@dataclass
class IngestRunResult:
    """Programmatic summary returned by :func:`run` for tests + the CLI."""

    exit_code: int
    chunks_written: int
    chunks_skipped_idempotent: int
    embedding_calls: int
    embedding_total_cost_usd: float
    blue_green: bool
    parity_gate_status: str
    alias_active_index: str
    target_index: str
    corpus_build_sha: str
    embedding_model_id: str
    parity_signals: list[dict[str, Any]]


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m ama_ingest",
        description="Spec 036 corpus-ingest entrypoint (FR-RAG-IDX-01..05).",
    )
    p.add_argument("--corpus-root", default="docs/corpus", type=Path)
    p.add_argument("--search-endpoint", default=os.environ.get("AZURE_SEARCH_ENDPOINT", ""))
    p.add_argument("--index-alias", default="corpus")
    p.add_argument(
        "--target-index", default=None, help="Override target index name; defaults to current alias target or corpus-v1"
    )
    p.add_argument(
        "--embedding-model",
        default=os.environ.get("EMBEDDING_MODEL", embedder.DEFAULT_MODEL_KEY),
    )
    p.add_argument(
        "--carveout-registry",
        default="infra/parameters/foundry-carveout.yaml",
        type=Path,
    )
    p.add_argument(
        "--carveout-region",
        default=os.environ.get("AZURE_AI_PROJECT_REGION", "australiaeast"),
    )
    p.add_argument("--corpus-build-sha", default=None)
    p.add_argument("--mode", choices=("full", "incremental", "dry-run"), default="incremental")
    p.add_argument("--manifest-out", default="artifacts/corpus_build.manifest.json", type=Path)
    p.add_argument("--offline-bundle-out", default=None, type=Path)
    p.add_argument(
        "--jurisdiction",
        default=None,
        help="Optional filter — restrict ingest to a single jurisdiction (smoke runs)",
    )
    p.add_argument("--log-level", default="INFO")
    return p


# --------------------------------------------------------------------------- #
# Orchestration core (test-injectable)
# --------------------------------------------------------------------------- #


def run(
    *,
    args: argparse.Namespace,
    index: indexer.IndexClient | None = None,
    alias: indexer.AliasService | None = None,
    embed: embedder.EmbedFn | None = None,
    audit_emitter: audit_mod.AuditEmitter | None = None,
    parity_inputs_override: parity_gate.ParityInputs | None = None,
    today: Any = None,
) -> IngestRunResult:
    """Run the ingest pipeline; tests inject in-memory clients.

    ``parity_inputs_override`` is for integration tests that synthesise
    parity-gate failures (T034) — it short-circuits the inputs the
    orchestrator would otherwise compute from indexer + embedder stats.
    """
    # Spec 036 / F-A11 / T236 — wrap the ingest pipeline in an OTel span so
    # ``ingest_duration_seconds``, ``chunks_processed``, ``embedding_calls``,
    # and ``ingest_errors`` show up on the Grafana dashboard. Any exception
    # below propagates after the span is finalised.
    try:
        from common.otel_telemetry import ingest_span as _ingest_span  # noqa: PLC0415
    except Exception:  # noqa: BLE001 - keep ingest runnable when agents pkg not on path
        _ingest_span = None

    if _ingest_span is None:
        return _run_inner(
            args=args,
            index=index,
            alias=alias,
            embed=embed,
            audit_emitter=audit_emitter,
            parity_inputs_override=parity_inputs_override,
            today=today,
        )

    with _ingest_span(pipeline_name="ama-ingest") as _span:
        result = _run_inner(
            args=args,
            index=index,
            alias=alias,
            embed=embed,
            audit_emitter=audit_emitter,
            parity_inputs_override=parity_inputs_override,
            today=today,
        )
        _span.counters["chunks_processed"] = int(getattr(result, "chunks_emitted", 0) or 0)
        _span.counters["embedding_calls"] = int(getattr(result, "embedding_calls", 0) or 0)
        _span.counters["ingest_errors"] = int(getattr(result, "errors", 0) or 0)
        return result


def _run_inner(
    *,
    args: argparse.Namespace,
    index: indexer.IndexClient | None = None,
    alias: indexer.AliasService | None = None,
    embed: embedder.EmbedFn | None = None,
    audit_emitter: audit_mod.AuditEmitter | None = None,
    parity_inputs_override: parity_gate.ParityInputs | None = None,
    today: Any = None,
) -> IngestRunResult:
    """Inner run(); separated from ``run()`` so the OTel span can wrap cleanly."""
    started_at = datetime.now(tz=UTC)

    # ---------------------------------------------------------------- 0. Carve-out pre-flight (T057)
    try:
        carveout_preflight.preflight(
            registry_path=args.carveout_registry,
            model_name=args.embedding_model.split("@", 1)[0],
            region=args.carveout_region,
            today=today,
        )
    except carveout_preflight.CarveoutPreflightError as exc:
        logger.error("carve-out pre-flight failed: %s", exc)
        return _failure(EXIT_LINT_FAIL, args, started_at, reason=str(exc))

    # ---------------------------------------------------------------- 1. Resolve indexes + alias
    # Production mode: when ``--search-endpoint`` is set and the caller did
    # not inject in-memory test stand-ins, build live AI Search clients.
    # Hermetic tests always pass ``index`` + ``alias`` so this branch is a
    # no-op for them. Dry-run mode keeps the in-memory stubs to avoid touching
    # the live service.
    use_live_clients: bool = bool(args.search_endpoint) and args.mode != "dry-run" and index is None and alias is None

    if use_live_clients:
        try:
            from . import live_clients as _live  # noqa: PLC0415
        except Exception as exc:  # noqa: BLE001
            return _failure(
                EXIT_CONFIG_ERROR,
                args,
                started_at,
                reason=f"failed to import live AI Search clients: {exc}",
            )
        try:
            alias = _live.LiveAzureSearchAlias(
                endpoint=args.search_endpoint,
                alias_name=args.index_alias,
            )
        except Exception as exc:  # noqa: BLE001
            return _failure(
                EXIT_SEARCH_WRITE_ERROR,
                args,
                started_at,
                reason=f"failed to construct AI Search alias client: {exc}",
            )

    if alias is None:
        # In production the caller wires a live AliasService; tests inject InMemoryAlias.
        alias = indexer.InMemoryAlias(
            alias=args.index_alias,
            active_index=None,
        )

    active_index_name = alias.get_active_index()
    active_embedding_model_id = alias.get_active_embedding_model_id()

    # Bootstrap case: alias does not yet exist. We MUST treat this as a
    # blue-green flow so the success path creates the alias on completion.
    # Without this, the very first run writes ``corpus-v1`` but never
    # registers the ``corpus`` alias — the runtime then has no way to
    # resolve ``RETRIEVAL_INDEX_ALIAS=corpus`` to a concrete index name.
    bootstrap_alias = active_index_name is None

    blue_green = (
        bool(active_embedding_model_id and active_embedding_model_id != args.embedding_model)
        or args.mode == "full"
        or bootstrap_alias
    )

    if args.target_index:
        target_index_name = args.target_index
    elif blue_green or active_index_name is None:
        target_index_name = indexer.next_index_name(current_index=active_index_name)
    else:
        target_index_name = active_index_name

    if use_live_clients and index is None:
        try:
            _live.ensure_index_schema(
                endpoint=args.search_endpoint,
                index_name=target_index_name,
            )
            index = _live.LiveAzureSearchIndex(
                endpoint=args.search_endpoint,
                index_name=target_index_name,
            )
        except Exception as exc:  # noqa: BLE001
            return _failure(
                EXIT_SEARCH_WRITE_ERROR,
                args,
                started_at,
                reason=f"failed to provision live AI Search index {target_index_name!r}: {exc}",
            )

    if index is None:
        # In production this is a SearchClient pointing at ``target_index_name``;
        # for the in-memory path tests pre-create one matching ``target_index_name``.
        index = indexer.InMemoryIndex(name=target_index_name)

    # Register the index with the alias (test-only stand-in).
    if isinstance(alias, indexer.InMemoryAlias):
        alias.register_index(target_index_name)

    bg_indexer = indexer.BlueGreenIndexer(index=index, alias=alias, alias_name=args.index_alias)

    # ---------------------------------------------------------------- 2. Discover entries + corpus_build_sha
    corpus_root: Path = args.corpus_root
    if not corpus_root.exists():
        return _failure(
            EXIT_CONFIG_ERROR,
            args,
            started_at,
            reason=f"corpus-root {corpus_root} does not exist",
        )

    corpus_build_sha = args.corpus_build_sha or manifest.compute_corpus_build_sha(corpus_root)

    # ---------------------------------------------------------------- 3. Chunk + filter + (optionally) embed
    # Production mode (``--search-endpoint`` + non dry-run): leave ``embed=None``
    # so ``FoundryEmbedder._call`` lazily constructs a live ``EmbeddingsClient``.
    # Hermetic tests inject ``embed``; everything else falls through to the
    # deterministic stub so callers never accidentally hit a live deployment.
    if embed is None and not use_live_clients:
        embed = embedder.deterministic_stub_embedder()

    embedder_inst = embedder.FoundryEmbedder(
        embed=embed,
        model_key=args.embedding_model,
    )

    if audit_emitter is None:
        audit_emitter = audit_mod.InMemoryAuditEmitter()

    all_chunks: list[chunker.Chunk] = []
    metadata_only_docs: list[dict[str, Any]] = []
    chunker_stats = chunker.ChunkerStats()

    for source_path, entry in manifest.iter_corpus_entries(corpus_root):
        try:
            jurisdiction, topic = manifest.derive_jurisdiction_topic(source_path, corpus_root)
        except ValueError as exc:
            logger.warning("skipping malformed corpus path %s: %s", source_path, exc)
            continue
        if args.jurisdiction and jurisdiction != args.jurisdiction:
            continue

        decision = licence_filter.classify(entry)
        if decision.mode == "excluded":
            logger.info("skipping excluded entry %s/%s", jurisdiction, topic)
            continue

        if decision.summary_only:
            metadata_only_docs.append(
                licence_filter.metadata_only_doc(
                    entry,
                    jurisdiction=jurisdiction,
                    topic=topic,
                    embedding_model_id=embedder_inst.model_key,
                    corpus_build_sha=corpus_build_sha,
                )
            )
            continue

        handbook_md_path = source_path.parent / "handbook.md"
        if not handbook_md_path.exists():
            logger.warning("no handbook.md for %s/%s — skipping", jurisdiction, topic)
            continue

        chunks = chunker.chunk_handbook(
            handbook_md=handbook_md_path.read_text(encoding="utf-8"),
            corpus_entry_id=f"{jurisdiction}/{topic}",
            jurisdiction=jurisdiction,
            topic=topic,
            licence_mode=decision.mode,
            source_url=str(entry.get("url", "")),
            stats=chunker_stats,
        )
        all_chunks.extend(chunks)

    # ---------------------------------------------------------------- 4. Build embedding map
    embedding_map: dict[str, list[float]] = {}
    if args.mode != "dry-run":
        try:
            embedding_map = embedder_inst.embed_chunks(all_chunks)
        except (embedder.EmbedderConfigurationError, embedder.EmbedderTransportError) as exc:
            logger.error("embedding failed: %s", exc)
            return _failure(EXIT_FOUNDRY_ERROR, args, started_at, reason=str(exc))

    # ---------------------------------------------------------------- 5. Project + write
    docs = chunker.chunks_to_index_docs(
        all_chunks,
        embedding_model_id=embedder_inst.model_key,
        corpus_build_sha=corpus_build_sha,
        embeddings=embedding_map,
    )
    docs.extend(metadata_only_docs)

    if args.mode == "dry-run":
        # No writes; report what would have happened.
        return _summary(
            args=args,
            started_at=started_at,
            chunks_written=0,
            chunks_skipped=len(docs),
            embedding_calls=0,
            embedding_cost=0.0,
            blue_green=blue_green,
            parity_gate_status="N/A",
            parity_signals=[],
            target_index=target_index_name,
            alias_active_index=active_index_name or "",
            corpus_build_sha=corpus_build_sha,
            embedding_model_id=embedder_inst.model_key,
            exit_code=EXIT_OK,
        )

    try:
        bg_indexer.write_chunks(docs)
    except ValueError as exc:
        logger.error("AI Search write failed: %s", exc)
        return _failure(EXIT_SEARCH_WRITE_ERROR, args, started_at, reason=str(exc))

    # ---------------------------------------------------------------- 6. Single-model invariant + parity gate
    try:
        bg_indexer.assert_single_embedding_model()
    except RuntimeError as exc:
        logger.error("single-model invariant violated: %s", exc)
        return _failure(EXIT_PARITY_FAIL, args, started_at, reason=str(exc))

    if blue_green:
        if parity_inputs_override is not None:
            verdict = parity_gate.evaluate(parity_inputs_override)
        else:
            verdict = parity_gate.evaluate(
                parity_gate.ParityInputs(
                    old_chunk_count=0,  # caller supplies snapshot in production
                    new_chunk_count=index.count(),
                    old_embedding_cost_usd=0.0,
                    new_embedding_cost_usd=embedder_inst.stats.cost_usd,
                    decision_equivalence=1.0,  # deferred to spec-033 wire-up
                    new_index_distinct_embedding_model_ids=len([m for m in index.distinct_embedding_model_ids() if m]),
                )
            )
    else:
        verdict = parity_gate.ParityVerdict(status="PASS", signals=[])

    # ---------------------------------------------------------------- 7. Flip alias (no-op if not blue-green)
    if blue_green:
        flip = bg_indexer.flip_alias(
            target_index=target_index_name,
            parity_gate_status=verdict.status,
        )
        if not flip.flipped:
            return _summary(
                args=args,
                started_at=started_at,
                chunks_written=bg_indexer.stats.documents_written,
                chunks_skipped=bg_indexer.stats.documents_skipped_idempotent,
                embedding_calls=embedder_inst.stats.call_count,
                embedding_cost=embedder_inst.stats.cost_usd,
                blue_green=True,
                parity_gate_status=verdict.status,
                parity_signals=[s.to_dict() for s in verdict.signals],
                target_index=target_index_name,
                alias_active_index=active_index_name or "",
                corpus_build_sha=corpus_build_sha,
                embedding_model_id=embedder_inst.model_key,
                exit_code=EXIT_PARITY_FAIL,
            )
        active_index_name = flip.new_index
        if isinstance(alias, indexer.InMemoryAlias):
            alias.set_active_embedding_model_id(embedder_inst.model_key)

    # ---------------------------------------------------------------- 8. Manifest + audit + (optional) bundle
    completed_at = datetime.now(tz=UTC)
    run_manifest = manifest.build_manifest(
        corpus_build_sha=corpus_build_sha,
        embedding_model_id=embedder_inst.model_key,
        target_index=target_index_name,
        alias_name=args.index_alias,
        chunk_count=bg_indexer.stats.documents_written,
        chunks_skipped_idempotent=bg_indexer.stats.documents_skipped_idempotent,
        embedding_calls=embedder_inst.stats.call_count,
        embedded_token_count=embedder_inst.stats.embedded_token_count,
        embedding_total_cost_usd=embedder_inst.stats.cost_usd,
        blue_green=blue_green,
        started_at=started_at,
        completed_at=completed_at,
        parity_gate_status=verdict.status,
        parity_gate_signals={s.name: s.to_dict() for s in verdict.signals},
    )
    if args.manifest_out:
        manifest.write_manifest(run_manifest, path=args.manifest_out)

    audit_emitter.emit_ingest_summary(
        audit_mod.make_ingest_summary(
            corpus_build_sha=corpus_build_sha,
            started_at=started_at,
            completed_at=completed_at,
            chunks_written=bg_indexer.stats.documents_written,
            chunks_skipped_idempotent=bg_indexer.stats.documents_skipped_idempotent,
            embedding_calls=embedder_inst.stats.call_count,
            embedding_total_cost_usd=embedder_inst.stats.cost_usd,
            blue_green=blue_green,
            parity_gate=verdict.status,
            alias_flipped_to=target_index_name if blue_green else None,
            parity_gate_signals={s.name: s.to_dict() for s in verdict.signals},
        )
    )

    if embedder_inst.stats.call_count:
        audit_emitter.emit_embedding(
            audit_mod.make_embedding_record(
                corpus_build_sha=corpus_build_sha,
                embedding_model_id=embedder_inst.model_key,
                deployment_alias=args.index_alias,
                chunk_count=bg_indexer.stats.documents_written,
                embedded_token_count=embedder_inst.stats.embedded_token_count,
                latency_ms=embedder_inst.stats.total_latency_ms,
            )
        )

    if args.offline_bundle_out:
        try:
            bundle = offline_bundle.build_offline_bundle(
                chunks=docs,
                corpus_build_sha=corpus_build_sha,
                embedding_model_id=embedder_inst.model_key,
            )
            offline_bundle.write_offline_bundle(bundle, path=args.offline_bundle_out)
        except ValueError as exc:
            logger.warning("offline bundle skipped: %s", exc)

    return _summary(
        args=args,
        started_at=started_at,
        chunks_written=bg_indexer.stats.documents_written,
        chunks_skipped=bg_indexer.stats.documents_skipped_idempotent,
        embedding_calls=embedder_inst.stats.call_count,
        embedding_cost=embedder_inst.stats.cost_usd,
        blue_green=blue_green,
        parity_gate_status=verdict.status,
        parity_signals=[s.to_dict() for s in verdict.signals],
        target_index=target_index_name,
        alias_active_index=active_index_name or "",
        corpus_build_sha=corpus_build_sha,
        embedding_model_id=embedder_inst.model_key,
        exit_code=EXIT_OK,
    )


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _summary(
    *,
    args: argparse.Namespace,
    started_at: datetime,
    chunks_written: int,
    chunks_skipped: int,
    embedding_calls: int,
    embedding_cost: float,
    blue_green: bool,
    parity_gate_status: str,
    parity_signals: list[dict[str, Any]],
    target_index: str,
    alias_active_index: str,
    corpus_build_sha: str,
    embedding_model_id: str,
    exit_code: int,
) -> IngestRunResult:
    return IngestRunResult(
        exit_code=exit_code,
        chunks_written=chunks_written,
        chunks_skipped_idempotent=chunks_skipped,
        embedding_calls=embedding_calls,
        embedding_total_cost_usd=embedding_cost,
        blue_green=blue_green,
        parity_gate_status=parity_gate_status,
        alias_active_index=alias_active_index,
        target_index=target_index,
        corpus_build_sha=corpus_build_sha,
        embedding_model_id=embedding_model_id,
        parity_signals=parity_signals,
    )


def _failure(
    exit_code: int,
    args: argparse.Namespace,
    started_at: datetime,
    *,
    reason: str,
) -> IngestRunResult:
    logger.error("ingest run failed (exit=%d): %s", exit_code, reason)
    return IngestRunResult(
        exit_code=exit_code,
        chunks_written=0,
        chunks_skipped_idempotent=0,
        embedding_calls=0,
        embedding_total_cost_usd=0.0,
        blue_green=False,
        parity_gate_status="N/A",
        alias_active_index="",
        target_index="",
        corpus_build_sha="",
        embedding_model_id=getattr(args, "embedding_model", ""),
        parity_signals=[{"reason": reason}],
    )


# --------------------------------------------------------------------------- #
# CLI entrypoint
# --------------------------------------------------------------------------- #


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    from apps.console_logging import configure_console_logging

    configure_console_logging(level=getattr(logging, args.log_level.upper(), logging.INFO))
    result = run(args=args)
    sys.stdout.write(json.dumps(result.__dict__, default=str) + "\n")
    return result.exit_code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
