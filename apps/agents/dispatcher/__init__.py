"""Sub-agent dispatcher — exposes ``POST /{role}/invoke`` for the simulation Controller.

Spec-036 / sub-agent-adapter contract: the Simulation Controller's
``query_sub_agent`` tool delegates to one of six operational sub-agents
(monitoring, planning, risk-assessment, communication, evacuation,
resource-allocation). Each adapter under
``apps/api/app/services/simulation/sub_agents/`` issues
``POST {AGENTS_BASE_URL}/{role}/invoke`` with ``{tenant_id, question}``
and expects ``{summary, citations, prompt_hash, model_deployment,
invocation_id}``.

This package implements a single FastAPI multiplex that fulfils that
contract for all six roles. It is the entrypoint of the ``ca-agents-*``
Container App.
"""
