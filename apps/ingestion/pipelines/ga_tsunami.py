import asyncio
import ftplib
import io
import logging

from apps.ingestion.normalisers.cap_normaliser import extract_cap_identity, normalise_cap_xml
from apps.ingestion.pipelines.bom_warnings import BomWarningsPipeline

logger = logging.getLogger(__name__)


class GaTsunamiPipeline(BomWarningsPipeline):
    """Polls BoM FTP for tsunami warning CAP/XML at 30-second intervals (FR-005 Tsunami)."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pipeline_id = "ga-tsunami"
        self.data_source_ids = ["ga-tsunami-warnings"]
        self.poll_interval_seconds = 30
        self._ftp_path = "/anon/gen/fwo/"

    def compute_canonical_key(self, raw_payload):
        cap_identity = extract_cap_identity(raw_payload)
        provider_version = str(raw_payload.get("provider_version", "")).strip()
        if provider_version:
            return f"ga-tsunami:{cap_identity['identifier']}:{cap_identity['sent']}:{provider_version}"
        return f"ga-tsunami:{cap_identity['identifier']}:{cap_identity['sent']}"

    def normalise(self, raw_payload):
        return normalise_cap_xml(raw_payload)

    async def poll_source(self):
        """Override parent to use retrbinary (avoids 8192-byte retrlines buffer overflow)."""

        def _fetch() -> list[dict[str, str]]:
            payloads: list[dict[str, str]] = []
            ftp = ftplib.FTP(self._ftp_host, timeout=30)
            ftp.login()
            ftp.cwd(self._ftp_path)
            files = ftp.nlst()

            xml_files = [f for f in files if f.endswith(".xml")]

            for filename in xml_files:
                buf = io.BytesIO()
                ftp.retrbinary(f"RETR {filename}", buf.write)
                content = buf.getvalue().decode("utf-8", errors="replace")

                if "tsunami" not in content.lower():
                    continue

                provider_version = _get_mdtm(ftp, filename)

                payloads.append(
                    {
                        "xml": content,
                        "filename": filename,
                        "provider_version": provider_version,
                        "data_source_id": "ga-tsunami-warnings",
                        "source_uri": f"ftp://{self._ftp_host}{self._ftp_path}{filename}",
                    }
                )

            ftp.quit()
            return payloads

        try:
            return await asyncio.to_thread(_fetch)
        except Exception as exc:
            logger.error("GA tsunami FTP poll failed: %s", exc)
            raise


def _get_mdtm(ftp: ftplib.FTP, filename: str) -> str:
    try:
        return ftp.sendcmd(f"MDTM {filename}").strip()
    except Exception:
        return ""
