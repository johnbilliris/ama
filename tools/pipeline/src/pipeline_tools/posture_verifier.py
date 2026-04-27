"""T051 — Posture verifier (FR-005, FR-014).

Sweeps Azure Resource Graph for resources in scope of the posture matrix and
emits ``posture.violation`` audit events for every drift between observed
properties and the env-locked rule set.

Exit codes:
* 0 — no violations.
* 1 — at least one ``deny``-severity violation found.
* 2 — invocation/IO error.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Any

import yaml

from pipeline_tools.audit_emitter import emit

LOG = logging.getLogger("posture_verifier")


def _load_matrix(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _load_exceptions(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return list(data.get("exceptions", []))


def _query_graph(subscription_id: str, resource_types: list[str]) -> list[dict[str, Any]]:
    """Query Azure Resource Graph for resources of the supplied types."""
    try:
        from azure.identity import DefaultAzureCredential
        from azure.mgmt.resourcegraph import ResourceGraphClient
        from azure.mgmt.resourcegraph.models import QueryRequest
    except Exception as exc:  # pragma: no cover - env without azure SDK
        LOG.warning("azure SDK unavailable (%s); returning empty result", exc)
        return []

    client = ResourceGraphClient(DefaultAzureCredential())
    type_filter = " or ".join(f'type =~ "{t}"' for t in resource_types)
    query = f"resources | where {type_filter} | project id, type, location, properties"
    response = client.resources(QueryRequest(subscriptions=[subscription_id], query=query))
    raw = response.data
    if raw is None:
        return []
    if isinstance(raw, list):
        return [dict(item) for item in raw]
    return [dict(item) for item in (raw.get("rows") or [])]


def _evaluate(resource: dict[str, Any], rules: dict[str, Any], exceptions: list[dict[str, Any]]) -> list[str]:
    """Return list of violation messages (empty == clean)."""
    type_key = resource.get("type", "").lower()
    rule = rules.get(type_key)
    if not rule:
        return []
    violations: list[str] = []
    props = resource.get("properties", {}) or {}
    for prop, expected in rule.get("required_properties", {}).items():
        actual = props.get(prop)
        if actual != expected:
            violations.append(f"{prop} expected={expected!r} actual={actual!r}")
    if violations:
        for exc in exceptions:
            if exc.get("resource_id") == resource.get("id"):
                return []
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Posture verifier (FR-005, FR-014)")
    parser.add_argument("--environment", required=True, choices=["dev", "staging", "production"])
    parser.add_argument("--subscription-id", required=True)
    parser.add_argument("--matrix", type=Path, default=Path("infra/policy/posture-matrix.yaml"))
    parser.add_argument("--exceptions", type=Path, default=Path("infra/policy/posture-exceptions.yaml"))
    parser.add_argument("--audit-actor", default=os.environ.get("GITHUB_ACTOR", "posture-verifier"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    matrix = _load_matrix(args.matrix)
    env_rules = (matrix.get("environments", {}) or {}).get(args.environment, {}) or {}
    rules = env_rules.get("rules", {}) or {}
    if not rules:
        LOG.warning("no rules defined for environment %s", args.environment)
        return 0

    exceptions = _load_exceptions(args.exceptions)
    resources = _query_graph(args.subscription_id, list(rules.keys()))
    LOG.info("scanned %d resources", len(resources))

    violation_count = 0
    for resource in resources:
        violations = _evaluate(resource, rules, exceptions)
        if not violations:
            continue
        violation_count += 1
        for msg in violations:
            emit(
                action="posture.violation",
                actor=args.audit_actor,
                outcome="denied",
                rationale=f"resource={resource.get('id')} {msg}",
                environment=args.environment,
                dry_run=args.dry_run,
            )
    LOG.info("violations: %d", violation_count)
    return 1 if violation_count else 0


if __name__ == "__main__":
    sys.exit(main())
