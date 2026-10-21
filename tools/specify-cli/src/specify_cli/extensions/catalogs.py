from __future__ import annotations

import hashlib
import ipaddress
import json
import multiprocessing
import queue
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, cast
from urllib.parse import urljoin, urlparse

import rfc8785

from specify_cli.extensions.inventory import discover_project, validate_local_fixture_access

_MAX_SOURCE_BYTES = 1_048_576
_MAX_REDIRECTS = 5
_AU_LOCATIONS = {"australiaeast", "australiasoutheast"}


class CatalogSourceError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class CatalogSourceRecord:
    stable_id: str
    name: str
    available_version: str | None
    description: str | None
    author: str | None
    catalog_name: str
    catalog_priority: int
    source_ordinal: int
    source_sha256: str
    record_sha256: str
    install_allowed: bool
    commands: int
    templates: int
    scripts: int
    hooks: int


@dataclass(frozen=True, slots=True)
class CatalogCollection:
    records: tuple[CatalogSourceRecord, ...]
    warning: str | None


@dataclass(frozen=True, slots=True)
class SourceDeadline:
    clock: Callable[[], float] = time.monotonic
    duration: float = 5.0
    deadline: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "deadline", self.clock() + self.duration)

    def remaining(self) -> float:
        remaining = self.deadline - self.clock()
        if remaining <= 0:
            raise CatalogSourceError("catalog-source-deadline-exceeded")
        return remaining


class DeadlineTransport(Protocol):
    def get(self, url: str, timeout: float) -> object: ...


def _schema_path(name: str) -> Path:
    return Path(__file__).resolve(strict=True).parents[5] / "specs" / "001-extension-list" / "contracts" / name


def _validate_schema(value: object, schema_name: str) -> None:
    from jsonschema import Draft202012Validator

    schema = json.loads(_schema_path(schema_name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(value)


def _read_json(path: Path, label: str) -> object:
    if not path.is_file() or path.is_symlink():
        raise CatalogSourceError(f"{label} must be a regular file")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CatalogSourceError(f"{label} is invalid") from error


def _contained_local_path(project_root: Path, configured_path: object) -> Path:
    if not isinstance(configured_path, str) or not configured_path:
        raise CatalogSourceError("catalog path is invalid")
    relative_path = Path(configured_path)
    if relative_path.is_absolute():
        raise CatalogSourceError("catalog path must be project-relative")
    candidate = project_root / ".specify" / "extensions" / relative_path
    if candidate.is_symlink():
        raise PermissionError("catalog source must not be a symlink")
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as error:
        raise CatalogSourceError("catalog source is unavailable") from error
    extensions_root = (project_root / ".specify" / "extensions").resolve(strict=True)
    if not resolved.is_relative_to(extensions_root) or resolved == extensions_root:
        raise PermissionError("catalog source escapes the extensions root")
    return resolved


def _load_configuration(path: Path) -> tuple[Mapping[str, object], ...]:
    value = _read_json(path, "catalog configuration")
    try:
        _validate_schema(value, "catalog-config.schema.json")
    except Exception as error:
        raise CatalogSourceError("configuration is invalid") from error
    if not isinstance(value, Mapping) or not isinstance(value.get("catalogs"), list):
        raise CatalogSourceError("configuration is invalid")
    catalogs = tuple(value["catalogs"])
    names = [entry["name"] for entry in catalogs if isinstance(entry, Mapping)]
    if len(names) != len(set(names)):
        raise CatalogSourceError("duplicate catalog name")
    return catalogs


def _source_digest(catalog_name: str) -> str:
    return hashlib.sha256(catalog_name.encode("utf-8")).hexdigest()


def _record_from_mapping(
    value: Mapping[str, object],
    *,
    catalog_name: str,
    catalog_priority: int,
    ordinal: int,
) -> CatalogSourceRecord:
    provides = value.get("provides")
    counts = provides if isinstance(provides, Mapping) else {}
    version = value.get("version")
    description = value.get("description")
    author = value.get("author")
    return CatalogSourceRecord(
        stable_id=str(value["id"]),
        name=str(value["name"]),
        available_version=version if isinstance(version, str) else None,
        description=description if isinstance(description, str) else None,
        author=author if isinstance(author, str) else None,
        catalog_name=catalog_name,
        catalog_priority=catalog_priority,
        source_ordinal=ordinal,
        source_sha256=_source_digest(catalog_name),
        record_sha256=hashlib.sha256(rfc8785.dumps(value)).hexdigest(),  # type: ignore[arg-type]
        install_allowed=bool(value["install_allowed"]),
        commands=cast(int, counts.get("commands", 0)),
        templates=cast(int, counts.get("templates", 0)),
        scripts=cast(int, counts.get("scripts", 0)),
        hooks=cast(int, counts.get("hooks", 0)),
    )


def _load_bounded_source(path: Path, deadline: SourceDeadline) -> object:
    metadata = run_deadline_stage(deadline, path.stat)
    if metadata.st_size > _MAX_SOURCE_BYTES:
        raise CatalogSourceError("catalog-source-too-large")

    def read_bounded() -> bytes:
        with path.open("rb") as source:
            return source.read(_MAX_SOURCE_BYTES + 1)

    payload = run_deadline_stage(deadline, read_bounded)
    if len(payload) > _MAX_SOURCE_BYTES:
        raise CatalogSourceError("catalog-source-too-large")
    try:
        text = run_deadline_stage(deadline, lambda: payload.decode("utf-8"))
    except UnicodeDecodeError as error:
        raise CatalogSourceError("source is invalid") from error
    try:
        return run_deadline_stage(deadline, lambda: json.loads(text))
    except json.JSONDecodeError as error:
        raise CatalogSourceError("source is invalid") from error


def _load_local_source(project_root: Path, entry: Mapping[str, object]) -> tuple[CatalogSourceRecord, ...]:
    source_path = _contained_local_path(project_root, entry.get("path"))
    deadline = SourceDeadline()
    value = _load_bounded_source(source_path, deadline)
    try:
        run_deadline_stage(deadline, lambda: _validate_schema(value, "catalog-source.schema.json"))
    except Exception as error:
        raise CatalogSourceError("source is invalid") from error
    if not isinstance(value, Mapping) or not isinstance(value.get("extensions"), list):
        raise CatalogSourceError("source is invalid")
    return tuple(
        _record_from_mapping(
            record,
            catalog_name=str(entry["name"]),
            catalog_priority=cast(int, entry["priority"]),
            ordinal=ordinal,
        )
        for ordinal, record in enumerate(value["extensions"])
        if isinstance(record, Mapping)
    )


class _RequestsDeadlineTransport:
    def get(self, url: str, timeout: float) -> object:
        import requests

        response = requests.get(url, timeout=timeout, stream=True, allow_redirects=False)
        return type(
            "DeadlineResponse",
            (),
            {
                "status_code": response.status_code,
                "headers": response.headers,
                "chunks": response.iter_content(chunk_size=64 * 1024),
            },
        )()


def _remote_fetch_operation(url: str, approved_host: str, duration: float) -> bytes:
    return fetch_remote_bytes(
        url,
        approved_host=approved_host,
        transport=_RequestsDeadlineTransport(),
        deadline=SourceDeadline(duration=duration),
    )


def _load_remote_source(
    entry: Mapping[str, object],
    *,
    precondition_loader: Callable[[Mapping[str, object]], Mapping[str, object]],
    authorization_loader: Callable[[Mapping[str, object]], Mapping[str, object]],
    clock: Callable[[], float],
    context_factory: Callable[[str], object],
) -> tuple[CatalogSourceRecord, ...]:
    deadline = SourceDeadline(clock=clock)
    preconditions = run_deadline_stage(deadline, lambda: precondition_loader(entry))
    authorization_inventory = run_deadline_stage(deadline, lambda: authorization_loader(entry))
    if not isinstance(preconditions, Mapping) or not isinstance(authorization_inventory, Mapping):
        raise CatalogSourceError("remote catalog verification is invalid")
    run_deadline_stage(
        deadline,
        lambda: authorize_remote_catalog_access(entry, preconditions, authorization_inventory),
    )
    url = str(entry["url"])
    approved_host = urlparse(url).hostname
    if approved_host is None:
        raise CatalogSourceError("remote catalog URL is invalid")
    payload = run_spawned(
        _remote_fetch_operation,
        (url, approved_host, deadline.remaining()),
        deadline=deadline,
        context_factory=context_factory,
    )
    if not isinstance(payload, bytes):
        raise CatalogSourceError("remote catalog worker result is invalid")
    try:
        text = run_deadline_stage(deadline, lambda: payload.decode("utf-8"))
        value = run_deadline_stage(deadline, lambda: json.loads(text))
        run_deadline_stage(deadline, lambda: _validate_schema(value, "catalog-source.schema.json"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CatalogSourceError("source is invalid") from error
    if not isinstance(value, Mapping) or not isinstance(value.get("extensions"), list):
        raise CatalogSourceError("source is invalid")
    return tuple(
        _record_from_mapping(
            record,
            catalog_name=str(entry["name"]),
            catalog_priority=cast(int, entry["priority"]),
            ordinal=ordinal,
        )
        for ordinal, record in enumerate(value["extensions"])
        if isinstance(record, Mapping)
    )


def validate_remote_catalog_access(
    entry: Mapping[str, object],
    preconditions: Mapping[str, object],
    *,
    reader_authorized: bool,
) -> None:
    url = str(entry.get("url", ""))
    parsed = urlparse(url)
    account_resource_id = str(entry.get("storage_account_resource_id", ""))
    container_scope = str(entry.get("container_scope", ""))
    account_name = account_resource_id.rsplit("/", 1)[-1]
    expected_host = f"{account_name}.blob.core.windows.net"
    if parsed.scheme != "https" or parsed.hostname != expected_host:
        raise PermissionError("remote catalog host does not match the storage account")
    if not container_scope.startswith(account_resource_id + "/blobServices/default/containers/"):
        raise PermissionError("remote catalog container scope does not match the storage account")
    if preconditions.get("account_resource_id") != account_resource_id:
        raise PermissionError("storage ARM resource mismatch")
    if preconditions.get("location") not in _AU_LOCATIONS:
        raise PermissionError("storage account must be in an Australian region")
    if preconditions.get("public_network_access") != "Disabled":
        raise PermissionError("storage public access must be disabled")
    if preconditions.get("default_action") != "Deny":
        raise PermissionError("storage network rules must use default Deny")
    if preconditions.get("approved_private_endpoint") is not True:
        raise PermissionError("storage requires an approved private endpoint")
    if preconditions.get("blob_host") != expected_host:
        raise PermissionError("verified storage host mismatch")
    addresses = preconditions.get("private_addresses")
    if not isinstance(addresses, Sequence) or isinstance(addresses, str | bytes) or not addresses:
        raise PermissionError("private DNS result is required")
    try:
        if not all(ipaddress.ip_address(str(address)).is_private for address in addresses):
            raise PermissionError("private DNS must resolve only to private addresses")
    except ValueError as error:
        raise PermissionError("private DNS result is invalid") from error
    if not reader_authorized:
        raise PermissionError("Storage Blob Data Reader authorization is required")


def authorize_remote_catalog_access(
    entry: Mapping[str, object],
    preconditions: Mapping[str, object],
    authorization_inventory: Mapping[str, object],
) -> None:
    from specify_cli.azure_authorization import evaluate_storage_blob_authorization

    decision = evaluate_storage_blob_authorization(authorization_inventory)
    validate_remote_catalog_access(entry, preconditions, reader_authorized=decision.authorized)


def _warning(error: Exception) -> str:
    message = str(error)
    if message in {"duplicate catalog name", "configuration is invalid", "source is invalid"}:
        return f"Catalog unavailable: {message}."
    return "Catalog unavailable: source is invalid."


def collect_catalog_records(
    start_path: Path,
    *,
    session_temp: Path,
    source_digest: str,
    synthetic_mode: bool,
    remote_precondition_loader: Callable[[Mapping[str, object]], Mapping[str, object]] | None = None,
    authorization_inventory_loader: Callable[[Mapping[str, object]], Mapping[str, object]] | None = None,
    clock: Callable[[], float] = time.monotonic,
    context_factory: Callable[[str], object] = multiprocessing.get_context,
) -> CatalogCollection:
    context = discover_project(start_path)
    if context.project_root is None:
        return CatalogCollection((), None)
    validate_local_fixture_access(context, session_temp, source_digest, synthetic_mode=synthetic_mode)
    if context.catalog_config is None:
        return CatalogCollection((), None)
    try:
        configuration = _load_configuration(context.catalog_config)
        records: list[CatalogSourceRecord] = []
        for entry in configuration:
            if "path" in entry:
                records.extend(_load_local_source(context.project_root, entry))
                continue
            if remote_precondition_loader is None or authorization_inventory_loader is None:
                raise CatalogSourceError("production remote catalogs require sovereign injected access")
            records.extend(
                _load_remote_source(
                    entry,
                    precondition_loader=remote_precondition_loader,
                    authorization_loader=authorization_inventory_loader,
                    clock=clock,
                    context_factory=context_factory,
                )
            )
        return CatalogCollection(tuple(records), None)
    except (CatalogSourceError, PermissionError) as error:
        return CatalogCollection((), _warning(error))


def run_deadline_stage[T](deadline: SourceDeadline, action: Callable[[], T]) -> T:
    deadline.remaining()
    result = action()
    deadline.remaining()
    return result


def fetch_remote_bytes(
    url: str,
    *,
    approved_host: str,
    transport: DeadlineTransport,
    deadline: SourceDeadline,
    max_redirects: int = _MAX_REDIRECTS,
) -> bytes:
    current_url = url
    redirects = 0
    body = bytearray()
    while True:
        parsed = urlparse(current_url)
        if parsed.scheme != "https" or parsed.hostname != approved_host:
            raise CatalogSourceError("remote redirect target must use HTTPS on the approved host")
        response = transport.get(current_url, deadline.remaining())
        deadline.remaining()
        status_code = getattr(response, "status_code", None)
        headers = getattr(response, "headers", None)
        if status_code in {301, 302, 303, 307, 308}:
            if redirects >= max_redirects:
                raise CatalogSourceError("remote redirect limit exceeded")
            if not isinstance(headers, Mapping):
                raise CatalogSourceError("remote redirect is invalid")
            location = headers.get("location") or headers.get("Location")
            if not isinstance(location, str) or not location:
                raise CatalogSourceError("remote redirect is invalid")
            current_url = urljoin(current_url, location)
            redirects += 1
            continue
        if status_code != 200:
            raise CatalogSourceError("remote catalog request failed")
        chunks = getattr(response, "chunks", None)
        if chunks is None:
            raise CatalogSourceError("remote catalog response is invalid")
        for chunk in chunks:
            deadline.remaining()
            if not isinstance(chunk, bytes):
                raise CatalogSourceError("remote catalog response is invalid")
            body.extend(chunk)
            if len(body) > _MAX_SOURCE_BYTES:
                raise CatalogSourceError("catalog-source-too-large")
            deadline.remaining()
        return bytes(body)


def _spawn_worker(result_queue: object, operation: Callable[..., object], arguments: tuple[object, ...]) -> None:
    try:
        result = operation(*arguments)
        result_queue.put(("ok", result))  # type: ignore[attr-defined]
    except Exception as error:
        result_queue.put(("error", str(error)))  # type: ignore[attr-defined]


def run_spawned(
    operation: Callable[..., object],
    arguments: tuple[object, ...],
    *,
    deadline: SourceDeadline,
    context_factory: Callable[[str], object] = multiprocessing.get_context,
) -> object:
    context = context_factory("spawn")
    result_queue = context.Queue()  # type: ignore[attr-defined]
    process = context.Process(  # type: ignore[attr-defined]
        target=_spawn_worker, args=(result_queue, operation, arguments)
    )
    try:
        process.start()
        process.join(deadline.remaining())
        if process.is_alive():
            process.terminate()
            process.join(min(0.25, deadline.duration))
            raise CatalogSourceError("catalog-source-deadline-exceeded")
        try:
            status, value = result_queue.get(timeout=deadline.remaining())
        except queue.Empty as error:
            raise CatalogSourceError("remote catalog worker returned no result") from error
        if status != "ok":
            raise CatalogSourceError(str(value))
        return value
    finally:
        if process.is_alive():
            process.terminate()
            process.join(min(0.25, deadline.duration))
        process.close()
        result_queue.close()
        result_queue.join_thread()
