from app.api.data_sources import router as data_sources_router
from app.api.dead_letters import router as dead_letters_router
from app.api.governance import router as governance_router
from app.api.handoffs import router as handoffs_router
from app.api.health import router as health_router
from app.api.routes.agents import router as agents_router
from app.api.routes.ai_analysis import router as ai_analysis_router
from app.api.routes.aiims import level_router as aiims_level_router
from app.api.routes.aiims import router as aiims_router
from app.api.routes.alerts import router as alerts_router
from app.api.routes.audit import router as audit_router
from app.api.routes.dead_letters import router as dead_letters_mgmt_router
from app.api.routes.emergency_plans import router as emergency_plans_router
from app.api.routes.evacuation import router as evacuation_router
from app.api.routes.frameworks import router as frameworks_router
from app.api.routes.governance.evidence_pack import router as evidence_pack_router
from app.api.routes.governance_dashboard import router as governance_dashboard_router
from app.api.routes.health import router as aidr_health_router
from app.api.routes.i18n import router as i18n_router
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
from app.api.routes.recovery_handover import router as recovery_handover_router
from app.api.routes.scenarios import router as scenarios_router
from app.api.routes.signals import router as signals_router
from app.api.routes.simulation_chat import router as simulation_chat_router
from app.api.routes.simulation_playback import router as simulation_playback_router
from app.api.routes.simulations import router as simulations_router
from app.api.routes.simulations_036 import router as simulations_036_router
from app.api.routes.tasks import router as tasks_router
from app.api.routes.warning_chain import router as warning_chain_router
from app.api.routes.workflow_runs import router as workflow_runs_router
from app.middleware import test_support_guard
from fastapi import APIRouter

# Lazy import for eval module to keep its repo deps optional
try:
    from app.api.routes.eval.router import register_subroutes as _register_eval_subroutes
    from app.api.routes.eval.router import router as eval_router

    _register_eval_subroutes()
    _EVAL_AVAILABLE = True
except Exception:  # pragma: no cover
    _EVAL_AVAILABLE = False

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
api_router.include_router(simulations_036_router)
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
api_router.include_router(recovery_handover_router)
api_router.include_router(emergency_plans_router)
api_router.include_router(me_frameworks_router)
api_router.include_router(recovery_catalogue_router)
api_router.include_router(ai_analysis_router)
api_router.include_router(aidr_health_router)
api_router.include_router(governance_dashboard_router)
# Spec-037 — Capstone Evidence Pack read-only API (FR-021).
api_router.include_router(evidence_pack_router)
api_router.include_router(dead_letters_mgmt_router)
api_router.include_router(radius_lookup_router)
api_router.include_router(workflow_runs_router)
api_router.include_router(i18n_router)
api_router.include_router(agents_router)
api_router.include_router(audit_router)

if _EVAL_AVAILABLE:
    api_router.include_router(eval_router)

# spec 034 (T009) — test-support router gated by dual-guard. The router is
# registered ONLY when both guards pass (env=dev|test AND AMA_TEST_SUPPORT=1);
# otherwise direct requests collapse to a stock 404.
test_support_guard.log_activation_status()
if test_support_guard.is_enabled():
    from app.api.routes.audit_list import router as audit_list_router
    from app.api.routes.outcome_evaluator import router as outcome_evaluator_router
    from app.api.routes.test_support import router as test_support_router

    api_router.include_router(test_support_router)
    # spec 034 (T178, T179) cycle-1 — outcome evaluator + audit-list under
    # the same dual-guard. FR-028 + FR-029 routable surface.
    api_router.include_router(outcome_evaluator_router)
    api_router.include_router(audit_list_router)


# spec-035 T028 — production-reachable registration block (FR-009).
# Layered ADDITIVELY over the dual-guarded test-support shard per OOS-006:
# when AMA_ENABLE_PRODUCTION_AUTH=1 we mount the SAME outcome_evaluator +
# audit_list routers without the test-support guard. The middleware stack
# wired in main.py (entra_auth, rbac_check, classifier_gateway,
# rate_limit_audit, audit_appender) is responsible for protecting them.
import os as _os  # noqa: E402

if _os.environ.get("AMA_ENABLE_PRODUCTION_AUTH", "0") == "1" and not test_support_guard.is_enabled():
    from app.api.routes.audit_list import router as audit_list_router  # type: ignore[no-redef]
    from app.api.routes.auth_whoami import router as auth_whoami_router
    from app.api.routes.offline_replay import router as offline_replay_router
    from app.api.routes.outcome_evaluator import router as outcome_evaluator_router  # type: ignore[no-redef]

    api_router.include_router(outcome_evaluator_router)
    api_router.include_router(audit_list_router)
    api_router.include_router(auth_whoami_router)
    api_router.include_router(offline_replay_router)
elif _os.environ.get("AMA_ENABLE_PRODUCTION_AUTH", "0") == "1":
    # Test-support is already mounting outcome/audit; only add the spec-035
    # net-new routes so we don't double-register.
    from app.api.routes.auth_whoami import router as auth_whoami_router
    from app.api.routes.offline_replay import router as offline_replay_router

    api_router.include_router(auth_whoami_router)
    api_router.include_router(offline_replay_router)

# Spec-035 follow-up: when neither AMA_TEST_SUPPORT nor
# AMA_ENABLE_PRODUCTION_AUTH is set, the canonical outcome_evaluator +
# audit_list routers are not mounted. The IC Approval Card workspace panel
# still calls ``POST /outcomes/sc-{id}/evaluate`` and
# ``GET /audit/list?correlation_id=...`` though. Mount a workspace-shaped
# fallback so the panel renders a defensible response instead of 404. The
# guard ensures we only ever mount this when both gated branches above are
# inactive, so there is no path-shadowing risk.
if _os.environ.get("AMA_ENABLE_PRODUCTION_AUTH", "0") != "1" and not test_support_guard.is_enabled():
    from app.api.routes.workspace_bridges import router as workspace_bridges_router

    api_router.include_router(workspace_bridges_router)
