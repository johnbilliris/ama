"""Agent-routing-table loader (T-G04 / FR-022..FR-025).

Loads ``apps/api/app/config/agent_routing_table.yaml`` and exposes
deterministic helpers used by the routing layer:

- :func:`combat_for(jurisdiction)` — combat agencies (FR-022).
- :func:`control_for(jurisdiction)` — control/coordination agencies (FR-022).
- :func:`police_for(jurisdiction)` — convenience that respects the FR-023
  ACT-AFP override.
- :func:`medical_brand_for(jurisdiction)` — FR-024 brand lookup.
- :func:`is_ic_eligible(jurisdiction, role)` — FR-025 NSW IC restriction.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "config" / "agent_routing_table.yaml"


@dataclass(frozen=True)
class RoutingTable:
    combat_agencies: Mapping[str, tuple[str, ...]]
    control_agencies: Mapping[str, tuple[str, ...]]
    medical_brand: Mapping[str, str]
    nsw_ic_eligible_roles: tuple[str, ...] = field(default_factory=tuple)


def _strip_quotes(value: str) -> str:
    v = value.strip()
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        return v[1:-1]
    return v


def _parse_list_inline(value: str) -> list[str]:
    """Parse `["a", "b"]` style inline lists used in the YAML."""
    v = value.strip()
    if not v.startswith("["):
        return [_strip_quotes(v)]
    inner = v.strip("[]").strip()
    if not inner:
        return []
    parts: list[str] = []
    cur = ""
    quote: str | None = None
    for ch in inner:
        if quote is None and ch in {'"', "'"}:
            quote = ch
            continue
        if quote is not None and ch == quote:
            quote = None
            continue
        if quote is None and ch == ",":
            parts.append(cur.strip())
            cur = ""
            continue
        cur += ch
    if cur.strip():
        parts.append(cur.strip())
    return [p for p in parts if p]


def _parse(text: str) -> dict[str, Any]:
    """Tiny YAML subset parser tuned to the routing-table layout.

    Supports two shapes: top-level ``key:`` followed by an indented map,
    and top-level ``key:`` followed by indented list items (``- foo``).
    """
    out: dict[str, Any] = {}
    section: str | None = None
    section_dict: dict[str, Any] = {}
    section_list: list[str] = []
    section_kind: str = "map"  # "map" | "list"
    last_list_key: str | None = None
    last_list: list[str] = []

    def _close_section() -> None:
        nonlocal section
        if section is None:
            return
        if section_kind == "list":
            out[section] = list(section_list)
        else:
            if last_list_key is not None and last_list:
                section_dict[last_list_key] = list(last_list)
            out[section] = dict(section_dict)

    for raw in text.splitlines():
        line = raw.split("#", 1)[0]
        if not line.strip():
            continue
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        if indent == 0 and stripped.endswith(":"):
            _close_section()
            section = stripped[:-1].strip()
            section_dict = {}
            section_list = []
            section_kind = "map"
            last_list_key = None
            last_list = []
            continue

        if indent > 0 and stripped.startswith("- ") and section is not None and last_list_key is None:
            # Top-level list under section.
            section_kind = "list"
            section_list.append(_strip_quotes(stripped[2:]))
            continue

        if indent > 0 and section is not None and ":" in stripped:
            if last_list_key is not None and last_list:
                section_dict[last_list_key] = list(last_list)
                last_list_key = None
                last_list = []
            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip()
            if not value:
                last_list_key = key
                last_list = []
                continue
            if value.startswith("["):
                section_dict[key] = _parse_list_inline(value)
            else:
                section_dict[key] = _strip_quotes(value)
            continue

        if indent > 0 and stripped.startswith("- ") and section is not None and last_list_key is not None:
            last_list.append(_strip_quotes(stripped[2:]))
            continue

    _close_section()
    return out


@lru_cache(maxsize=1)
def _load() -> RoutingTable:
    if not DEFAULT_PATH.exists():
        return RoutingTable(combat_agencies={}, control_agencies={}, medical_brand={})
    raw = _parse(DEFAULT_PATH.read_text(encoding="utf-8"))
    combat_raw = raw.get("combat_agencies", {})
    control_raw = raw.get("control_agencies", {})
    medical_raw = raw.get("medical_brand", {})
    ic_raw = raw.get("nsw_ic_eligible_roles", [])

    combat = {k: tuple(v) for k, v in combat_raw.items() if isinstance(v, list)}
    control = {k: tuple(v) for k, v in control_raw.items() if isinstance(v, list)}
    medical = {k: str(v) for k, v in medical_raw.items() if isinstance(v, str)}
    ic_list = tuple(ic_raw) if isinstance(ic_raw, list) else ()
    return RoutingTable(
        combat_agencies=combat,
        control_agencies=control,
        medical_brand=medical,
        nsw_ic_eligible_roles=ic_list,
    )


def reset_cache_for_tests() -> None:
    _load.cache_clear()


def combat_for(jurisdiction: str) -> tuple[str, ...]:
    return _load().combat_agencies.get(jurisdiction.upper(), ())


def control_for(jurisdiction: str) -> tuple[str, ...]:
    return _load().control_agencies.get(jurisdiction.upper(), ())


def police_for(jurisdiction: str) -> str | None:
    """Honour the FR-023 ACT-AFP override; otherwise first control entry."""
    juris = jurisdiction.upper()
    if juris == "ACT":
        return "Australian Federal Police"
    ctrl = control_for(juris)
    return ctrl[0] if ctrl else None


def medical_brand_for(jurisdiction: str) -> str | None:
    return _load().medical_brand.get(jurisdiction.upper())


def is_ic_eligible(jurisdiction: str, role: str) -> bool:
    """Return ``True`` if *role* may serve as Incident Controller for *jurisdiction*."""
    if jurisdiction.upper() != "NSW":
        return True  # FR-025 only restricts NSW
    return role in _load().nsw_ic_eligible_roles


__all__ = [
    "RoutingTable",
    "combat_for",
    "control_for",
    "is_ic_eligible",
    "medical_brand_for",
    "police_for",
    "reset_cache_for_tests",
]
