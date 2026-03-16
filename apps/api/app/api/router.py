from fastapi import APIRouter

from app.api.dead_letters import router as dead_letters_router
from app.api.handoffs import router as handoffs_router
from app.api.health import router as health_router
from app.api.routes.alerts import router as alerts_router
from app.api.routes.frameworks import router as frameworks_router
from app.api.routes.incidents import router as incidents_router
from app.api.routes.organisations import router as organisations_router
from app.api.routes.personas import router as personas_router
from app.api.routes.recommendations import router as recommendations_router
from app.api.routes.scenarios import router as scenarios_router
from app.api.routes.signals import router as signals_router
from app.api.routes.tasks import router as tasks_router

api_router = APIRouter()
api_router.include_router(signals_router)
api_router.include_router(incidents_router)
api_router.include_router(recommendations_router)
api_router.include_router(alerts_router)
api_router.include_router(personas_router)
api_router.include_router(tasks_router)
api_router.include_router(organisations_router)
api_router.include_router(frameworks_router)
api_router.include_router(scenarios_router)
api_router.include_router(handoffs_router)
api_router.include_router(dead_letters_router)
api_router.include_router(health_router)

