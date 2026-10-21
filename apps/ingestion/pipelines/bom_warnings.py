import asyncio
import ftplib
import logging
from typing import Any

from apps.api.app.services.ingestion.pipeline_base import IngestionPipelineBase
from apps.ingestion.normalisers.bom_xml_normaliser import extract_bom_product_metadata, normalise_bom_xml

logger = logging.getLogger(__name__)

BOM_FTP_HOST = "ftp.bom.gov.au"
BOM_FTP_WARNINGS_PATH = "/anon/gen/fwo/"


class BomWarningsPipeline(IngestionPipelineBase):
    """Polls BoM anonymous FTP for XML warning products (FR-004).

    Products conform to BoM product XML schema (XSD v1.7). Includes severe
    weather, tropical cyclone, flood, fire weather, and coastal warnings.
    Products are event-driven and deleted from FTP within 8-36 hours.
    """

    def __init__(self, **kwargs: Any):
        super().__init__(
            pipeline_id="bom-warnings",
            data_source_ids=["bom-warnings"],
            poll_interval_seconds=60,
            trust_tier="tier_1_authoritative_government",
            expected_update_seconds=60,
            **kwargs,
        )
        self._ftp_host = BOM_FTP_HOST
        self._ftp_path = BOM_FTP_WARNINGS_PATH

    async def poll_source(self) -> list[dict[str, Any]]:
        def _fetch() -> list[dict[str, Any]]:
            payloads: list[dict[str, Any]] = []
            ftp = ftplib.FTP(self._ftp_host, timeout=30)
            ftp.login()
            ftp.cwd(self._ftp_path)
            files = ftp.nlst()

            xml_files = [f for f in files if f.endswith(".xml")]
            for filename in xml_files:
                import io

                buf = io.BytesIO()
                ftp.retrbinary(f"RETR {filename}", buf.write)
                content = buf.getvalue().decode("utf-8", errors="replace")
                provider_version = _get_mdtm(ftp, filename)
                raw_payload = {
                    "xml": content,
                    "filename": filename,
                    "provider_version": provider_version,
                    "data_source_id": "bom-warnings",
                    "source_uri": f"ftp://{self._ftp_host}{self._ftp_path}{filename}",
                }
                if _is_warning_product(raw_payload):
                    payloads.append(raw_payload)

            ftp.quit()
            return payloads

        try:
            return await asyncio.to_thread(_fetch)
        except Exception as exc:
            logger.error("BoM FTP poll failed: %s", exc)
            raise

    def normalise(self, raw_payload: dict[str, Any]) -> dict[str, Any]:
        return normalise_bom_xml(raw_payload)

    def compute_canonical_key(self, raw_payload: dict[str, Any]) -> str:
        metadata = extract_bom_product_metadata(raw_payload)
        provider_version = str(raw_payload.get("provider_version", "")).strip()
        if provider_version:
            return f"bom-ftp-fwo:{metadata['productId']}:{metadata['issueTimeUtc']}:{provider_version}"
        return f"bom-ftp-fwo:{metadata['productId']}:{metadata['issueTimeUtc']}"


def _is_warning_product(raw_payload: dict[str, Any]) -> bool:
    try:
        metadata = extract_bom_product_metadata(raw_payload)
    except ValueError as exc:
        logger.debug("Skipping non-warning BoM XML product %s: %s", raw_payload.get("filename", "unknown"), exc)
        return False
    return "warning" in metadata["productType"]


def _get_mdtm(ftp: ftplib.FTP, filename: str) -> str:
    try:
        response = ftp.sendcmd(f"MDTM {filename}")
    except Exception:
        return ""
    return response.strip()
