"""Tests for risk_assessment.versioning – VersionCounter with Cosmos OCC."""

from unittest.mock import MagicMock

import pytest
from risk_assessment.versioning import VersionCounter


class TestVersionCounterNoCosmos:
    @pytest.mark.asyncio
    async def test_no_cosmos_returns_version_one(self):
        counter = VersionCounter(cosmos_container=None)
        v = await counter.assign_version("inc-1", "spread_prediction")
        assert v == 1


class TestVersionCounterWithCosmos:
    @pytest.mark.asyncio
    async def test_first_version_creates_counter_doc(self):
        container = MagicMock()
        # read_item raises 404 → triggers _create_counter
        container.read_item.side_effect = Exception("404 NotFound")
        container.create_item.return_value = {"id": "counter", "current_version": 1}
        counter = VersionCounter(cosmos_container=container)
        v = await counter.assign_version("inc-1", "spread_prediction")
        assert v == 1
        container.create_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_monotonic_increment(self):
        container = MagicMock()
        container.read_item.return_value = {
            "id": "inc-1_spread_prediction_counter",
            "current_version": 5,
            "_etag": "etag-5",
        }
        container.replace_item.return_value = {
            "id": "inc-1_spread_prediction_counter",
            "current_version": 6,
        }
        counter = VersionCounter(cosmos_container=container)
        v = await counter.assign_version("inc-1", "spread_prediction")
        assert v == 6

    @pytest.mark.asyncio
    async def test_412_conflict_triggers_retry(self):
        container = MagicMock()
        # Return a fresh copy each time to avoid in-place mutation
        container.read_item.side_effect = [
            {"id": "inc-1_spread_prediction_counter", "current_version": 3, "_etag": "etag-3"},
            {"id": "inc-1_spread_prediction_counter", "current_version": 3, "_etag": "etag-4"},
        ]
        # First replace fails with 412, second succeeds
        container.replace_item.side_effect = [
            Exception("412 PreconditionFailed"),
            {"id": "counter", "current_version": 4},
        ]
        counter = VersionCounter(cosmos_container=container)
        v = await counter.assign_version("inc-1", "spread_prediction")
        assert v == 4

    @pytest.mark.asyncio
    async def test_max_retries_with_fallback(self):
        container = MagicMock()
        doc = {
            "id": "inc-1_spread_prediction_counter",
            "current_version": 3,
            "_etag": "etag-3",
        }
        container.read_item.return_value = doc
        # All replaces fail with 412 — triggers fallback
        container.replace_item.side_effect = Exception("412 PreconditionFailed")
        counter = VersionCounter(cosmos_container=container)
        v = await counter.assign_version("inc-1", "spread_prediction")
        # Fallback reads current_version and returns +1
        assert isinstance(v, int)
        assert v >= 1
