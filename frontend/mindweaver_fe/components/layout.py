import reflex as rx
from mindweaver_fe.components.sidebar import sidebar
from mindweaver_fe.components.header import header_component

# Add ProjectState.check_access and BaseState.on_load to the beginning of on_mount list
from ..states.project_state import ProjectState
from ..states.base_state import BaseState
from pprint import pprint


def base_layout(child: rx.Component, **props) -> rx.Component:
    """The base layout for all pages, including sidebar and header."""

    # Extract on_mount from props if it exists
    on_mount = props.pop("on_mount", [])
    if not isinstance(on_mount, list):
        on_mount = [on_mount]

    on_mount.insert(0, BaseState.on_load)
    on_mount.insert(0, ProjectState.check_access)

    return rx.el.div(
        rx.cond(
            BaseState.router.page.path != "/index",
            sidebar(),
        ),
        rx.el.div(
            header_component(),
            rx.el.main(child, class_name="flex-1 p-6 bg-gray-50"),
            class_name="flex flex-col flex-1",
        ),
        class_name="flex min-h-screen w-full font-['Raleway'] bg-gray-50",
        on_mount=on_mount,
        **props,
    )
