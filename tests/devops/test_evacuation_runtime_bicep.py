"""Provisioning contract for the dedicated evacuation Container App runtime."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "infra" / "bicep" / "modules" / "evacuation-runtime.bicep"
MAIN_PATH = ROOT / "infra" / "main.bicep"
AZURE_YAML_PATH = ROOT / "azure.yaml"


@pytest.fixture(scope="module")
def module_text() -> str:
    return MODULE_PATH.read_text(encoding="utf-8")


def test_runtime_uses_pinned_avms_and_only_approved_raw_storage(
    module_text: str,
) -> None:
    assert "br/public:avm/res/app/container-app:0.23.0" in module_text
    assert "br/public:avm/res/managed-identity/user-assigned-identity:0.6.0" in module_text
    assert "br/public:avm/res/service-bus/namespace:0.17.1" in module_text
    assert "br/public:avm/res/document-db/database-account/sql-database/container:0.2.1" in module_text
    assert "br/public:avm/res/document-db/database-account/sql-role-assignment:0.2.2" in module_text
    assert "br/public:avm/res/storage/storage-account/file-service/share:0.1.3" in module_text
    raw_types = {
        line.split("'")[1].split("@")[0]
        for line in module_text.splitlines()
        if line.lstrip().startswith("resource ") and "@" in line
    }
    assert raw_types == {
        "Microsoft.App/managedEnvironments",
        "Microsoft.App/managedEnvironments/storages",
    }


def test_runtime_provisions_scoped_cosmos_and_queue(module_text: str) -> None:
    for container in (
        "evacuation-plans",
        "evacuation-decisions",
        "hazard-assessments",
        "risk-recommendations",
    ):
        assert f"  '{container}'" in module_text
    assert "paths: ['/incident_scope_key']" in module_text
    assert "var queueName = 'evacuation-handoffs'" in module_text
    assert "name: queueName" in module_text
    assert "maxDeliveryCount: 3" in module_text
    assert "Azure Service Bus Data Receiver" in module_text
    assert "Azure Service Bus Data Sender" in module_text
    for role_id in (
        "7f951dda-4ed3-4680-a7ca-43fe172d538d",
        "3913510d-42f4-4e42-8a64-420c390055eb",
        "5e0bd9bd-7b93-4f28-af87-19fc36ad61bd",
    ):
        assert role_id in module_text


def test_container_runs_evacuation_on_8082_with_real_probes(
    module_text: str,
) -> None:
    assert "name: 'AMA_AGENTS_RUNTIME'" in module_text
    assert "value: 'evacuation'" in module_text
    assert "name: 'PORT'" in module_text
    assert "value: '8082'" in module_text
    assert "name: 'COSMOS_DATABASE_NAME'" in module_text
    assert "name: 'EVACUATION_PLANS_CONTAINER_NAME'" in module_text
    assert "name: 'EVACUATION_DECISIONS_CONTAINER_NAME'" in module_text
    assert "name: 'AZURE_SERVICEBUS_NAMESPACE'" in module_text
    assert "name: 'EVACUATION_HANDOFFS_QUEUE'" in module_text
    assert "ingressTargetPort: 8082" in module_text
    assert "path: '/live'" in module_text
    assert "path: '/ready'" in module_text
    assert "port: 8082" in module_text


def test_keda_uses_managed_identity_and_queue_threshold_20(
    module_text: str,
) -> None:
    assert "type: 'azure-servicebus'" in module_text
    assert "var queueName = 'evacuation-handoffs'" in module_text
    assert "queueName: queueName" in module_text
    assert "messageCount: '20'" in module_text
    assert "identity: evacuationIdentity.outputs.resourceId" in module_text
    assert "minReplicas: 1" in module_text
    assert "maxReplicas: 4" in module_text


def test_runtime_mounts_durable_audit_wal_and_assets(module_text: str) -> None:
    assert "var auditStorageName = 'evacuation-audit-wal'" in module_text
    assert "name: auditStorageName" in module_text
    assert "storageType: 'AzureFile'" in module_text
    assert "mountPath: '/app/var/evacuation-agent'" in module_text
    assert "AUDIT_BUFFER_FILE_PATH" in module_text
    assert "/app/var/evacuation-agent/audit-buffer.jsonl" in module_text
    assert "ROAD_NETWORK_FILE_PATH" in module_text
    assert "data/road-networks/far-north-qld-sample.json" in module_text
    assert "POPULATION_DATA_FILE_PATH" in module_text
    assert "data/population/sample-population.json" in module_text


def test_main_and_azd_deploy_dedicated_evacuation_service() -> None:
    main_text = MAIN_PATH.read_text(encoding="utf-8")
    azure_yaml = AZURE_YAML_PATH.read_text(encoding="utf-8")
    assert "param evacuationImage string" in main_text
    assert "module evacuationRuntime './bicep/modules/evacuation-runtime.bicep'" in main_text
    assert "output AZURE_EVACUATION_SERVICE_ENDPOINT" in main_text
    assert "output SERVICE_EVACUATION_ENDPOINT_URL" in main_text
    assert "\n  evacuation:\n" in azure_yaml
    assert "project: ./apps/agents" in azure_yaml
    assert "path: ./Dockerfile" in azure_yaml
