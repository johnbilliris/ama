"""AI-assisted cross-domain correlation analysis.

Queries indicator data across domains, computes trend comparisons,
sends structured prompts to Azure OpenAI, generates correlation
descriptions and recommendations. All outputs through content safety.

FRs: FR-025–028 | Research: R-006
"""

import logging
from datetime import UTC, datetime

logger = logging.getLogger(__name__)


class IndicatorAnalysisService:
    def __init__(self, llm_client=None, content_safety=None, catalogue_service=None):
        self._llm = llm_client
        self._content_safety = content_safety
        self._catalogue = catalogue_service

    def analyse_cross_domain_correlations(self, indicator_data: list[dict]) -> dict:
        """Identify cross-domain correlations in recovery indicator data."""
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

        # Cross-domain correlation detection
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

        result: dict = {
            "analysis_id": f"analysis-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}",
            "domains_analysed": list(domains.keys()),
            "total_indicators": len(indicator_data),
            "correlations": correlations,
            "lagging_domains": lagging_domains,
            "generated_at": datetime.now(UTC).isoformat(),
        }

        # Attempt LLM enrichment
        if self._llm and correlations:
            try:
                prompt = self._build_analysis_prompt(correlations, lagging_domains)
                response = self._llm.generate_response(
                    purpose="drafting",
                    prompt=prompt,
                    max_output_tokens=500,
                )
                llm_text = response.get("text", "").strip()
                if llm_text and self._content_safety:
                    safety = self._content_safety.validate(text=llm_text)
                    if safety.passed:
                        result["ai_summary"] = llm_text
                        result["content_safety_result"] = "passed"
                    else:
                        result["content_safety_result"] = "failed"
                elif llm_text:
                    result["content_safety_result"] = "content_safety_unavailable"
            except Exception:
                logger.info("LLM unavailable for analysis, using rule-based output")
                result["content_safety_result"] = "llm_unavailable"

        return result

    def recommend_activities(self, lagging_indicator_ids: list[str]) -> list[dict]:
        """Recommend AIDR catalogue activities for lagging indicators."""
        if not self._catalogue:
            return []
        return self._catalogue.suggest_activities(lagging_indicator_ids)

    def generate_community_summary(
        self,
        indicator_data: list[dict],
        domain_filter: str | None = None,
    ) -> dict:
        """Generate a plain-language recovery summary for community communication."""
        summary_parts: list[str] = []
        domains: dict[str, list[dict]] = {}
        for ind in indicator_data:
            d = ind.get("domain", "unknown")
            if domain_filter and d != domain_filter:
                continue
            domains.setdefault(d, []).append(ind)

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

    def _build_analysis_prompt(self, correlations: list[dict], lagging: list[dict]) -> str:
        parts = ["Analyse these cross-domain recovery correlations for an Australian disaster recovery program:"]
        for c in correlations:
            parts.append(f"- {c['description']} (Evidence: {c['evidence']})")
        parts.append("Provide a brief analysis of potential causal relationships and priority recommendations.")
        return "\n".join(parts)
