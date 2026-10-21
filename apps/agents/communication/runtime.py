"""Composition root for the standalone Communication Agent service."""

from __future__ import annotations

import logging
import os
from importlib import import_module
from typing import TYPE_CHECKING

from common.foundry_query_embedder import build_query_embedder
from communication.agent import create_app
from communication.approval import ApprovalWorkflow, ServiceBusApprovalPublisher
from communication.audit import AuditWriter
from communication.config import CommunicationConfig
from communication.dedup import HandoffDeduplicator
from communication.delivery import MultiChannelDeliveryService, NotificationHubRestClient, SmsDeliveryClient
from communication.health import DependencyHealthReporter
from communication.models import PublicAlert
from communication.pipeline import CommunicationProcessingPipeline
from communication.repository import CommunicationAlertRepository
from communication.segmentation import AudienceSegmenter
from communication.telemetry import configure_telemetry
from communication.templates import TemplateLoader
from communication.translator import MultilingualTranslator
from communication.versioning import VersionCounter
from fastapi import FastAPI

from apps.console_logging import configure_console_logging, uvicorn_log_config

if TYPE_CHECKING:
    from azure.cosmos import ContainerProxy

logger = logging.getLogger(__name__)


def build_application(config: CommunicationConfig | None = None) -> FastAPI:
    """Compose the complete draft, approval, and delivery runtime."""
    runtime_config = config or CommunicationConfig()
    configure_telemetry()
    containers = _resolve_containers(runtime_config)
    template_loader = TemplateLoader()
    alert_repository = CommunicationAlertRepository(containers.get("alerts"))
    version_counter = VersionCounter(config=runtime_config, cosmos_container=containers.get("alerts"))
    approval_publisher = (
        ServiceBusApprovalPublisher(
            runtime_config.service_bus_namespace,
            runtime_config.commander_approval_queue,
        )
        if runtime_config.service_bus_namespace
        else None
    )
    audit_writer = AuditWriter(config=runtime_config, cosmos_client=containers.get("decisions"))
    approval_workflow = ApprovalWorkflow(
        config=runtime_config,
        service_bus_client=approval_publisher,
        alert_repository=alert_repository,
        version_counter=version_counter,
        audit_writer=audit_writer,
    )
    sms_client = _build_sms_client(runtime_config)
    push_client = (
        NotificationHubRestClient(
            runtime_config.notification_hub_url,
            runtime_config.notification_hub_sas_token,
            runtime_config.eas_timeout_seconds,
        )
        if runtime_config.notification_hub_url and runtime_config.notification_hub_sas_token
        else None
    )
    delivery_service = MultiChannelDeliveryService(
        config=runtime_config,
        sms_client=sms_client,
        push_client=push_client,
        approval_resolver=lambda tenant_id, alert_id, version: _resolve_approved_alert(
            alert_repository,
            tenant_id,
            alert_id,
            version,
        ),
    )
    pipeline = CommunicationProcessingPipeline(
        config=runtime_config,
        deduplicator=HandoffDeduplicator(window_minutes=runtime_config.handoff_dedup_window_minutes),
        template_loader=template_loader,
        translator=MultilingualTranslator(
            config=runtime_config,
            template_loader=template_loader,
            embedding_client=build_query_embedder(),
        ),
        segmenter=AudienceSegmenter(config=runtime_config),
        version_counter=version_counter,
        audit_writer=audit_writer,
        delivery_service=delivery_service,
        alert_repository=alert_repository,
        incident_store=containers.get("incidents"),
        recommendation_store=containers.get("recommendations"),
        assessment_store=containers.get("assessments"),
        approval_workflow=approval_workflow,
    )
    health_reporter = DependencyHealthReporter(
        {
            "cosmos_connectivity": (
                (lambda: containers["alerts"].read()) if containers.get("alerts") is not None else None,
                runtime_config.environment in {"staging", "production"},
            ),
            "llm_connectivity": (None, False),
            "sms_service_status": (None, False),
            "push_service_status": (None, False),
            "broadcast_endpoint_status": (None, False),
        }
    )
    return create_app(
        config=runtime_config,
        pipeline=pipeline,
        approval_workflow=approval_workflow,
        audit_writer=audit_writer,
        health_reporter=health_reporter,
    )


def _resolve_containers(config: CommunicationConfig) -> dict[str, ContainerProxy]:
    if not config.cosmos_endpoint:
        if config.environment in {"staging", "production"}:
            raise RuntimeError("COSMOS_ENDPOINT is required outside development and test")
        return {}

    from azure.cosmos import CosmosClient
    from azure.identity import DefaultAzureCredential

    client_id = os.environ.get("AZURE_CLIENT_ID")
    credential = DefaultAzureCredential(managed_identity_client_id=client_id) if client_id else DefaultAzureCredential()
    client = CosmosClient(config.cosmos_endpoint, credential=credential)
    database = client.get_database_client(config.cosmos_database_name)
    return {
        "alerts": database.get_container_client(config.public_alerts_container_name),
        "decisions": database.get_container_client(config.communication_decisions_container_name),
        "incidents": database.get_container_client(config.incidents_container_name),
        "recommendations": database.get_container_client(config.recommendations_container_name),
        "assessments": database.get_container_client(config.assessments_container_name),
    }


def _build_sms_client(config: CommunicationConfig) -> SmsDeliveryClient | None:
    if not config.sms_endpoint:
        return None
    from azure.identity import DefaultAzureCredential

    SmsClient = import_module("azure.communication.sms").SmsClient
    client_id = os.environ.get("AZURE_CLIENT_ID")
    credential = DefaultAzureCredential(managed_identity_client_id=client_id) if client_id else DefaultAzureCredential()
    return SmsClient(endpoint=config.sms_endpoint, credential=credential)


def _resolve_approved_alert(
    repository: CommunicationAlertRepository,
    tenant_id: str,
    alert_id: str,
    version: int,
) -> PublicAlert | None:
    alert = repository.get(tenant_id, alert_id)
    if alert is None or alert.tenant_id != tenant_id or alert.version != version:
        return None
    return alert


def main() -> None:
    """Run the configured Communication Agent HTTP service."""
    uvicorn = import_module("uvicorn")
    configure_console_logging()
    port = int(os.environ.get("PORT", "8084"))
    logger.info("Communication Agent service starting on port %d", port)
    uvicorn.run(
        build_application(),
        host="0.0.0.0",
        port=port,
        log_level="info",
        log_config=uvicorn_log_config(),
    )


__all__ = ["build_application", "main"]
