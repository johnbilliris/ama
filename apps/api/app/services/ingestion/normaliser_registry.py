from collections.abc import Callable
from typing import Any


class NormaliserRegistry:
    """Dispatches source-specific normalisers by endpoint format."""

    def __init__(self) -> None:
        self._normalisers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {}

    def register(self, format_key: str, normaliser: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
        self._normalisers[format_key] = normaliser

    def get(self, format_key: str) -> Callable[[dict[str, Any]], dict[str, Any]] | None:
        return self._normalisers.get(format_key)

    def normalise(self, format_key: str, raw_payload: dict[str, Any]) -> dict[str, Any]:
        normaliser = self._normalisers.get(format_key)
        if normaliser is None:
            raise ValueError(f"No normaliser registered for format '{format_key}'")
        return normaliser(raw_payload)

    @property
    def registered_formats(self) -> list[str]:
        return list(self._normalisers.keys())
