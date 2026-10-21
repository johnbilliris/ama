#!/usr/bin/env python3
"""Spec-007 AUD-031 — no unoffloaded storage I/O on the async simulation surface.

The simulation stack uses the *synchronous* Azure Cosmos / Blob SDKs. Calling
them (or the blocking repository facades built on them) directly inside an
``async def`` blocks the shared API event loop that also serves live ingestion.
Every such call must be handed to :func:`app.core.async_io.run_blocking`, which
applies the per-loop semaphore, or batched through ``gather_bounded``.

Two rules are enforced across the modules listed in :data:`SURFACE`:

1. Inside ``async def`` bodies, a direct call to a blocking storage method is a
   violation unless it is passed to ``run_blocking`` / ``gather_bounded``
   (arguments of those calls are not descended into, so
   ``run_blocking(lambda: list(container.query_items(...)))`` is accepted).
2. ``asyncio.to_thread`` may not be used directly, because a bare thread hop
   escapes the shared concurrency bound.

This is a static scan. It proves call-shape only; it makes no latency or
throughput claim.

Usage::

    python tools/lint/check_spec007_async_offload.py
    python tools/lint/check_spec007_async_offload.py --repo-root .
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

#: Async modules reached from simulation request, service and background paths.
SURFACE: tuple[str, ...] = (
    "apps/api/app/api/routes/simulations.py",
    "apps/api/app/api/routes/simulation_chat.py",
    "apps/api/app/repositories/signal_repository.py",
    "apps/api/app/repositories/simulation_repository.py",
    "apps/api/app/repositories/sim_chat_history_repository.py",
    "apps/api/app/repositories/simulation_idempotency_repository.py",
    "apps/api/app/repositories/simulation_sequence_repository.py",
    "apps/api/app/repositories/synthetic_signals_repository.py",
    "apps/api/app/services/annotation_service.py",
    "apps/api/app/services/exercise_report_service.py",
    "apps/api/app/services/playback_service.py",
    "apps/api/app/services/scenario_seeding_service.py",
    "apps/api/app/services/simulation_audit_writer.py",
    "apps/api/app/services/simulation_service.py",
    "apps/api/app/services/warp_scheduler.py",
    "apps/api/app/services/simulation/audit_writer.py",
    "apps/api/app/services/simulation/controller_service.py",
)

#: Synchronous Azure Cosmos / Blob SDK methods.
SDK_METHODS: frozenset[str] = frozenset(
    {
        "create_item",
        "delete_item",
        "patch_item",
        "query_items",
        "read_all_items",
        "read_item",
        "replace_item",
        "upsert_item",
        "delete_blob",
        "download_blob",
        "get_blob_properties",
        "list_blobs",
        "upload_blob",
    }
)

#: Blocking repository / recorder facades that wrap the SDKs above.
FACADE_METHODS: frozenset[str] = frozenset(
    {
        "append_event",
        "append_turn",
        "count_events",
        "delete_event",
        "delete_history",
        "delete_tenant",
        "get_annotation",
        "get_nearest_snapshot",
        "get_scheduler_state",
        "get_scheduler_timeline",
        "list_events",
        "list_snapshots",
        "list_turns",
        "next_sequence",
        "record_chat_turn",
        "record_signal_delivered",
        "record_tool_invocation",
        "save_scheduler_state",
        "save_scheduler_timeline",
        "update_event",
    }
)

BLOCKING_METHODS = SDK_METHODS | FACADE_METHODS

#: Calls whose arguments are already executed off the loop under the shared bound.
OFFLOAD_WRAPPERS: frozenset[str] = frozenset({"run_blocking", "gather_bounded"})


def _callee_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return ""


def _is_to_thread(node: ast.Call) -> bool:
    func = node.func
    return isinstance(func, ast.Attribute) and func.attr == "to_thread"


class _AsyncBodyScanner(ast.NodeVisitor):
    """Collect blocking calls reachable on the event loop within one async def."""

    def __init__(self) -> None:
        self.hits: list[ast.Call] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        return  # nested sync helper: only reachable off-loop via a wrapper

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        self.generic_visit(node)

    def visit_Lambda(self, node: ast.Lambda) -> None:  # noqa: N802
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        name = _callee_name(node)
        if name in OFFLOAD_WRAPPERS:
            # Arguments run inside the worker thread; only inspect the callee itself.
            self.visit(node.func)
            return
        if name in BLOCKING_METHODS:
            self.hits.append(node)
        self.generic_visit(node)


def _scan_module(relative: str, source: str) -> list[str]:
    failures: list[str] = []
    tree = ast.parse(source, filename=relative)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _is_to_thread(node):
            failures.append(
                f"{relative}:{node.lineno}: bare asyncio.to_thread escapes the shared bound; use run_blocking"
            )

    for node in ast.walk(tree):
        if not isinstance(node, ast.AsyncFunctionDef):
            continue
        scanner = _AsyncBodyScanner()
        for statement in node.body:
            scanner.visit(statement)
        for hit in scanner.hits:
            failures.append(
                f"{relative}:{hit.lineno}: '{_callee_name(hit)}' is called on the event loop "
                f"inside async def {node.name}; wrap it in run_blocking"
            )
    return failures


def run(repo_root: Path, surface: tuple[str, ...] = SURFACE) -> list[str]:
    failures: list[str] = []
    for relative in surface:
        path = repo_root / relative
        if not path.exists():
            failures.append(f"{relative}: module in the AUD-031 surface no longer exists")
            continue
        failures.extend(_scan_module(relative, path.read_text(encoding="utf-8")))
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", type=Path)
    args = parser.parse_args(argv)

    failures = run(args.repo_root.resolve())
    for failure in failures:
        print(f"FAIL: {failure}", file=sys.stderr)
    if failures:
        return 1
    print(f"OK: {len(SURFACE)} simulation modules offload all blocking storage calls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
