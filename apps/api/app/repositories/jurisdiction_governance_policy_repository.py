"""JurisdictionGovernancePolicy repository (spec-032 FR-AG02, T701).

Cosmos-backed repository for ``jurisdiction_governance_policies`` (PK ``/jurisdiction_code``).
Auto-connects when ``COSMOS_ENDPOINT`` env var is set (per the repo convention
documented in stored memory). Falls back to in-memory for unit tests.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from azure.identity import DefaultAzureCredential

from packages.domain.src.domain.models.jurisdiction_governance_policy import (
    JurisdictionGovernancePolicy,
)

logger = logging.getLogger(__name__)


class JurisdictionGovernancePolicyRepository:
    """Read + write jurisdiction governance policies from Cosmos.

    Used by:
      - apps/api/app/api/routes/jurisdictions.py (read endpoint per OpenAPI delta)
      - apps/agents/common/lifecycle/autonomy_eval.py (lookup callable)
    """

    def __init__(self, container: Any | None = None) -> None:
        self._container = container if container is not None else self._build_container()
        self._memory: dict[str, JurisdictionGovernancePolicy] = {}

    @staticmethod
    def _build_container() -> Any | None:
        endpoint = os.getenv("COSMOS_ENDPOINT")
        database = os.getenv("COSMOS_DATABASE", "ama")
        if not endpoint:
            return None
        try:
            from azure.cosmos import CosmosClient

            client = CosmosClient(endpoint, credential=DefaultAzureCredential())
            db = client.get_database_client(database)
            return db.get_container_client("jurisdiction_governance_policies")
        except Exception:  # noqa: BLE001
            logger.exception("Cosmos jurisdiction_governance_policies init failed; using in-memory")
            return None

    def get(self, jurisdiction_code: str) -> JurisdictionGovernancePolicy | None:
        if self._container is None:
            return self._memory.get(jurisdiction_code)
        try:
            doc = self._container.read_item(item=jurisdiction_code, partition_key=jurisdiction_code)
            return JurisdictionGovernancePolicy(
                **{k: v for k, v in doc.items() if not k.startswith("_")}
            )
        except Exception:  # noqa: BLE001
            return None

    def upsert(self, policy: JurisdictionGovernancePolicy) -> JurisdictionGovernancePolicy:
        if self._container is None:
            self._memory[policy.jurisdiction_code] = policy
            return policy
        doc: dict[str, Any] = policy.model_dump(mode="json")
        doc["id"] = policy.jurisdiction_code
        self._container.upsert_item(doc)
        return policy

    def list_all(self) -> list[JurisdictionGovernancePolicy]:
        if self._container is None:
            return list(self._memory.values())
        try:
            return [
                JurisdictionGovernancePolicy(
                    **{k: v for k, v in item.items() if not k.startswith("_")}
                )
                for item in self._container.query_items(
                    query="SELECT * FROM c", enable_cross_partition_query=True
                )
            ]
        except Exception:  # noqa: BLE001
            logger.exception("Cosmos query failed")
            return []
