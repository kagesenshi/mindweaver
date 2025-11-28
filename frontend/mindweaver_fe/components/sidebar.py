import reflex as rx
from mindweaver_fe.states.base_state import BaseState


def nav_item(item: dict, current_path: str) -> rx.Component:
    """A single navigation item for the sidebar."""
    is_active = item["path"] == current_path
    return rx.el.a(
        rx.icon(
            item["icon"],
            class_name=rx.cond(
                is_active,
                "h-5 w-5 text-orange-500",
                "h-5 w-5 text-gray-500 group-hover:text-orange-500",
            ),
        ),
        rx.cond(
            BaseState.sidebar_collapsed,
            None,
            rx.el.span(
                item["name"],
                class_name="ml-3 font-medium transition-opacity duration-300",
            ),
        ),
        href=item["path"],
        class_name=rx.cond(
            is_active,
            "group flex items-center px-3 py-2.5 rounded-lg bg-orange-50 text-orange-600 transition-colors duration-200",
            "group flex items-center px-3 py-2.5 rounded-lg hover:bg-gray-100 text-gray-700 hover:text-gray-900 transition-colors duration-200",
        ),
    )


def sidebar() -> rx.Component:
    """The main sidebar component for navigation."""
    return rx.el.aside(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("brain-circuit", class_name="h-8 w-8 text-orange-500"),
                    rx.cond(
                        BaseState.sidebar_collapsed,
                        None,
                        rx.el.h1(
                            "AI Platform",
                            class_name="text-xl font-bold text-gray-800 ml-2 transition-opacity duration-300",
                        ),
                    ),
                    class_name="flex items-center",
                ),
                class_name="flex items-center justify-between h-16 px-4 border-b border-gray-200",
            ),
            rx.el.nav(
                rx.foreach(
                    BaseState.nav_items,
                    lambda item: nav_item(item, BaseState.router.page.path),
                ),
                class_name="flex-1 flex flex-col gap-1 p-4",
            ),
            rx.el.nav(
                nav_item(
                    {
                        "path": "/",
                        "name": "Projects",
                        "icon": "brain-circuit",
                    },
                    BaseState.router.page.path,
                ),
                class_name="flex flex-col gap-1 p-4",
            ),
            rx.el.div(
                rx.el.button(
                    rx.icon(
                        rx.cond(
                            BaseState.sidebar_collapsed,
                            "chevrons-right",
                            "chevrons-left",
                        ),
                        class_name="h-5 w-5 text-gray-600",
                    ),
                    on_click=BaseState.toggle_sidebar,
                    class_name="p-2 rounded-lg hover:bg-gray-100 transition-colors duration-200",
                ),
                class_name="flex items-center justify-center p-4 border-t border-gray-200",
            ),
            class_name="flex flex-col h-full",
        ),
        class_name=rx.cond(
            BaseState.sidebar_collapsed,
            "hidden md:flex flex-col bg-white border-r border-gray-200 transition-all duration-300 w-20",
            "hidden md:flex flex-col bg-white border-r border-gray-200 transition-all duration-300 w-64",
        ),
    )
