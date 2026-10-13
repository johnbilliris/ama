"""Exercise emulator exceptions with real scanners and synthetic non-exempt keys."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def scan(scanner: str, directory: Path, expected_rules: set[str]) -> None:
    report = directory / "report.json"
    if scanner == "gitleaks":
        command = [
            scanner,
            "dir",
            "--config",
            str(ROOT / ".gitleaks.toml"),
            "--redact",
            "--report-format",
            "json",
            "--report-path",
            str(report),
            ".",
        ]
    else:
        command = [
            scanner,
            "fs",
            "--secret-config",
            str(ROOT / "trivy-secret.yaml"),
            "--scanners",
            "secret",
            "--exit-code",
            "1",
            "--format",
            "json",
            "--output",
            str(report),
            ".",
        ]
    result = subprocess.run(command, cwd=directory, capture_output=True, text=True, check=False)
    expected_exit = 1 if expected_rules else 0
    if result.returncode != expected_exit:
        raise RuntimeError(
            f"{scanner}: expected exit {expected_exit}, got {result.returncode}\n{result.stdout}\n{result.stderr}"
        )
    findings = json.loads(report.read_text(encoding="utf-8"))
    if scanner == "gitleaks":
        actual_rules = {finding["RuleID"] for finding in findings}
    else:
        actual_rules = {
            finding["RuleID"] for target in findings.get("Results", []) for finding in target.get("Secrets", [])
        }
    if actual_rules != expected_rules:
        raise RuntimeError(f"{scanner}: expected rules {expected_rules}, got {actual_rules}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scanner", choices=["gitleaks", "trivy"])
    scanner = parser.parse_args().scanner
    compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")
    cosmos_match = re.search(r"COSMOS_KEY:\s*(\S+)", compose)
    azurite_match = re.search(r"AccountKey=([^;]+);", compose)
    if cosmos_match is None or azurite_match is None:
        raise RuntimeError("Compose must contain both local emulator keys")
    cosmos_key = cosmos_match.group(1)
    azurite_key = azurite_match.group(1)
    synthetic_key = base64.b64encode(hashlib.sha512(b"emulator-exception-regression").digest()).decode()
    storage_rule = "generic-api-key" if scanner == "gitleaks" else "azure-storage-account-key"
    cases = [
        ("emulator-values", "compose.yaml", compose, set()),
        ("replacement-storage-key", "compose.yaml", compose.replace(azurite_key, synthetic_key), {storage_rule}),
        (
            "additional-storage-key",
            "compose.yaml",
            compose + f"\n# Synthetic regression fixture: AccountKey={synthetic_key};\n",
            {storage_rule},
        ),
        (
            "modified-public-storage-key",
            "compose.yaml",
            compose.replace(azurite_key, azurite_key.replace("GMGw", "GMGx")),
            {storage_rule},
        ),
    ]
    if scanner == "gitleaks":
        cases.extend(
            [
                (
                    "replacement-cosmos-key",
                    "compose.yaml",
                    compose.replace(cosmos_key, synthetic_key),
                    {"generic-api-key"},
                ),
                ("emulator-values-outside-compose", "other.yaml", compose, {"generic-api-key"}),
            ]
        )
    for name, filename, content, expected_rules in cases:
        with tempfile.TemporaryDirectory(prefix=f"{scanner}-{name}-") as temporary:
            directory = Path(temporary)
            (directory / filename).write_text(content, encoding="utf-8")
            scan(scanner, directory, expected_rules)
        print(f"{scanner}: {name} passed")


if __name__ == "__main__":
    main()
