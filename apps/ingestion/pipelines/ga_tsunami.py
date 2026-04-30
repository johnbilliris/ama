import ftplib
import io
import logging

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
        filename = raw_payload.get("filename", "")
        return f"bom-ftp-fwo:{filename}"

    async def poll_source(self):
        """Override parent to use retrbinary (avoids 8192-byte retrlines buffer overflow)."""
        payloads = []
        try:
            ftp = ftplib.FTP(self._ftp_host, timeout=30)
            ftp.login()
            ftp.cwd(self._ftp_path)
            files = ftp.nlst()

            xml_files = [f for f in files if f.endswith(".xml") and f not in self._known_files]

            for filename in xml_files[:50]:
                buf = io.BytesIO()
                ftp.retrbinary(f"RETR {filename}", buf.write)
                content = buf.getvalue().decode("utf-8", errors="replace")

                if "tsunami" not in content.lower():
                    self._known_files.add(filename)
                    continue

                payloads.append(
                    {
                        "xml": content,
                        "filename": filename,
                        "data_source_id": "ga-tsunami-warnings",
                        "source_uri": f"ftp://{self._ftp_host}{self._ftp_path}{filename}",
                    }
                )
                self._known_files.add(filename)

            ftp.quit()
        except Exception as exc:
            logger.error("GA tsunami FTP poll failed: %s", exc)
            raise
        return payloads
