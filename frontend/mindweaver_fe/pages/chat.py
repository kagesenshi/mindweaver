import reflex as rx
from mindweaver_fe.components.layout import base_layout
from mindweaver_fe.components.reusables import base_button
from mindweaver_fe.states.chat_state import ChatState


def conversation_sidebar() -> rx.Component:
    """Sidebar to display conversation history."""
    return rx.el.div(
        rx.el.div(
            rx.el.h2("Conversations", class_name="text-lg font-semibold text-gray-800"),
            base_button(
                "New Chat",
                on_click=ChatState.create_new_conversation,
                icon="plus",
                class_name="text-sm bg-transparent text-orange-500 hover:bg-orange-50 focus:ring-orange-500 shadow-none font-medium !px-2 !py-1.5",
            ),
            class_name="flex justify-between items-center p-4 border-b border-gray-200",
        ),
        rx.el.div(
            rx.foreach(
                ChatState.conversation_history,
                lambda conv: rx.el.button(
                    rx.el.div(
                        rx.el.span(conv["title"], class_name="truncate font-medium"),
                        class_name="flex-1 text-left overflow-hidden",
                    ),
                    on_click=lambda: ChatState.select_conversation(conv["id"]),
                    class_name=rx.cond(
                        ChatState.current_conversation_id == conv["id"],
                        "w-full text-left p-3 rounded-lg bg-orange-50 text-orange-600 transition-colors duration-150",
                        "w-full text-left p-3 rounded-lg hover:bg-gray-100 text-gray-700 transition-colors duration-150",
                    ),
                    title=conv["title"],
                ),
            ),
            class_name="flex flex-col gap-1 p-2 overflow-y-auto",
        ),
        class_name="h-full flex flex-col bg-white border-r border-gray-200 w-80",
    )


def chat_header() -> rx.Component:
    """Header for the chat interface with agent selector."""
    return rx.el.div(
        rx.cond(
            ChatState.selected_agent,
            rx.el.div(
                rx.el.div(
                    rx.icon("bot", class_name="h-6 w-6 text-gray-600"),
                    rx.el.h2(
                        ChatState.selected_agent["name"],
                        class_name="text-lg font-semibold text-gray-800 ml-2",
                    ),
                    class_name="flex items-center",
                ),
                rx.el.div(
                    rx.icon("database", class_name="h-4 w-4 text-gray-400"),
                    rx.el.span(
                        f"{ChatState.connected_dbs.length()} DBs connected",
                        class_name="text-xs text-gray-500 ml-1.5",
                    ),
                    class_name="flex items-center bg-gray-100 px-2 py-1 rounded-full",
                ),
                class_name="flex items-center justify-between w-full",
            ),
            rx.el.select(
                rx.foreach(
                    ChatState.all_agents,
                    lambda agent: rx.el.option(agent["name"], value=agent["id"]),
                ),
                placeholder="Select an AI Agent to start...",
                value=ChatState.selected_agent_id,
                on_change=ChatState.set_agent_and_start_chat,
                class_name="w-full max-w-sm px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-orange-500",
            ),
        ),
        class_name="p-4 border-b border-gray-200 flex items-center bg-white",
    )


def message_bubble(message: dict) -> rx.Component:
    """A message bubble component."""
    is_user = message["role"] == "user"
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.icon(rx.cond(is_user, "user", "bot"), class_name="h-5 w-5"),
                class_name=rx.cond(
                    is_user,
                    "p-2 bg-orange-500 text-white rounded-full",
                    "p-2 bg-gray-200 text-gray-700 rounded-full",
                ),
            ),
            rx.el.div(
                rx.el.p(
                    message["content"], class_name="text-gray-800 whitespace-pre-wrap"
                ),
                rx.el.span(
                    message["timestamp"], class_name="text-xs text-gray-400 mt-1"
                ),
                class_name=rx.cond(
                    is_user,
                    "p-3 rounded-lg rounded-bl-none bg-orange-100 text-gray-800",
                    "p-3 rounded-lg rounded-br-none bg-gray-100 text-gray-800",
                ),
            ),
            class_name=rx.cond(
                is_user,
                "flex items-start gap-3 flex-row-reverse",
                "flex items-start gap-3",
            ),
        ),
        class_name=rx.cond(is_user, "flex justify-end", "flex justify-start"),
    )


def chat_area() -> rx.Component:
    """The main area where chat messages are displayed."""
    return rx.el.div(
        rx.cond(
            ChatState.current_conversation_id.is_not_none(),
            rx.el.div(
                rx.foreach(ChatState.current_conversation_messages, message_bubble),
                rx.cond(
                    ChatState.is_streaming,
                    rx.el.div(
                        rx.el.div(
                            rx.icon("bot", class_name="h-5 w-5 text-gray-700"),
                            class_name="p-2 bg-gray-200 rounded-full",
                        ),
                        rx.el.div(
                            rx.el.div(
                                class_name="h-2 w-2 bg-orange-400 rounded-full animate-pulse",
                                style={"animation_delay": "-0.3s"},
                            ),
                            rx.el.div(
                                class_name="h-2 w-2 bg-orange-400 rounded-full animate-pulse",
                                style={"animation_delay": "-0.15s"},
                            ),
                            rx.el.div(
                                class_name="h-2 w-2 bg-orange-400 rounded-full animate-pulse"
                            ),
                            class_name="flex items-center gap-1 p-3 bg-gray-100 rounded-lg",
                        ),
                        class_name="flex items-start gap-3 mt-4",
                    ),
                    None,
                ),
                id="chat-messages",
                class_name="flex-1 p-6 space-y-6 overflow-y-auto",
            ),
            rx.el.div(
                rx.icon("messages-square", class_name="h-16 w-16 text-gray-300"),
                rx.el.h3(
                    "Select an agent and start chatting",
                    class_name="text-lg font-medium text-gray-500 mt-4",
                ),
                class_name="flex flex-col items-center justify-center h-full text-center",
            ),
        ),
        class_name="flex-1 overflow-hidden",
    )


def message_input() -> rx.Component:
    """The input area for typing and sending messages."""
    return rx.el.form(
        rx.el.div(
            rx.el.textarea(
                placeholder="Type your message...",
                name="input_message",
                on_change=ChatState.set_input_message,
                on_key_down=lambda key: rx.cond(
                    key == "Enter", ChatState.handle_send_message({}), rx.noop()
                ),
                class_name="flex-1 p-3 pr-12 border-0 focus:ring-0 resize-none bg-transparent placeholder-gray-500",
                rows=1,
                default_value=ChatState.input_message,
            ),
            rx.el.button(
                rx.icon("send", class_name="h-5 w-5"),
                type="submit",
                disabled=ChatState.input_message.strip() == "",
                class_name="absolute right-3 top-1/2 -translate-y-1/2 p-2 rounded-full text-white bg-orange-500 hover:bg-orange-600 disabled:bg-gray-300 transition-colors",
            ),
            class_name="relative flex items-center border border-gray-300 rounded-xl m-4 bg-white shadow-sm",
        ),
        on_submit=ChatState.handle_send_message,
        reset_on_submit=False,
        width="100%",
    )


def chat_page() -> rx.Component:
    """The Chat page content."""
    return base_layout(
        rx.el.div(
            conversation_sidebar(),
            rx.el.div(
                chat_header(),
                chat_area(),
                message_input(),
                class_name="flex-1 flex flex-col bg-gray-50",
            ),
            class_name="flex h-full w-full",
        ),
        on_mount=ChatState.load_initial_data,
    )