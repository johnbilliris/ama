"""Real sub-agent adapters (spec-036 / FR-001).

Each module under this package exports a single async ``invoke`` function that
the ``production_invoker`` factory in :mod:`apps.api.app.services.simulation.sub_agent_invoker`
binds against an :class:`httpx.AsyncClient`.

The adapters replace the stub trip-wire registered by ``default_invoker``:
they make real HTTP calls to the agent Container Apps and capture the
``prompt_hash`` (FR-060), ``model_deployment``, and ``sub_agent_invocation_id``
fields on :class:`SubAgentReply`.
"""
