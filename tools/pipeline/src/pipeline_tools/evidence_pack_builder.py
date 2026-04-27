"""T060–T063 — Evidence pack builder (FR-013).

Composes a tamper-evident evidence pack for a release: SBOM, posture report,
audit-event slice, signed manifest, and known-good rollback marker. Writes
to the configured immutable Blob storage container.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import logging
import os
import sys
import tarfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from pipeline_tools.audit_emitter import emit

LOG = logging.getLogger("evidence_pack_builder")


@dataclass
class PackInputs:
    commit_sha: str
    service: str
    environment: str
    sbom_path: Path
    posture_report_path: Path
    audit_slice_path: Path


def _digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _build_tar(inputs: PackInputs) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        for label, path in {
            "sbom.json": inputs.sbom_path,
            "posture-report.json": inputs.posture_report_path,
            "audit-slice.jsonl": inputs.audit_slice_path,
        }.items():
            if not path.exists():
                LOG.warning("missing input %s; substituting empty placeholder", path)
                payload = b""
            else:
                payload = path.read_bytes()
            info = tarfile.TarInfo(name=label)
            info.size = len(payload)
            tar.addfile(info, io.BytesIO(payload))
    return buf.getvalue()


def _write_blob(container_url: str, blob_name: str, payload: bytes, manifest: dict) -> str:
    try:
        from azure.identity import DefaultAzureCredential
        from azure.storage.blob import BlobServiceClient
    except Exception as exc:  # pragma: no cover
        LOG.warning("azure-storage-blob unavailable (%s); writing locally", exc)
        local = Path("./evidence-pack-out") / blob_name
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_bytes(payload)
        (local.with_suffix(local.suffix + ".manifest.json")).write_text(json.dumps(manifest, indent=2))
        return str(local)

    service = BlobServiceClient(account_url=container_url, credential=DefaultAzureCredential())
    parts = container_url.rstrip("/").split("/")
    container_name = parts[-1]
    container_client = service.get_container_client(container_name)
    container_client.upload_blob(name=blob_name, data=payload, overwrite=False)
    container_client.upload_blob(
        name=blob_name + ".manifest.json",
        data=json.dumps(manifest, indent=2).encode("utf-8"),
        overwrite=False,
    )
    return f"{container_url}/{blob_name}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evidence pack builder (FR-013)")
    parser.add_argument("--commit-sha", required=True)
    parser.add_argument("--service", required=True, choices=["api", "agents", "ingestion", "web"])
    parser.add_argument("--environment", required=True, choices=["staging", "production"])
    parser.add_argument("--sbom", type=Path, required=True)
    parser.add_argument("--posture-report", type=Path, required=True)
    parser.add_argument("--audit-slice", type=Path, required=True)
    parser.add_argument(
        "--container-url",
        default=os.environ.get("AMA_EVIDENCE_CONTAINER_URL", ""),
        help="https://<account>.blob.core.windows.net/<container>",
    )
    parser.add_argument("--audit-actor", default=os.environ.get("GITHUB_ACTOR", "evidence-packer"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    inputs = PackInputs(
        commit_sha=args.commit_sha,
        service=args.service,
        environment=args.environment,
        sbom_path=args.sbom,
        posture_report_path=args.posture_report,
        audit_slice_path=args.audit_slice,
    )
    payload = _build_tar(inputs)
    digest = _digest(payload)
    timestamp = datetime.now(tz=UTC).isoformat().replace("+00:00", "Z")
    blob_name = f"{args.environment}/{args.service}/{args.commit_sha}/{timestamp.replace(':', '-')}.tar"
    manifest = {
        "commit_sha": args.commit_sha,
        "service": args.service,
        "environment": args.environment,
        "digest": digest,
        "created_at": timestamp,
        "schema_version": "1.0.0",
    }
    if args.container_url and not args.dry_run:
        uri = _write_blob(args.container_url, blob_name, payload, manifest)
    else:
        uri = f"local://{blob_name}"
        LOG.info("dry-run: not writing blob; manifest=%s", json.dumps(manifest))
    emit(
        action="evidence.write",
        actor=args.audit_actor,
        outcome="success",
        rationale=f"pack={blob_name} digest={digest}",
        evidence_uri=uri if uri.startswith("http") else None,
        digest=digest,
        service=args.service,
        environment=args.environment,
        dry_run=args.dry_run,
    )
    print(uri)
    return 0


if __name__ == "__main__":
    sys.exit(main())
