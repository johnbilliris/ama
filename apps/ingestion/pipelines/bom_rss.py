import ftplib
import io
import logging
from typing import Any
from xml.etree import ElementTree

from apps.api.app.services.ingestion.pipeline_base import IngestionPipelineBase
from apps.ingestion.normalisers.bom_xml_normaliser import normalise_bom_xml

logger = logging.getLogger(__name__)

BOM_FTP_HOST = "ftp.bom.gov.au"
BOM_FTP_FWO_PATH = "/anon/gen/fwo/"

# BoM product-code prefix per state (used on anonymous FTP)
_STATE_PREFIX: dict[str, str] = {
    "nsw": "IDN",
    "vic": "IDV",
    "qld": "IDQ",
    "sa": "IDS",
    "wa": "IDW",
    "tas": "IDT",
    "nt": "IDD",
}

# AMOC product-type values that represent warnings
_WARNING_PRODUCT_TYPES = {"W"}


class BomRssPipeline(IngestionPipelineBase):
    """Polls BoM anonymous FTP for state-based XML warning products (FR-004).

    Replaces the previous HTTP RSS approach (IDZ0005x feeds) which returns 403.
    Scans ``ftp.bom.gov.au/anon/gen/fwo/`` for state-prefixed XML products and
    filters for warning product-type (``W``) in the AMOC header.
    """

    def __init__(self, states: list[str] | None = None, **kwargs: Any):
        self._states = states or list(_STATE_PREFIX.keys())
        super().__init__(
            pipeline_id="bom-rss",
            data_source_ids=["bom-warnings"],
            poll_interval_seconds=60,
            trust_tier="tier_1_authoritative_government",
            expected_update_seconds=60,
            **kwargs,
        )
        self._known_files: set[str] = set()

    async def poll_source(self) -> list[dict[str, Any]]:
        payloads: list[dict[str, Any]] = []
        try:
            ftp = ftplib.FTP(BOM_FTP_HOST, timeout=30)
            ftp.login()
            ftp.cwd(BOM_FTP_FWO_PATH)
            all_files = ftp.nlst()

            for state in self._states:
                prefix = _STATE_PREFIX.get(state)
                if not prefix:
                    continue
                # Filter for this state's XML products (skip .amoc.xml metadata files)
                state_xmls = [
                    f for f in all_files
                    if f.startswith(prefix)
                    and f.endswith(".xml")
                    and not f.endswith(".amoc.xml")
                    and f not in self._known_files
                ]
                for filename in state_xmls:
                    try:
                        buf = io.BytesIO()
                        ftp.retrbinary(f"RETR {filename}", buf.write)
                        content = buf.getvalue().decode("utf-8", errors="replace")

                        # Check AMOC header for warning product-type
                        if not self._is_warning_product(content):
                            self._known_files.add(filename)
                            continue

                        payloads.append({
                            "xml": content,
                            "filename": filename,
                            "data_source_id": "bom-warnings",
                            "source_uri": f"ftp://{BOM_FTP_HOST}{BOM_FTP_FWO_PATH}{filename}",
                            "jurisdiction_id": state,
                        })
                        self._known_files.add(filename)
                    except Exception as exc:
                        logger.warning("Failed to retrieve %s: %s", filename, exc)

            ftp.quit()
        except Exception as exc:
            logger.error("BoM FTP warning poll failed: %s", exc)
            raise
        return payloads

    @staticmethod
    def _is_warning_product(xml_text: str) -> bool:
        """Return True if the AMOC header indicates a warning product."""
        try:
            root = ElementTree.fromstring(xml_text)
            amoc = root.find(".//amoc")
            if amoc is not None:
                product_type = (amoc.findtext("product-type") or "").strip()
                return product_type in _WARNING_PRODUCT_TYPES
        except ElementTree.ParseError:
            pass
        return False

    def normalise(self, raw_payload: dict[str, Any]) -> dict[str, Any]:
        return normalise_bom_xml(raw_payload)

    def compute_canonical_key(self, raw_payload: dict[str, Any]) -> str:
        filename = raw_payload.get("filename", "")
        return f"bom-ftp-fwo:{filename}"
