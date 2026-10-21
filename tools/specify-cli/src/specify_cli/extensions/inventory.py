from __future__ import annotations

import hashlib
import json
import os
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import rfc8785
import yaml

from specify_cli.extensions.models import ExtensionListEntry, project_entry

if TYPE_CHECKING:
    from specify_cli.extensions.catalogs import CatalogSourceRecord


_MARKER_FIELDS = {"schema_version", "feature", "fixture_id", "source_digest"}
_SHA256_LENGTH = 64
_STABLE_ID = re.compile(r"^[a-z0-9-]+$")


@dataclass(frozen=True, slots=True)
class ProjectContext:
    project_root: Path | None
    extensions_root: Path | None
    catalog_config: Path | None

    def __post_init__(self) -> None:
        if self.project_root is None:
            if self.extensions_root is not None or self.catalog_config is not None:
                raise ValueError("null project context cannot contain project paths")
            return
        expected_extensions = self.project_root / ".specify" / "extensions"
        if self.extensions_root != expected_extensions:
            raise ValueError("extensions root must belong to the project root")
        expected_catalog = expected_extensions / "catalogs.json"
        if self.catalog_config not in {None, expected_catalog}:
            raise ValueError("catalog configuration must belong to the extensions root")


def discover_project(start_path: Path | None = None) -> ProjectContext:
    start = Path.cwd() if start_path is None else Path(start_path)
    current = start.parent if start.is_file() else start
    current = current.resolve(strict=True)
    for candidate in (current, *current.parents):
        extensions_root = candidate / ".specify" / "extensions"
        if extensions_root.is_dir() and not extensions_root.is_symlink():
            catalog = extensions_root / "catalogs.json"
            catalog_config = catalog if catalog.is_file() and not catalog.is_symlink() else None
            return ProjectContext(candidate, extensions_root, catalog_config)
    return ProjectContext(None, None, None)


def _validate_owner_only_directory(path: Path, label: str) -> Path:
    if path.is_symlink():
        raise PermissionError(f"{label} must not be a symlink")
    try:
        resolved = path.resolve(strict=True)
    except FileNotFoundError as error:
        raise PermissionError(f"{label} is unavailable") from error
    metadata = resolved.stat()
    if hasattr(os, "getuid") and metadata.st_uid != os.getuid():
        raise PermissionError(f"{label} must be owned by the current user")
    return resolved


def _load_marker(path: Path) -> Mapping[str, object]:
    if not path.is_file() or path.is_symlink():
        raise PermissionError("closed synthetic fixture marker is required")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("synthetic fixture marker is invalid") from error
    if not isinstance(value, Mapping) or set(value) != _MARKER_FIELDS:
        raise ValueError("synthetic fixture marker is not closed")
    return value


def validate_local_fixture_access(
    context: ProjectContext,
    session_temp: Path,
    source_digest: str,
    *,
    synthetic_mode: bool,
) -> None:
    if context.project_root is None:
        return
    if not synthetic_mode:
        raise PermissionError("local data access requires synthetic mode")
    resolved_session = _validate_owner_only_directory(session_temp, "session temporary root")
    project_root = context.project_root
    if project_root.is_symlink():
        raise PermissionError("fixture root must not be a symlink")
    resolved_project = project_root.resolve(strict=True)
    if not resolved_project.is_relative_to(resolved_session):
        raise PermissionError("fixture root must be beneath the session temporary root")
    marker = _load_marker(resolved_project / ".spec001-synthetic-fixture.json")
    if marker["schema_version"] != "1.0" or marker["feature"] != "001-extension-list":
        raise ValueError("synthetic fixture marker binding mismatch")
    fixture_id = marker["fixture_id"]
    if not isinstance(fixture_id, str) or not fixture_id:
        raise ValueError("synthetic fixture ID is required")
    marker_digest = marker["source_digest"]
    if (
        not isinstance(marker_digest, str)
        or len(marker_digest) != _SHA256_LENGTH
        or any(character not in "0123456789abcdef" for character in marker_digest)
    ):
        raise ValueError("synthetic fixture source digest is invalid")
    if marker_digest != source_digest:
        raise PermissionError("synthetic fixture source digest mismatch")


def _read_mapping(path: Path, label: str) -> Mapping[str, object]:
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"{label} must be a regular file")
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as error:
        raise ValueError(f"{label} is invalid") from error
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must contain an object")
    return value


def _canonical_digest(value: object) -> str:
    return hashlib.sha256(rfc8785.dumps(value)).hexdigest()  # type: ignore[arg-type]


def _source_digest(source_location: str) -> str:
    return hashlib.sha256(source_location.encode("utf-8")).hexdigest()


def _source_directory(extensions_root: Path, value: object) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError("registry path must be a non-empty string")
    relative = Path(value)
    if relative.is_absolute():
        raise PermissionError("registry path must be project-relative")
    candidate = extensions_root / relative
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as error:
        raise ValueError("registry extension source is unavailable") from error
    resolved_extensions = extensions_root.resolve(strict=True)
    if not resolved.is_relative_to(resolved_extensions) or resolved == resolved_extensions:
        raise PermissionError("extension source escapes the extensions root")
    if not resolved.is_dir():
        raise ValueError("extension source must be a directory")
    return resolved


def _source_location(project_root: Path, source_directory: Path) -> str:
    return source_directory.relative_to(project_root.resolve(strict=True)).as_posix()


def _valid_text(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _positive_integer(value: object, default: int) -> int:
    if isinstance(value, int) and not isinstance(value, bool) and value > 0:
        return value
    return default


def _string_members(value: object) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, str | bytes):
        return ()
    return tuple(item for item in value if isinstance(item, str) and item)


def _registered_commands(value: object) -> tuple[str, ...]:
    if not isinstance(value, Mapping):
        return ()
    commands: list[str] = []
    for members in value.values():
        commands.extend(_string_members(members))
    return tuple(commands)


def _activation_details(
    registry: Mapping[str, object] | None,
    enabled: bool,
    source_location: str,
) -> tuple[str, str | None, tuple[dict[str, object], ...]]:
    if not enabled:
        return "disabled", None, ()
    if registry is None:
        return "inactive", None, ()
    raw_activation = registry.get("activation", registry.get("activation_evidence"))
    if isinstance(raw_activation, Mapping):
        state = raw_activation.get("state")
        if state in {"active", "inactive"}:
            return str(state), None, ()
        if state == "activation-failed":
            diagnostic = _valid_text(raw_activation.get("diagnostic")) or "Extension activation failed."
            return "activation-failed", diagnostic, ()
        return (
            "inactive",
            None,
            (
                _diagnostic(
                    "invalid-activation-state",
                    "Registry activation state is invalid.",
                    source_location,
                ),
            ),
        )
    if raw_activation is not None:
        return (
            "inactive",
            None,
            (
                _diagnostic(
                    "invalid-activation-state",
                    "Registry activation state is invalid.",
                    source_location,
                ),
            ),
        )
    if _registered_commands(registry.get("registered_commands")) or _string_members(registry.get("registered_skills")):
        return "active", None, ()
    return "inactive", None, ()


def _manifest_paths(extensions_root: Path) -> tuple[Path, ...]:
    paths: list[Path] = []
    for candidate in extensions_root.glob("*/extension.yml"):
        if candidate.is_symlink() or candidate.parent.is_symlink():
            raise PermissionError("extension manifest path must not be a symlink")
        resolved = candidate.resolve(strict=True)
        if not resolved.is_relative_to(extensions_root.resolve(strict=True)):
            raise PermissionError("extension manifest escapes the extensions root")
        paths.append(resolved)
    return tuple(sorted(paths, key=lambda path: path.as_posix()))


def _registry_records(extensions_root: Path) -> tuple[tuple[str, Mapping[str, object]], ...]:
    registry_path = extensions_root / ".registry"
    if not registry_path.exists():
        return ()
    registry = _read_mapping(registry_path, "extension registry")
    records: list[tuple[str, Mapping[str, object]]] = []
    for key, value in registry.items():
        if not isinstance(key, str) or not isinstance(value, Mapping):
            raise ValueError("extension registry entries must be objects")
        records.append((key, value))
    return tuple(sorted(records, key=lambda item: (item[0].casefold(), item[0])))


def _coalesced_registry(records: Sequence[tuple[str, Mapping[str, object]]]) -> Mapping[str, object] | None:
    if not records:
        return None
    merged: dict[str, object] = {}
    for _, record in records:
        for key, value in record.items():
            merged.setdefault(key, value)
    return merged


def _diagnostic(code: str, message: str, source: str | None) -> dict[str, object]:
    return {"code": code, "message": message, "source": source}


def _manifest_observation(
    project_root: Path,
    manifest_path: Path,
) -> tuple[Mapping[str, object], object, tuple[dict[str, object], ...]]:
    source_location = _source_location(project_root, manifest_path.parent)
    if not manifest_path.is_file() or manifest_path.is_symlink():
        diagnostic = _diagnostic(
            "manifest-unreadable",
            "Extension manifest is not a readable regular file.",
            source_location,
        )
        return {}, diagnostic, (diagnostic,)
    try:
        content = manifest_path.read_bytes()
    except OSError:
        diagnostic = _diagnostic("manifest-unreadable", "Extension manifest could not be read.", source_location)
        return {}, diagnostic, (diagnostic,)
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        diagnostic = _diagnostic(
            "manifest-unreadable",
            "Extension manifest could not be read as UTF-8.",
            source_location,
        )
        return {}, {"sha256": hashlib.sha256(content).hexdigest()}, (diagnostic,)
    try:
        value = yaml.safe_load(text)
    except yaml.YAMLError:
        diagnostic = _diagnostic("manifest-invalid", "Extension manifest metadata is invalid.", source_location)
        return {}, {"sha256": hashlib.sha256(content).hexdigest()}, (diagnostic,)
    if not isinstance(value, Mapping):
        diagnostic = _diagnostic("manifest-invalid", "Extension manifest must contain an object.", source_location)
        return {}, {"sha256": hashlib.sha256(content).hexdigest()}, (diagnostic,)
    return value, value, ()


def _entry_from_observations(
    project_root: Path,
    source_directory: Path,
    manifest: Mapping[str, object],
    registry: Mapping[str, object] | None,
    observations: Sequence[tuple[int, object]],
    metadata_diagnostics: Sequence[dict[str, object]] = (),
) -> ExtensionListEntry:
    source_location = _source_location(project_root, source_directory)
    diagnostics = list(metadata_diagnostics)
    conflict_reasons: list[str] = []
    parsed_manifest = bool(manifest) or not metadata_diagnostics
    identifier = _valid_text(manifest.get("id"))
    if identifier is None and parsed_manifest:
        diagnostics.append(
            _diagnostic(
                "missing-stable-id",
                "Extension manifest is missing a stable identifier.",
                source_location,
            )
        )
    elif identifier is not None and _STABLE_ID.fullmatch(identifier) is None:
        diagnostics.append(
            _diagnostic(
                "invalid-stable-id",
                "Extension manifest stable identifier is invalid.",
                source_location,
            )
        )
        identifier = None
    registry_identifier = _valid_text(registry.get("id")) if registry is not None else None
    if (
        identifier is not None
        and registry_identifier is not None
        and _STABLE_ID.fullmatch(registry_identifier) is not None
        and registry_identifier != identifier
    ):
        diagnostics.append(
            _diagnostic(
                "local-identity-conflict",
                "Registry and manifest stable identifiers disagree.",
                source_location,
            )
        )
        conflict_reasons.append("local-identity-conflict")
        identifier = None
    name = _valid_text(manifest.get("name"))
    if name is None:
        name = source_directory.name
        if parsed_manifest:
            diagnostics.append(
                _diagnostic("manifest-invalid", "Extension manifest name is missing or invalid.", source_location)
            )
    manifest_version = _valid_text(manifest.get("version"))
    registry_version = _valid_text(registry.get("version")) if registry is not None else None
    installed_version = registry_version or manifest_version
    enabled_value = registry.get("enabled", True) if registry is not None else True
    enabled = enabled_value if isinstance(enabled_value, bool) else True
    if registry is not None and "enabled" in registry and not isinstance(enabled_value, bool):
        diagnostics.append(
            _diagnostic("registry-metadata-invalid", "Registry enabled metadata is invalid.", source_location)
        )
    priority = _positive_integer(
        registry.get("priority") if registry is not None else None,
        _positive_integer(manifest.get("priority"), 10),
    )
    raw_manifest_commands = manifest.get("commands", ())
    manifest_commands = _string_members(raw_manifest_commands)
    if (
        not isinstance(raw_manifest_commands, Sequence)
        or isinstance(raw_manifest_commands, str | bytes)
        or len(manifest_commands) != len(raw_manifest_commands)
    ):
        diagnostics.append(
            _diagnostic("manifest-invalid", "Extension manifest commands contain invalid members.", source_location)
        )
    registry_commands = _registered_commands(registry.get("registered_commands")) if registry is not None else ()
    commands = tuple(dict.fromkeys((*manifest_commands, *registry_commands)))
    raw_hooks = manifest.get("hooks")
    hooks = tuple(raw_hooks) if isinstance(raw_hooks, Mapping) else ()
    activation_state, activation_diagnostic, activation_metadata_diagnostics = _activation_details(
        registry,
        enabled,
        source_location,
    )
    diagnostics.extend(activation_metadata_diagnostics)
    evidence = [
        {
            "kind": "local",
            "source_sha256": _source_digest(source_location),
            "source_ordinal": ordinal,
            "record_sha256": _canonical_digest(record),
        }
        for ordinal, record in observations
    ]
    return project_entry(
        {
            "id": identifier,
            "fallback_identity": source_location if identifier is None else None,
            "source_locations": [source_location],
            "name": name,
            "description": _valid_text(manifest.get("description")),
            "version": installed_version or "unknown",
            "priority": priority,
            "enabled": enabled,
            "source": {"kind": "local"},
            "evidence": evidence,
            "provides": {"commands": len(commands), "templates": 0, "scripts": 0, "hooks": len(hooks)},
            "install_allowed": None,
            "installed": True,
            "installed_version": installed_version,
            "available_versions": [],
            "activation_state": activation_state,
            "activation_diagnostic": activation_diagnostic,
            "health": {
                "state": "invalid" if diagnostics else "healthy",
                "diagnostics": sorted(diagnostics, key=lambda item: (str(item["code"]), str(item["source"] or ""))),
            },
            "conflict": bool(conflict_reasons),
            "conflict_reasons": conflict_reasons,
            "catalog_sources": [],
        }
    )


def _merge_duplicate_installed(entries: Sequence[ExtensionListEntry]) -> ExtensionListEntry:
    preferred = min(entries, key=lambda entry: (entry.source_locations[0], entry.name.casefold(), entry.name))
    identifier = preferred.id
    if identifier is None:
        raise ValueError("duplicate installed grouping requires a stable identifier")
    source_locations = sorted({location for entry in entries for location in entry.source_locations})
    evidence = [
        {
            "kind": item.kind,
            "source_sha256": item.source_sha256,
            "source_ordinal": item.source_ordinal,
            "record_sha256": item.record_sha256,
        }
        for entry in entries
        for item in entry.evidence
    ]
    diagnostics: list[dict[str, object]] = [
        {"code": item.code, "message": item.message, "source": item.source}
        for entry in entries
        for item in entry.health.diagnostics
    ]
    diagnostics.append(
        _diagnostic(
            "duplicate-installed-id",
            "Stable ID is installed from multiple physical sources.",
            None,
        )
    )
    unique_diagnostics = {(str(item["code"]), str(item["message"]), item["source"]): item for item in diagnostics}
    ordered_diagnostics = sorted(
        unique_diagnostics.values(),
        key=lambda item: (str(item["code"]), str(item["source"] or ""), str(item["message"])),
    )
    return project_entry(
        {
            "id": identifier,
            "fallback_identity": None,
            "source_locations": source_locations,
            "name": preferred.name,
            "description": preferred.description,
            "version": preferred.version,
            "priority": preferred.priority,
            "enabled": preferred.enabled,
            "source": {"kind": "local"},
            "evidence": evidence,
            "provides": {
                "commands": preferred.provides.commands,
                "templates": preferred.provides.templates,
                "scripts": preferred.provides.scripts,
                "hooks": preferred.provides.hooks,
            },
            "install_allowed": None,
            "installed": True,
            "installed_version": preferred.installed_version,
            "available_versions": [],
            "activation_state": preferred.activation_state,
            "activation_diagnostic": preferred.activation_diagnostic,
            "health": {"state": "invalid", "diagnostics": ordered_diagnostics},
            "conflict": True,
            "conflict_reasons": ["duplicate-installed-id"],
            "catalog_sources": [],
        }
    )


def _group_installed_entries(entries: Sequence[ExtensionListEntry]) -> tuple[ExtensionListEntry, ...]:
    by_identifier: dict[str, list[ExtensionListEntry]] = {}
    fallback_entries: list[ExtensionListEntry] = []
    for entry in entries:
        if entry.id is None:
            fallback_entries.append(entry)
        else:
            by_identifier.setdefault(entry.id, []).append(entry)
    grouped = list(fallback_entries)
    for identifier in sorted(by_identifier):
        candidates = by_identifier[identifier]
        grouped.append(candidates[0] if len(candidates) == 1 else _merge_duplicate_installed(candidates))
    return tuple(
        sorted(
            grouped,
            key=lambda entry: (entry.name.casefold(), entry.name, entry.id or "", entry.fallback_identity or ""),
        )
    )


def load_installed_entries(
    start_path: Path,
    *,
    session_temp: Path,
    source_digest: str,
    synthetic_mode: bool,
) -> tuple[ExtensionListEntry, ...]:
    context = discover_project(start_path)
    if context.project_root is None or context.extensions_root is None:
        return ()
    validate_local_fixture_access(context, session_temp, source_digest, synthetic_mode=synthetic_mode)

    manifest_by_source: dict[Path, tuple[Mapping[str, object], object, tuple[dict[str, object], ...]]] = {}
    for manifest_path in _manifest_paths(context.extensions_root):
        manifest_by_source[manifest_path.parent] = _manifest_observation(context.project_root, manifest_path)

    registry_by_source: dict[Path, list[tuple[str, Mapping[str, object]]]] = {}
    registry_observations: dict[Path, list[tuple[int, Mapping[str, object]]]] = {}
    ordinal = 0
    for registry_key, registry in _registry_records(context.extensions_root):
        source_directory = _source_directory(context.extensions_root, registry.get("path"))
        registry_by_source.setdefault(source_directory, []).append((registry_key, registry))
        registry_observations.setdefault(source_directory, []).append((ordinal, registry))
        ordinal += 1

    entries: list[ExtensionListEntry] = []
    all_sources = sorted(set(manifest_by_source) | set(registry_by_source), key=lambda path: path.as_posix())
    physical_ordinals = {
        source: ordinal + index
        for index, source in enumerate(sorted(manifest_by_source, key=lambda path: path.as_posix()))
    }
    for source_directory in all_sources:
        manifest_observation = manifest_by_source.get(source_directory)
        if manifest_observation is None:
            source_location = _source_location(context.project_root, source_directory)
            missing_diagnostic = _diagnostic(
                "manifest-unreadable",
                "Registered extension manifest is unavailable.",
                source_location,
            )
            manifest: Mapping[str, object] = {}
            manifest_record: object = missing_diagnostic
            manifest_diagnostics = (missing_diagnostic,)
        else:
            manifest, manifest_record, manifest_diagnostics = manifest_observation  # type: ignore[assignment]
        observations: list[tuple[int, object]] = []
        observations.extend(registry_observations.get(source_directory, ()))
        observations.append((physical_ordinals.get(source_directory, ordinal), manifest_record))
        coalesced_registry = _coalesced_registry(registry_by_source.get(source_directory, ()))
        entries.append(
            _entry_from_observations(
                context.project_root,
                source_directory,
                manifest,
                coalesced_registry,
                observations,
                manifest_diagnostics,
            )
        )
    return _group_installed_entries(entries)


def _catalog_sort_key(record: CatalogSourceRecord) -> tuple[object, ...]:
    return (
        record.catalog_priority,
        record.catalog_name.casefold(),
        record.catalog_name,
        record.record_sha256,
        record.source_ordinal,
    )


def _catalog_provides(record: CatalogSourceRecord) -> tuple[int, int, int, int]:
    return (record.commands, record.templates, record.scripts, record.hooks)


def _catalog_conflict_reasons(records: Sequence[CatalogSourceRecord]) -> tuple[str, ...]:
    if len(records) < 2:
        return ()
    differing_fields: list[str] = []
    comparisons: dict[str, set[object]] = {
        "description": {record.description for record in records},
        "install_allowed": {record.install_allowed for record in records},
        "name": {record.name for record in records},
        "provides": {_catalog_provides(record) for record in records},
    }
    for field_name, values in comparisons.items():
        if len(values) > 1:
            differing_fields.append(f"catalog-field-diff:{field_name}")
    differing_fields.append("duplicate-catalog-id")
    return tuple(differing_fields)


def _catalog_evidence(records: Sequence[CatalogSourceRecord]) -> list[dict[str, object]]:
    return [
        {
            "kind": "catalog",
            "source_sha256": record.source_sha256,
            "source_ordinal": record.source_ordinal,
            "record_sha256": record.record_sha256,
        }
        for record in records
    ]


def _catalog_diagnostic(reason: str) -> dict[str, object]:
    messages = {
        "duplicate-catalog-id": "Stable ID is present in multiple catalog records.",
        "installed-version-mismatch": "Installed and available extension versions differ.",
    }
    if reason.startswith("catalog-field-diff:"):
        field_name = reason.partition(":")[2]
        message = f"Catalog records differ for field: {field_name}."
    else:
        message = messages[reason]
    return _diagnostic(reason, message, None)


def _catalog_only_entry(records: Sequence[CatalogSourceRecord]) -> ExtensionListEntry:
    preferred = min(records, key=_catalog_sort_key)
    conflict_reasons = _catalog_conflict_reasons(records)
    versions = sorted({record.available_version or "unknown" for record in records})
    return project_entry(
        {
            "id": preferred.stable_id,
            "fallback_identity": None,
            "source_locations": [],
            "name": preferred.name,
            "description": preferred.description,
            "version": preferred.available_version or "unknown",
            "priority": None,
            "enabled": None,
            "source": {"kind": "catalog"},
            "evidence": _catalog_evidence(records),
            "provides": {
                "commands": preferred.commands,
                "templates": preferred.templates,
                "scripts": preferred.scripts,
                "hooks": preferred.hooks,
            },
            "install_allowed": all(record.install_allowed for record in records),
            "installed": False,
            "installed_version": None,
            "available_versions": versions,
            "activation_state": None,
            "activation_diagnostic": None,
            "health": {
                "state": "invalid" if conflict_reasons else "healthy",
                "diagnostics": [_catalog_diagnostic(reason) for reason in conflict_reasons],
            },
            "conflict": bool(conflict_reasons),
            "conflict_reasons": list(conflict_reasons),
            "catalog_sources": sorted({record.source_sha256 for record in records}),
        }
    )


def _combined_entry(installed: ExtensionListEntry, records: Sequence[CatalogSourceRecord]) -> ExtensionListEntry:
    conflict_reasons = [*installed.conflict_reasons, *_catalog_conflict_reasons(records)]
    versions = sorted({record.available_version or "unknown" for record in records})
    if installed.installed_version is not None and installed.installed_version not in versions:
        conflict_reasons.append("installed-version-mismatch")
    conflict_reasons = list(dict.fromkeys(conflict_reasons))
    diagnostics: list[dict[str, object]] = [
        {"code": item.code, "message": item.message, "source": item.source} for item in installed.health.diagnostics
    ]
    existing_codes = {str(item["code"]) for item in diagnostics}
    diagnostics.extend(_catalog_diagnostic(reason) for reason in conflict_reasons if reason not in existing_codes)
    evidence = [
        {
            "kind": item.kind,
            "source_sha256": item.source_sha256,
            "source_ordinal": item.source_ordinal,
            "record_sha256": item.record_sha256,
        }
        for item in installed.evidence
    ]
    evidence.extend(_catalog_evidence(records))
    return project_entry(
        {
            "id": installed.id,
            "fallback_identity": None,
            "source_locations": list(installed.source_locations),
            "name": installed.name,
            "description": installed.description,
            "version": installed.version,
            "priority": installed.priority,
            "enabled": installed.enabled,
            "source": {"kind": "combined"},
            "evidence": evidence,
            "provides": {
                "commands": installed.provides.commands,
                "templates": installed.provides.templates,
                "scripts": installed.provides.scripts,
                "hooks": installed.provides.hooks,
            },
            "install_allowed": all(record.install_allowed for record in records),
            "installed": True,
            "installed_version": installed.installed_version,
            "available_versions": versions,
            "activation_state": installed.activation_state,
            "activation_diagnostic": installed.activation_diagnostic,
            "health": {
                "state": "invalid" if diagnostics else "healthy",
                "diagnostics": sorted(
                    diagnostics,
                    key=lambda item: (str(item["code"]), str(item["source"] or ""), str(item["message"])),
                ),
            },
            "conflict": bool(conflict_reasons),
            "conflict_reasons": conflict_reasons,
            "catalog_sources": sorted({record.source_sha256 for record in records}),
        }
    )


def reconcile_entries(
    installed_entries: Sequence[ExtensionListEntry],
    catalog_records: Sequence[CatalogSourceRecord],
) -> tuple[ExtensionListEntry, ...]:
    catalogs_by_id: dict[str, list[CatalogSourceRecord]] = {}
    for record in catalog_records:
        catalogs_by_id.setdefault(record.stable_id, []).append(record)
    installed_by_id = {entry.id: entry for entry in installed_entries if entry.id is not None}
    rows: list[ExtensionListEntry] = []
    rows.extend(entry for entry in installed_entries if entry.id is None)
    for identifier in sorted(set(installed_by_id) | set(catalogs_by_id)):
        installed = installed_by_id.get(identifier)
        catalog_candidates = catalogs_by_id.get(identifier, [])
        if installed is None:
            rows.append(_catalog_only_entry(catalog_candidates))
        elif not catalog_candidates:
            rows.append(installed)
        else:
            rows.append(_combined_entry(installed, catalog_candidates))
    return tuple(
        sorted(
            rows,
            key=lambda entry: (entry.name.casefold(), entry.name, entry.id or "", entry.fallback_identity or ""),
        )
    )
