import reflex as rx
from mindweaver_fe.components.layout import base_layout
from mindweaver_fe.components.reusables import card, base_button
from mindweaver_fe.components.loading_spinner import loading_spinner
from mindweaver_fe.states.ai_agents_state import AIAgentsState, AIAgent


def status_badge(status: rx.Var[str]) -> rx.Component:
    """A badge component to display the agent status."""
    base_class = (
        " text-xs font-medium px-2.5 py-1 rounded-full w-fit flex items-center gap-1.5"
    )
    return rx.el.span(
        rx.el.div(
            class_name=rx.cond(
                status == "Active",
                "h-2 w-2 rounded-full bg-green-500",
                "h-2 w-2 rounded-full bg-gray-400",
            )
        ),
        status,
        class_name=rx.match(
            status,
            ("Active", "bg-green-100 text-green-800" + base_class),
            ("Inactive", "bg-gray-100 text-gray-800" + base_class),
            "bg-gray-100 text-gray-800" + base_class,
        ),
    )


def agent_card(agent: AIAgent) -> rx.Component:
    """A card component for a single AI agent."""
    return card(
        rx.el.div(
            rx.el.div(
                rx.el.h3(agent["name"], class_name="text-lg font-bold text-gray-900"),
                status_badge(agent["status"]),
                class_name="flex justify-between items-start mb-2",
            ),
            rx.el.p(
                agent["system_prompt"],
                class_name="text-sm text-gray-600 mb-4 h-10 overflow-hidden line-clamp-2",
            ),
            rx.el.div(
                rx.el.div(
                    rx.icon("cpu", class_name="h-4 w-4 text-gray-400"),
                    rx.el.span(agent["model"], class_name="text-sm text-gray-500 ml-2"),
                    class_name="flex items-center",
                ),
                rx.el.div(
                    rx.icon("database", class_name="h-4 w-4 text-gray-400"),
                    rx.el.span(
                        f"{agent['knowledge_db_ids'].length()} DBs",
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
                on_click=lambda: AIAgentsState.open_edit_modal(agent),
                icon="pencil",
                class_name="bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 shadow-sm focus:ring-gray-300",
            ),
            base_button(
                "Delete",
                on_click=lambda: AIAgentsState.open_delete_dialog(agent),
                icon="trash-2",
                class_name="bg-red-500 text-white hover:bg-red-600 shadow-sm focus:ring-red-500",
            ),
            class_name="flex gap-2 mt-4",
        ),
    )


def agent_modal() -> rx.Component:
    """Modal for creating and editing agents."""
    return rx.radix.primitives.dialog.root(
        rx.radix.primitives.dialog.portal(
            rx.radix.primitives.dialog.overlay(
                class_name="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
            ),
            rx.radix.primitives.dialog.content(
                rx.radix.primitives.dialog.title(
                    rx.cond(
                        AIAgentsState.is_editing, "Edit AI Agent", "Create New AI Agent"
                    ),
                    class_name="text-xl font-semibold text-gray-800 mb-4",
                ),
                rx.el.form(
                    # General error message display
                    rx.cond(
                        AIAgentsState.error_message != "",
                        rx.el.div(
                            rx.icon("circle-alert", class_name="h-5 w-5 text-red-500"),
                            rx.el.span(
                                AIAgentsState.error_message,
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
                            placeholder="e.g., Customer Support Bot",
                            name="name",
                            default_value=AIAgentsState.form_data["name"],
                            class_name=rx.cond(
                                AIAgentsState.form_errors.get("name") != None,
                                "w-full px-3 py-2 border border-red-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-red-500",
                                "w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
                            ),
                        ),
                        rx.cond(
                            AIAgentsState.form_errors.get("name") != None,
                            rx.el.p(
                                AIAgentsState.form_errors.get("name"),
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
                            placeholder="e.g., Customer Support Assistant",
                            name="title",
                            default_value=AIAgentsState.form_data["title"],
                            class_name=rx.cond(
                                AIAgentsState.form_errors.get("title") != None,
                                "w-full px-3 py-2 border border-red-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-red-500",
                                "w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
                            ),
                        ),
                        rx.cond(
                            AIAgentsState.form_errors.get("title") != None,
                            rx.el.p(
                                AIAgentsState.form_errors.get("title"),
                                class_name="text-sm text-red-600 mt-1",
                            ),
                        ),
                        class_name="mb-4",
                    ),
                    rx.el.div(
                        rx.el.label(
                            "System Prompt",
                            class_name="text-sm font-medium text-gray-700 mb-1 block",
                        ),
                        rx.el.textarea(
                            placeholder="You are a helpful assistant...",
                            name="system_prompt",
                            default_value=AIAgentsState.form_data["system_prompt"],
                            class_name="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
                            rows=4,
                        ),
                        class_name="mb-4",
                    ),
                    rx.el.div(
                        rx.el.div(
                            rx.el.label(
                                "Model",
                                class_name="text-sm font-medium text-gray-700 mb-1 block",
                            ),
                            rx.el.select(
                                rx.foreach(
                                    AIAgentsState.available_models,
                                    lambda model: rx.el.option(model, value=model),
                                ),
                                name="model",
                                default_value=AIAgentsState.form_data["model"],
                                on_change=lambda value: AIAgentsState.set_form_data_field(
                                    "model", value
                                ),
                                class_name="w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
                            ),
                            class_name="flex-1",
                        ),
                        rx.el.div(
                            rx.el.label(
                                f"Temperature: {AIAgentsState.form_data['temperature']}",
                                class_name="text-sm font-medium text-gray-700 mb-1 block",
                            ),
                            rx.el.input(
                                type="range",
                                min=0,
                                max=1,
                                step=0.1,
                                name="temperature",
                                default_value=AIAgentsState.form_data["temperature"].to(
                                    str
                                ),
                                on_change=lambda val: AIAgentsState.set_form_data_field(
                                    "temperature", val
                                ).throttle(50),
                                key=f"temp-slider-{rx.cond(AIAgentsState.is_editing, AIAgentsState.agent_to_edit['id'], 'new')}",
                                class_name="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-orange-500",
                            ),
                            class_name="flex-1",
                        ),
                        class_name="flex gap-4 mb-4",
                    ),
                    rx.el.div(
                        rx.el.label(
                            "Link Knowledge Databases",
                            class_name="text-sm font-medium text-gray-700 mb-2 block",
                        ),
                        rx.el.div(
                            rx.foreach(
                                AIAgentsState.all_knowledge_dbs,
                                lambda db: rx.el.label(
                                    rx.el.input(
                                        type="checkbox",
                                        name="knowledge_db_ids",
                                        checked=AIAgentsState.form_data[
                                            "knowledge_db_ids"
                                        ]
                                        .to(list[str])
                                        .contains(db["id"]),
                                        on_change=lambda checked: AIAgentsState.toggle_db_selection(
                                            db["id"], checked
                                        ),
                                        class_name="h-4 w-4 rounded border-gray-300 text-orange-600 focus:ring-orange-500",
                                        default_value=db["id"],
                                    ),
                                    rx.el.span(
                                        db["name"], class_name="ml-2 text-gray-700"
                                    ),
                                    class_name="flex items-center p-2 rounded-lg hover:bg-gray-50",
                                ),
                            ),
                            class_name="grid grid-cols-2 gap-2 p-3 border border-gray-200 rounded-lg max-h-40 overflow-y-auto",
                        ),
                        class_name="mb-6",
                    ),
                    on_submit=AIAgentsState.handle_submit,
                    id="agent-form",
                ),
                rx.el.div(
                    rx.radix.primitives.dialog.close(
                        base_button(
                            "Cancel",
                            on_click=AIAgentsState.close_agent_modal,
                            class_name="bg-gray-200 text-gray-800 hover:bg-gray-300 focus:ring-gray-300",
                        ),
                        as_child=True,
                    ),
                    base_button(
                        "Save Agent", type="submit", form="agent-form", icon="save"
                    ),
                    class_name="flex justify-end gap-3 pt-4 border-t border-gray-200",
                ),
                class_name="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-xl shadow-2xl p-6 w-full max-w-2xl z-50",
            ),
        ),
        open=AIAgentsState.show_agent_modal,
        on_open_change=AIAgentsState.close_agent_modal,
    )


def delete_dialog() -> rx.Component:
    """Confirmation dialog for deleting an agent."""
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
                    "Are you sure you want to delete this AI agent? This action cannot be undone.",
                    class_name="text-gray-600 my-4",
                ),
                rx.el.div(
                    rx.radix.primitives.dialog.close(
                        base_button(
                            "Cancel",
                            on_click=AIAgentsState.close_delete_dialog,
                            class_name="bg-gray-200 text-gray-800 hover:bg-gray-300 focus:ring-gray-300",
                        ),
                        as_child=True,
                    ),
                    base_button(
                        "Delete",
                        on_click=AIAgentsState.confirm_delete,
                        class_name="bg-red-600 text-white hover:bg-red-700 focus:ring-red-500",
                    ),
                    class_name="flex justify-end gap-3 pt-4 border-t border-gray-200",
                ),
                class_name="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-xl shadow-2xl p-6 w-full max-w-md z-50",
            ),
        ),
        open=AIAgentsState.show_delete_dialog,
        on_open_change=AIAgentsState.close_delete_dialog,
    )


def empty_state() -> rx.Component:
    """Display when no agents are found."""
    return rx.el.div(
        rx.el.div(
            rx.icon("bot", class_name="h-16 w-16 text-gray-400 mx-auto"),
            rx.el.h3(
                "No AI Agents Found",
                class_name="mt-4 text-lg font-semibold text-gray-800",
            ),
            rx.el.p(
                "Get started by creating your first AI agent.",
                class_name="mt-2 text-sm text-gray-500",
            ),
            base_button(
                "Create New Agent",
                icon="message-circle-plus",
                on_click=AIAgentsState.open_create_modal,
                class_name="mt-6",
            ),
            class_name="text-center",
        ),
        class_name="flex items-center justify-center h-full bg-gray-50 rounded-lg border-2 border-dashed border-gray-200 p-12",
    )


def ai_agents_page() -> rx.Component:
    """The AI Agents page content."""
    return base_layout(
        rx.el.div(
            agent_modal(),
            delete_dialog(),
            rx.cond(
                AIAgentsState.is_loading,
                loading_spinner(),
                rx.el.div(
                    rx.el.div(
                        rx.el.div(
                            rx.el.div(
                                rx.icon("search", class_name="h-5 w-5 text-gray-400"),
                                class_name="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none",
                            ),
                            rx.el.input(
                                placeholder="Search agents...",
                                on_change=AIAgentsState.set_search_query,
                                class_name="w-full max-w-xs pl-10 pr-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
                                default_value=AIAgentsState.search_query,
                            ),
                            class_name="relative",
                        ),
                        rx.el.div(
                            rx.el.select(
                                rx.foreach(
                                    AIAgentsState.status_options,
                                    lambda status: rx.el.option(status, value=status),
                                ),
                                value=AIAgentsState.filter_status,
                                on_change=AIAgentsState.set_filter_status,
                                class_name="py-2 pl-3 pr-8 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
                            ),
                            base_button(
                                "Create New Agent",
                                icon="message-circle-plus",
                                on_click=AIAgentsState.open_create_modal,
                            ),
                            class_name="flex items-center gap-4",
                        ),
                        class_name="flex justify-between items-center mb-6",
                    ),
                    rx.cond(
                        AIAgentsState.filtered_agents.length() > 0,
                        rx.el.div(
                            rx.foreach(AIAgentsState.filtered_agents, agent_card),
                            class_name="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6",
                        ),
                        empty_state(),
                    ),
                    class_name="h-full",
                ),
            ),
        ),
        on_mount=AIAgentsState.load_agents,
    )
