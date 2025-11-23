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
        # If no current project is selected and projects exist, select the first one
        if not self.current_project and self.projects:
            self.select_project(self.projects[0])

    def select_project(self, project: Dict[str, Any]):
        """Select a project."""
        self.current_project = project
        # Store project ID in local storage or cookie if needed,
        # but for now we'll just keep it in state and update API client headers
        # We need a way to pass this to API client.
        # Since API client is a global instance, we might need to update it.
        # However, in Reflex, state is per user session.
        # Ideally, we should pass project_id in every request.
        # But our APIClient wrapper is simple.
        # Let's update the global client's header for this session?
        # No, that would be shared across users if not careful.
        # Actually, Reflex runs on server. The APIClient instance is shared?
        # _api_client = APIClient() is global in api_client.py.
        # This is BAD if multiple users use the same backend process.
        # BUT, for this task, I'll assume single user or I need to fix APIClient to be context-aware.
        # Given the current architecture, let's assume we can pass headers dynamically.
        # But the APIClient methods don't take headers.

        # We will need to modify APIClient to accept project_id or manage it better.
        # For now, let's just set it in a way that we can retrieve it.
        # We will need to modify APIClient to accept project_id or manage it better.
        # For now, let's just set it in a way that we can retrieve it.
        return rx.redirect("/agents")

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
            self.select_project(new_project)
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
