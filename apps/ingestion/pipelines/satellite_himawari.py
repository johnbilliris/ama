import ftplib
import logging
from typing import Any

from apps.api.app.services.ingestion.pipeline_base import IngestionPipelineBase
from apps.ingestion.normalisers.binary_metadata_normaliser import normalise_binary_metadata

logger = logging.getLogger(__name__)

BOM_FTP_HOST = "ftp.bom.gov.au"
BOM_FTP_GMS_PATH = "/anon/gen/gms/"
IDE_PREFIX = "IDE"


class HimawariSatellitePipeline(IngestionPipelineBase):
    """Polls BoM FTP for Himawari satellite imagery (IDE-prefixed files)."""

    def __init__(self, **kwargs: Any):
        super().__init__(
            pipeline_id="himawari-satellite",
            data_source_ids=["himawari-satellite"],
            poll_interval_seconds=600,
            trust_tier="tier_3_operational_sensor",
            expected_update_seconds=600,
            **kwargs,
        )
        self._ftp_host = BOM_FTP_HOST
        self._ftp_path = BOM_FTP_GMS_PATH
        self._known_files: set[str] = set()

    async def poll_source(self) -> list[dict[str, Any]]:
        payloads: list[dict[str, Any]] = []
        try:
            ftp = ftplib.FTP(self._ftp_host, timeout=30)
            ftp.login()
            ftp.cwd(self._ftp_path)
            files = ftp.nlst()

            ide_files = [f for f in files if f.startswith(IDE_PREFIX)]
            new_files = [f for f in ide_files if f not in self._known_files]

            for filename in new_files[:20]:
                source_uri = f"ftp://{self._ftp_host}{self._ftp_path}{filename}"
                payloads.append(
                    {
                        "data_source_id": "himawari-satellite",
                        "source_name": "BoM Himawari-9 Satellite",
                        "source_kind": "sensor",
                        "product_type": "infrared",
                        "source_uri": source_uri,
                        "timestamp": filename,
                        "coverage_bbox": [112.0, -44.0, 154.0, -10.0],
                        "file_format": "png",
                        "product_code": filename,
                        "collection_method": "satellite_downlink",
                        "jurisdiction_id": "national",
                    }
                )
                self._known_files.add(filename)

            ftp.quit()
        except Exception as exc:
            logger.error("Himawari FTP poll failed: %s", exc)
            raise
        return payloads

    def normalise(self, raw_payload: dict[str, Any]) -> dict[str, Any]:
        return normalise_binary_metadata(raw_payload)

    def compute_canonical_key(self, raw_payload: dict[str, Any]) -> str:
        product_code = raw_payload.get("product_code", "")
        return f"himawari:{product_code}"
