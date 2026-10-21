"""Opt-in, synthetic inputs for deployment-routing tests; no Azure resources."""

from __future__ import annotations

import os
import socket
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from itertools import permutations
from typing import Any

import pytest

MODEL_ID = "synthetic-chat"
MODEL_VERSION = "opaque-release/+041"
MODEL_KEY = f"{MODEL_ID}@{MODEL_VERSION}"
TIER_DEPLOYMENTS = (
    ("reasoning", "synthetic-live-r"),
    ("drafting", "synthetic-live-d"),
    ("simulation", "synthetic-exercise-s"),
)
TIER_ORDERINGS = tuple(permutations(TIER_DEPLOYMENTS))
ALIAS_CSV_ORDERINGS = tuple(
    ",".join(f"{tier}={deployment}" for tier, deployment in ordering) for ordering in TIER_ORDERINGS
)
CONFLICTING_CSV_ORDERINGS = tuple(
    ",".join(f"{MODEL_KEY}={deployment}" for _, deployment in ordering) for ordering in TIER_ORDERINGS
)
IDENTICAL_DUPLICATE_CSV = f"{MODEL_KEY}=synthetic-live-r, {MODEL_KEY}=synthetic-live-r"
SETTING_CASES: dict[str, dict[str, str | None]] = {
    "absent": {"AZURE_AI_REASONING_DEPLOYMENT": None},
    "blank": {"AZURE_AI_REASONING_DEPLOYMENT": " "},
    "partial_id": {"AZURE_AI_REASONING_MODEL_ID": MODEL_ID},
    "partial_version": {"AZURE_AI_REASONING_MODEL_VERSION": MODEL_VERSION},
    "blank_version": {
        "AZURE_AI_REASONING_MODEL_ID": MODEL_ID,
        "AZURE_AI_REASONING_MODEL_VERSION": "",
    },
    "complete": {
        "AZURE_AI_REASONING_DEPLOYMENT": "synthetic-live-r",
        "AZURE_AI_REASONING_MODEL_ID": MODEL_ID,
        "AZURE_AI_REASONING_MODEL_VERSION": MODEL_VERSION,
        "AZURE_AI_REASONING_MODEL_KEY": MODEL_KEY,
    },
}


def deny_network(*args: Any, **kwargs: Any) -> Any:
    """Fail before DNS or outbound socket traffic, including SDK credential probes."""
    raise AssertionError("Real network is forbidden in routing fixtures")


@contextmanager
def routing_environment() -> Iterator[pytest.MonkeyPatch]:
    """Clear inherited model settings and block network only within this context."""
    with pytest.MonkeyPatch.context() as patch:
        for name in tuple(os.environ):
            if name.startswith(("AZURE_AI_", "AZURE_OPENAI_")):
                patch.delenv(name)
        patch.setattr(socket, "getaddrinfo", deny_network)
        patch.setattr(socket, "create_connection", deny_network)
        patch.setattr(socket.socket, "connect", deny_network)
        patch.setattr(socket.socket, "connect_ex", deny_network)
        patch.setattr(socket.socket, "sendto", deny_network)
        yield patch


@pytest.fixture
def hermetic_routing_environment() -> Iterator[pytest.MonkeyPatch]:
    """Opt in per test; other modules never inherit the network/environment patches."""
    with routing_environment() as patch:
        yield patch


@dataclass
class RequestSubmissionSpy:
    """Keep SDK entry separate from a fake request-bound transport handoff."""

    method_entries: list[str] = field(default_factory=list)
    submissions: list[tuple[str, str]] = field(default_factory=list)

    def enter_method(self, call_id: str) -> None:
        self.method_entries.append(call_id)

    def submit(self, *, call_id: str, deployment_name: str) -> None:
        self.submissions.append((call_id, deployment_name))

    async def submit_async(self, *, call_id: str, deployment_name: str) -> None:
        self.submit(call_id=call_id, deployment_name=deployment_name)


@pytest.fixture
def request_submission_spy() -> RequestSubmissionSpy:
    """Return fresh request evidence for one test, never a process-wide ledger."""
    return RequestSubmissionSpy()
