import fastapi
from .config import settings
from .service.data_source import router as ds_router
from .service.knowledge_db import router as kdb_router
from .service.ontology import router as ontology_router
from .service.ai_agent import router as agent_router
from .service.chat import router as chat_router
from .service.lakehouse_storage import router as lakehouse_router
from .service.ingestion import (
    router as ingestion_router,
    run_router as ingestion_run_router,
)
from .service.project import router as project_router

app = fastapi.FastAPI(title="Mindweaver")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/feature-flags")
async def feature_flags():
    return {
        "experimental_ai_agent": settings.experimental_ai_agent,
        "experimental_data_source": settings.experimental_data_source,
        "experimental_knowledge_db": settings.experimental_knowledge_db,
        "experimental_lakehouse_storage": settings.experimental_lakehouse_storage,
        "experimental_ingestion": settings.experimental_ingestion,
        "experimental_chat": settings.experimental_chat,
        "experimental_ontology": settings.experimental_ontology,
    }


app.include_router(project_router, prefix="/api/v1")

if settings.experimental_data_source:
    app.include_router(ds_router, prefix="/api/v1")
if settings.experimental_knowledge_db:
    app.include_router(kdb_router, prefix="/api/v1")
if settings.experimental_ontology:
    app.include_router(ontology_router, prefix="/api/v1")
if settings.experimental_ai_agent:
    app.include_router(agent_router, prefix="/api/v1")
if settings.experimental_chat:
    app.include_router(chat_router, prefix="/api/v1")
if settings.experimental_lakehouse_storage:
    app.include_router(lakehouse_router, prefix="/api/v1")
if settings.experimental_ingestion:
    app.include_router(ingestion_router, prefix="/api/v1")
    app.include_router(ingestion_run_router, prefix="/api/v1")
