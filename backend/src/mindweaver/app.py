import fastapi
from .service.data_source import router as ds_router
from .service.knowledge_db import router as kdb_router
from .service.ai_agent import router as agent_router
from .service.chat import router as chat_router
from .service.lakehouse_storage import router as lakehouse_router
from .service.ingestion import (
    router as ingestion_router,
    run_router as ingestion_run_router,
)
from .service.project import router as project_router

app = fastapi.FastAPI(title="Mindweaver")
app.include_router(project_router, prefix="/api/v1")
app.include_router(ds_router, prefix="/api/v1")
app.include_router(kdb_router, prefix="/api/v1")
app.include_router(agent_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(lakehouse_router, prefix="/api/v1")
app.include_router(ingestion_router, prefix="/api/v1")
app.include_router(ingestion_run_router, prefix="/api/v1")
