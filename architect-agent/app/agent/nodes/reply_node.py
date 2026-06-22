import uuid
from app.agent.contracts.agent_interface import ArchitectState


class ReplyNode:
    async def __call__(self, state: ArchitectState) -> dict:
        solution = state.get("solution", {})
        tickets = state.get("tickets", [])
        requirement = state.get("requirement", "")
        prior_solution = state.get("prior_solution")

        epic_name = requirement
        epic_requirements = [{"requirement": requirement}]
        if prior_solution:
            epic_name, epic_requirements = self._resolve_epic_meta(state, epic_name, epic_requirements)

        epic_id = tickets[0]["epicId"] if tickets else str(uuid.uuid4())
        epic = self._build_epic(epic_id, epic_name, epic_requirements, solution)

        return {"final_reply": {"epic": epic, "tickets": tickets}}

    def _build_epic(self, epic_id: str, name: str, requirements: list, solution: dict) -> dict:
        return {
            "id": epic_id,
            "name": name[:200] if name else "Software Solution",
            "requirements": requirements,
            "solution": solution,
        }

    def _resolve_epic_meta(self, state: ArchitectState, default_name: str, default_requirements: list) -> tuple:
        for msg in reversed(state.get("raw_history", [])):
            content = msg.get("content", {})
            if isinstance(content, dict) and "epic" in content:
                prior_epic = content.get("epic", {})
                return prior_epic.get("name", default_name), prior_epic.get("requirements", default_requirements)
        return default_name, default_requirements
