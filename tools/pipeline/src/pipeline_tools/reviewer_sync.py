"""Reviewer-sync reconciler (T024) — ADR-029-01 / R17 user-owned-mode mitigation.

Asserts that the GitHub `production` environment's required-reviewers list
equals the union of three Entra groups (ama-oncall-sre + ama-incident-commander
+ ama-emergency-approver). Fails loudly when union > 6 (GitHub Environments
hard cap) and recommends migration to org mode.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any

import frontmatter  # type: ignore[import-untyped]
import httpx

from .audit_emitter import build_event, emit

GITHUB_API = os.environ.get("GITHUB_API", "https://api.github.com")
GRAPH_API = os.environ.get("GRAPH_API", "https://graph.microsoft.com/v1.0")
GITHUB_ENV_REVIEWER_CAP = 6


def _gh_headers() -> dict[str, str]:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("reviewer_sync: GITHUB_TOKEN env var required")
    return {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}


def _graph_headers() -> dict[str, str]:
    token = os.environ.get("GRAPH_TOKEN")
    if not token:
        raise RuntimeError("reviewer_sync: GRAPH_TOKEN env var required (Entra access token)")
    return {"Authorization": f"Bearer {token}"}


def fetch_entra_group_members(object_id: str, *, client: httpx.Client) -> set[str]:
    """Return {github_handle, ...} for an Entra group (resolves via UPN convention)."""
    members: set[str] = set()
    url = f"{GRAPH_API}/groups/{object_id}/members"
    while url:
        resp = client.get(url, headers=_graph_headers())
        resp.raise_for_status()
        data = resp.json()
        for m in data.get("value", []):
            handle = m.get("onPremisesSamAccountName") or m.get("mailNickname")
            if handle:
                members.add(handle)
        url = data.get("@odata.nextLink", "")
    return members


def fetch_environment_reviewers(owner: str, repo: str, env: str, *, client: httpx.Client) -> set[str]:
    """Return {github_handle, ...} from a GitHub Environment's required reviewers list."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}/environments/{env}"
    resp = client.get(url, headers=_gh_headers())
    resp.raise_for_status()
    payload = resp.json()
    reviewers: set[str] = set()
    for rule in payload.get("protection_rules", []):
        if rule.get("type") != "required_reviewers":
            continue
        for r in rule.get("reviewers", []):
            if r.get("type") == "User":
                reviewers.add(r["reviewer"]["login"])
    return reviewers


def add_environment_reviewer(owner: str, repo: str, env: str, login: str, *, client: httpx.Client) -> None:
    url = f"{GITHUB_API}/repos/{owner}/{repo}/environments/{env}"
    resp = client.get(url, headers=_gh_headers())
    resp.raise_for_status()
    current = resp.json()
    user_resp = client.get(f"{GITHUB_API}/users/{login}", headers=_gh_headers())
    user_resp.raise_for_status()
    user_id = user_resp.json()["id"]

    rules: list[dict[str, Any]] = []
    for rule in current.get("protection_rules", []):
        if rule["type"] == "required_reviewers":
            existing = rule.get("reviewers", [])
            existing.append({"type": "User", "reviewer": {"id": user_id}})
            rules.append({"type": "required_reviewers", "reviewers": existing})
        else:
            rules.append(rule)
    body = {"protection_rules": rules}
    put = client.put(url, headers=_gh_headers(), json=body)
    put.raise_for_status()


def reconcile(*, owner: str, repo: str, env: str, identity_path: str, mode: str, client: httpx.Client) -> int:
    """Return exit code: 0 on no drift / cap OK, 1 on drift, 2 on cap breach."""
    meta = frontmatter.load(identity_path).metadata
    groups = meta.get("entra_groups", [])
    union: set[str] = set()
    for g in groups:
        oid = g.get("object_id")
        if not oid or oid.startswith("00000000"):
            sys.stderr.write(f"reviewer_sync: group {g.get('name')} has placeholder object_id; skipping\n")
            continue
        union |= fetch_entra_group_members(oid, client=client)

    cap_breach = len(union) > GITHUB_ENV_REVIEWER_CAP
    if cap_breach:
        emit(
            build_event(
                actor="reviewer-sync",
                action="deploy.warning",
                outcome="denied",
                rationale=(
                    f"reviewer_sync_cap_breach: union={len(union)} "
                    f"exceeds GitHub Environments cap of {GITHUB_ENV_REVIEWER_CAP} "
                    "(per ADR-029-01 / research.md §R17). Migrate to org mode."
                ),
                environment="production",
            )
        )
        sys.stderr.write(
            f"reviewer_sync: cap breach — {len(union)} > {GITHUB_ENV_REVIEWER_CAP}; recommend migrate to org mode\n"
        )
        return 2

    current = fetch_environment_reviewers(owner, repo, env, client=client)
    drift = union - current
    extra = current - union
    if not drift and not extra:
        return 0

    if mode == "check":
        emit(
            build_event(
                actor="reviewer-sync",
                action="deploy.warning",
                outcome="denied",
                rationale=f"reviewer_sync_drift: missing={sorted(drift)} extra={sorted(extra)}",
                environment="production",
            )
        )
        return 1

    for login in drift:
        add_environment_reviewer(owner, repo, env, login, client=client)
        emit(
            build_event(
                actor="reviewer-sync",
                action="gate.decision",
                outcome="success",
                rationale=f"reviewer_sync_added: {login}",
                environment="production",
            )
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Reconcile GitHub production-env reviewers with Entra groups (T024)")
    p.add_argument("--owner", default=os.environ.get("GITHUB_REPOSITORY_OWNER", "johnbilliris"))
    p.add_argument("--repo", default="ama")
    p.add_argument("--env", default="production")
    p.add_argument("--identity-file", default="infra/IDENTITY.md")
    p.add_argument("--check", dest="mode", action="store_const", const="check", default="check")
    p.add_argument("--apply", dest="mode", action="store_const", const="apply")
    args = p.parse_args(argv)

    with httpx.Client(timeout=30.0) as client:
        return reconcile(
            owner=args.owner,
            repo=args.repo,
            env=args.env,
            identity_path=args.identity_file,
            mode=args.mode,
            client=client,
        )


if __name__ == "__main__":
    raise SystemExit(main())
