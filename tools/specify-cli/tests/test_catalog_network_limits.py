from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest


def _load_cases() -> ModuleType:
    fixture_path = Path(__file__).resolve().parent / "fixtures" / "catalog_remote_cases.py"
    spec = importlib.util.spec_from_file_location("spec001_catalog_network_cases", fixture_path)
    if spec is None or spec.loader is None:
        raise ImportError("cannot load catalog network fixture builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CASES = _load_cases()


@pytest.mark.parametrize("stage", ["dns", "connect", "redirect", "stream", "decode", "parse", "schema"])
def test_catalog_deadline_one_five_second_budget_covers_every_stage(stage: str) -> None:
    from specify_cli.extensions.catalogs import CatalogSourceError, SourceDeadline, run_deadline_stage

    clock = CASES.FakeClock()
    deadline = SourceDeadline(clock=clock)

    def exhaust_budget() -> str:
        clock.advance(5.0)
        return stage

    with pytest.raises(CatalogSourceError, match="catalog-source-deadline-exceeded"):
        run_deadline_stage(deadline, exhaust_budget)


def test_catalog_deadline_remaining_budget_is_passed_to_each_redirect_and_stream() -> None:
    from specify_cli.extensions.catalogs import SourceDeadline, fetch_remote_bytes

    clock = CASES.FakeClock()
    first = "https://spec001catalog.blob.core.windows.net/extensions/first.json"
    second = "https://spec001catalog.blob.core.windows.net/extensions/second.json"
    transport = CASES.FakeDeadlineTransport(
        {
            first: CASES.FakeHttpResponse(302, {"location": second}, ()),
            second: CASES.FakeHttpResponse(200, {}, (b'{"schema_version":"1.0",', b'"extensions":[]}')),
        },
        clock=clock,
        stage_cost=0.25,
    )

    body = fetch_remote_bytes(
        first,
        approved_host="spec001catalog.blob.core.windows.net",
        transport=transport,
        deadline=SourceDeadline(clock=clock),
    )

    assert body == b'{"schema_version":"1.0","extensions":[]}'
    assert [url for url, _ in transport.calls] == [first, second]
    assert transport.calls[0][1] == pytest.approx(5.0)
    assert transport.calls[1][1] < transport.calls[0][1]


def test_catalog_deadline_redirect_host_and_count_are_revalidated() -> None:
    from specify_cli.extensions.catalogs import CatalogSourceError, SourceDeadline, fetch_remote_bytes

    clock = CASES.FakeClock()
    start = "https://spec001catalog.blob.core.windows.net/extensions/0.json"
    wrong_host = "https://other.blob.core.windows.net/extensions/catalog.json"
    wrong_transport = CASES.FakeDeadlineTransport({start: CASES.FakeHttpResponse(302, {"location": wrong_host}, ())})
    with pytest.raises(CatalogSourceError, match="approved host"):
        fetch_remote_bytes(
            start,
            approved_host="spec001catalog.blob.core.windows.net",
            transport=wrong_transport,
            deadline=SourceDeadline(clock=clock),
        )

    urls = [f"https://spec001catalog.blob.core.windows.net/extensions/{index}.json" for index in range(7)]
    loop_transport = CASES.FakeDeadlineTransport(
        {url: CASES.FakeHttpResponse(302, {"location": urls[index + 1]}, ()) for index, url in enumerate(urls[:-1])}
    )
    with pytest.raises(CatalogSourceError, match="redirect limit"):
        fetch_remote_bytes(
            urls[0],
            approved_host="spec001catalog.blob.core.windows.net",
            transport=loop_transport,
            deadline=SourceDeadline(clock=CASES.FakeClock()),
        )


def test_catalog_deadline_decoded_body_limit_is_one_mibibyte() -> None:
    from specify_cli.extensions.catalogs import CatalogSourceError, SourceDeadline, fetch_remote_bytes

    url = "https://spec001catalog.blob.core.windows.net/extensions/catalog.json"
    transport = CASES.FakeDeadlineTransport({url: CASES.FakeHttpResponse(200, {}, (b"x" * 1_048_577,))})

    with pytest.raises(CatalogSourceError, match="catalog-source-too-large"):
        fetch_remote_bytes(
            url,
            approved_host="spec001catalog.blob.core.windows.net",
            transport=transport,
            deadline=SourceDeadline(clock=CASES.FakeClock()),
        )


def test_catalog_deadline_spawn_worker_is_module_level_and_resources_close_on_success() -> None:
    from specify_cli.extensions.catalogs import SourceDeadline, run_spawned

    clock = CASES.FakeClock()
    context = CASES.FakeSpawnContext(run_target=True)
    selected: list[str] = []

    def context_factory(method: str) -> object:
        selected.append(method)
        return context

    result = run_spawned(
        bytes,
        (b"catalog",),
        deadline=SourceDeadline(clock=clock),
        context_factory=context_factory,
    )

    assert result == b"catalog"
    assert selected == ["spawn"]
    assert context.processes[0].target.__module__ == "specify_cli.extensions.catalogs"
    assert context.processes[0].target.__name__ == "_spawn_worker"
    assert context.processes[0].started is True
    assert context.processes[0].join_timeouts
    assert context.processes[0].closed is True
    assert context.queues[0].closed is True
    assert context.queues[0].joined is True


def test_catalog_deadline_timeout_terminates_boundedly_joins_and_closes_all_resources() -> None:
    from specify_cli.extensions.catalogs import CatalogSourceError, SourceDeadline, run_spawned

    context = CASES.FakeSpawnContext(run_target=False)
    with pytest.raises(CatalogSourceError, match="catalog-source-deadline-exceeded"):
        run_spawned(
            bytes,
            (b"never-returned",),
            deadline=SourceDeadline(clock=CASES.FakeClock()),
            context_factory=lambda _: context,
        )

    process = context.processes[0]
    assert process.terminated is True
    assert len(process.join_timeouts) == 2
    assert process.join_timeouts[1] <= 0.25
    assert process.closed is True
    assert context.queues[0].closed is True
    assert context.queues[0].joined is True


def test_catalog_deadline_worker_failure_still_closes_process_and_queue() -> None:
    from specify_cli.extensions.catalogs import CatalogSourceError, SourceDeadline, run_spawned

    def fail() -> bytes:
        raise RuntimeError("synthetic failure")

    context = CASES.FakeSpawnContext(run_target=True)
    with pytest.raises(CatalogSourceError, match="synthetic failure"):
        run_spawned(
            fail,
            (),
            deadline=SourceDeadline(clock=CASES.FakeClock()),
            context_factory=lambda _: context,
        )

    assert context.processes[0].closed is True
    assert context.queues[0].closed is True
    assert context.queues[0].joined is True
