import reflex as rx
from typing import TypedDict
import httpx
from ..config import settings


class NavItem(TypedDict):
    name: str
    path: str
    icon: str


class BaseState(rx.State):
    """Manages the base state of the application, including navigation."""

    # All possible navigation items
    _all_nav_items: list[NavItem] = [
        {"name": "Overview", "path": "/overview", "icon": "layout-dashboard"},
        {"name": "Data Sources", "path": "/sources", "icon": "cloud-download"},
        {"name": "Lakehouse Storage", "path": "/lakehouse", "icon": "warehouse"},
        {"name": "Ingestion", "path": "/ingestion", "icon": "database-zap"},
        {"name": "Knowledge DB", "path": "/", "icon": "database"},
        {"name": "AI Agents", "path": "/agents", "icon": "cpu"},
        {"name": "Chat", "path": "/chat", "icon": "messages-square"},
        #    {"name": "Graph Explorer", "path": "/graph", "icon": "git-fork"},
    ]

    # Feature flags from backend
    feature_flags: dict[str, bool] = {}

    # Dynamically filtered nav items based on feature flags
    nav_items: list[NavItem] = []

    sidebar_collapsed: bool = False

    async def on_load(self):
        """Load feature flags when the state is initialized."""
        async for i in self.load_feature_flags():
            yield i

    @rx.event
    async def load_feature_flags(self):
        """Fetch feature flags from backend and update nav_items."""

        # All possible navigation items
        _all_nav_items: list[NavItem] = [
            {"name": "Overview", "path": "/overview", "icon": "layout-dashboard"},
            {"name": "Data Sources", "path": "/sources", "icon": "cloud-download"},
            {"name": "Lakehouse Storage", "path": "/lakehouse", "icon": "warehouse"},
            {"name": "Ingestion", "path": "/ingestion", "icon": "database-zap"},
            {"name": "Knowledge DB", "path": "/knowledge_db", "icon": "database"},
            {"name": "Ontology", "path": "/ontology", "icon": "workflow"},
            {"name": "AI Agents", "path": "/agents", "icon": "cpu"},
            {"name": "Chat", "path": "/chat", "icon": "messages-square"},
            #    {"name": "Graph Explorer", "path": "/graph", "icon": "git-fork"},
        ]

        if self.nav_items:
            return

        print("loading feature flags")

        try:
            async with httpx.AsyncClient(
                base_url=settings.api_base_url, timeout=settings.api_timeout
            ) as client:
                response = await client.get("/feature-flags")
                response.raise_for_status()
                self.feature_flags = response.json()

                # Map nav items to feature flags
                nav_to_feature = {
                    "Data Sources": "experimental_data_source",
                    "Lakehouse Storage": "experimental_lakehouse_storage",
                    "Ingestion": "experimental_ingestion",
                    "Knowledge DB": "experimental_knowledge_db",
                    "Ontology": "experimental_ontology",
                    "AI Agents": "experimental_ai_agent",
                    "Chat": "experimental_chat",
                }

                # Filter nav items based on enabled feature flags
                enabled_nav_items = []
                for item in _all_nav_items:
                    # Find the corresponding feature flag
                    feature_flag = nav_to_feature.get(item["name"])

                    # Include item if feature flag is enabled (or if no flag exists for it)
                    if feature_flag is None or self.feature_flags.get(
                        feature_flag, False
                    ):
                        enabled_nav_items.append(item)

                self.nav_items = enabled_nav_items
        except httpx.HTTPStatusError as e:
            yield rx.toast(f"Error fetching feature flags: {e}")
            # Fallback to all items if feature flags can't be fetched
            self.nav_items = _all_nav_items
        except Exception as e:
            yield rx.toast(f"Unexpected error fetching feature flags: {e}")
            # Fallback to all items if feature flags can't be fetched
            self.nav_items = _all_nav_items

    @rx.var
    def current_page_name(self) -> str:
        """Returns the name of the current page based on the route."""
        path = self.router.url.path
        for item in self.nav_items:
            if item["path"] == path:
                return item["name"]
        if path == "/":
            return "Overview"
        return path.strip("/").replace("_", " ").title()

    @rx.event
    def toggle_sidebar(self):
        """Toggles the collapsed state of the sidebar."""
        self.sidebar_collapsed = not self.sidebar_collapsed

    async def _get_project_params(self) -> dict[str, str]:
        """Get project_id as params dict for API calls."""
        from .project_state import ProjectState

        project_state = await self.get_state(ProjectState)
        if project_state.current_project_id:
            return {"project_id": str(project_state.current_project_id)}
        return {}
