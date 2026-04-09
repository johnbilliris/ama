from fastapi import APIRouter

router = APIRouter(prefix="/ingestion", tags=["ingestion"])

_pipeline_statuses: list[dict] = []


def register_pipeline_status(status: dict) -> None:
    _pipeline_statuses.append(status)


@router.get("/status")
async def get_ingestion_status() -> dict:
    total_signals = sum(p.get("signalsIngested", 0) for p in _pipeline_statuses)
    degraded = sum(1 for p in _pipeline_statuses if p.get("circuitBreakerState") == "open")
    return {
        "pipelines": _pipeline_statuses,
        "totalSignalsLastHour": total_signals,
        "degradedSources": degraded,
    }
