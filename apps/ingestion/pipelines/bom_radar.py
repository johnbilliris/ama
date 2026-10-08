import asyncio
import ftplib
import logging
from typing import Any

from apps.api.app.services.ingestion.pipeline_base import IngestionPipelineBase
from apps.ingestion.normalisers.binary_metadata_normaliser import normalise_binary_metadata

logger = logging.getLogger(__name__)


class BomRadarPipeline(IngestionPipelineBase):
    """Polls BoM FTP for radar images — metadata-only by default, incident-triggered download (FR-004, FR-009a)."""

    def __init__(self, **kwargs: Any):
        super().__init__(
            pipeline_id="bom-radar",
            data_source_ids=["bom-radar"],
            poll_interval_seconds=300,
            trust_tier="tier_3_operational_sensor",
            expected_update_seconds=300,
            **kwargs,
        )

    async def poll_source(self) -> list[dict[str, Any]]:
        def _fetch() -> list[dict[str, Any]]:
            payloads: list[dict[str, Any]] = []
            ftp = ftplib.FTP("ftp.bom.gov.au", timeout=30)
            ftp.login()
            ftp.cwd("/anon/gen/radar/")
            files = ftp.nlst()
            png_files = [f for f in files if f.endswith(".png") and f.startswith("IDR")]

            for filename in png_files:
                provider_version = _get_mdtm(ftp, filename)
                payloads.append(
                    {
                        "data_source_id": "bom-radar",
                        "source_name": "Bureau of Meteorology — Radar",
                        "product_type": "radar",
                        "product_code": filename.split(".")[0] if "." in filename else filename,
                        "file_format": "png",
                        "source_uri": f"ftp://ftp.bom.gov.au/anon/gen/radar/{filename}",
                        "timestamp": filename,
                        "provider_version": provider_version,
                        "source_timezone": "Australia/Sydney",
                        "collection_method": "api_pull",
                        "source_kind": "sensor",
                    }
                )
            ftp.quit()
            return payloads

        try:
            return await asyncio.to_thread(_fetch)
        except Exception as exc:
            logger.error("BoM radar FTP poll failed: %s", exc)
            raise

    def normalise(self, raw_payload: dict[str, Any]) -> dict[str, Any]:
        return normalise_binary_metadata(raw_payload)

    def compute_canonical_key(self, raw_payload: dict[str, Any]) -> str:
        provider_version = str(raw_payload.get("provider_version", "")).strip()
        if provider_version:
            return f"bom-radar:{raw_payload.get('product_code', '')}:{provider_version}"
        return f"bom-radar:{raw_payload.get('product_code', '')}:{raw_payload.get('timestamp', '')}"


def _get_mdtm(ftp: ftplib.FTP, filename: str) -> str:
    try:
        return ftp.sendcmd(f"MDTM {filename}").strip()
    except Exception:
        return ""
