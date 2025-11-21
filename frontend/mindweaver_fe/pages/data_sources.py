import reflex as rx
from mindweaver_fe.components.layout import base_layout
from mindweaver_fe.components.reusables import card, base_button
from mindweaver_fe.states.data_sources_state import (
    DataSourcesState,
    DataSource,
    ImportJob,
)
import mindweaver_fe.util as util


def type_badge(source_type: rx.Var[str]) -> rx.Component:
    """A badge component to display the data source type."""
    base_class = " text-xs font-medium px-2.5 py-1 rounded-full w-fit"
    return rx.el.span(
        source_type,
        class_name=rx.match(
            source_type,
            ("API", "bg-blue-100 text-blue-800" + base_class),
            ("Database", "bg-purple-100 text-purple-800" + base_class),
            ("File Upload", "bg-green-100 text-green-800" + base_class),
            ("Web Scraper", "bg-yellow-100 text-yellow-800" + base_class),
            "bg-gray-100 text-gray-800" + base_class,
        ),
    )


def status_indicator(status: rx.Var[str]) -> rx.Component:
    """A badge component to display the data source status."""
    base_class = (
        " text-xs font-medium px-2.5 py-1 rounded-full w-fit flex items-center gap-1.5"
    )
    return rx.el.span(
        rx.el.div(
            class_name=rx.match(
                status,
                ("Connected", "h-2 w-2 rounded-full bg-green-500"),
                ("Disconnected", "h-2 w-2 rounded-full bg-gray-400"),
                ("Error", "h-2 w-2 rounded-full bg-red-500"),
                "h-2 w-2 rounded-full bg-gray-400",
            )
        ),
        status,
        class_name=rx.match(
            status,
            ("Connected", "bg-green-100 text-green-800" + base_class),
            ("Disconnected", "bg-gray-100 text-gray-800" + base_class),
            ("Error", "bg-red-100 text-red-800" + base_class),
            "bg-gray-100 text-gray-800" + base_class,
        ),
    )


def source_card(source: DataSource) -> rx.Component:
    """A card component for a single data source."""
    return card(
        rx.el.div(
            rx.el.div(
                rx.el.h3(source["name"], class_name="text-lg font-bold text-gray-900"),
                type_badge(source["type"]),
                class_name="flex justify-between items-start mb-2",
            ),
            rx.el.p(
                f"Syncs data via {source['type']}",
                class_name="text-sm text-gray-600 mb-4 h-10 overflow-hidden",
            ),
            rx.el.div(
                status_indicator(source["status"]),
                rx.el.div(
                    rx.icon("clock", class_name="h-4 w-4 text-gray-400"),
                    rx.el.span(
                        f"Synced: {source['last_sync']}",
                        class_name="text-sm text-gray-500 ml-2",
                    ),
                    class_name="flex items-center",
                ),
                class_name="flex justify-between items-center text-sm text-gray-500 border-t border-gray-100 pt-4 mt-4",
            ),
        ),
        rx.el.div(
            base_button(
                "Import Data",
                on_click=lambda: DataSourcesState.open_import_dialog(source),
                icon="cloud-upload",
                class_name="bg-green-500 text-white hover:bg-green-600 shadow-sm focus:ring-green-500",
            ),
            base_button(
                "Edit",
                on_click=lambda: DataSourcesState.open_edit_modal(source),
                icon="pencil",
                class_name="bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 shadow-sm focus:ring-gray-300",
            ),
            base_button(
                "Delete",
                on_click=lambda: DataSourcesState.open_delete_dialog(source),
                icon="trash-2",
                class_name="bg-red-500 text-white hover:bg-red-600 shadow-sm focus:ring-red-500",
            ),
            class_name="flex gap-2 mt-4",
        ),
    )


def api_form_fields() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.label(
                "Base URL", class_name="text-sm font-medium text-gray-700 mb-1 block"
            ),
            rx.el.input(
                name="parameters.base_url",
                default_value=util.default(
                    DataSourcesState.form_data["parameters"]["base_url"], ""
                ),
                placeholder="https://api.example.com/v1",
                class_name="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
            ),
            class_name="mb-4",
        ),
        rx.el.div(
            rx.el.label(
                "API Key", class_name="text-sm font-medium text-gray-700 mb-1 block"
            ),
            rx.el.input(
                name="parameters.api_key",
                default_value=util.default(
                    DataSourcesState.form_data["parameters"]["api_key"], ""
                ),
                type="password",
                placeholder="**********",
                class_name="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
            ),
            class_name="mb-4",
        ),
    )


def db_form_fields() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.label(
                "Database Type",
                class_name="text-sm font-medium text-gray-700 mb-1 block",
            ),
            rx.el.select(
                rx.el.option("PostgreSQL", value="postgresql"),
                rx.el.option("MySQL", value="mysql"),
                rx.el.option("MongoDB", value="mongodb"),
                rx.el.option("MS SQL Server", value="mssql"),
                rx.el.option("Oracle", value="oracle"),
                name="parameters.database_type",
                default_value=util.default(
                    DataSourcesState.form_data["parameters"]["database_type"],
                    "postgresql",
                ),
                class_name="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
            ),
            class_name="mb-4",
        ),
        rx.el.div(
            rx.el.label(
                "Host", class_name="text-sm font-medium text-gray-700 mb-1 block"
            ),
            rx.el.input(
                name="parameters.host",
                default_value=util.default(
                    DataSourcesState.form_data["parameters"]["host"], ""
                ),
                placeholder="localhost",
                class_name="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
            ),
            class_name="mb-4",
        ),
        rx.el.div(
            rx.el.label(
                "Port", class_name="text-sm font-medium text-gray-700 mb-1 block"
            ),
            rx.el.input(
                name="parameters.port",
                default_value=DataSourcesState.form_data["parameters"][
                    "port"
                ].to_string(),
                placeholder="5432",
                type="number",
                class_name="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
            ),
            class_name="mb-4",
        ),
        rx.el.div(
            rx.el.label(
                "Username", class_name="text-sm font-medium text-gray-700 mb-1 block"
            ),
            rx.el.input(
                name="parameters.username",
                default_value=util.default(
                    DataSourcesState.form_data["parameters"]["username"], ""
                ),
                placeholder="admin",
                class_name="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
            ),
            class_name="mb-4",
        ),
        rx.el.div(
            rx.el.label(
                "Password", class_name="text-sm font-medium text-gray-700 mb-1 block"
            ),
            rx.el.input(
                name="parameters.password",
                default_value=util.default(
                    DataSourcesState.form_data["parameters"]["password"], ""
                ),
                type="password",
                placeholder=rx.cond(
                    DataSourcesState.is_editing,
                    "Leave empty to keep existing password",
                    "Enter database password",
                ),
                class_name="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
            ),
            # Show help text in edit mode
            rx.cond(
                DataSourcesState.is_editing,
                rx.el.p(
                    "Password is encrypted and hidden. Leave empty to keep the existing password.",
                    class_name="text-xs text-gray-500 mt-1",
                ),
            ),
            # Show clear password checkbox in edit mode
            rx.cond(
                DataSourcesState.is_editing,
                rx.el.div(
                    rx.el.label(
                        rx.el.input(
                            type="checkbox",
                            checked=DataSourcesState.clear_password,
                            on_change=DataSourcesState.toggle_clear_password,
                            class_name="mr-2 h-4 w-4 text-orange-600 focus:ring-orange-500 border-gray-300 rounded",
                        ),
                        rx.el.span(
                            "Clear password (remove stored password)",
                            class_name="text-sm text-gray-700",
                        ),
                        class_name="flex items-center cursor-pointer",
                    ),
                    class_name="mt-2",
                ),
            ),
            class_name="mb-4",
        ),
    )


def file_upload_form_fields() -> rx.Component:
    return rx.el.div(
        rx.el.label(
            "Upload Area", class_name="text-sm font-medium text-gray-700 mb-1 block"
        ),
        rx.el.div(
            rx.icon("cloud_upload", class_name="h-8 w-8 text-gray-400 mb-2"),
            rx.el.text("Drag and drop files here or click to select files."),
            class_name="flex flex-col items-center justify-center p-6 border-2 border-dashed border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50",
        ),
    )


def web_scraper_form_fields() -> rx.Component:
    return rx.el.div(
        rx.el.label(
            "Start URL", class_name="text-sm font-medium text-gray-700 mb-1 block"
        ),
        rx.el.input(
            name="parameters.start_url",
            default_value=util.default(
                DataSourcesState.form_data["parameters"]["start_url"], ""
            ),
            placeholder="https://example.com",
            class_name="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
        ),
    )


def source_modal() -> rx.Component:
    """Modal for creating and editing data sources."""
    return rx.radix.primitives.dialog.root(
        rx.radix.primitives.dialog.portal(
            rx.radix.primitives.dialog.overlay(
                class_name="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
            ),
            rx.radix.primitives.dialog.content(
                rx.radix.primitives.dialog.title(
                    rx.cond(
                        DataSourcesState.is_editing,
                        "Edit Data Source",
                        "Create New Data Source",
                    ),
                    class_name="text-xl font-semibold text-gray-800 mb-4",
                ),
                rx.el.form(
                    # General error message display
                    rx.cond(
                        DataSourcesState.error_message != "",
                        rx.el.div(
                            rx.icon("circle-alert", class_name="h-5 w-5 text-red-500"),
                            rx.el.span(
                                DataSourcesState.error_message,
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
                            placeholder="e.g., Stripe API",
                            name="name",
                            default_value=DataSourcesState.form_data["name"],
                            class_name=rx.cond(
                                DataSourcesState.form_errors.get("name") != None,
                                "w-full px-3 py-2 border border-red-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-red-500",
                                "w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
                            ),
                        ),
                        rx.cond(
                            DataSourcesState.form_errors.get("name") != None,
                            rx.el.p(
                                DataSourcesState.form_errors.get("name"),
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
                            placeholder="e.g., Stripe Payment API",
                            name="title",
                            default_value=DataSourcesState.form_data["title"],
                            class_name=rx.cond(
                                DataSourcesState.form_errors.get("title") != None,
                                "w-full px-3 py-2 border border-red-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-red-500",
                                "w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
                            ),
                        ),
                        rx.cond(
                            DataSourcesState.form_errors.get("title") != None,
                            rx.el.p(
                                DataSourcesState.form_errors.get("title"),
                                class_name="text-sm text-red-600 mt-1",
                            ),
                        ),
                        class_name="mb-4",
                    ),
                    rx.el.div(
                        rx.el.label(
                            "Source Type",
                            class_name="text-sm font-medium text-gray-700 mb-1 block",
                        ),
                        rx.el.select(
                            rx.foreach(
                                DataSourcesState.source_type_options,
                                lambda type: rx.el.option(type, value=type),
                            ),
                            name="source_type",
                            value=DataSourcesState.form_data["source_type"],
                            on_change=lambda val: DataSourcesState.set_form_data_field(
                                "source_type", val
                            ),
                            class_name="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
                            disabled=DataSourcesState.is_editing,
                        ),
                        class_name="mb-4",
                    ),
                    rx.el.div(
                        rx.el.h3(
                            "Configuration",
                            class_name="font-semibold text-gray-700 mb-2",
                        ),
                        rx.match(
                            DataSourcesState.form_data["source_type"],
                            ("API", api_form_fields()),
                            ("Database", db_form_fields()),
                            ("File Upload", file_upload_form_fields()),
                            ("Web Scraper", web_scraper_form_fields()),
                            rx.el.p(
                                "Select a source type to see configuration options."
                            ),
                        ),
                        class_name="p-4 bg-gray-50 rounded-lg border border-gray-200 mb-6",
                    ),
                    on_submit=DataSourcesState.handle_submit,
                    id="source-form",
                ),
                rx.el.div(
                    rx.radix.primitives.dialog.close(
                        base_button(
                            "Cancel",
                            on_click=DataSourcesState.close_source_modal,
                            class_name="bg-gray-200 text-gray-800 hover:bg-gray-300 focus:ring-gray-300",
                        ),
                        as_child=True,
                    ),
                    base_button(
                        "Test Connection",
                        type="submit",
                        form="source-form",
                        on_click=DataSourcesState.set_submit_action("test"),
                        icon="plug-zap",
                        is_loading=DataSourcesState.is_testing_connection,
                        class_name="bg-blue-500 text-white hover:bg-blue-600 focus:ring-blue-500",
                    ),
                    base_button(
                        "Save Source",
                        type="submit",
                        form="source-form",
                        on_click=DataSourcesState.set_submit_action("save"),
                        icon="save",
                    ),
                    class_name="flex justify-end gap-3 pt-4 border-t border-gray-200",
                ),
                class_name="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-xl shadow-2xl p-6 w-full max-w-2xl z-50",
            ),
        ),
        open=DataSourcesState.show_source_modal,
        on_open_change=DataSourcesState.close_source_modal,
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
                    "Are you sure you want to delete this data source? This action cannot be undone.",
                    class_name="text-gray-600 my-4",
                ),
                rx.el.div(
                    rx.radix.primitives.dialog.close(
                        base_button(
                            "Cancel",
                            on_click=DataSourcesState.close_delete_dialog,
                            class_name="bg-gray-200 text-gray-800 hover:bg-gray-300 focus:ring-gray-300",
                        ),
                        as_child=True,
                    ),
                    base_button(
                        "Delete",
                        on_click=DataSourcesState.confirm_delete,
                        class_name="bg-red-600 text-white hover:bg-red-700 focus:ring-red-500",
                    ),
                    class_name="flex justify-end gap-3 pt-4 border-t border-gray-200",
                ),
                class_name="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-xl shadow-2xl p-6 w-full max-w-md z-50",
            ),
        ),
        open=DataSourcesState.show_delete_dialog,
        on_open_change=DataSourcesState.close_delete_dialog,
    )


def import_status_badge(status: rx.Var[str]) -> rx.Component:
    """Badge for import job status."""
    base_class = (
        " text-xs font-medium px-2.5 py-1 rounded-full w-fit flex items-center gap-1.5"
    )
    return rx.el.span(
        rx.cond(
            status == "Running",
            rx.el.div(class_name="h-2 w-2 rounded-full bg-blue-500 animate-pulse"),
            None,
        ),
        status,
        class_name=rx.match(
            status,
            ("Running", "bg-blue-100 text-blue-800" + base_class),
            ("Completed", "bg-green-100 text-green-800" + base_class),
            ("Failed", "bg-red-100 text-red-800" + base_class),
            "bg-gray-100 text-gray-800" + base_class,
        ),
    )


def import_dialog() -> rx.Component:
    """Dialog to trigger a data import."""
    return rx.radix.primitives.dialog.root(
        rx.radix.primitives.dialog.portal(
            rx.radix.primitives.dialog.overlay(
                class_name="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
            ),
            rx.radix.primitives.dialog.content(
                rx.radix.primitives.dialog.title(
                    "Import Data", class_name="text-xl font-semibold text-gray-800"
                ),
                rx.el.p(
                    f"Select a Knowledge Database to import data from {DataSourcesState.source_to_import['name']}.",
                    class_name="text-gray-600 my-4",
                ),
                rx.el.div(
                    rx.el.label(
                        "Destination Knowledge DB",
                        class_name="text-sm font-medium text-gray-700 mb-1 block",
                    ),
                    rx.el.select(
                        rx.foreach(
                            DataSourcesState.all_knowledge_dbs,
                            lambda db: rx.el.option(db["name"], value=db["id"]),
                        ),
                        value=DataSourcesState.import_kb_id,
                        on_change=DataSourcesState.set_import_kb_id,
                        class_name="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
                        placeholder="Select a destination...",
                    ),
                    class_name="mb-6",
                ),
                rx.el.div(
                    rx.radix.primitives.dialog.close(
                        base_button(
                            "Cancel",
                            on_click=DataSourcesState.close_import_dialog,
                            class_name="bg-gray-200 text-gray-800 hover:bg-gray-300 focus:ring-gray-300",
                        ),
                        as_child=True,
                    ),
                    base_button(
                        "Start Import",
                        on_click=DataSourcesState.start_import,
                        icon="play",
                        is_loading=DataSourcesState.is_importing,
                        disabled=DataSourcesState.import_kb_id == "",
                    ),
                    class_name="flex justify-end gap-3 pt-4 border-t border-gray-200",
                ),
                class_name="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-xl shadow-2xl p-6 w-full max-w-lg z-50",
            ),
        ),
        open=DataSourcesState.show_import_dialog,
        on_open_change=DataSourcesState.close_import_dialog,
    )


def import_history_section() -> rx.Component:
    return rx.el.div(
        rx.el.h2(
            "Import History", class_name="text-xl font-semibold text-gray-800 mb-4"
        ),
        rx.cond(
            DataSourcesState.import_jobs.length() > 0,
            card(
                rx.el.table(
                    rx.el.thead(
                        rx.el.tr(
                            rx.el.th("Source"),
                            rx.el.th("Destination KB"),
                            rx.el.th("Status"),
                            rx.el.th("Records"),
                            rx.el.th("Timestamp"),
                            class_name="text-left text-xs font-medium text-gray-500 uppercase tracking-wider",
                        )
                    ),
                    rx.el.tbody(
                        rx.foreach(
                            DataSourcesState.sorted_import_jobs,
                            lambda job: rx.el.tr(
                                rx.el.td(
                                    DataSourcesState.source_names[job["source_id"]]
                                ),
                                rx.el.td(DataSourcesState.kb_names[job["kb_id"]]),
                                rx.el.td(import_status_badge(job["status"])),
                                rx.el.td(job["records_imported"]),
                                rx.el.td(job["completed_at"]),
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
                    "No import jobs have been run yet.",
                    class_name="text-center text-gray-500",
                ),
                class_name="py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-200",
            ),
        ),
        class_name="mt-12",
    )


def empty_state() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon("cloud-off", class_name="h-16 w-16 text-gray-400 mx-auto"),
            rx.el.h3(
                "No Data Sources Found",
                class_name="mt-4 text-lg font-semibold text-gray-800",
            ),
            rx.el.p(
                "Get started by creating your first data source.",
                class_name="mt-2 text-sm text-gray-500",
            ),
            base_button(
                "Create New Source",
                icon="message-circle-plus",
                on_click=DataSourcesState.open_create_modal,
                class_name="mt-6",
            ),
            class_name="text-center",
        ),
        class_name="flex items-center justify-center h-full bg-gray-50 rounded-lg border-2 border-dashed border-gray-200 p-12",
    )


def data_sources_page() -> rx.Component:
    return base_layout(
        rx.el.div(
            source_modal(),
            delete_dialog(),
            import_dialog(),
            rx.el.div(
                rx.el.div(
                    rx.el.div(
                        rx.icon("search", class_name="h-5 w-5 text-gray-400"),
                        class_name="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none",
                    ),
                    rx.el.input(
                        placeholder="Search sources...",
                        on_change=DataSourcesState.set_search_query,
                        class_name="w-full max-w-xs pl-10 pr-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
                        default_value=DataSourcesState.search_query,
                    ),
                    class_name="relative",
                ),
                rx.el.div(
                    rx.el.select(
                        rx.foreach(
                            DataSourcesState.filter_type_options,
                            lambda type: rx.el.option(type, value=type),
                        ),
                        value=DataSourcesState.filter_type,
                        on_change=DataSourcesState.set_filter_type,
                        class_name="py-2 pl-3 pr-8 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
                    ),
                    base_button(
                        "Create New Source",
                        icon="message-circle-plus",
                        on_click=DataSourcesState.open_create_modal,
                    ),
                    class_name="flex items-center gap-4",
                ),
                class_name="flex justify-between items-center mb-6",
            ),
            rx.cond(
                DataSourcesState.filtered_sources.length() > 0,
                rx.el.div(
                    rx.foreach(DataSourcesState.filtered_sources, source_card),
                    class_name="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6",
                ),
                empty_state(),
            ),
            import_history_section(),
            class_name="h-full",
        ),
        on_mount=DataSourcesState.load_initial_data,
    )
