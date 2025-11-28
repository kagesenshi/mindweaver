import reflex as rx
from typing import List, Dict, Any, Optional
from ..api_client import project_client
from .base_state import BaseState


class ProjectState(BaseState):
    """State for managing projects."""

    projects: List[Dict[str, Any]] = []
    current_project: Optional[Dict[str, Any]] = None
    is_create_modal_open: bool = False
    new_project_name: str = ""
    new_project_description: str = ""

    async def load_projects(self):
        """Load all projects."""
        self.projects = await project_client.list_all()

    @rx.event
    async def select_project(self, project: Dict[str, Any]):
        """Select a project."""
        self.current_project = project
        # force page reload
        yield rx.redirect(f"/overview")

    def open_create_modal(self):
        self.is_create_modal_open = True
        self.new_project_name = ""
        self.new_project_description = ""

    def close_create_modal(self):
        self.is_create_modal_open = False

    def set_is_create_modal_open(self, value: bool):
        self.is_create_modal_open = value

    async def create_project(self):
        """Create a new project."""
        if not self.new_project_name:
            return

        data = {
            "name": self.new_project_name,
            "title": self.new_project_name,  # Use name as title for now
            "description": self.new_project_description,
        }

        try:
            new_project = await project_client.create(data)
            self.projects.append(new_project)
            await self.select_project(new_project)
            self.close_create_modal()
            return rx.window_alert("Project created successfully!")
        except Exception as e:
            return rx.window_alert(f"Failed to create project: {str(e)}")

    def set_new_project_name(self, value: str):
        self.new_project_name = value

    def set_new_project_description(self, value: str):
        self.new_project_description = value

    async def check_access(self):
        """Check if a project is selected, otherwise redirect to projects page."""
        # Allow access to the projects page itself to avoid infinite redirect loop
        # Note: router.url.path causes a VarAttributeError in Reflex 0.6.x/0.8.x, so we use router.page.path
        # despite the deprecation warning until a proper fix is found.
        if self.router.url.path == "/projects":
            return

        # If no project is selected, redirect to projects page
        if not self.current_project:
            return rx.redirect("/projects")
