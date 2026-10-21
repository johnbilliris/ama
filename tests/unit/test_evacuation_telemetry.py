"""Focused exporter and custom-event tests for evacuation telemetry."""

import sys
from types import SimpleNamespace

from evacuation import telemetry as tel


class _SpanCapture:
    def __init__(self):
        self.events = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        del args

    def add_event(self, name, attributes=None):
        self.events.append((name, attributes))


class _TracerCapture:
    def __init__(self):
        self.spans = []

    def start_as_current_span(self, name, attributes=None):
        span = _SpanCapture()
        self.spans.append((name, attributes, span))
        return span


def test_event_uses_recording_span_when_no_parent_is_active(monkeypatch):
    tracer = _TracerCapture()
    monkeypatch.setattr(tel, "tracer", tracer)
    monkeypatch.setattr(tel, "_current_span", lambda: None)

    tel.emit_override_applied(
        plan_id="ep-inc-1-v1",
        action="approve",
        user_id="commander-1",
        role="incident_commander",
        incident_id="inc-1",
        tenant_id="tenant-a",
    )

    assert tracer.spans[0][0] == "evacuation.event.OverrideApplied"
    assert tracer.spans[0][2].events == [
        (
            "OverrideApplied",
            {
                "plan_id": "ep-inc-1-v1",
                "action": "approve",
                "user_id": "commander-1",
                "role": "incident_commander",
                "incident_id": "inc-1",
                "tenant_id": "tenant-a",
            },
        )
    ]


def test_all_contract_events_record_without_an_active_parent(monkeypatch):
    tracer = _TracerCapture()
    monkeypatch.setattr(tel, "tracer", tracer)
    monkeypatch.setattr(tel, "_current_span", lambda: None)
    emitters = [
        lambda: tel.emit_handoff_received("handoff-1", "inc-1", "tenant-a"),
        lambda: tel.emit_plan_generated(
            "ep-inc-1-v1",
            1,
            0.8,
            2,
            "template_fallback",
        ),
        lambda: tel.emit_plan_updated(
            "ep-inc-1-v2",
            2,
            ["road_closure"],
            "Route changed",
        ),
        lambda: tel.emit_shelter_in_place_recommended(
            "inc-1",
            "1",
            100,
            "flood",
        ),
        lambda: tel.emit_shelter_to_evacuation_recovery(
            "ep-inc-1-v2",
            "1",
            "route-1",
        ),
        lambda: tel.emit_emergency_escalation("inc-1", "1", 100),
        lambda: tel.emit_override_applied(
            "ep-inc-1-v2",
            "approve",
            "commander-1",
            "incident_commander",
            "inc-1",
            "tenant-a",
        ),
        lambda: tel.emit_degradation_event("cosmos", 2),
        lambda: tel.emit_sla_breach("handoff-1", 31_000, "initial"),
        lambda: tel.emit_version_conflict("inc-1", 1),
        lambda: tel.emit_route_conflict("ep-inc-1-v2", "route-1", 85),
        lambda: tel.emit_time_deficit_detected("ep-inc-1-v2", "1", 12),
    ]

    for emit in emitters:
        emit()

    events = [span.events[0] for _, _, span in tracer.spans]
    assert [name for name, _ in events] == [
        "HandoffReceived",
        "PlanGenerated",
        "PlanUpdated",
        "ShelterInPlaceRecommended",
        "ShelterToEvacuationRecovery",
        "EmergencyEscalation",
        "OverrideApplied",
        "DegradationEvent",
        "SLABreach",
        "VersionConflict",
        "RouteConflict",
        "TimeDeficitDetected",
    ]
    identifier_values = [
        str(value) for _, attributes in events for key, value in attributes.items() if key.endswith("_id")
    ]
    assert identifier_values
    assert all(identifier_values)


def test_configure_telemetry_uses_managed_identity(monkeypatch):
    calls = []

    class Credential:
        def __init__(self, **kwargs):
            self.options = kwargs

    def configure(**kwargs):
        calls.append(kwargs)

    monkeypatch.setenv(
        "APPLICATIONINSIGHTS_CONNECTION_STRING",
        "InstrumentationKey=test;IngestionEndpoint=https://australiaeast.test/",
    )
    monkeypatch.setenv("AZURE_CLIENT_ID", "identity-client-id")
    monkeypatch.setitem(
        sys.modules,
        "azure.identity",
        SimpleNamespace(DefaultAzureCredential=Credential),
    )
    monkeypatch.setitem(
        sys.modules,
        "azure.monitor.opentelemetry",
        SimpleNamespace(configure_azure_monitor=configure),
    )
    monkeypatch.setattr(tel, "_TELEMETRY_CONFIGURED", False)

    assert tel.configure_telemetry() is True
    assert calls[0]["credential"].options == {"managed_identity_client_id": "identity-client-id"}
    assert calls[0]["resource_attributes"] == {
        "service.name": "evacuation-agent",
        "service.version": "0.1.0",
    }
