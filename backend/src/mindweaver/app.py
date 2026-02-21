import fastapi
from .config import settings
from .service.data_source import router as ds_router
from .service.knowledge_db import router as kdb_router
from .service.ontology import router as ontology_router
from .service.ai_agent import router as agent_router
from .service.chat import router as chat_router
from .service.s3_storage import router as s3_router
from .service.ingestion import (
    router as ingestion_router,
    run_router as ingestion_run_router,
)
from .service.project import router as project_router
from .service.auth import router as auth_router, verify_token
from .platform_service.pgsql import router as pgsql_router

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi import Depends
from fastapi.security import HTTPBearer
from .fw.service import Error, ValidationErrorDetail
from .fw.exc import MindWeaverError

app = fastapi.FastAPI(
    title="Mindweaver",
    dependencies=[
        Depends(verify_token),
        Depends(HTTPBearer(auto_error=False)),
    ],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: fastapi.Request, exc: RequestValidationError
):
    # For validation errors, we might have multiple, but the spec says single ValidationErrorDetail.
    # We take the first one as representative if there are multiple.
    errors = exc.errors()
    if not errors:
        detail = "Validation failed"
    else:
        detail = [
            ValidationErrorDetail(
                msg=err.get("msg", "Value error"),
                type=err.get("type", "value_error"),
                loc=[str(l) for l in err.get("loc", [])],
            )
            for err in errors
        ]

    error_resp = Error(status="error", type="validation_error", detail=detail)
    return JSONResponse(status_code=422, content=error_resp.model_dump())


@app.exception_handler(HTTPException)
async def http_exception_handler(request: fastapi.Request, exc: HTTPException):
    # Handle standard HTTP exceptions
    # If exc.detail is a list (like from some of our custom exceptions), inspect the first item
    detail_msg = exc.detail
    if isinstance(detail_msg, list) and len(detail_msg) > 0:
        # Check if it's a list of validation errors
        if all(isinstance(d, dict) and "msg" in d for d in detail_msg):
            detail = [
                ValidationErrorDetail(
                    msg=d.get("msg", ""),
                    type=d.get("type", "value_error"),
                    loc=[str(l) for l in d.get("loc", [])],
                )
                for d in detail_msg
            ]
            error_resp = Error(status="error", type="validation_error", detail=detail)
            return JSONResponse(
                status_code=exc.status_code, content=error_resp.model_dump()
            )
        else:
            detail_msg = str(detail_msg[0])
    elif isinstance(detail_msg, list):
        detail_msg = "An error occurred"

    error_resp = Error(status="error", type="http_error", detail=str(detail_msg))
    return JSONResponse(status_code=exc.status_code, content=error_resp.model_dump())


@app.exception_handler(MindWeaverError)
async def mindweaver_exception_handler(request: fastapi.Request, exc: MindWeaverError):
    # MindWeaverError inherits from HTTPException, but we handle it specifically if needed.
    # Reuse http_exception_handler logic for now as they are very similar.
    return await http_exception_handler(request, exc)


@app.exception_handler(Exception)
async def general_exception_handler(request: fastapi.Request, exc: Exception):
    # Handle any other unexpected exceptions
    error_resp = Error(status="error", type="server_error", detail=str(exc))
    return JSONResponse(status_code=500, content=error_resp.model_dump())


@app.exception_handler(404)
async def not_found_handler(request: fastapi.Request, exc: Exception):
    # This handles both non-existent routes and raised 404s.
    # If it's a raised HTTPException, use its detail.
    detail = "Not Found"
    if isinstance(exc, HTTPException):
        detail = exc.detail
        if isinstance(detail, list) and len(detail) > 0:
            if isinstance(detail[0], dict) and "msg" in detail[0]:
                detail = detail[0]["msg"]
            else:
                detail = str(detail[0])

    error_resp = Error(status="error", type="http_error", detail=str(detail))
    return JSONResponse(status_code=404, content=error_resp.model_dump())


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/feature-flags")
async def feature_flags():
    return {
        "experimental_data_source": settings.experimental_data_source,
        "experimental_knowledge_db": settings.experimental_knowledge_db,
        "experimental_s3_storage": settings.experimental_s3_storage,
        "experimental_ingestion": settings.experimental_ingestion,
    }


app.include_router(project_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(pgsql_router, prefix="/api/v1")
app.include_router(s3_router, prefix="/api/v1")

if settings.experimental_data_source:
    app.include_router(ds_router, prefix="/api/v1")
if settings.experimental_knowledge_db:
    app.include_router(kdb_router, prefix="/api/v1")
    app.include_router(ontology_router, prefix="/api/v1")
    app.include_router(agent_router, prefix="/api/v1")
    app.include_router(chat_router, prefix="/api/v1")

if settings.experimental_ingestion:
    app.include_router(ingestion_router, prefix="/api/v1")
    app.include_router(ingestion_run_router, prefix="/api/v1")
