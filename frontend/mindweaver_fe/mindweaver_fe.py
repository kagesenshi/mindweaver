import reflex as rx
from mindweaver_fe.pages.knowledge_db import knowledge_db_page
from mindweaver_fe.pages.ai_agents import ai_agents_page
from mindweaver_fe.pages.chat import chat_page
from mindweaver_fe.pages.data_sources import data_sources_page
from mindweaver_fe.pages.lakehouse_storage import lakehouse_storage_page
from mindweaver_fe.pages.ingestion import ingestion_page
from mindweaver_fe.pages.projects import projects_page

# from mindweaver_fe.pages.graph import graph_page

import logging

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s"
)

app = rx.App(
    theme=rx.theme(appearance="light"),
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(rel="preconnect", href="https://fonts.gstatic.com", cross_origin=""),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Raleway:wght@400;500;600;700&display=swap",
            rel="stylesheet",
        ),
    ],
)
app.add_page(knowledge_db_page, route="/")
app.add_page(ai_agents_page, route="/agents")
app.add_page(chat_page, route="/chat")
app.add_page(data_sources_page, route="/sources")
app.add_page(lakehouse_storage_page, route="/lakehouse")
app.add_page(ingestion_page, route="/ingestion")
app.add_page(projects_page, route="/projects")

# app.add_page(graph_page, route="/graph")
