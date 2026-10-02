from app.services.ingestion.pipeline_status_store import get_pipeline_status_store
from fastapi import APIRouter

router = APIRouter(prefix="/ingestion", tags=["ingestion"])

_status_store = get_pipeline_status_store()


def register_pipeline_status(status: dict) -> None:
    _status_store.record(status)


@router.get("/status")
async def get_ingestion_status() -> dict:
    return _status_store.summary()
