"""Evidence bundle builder for compliance audits (FR-026, US5).

Bundles run.json + scorecard.json + audit-events.json + model registry +
metric set + judge set + dataset manifest into a tar.gz with a sha256 manifest.
The bundle is signed via Azure Key Vault if `EVAL_EVIDENCE_SIGNING_KEY` is set;
otherwise emits an unsigned bundle with a manifest hash for non-prod.
"""

from __future__ import annotations

import hashlib
import io
import json
import logging
import os
import tarfile
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EvidenceBundle:
    run_id: str
    bundle_bytes: bytes
    manifest: dict[str, Any]
    manifest_sha256: str
    signature: str | None
    created_at: datetime


def _hash_bytes(b: bytes) -> str:
    return "sha256:" + hashlib.sha256(b).hexdigest()


def _serialise(obj: Any) -> bytes:
    return json.dumps(obj, indent=2, sort_keys=True, default=str).encode("utf-8")


def build_evidence_bundle(
    *,
    run: dict[str, Any],
    scorecard: dict[str, Any],
    audit_events: list[dict[str, Any]],
    dataset_manifest: dict[str, Any],
    metric_set: dict[str, Any],
    judge_set: dict[str, Any],
    model_registry: dict[str, Any],
    extra_artifacts: dict[str, bytes] | None = None,
    signer=None,
) -> EvidenceBundle:
    now = datetime.now(UTC)

    artefacts: dict[str, bytes] = {
        "run.json": _serialise(run),
        "scorecard.json": _serialise(scorecard),
        "audit-events.json": _serialise(audit_events),
        "dataset-manifest.json": _serialise(dataset_manifest),
        "metric-set.json": _serialise(metric_set),
        "judge-set.json": _serialise(judge_set),
        "model-registry.json": _serialise(model_registry),
    }
    if extra_artifacts:
        artefacts.update(extra_artifacts)

    manifest = {
        "schemaVersion": "1.0.0",
        "runId": run.get("runId"),
        "createdAt": now.isoformat(),
        "files": {name: _hash_bytes(data) for name, data in artefacts.items()},
    }
    manifest_bytes = _serialise(manifest)
    manifest_hash = _hash_bytes(manifest_bytes)

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name, data in {**artefacts, "manifest.json": manifest_bytes}.items():
            info = tarfile.TarInfo(name=name)
            info.size = len(data)
            info.mtime = int(now.timestamp())
            info.mode = 0o644
            tar.addfile(info, io.BytesIO(data))

    signature: str | None = None
    if signer is not None:
        signature = signer(manifest_bytes)
    elif os.environ.get("EVAL_EVIDENCE_SIGNING_KEY") and os.environ.get("AZURE_KEY_VAULT_URI"):
        signature = _kv_sign(manifest_bytes)

    return EvidenceBundle(
        run_id=str(run.get("runId", "")),
        bundle_bytes=buf.getvalue(),
        manifest=manifest,
        manifest_sha256=manifest_hash,
        signature=signature,
        created_at=now,
    )


def _kv_sign(data: bytes) -> str | None:
    try:
        from azure.identity import DefaultAzureCredential
        from azure.keyvault.keys import KeyClient
        from azure.keyvault.keys.crypto import CryptographyClient, SignatureAlgorithm

        vault = os.environ["AZURE_KEY_VAULT_URI"]
        key_name = os.environ["EVAL_EVIDENCE_SIGNING_KEY"]
        cred = DefaultAzureCredential()
        kc = KeyClient(vault_url=vault, credential=cred)
        key = kc.get_key(key_name)
        crypto = CryptographyClient(key, credential=cred)
        digest = hashlib.sha256(data).digest()
        result = crypto.sign(SignatureAlgorithm.rs256, digest)
        import base64

        return base64.b64encode(result.signature).decode("ascii")
    except Exception as exc:
        logger.warning("Evidence bundle signing failed; emitting unsigned bundle: %s", exc)
        return None


__all__ = ["EvidenceBundle", "build_evidence_bundle"]


# ---------------------------------------------------------------------------
# CLI entry-point (``python -m ama_eval.evidence``)
# ---------------------------------------------------------------------------


def _api_base_url() -> str:
    base = os.environ.get("AMA_API_BASE_URL", "").rstrip("/")
    if base:
        return base
    # Dev default deployed by the eval Bicep module.
    return "https://app-ama-api-dev.livelybush-e17946ba.australiaeast.azurecontainerapps.io"


def _maybe_auth_header() -> dict[str, str]:
    """Return ``Authorization`` header only when the API requires one.

    Honours FR-022a: if the API advertises ``anonymousAccess: true`` on
    ``/api/eval/health``, we do NOT send an ``Authorization`` header.
    """

    import requests  # noqa: PLC0415

    base = _api_base_url()
    try:
        h = requests.get(f"{base}/api/eval/health", timeout=10)
        if h.status_code == 200 and h.json().get("anonymousAccess") is True:
            return {}
    except Exception:  # noqa: BLE001
        pass
    token = os.environ.get("AMA_API_TOKEN")
    return {"Authorization": f"Bearer {token}"} if token else {}


def _fetch(url: str, headers: dict[str, str]) -> dict[str, Any]:
    import requests  # noqa: PLC0415

    resp = requests.get(url, headers=headers, timeout=60)
    if resp.status_code >= 400:
        logger.warning("fetch %s returned %s; using empty payload", url, resp.status_code)
        return {}
    try:
        return resp.json()
    except ValueError:
        return {}


def _cli(argv: list[str] | None = None) -> int:
    import argparse  # noqa: PLC0415
    from pathlib import Path  # noqa: PLC0415

    p = argparse.ArgumentParser(prog="python -m ama_eval.evidence")
    p.add_argument("--run-id", required=True)
    p.add_argument("--output", required=True)
    p.add_argument(
        "--sign-with-keyvault",
        help="Optional Key Vault key reference (NAME/KEY); enables KV signing via env vars.",
    )
    args = p.parse_args(argv)

    base = _api_base_url()
    headers = _maybe_auth_header()
    run = _fetch(f"{base}/api/eval/runs/{args.run_id}", headers)
    scorecard = _fetch(f"{base}/api/eval/runs/{args.run_id}/scorecard", headers)

    if not run:
        run = {"runId": args.run_id}

    if args.sign_with_keyvault:
        kv, _, key = args.sign_with_keyvault.partition("/")
        os.environ.setdefault("EVAL_EVIDENCE_SIGNING_KEY", key or kv)

    bundle = build_evidence_bundle(
        run=run,
        scorecard=scorecard,
        audit_events=[],
        dataset_manifest={},
        metric_set={},
        judge_set={},
        model_registry={},
    )

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(bundle.bundle_bytes)
    logger.info(
        "evidence bundle written run_id=%s bytes=%d sha=%s output=%s",
        bundle.run_id,
        len(bundle.bundle_bytes),
        bundle.manifest_sha256,
        out,
    )
    return 0


if __name__ == "__main__":
    import sys  # noqa: PLC0415

    from apps.console_logging import configure_console_logging  # noqa: PLC0415

    configure_console_logging()
    sys.exit(_cli())
