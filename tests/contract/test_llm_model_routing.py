"""Contract tests: LLM model routing (US2).

Verifies:
- purpose="reasoning" routes to reasoning deployment
- purpose="drafting" routes to drafting deployment
- Unknown purpose raises descriptive error
- Temperature defaults: 0.0 for reasoning, 0.3 for drafting
"""

from __future__ import annotations

import pytest
from common.foundry_chat_client import FoundryConfigurationError, LiveFoundryChatClient
from common.llm_config import LLMClientConfig


class TestModelRouting:
    """Verify model tier routing logic."""

    def test_reasoning_purpose_routes_to_reasoning_deployment(self) -> None:
        config = LLMClientConfig(
            endpoint="https://test.australiaeast.openai.azure.com",
            reasoning_deployment="gpt-4o-dev",
            drafting_deployment="gpt-4o-mini-dev",
            model_tier="reasoning",
        )
        assert config.deployment_for("reasoning") == "gpt-4o-dev"

    def test_drafting_purpose_routes_to_drafting_deployment(self) -> None:
        config = LLMClientConfig(
            endpoint="https://test.australiaeast.openai.azure.com",
            reasoning_deployment="gpt-4o-dev",
            drafting_deployment="gpt-4o-mini-dev",
            model_tier="drafting",
        )
        assert config.deployment_for("drafting") == "gpt-4o-mini-dev"

    def test_unknown_purpose_raises_error(self) -> None:
        config = LLMClientConfig(
            endpoint="https://test.australiaeast.openai.azure.com",
            model_tier="reasoning",
        )
        with pytest.raises(ValueError, match="Unknown LLM purpose"):
            config.deployment_for("unknown")

    @pytest.mark.parametrize("purpose", ["reasoning", "drafting", "simulation"])
    def test_explicit_foundry_tiers_need_no_duplicate_legacy_aliases(
        self, purpose: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        for tier in ("reasoning", "drafting", "simulation"):
            monkeypatch.setenv(f"AZURE_AI_{tier.upper()}_DEPLOYMENT", f"explicit-{tier}")
        config = LLMClientConfig(foundry_deployments="text-embedding-3-large@1=embedding-target")
        deployments = config.foundry_deployment_map()
        assert purpose not in deployments
        client = LiveFoundryChatClient(
            endpoint="https://synthetic.cognitiveservices.azure.com",
            region="australiaeast",
            deployments=deployments,
            credential=object(),
        )
        assert client._resolve(config.foundry_model_key_for(purpose)) == f"explicit-{purpose}"
        assert deployments == {"text-embedding-3-large@1": "embedding-target"}

    @pytest.mark.parametrize("destinations", [("a", "b"), ("b", "a")])
    def test_foundry_config_rejects_conflicting_raw_map(self, destinations: tuple[str, str]) -> None:
        first, second = destinations
        config = LLMClientConfig(foundry_deployments=f"model@opaque={first},model@opaque={second}")
        with pytest.raises(FoundryConfigurationError) as error:
            config.foundry_deployment_map()
        assert all(value in str(error.value) for value in ("model@opaque", repr(first), repr(second)))

    def test_reasoning_tier_defaults(self) -> None:
        """Risk Assessment and Evacuation agents use reasoning tier."""
        from apps.agents.evacuation.config import EvacuationConfig
        from apps.agents.risk_assessment.config import RiskAssessmentConfig

        risk_config = RiskAssessmentConfig()
        assert risk_config.llm_model_tier == "reasoning"
        assert risk_config.llm_temperature == 0.0
        assert risk_config.llm_max_output_tokens == 4000

        evac_config = EvacuationConfig()
        assert evac_config.llm_model_tier == "reasoning"
        assert evac_config.llm_temperature == 0.0
        assert evac_config.llm_max_output_tokens == 4000

    def test_drafting_tier_defaults(self) -> None:
        """Monitoring, Communication, Resource Allocation agents use drafting tier."""
        from apps.agents.communication.config import CommunicationConfig
        from apps.agents.monitoring.config import MonitoringConfig
        from apps.agents.resource_allocation.config import ResourceAllocationConfig

        for ConfigCls in (MonitoringConfig, CommunicationConfig, ResourceAllocationConfig):
            config = ConfigCls()
            assert config.llm_model_tier == "drafting", f"{ConfigCls.__name__} should be drafting"
            assert config.llm_temperature == 0.3, f"{ConfigCls.__name__} should have temp 0.3"
            assert config.llm_max_output_tokens == 2000, f"{ConfigCls.__name__} should have 2000 tokens"


class TestModelTierValidation:
    """Verify model tier validation."""

    def test_invalid_model_tier_rejected(self) -> None:
        with pytest.raises(ValueError, match="Invalid LLM_MODEL_TIER"):
            LLMClientConfig(
                endpoint="https://test.australiaeast.openai.azure.com",
                model_tier="unknown",
            )

    def test_temperature_out_of_range_rejected(self) -> None:
        with pytest.raises(ValueError, match="LLM_TEMPERATURE"):
            LLMClientConfig(
                endpoint="https://test.australiaeast.openai.azure.com",
                model_tier="drafting",
                temperature=3.0,
            )

    def test_max_tokens_zero_rejected(self) -> None:
        with pytest.raises(ValueError, match="LLM_MAX_OUTPUT_TOKENS"):
            LLMClientConfig(
                endpoint="https://test.australiaeast.openai.azure.com",
                model_tier="drafting",
                max_output_tokens=0,
            )

    def test_max_tokens_over_limit_rejected(self) -> None:
        with pytest.raises(ValueError, match="LLM_MAX_OUTPUT_TOKENS"):
            LLMClientConfig(
                endpoint="https://test.australiaeast.openai.azure.com",
                model_tier="drafting",
                max_output_tokens=20000,
            )
