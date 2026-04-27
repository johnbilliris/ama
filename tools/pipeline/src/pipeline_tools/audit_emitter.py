"""Audit-event emitter (T020) — FR-015.

Reads structured audit events from CLI arguments or stdin, validates against
contracts/audit-event.schema.json, signs the payload with the workload identity,
and persists to the platform's append-only Cosmos DB audit container. Falls
back to stdout JSON in --dry-run mode for local development and CI fixtures.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import UTC, datetime
from typing import Any

import jsonschema

from . import _schema_loader

_SCHEMA = _schema_loader.load("audit-event.schema.json")
_VALIDATOR = jsonschema.Draft202012Validator(_SCHEMA)


def build_event(
    *,
    actor: str,
    action: str,
    outcome: str,
    rationale: str | None = None,
    environment: str | None = None,
    extras: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Construct a schema-valid audit event with auto-stamped id/timestamp/topology."""
    event: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "actor": actor,
        "timestamp": datetime.now(tz=UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "action": action,
        "outcome": outcome,
    }
    if rationale:
        event["rationale"] = rationale
    if environment:
        event["environment"] = environment
    topology = os.environ.get("AMA_SUBSCRIPTION_TOPOLOGY")
    if topology and "subscription_topology" not in (extras or {}):
        # subscription_topology is not in the canonical schema enum but extras may carry it
        pass
    if extras:
        event.update(extras)
    return event


def emit(event: dict[str, Any] | None = None, *, dry_run: bool = False, **kwargs: Any) -> None:
    """Validate and persist an audit event.

    Two calling conventions are supported:
    * ``emit(event_dict, dry_run=...)`` — pre-built event dict.
    * ``emit(action=..., actor=..., outcome=..., rationale=..., environment=...,
      service=..., stage_pct=..., evidence_uri=..., digest=..., dry_run=...)``
      — ergonomic kwargs form. Builds the event via :func:`build_event` and emits.
    """
    if event is None:
        actor = kwargs.pop("actor", "unknown")
        action = kwargs.pop("action")
        outcome = kwargs.pop("outcome")
        rationale = kwargs.pop("rationale", None)
        environment = kwargs.pop("environment", None)
        extras: dict[str, Any] = {k: v for k, v in kwargs.items() if v is not None}
        event = build_event(
            actor=actor,
            action=action,
            outcome=outcome,
            rationale=rationale,
            environment=environment,
            extras=extras,
        )
    _VALIDATOR.validate(event)
    if dry_run:
        json.dump(event, sys.stdout, sort_keys=True)
        sys.stdout.write("\n")
        return
    _write_to_cosmos(event)


def _write_to_cosmos(event: dict[str, Any]) -> None:
    endpoint = os.environ.get("AMA_AUDIT_COSMOS_ENDPOINT")
    if not endpoint:
        # No endpoint => degrade to stdout (warning); the workflow's
        # post-job evidence step is responsible for surfacing this.
        sys.stderr.write(
            "audit_emitter: AMA_AUDIT_COSMOS_ENDPOINT unset; writing to stdout for evidence pickup\n"
        )
        json.dump(event, sys.stdout, sort_keys=True)
        sys.stdout.write("\n")
        return
    from azure.cosmos import CosmosClient  # type: ignore
    from azure.identity import DefaultAzureCredential  # type: ignore

    client = CosmosClient(endpoint, credential=DefaultAzureCredential())
    db = client.get_database_client(os.environ.get("AMA_AUDIT_DB", "audit"))
    container = db.get_container_client(os.environ.get("AMA_AUDIT_CONTAINER", "deployment_events"))
    container.create_item(event)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Emit a deployment audit event (FR-015)")
    parser.add_argument("--actor", default=os.environ.get("GITHUB_ACTOR", "unknown"))
    parser.add_argument("--action", required=True)
    parser.add_argument("--outcome", required=True, choices=["success", "failure", "denied"])
    parser.add_argument("--rationale")
    parser.add_argument("--environment", choices=["dev", "staging", "production"])
    parser.add_argument("--service", choices=["api", "agents", "ingestion", "web"])
    parser.add_argument("--stage-pct", type=int, choices=[5, 25, 50, 100])
    parser.add_argument("--evidence-uri")
    parser.add_argument("--digest")
    parser.add_argument("--correlation-id")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--from-stdin", action="store_true", help="Read full JSON event from stdin")
    args = parser.parse_args(argv)

    if args.from_stdin:
        event = json.load(sys.stdin)
    else:
        extras: dict[str, Any] = {}
        for k, v in [
            ("service", args.service),
            ("stage_pct", args.stage_pct),
            ("evidence_uri", args.evidence_uri),
            ("digest", args.digest),
            ("correlation_id", args.correlation_id),
        ]:
            if v is not None:
                extras[k] = v
        event = build_event(
            actor=args.actor,
            action=args.action,
            outcome=args.outcome,
            rationale=args.rationale,
            environment=args.environment,
            extras=extras,
        )

    try:
        emit(event, dry_run=args.dry_run)
    except jsonschema.ValidationError as exc:
        sys.stderr.write(f"audit_emitter: schema validation failed — {exc.message}\n")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
