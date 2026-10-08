from __future__ import annotations

from datetime import datetime
from typing import Protocol

from packages.domain.src.domain.models.signal import Signal


class SignalReadWrite(Protocol):
    async def query_unassociated(
        self,
        jurisdiction_id: str,
        since: datetime | None = None,
        *,
        scope: str,
        owning_agency_id: str | None = None,
        allowed_jurisdictions: set[str] | None = None,
        include_all_jurisdictions: bool = False,
    ) -> list[Signal]: ...

    async def update_incident_id(
        self,
        signal_id: str,
        incident_id: str,
        *,
        scope: str,
        expected_incident_id: str | None = None,
    ) -> bool: ...
