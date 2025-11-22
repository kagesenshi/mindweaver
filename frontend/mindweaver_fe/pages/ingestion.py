import reflex as rx
from mindweaver_fe.components.layout import base_layout
from mindweaver_fe.components.reusables import card, base_button
from mindweaver_fe.components.loading_spinner import loading_spinner
from mindweaver_fe.states.ingestion_state import IngestionState, Ingestion, IngestionRun
import mindweaver_fe.util as util


TIMEZONES = [
    "UTC",
    "America/New_York",
    "America/Chicago",
    "America/Denver",
    "America/Los_Angeles",
    "Europe/London",
    "Europe/Paris",
    "Asia/Tokyo",
    "Asia/Shanghai",
    "Asia/Singapore",
    "Australia/Sydney",
]


def status_badge(status: rx.Var[str]) -> rx.Component:
    """Badge for ingestion run status."""
    base_class = (
        " text-xs font-medium px-2.5 py-1 rounded-full w-fit flex items-center gap-1.5"
    )
    return rx.el.span(
        rx.cond(
            status == "running",
            rx.el.div(class_name="h-2 w-2 rounded-full bg-blue-500 animate-pulse"),
            None,
        ),
        status,
        class_name=rx.match(
            status,
            ("pending", "bg-gray-100 text-gray-800" + base_class),
            ("running", "bg-blue-100 text-blue-800" + base_class),
            ("completed", "bg-green-100 text-green-800" + base_class),
            ("failed", "bg-red-100 text-red-800" + base_class),
            "bg-gray-100 text-gray-800" + base_class,
        ),
    )


def ingestion_table() -> rx.Component:
    """Table displaying all ingestions."""
    return rx.el.div(
        rx.el.table(
            rx.el.thead(
                rx.el.tr(
                    rx.el.th(
                        "Name",
                        class_name="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider",
                    ),
                    rx.el.th(
                        "Data Source",
                        class_name="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider",
                    ),
                    rx.el.th(
                        "Lakehouse Storage",
                        class_name="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider",
                    ),
                    rx.el.th(
                        "Schedule",
                        class_name="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider",
                    ),
                    rx.el.th(
                        "Type",
                        class_name="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider",
                    ),
                    rx.el.th(
                        "Actions",
                        class_name="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider",
                    ),
                ),
                class_name="bg-gray-50",
            ),
            rx.el.tbody(
                rx.foreach(
                    IngestionState.filtered_ingestions,
                    lambda ingestion: rx.el.tr(
                        rx.el.td(
                            rx.el.div(
                                rx.el.div(
                                    ingestion["name"],
                                    class_name="text-sm font-medium text-gray-900",
                                ),
                                rx.el.div(
                                    ingestion["title"],
                                    class_name="text-sm text-gray-500",
                                ),
                            ),
                            class_name="px-6 py-4 whitespace-nowrap",
                        ),
                        rx.el.td(
                            IngestionState.data_source_names[
                                ingestion["data_source_id"]
                            ],
                            class_name="px-6 py-4 whitespace-nowrap text-sm text-gray-700",
                        ),
                        rx.el.td(
                            IngestionState.lakehouse_storage_names[
                                ingestion["lakehouse_storage_id"]
                            ],
                            class_name="px-6 py-4 whitespace-nowrap text-sm text-gray-700",
                        ),
                        rx.el.td(
                            rx.el.code(
                                ingestion["cron_schedule"],
                                class_name="text-xs bg-gray-100 px-2 py-1 rounded",
                            ),
                            class_name="px-6 py-4 whitespace-nowrap",
                        ),
                        rx.el.td(
                            rx.el.span(
                                ingestion["ingestion_type"],
                                class_name="text-xs font-medium px-2.5 py-1 rounded-full bg-purple-100 text-purple-800",
                            ),
                            class_name="px-6 py-4 whitespace-nowrap",
                        ),
                        rx.el.td(
                            rx.el.div(
                                base_button(
                                    "Execute",
                                    on_click=lambda: IngestionState.open_execute_dialog(
                                        ingestion
                                    ),
                                    icon="play",
                                    class_name="text-green-600 hover:text-green-900 bg-green-50 hover:bg-green-100 border-none shadow-none px-3 py-1 h-8 text-xs",
                                ),
                                base_button(
                                    "Edit",
                                    on_click=lambda: IngestionState.open_edit_modal(
                                        ingestion
                                    ),
                                    icon="pencil",
                                    class_name="text-blue-600 hover:text-blue-900 bg-blue-50 hover:bg-blue-100 border-none shadow-none px-3 py-1 h-8 text-xs",
                                ),
                                base_button(
                                    "Delete",
                                    on_click=lambda: IngestionState.open_delete_dialog(
                                        ingestion
                                    ),
                                    icon="trash-2",
                                    class_name="text-red-600 hover:text-red-900 bg-red-50 hover:bg-red-100 border-none shadow-none px-3 py-1 h-8 text-xs",
                                ),
                                class_name="flex justify-end gap-2",
                            ),
                            class_name="px-6 py-4 whitespace-nowrap text-right text-sm font-medium",
                        ),
                        class_name="bg-white border-b border-gray-100 hover:bg-gray-50",
                    ),
                ),
                class_name="divide-y divide-gray-200",
            ),
            class_name="min-w-full divide-y divide-gray-200",
        ),
        class_name="overflow-x-auto rounded-lg border border-gray-200 shadow-sm",
    )


def database_config_fields() -> rx.Component:
    """Configuration fields for database ingestion."""
    return rx.el.div(
        rx.el.div(
            rx.el.label(
                "Table Name",
                class_name="text-sm font-medium text-gray-700 mb-1 block",
            ),
            rx.el.input(
                name="config.table_name",
                default_value=util.default(
                    IngestionState.form_data["config"]["table_name"], ""
                ),
                placeholder="e.g., users",
                class_name="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
            ),
            class_name="mb-4",
        ),
        rx.el.div(
            rx.el.label(
                "Ingestion Type",
                class_name="text-sm font-medium text-gray-700 mb-1 block",
            ),
            rx.el.select(
                rx.el.option("Full Refresh", value="full_refresh"),
                rx.el.option("Incremental", value="incremental"),
                name="config.ingestion_type",
                value=IngestionState.form_data["config"]["ingestion_type"],
                on_change=lambda val: IngestionState.set_config_field(
                    "ingestion_type", val
                ),
                class_name="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
            ),
            class_name="mb-4",
        ),
        # Incremental-specific fields
        rx.cond(
            IngestionState.form_data["config"]["ingestion_type"] == "incremental",
            rx.el.div(
                rx.el.div(
                    rx.el.label(
                        "Primary Keys (comma-separated)",
                        class_name="text-sm font-medium text-gray-700 mb-1 block",
                    ),
                    rx.el.input(
                        name="config.primary_keys",
                        default_value=IngestionState.primary_keys_string,
                        placeholder="e.g., id, user_id",
                        class_name="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
                    ),
                    class_name="mb-4",
                ),
                rx.el.div(
                    rx.el.label(
                        "Last Modified Column",
                        class_name="text-sm font-medium text-gray-700 mb-1 block",
                    ),
                    rx.el.input(
                        name="config.last_modified_column",
                        default_value=util.default(
                            IngestionState.form_data["config"]["last_modified_column"],
                            "",
                        ),
                        placeholder="e.g., updated_at",
                        class_name="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
                    ),
                    class_name="mb-4",
                ),
                rx.el.div(
                    rx.el.label(
                        "Created Column",
                        class_name="text-sm font-medium text-gray-700 mb-1 block",
                    ),
                    rx.el.input(
                        name="config.created_column",
                        default_value=util.default(
                            IngestionState.form_data["config"]["created_column"], ""
                        ),
                        placeholder="e.g., created_at",
                        class_name="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
                    ),
                    class_name="mb-4",
                ),
                rx.el.div(
                    rx.el.label(
                        "Source Timezone",
                        class_name="text-sm font-medium text-gray-700 mb-1 block",
                    ),
                    rx.el.select(
                        rx.foreach(
                            TIMEZONES,
                            lambda tz: rx.el.option(tz, value=tz),
                        ),
                        name="config.source_timezone",
                        default_value=util.default(
                            IngestionState.form_data["config"]["source_timezone"], "UTC"
                        ),
                        class_name="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
                    ),
                    class_name="mb-4",
                ),
                class_name="p-4 bg-blue-50 rounded-lg border border-blue-200",
            ),
        ),
    )


def ingestion_modal() -> rx.Component:
    """Modal for creating and editing ingestions."""
    return rx.radix.primitives.dialog.root(
        rx.radix.primitives.dialog.portal(
            rx.radix.primitives.dialog.overlay(
                class_name="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
            ),
            rx.radix.primitives.dialog.content(
                rx.radix.primitives.dialog.title(
                    rx.cond(
                        IngestionState.is_editing,
                        "Edit Ingestion",
                        "Create New Ingestion",
                    ),
                    class_name="text-xl font-semibold text-gray-800 mb-4",
                ),
                rx.radix.primitives.dialog.description(
                    rx.cond(
                        IngestionState.is_editing,
                        "Update the configuration for your ingestion.",
                        "Configure a new data ingestion to lakehouse storage.",
                    ),
                    class_name="text-sm text-gray-600 mb-4",
                ),
                rx.el.form(
                    # General error message display
                    rx.cond(
                        IngestionState.error_message != "",
                        rx.el.div(
                            rx.icon("circle-alert", class_name="h-5 w-5 text-red-500"),
                            rx.el.span(
                                IngestionState.error_message,
                                class_name="text-sm text-red-700",
                            ),
                            class_name="flex items-center gap-2 p-3 mb-4 bg-red-50 border border-red-200 rounded-lg",
                        ),
                    ),
                    # Basic Info
                    rx.el.div(
                        rx.el.label(
                            "Name",
                            class_name="text-sm font-medium text-gray-700 mb-1 block",
                        ),
                        rx.el.input(
                            placeholder="e.g., daily-user-sync",
                            name="name",
                            default_value=IngestionState.form_data["name"],
                            class_name=rx.cond(
                                IngestionState.form_errors.get("name") != None,
                                "w-full px-3 py-2 border border-red-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-red-500",
                                "w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
                            ),
                        ),
                        rx.cond(
                            IngestionState.form_errors.get("name") != None,
                            rx.el.p(
                                IngestionState.form_errors.get("name"),
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
                            placeholder="e.g., Daily User Synchronization",
                            name="title",
                            default_value=IngestionState.form_data["title"],
                            class_name=rx.cond(
                                IngestionState.form_errors.get("title") != None,
                                "w-full px-3 py-2 border border-red-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-red-500",
                                "w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
                            ),
                        ),
                        rx.cond(
                            IngestionState.form_errors.get("title") != None,
                            rx.el.p(
                                IngestionState.form_errors.get("title"),
                                class_name="text-sm text-red-600 mt-1",
                            ),
                        ),
                        class_name="mb-4",
                    ),
                    # Source Configuration
                    rx.el.h3(
                        "Source Configuration",
                        class_name="font-semibold text-gray-700 mb-2 mt-6",
                    ),
                    rx.el.div(
                        rx.el.label(
                            "Data Source",
                            class_name="text-sm font-medium text-gray-700 mb-1 block",
                        ),
                        rx.el.select(
                            rx.foreach(
                                IngestionState.all_data_sources,
                                lambda ds: rx.el.option(
                                    ds["name"], value=ds["id"].to_string()
                                ),
                            ),
                            name="data_source_id",
                            value=IngestionState.form_data[
                                "data_source_id"
                            ].to_string(),
                            on_change=IngestionState.set_data_source_id,
                            class_name="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
                        ),
                        class_name="mb-4",
                    ),
                    rx.el.div(
                        rx.el.label(
                            "Lakehouse Storage",
                            class_name="text-sm font-medium text-gray-700 mb-1 block",
                        ),
                        rx.el.select(
                            rx.foreach(
                                IngestionState.all_lakehouse_storages,
                                lambda ls: rx.el.option(
                                    ls["name"], value=ls["id"].to_string()
                                ),
                            ),
                            name="lakehouse_storage_id",
                            value=IngestionState.form_data[
                                "lakehouse_storage_id"
                            ].to_string(),
                            on_change=IngestionState.set_lakehouse_storage_id,
                            class_name="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
                        ),
                        class_name="mb-4",
                    ),
                    rx.el.div(
                        rx.el.label(
                            "Storage Path",
                            class_name="text-sm font-medium text-gray-700 mb-1 block",
                        ),
                        rx.el.input(
                            name="storage_path",
                            default_value=IngestionState.form_data["storage_path"],
                            placeholder="e.g., /data/users/",
                            class_name="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
                        ),
                        class_name="mb-4",
                    ),
                    # Schedule Configuration
                    rx.el.h3(
                        "Schedule Configuration",
                        class_name="font-semibold text-gray-700 mb-2 mt-6",
                    ),
                    rx.el.div(
                        rx.el.label(
                            "Cron Schedule",
                            class_name="text-sm font-medium text-gray-700 mb-1 block",
                        ),
                        rx.el.input(
                            name="cron_schedule",
                            default_value=IngestionState.form_data["cron_schedule"],
                            placeholder="e.g., 0 2 * * * (daily at 2 AM)",
                            class_name="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
                        ),
                        rx.el.p(
                            "Use cron syntax: minute hour day month weekday",
                            class_name="text-xs text-gray-500 mt-1",
                        ),
                        class_name="mb-4",
                    ),
                    rx.el.div(
                        rx.el.div(
                            rx.el.label(
                                "Start Date (Optional)",
                                class_name="text-sm font-medium text-gray-700 mb-1 block",
                            ),
                            rx.el.input(
                                name="start_date",
                                type="datetime-local",
                                default_value=IngestionState.form_data["start_date"],
                                class_name="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
                            ),
                            class_name="flex-1",
                        ),
                        rx.el.div(
                            rx.el.label(
                                "End Date (Optional)",
                                class_name="text-sm font-medium text-gray-700 mb-1 block",
                            ),
                            rx.el.input(
                                name="end_date",
                                type="datetime-local",
                                default_value=IngestionState.form_data["end_date"],
                                class_name="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
                            ),
                            class_name="flex-1",
                        ),
                        class_name="flex gap-4 mb-4",
                    ),
                    rx.el.div(
                        rx.el.label(
                            "Timezone",
                            class_name="text-sm font-medium text-gray-700 mb-1 block",
                        ),
                        rx.el.select(
                            rx.foreach(
                                TIMEZONES,
                                lambda tz: rx.el.option(tz, value=tz),
                            ),
                            name="timezone",
                            default_value=IngestionState.form_data["timezone"],
                            class_name="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
                        ),
                        class_name="mb-4",
                    ),
                    # Database-Specific Configuration
                    rx.cond(
                        IngestionState.selected_data_source_type == "Database",
                        rx.el.div(
                            rx.el.h3(
                                "Database Configuration",
                                class_name="font-semibold text-gray-700 mb-2 mt-6",
                            ),
                            database_config_fields(),
                        ),
                    ),
                    on_submit=IngestionState.handle_submit,
                    id="ingestion-form",
                ),
                rx.el.div(
                    rx.radix.primitives.dialog.close(
                        base_button(
                            "Cancel",
                            on_click=IngestionState.close_ingestion_modal,
                            class_name="bg-gray-200 text-gray-800 hover:bg-gray-300 focus:ring-gray-300",
                        ),
                        as_child=True,
                    ),
                    base_button(
                        "Save Ingestion",
                        type="submit",
                        form="ingestion-form",
                        icon="save",
                    ),
                    class_name="flex justify-end gap-3 pt-4 border-t border-gray-200 mt-6",
                ),
                class_name="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-xl shadow-2xl p-6 w-full max-w-3xl max-h-[90vh] overflow-y-auto z-50",
            ),
        ),
        open=IngestionState.show_ingestion_modal,
        on_open_change=IngestionState.close_ingestion_modal,
    )


def delete_dialog() -> rx.Component:
    """Confirmation dialog for deleting an ingestion."""
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
                    "Are you sure you want to delete this ingestion? This action cannot be undone.",
                    class_name="text-gray-600 my-4",
                ),
                rx.el.div(
                    rx.radix.primitives.dialog.close(
                        base_button(
                            "Cancel",
                            on_click=IngestionState.close_delete_dialog,
                            class_name="bg-gray-200 text-gray-800 hover:bg-gray-300 focus:ring-gray-300",
                        ),
                        as_child=True,
                    ),
                    base_button(
                        "Delete",
                        on_click=IngestionState.confirm_delete,
                        class_name="bg-red-600 text-white hover:bg-red-700 focus:ring-red-500",
                    ),
                    class_name="flex justify-end gap-3 pt-4 border-t border-gray-200",
                ),
                class_name="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-xl shadow-2xl p-6 w-full max-w-md z-50",
            ),
        ),
        open=IngestionState.show_delete_dialog,
        on_open_change=IngestionState.close_delete_dialog,
    )


def execute_dialog() -> rx.Component:
    """Confirmation dialog for executing an ingestion."""
    return rx.radix.primitives.dialog.root(
        rx.radix.primitives.dialog.portal(
            rx.radix.primitives.dialog.overlay(
                class_name="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
            ),
            rx.radix.primitives.dialog.content(
                rx.radix.primitives.dialog.title(
                    "Execute Ingestion",
                    class_name="text-xl font-semibold text-gray-800",
                ),
                rx.radix.primitives.dialog.description(
                    "Trigger a manual execution of this ingestion now?",
                    class_name="text-gray-600 my-4",
                ),
                rx.el.div(
                    rx.radix.primitives.dialog.close(
                        base_button(
                            "Cancel",
                            on_click=IngestionState.close_execute_dialog,
                            class_name="bg-gray-200 text-gray-800 hover:bg-gray-300 focus:ring-gray-300",
                        ),
                        as_child=True,
                    ),
                    base_button(
                        "Execute Now",
                        on_click=IngestionState.confirm_execute,
                        icon="play",
                        is_loading=IngestionState.is_executing,
                        class_name="bg-green-600 text-white hover:bg-green-700 focus:ring-green-500",
                    ),
                    class_name="flex justify-end gap-3 pt-4 border-t border-gray-200",
                ),
                class_name="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-xl shadow-2xl p-6 w-full max-w-md z-50",
            ),
        ),
        open=IngestionState.show_execute_dialog,
        on_open_change=IngestionState.close_execute_dialog,
    )


def run_history_section() -> rx.Component:
    """Section displaying ingestion run history."""
    return rx.el.div(
        rx.el.h2(
            "Execution History", class_name="text-xl font-semibold text-gray-800 mb-4"
        ),
        rx.cond(
            IngestionState.all_runs.length() > 0,
            card(
                rx.el.table(
                    rx.el.thead(
                        rx.el.tr(
                            rx.el.th("Ingestion"),
                            rx.el.th("Status"),
                            rx.el.th("Records"),
                            rx.el.th("Started"),
                            rx.el.th("Completed"),
                            rx.el.th("Error"),
                            class_name="text-left text-xs font-medium text-gray-500 uppercase tracking-wider",
                        )
                    ),
                    rx.el.tbody(
                        rx.foreach(
                            IngestionState.all_runs,
                            lambda run: rx.el.tr(
                                rx.el.td(
                                    IngestionState.ingestion_names[run["ingestion_id"]]
                                ),
                                rx.el.td(status_badge(run["status"])),
                                rx.el.td(run["records_processed"]),
                                rx.el.td(run["started_at"]),
                                rx.el.td(run["completed_at"]),
                                rx.el.td(
                                    rx.cond(
                                        run["error_message"] != "",
                                        rx.el.span(
                                            run["error_message"],
                                            class_name="text-xs text-red-600",
                                        ),
                                        "-",
                                    )
                                ),
                                class_name="border-t border-gray-100",
                            ),
                        ),
                        class_name="divide-y divide-gray-100 bg-white text-sm text-gray-700",
                    ),
                    class_name="w-full table-auto",
                )
            ),
            rx.el.div(
                rx.el.p(
                    "No execution runs yet.",
                    class_name="text-center text-gray-500",
                ),
                class_name="py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-200",
            ),
        ),
        class_name="mt-12",
    )


def empty_state() -> rx.Component:
    """Empty state when no ingestions exist."""
    return rx.el.div(
        rx.el.div(
            rx.icon("database-zap", class_name="h-16 w-16 text-gray-400 mx-auto"),
            rx.el.h3(
                "No Ingestions Found",
                class_name="mt-4 text-lg font-semibold text-gray-800",
            ),
            rx.el.p(
                "Get started by creating your first data ingestion.",
                class_name="mt-2 text-sm text-gray-500",
            ),
            base_button(
                "Create New Ingestion",
                icon="plus",
                on_click=IngestionState.open_create_modal,
                class_name="mt-6",
            ),
            class_name="text-center",
        ),
        class_name="flex items-center justify-center h-full bg-gray-50 rounded-lg border-2 border-dashed border-gray-200 p-12",
    )


def ingestion_page() -> rx.Component:
    """Main ingestion management page."""
    return base_layout(
        rx.el.div(
            ingestion_modal(),
            delete_dialog(),
            execute_dialog(),
            rx.cond(
                IngestionState.is_loading,
                loading_spinner(),
                rx.el.div(
                    rx.el.div(
                        rx.el.div(
                            rx.el.div(
                                rx.icon("search", class_name="h-5 w-5 text-gray-400"),
                                class_name="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none",
                            ),
                            rx.el.input(
                                placeholder="Search ingestions...",
                                on_change=IngestionState.set_search_query,
                                class_name="w-full max-w-xs pl-10 pr-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
                                default_value=IngestionState.search_query,
                            ),
                            class_name="relative",
                        ),
                        base_button(
                            "Create New Ingestion",
                            icon="plus",
                            on_click=IngestionState.open_create_modal,
                        ),
                        class_name="flex justify-between items-center mb-6",
                    ),
                    rx.cond(
                        IngestionState.filtered_ingestions.length() > 0,
                        ingestion_table(),
                        empty_state(),
                    ),
                    run_history_section(),
                    class_name="h-full",
                ),
            ),
        ),
        on_mount=IngestionState.load_initial_data,
    )
