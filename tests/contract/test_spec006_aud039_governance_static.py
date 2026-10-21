from __future__ import annotations

import json
import re
from pathlib import Path

AZURE_YAML = Path("azure.yaml")
ACTIVE_BICEP = Path("infra/main.bicep")
LEGACY_BICEP = Path("infra/bicep/main.bicep")
LEGACY_MODULE_DIR = Path("infra/bicep/modules")
GOV_MD = Path("specs/006-data-ingestion-storage/04-governance-constraints.md")
GOV_JSON = Path("specs/006-data-ingestion-storage/04-governance-constraints.json")


def test_governance_constraints_files_exist_and_are_blocked() -> None:
    assert GOV_MD.exists()
    assert GOV_JSON.exists()

    payload = json.loads(GOV_JSON.read_text(encoding="utf-8"))
    assert payload["status"] == "GOVERNANCE-BLOCKED"
    assert payload["discovery"]["portalParity"] == "UNVERIFIED"
    assert payload["discovery"]["managementGroupInheritedAssignments"] == "UNVERIFIED"
    assert payload["discovery"]["subscriptionScopedAssignments"] == 0
    assert payload["discovery"]["restApiTotalAssignments"] == 0


def test_governance_markdown_contains_required_blocked_discovery_context() -> None:
    text = GOV_MD.read_text(encoding="utf-8")
    assert "## Discovery Source" in text
    assert "Status: GOVERNANCE-BLOCKED" in text
    assert "Portal Validation: UNVERIFIED" in text
    assert "Subscription: AI Impact Analyzer" in text


def test_authoritative_iac_path_is_azure_yaml_to_infra_main() -> None:
    text = AZURE_YAML.read_text(encoding="utf-8")
    assert re.search(r"(?m)^infra:\s*$", text)
    assert re.search(r"(?m)^\s*path:\s*infra\s*$", text)
    assert re.search(r"(?m)^\s*module:\s*main\s*$", text)
    assert ACTIVE_BICEP.exists()
    assert LEGACY_BICEP.exists()


def test_static_drift_detection_for_worker_scaling_probe_and_orphan_modules() -> None:
    active_text = ACTIVE_BICEP.read_text(encoding="utf-8")
    assert "minReplicas: 2" in active_text
    assert "maxReplicas: 6" in active_text

    referenced_paths = set(re.findall(r"module\s+\w+\s+'([^']+)'", active_text))
    legacy_modules = [path for path in LEGACY_MODULE_DIR.glob("*.bicep")]
    orphaned = [path for path in legacy_modules if f"bicep/modules/{path.name}" not in referenced_paths]

    assert orphaned, "expected at least one legacy module to be unreferenced from infra/main.bicep"

    payload = json.loads(GOV_JSON.read_text(encoding="utf-8"))
    findings = payload["authoritativeIac"]["staticFindings"]
    assert findings["probeConfiguration"] == "missing-or-unverified"
    assert findings["queueScalingConfiguration"] == "missing-or-unverified"
    assert findings["orphanLegacyModulesDetected"] is True
