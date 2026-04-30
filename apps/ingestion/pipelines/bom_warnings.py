import ftplib
import logging
from typing import Any

from apps.api.app.services.ingestion.pipeline_base import IngestionPipelineBase
from apps.ingestion.normalisers.bom_xml_normaliser import normalise_bom_xml

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
        self._known_files: set[str] = set()

    async def poll_source(self) -> list[dict[str, Any]]:
        payloads: list[dict[str, Any]] = []
        try:
            ftp = ftplib.FTP(self._ftp_host, timeout=30)
            ftp.login()
            ftp.cwd(self._ftp_path)
            files = ftp.nlst()

            xml_files = [f for f in files if f.endswith(".xml")]
            new_files = [f for f in xml_files if f not in self._known_files]

            for filename in new_files[:50]:
                import io

                buf = io.BytesIO()
                ftp.retrbinary(f"RETR {filename}", buf.write)
                content = buf.getvalue().decode("utf-8", errors="replace")
                payloads.append(
                    {
                        "xml": content,
                        "filename": filename,
                        "data_source_id": "bom-warnings",
                        "source_uri": f"ftp://{self._ftp_host}{self._ftp_path}{filename}",
                    }
                )
                self._known_files.add(filename)

            ftp.quit()
        except Exception as exc:
            logger.error("BoM FTP poll failed: %s", exc)
            raise
        return payloads

    def normalise(self, raw_payload: dict[str, Any]) -> dict[str, Any]:
        return normalise_bom_xml(raw_payload)

    def compute_canonical_key(self, raw_payload: dict[str, Any]) -> str:
        filename = raw_payload.get("filename", "")
        return f"bom-ftp-fwo:{filename}"
