from app.api.data_sources import router as data_sources_router
from app.api.dead_letters import router as dead_letters_router
from app.api.governance import router as governance_router
from app.api.handoffs import router as handoffs_router
from app.api.health import router as health_router
from app.api.routes.ai_analysis import router as ai_analysis_router
from app.api.routes.aiims import level_router as aiims_level_router
from app.api.routes.aiims import router as aiims_router
from app.api.routes.alerts import router as alerts_router
from app.api.routes.dead_letters import router as dead_letters_mgmt_router
from app.api.routes.emergency_plans import router as emergency_plans_router
from app.api.routes.evacuation import router as evacuation_router
from app.api.routes.frameworks import router as frameworks_router
from app.api.routes.governance_dashboard import router as governance_dashboard_router
from app.api.routes.health import router as aidr_health_router
from app.api.routes.incidents import router as incidents_router
from app.api.routes.incidents_map import router as incidents_map_router
from app.api.routes.jurisdictions import router as jurisdictions_router
from app.api.routes.lessons import router as lessons_router
from app.api.routes.me_frameworks import router as me_frameworks_router
from app.api.routes.organisations import router as organisations_router
from app.api.routes.personas import router as personas_router
from app.api.routes.pprr import context_router as pprr_context_router
from app.api.routes.pprr import router as pprr_router
from app.api.routes.radius_lookup import router as radius_lookup_router
from app.api.routes.recommendations import router as recommendations_router
from app.api.routes.recovery import router as recovery_router
from app.api.routes.recovery_catalogue import router as recovery_catalogue_router
from app.api.routes.scenarios import router as scenarios_router
from app.api.routes.signals import router as signals_router
from app.api.routes.simulation_chat import router as simulation_chat_router
from app.api.routes.simulation_playback import router as simulation_playback_router
from app.api.routes.simulations import router as simulations_router
from app.api.routes.tasks import router as tasks_router
from app.api.routes.warning_chain import router as warning_chain_router
from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(signals_router)
api_router.include_router(incidents_router)
api_router.include_router(incidents_map_router)
api_router.include_router(recommendations_router)
api_router.include_router(alerts_router)
api_router.include_router(personas_router)
api_router.include_router(tasks_router)
api_router.include_router(organisations_router)
api_router.include_router(frameworks_router)
api_router.include_router(jurisdictions_router)
api_router.include_router(scenarios_router)
api_router.include_router(simulations_router)
api_router.include_router(simulation_playback_router)
api_router.include_router(simulation_chat_router)
api_router.include_router(handoffs_router)
api_router.include_router(dead_letters_router)
api_router.include_router(health_router)
api_router.include_router(data_sources_router)
api_router.include_router(governance_router)
api_router.include_router(warning_chain_router)
api_router.include_router(aiims_router)
api_router.include_router(aiims_level_router)
api_router.include_router(evacuation_router)
api_router.include_router(lessons_router)
api_router.include_router(pprr_router)
api_router.include_router(pprr_context_router)
api_router.include_router(recovery_router)
api_router.include_router(emergency_plans_router)
api_router.include_router(me_frameworks_router)
api_router.include_router(recovery_catalogue_router)
api_router.include_router(ai_analysis_router)
api_router.include_router(aidr_health_router)
api_router.include_router(governance_dashboard_router)
api_router.include_router(dead_letters_mgmt_router)
api_router.include_router(radius_lookup_router)
