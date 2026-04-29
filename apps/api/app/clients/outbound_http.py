"""Outbound HTTP client wrapper with sim-egress safety gate.

Constitutional NON-NEGOTIABLE #1: no irreversible real-world action without human
authorisation. This wrapper inspects the current TenantContext and refuses any outbound
request originating from a simulation tenant (tenant_id prefixed with "sim-"). Every
refusal is recorded as a SimSyntheticDelivery audit entry.

See specs/024-simulation-control-chat/spec.md FR-019..FR-021.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any, Literal

import httpx
from app.core.tenant_context import TenantContext, get_current_tenant
from app.services.simulation.synthetic_delivery_service import (
    SyntheticDeliveryService,
    get_synthetic_delivery_service,
)

logger = logging.getLogger(__name__)

SimChannel = Literal["sms", "email", "broadcast", "social", "cap_push", "http"]


class SimEgressBlocked(Exception):
    """Raised when a simulation tenant attempts an outbound public-facing call."""

    def __init__(self, *, tenant_id: str, url: str, channel: SimChannel) -> None:
        super().__init__(f"Sim egress blocked for tenant={tenant_id} channel={channel} url={url}")
        self.tenant_id = tenant_id
        self.url = url
        self.channel = channel


class SimAwareHttpClient:
    """Thin wrapper around ``httpx.AsyncClient`` with a simulation-egress interlock."""

    def __init__(
        self,
        *,
        channel: SimChannel = "http",
        delivery_service: SyntheticDeliveryService | None = None,
        tenant_resolver=None,
        timeout: float = 10.0,
    ) -> None:
        self._channel = channel
        self._delivery = delivery_service or get_synthetic_delivery_service()
        self._tenant_resolver = tenant_resolver or get_current_tenant
        self._client = httpx.AsyncClient(timeout=timeout)

    async def __aenter__(self) -> SimAwareHttpClient:
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self._client.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _guard(self, method: str, url: str, payload: Any = None) -> None:
        try:
            tenant = self._tenant_resolver()
        except LookupError:
            return
        if not isinstance(tenant, TenantContext):
            return
        if not tenant.is_simulation:
            return
        payload_bytes = _serialize_payload(payload)
        await self._delivery.record_blocked(
            tenant_id=tenant.tenant_id,
            simulation_id=tenant.tenant_id,
            channel=self._channel,
            audience=url,
            payload_bytes=payload_bytes,
            block_reason="http-wrapper-gate",
            intended_url=url,
        )
        logger.warning(
            "sim.egress.blocked tenant=%s channel=%s method=%s url=%s",
            tenant.tenant_id,
            self._channel,
            method,
            url,
        )
        raise SimEgressBlocked(tenant_id=tenant.tenant_id, url=url, channel=self._channel)

    async def get(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self._client.get(url, **kwargs)

    async def post(self, url: str, *, json: Any = None, data: Any = None, **kwargs: Any) -> httpx.Response:
        await self._guard("POST", url, json or data)
        return await self._client.post(url, json=json, data=data, **kwargs)

    async def put(self, url: str, *, json: Any = None, data: Any = None, **kwargs: Any) -> httpx.Response:
        await self._guard("PUT", url, json or data)
        return await self._client.put(url, json=json, data=data, **kwargs)

    async def patch(self, url: str, *, json: Any = None, data: Any = None, **kwargs: Any) -> httpx.Response:
        await self._guard("PATCH", url, json or data)
        return await self._client.patch(url, json=json, data=data, **kwargs)

    async def delete(self, url: str, **kwargs: Any) -> httpx.Response:
        await self._guard("DELETE", url, None)
        return await self._client.delete(url, **kwargs)


def _serialize_payload(payload: Any) -> bytes:
    if payload is None:
        return b""
    if isinstance(payload, (bytes, bytearray)):
        return bytes(payload)
    if isinstance(payload, str):
        return payload.encode("utf-8")
    try:
        import json

        return json.dumps(payload, default=str, sort_keys=True).encode("utf-8")
    except Exception:  # pragma: no cover
        return repr(payload).encode("utf-8")


def hash_payload(payload: Any) -> str:
    return hashlib.sha256(_serialize_payload(payload)).hexdigest()
