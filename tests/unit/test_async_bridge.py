"""Tests for async-to-sync bridge utility."""

from __future__ import annotations

import asyncio

import pytest

from common.async_bridge import run_async


class TestRunAsync:
    """Tests for run_async() bridge."""

    def test_run_simple_coroutine(self):
        async def add(a, b):
            return a + b

        result = run_async(add(1, 2))
        assert result == 3

    def test_run_coroutine_with_sleep(self):
        async def delayed():
            await asyncio.sleep(0.01)
            return "done"

        result = run_async(delayed())
        assert result == "done"

    def test_propagates_exception(self):
        async def failing():
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            run_async(failing())
