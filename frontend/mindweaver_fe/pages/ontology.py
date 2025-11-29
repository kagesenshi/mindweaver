import reflex as rx
from mindweaver_fe.components.layout import base_layout
from mindweaver_fe.components.reusables import card, base_button
from mindweaver_fe.components.loading_spinner import loading_spinner
from mindweaver_fe.states.ontology_state import OntologyState, Ontology


def ontology_card(ontology: Ontology) -> rx.Component:
    return card(
        rx.el.div(
            rx.el.div(
                rx.el.h3(
                    ontology["title"], class_name="text-lg font-bold text-gray-900"
                ),
                rx.el.p(
                    f"Name: {ontology['name']}",
                    class_name="text-xs text-gray-500 mt-1",
                ),
                class_name="flex justify-between items-start mb-2",
            ),
            rx.el.p(
                ontology["description"],
                class_name="text-sm text-gray-600 mb-4 h-10 overflow-hidden",
            ),
            rx.el.div(
                rx.el.div(
                    rx.icon("calendar", class_name="h-4 w-4 text-gray-400"),
                    rx.el.span(
                        f"Created: {ontology['created']}",
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
                on_click=lambda: OntologyState.open_edit_modal(ontology),
                icon="pencil",
                class_name="bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 shadow-sm focus:ring-gray-300",
            ),
            class_name="flex gap-2 mt-4",
        ),
    )


def ontology_modal() -> rx.Component:
    return rx.radix.primitives.dialog.root(
        rx.radix.primitives.dialog.portal(
            rx.radix.primitives.dialog.overlay(
                class_name="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
            ),
            rx.radix.primitives.dialog.content(
                rx.radix.primitives.dialog.title(
                    rx.cond(
                        OntologyState.is_editing,
                        "Edit Ontology",
                        "Create New Ontology",
                    ),
                    class_name="text-xl font-semibold text-gray-800 mb-4",
                ),
                rx.el.div(
                    # General error message
                    rx.cond(
                        OntologyState.error_message != "",
                        rx.el.div(
                            OntologyState.error_message,
                            class_name="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4",
                        ),
                    ),
                    rx.el.label(
                        "Name",
                        class_name="text-sm font-medium text-gray-700 mb-1 block",
                    ),
                    rx.el.input(
                        placeholder="e.g., domain-ontology",
                        value=OntologyState.form_data["name"],
                        on_change=lambda v: OntologyState.set_form_data("name", v),
                        class_name="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500 mb-1",
                    ),
                    # Name error message
                    rx.cond(
                        OntologyState.form_errors.get("name", "") != "",
                        rx.el.p(
                            OntologyState.form_errors.get("name", ""),
                            class_name="text-sm text-red-600 mb-3",
                        ),
                        rx.el.div(class_name="mb-3"),
                    ),
                    rx.el.label(
                        "Title",
                        class_name="text-sm font-medium text-gray-700 mb-1 block",
                    ),
                    rx.el.input(
                        placeholder="e.g., Domain Ontology",
                        value=OntologyState.form_data["title"],
                        on_change=lambda v: OntologyState.set_form_data("title", v),
                        class_name="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500 mb-1",
                    ),
                    # Title error message
                    rx.cond(
                        OntologyState.form_errors.get("title", "") != "",
                        rx.el.p(
                            OntologyState.form_errors.get("title", ""),
                            class_name="text-sm text-red-600 mb-3",
                        ),
                        rx.el.div(class_name="mb-3"),
                    ),
                    rx.el.label(
                        "Description",
                        class_name="text-sm font-medium text-gray-700 mb-1 block",
                    ),
                    rx.el.textarea(
                        placeholder="Description of the ontology",
                        value=OntologyState.form_data["description"],
                        on_change=lambda v: OntologyState.set_form_data(
                            "description", v
                        ),
                        class_name="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500 mb-1",
                    ),
                    # Description error message
                    rx.cond(
                        OntologyState.form_errors.get("description", "") != "",
                        rx.el.p(
                            OntologyState.form_errors.get("description", ""),
                            class_name="text-sm text-red-600 mb-6",
                        ),
                        rx.el.div(class_name="mb-6"),
                    ),
                    rx.el.div(
                        rx.radix.primitives.dialog.close(
                            base_button(
                                "Cancel",
                                on_click=OntologyState.close_modal,
                                class_name="bg-gray-200 text-gray-800",
                            ),
                            as_child=True,
                        ),
                        base_button(
                            "Save", on_click=OntologyState.handle_submit, icon="save"
                        ),
                        class_name="flex justify-end gap-3",
                    ),
                ),
                class_name="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-xl shadow-2xl p-6 w-full max-w-lg z-50",
            ),
        ),
        open=OntologyState.show_modal,
        on_open_change=OntologyState.close_modal,
    )


def ontology_page() -> rx.Component:
    return base_layout(
        rx.el.div(
            ontology_modal(),
            rx.cond(
                OntologyState.is_loading,
                loading_spinner(),
                rx.el.div(
                    rx.el.div(
                        rx.el.h1(
                            "Ontologies", class_name="text-2xl font-bold text-gray-900"
                        ),
                        base_button(
                            "Create Ontology",
                            icon="plus",
                            on_click=OntologyState.open_create_modal,
                        ),
                        class_name="flex justify-between items-center mb-6",
                    ),
                    rx.el.div(
                        rx.foreach(OntologyState.ontologies, ontology_card),
                        class_name="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6",
                    ),
                ),
            ),
        ),
        on_mount=OntologyState.load_ontologies,
    )
