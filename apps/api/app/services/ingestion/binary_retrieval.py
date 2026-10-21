from __future__ import annotations

import asyncio
import ftplib
import hashlib
import mimetypes
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

import httpx


class BinaryRetrievalService:
    def __init__(
        self,
        *,
        signal_repository: Any,
        blob_storage: Any,
        allowed_hosts: set[str],
        allowed_schemes: set[str] | None = None,
        timeout_seconds: int = 30,
        max_bytes: int = 25 * 1024 * 1024,
    ) -> None:
        self._signal_repository = signal_repository
        self._blob_storage = blob_storage
        self._allowed_hosts = {h.strip().lower() for h in allowed_hosts if h and h.strip()}
        self._allowed_schemes = allowed_schemes or {"https", "http", "ftp"}
        self._timeout_seconds = timeout_seconds
        self._max_bytes = max_bytes

    async def retrieve_for_signal(
        self,
        *,
        scope: str,
        signal_id: str,
        incident_id: str | None = None,
    ) -> str:
        signal = await self._signal_repository.get_signal(scope, signal_id)
        if signal is None:
            raise ValueError("signal not found")

        payload = signal.get("payload") if isinstance(signal, dict) else None
        if not isinstance(payload, dict):
            raise ValueError("signal payload missing")

        source_uri = str(payload.get("binaryAssetUri", "")).strip()
        if not source_uri:
            raise ValueError("binaryAssetUri missing")

        parsed = urlparse(source_uri)
        if parsed.scheme.lower() not in self._allowed_schemes:
            raise ValueError("binary source scheme not allowed")
        if parsed.hostname is None or parsed.hostname.lower() not in self._allowed_hosts:
            raise ValueError("binary source host not allowlisted")

        content, content_type = await self._fetch_binary(source_uri)
        checksum = hashlib.sha256(content).hexdigest()
        file_format = self._infer_file_format(source_uri, content_type)

        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        stored_uri = await self._blob_storage.store_binary_asset(
            incident_id=incident_id,
            data_source_id=str(signal.get("dataSourceId", signal.get("data_source_id", "unknown"))),
            timestamp=timestamp,
            binary_data=content,
            file_format=file_format,
        )

        updated = await self._signal_repository.update_binary_asset_uri(
            signal_id=signal_id,
            scope=scope,
            source_uri=source_uri,
            stored_uri=stored_uri,
        )
        if not updated:
            raise RuntimeError("binary stored but signal URI update was rejected")

        return f"{stored_uri}#sha256={checksum}"

    async def _fetch_binary(self, source_uri: str) -> tuple[bytes, str]:
        parsed = urlparse(source_uri)
        scheme = parsed.scheme.lower()
        if scheme in {"http", "https"}:
            async with httpx.AsyncClient(timeout=self._timeout_seconds, follow_redirects=False) as client:
                response = await client.get(source_uri)
                if 300 <= response.status_code < 400:
                    location = response.headers.get("Location", "")
                    if location:
                        redirect = urlparse(location)
                        if redirect.hostname and redirect.hostname.lower() not in self._allowed_hosts:
                            raise ValueError("redirect target host not allowlisted")
                    raise ValueError("binary source returned redirect")
                response.raise_for_status()
                content = response.content
                if len(content) > self._max_bytes:
                    raise ValueError("binary source exceeded configured max_bytes")
                content_type = response.headers.get("Content-Type", "application/octet-stream")
                return content, content_type

        if scheme == "ftp":
            host = parsed.hostname
            if host is None:
                raise ValueError("ftp URI missing host")
            path = parsed.path
            directory, _, filename = path.rpartition("/")
            if not filename:
                raise ValueError("ftp URI missing filename")

            chunks: list[bytes] = []
            size = 0

            def _accumulate(chunk: bytes) -> None:
                nonlocal size
                size += len(chunk)
                if size > self._max_bytes:
                    raise ValueError("binary source exceeded configured max_bytes")
                chunks.append(chunk)

            def _fetch_ftp() -> bytes:
                ftp = ftplib.FTP(host, timeout=self._timeout_seconds)
                ftp.login()
                if directory:
                    ftp.cwd(directory)
                ftp.retrbinary(f"RETR {filename}", _accumulate)
                ftp.quit()
                return b"".join(chunks)

            content = await asyncio.to_thread(_fetch_ftp)
            content_type = mimetypes.guess_type(source_uri)[0] or "application/octet-stream"
            return content, content_type

        raise ValueError("unsupported binary source scheme")

    @staticmethod
    def _infer_file_format(source_uri: str, content_type: str) -> str:
        suffix = source_uri.rsplit(".", 1)[-1].lower() if "." in source_uri else ""
        if suffix in {"png", "jpg", "jpeg", "gif", "webp", "tif", "tiff", "jp2", "json", "xml"}:
            return "jpg" if suffix == "jpeg" else suffix
        guessed = mimetypes.guess_extension(content_type.split(";", 1)[0].strip().lower())
        if guessed:
            return guessed.lstrip(".")
        return "bin"
