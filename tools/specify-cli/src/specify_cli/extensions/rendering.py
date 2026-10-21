from __future__ import annotations

from collections.abc import Sequence
from io import StringIO
from typing import Literal

from rich.console import Console
from rich.text import Text

from specify_cli.extensions.models import ExtensionListEntry, serialize_entries

_EMPTY_TEXT = {
    "installed": "No extensions installed.\n",
    "available": "No catalog extensions available.\n",
    "all": "No installed or catalog extensions found.\n",
}


def _row_lines(entry: ExtensionListEntry) -> tuple[str, ...]:
    identity = f"ID: {entry.id}" if entry.id is not None else f"Source: {entry.fallback_identity}"
    lines = [entry.name, identity, f"Version: {entry.version}"]
    if entry.description is not None:
        lines.append(f"Description: {entry.description}")
    lines.extend(
        (
            f"Installed: {'yes' if entry.installed else 'no'}",
            f"Activation: {entry.activation_state or 'not-installed'}",
            f"Health: {entry.health.state}",
        )
    )
    if entry.available_versions:
        lines.append(f"Available versions: {', '.join(entry.available_versions)}")
    if entry.install_allowed is not None:
        lines.append(f"Install allowed: {'yes' if entry.install_allowed else 'no'}")
    if entry.catalog_sources:
        lines.append(f"Catalog sources: {len(entry.catalog_sources)}")
    if entry.conflict_reasons:
        lines.append(f"Conflict: {', '.join(entry.conflict_reasons)}")
    if entry.activation_diagnostic is not None:
        lines.append(f"Activation diagnostic: {entry.activation_diagnostic}")
    lines.extend(
        f"Metadata diagnostic [{diagnostic.code}]: {diagnostic.message}" for diagnostic in entry.health.diagnostics
    )
    lines.extend((f"Commands: {entry.provides.commands}", f"Hooks: {entry.provides.hooks}"))
    return tuple(lines)


def render_entries(
    entries: Sequence[ExtensionListEntry],
    *,
    view: str,
    output_json: bool,
    width: int | None = None,
    color_system: Literal["auto", "standard", "256", "truecolor", "windows"] | None = None,
    force_terminal: bool | None = False,
) -> str:
    if view not in _EMPTY_TEXT:
        raise ValueError("extension list view is invalid")
    if output_json:
        return serialize_entries(entries)
    if not entries:
        return _EMPTY_TEXT[view]

    buffer = StringIO()
    console = Console(
        file=buffer,
        width=width,
        color_system=color_system,
        force_terminal=force_terminal,
        no_color=color_system is None,
        highlight=False,
        markup=False,
    )
    for index, entry in enumerate(entries):
        for line in _row_lines(entry):
            console.print(Text(line))
        if index < len(entries) - 1:
            console.print()
    return buffer.getvalue()
