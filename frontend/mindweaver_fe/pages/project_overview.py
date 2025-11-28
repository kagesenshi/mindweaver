import reflex as rx
from ..components.layout import base_layout
from ..components.reusables import card, base_button
from ..components.loading_spinner import loading_spinner
from ..states.project_overview_state import ProjectOverviewState


def stat_card(title: str, count: rx.Var[int], icon: str, route: str) -> rx.Component:
    """A card component displaying a resource statistic."""
    return card(
        rx.el.div(
            rx.el.div(
                rx.icon(icon, class_name="h-8 w-8 text-blue-600"),
                rx.el.div(
                    rx.el.h3(
                        title,
                        class_name="text-sm font-medium text-gray-600",
                    ),
                    rx.el.p(
                        count,
                        class_name="text-3xl font-bold text-gray-900 mt-1",
                    ),
                    class_name="flex-1",
                ),
                class_name="flex items-start gap-4",
            ),
            rx.el.div(
                base_button(
                    "View",
                    icon="arrow-right",
                    on_click=lambda: ProjectOverviewState.navigate_to(route),
                    class_name="w-full justify-center bg-blue-50 text-blue-700 hover:bg-blue-100 border-0",
                ),
                class_name="mt-4 pt-4 border-t border-gray-100",
            ),
            class_name="h-full flex flex-col",
        ),
        class_name="h-full hover:shadow-lg transition-shadow duration-200",
    )


def project_header() -> rx.Component:
    """Header section displaying project details."""
    return rx.el.div(
        rx.el.div(
            rx.icon("folder", class_name="h-12 w-12 text-blue-600"),
            rx.el.div(
                rx.el.h1(
                    ProjectOverviewState.current_project["title"],
                    class_name="text-3xl font-bold text-gray-900",
                ),
                rx.el.p(
                    ProjectOverviewState.current_project["description"],
                    class_name="text-gray-600 mt-2",
                ),
                class_name="flex-1",
            ),
            class_name="flex items-start gap-4",
        ),
        rx.el.div(
            rx.el.div(
                rx.icon("hash", class_name="h-4 w-4 text-gray-400"),
                rx.el.span(
                    f"ID: {ProjectOverviewState.current_project['id']}",
                    class_name="text-sm text-gray-500 ml-2",
                ),
                class_name="flex items-center",
            ),
            rx.el.div(
                rx.icon("calendar", class_name="h-4 w-4 text-gray-400"),
                rx.el.span(
                    f"Created: {ProjectOverviewState.current_project.get('created', 'N/A')}",
                    class_name="text-sm text-gray-500 ml-2",
                ),
                class_name="flex items-center",
            ),
            class_name="flex gap-6 mt-4",
        ),
        class_name="bg-white rounded-lg shadow-sm p-6 mb-6",
    )


def stats_grid() -> rx.Component:
    """Grid of statistics cards."""
    return rx.el.div(
        rx.el.h2(
            "Resources",
            class_name="text-xl font-semibold text-gray-900 mb-4",
        ),
        rx.el.div(
            stat_card(
                "Data Sources",
                ProjectOverviewState.project_stats["data_sources"],
                "cloud-download",
                "/sources",
            ),
            stat_card(
                "Lakehouse Storages",
                ProjectOverviewState.project_stats["lakehouse_storages"],
                "warehouse",
                "/lakehouse",
            ),
            stat_card(
                "Ingestions",
                ProjectOverviewState.project_stats["ingestions"],
                "database-zap",
                "/ingestion",
            ),
            stat_card(
                "Knowledge DBs",
                ProjectOverviewState.project_stats["knowledge_dbs"],
                "database",
                "/",
            ),
            stat_card(
                "AI Agents",
                ProjectOverviewState.project_stats["ai_agents"],
                "cpu",
                "/agents",
            ),
            stat_card(
                "Chats",
                ProjectOverviewState.project_stats["chats"],
                "messages-square",
                "/chat",
            ),
            class_name="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6",
        ),
    )


def project_overview_page() -> rx.Component:
    """The project overview page content."""
    return base_layout(
        rx.el.div(
            rx.cond(
                ProjectOverviewState.is_loading,
                loading_spinner(),
                rx.el.div(
                    rx.cond(
                        ProjectOverviewState.current_project,
                        rx.el.div(
                            project_header(),
                            stats_grid(),
                        ),
                        rx.el.div(
                            rx.el.p(
                                "No project selected. Redirecting...",
                                class_name="text-gray-500 text-center",
                            ),
                            class_name="flex items-center justify-center h-64",
                        ),
                    ),
                ),
            ),
        ),
        on_mount=ProjectOverviewState.load_overview,
    )
