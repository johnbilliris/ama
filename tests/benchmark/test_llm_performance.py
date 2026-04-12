"""LLM client overhead benchmarks with mocked responses.

Measures the application-side overhead of :meth:`LLMClient.generate_response`
(serialisation, retry logic setup, response parsing, and logging) with the
actual Azure OpenAI call replaced by an instant mock.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from common.llm_client import LLMClient
from common.llm_config import LLMClientConfig
from conftest import set_benchmark_metadata

# ── Fixture ───────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def mock_llm_client() -> LLMClient:
    """LLMClient with a mocked ``_client`` that returns instantly."""
    config = LLMClientConfig(
        endpoint="https://fake-australiaeast.openai.azure.com",
        reasoning_deployment="gpt-4o-bench",
        drafting_deployment="gpt-4o-mini-bench",
    )
    client = LLMClient.__new__(LLMClient)
    client._config = config

    # Build a mock response matching Azure OpenAI shape
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="Benchmark test response"))
    ]
    mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=20)

    # Replace the actual client with a mock that returns instantly
    mock_inner = MagicMock()
    mock_inner.chat.completions.create.return_value = mock_response
    client._client = mock_inner

    return client


# ── Benchmark ─────────────────────────────────────────────────────────────────


@pytest.mark.benchmark(group="llm")
def test_llm_client_overhead(benchmark, mock_llm_client) -> None:
    set_benchmark_metadata(
        benchmark, agent="shared", metric_type="llm", slo_target_s=0.500
    )
    result = benchmark(
        mock_llm_client.generate_response,
        purpose="reasoning",
        prompt="Assess wildfire risk for region XYZ",
    )
    assert "text" in result
