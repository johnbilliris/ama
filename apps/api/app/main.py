from fastapi import FastAPI

from app.api.router import api_router
from app.core.settings import get_settings
from app.middleware.resilience import add_resilience_middleware


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Autonomous Disaster Response Coordination Hub",
        version="0.1.0",
        docs_url=f"{settings.api_prefix}/docs",
        openapi_url=f"{settings.api_prefix}/openapi.json",
    )
    add_resilience_middleware(app)
    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()
