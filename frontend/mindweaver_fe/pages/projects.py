import reflex as rx
from ..states.project_state import ProjectState
from ..components.layout import base_layout
from ..components.reusables import card, base_button


def create_project_modal() -> rx.Component:
    return rx.radix.primitives.dialog.root(
        rx.radix.primitives.dialog.portal(
            rx.radix.primitives.dialog.overlay(
                class_name="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
            ),
            rx.radix.primitives.dialog.content(
                rx.radix.primitives.dialog.title(
                    "Create New Project",
                    class_name="text-xl font-semibold text-gray-800 mb-4",
                ),
                rx.radix.primitives.dialog.description(
                    "Enter details for the new project.",
                    class_name="text-sm text-gray-600 mb-4",
                ),
                rx.el.div(
                    rx.el.label(
                        "Project Name",
                        class_name="text-sm font-medium text-gray-700 mb-1 block",
                    ),
                    rx.input(
                        placeholder="My Project",
                        value=ProjectState.new_project_name,
                        on_change=ProjectState.set_new_project_name,
                        class_name="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
                    ),
                    class_name="mb-4",
                ),
                rx.el.div(
                    rx.el.label(
                        "Description",
                        class_name="text-sm font-medium text-gray-700 mb-1 block",
                    ),
                    rx.text_area(
                        placeholder="Project description...",
                        value=ProjectState.new_project_description,
                        on_change=ProjectState.set_new_project_description,
                        class_name="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
                        rows="4",
                    ),
                    class_name="mb-6",
                ),
                rx.el.div(
                    rx.radix.primitives.dialog.close(
                        base_button(
                            "Cancel",
                            variant="soft",
                            color_scheme="gray",
                            on_click=ProjectState.close_create_modal,
                            class_name="bg-gray-200 text-gray-800 hover:bg-gray-300 focus:ring-gray-300",
                        ),
                        as_child=True,
                    ),
                    base_button(
                        "Create Project",
                        class_name="bg-blue-600 hover:bg-blue-700 text-white",
                        on_click=ProjectState.create_project,
                    ),
                    class_name="flex justify-end gap-3 pt-4 border-t border-gray-200",
                ),
                class_name="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-xl shadow-2xl p-6 w-full max-w-md z-50",
            ),
        ),
        open=ProjectState.is_create_modal_open,
        on_open_change=ProjectState.set_is_create_modal_open,
    )


def project_card(project: dict) -> rx.Component:
    return card(
        rx.el.div(
            rx.el.div(
                rx.el.h3(
                    project["title"],
                    class_name="text-lg font-bold text-gray-900",
                ),
                rx.el.p(
                    project["description"],
                    class_name="mt-1 text-sm text-gray-600 h-10 overflow-hidden line-clamp-2",
                ),
                class_name="flex-1 mb-4",
            ),
            rx.el.div(
                base_button(
                    "Select",
                    variant="outline",
                    on_click=lambda: ProjectState.select_project(project),
                    class_name="w-full justify-center",
                ),
                class_name="mt-auto",
            ),
            class_name="flex flex-col h-full",
        ),
        class_name="h-full flex flex-col",
    )


def projects_page() -> rx.Component:
    return base_layout(
        rx.el.div(
            rx.el.div(
                rx.el.h1(
                    "Projects",
                    class_name="text-2xl font-bold text-gray-900",
                ),
                base_button(
                    "New Project",
                    icon="plus",
                    class_name="bg-blue-600 hover:bg-blue-700 text-white",
                    on_click=ProjectState.open_create_modal,
                ),
                create_project_modal(),
                class_name="flex items-center justify-between mb-6",
            ),
            rx.cond(
                ProjectState.projects,
                rx.el.div(
                    rx.foreach(
                        ProjectState.projects,
                        project_card,
                    ),
                    class_name="grid gap-6 md:grid-cols-2 lg:grid-cols-3",
                ),
                rx.el.div(
                    rx.text(
                        "No projects found. Create one to get started.",
                        class_name="text-gray-500",
                    ),
                    class_name="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-200",
                ),
            ),
            class_name="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8",
        ),
        on_mount=ProjectState.load_projects,
    )
