"""eval-runner CLI entry — `python -m ama_eval.runner --run-id ...`.

Reads a run config from environment / args, drives the orchestrator, persists
results to Cosmos via the eval repositories, uploads sample traces to blob,
and writes the final exit code (0/1/2/3) per FR-018.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


def _setup_logging() -> None:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def main(argv: list[str] | None = None) -> int:
    _setup_logging()
    parser = argparse.ArgumentParser(prog="ama-eval-runner", description="LLM Evaluation Framework runner")
    parser.add_argument(
        "--run-id",
        default=os.environ.get("AMA_EVAL_RUN_ID"),
        help="run identifier (defaults to env AMA_EVAL_RUN_ID)",
    )
    parser.add_argument(
        "--dataset-id",
        default=os.environ.get("AMA_EVAL_DATASET_ID"),
        help="dataset identifier (defaults to env AMA_EVAL_DATASET_ID)",
    )
    parser.add_argument(
        "--dataset-version",
        default=os.environ.get("AMA_EVAL_DATASET_VERSION"),
        help="dataset version (defaults to env AMA_EVAL_DATASET_VERSION)",
    )
    parser.add_argument("--mode", default=os.environ.get("AMA_EVAL_MODE", "ad-hoc"))
    parser.add_argument("--max-cases", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    missing = [name for name, value in (
        ("--run-id/AMA_EVAL_RUN_ID", args.run_id),
        ("--dataset-id/AMA_EVAL_DATASET_ID", args.dataset_id),
        ("--dataset-version/AMA_EVAL_DATASET_VERSION", args.dataset_version),
    ) if not value]
    if missing:
        parser.error(f"missing required argument(s): {', '.join(missing)}")

    logger.info(
        "eval-runner starting run_id=%s dataset=%s@%s mode=%s",
        args.run_id,
        args.dataset_id,
        args.dataset_version,
        args.mode,
    )

    if args.dry_run:
        logger.info("dry-run: skipping orchestrator")
        return 0

    # Lazy imports so unit tests can import this module without Cosmos SDK
    try:
        from apps.api.app.repositories.eval.repositories import (
            AuditRepository,
            DatasetRepository,
            RunRepository,
        )

        from .foundry_client import FoundryClient
        from .orchestrator import OrchestratorContext, execute_run

        ds_repo = DatasetRepository()
        run_repo = RunRepository()
        audit = AuditRepository()

        logger.info(
            "repository backends: dataset=%s run=%s audit=%s cosmos_endpoint=%s",
            "cosmos" if getattr(ds_repo, "_cosmos", None) is not None else "memory",
            "cosmos" if getattr(run_repo, "_cosmos", None) is not None else "memory",
            "cosmos" if getattr(audit, "_cosmos", None) is not None else "memory",
            os.environ.get("COSMOS_ENDPOINT", "<unset>"),
        )

        run = run_repo.get_run(args.run_id)
        if not run:
            logger.error("run %s not found (item id=run:%s pk=%s)", args.run_id, args.run_id, args.run_id)
            return 1

        cases = ds_repo.list_cases(args.dataset_id, version=args.dataset_version)
        if not cases:
            cases = _load_cases_from_blob(args.dataset_id, args.dataset_version)
            if cases:
                logger.info("loaded %d cases from blob storage", len(cases))
        # Honour datasetSubset.maxCases on the run if --max-cases not passed
        run_max_cases = None
        try:
            run_max_cases = (run.datasetSubset.maxCases if run.datasetSubset else None)
        except AttributeError:
            run_max_cases = None
        effective_max = args.max_cases or run_max_cases
        if effective_max:
            cases = cases[:effective_max]
            logger.info("dataset capped to %d cases (max-cases=%s)", len(cases), effective_max)
        if not cases:
            logger.error("no cases for dataset %s@%s", args.dataset_id, args.dataset_version)
            return 1

        client = FoundryClient()

        def _foundry_call(model_id: str, messages: list[dict], parameters: dict) -> Any:
            from .evaluators.base import ModelOutput

            # The orchestrator passes ModelUnderTest.parameters via **kwargs;
            # `version` is needed by FoundryClient to look up the deployment.
            target_version = next(
                (m.version for m in run.models if m.modelId == model_id),
                None,
            )
            r = client.complete(
                model_id=model_id,
                messages=messages,
                version=target_version,
                **parameters,
            )
            return ModelOutput(
                text=r.text,
                finish_reason=r.finish_reason,
                safety_filter_triggered=r.safety_filter_triggered,
                latency_ms=r.latency_ms,
                prompt_tokens=r.usage_prompt_tokens,
                completion_tokens=r.usage_completion_tokens,
            )

        ctx = OrchestratorContext(
            cases=cases,
            run=run,
            audit_emit=lambda **kw: audit.emit_action(**kw),
            foundry_call=_foundry_call,
        )

        try:
            sc = execute_run(ctx)
        except Exception:
            run = run.model_copy(update={"status": "failed", "completedAt": datetime.now(UTC), "exitCode": 1})
            run_repo.save_run(run)
            raise
        run_repo.save_scorecard(sc)
        run = run.model_copy(update={"status": "succeeded", "completedAt": datetime.now(UTC), "exitCode": 0})
        run_repo.save_run(run)

        # Upload traces (best effort — log only on failure to avoid orphan-creation)
        _upload_traces(args.run_id, ctx.sample_traces)
        return 0

    except Exception as exc:
        logger.exception("eval-runner failed: %s", exc)
        return 1  # hard failure surfaces in API run document


def _load_cases_from_blob(dataset_id: str, version: str) -> list:
    """Load cases from the dataset cases.jsonl blob. Returns [] when storage env vars missing or blob absent."""
    account = os.environ.get("EVAL_BLOB_ACCOUNT") or os.environ.get("EVAL_STORAGE_ACCOUNT")
    container_name = os.environ.get("EVAL_DATASETS_CONTAINER", "datasets")
    if not account:
        return []
    try:
        import json as _json

        from ama_eval_core.models import EvaluationCase
        from azure.identity import DefaultAzureCredential
        from azure.storage.blob import BlobServiceClient

        cred = DefaultAzureCredential()
        svc = BlobServiceClient(account_url=f"https://{account}.blob.core.windows.net", credential=cred)
        blob = svc.get_container_client(container_name).get_blob_client(f"{dataset_id}/{version}/cases.jsonl")
        payload = blob.download_blob().readall().decode("utf-8")
        cases: list[EvaluationCase] = []
        for line in payload.splitlines():
            line = line.strip()
            if not line:
                continue
            cases.append(EvaluationCase(**_json.loads(line)))
        return cases
    except Exception as exc:  # noqa: BLE001
        logger.warning("could not load cases from blob: %s", exc)
        return []


def _upload_traces(run_id: str, traces: list) -> None:
    """Upload SampleTrace records to Azure Blob Storage. No-op when env not configured."""
    if not os.environ.get("EVAL_TRACES_CONTAINER"):
        return
    try:
        from azure.identity import DefaultAzureCredential
        from azure.storage.blob import BlobServiceClient

        account = os.environ["EVAL_STORAGE_ACCOUNT"]
        container = os.environ["EVAL_TRACES_CONTAINER"]
        cred = DefaultAzureCredential()
        svc = BlobServiceClient(account_url=f"https://{account}.blob.core.windows.net", credential=cred)
        cc = svc.get_container_client(container)
        for t in traces:
            blob = cc.get_blob_client(f"runs/{run_id}/traces/{t.caseId}.json")
            blob.upload_blob(t.model_dump_json(by_alias=True), overwrite=True)
    except Exception as exc:
        logger.warning("trace upload failed: %s", exc)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())


__all__ = ["main"]
