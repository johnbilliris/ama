import logging
import os

from app.api.router import api_router
from app.core.settings import get_settings
from app.middleware.error_handler import add_error_handler_middleware
from app.middleware.resilience import add_resilience_middleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Autonomous Disaster Response Coordination Hub",
        version="0.1.0",
        docs_url=f"{settings.api_prefix}/docs",
        openapi_url=f"{settings.api_prefix}/openapi.json",
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

    from app.middleware.auth_middleware import add_auth_middleware
    from app.middleware.tenant_middleware import add_tenant_middleware

    add_tenant_middleware(app)
    add_auth_middleware(app)

    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()
