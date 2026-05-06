from app.repositories.coordination_tasks_repository import (
    get_coordination_tasks_repository,
)
from app.repositories.persona_registry_repository import (
    Persona as RegistryPersona,
)
from app.repositories.persona_registry_repository import (
    get_persona_registry_repository,
)
from app.services.state_store import PERSONAS
from fastapi import HTTPException


def _persona_view(persona_id: str, display_name: str, organisation_id: str, jurisdiction_id: str) -> dict[str, str]:
    # role is set to persona_id (kebab-case) so the frontend's panel-routing
    # checks (e.g. role === "incident-commander") match consistently across
    # the in-memory and seed-backed lookup paths.
    return {
        "persona_id": persona_id,
        "display_name": display_name,
        "organisation_id": organisation_id,
        "jurisdiction_id": jurisdiction_id,
        "role": persona_id,
    }


class PersonaWorkspaceService:
    def get_workspace(self, persona_id: str) -> dict[str, object]:
        persona = PERSONAS.get(persona_id)
        if persona is not None:
            organisation_id = persona.organisation_id
            persona_view = _persona_view(
                persona_id=persona.persona_id,
                display_name=persona.display_name,
                organisation_id=persona.organisation_id,
                jurisdiction_id=persona.jurisdiction_id,
            )
        else:
            registry_persona = self._resolve_from_registry(persona_id)
            organisation_id = registry_persona.organisation_id or ""
            persona_view = _persona_view(
                persona_id=registry_persona.persona_id,
                display_name=registry_persona.display_name or registry_persona.persona_id,
                organisation_id=organisation_id,
                jurisdiction_id=registry_persona.jurisdiction_id or "",
            )

        repo = get_coordination_tasks_repository()
        visible = repo.list_for_persona_or_org(persona_id, organisation_id)
        visible_tasks = [task.model_dump(mode="json") for task in visible]

        dependency_ids = [dep_id for task in visible_tasks for dep_id in task.get("dependency_task_ids", [])]
        dependency_chain = [
            task.model_dump(mode="json") for task in repo.list_dependencies(organisation_id, dependency_ids)
        ]

        return {
            "persona": persona_view,
            "tasks": visible_tasks,
            "dependencies": dependency_chain,
        }

    @staticmethod
    def _resolve_from_registry(persona_id: str) -> RegistryPersona:
        registry_persona = get_persona_registry_repository().find_by_id(persona_id)
        if registry_persona is None:
            raise HTTPException(status_code=404, detail="Persona not found")
        return registry_persona
