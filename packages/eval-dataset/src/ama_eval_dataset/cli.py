"""CLI entry points for ama_eval_dataset."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ama_eval_core.models import EvaluationCase

from .generator import DATASET_ID, VERSION, generate_corpus
from .manifest import build_manifest


def cmd_generate(args: argparse.Namespace) -> int:
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    cases = generate_corpus(seed=args.seed, target_size=args.size)

    cases_path = out / "cases.jsonl"
    with cases_path.open("w", encoding="utf-8") as fh:
        for case in cases:
            fh.write(case.model_dump_json() + "\n")

    manifest = build_manifest(
        cases=cases,
        dataset_id=DATASET_ID,
        version=VERSION,
        published_by="cli-generator",
        blob_uri=f"file://{cases_path.resolve().as_posix()}",
    )
    manifest_path = out / "manifest.json"
    manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")

    print(f"Generated {len(cases)} cases -> {cases_path}")
    print(f"Manifest -> {manifest_path}")
    print(f"Content hash: {manifest.contentHash}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    path = Path(args.input)
    if not path.exists():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        return 1

    errors: list[str] = []
    cases: list[EvaluationCase] = []
    with path.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                cases.append(EvaluationCase.model_validate_json(line))
            except Exception as exc:  # noqa: BLE001
                errors.append(f"Line {lineno}: {exc}")

    if errors:
        for e in errors:
            print(f"REJECT: {e}", file=sys.stderr)
        print(f"\n{len(errors)} rejection(s) from {len(cases) + len(errors)} lines", file=sys.stderr)
        return 1

    case_ids = [c.caseId for c in cases]
    seen: set[str] = set()
    dupes: set[str] = set()
    for cid in case_ids:
        if cid in seen:
            dupes.add(cid)
        seen.add(cid)
    if dupes:
        print(f"ERROR: duplicate caseIds: {sorted(dupes)[:10]}", file=sys.stderr)
        return 1

    print(f"OK: {len(cases)} cases validated, 0 rejections")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="ama_eval_dataset")
    sub = parser.add_subparsers(dest="command", required=True)

    gen_p = sub.add_parser("generate", help="Generate a synthetic evaluation corpus")
    gen_p.add_argument("--seed", type=int, required=True, help="Random seed for determinism")
    gen_p.add_argument("--output", required=True, help="Output directory")
    gen_p.add_argument("--size", type=int, default=5000, help="Number of cases (default 5000)")

    val_p = sub.add_parser("validate", help="Validate a cases.jsonl file")
    val_p.add_argument("--input", required=True, help="Path to cases.jsonl")

    args = parser.parse_args()
    if args.command == "generate":
        sys.exit(cmd_generate(args))
    elif args.command == "validate":
        sys.exit(cmd_validate(args))
