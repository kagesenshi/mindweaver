import reflex as rx
from typing import TypedDict


class NavItem(TypedDict):
    name: str
    path: str
    icon: str


class BaseState(rx.State):
    """Manages the base state of the application, including navigation."""

    nav_items: list[NavItem] = [
        {"name": "Data Sources", "path": "/sources", "icon": "cloud-download"},
        {"name": "Lakehouse Storage", "path": "/lakehouse", "icon": "warehouse"},
        {"name": "Ingestion", "path": "/ingestion", "icon": "database-zap"},
        {"name": "Knowledge DB", "path": "/", "icon": "database"},
        {"name": "AI Agents", "path": "/agents", "icon": "cpu"},
        {"name": "Chat", "path": "/chat", "icon": "messages-square"},
        #    {"name": "Graph Explorer", "path": "/graph", "icon": "git-fork"},
    ]
    sidebar_collapsed: bool = False

    @rx.var
    def current_page_name(self) -> str:
        """Returns the name of the current page based on the route."""
        path = self.router.url.path
        for item in self.nav_items:
            if item["path"] == path:
                return item["name"]
        if path == "/":
            return "Knowledge DB"
        return path.strip("/").replace("_", " ").title()

    @rx.event
    def toggle_sidebar(self):
        """Toggles the collapsed state of the sidebar."""
        self.sidebar_collapsed = not self.sidebar_collapsed
