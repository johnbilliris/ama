import logging
import os
from datetime import UTC, datetime, timedelta

if os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING"):
    try:
        from azure.identity import ManagedIdentityCredential
        from azure.monitor.opentelemetry import configure_azure_monitor

        configure_azure_monitor(
            enable_live_metrics=True,
            credential=ManagedIdentityCredential(),
        )
    except Exception:
        logging.getLogger(__name__).warning("Failed to configure Azure Monitor", exc_info=True)

from app.validators.signal_envelope import SignalEnvelope
from common.handoffs import AgentHandoffEvent, build_handoff

logger = logging.getLogger(__name__)

RETROSPECTIVE_LOOKBACK_HOURS = 24


class MonitoringAgent:
    def __init__(self, signal_repository=None, llm_client=None):
        self._signal_repository = signal_repository
        self._llm_client = llm_client

    def summarize_signal(self, envelope: SignalEnvelope) -> dict[str, object]:
        return {
            "category": envelope.category,
            "sourceKind": envelope.source.kind,
            "incidentId": envelope.incidentId,
        }

    def build_high_risk_handoff(self, envelope: SignalEnvelope) -> AgentHandoffEvent | None:
        if envelope.validationStatus == "escalated":
            tier2_result = self._evaluate_escalated_signal(envelope)
            if tier2_result == "misinformation":
                logger.info("Tier 2 LLM classified signal as misinformation, blocking handoff")
                return None
            if tier2_result == "llm_unavailable":
                logger.info("LLM unavailable — holding escalated signal for human review")
                return None

        is_high_risk = (
            envelope.category in {"fire", "weather", "hydrology"}
            and envelope.confidenceScore >= 0.8
        )
        if not is_high_risk or not envelope.incidentId:
            return None

        return build_handoff(
            incident_id=envelope.incidentId,
            source_agent="monitoring",
            target_agent="risk_assessment",
            scope_key=envelope.incidentId,
            payload={
                "category": envelope.category,
                "sourceKind": envelope.source.kind,
                "signalSummary": self.summarize_signal(envelope),
            },
            confidence=envelope.confidenceScore,
        )

    def _evaluate_escalated_signal(self, envelope: SignalEnvelope) -> str:
        """Tier 2 LLM-based evaluation of escalated social signals (FR-010a)."""
        if not self._llm_client:
            return "llm_unavailable"
        try:
            prompt = (
                f"Evaluate this disaster-related social media post for credibility. "
                f"Category: {envelope.category}. Content: {envelope.payload}. "
                f"Is this credible community intelligence or misinformation? "
                f"Respond with exactly one word: credible, suspicious, or misinformation."
            )
            response = self._llm_client.generate_response(
                system_prompt="You are a misinformation detection assistant for Australian disaster response.",
                user_prompt=prompt,
                purpose="reasoning",
                max_output_tokens=10,
            )
            result_text = response.get("text", "").strip().lower()
            if "misinformation" in result_text:
                return "misinformation"
            return "credible"
        except Exception:
            logger.warning("LLM evaluation failed for escalated signal, holding for human review")
            return "llm_unavailable"

    async def retrospective_associate(
        self,
        incident_id: str,
        jurisdiction_id: str,
        lookback_hours: int = RETROSPECTIVE_LOOKBACK_HOURS,
    ) -> int:
        """Retrospectively associate unmatched signals with a newly declared incident (FR-019b)."""
        if not self._signal_repository:
            return 0
        cutoff = datetime.now(UTC) - timedelta(hours=lookback_hours)
        unassociated = await self._signal_repository.query_unassociated(
            jurisdiction_id=jurisdiction_id,
            since=cutoff,
        )
        count = 0
        for signal in unassociated:
            await self._signal_repository.update_incident_id(signal.signal_id, incident_id)
            count += 1
            logger.info(
                "Retrospectively associated signal %s with incident %s",
                signal.signal_id, incident_id,
            )
        return count


# ---------------------------------------------------------------------------
# Lightweight health server – keeps the container alive and satisfies
# Container Apps ingress health probes on the configured targetPort.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from http.server import HTTPServer, BaseHTTPRequestHandler

    # configure_azure_monitor() (called at module level) may have already
    # added handlers to the root logger, which makes basicConfig() a no-op.
    # Explicitly add a StreamHandler so logs also reach stdout/stderr.
    _fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    _console = logging.StreamHandler()
    _console.setFormatter(_fmt)
    root = logging.getLogger()
    root.addHandler(_console)
    root.setLevel(logging.INFO)

    _PORT = int(os.environ.get("PORT", "8080"))

    class _HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/health":
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"status":"healthy"}')
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):  # noqa: A002
            pass  # suppress per-request logs

    server = HTTPServer(("0.0.0.0", _PORT), _HealthHandler)
    logger.info("Agents health server listening on port %d", _PORT)
    server.serve_forever()
