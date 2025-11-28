import reflex as rx
from typing import Dict, Any, Optional
from .base_state import BaseState
from .project_state import ProjectState
from ..api_client import (
    data_source_client,
    lakehouse_storage_client,
    ingestion_client,
    knowledge_db_client,
    ai_agent_client,
    chat_client,
)
import httpx


class ProjectOverviewState(BaseState):
    """State for managing the project overview page."""

    is_loading: bool = False
    current_project: Optional[Dict[str, Any]] = None
    project_stats: Dict[str, int] = {
        "data_sources": 0,
        "lakehouse_storages": 0,
        "ingestions": 0,
        "knowledge_dbs": 0,
        "ai_agents": 0,
        "chats": 0,
    }

    async def load_overview(self):
        """Load project overview data including resource counts."""
        self.is_loading = True
        yield

        try:
            # Get project from ProjectState
            project_state = await self.get_state(ProjectState)
            if not project_state.current_project:
                self.is_loading = False
                yield rx.redirect("/projects")
                return

            # Store current project in local state
            self.current_project = project_state.current_project
            project_id = self.current_project.get("id")
            headers = {"X-Project-Id": str(project_id)}

            # Fetch counts for each resource type
            try:
                data_sources = await data_source_client.list_all(headers=headers)
                self.project_stats["data_sources"] = len(data_sources)
            except httpx.HTTPStatusError:
                self.project_stats["data_sources"] = 0

            try:
                lakehouse_storages = await lakehouse_storage_client.list_all(
                    headers=headers
                )
                self.project_stats["lakehouse_storages"] = len(lakehouse_storages)
            except httpx.HTTPStatusError:
                self.project_stats["lakehouse_storages"] = 0

            try:
                ingestions = await ingestion_client.list_all(headers=headers)
                self.project_stats["ingestions"] = len(ingestions)
            except httpx.HTTPStatusError:
                self.project_stats["ingestions"] = 0

            try:
                knowledge_dbs = await knowledge_db_client.list_all(headers=headers)
                self.project_stats["knowledge_dbs"] = len(knowledge_dbs)
            except httpx.HTTPStatusError:
                self.project_stats["knowledge_dbs"] = 0

            try:
                ai_agents = await ai_agent_client.list_all(headers=headers)
                self.project_stats["ai_agents"] = len(ai_agents)
            except httpx.HTTPStatusError:
                self.project_stats["ai_agents"] = 0

            try:
                chats = await chat_client.list_all(headers=headers)
                self.project_stats["chats"] = len(chats)
            except httpx.HTTPStatusError:
                self.project_stats["chats"] = 0

        except Exception as e:
            yield rx.toast(f"Error loading overview: {str(e)}", variant="error")
        finally:
            self.is_loading = False
            yield

    def navigate_to(self, path: str):
        """Navigate to a specific page."""
        return rx.redirect(path)
