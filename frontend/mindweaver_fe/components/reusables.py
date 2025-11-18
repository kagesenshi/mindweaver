import reflex as rx


def base_button(
    text: str,
    on_click: rx.event.EventType | None = None,
    icon: str | None = None,
    **props,
) -> rx.Component:
    """A reusable base button component with modern styling."""
    children = []
    if icon:
        children.append(rx.icon(icon, class_name="mr-2 h-4 w-4"))
    children.append(text)
    custom_class = props.pop("class_name", "")
    base_class = "flex items-center justify-center px-4 py-2 font-semibold rounded-lg shadow-md focus:outline-none focus:ring-2 focus:ring-opacity-75 transition-all duration-300"
    if not custom_class:
        custom_class = (
            "bg-orange-500 text-white hover:bg-orange-600 focus:ring-orange-500"
        )
    return rx.el.button(
        *children, on_click=on_click, class_name=f"{base_class} {custom_class}", **props
    )


def card(*children, **props) -> rx.Component:
    """A reusable card component with modern styling."""
    return rx.el.div(
        *children,
        class_name="bg-white rounded-xl border border-gray-200 shadow-sm p-6 transition-all duration-300 hover:shadow-lg",
        **props,
    )