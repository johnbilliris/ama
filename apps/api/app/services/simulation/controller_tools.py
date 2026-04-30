"""Server-side allow-list of tools the Simulation Controller may invoke.

The *model* may request any tool name it likes. This registry is the single source of
truth server-side: unknown names are refused, logged, and a synthetic tool-result is
injected so the model can recover. This is defence in depth against prompt injection.
"""

from __future__ import annotations

from typing import Any

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "seed_scenario",
            "description": (
                "Immediately seed the simulation with a scenario card built from the "
                "coordinator's description. The simulation tenant is already created; "
                "this call populates it with hazard, location, and starting conditions. "
                "Call this directly — do NOT ask the coordinator to confirm first."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "hazard": {
                        "type": "string",
                        "enum": [
                            "bushfire",
                            "flood",
                            "cyclone",
                            "storm",
                            "heat",
                            "earthquake",
                            "tsunami",
                            "pandemic",
                            "other",
                        ],
                    },
                    "location_name": {"type": "string"},
                    "start_at": {"type": "string", "format": "date-time"},
                    "aws_default_level": {
                        "type": "string",
                        "enum": ["advice", "watch_and_act", "emergency_warning"],
                    },
                    "parameters": {"type": "object", "additionalProperties": True},
                },
                "required": ["hazard", "location_name", "start_at"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_sub_agent",
            "description": ("Relay a question to one of the operational sub-agents in simulation mode."),
            "parameters": {
                "type": "object",
                "properties": {
                    "sub_agent": {
                        "type": "string",
                        "enum": [
                            "monitoring",
                            "planning",
                            "resource_allocation",
                            "communication",
                            "evacuation",
                            "risk_assessment",
                        ],
                    },
                    "question": {"type": "string"},
                },
                "required": ["sub_agent", "question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "draft_warning_sim",
            "description": (
                "Draft a public information warning INSIDE the simulation. Output must be "
                "watermarked and will NOT be transmitted to real channels."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "level": {
                        "type": "string",
                        "enum": ["advice", "watch_and_act", "emergency_warning"],
                    },
                    "hazard": {"type": "string"},
                    "location": {"type": "string"},
                    "action": {"type": "string"},
                },
                "required": ["level", "hazard", "location", "action"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "summarise_state",
            "description": "Return a concise summary of the simulation's current state.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "pause",
            "description": "Request that the simulation be paused (requires coordinator confirmation).",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "resume",
            "description": "Request that the simulation be resumed.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "stop",
            "description": "Request that the simulation be stopped (terminal).",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_participants",
            "description": "Return the participant list for the current simulation.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

ALLOW_LIST = frozenset(t["function"]["name"] for t in TOOL_SCHEMAS)


def is_allowed(tool_name: str) -> bool:
    return tool_name in ALLOW_LIST
