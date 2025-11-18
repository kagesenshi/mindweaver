import reflex as rx
from mindweaver_fe.components.sidebar import sidebar
from mindweaver_fe.components.header import header_component


def base_layout(child: rx.Component, **props) -> rx.Component:
    """The base layout for all pages, including sidebar and header."""
    return rx.el.div(
        sidebar(),
        rx.el.div(
            header_component(),
            rx.el.main(child, class_name="flex-1 p-6 bg-gray-50"),
            class_name="flex flex-col flex-1",
        ),
        class_name="flex min-h-screen w-full font-['Raleway'] bg-gray-50",
        **props,
    )