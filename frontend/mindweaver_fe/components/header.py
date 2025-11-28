import reflex as rx
from mindweaver_fe.states.base_state import BaseState
from mindweaver_fe.states.project_state import ProjectState


def header_component() -> rx.Component:
    """The header component with breadcrumbs, title, and project switcher."""
    return rx.el.header(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("home", class_name="h-4 w-4 text-gray-500"),
                    rx.cond(
                        BaseState.router.page.path != "/index",
                        rx.el.span(
                            rx.el.span("/", class_name="mx-2 text-gray-400"),
                            rx.el.span(
                                ProjectState.current_project["name"],
                                class_name="font-medium text-gray-700",
                            ),
                            rx.el.span("/", class_name="mx-2 text-gray-400"),
                            rx.el.span(
                                BaseState.current_page_name,
                                class_name="font-medium text-gray-700",
                            ),
                        ),
                    ),
                    class_name="flex items-center text-sm",
                ),
                rx.el.h1(
                    BaseState.current_page_name,
                    class_name="text-2xl font-bold text-gray-900 mt-1",
                ),
            ),
            class_name="flex items-center justify-between",
        ),
        class_name="bg-white/80 backdrop-blur-sm sticky top-0 z-10 border-b border-gray-200 px-6 py-4",
        on_mount=ProjectState.load_projects,
    )
