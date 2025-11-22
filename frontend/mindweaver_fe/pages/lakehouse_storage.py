import reflex as rx
from mindweaver_fe.components.layout import base_layout
from mindweaver_fe.components.reusables import card, base_button
from mindweaver_fe.components.loading_spinner import loading_spinner
from mindweaver_fe.states.lakehouse_storage_state import (
    LakehouseStorageState,
    LakehouseStorage,
)
import mindweaver_fe.util as util


def storage_card(storage: LakehouseStorage) -> rx.Component:
    """A card component for a single lakehouse storage."""
    return card(
        rx.el.div(
            rx.el.div(
                rx.el.h3(storage["name"], class_name="text-lg font-bold text-gray-900"),
                rx.el.span(
                    "S3 Storage",
                    class_name="text-xs font-medium px-2.5 py-1 rounded-full w-fit bg-blue-100 text-blue-800",
                ),
                class_name="flex justify-between items-start mb-2",
            ),
            rx.el.p(
                f"Bucket: {storage['parameters'].get('bucket', 'N/A')} | Region: {storage['parameters'].get('region', 'N/A')}",
                class_name="text-sm text-gray-600 mb-4 h-10 overflow-hidden",
            ),
            rx.el.div(
                rx.el.div(
                    rx.icon("database", class_name="h-4 w-4 text-gray-400"),
                    rx.el.span(
                        rx.cond(
                            storage["created"],
                            "Created: " + storage["created"][:10],
                            "Created: N/A",
                        ),
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
                on_click=lambda: LakehouseStorageState.open_edit_modal(storage),
                icon="pencil",
                class_name="bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 shadow-sm focus:ring-gray-300",
            ),
            base_button(
                "Delete",
                on_click=lambda: LakehouseStorageState.open_delete_dialog(storage),
                icon="trash-2",
                class_name="bg-red-500 text-white hover:bg-red-600 shadow-sm focus:ring-red-500",
            ),
            class_name="flex gap-2 mt-4",
        ),
    )


def s3_form_fields() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.label(
                "Bucket Name", class_name="text-sm font-medium text-gray-700 mb-1 block"
            ),
            rx.el.input(
                name="parameters.bucket",
                default_value=util.default(
                    LakehouseStorageState.form_data["parameters"]["bucket"], ""
                ),
                placeholder="my-lakehouse-bucket",
                class_name="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
            ),
            class_name="mb-4",
        ),
        rx.el.div(
            rx.el.label(
                "Region", class_name="text-sm font-medium text-gray-700 mb-1 block"
            ),
            rx.el.input(
                name="parameters.region",
                default_value=util.default(
                    LakehouseStorageState.form_data["parameters"]["region"], "us-east-1"
                ),
                placeholder="us-east-1",
                class_name="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
            ),
            class_name="mb-4",
        ),
        rx.el.div(
            rx.el.label(
                "Access Key", class_name="text-sm font-medium text-gray-700 mb-1 block"
            ),
            rx.el.input(
                name="parameters.access_key",
                default_value=util.default(
                    LakehouseStorageState.form_data["parameters"]["access_key"], ""
                ),
                placeholder="AKIAIOSFODNN7EXAMPLE",
                class_name="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
            ),
            class_name="mb-4",
        ),
        rx.el.div(
            rx.el.label(
                "Secret Key", class_name="text-sm font-medium text-gray-700 mb-1 block"
            ),
            rx.el.input(
                name="parameters.secret_key",
                default_value=util.default(
                    LakehouseStorageState.form_data["parameters"]["secret_key"], ""
                ),
                type="password",
                placeholder=rx.cond(
                    LakehouseStorageState.is_editing,
                    "Leave empty to keep existing secret key",
                    "Enter secret key",
                ),
                class_name="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
            ),
            # Show help text in edit mode
            rx.cond(
                LakehouseStorageState.is_editing,
                rx.el.p(
                    "Secret key is encrypted and hidden. Leave empty to keep the existing secret key.",
                    class_name="text-xs text-gray-500 mt-1",
                ),
            ),
            # Show clear secret key checkbox in edit mode
            rx.cond(
                LakehouseStorageState.is_editing,
                rx.el.div(
                    rx.el.label(
                        rx.el.input(
                            type="checkbox",
                            checked=LakehouseStorageState.clear_secret_key,
                            on_change=LakehouseStorageState.toggle_clear_secret_key,
                            class_name="mr-2 h-4 w-4 text-orange-600 focus:ring-orange-500 border-gray-300 rounded",
                        ),
                        rx.el.span(
                            "Clear secret key (remove stored secret key)",
                            class_name="text-sm text-gray-700",
                        ),
                        class_name="flex items-center cursor-pointer",
                    ),
                    class_name="mt-2",
                ),
            ),
            class_name="mb-4",
        ),
        rx.el.div(
            rx.el.label(
                "Endpoint URL (Optional)",
                class_name="text-sm font-medium text-gray-700 mb-1 block",
            ),
            rx.el.input(
                name="parameters.endpoint_url",
                default_value=util.default(
                    LakehouseStorageState.form_data["parameters"]["endpoint_url"], ""
                ),
                placeholder="https://s3.custom-endpoint.com",
                class_name="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
            ),
            rx.el.p(
                "For S3-compatible services like MinIO or Wasabi",
                class_name="text-xs text-gray-500 mt-1",
            ),
            class_name="mb-4",
        ),
    )


def storage_modal() -> rx.Component:
    """Modal for creating and editing lakehouse storage."""
    return rx.radix.primitives.dialog.root(
        rx.radix.primitives.dialog.portal(
            rx.radix.primitives.dialog.overlay(
                class_name="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
            ),
            rx.radix.primitives.dialog.content(
                rx.radix.primitives.dialog.title(
                    rx.cond(
                        LakehouseStorageState.is_editing,
                        "Edit Lakehouse Storage",
                        "Create New Lakehouse Storage",
                    ),
                    class_name="text-xl font-semibold text-gray-800 mb-4",
                ),
                rx.radix.primitives.dialog.description(
                    rx.cond(
                        LakehouseStorageState.is_editing,
                        "Update the S3 configuration for your lakehouse storage.",
                        "Configure a new S3-based lakehouse storage for Iceberg datasets.",
                    ),
                    class_name="text-sm text-gray-600 mb-4",
                ),
                rx.el.form(
                    # General error message display
                    rx.cond(
                        LakehouseStorageState.error_message != "",
                        rx.el.div(
                            rx.icon("circle-alert", class_name="h-5 w-5 text-red-500"),
                            rx.el.span(
                                LakehouseStorageState.error_message,
                                class_name="text-sm text-red-700",
                            ),
                            class_name="flex items-center gap-2 p-3 mb-4 bg-red-50 border border-red-200 rounded-lg",
                        ),
                    ),
                    rx.el.div(
                        rx.el.label(
                            "Name",
                            class_name="text-sm font-medium text-gray-700 mb-1 block",
                        ),
                        rx.el.input(
                            placeholder="e.g., production-lakehouse",
                            name="name",
                            default_value=LakehouseStorageState.form_data["name"],
                            class_name=rx.cond(
                                LakehouseStorageState.form_errors.get("name") != None,
                                "w-full px-3 py-2 border border-red-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-red-500",
                                "w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
                            ),
                        ),
                        rx.cond(
                            LakehouseStorageState.form_errors.get("name") != None,
                            rx.el.p(
                                LakehouseStorageState.form_errors.get("name"),
                                class_name="text-sm text-red-600 mt-1",
                            ),
                        ),
                        class_name="mb-4",
                    ),
                    rx.el.div(
                        rx.el.label(
                            "Title",
                            class_name="text-sm font-medium text-gray-700 mb-1 block",
                        ),
                        rx.el.input(
                            placeholder="e.g., Production Lakehouse Storage",
                            name="title",
                            default_value=LakehouseStorageState.form_data["title"],
                            class_name=rx.cond(
                                LakehouseStorageState.form_errors.get("title") != None,
                                "w-full px-3 py-2 border border-red-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-red-500",
                                "w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
                            ),
                        ),
                        rx.cond(
                            LakehouseStorageState.form_errors.get("title") != None,
                            rx.el.p(
                                LakehouseStorageState.form_errors.get("title"),
                                class_name="text-sm text-red-600 mt-1",
                            ),
                        ),
                        class_name="mb-4",
                    ),
                    rx.el.div(
                        rx.el.h3(
                            "S3 Configuration",
                            class_name="font-semibold text-gray-700 mb-2",
                        ),
                        s3_form_fields(),
                        class_name="p-4 bg-gray-50 rounded-lg border border-gray-200 mb-6",
                    ),
                    on_submit=LakehouseStorageState.handle_submit,
                    id="storage-form",
                ),
                rx.el.div(
                    rx.radix.primitives.dialog.close(
                        base_button(
                            "Cancel",
                            on_click=LakehouseStorageState.close_storage_modal,
                            class_name="bg-gray-200 text-gray-800 hover:bg-gray-300 focus:ring-gray-300",
                        ),
                        as_child=True,
                    ),
                    base_button(
                        "Test Connection",
                        type="submit",
                        form="storage-form",
                        on_click=LakehouseStorageState.set_submit_action("test"),
                        icon="plug-zap",
                        is_loading=LakehouseStorageState.is_testing_connection,
                        class_name="bg-blue-500 text-white hover:bg-blue-600 focus:ring-blue-500",
                    ),
                    base_button(
                        "Save Storage",
                        type="submit",
                        form="storage-form",
                        on_click=LakehouseStorageState.set_submit_action("save"),
                        icon="save",
                    ),
                    class_name="flex justify-end gap-3 pt-4 border-t border-gray-200",
                ),
                class_name="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-xl shadow-2xl p-6 w-full max-w-2xl z-50",
            ),
        ),
        open=LakehouseStorageState.show_storage_modal,
        on_open_change=LakehouseStorageState.close_storage_modal,
    )


def delete_dialog() -> rx.Component:
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
                    "Are you sure you want to delete this lakehouse storage? This action cannot be undone.",
                    class_name="text-gray-600 my-4",
                ),
                rx.el.div(
                    rx.radix.primitives.dialog.close(
                        base_button(
                            "Cancel",
                            on_click=LakehouseStorageState.close_delete_dialog,
                            class_name="bg-gray-200 text-gray-800 hover:bg-gray-300 focus:ring-gray-300",
                        ),
                        as_child=True,
                    ),
                    base_button(
                        "Delete",
                        on_click=LakehouseStorageState.confirm_delete,
                        class_name="bg-red-600 text-white hover:bg-red-700 focus:ring-red-500",
                    ),
                    class_name="flex justify-end gap-3 pt-4 border-t border-gray-200",
                ),
                class_name="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-xl shadow-2xl p-6 w-full max-w-md z-50",
            ),
        ),
        open=LakehouseStorageState.show_delete_dialog,
        on_open_change=LakehouseStorageState.close_delete_dialog,
    )


def empty_state() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("database", class_name="h-16 w-16 text-gray-400 mx-auto"),
            rx.el.h3(
                "No Lakehouse Storage Found",
                class_name="mt-4 text-lg font-semibold text-gray-800",
            ),
            rx.el.p(
                "Get started by creating your first lakehouse storage.",
                class_name="mt-2 text-sm text-gray-500",
            ),
            base_button(
                "Create New Storage",
                icon="plus",
                on_click=LakehouseStorageState.open_create_modal,
                class_name="mt-6",
            ),
            class_name="text-center",
        ),
        class_name="flex items-center justify-center h-full bg-gray-50 rounded-lg border-2 border-dashed border-gray-200 p-12",
    )


def lakehouse_storage_page() -> rx.Component:
    return base_layout(
        rx.el.div(
            storage_modal(),
            delete_dialog(),
            rx.cond(
                LakehouseStorageState.is_loading,
                loading_spinner(),
                rx.el.div(
                    rx.el.div(
                        rx.el.div(
                            rx.el.div(
                                rx.icon("search", class_name="h-5 w-5 text-gray-400"),
                                class_name="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none",
                            ),
                            rx.el.input(
                                placeholder="Search storages...",
                                on_change=LakehouseStorageState.set_search_query,
                                class_name="w-full max-w-xs pl-10 pr-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
                                default_value=LakehouseStorageState.search_query,
                            ),
                            class_name="relative",
                        ),
                        base_button(
                            "Create New Storage",
                            icon="plus",
                            on_click=LakehouseStorageState.open_create_modal,
                        ),
                        class_name="flex justify-between items-center mb-6",
                    ),
                    rx.cond(
                        LakehouseStorageState.filtered_storages.length() > 0,
                        rx.el.div(
                            rx.foreach(
                                LakehouseStorageState.filtered_storages, storage_card
                            ),
                            class_name="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6",
                        ),
                        empty_state(),
                    ),
                    class_name="h-full",
                ),
            ),
        ),
        on_mount=LakehouseStorageState.load_initial_data,
    )
