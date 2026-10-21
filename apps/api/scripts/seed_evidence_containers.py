#!/usr/bin/env python
"""Idempotent CLI for local Cosmos-emulator seeding of the 7 spec-040 (originally Spec-038) containers.

Quickstart §1. Reuses the in-memory registry as a no-op against the local
emulator when `--account` is not supplied; otherwise calls Cosmos SDK to
create-if-missing.
"""

from __future__ import annotations

import argparse
import sys

DEFAULT_CONTAINERS = (
    "kpi_ladder",
    "kpi_signals",
    "delta_scorecards",
    "causal_chains",
    "benchmark_register",
    "evidence_audit",
    "evidence_audit_dlq",
)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Seed evidence Cosmos containers.")
    p.add_argument("--account", default=None, help="Cosmos endpoint URL (None → in-memory).")
    p.add_argument("--database", default="ama-dev")
    p.add_argument(
        "--containers",
        default=",".join(DEFAULT_CONTAINERS),
        help="Comma-separated container names to ensure.",
    )
    args = p.parse_args(argv)
    names = [n.strip() for n in args.containers.split(",") if n.strip()]

    if args.account is None:
        from app.services.evidence._clients import get_registry

        reg = get_registry()
        for n in names:
            try:
                reg.get(n)
                print(f"ok  in-memory     {n}")
            except KeyError:
                print(f"err unknown        {n}", file=sys.stderr)
                return 2
        return 0

    try:  # pragma: no cover — exercised against real Cosmos only.
        from azure.cosmos import CosmosClient, PartitionKey
        from azure.identity import DefaultAzureCredential

        client = CosmosClient(args.account, credential=DefaultAzureCredential())
        db = client.create_database_if_not_exists(args.database)
        for n in names:
            pk = (
                "/audit_id"
                if n.startswith("evidence_audit")
                else "/kpi_id"
                if n.endswith("ladder")
                else "/scenario_id"
                if n.endswith("signals") or n.endswith("scorecards")
                else "/capability_id"
                if n.endswith("chains")
                else "/kpi_id"
            )
            db.create_container_if_not_exists(id=n, partition_key=PartitionKey(path=pk))
            print(f"ok  cosmos        {n} ({pk})")
        return 0
    except Exception as exc:
        print(f"err cosmos: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
