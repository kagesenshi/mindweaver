import reflex as rx


def loading_spinner() -> rx.Component:
    """A centered loading spinner with animated icon and text."""
    return rx.el.div(
        rx.el.div(
            rx.icon(
                "loader-circle",
                class_name="h-12 w-12 text-orange-500 animate-spin",
            ),
            rx.el.p(
                "Loading...",
                class_name="mt-4 text-lg font-medium text-gray-600",
            ),
            class_name="flex flex-col items-center justify-center",
        ),
        class_name="flex items-center justify-center h-full min-h-[400px] bg-gray-50 rounded-lg",
    )
