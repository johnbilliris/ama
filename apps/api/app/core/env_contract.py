from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

_CANONICAL_TO_ALIASES: dict[str, tuple[str, ...]] = {
    "AMA_ENVIRONMENT": ("ENVIRONMENT",),
    "AMA_ENABLE_PRODUCTION_AUTH": ("ENABLE_PRODUCTION_AUTH",),
    "AMA_ENTRA_TENANT_ID": ("ENTRA_TENANT_ID",),
    "AMA_ENTRA_AUDIENCE": ("ENTRA_AUDIENCE",),
    "COSMOS_ENDPOINT": ("COSMOS_DB_ENDPOINT", "AZURE_COSMOS_ENDPOINT"),
    "ALLOWED_AZURE_REGIONS": ("AMA_ALLOWED_AZURE_REGIONS",),
}

_AU_REGIONS = frozenset({"australia east", "australia southeast"})
_warned_aliases: set[str] = set()


class EnvironmentContractError(ValueError):
    pass


def resolve_canonical_env() -> dict[str, str]:
    """Resolve supported aliases to canonical env keys with conflict detection."""
    resolved: dict[str, str] = {}
    for canonical, aliases in _CANONICAL_TO_ALIASES.items():
        canonical_value = os.environ.get(canonical)
        alias_values = [(alias, os.environ.get(alias)) for alias in aliases if os.environ.get(alias) is not None]

        if canonical_value is not None:
            for alias, value in alias_values:
                if value is not None and value != canonical_value:
                    raise EnvironmentContractError(f"conflicting values for {canonical}")
            resolved[canonical] = canonical_value
            continue

        if alias_values:
            alias, value = alias_values[0]
            if value is not None:
                resolved[canonical] = value
                _warn_alias_once(alias, canonical)

    return resolved


def validate_runtime_environment() -> None:
    resolved = resolve_canonical_env()

    environment = (resolved.get("AMA_ENVIRONMENT") or "").strip().lower()
    production_auth = _is_truthy(
        resolved.get("AMA_ENABLE_PRODUCTION_AUTH") or os.environ.get("AMA_ENABLE_PRODUCTION_AUTH")
    )

    if environment in {"production", "staging"}:
        if not production_auth:
            raise EnvironmentContractError("production auth gate missing")
        if not (resolved.get("AMA_ENTRA_TENANT_ID") and resolved.get("AMA_ENTRA_AUDIENCE")):
            raise EnvironmentContractError("entra tenant/audience missing")
        if not resolved.get("COSMOS_ENDPOINT"):
            raise EnvironmentContractError("cosmos endpoint missing")
        if os.environ.get("AMA_ENTRA_TEST_PRINCIPAL"):
            raise EnvironmentContractError("test principal is not permitted")
        if _is_truthy(os.environ.get("AMA_TRUST_FORWARDED_PRINCIPAL")):
            raise EnvironmentContractError("forwarded principal trust is not permitted")

    if "ALLOWED_AZURE_REGIONS" in resolved:
        regions_raw = resolved["ALLOWED_AZURE_REGIONS"]
        regions = [item.strip() for item in regions_raw.split(",") if item.strip()]
        if not regions:
            raise EnvironmentContractError("allowed regions list is empty")
        unsupported = [region for region in regions if region.lower() not in _AU_REGIONS]
        if unsupported:
            raise EnvironmentContractError("allowed regions include unsupported values")


def _warn_alias_once(alias: str, canonical: str) -> None:
    key = f"{alias}->{canonical}"
    if key in _warned_aliases:
        return
    logger.warning("Environment alias '%s' is deprecated; use '%s' instead", alias, canonical)
    _warned_aliases.add(key)


def _is_truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}
