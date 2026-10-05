import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from app.api.dependencies.governance_composition import initialize_governance_composition
from app.api.dependencies.simulation_composition import simulation_repository_proxy
from app.api.router import api_router
from app.core.env_contract import EnvironmentContractError, validate_runtime_environment
from app.core.settings import get_settings
from app.middleware.activation_mutex import activation_mutex_lifespan
from app.middleware.error_handler import add_error_handler_middleware
from app.middleware.resilience import add_resilience_middleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.console_logging import configure_console_logging

if os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING"):
    try:
        from azure.identity import ManagedIdentityCredential
        from azure.monitor.opentelemetry import configure_azure_monitor

        configure_azure_monitor(
            enable_live_metrics=True,
            credential=ManagedIdentityCredential(),
        )
    except Exception:
        logging.getLogger(__name__).warning("Failed to configure Azure Monitor", exc_info=True)

configure_console_logging()


@asynccontextmanager
async def _composed_lifespan(app: FastAPI) -> AsyncIterator[None]:
    from app.services.evidence._clients import close_registry, initialize_registry

    try:
        validate_runtime_environment()
    except EnvironmentContractError as exc:
        raise RuntimeError(f"Startup blocked by environment contract: {exc}") from exc
    initialize_governance_composition(app)
    initialize_registry()
    try:
        async with activation_mutex_lifespan(app):
            yield
    finally:
        close_registry()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Autonomous Disaster Response Coordination Hub",
        version="0.1.0",
        docs_url=f"{settings.api_prefix}/docs",
        openapi_url=f"{settings.api_prefix}/openapi.json",
        lifespan=_composed_lifespan,
    )
    add_error_handler_middleware(app)
    add_resilience_middleware(app)

    # CORS — must be added before auth/tenant middleware so preflight OPTIONS
    # requests are answered before they reach authentication checks.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
    )

    from app.middleware.audit_appender import add_audit_appender_middleware
    from app.middleware.auth_middleware import add_auth_middleware
    from app.middleware.classifier_gateway import add_classifier_gateway_middleware
    from app.middleware.entra_auth import add_entra_auth_middleware
    from app.middleware.rate_limit_audit import add_rate_limit_audit_middleware
    from app.middleware.rbac_check import add_rbac_check_middleware
    from app.middleware.tenant_middleware import add_tenant_middleware
    from app.services.evidence.middleware import add_evidence_contract_middleware

    add_tenant_middleware(app, simulation_repository=simulation_repository_proxy())
    add_auth_middleware(app)

    # spec-035 production-auth stack. The full stack activates only when
    # AMA_ENABLE_PRODUCTION_AUTH=1. Entra + RBAC can also activate narrowly for
    # the incident map without applying classifier/rate-limit behavior to other
    # dev routes. In Starlette the LAST registered middleware is the OUTERMOST.
    #
    # Runtime order (outer → inner):
    #   audit_appender → classifier_gateway → entra_auth → rbac_check
    #   → rate_limit_audit → route handler
    add_rate_limit_audit_middleware(app)
    add_rbac_check_middleware(app)
    add_entra_auth_middleware(app)
    add_classifier_gateway_middleware(app)
    add_audit_appender_middleware(app)
    add_evidence_contract_middleware(app)

    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()
