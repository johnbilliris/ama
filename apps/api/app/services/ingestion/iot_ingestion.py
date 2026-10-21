from app.core.auth import AuthenticatedPrincipal
from app.services.governance_registry import GovernanceRegistryService
from app.services.ingestion.authoritative_ingestion import AuthoritativeIngestionService
from app.services.ingestion.pipeline_base import IngestionProcessingResult
from app.validators.signal_envelope import SignalEnvelope

from packages.domain.src.domain.models.data_source import DataSource


class IoTIngestionService:
    def __init__(self, registry: GovernanceRegistryService | None = None) -> None:
        self._registry = registry

    async def ingest(
        self,
        envelope: SignalEnvelope,
        *,
        principal: AuthenticatedPrincipal,
        tenant_id: str,
        source: DataSource | None = None,
    ) -> IngestionProcessingResult:
        return AuthoritativeIngestionService(registry=self._registry).ingest(
            envelope,
            source=source,
        )
