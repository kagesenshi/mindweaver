import reflex as rx
from mindweaver_fe.components.layout import base_layout
from mindweaver_fe.components.reusables import card, base_button
from mindweaver_fe.states.knowledge_db_state import KnowledgeDBState, KnowledgeDB


def type_badge(db_type: rx.Var[str]) -> rx.Component:
    """A badge component to display the database type."""
    base_class = " text-xs font-medium px-2.5 py-1 rounded-full w-fit"
    return rx.el.span(
        db_type,
        class_name=rx.match(
            db_type,
            ("Vector", "bg-blue-100 text-blue-800" + base_class),
            ("Graph", "bg-purple-100 text-purple-800" + base_class),
            ("Hybrid", "bg-green-100 text-green-800" + base_class),
            "bg-gray-100 text-gray-800" + base_class,
        ),
    )


def db_card(db: KnowledgeDB) -> rx.Component:
    """A card component for a single knowledge database."""
    return card(
        rx.el.div(
            rx.el.div(
                rx.el.h3(db["name"], class_name="text-lg font-bold text-gray-900"),
                type_badge(db["type"]),
                class_name="flex justify-between items-start mb-2",
            ),
            rx.el.p(
                db["description"],
                class_name="text-sm text-gray-600 mb-4 h-10 overflow-hidden",
            ),
            rx.el.div(
                rx.el.div(
                    rx.icon("database", class_name="h-4 w-4 text-gray-400"),
                    rx.el.span(
                        f"{db['entry_count']} entries",
                        class_name="text-sm text-gray-500 ml-2",
                    ),
                    class_name="flex items-center",
                ),
                rx.el.div(
                    rx.icon("calendar", class_name="h-4 w-4 text-gray-400"),
                    rx.el.span(
                        f"Created: {db['created']}",
                        class_name="text-sm text-gray-500 ml-2",
                    ),
                    class_name="flex items-center",
                ),
                class_name="flex justify-between items-center text-sm text-gray-500 border-t border-gray-100 pt-4 mt-4",
            ),
        ),
        rx.el.div(
            base_button(
                "Edit",
                on_click=lambda: KnowledgeDBState.open_edit_modal(db),
                icon="pencil",
                class_name="bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 shadow-sm focus:ring-gray-300",
            ),
            base_button(
                "Delete",
                on_click=lambda: KnowledgeDBState.open_delete_dialog(db),
                icon="trash-2",
                class_name="bg-red-500 text-white hover:bg-red-600 shadow-sm focus:ring-red-500",
            ),
            class_name="flex gap-2 mt-4",
        ),
    )


def db_modal() -> rx.Component:
    """Modal for creating and editing databases."""
    return rx.radix.primitives.dialog.root(
        rx.radix.primitives.dialog.portal(
            rx.radix.primitives.dialog.overlay(
                class_name="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
            ),
            rx.radix.primitives.dialog.content(
                rx.radix.primitives.dialog.title(
                    rx.cond(
                        KnowledgeDBState.is_editing,
                        "Edit Knowledge Database",
                        "Create New Knowledge Database",
                    ),
                    class_name="text-xl font-semibold text-gray-800 mb-4",
                ),
                rx.el.form(
                    rx.el.div(
                        rx.el.label(
                            "Name",
                            class_name="text-sm font-medium text-gray-700 mb-1 block",
                        ),
                        rx.el.input(
                            placeholder="e.g., Project Documentation",
                            name="name",
                            default_value=KnowledgeDBState.form_data["name"],
                            class_name="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
                        ),
                        rx.cond(
                            KnowledgeDBState.form_errors.contains("name"),
                            rx.el.p(
                                KnowledgeDBState.form_errors["name"],
                                class_name="text-red-500 text-xs mt-1",
                            ),
                            None,
                        ),
                        class_name="mb-4",
                    ),
                    rx.el.div(
                        rx.el.label(
                            "Description",
                            class_name="text-sm font-medium text-gray-700 mb-1 block",
                        ),
                        rx.el.textarea(
                            placeholder="A brief description of the database.",
                            name="description",
                            default_value=KnowledgeDBState.form_data["description"],
                            class_name="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
                            rows=3,
                        ),
                        class_name="mb-4",
                    ),
                    rx.el.div(
                        rx.el.label(
                            "Database Type",
                            class_name="text-sm font-medium text-gray-700 mb-1 block",
                        ),
                        rx.el.select(
                            rx.foreach(
                                KnowledgeDBState.modal_db_types,
                                lambda type: rx.el.option(type, value=type),
                            ),
                            name="db_type",
                            default_value=KnowledgeDBState.form_data["db_type"],
                            on_change=lambda value: KnowledgeDBState.set_form_data_field(
                                "db_type", value
                            ),
                            class_name="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
                        ),
                        class_name="mb-6",
                    ),
                    on_submit=KnowledgeDBState.handle_submit,
                    id="db-form",
                ),
                rx.el.div(
                    rx.radix.primitives.dialog.close(
                        base_button(
                            "Cancel",
                            on_click=KnowledgeDBState.close_db_modal,
                            class_name="bg-gray-200 text-gray-800 hover:bg-gray-300 focus:ring-gray-300",
                        )
                    ),
                    base_button(
                        "Save Database", type="submit", form="db-form", icon="save"
                    ),
                    class_name="flex justify-end gap-3 pt-4 border-t border-gray-200",
                ),
                class_name="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-xl shadow-2xl p-6 w-full max-w-lg z-50",
            ),
        ),
        open=KnowledgeDBState.show_db_modal,
        on_open_change=KnowledgeDBState.close_db_modal,
    )


def delete_dialog() -> rx.Component:
    """Confirmation dialog for deleting a database."""
    return rx.radix.primitives.dialog.root(
        rx.radix.primitives.dialog.portal(
            rx.radix.primitives.dialog.overlay(
                class_name="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
            ),
            rx.radix.primitives.dialog.content(
                rx.radix.primitives.dialog.title(
                    "Confirm Deletion", class_name="text-xl font-semibold text-gray-800"
                ),
                rx.radix.primitives.dialog.description(
                    "Are you sure you want to delete this knowledge database? This action cannot be undone.",
                    class_name="text-gray-600 my-4",
                ),
                rx.el.div(
                    rx.radix.primitives.dialog.close(
                        base_button(
                            "Cancel",
                            on_click=KnowledgeDBState.close_delete_dialog,
                            class_name="bg-gray-200 text-gray-800 hover:bg-gray-300 focus:ring-gray-300",
                        )
                    ),
                    base_button(
                        "Delete",
                        on_click=KnowledgeDBState.confirm_delete,
                        class_name="bg-red-600 text-white hover:bg-red-700 focus:ring-red-500",
                    ),
                    class_name="flex justify-end gap-3 pt-4 border-t border-gray-200",
                ),
                class_name="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-xl shadow-2xl p-6 w-full max-w-md z-50",
            ),
        ),
        open=KnowledgeDBState.show_delete_dialog,
        on_open_change=KnowledgeDBState.close_delete_dialog,
    )


def empty_state() -> rx.Component:
    """Display when no databases are found."""
    return rx.el.div(
        rx.el.div(
            rx.icon("database-zap", class_name="h-16 w-16 text-gray-400 mx-auto"),
            rx.el.h3(
                "No Knowledge Databases Found",
                class_name="mt-4 text-lg font-semibold text-gray-800",
            ),
            rx.el.p(
                "Get started by creating your first knowledge database.",
                class_name="mt-2 text-sm text-gray-500",
            ),
            base_button(
                "Create New DB",
                icon="message-circle-plus",
                on_click=KnowledgeDBState.open_create_modal,
                class_name="mt-6",
            ),
            class_name="text-center",
        ),
        class_name="flex items-center justify-center h-full bg-gray-50 rounded-lg border-2 border-dashed border-gray-200 p-12",
    )


def knowledge_db_page() -> rx.Component:
    """The Knowledge DB page content."""
    return base_layout(
        rx.el.div(
            db_modal(),
            delete_dialog(),
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        rx.icon("search", class_name="h-5 w-5 text-gray-400"),
                        class_name="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none",
                    ),
                    rx.el.input(
                        placeholder="Search databases...",
                        on_change=KnowledgeDBState.set_search_query,
                        class_name="w-full max-w-xs pl-10 pr-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
                        default_value=KnowledgeDBState.search_query,
                    ),
                    class_name="relative",
                ),
                rx.el.div(
                    rx.el.select(
                        rx.foreach(
                            KnowledgeDBState.db_types,
                            lambda type: rx.el.option(type, value=type),
                        ),
                        value=KnowledgeDBState.filter_type,
                        on_change=KnowledgeDBState.set_filter_type,
                        class_name="py-2 pl-3 pr-8 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
                    ),
                    base_button(
                        "Create New DB",
                        icon="message-circle-plus",
                        on_click=KnowledgeDBState.open_create_modal,
                    ),
                    class_name="flex items-center gap-4",
                ),
                class_name="flex justify-between items-center mb-6",
            ),
            rx.cond(
                KnowledgeDBState.filtered_databases.length() > 0,
                rx.el.div(
                    rx.foreach(KnowledgeDBState.filtered_databases, db_card),
                    class_name="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6",
                ),
                empty_state(),
            ),
            class_name="h-full",
        )
    )
