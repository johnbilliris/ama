"""Platform API AI analysis service.

Delegates cross-domain correlation analysis, activity recommendations,
and community summary generation. Wraps the monitoring agent's analysis
logic for use by the platform API layer.

FRs: FR-025–028
"""

import logging
from datetime import UTC, datetime

logger = logging.getLogger(__name__)


class AIAnalysisService:
    """Platform-level AI analysis facade.

    When no monitoring agent client is available, provides lightweight
    rule-based analysis directly.
    """

    def __init__(self, monitoring_client=None):
        self._monitoring_client = monitoring_client

    async def cross_domain_analysis(self, indicator_data: list[dict]) -> dict:
        """Run cross-domain correlation analysis on indicator data."""
        if self._monitoring_client:
            return await self._monitoring_client.analyse_cross_domain(indicator_data)

        # Inline rule-based fallback (mirrors IndicatorAnalysisService logic)
        domains: dict[str, list[dict]] = {}
        for ind in indicator_data:
            d = ind.get("domain", "unknown")
            domains.setdefault(d, []).append(ind)

        correlations: list[dict] = []
        lagging_domains: list[dict] = []
        for domain, indicators in domains.items():
            lagging = [
                i
                for i in indicators
                if i.get("trend") == "negative"
                or (
                    i.get("value") is not None
                    and i.get("target_value") is not None
                    and i["value"] < i["target_value"] * 0.8
                )
            ]
            if lagging:
                lagging_domains.append(
                    {
                        "domain": domain,
                        "lagging_count": len(lagging),
                        "indicators": [i.get("indicator_name", "") for i in lagging],
                    }
                )

        if len(lagging_domains) > 1:
            for i, d1 in enumerate(lagging_domains):
                for d2 in lagging_domains[i + 1 :]:
                    correlations.append(
                        {
                            "domains": [d1["domain"], d2["domain"]],
                            "description": (
                                f"Both {d1['domain']} and {d2['domain']} domains show lagging "
                                f"indicators, suggesting potential cross-domain impact"
                            ),
                            "evidence": (
                                f"{d1['domain']}: {d1['lagging_count']} lagging, "
                                f"{d2['domain']}: {d2['lagging_count']} lagging"
                            ),
                        }
                    )

        return {
            "analysis_id": f"analysis-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}",
            "domains_analysed": list(domains.keys()),
            "total_indicators": len(indicator_data),
            "correlations": correlations,
            "lagging_domains": lagging_domains,
            "generated_at": datetime.now(UTC).isoformat(),
        }

    async def recommend_activities(self, lagging_indicator_ids: list[str]) -> list[dict]:
        """Recommend AIDR catalogue activities for lagging indicators."""
        if self._monitoring_client:
            return await self._monitoring_client.recommend_activities(lagging_indicator_ids)
        return []

    async def community_summary(
        self,
        indicator_data: list[dict],
        domain_filter: str | None = None,
    ) -> dict:
        """Generate a plain-language community recovery summary."""
        if self._monitoring_client:
            return await self._monitoring_client.community_summary(indicator_data, domain_filter)

        domains: dict[str, list[dict]] = {}
        for ind in indicator_data:
            d = ind.get("domain", "unknown")
            if domain_filter and d != domain_filter:
                continue
            domains.setdefault(d, []).append(ind)

        summary_parts: list[str] = []
        for domain, indicators in sorted(domains.items()):
            progressing = sum(1 for i in indicators if i.get("trend") == "positive")
            total = len(indicators)
            summary_parts.append(f"{domain.title()} recovery: {progressing}/{total} indicators progressing")

        return {
            "summary": ". ".join(summary_parts) if summary_parts else "No indicator data available",
            "domains_covered": list(domains.keys()),
            "generated_at": datetime.now(UTC).isoformat(),
            "content_safety_result": None,
        }
