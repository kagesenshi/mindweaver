# SPDX-FileCopyrightText: Copyright © 2025 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import fastapi
from pathlib import Path
from .config import settings, logger

from .service.s3_storage import router as s3_router
from .service.ldap_config import router as ldap_config_router
from .service.project import router as project_router
from .service.k8s_cluster import router as k8s_cluster_router
from .service.project_user import router as project_user_router
from .datasource_service import (
    db_router,
)
from .fw.auth import (
    router as auth_router,
    user_router,
    verify_token,
    User,
    get_password_hash,
)
from .platform_service.pgsql import router as pgsql_router
from .platform_service.hive_metastore import router as hms_router
from .platform_service.trino import router as trino_router
from .platform_service.superset import router as superset_router
from .platform_service.airflow import router as airflow_router
from .platform_service.kafka import router as kafka_router
from .platform_service.nifi import router as nifi_router
from .service.name_tracker import router as name_tracker_router
from .service.ssh_key import router as ssh_key_router
from .service.git_repo import router as git_repo_router
from .service.container_registry import router as container_registry_router
from .service.stack.service import StackService


from .fw.model import get_engine, get_session
from sqlmodel import select

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi import Depends
from fastapi.security import HTTPBearer
from .fw.service import Error, ValidationErrorDetail
from .fw.exc import MindWeaverError

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: fastapi.FastAPI):
    from mindweaver.crypto import _get_fernet_instance
    _get_fernet_instance()

    import asyncio
    from mindweaver.tasks.name_tracker import scan_and_clean_names
    asyncio.create_task(scan_and_clean_names())

    if settings.default_admin_username and settings.default_admin_password:
        async for session in get_session(get_engine()):
            statement = select(User).where(User.name == settings.default_admin_username)
            result = await session.exec(statement)
            user = result.first()
            if not user:
                user = User(
                    name=settings.default_admin_username,
                    title="Administrator",
                    email=f"{settings.default_admin_username}@local",
                    password=get_password_hash(settings.default_admin_password),
                    display_name="Administrator",
                    is_superadmin=True,
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)
                logger.info(f"Created default admin user: {user.name}")
            break
    yield


app = fastapi.FastAPI(
    title="Mindweaver",
    lifespan=lifespan,
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
    if exc.status_code >= 500:
        logger.exception("An unexpected server error occurred:")
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
    logger.exception("An unexpected error occurred:")
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
        "oidc_enabled": settings.oidc_issuer is not None,
        "enable_superset_oidc": settings.enable_superset_oidc,
        "enable_airflow_oidc": settings.enable_airflow_oidc,
        "enable_dex": settings.enable_dex,
    }


@app.get("/api/v1/_brand")
async def get_brand():
    """
    Get brand name and logo SVG content.
    """
    assets_dir = Path(__file__).parent / "resources" / "assets"
    logo_filename = settings.brand_logo or "logo.svg"
    logo_path = assets_dir / logo_filename

    logo_content = ""
    try:
        if logo_path.exists():
            logo_content = logo_path.read_text(encoding="utf-8")
        else:
            fallback_path = assets_dir / "logo.svg"
            if fallback_path.exists():
                logo_content = fallback_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.error(f"Error reading brand logo: {e}")

    return {
        "name": settings.brand_name,
        "logo": logo_content,
        "bgcolor": settings.brand_bgcolor,
    }





app.include_router(project_router, prefix="/api/v1")
app.include_router(k8s_cluster_router, prefix="/api/v1")
app.include_router(project_user_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(user_router, prefix="/api/v1")
app.include_router(pgsql_router, prefix="/api/v1")
app.include_router(hms_router, prefix="/api/v1")
app.include_router(trino_router, prefix="/api/v1")
app.include_router(superset_router, prefix="/api/v1")
app.include_router(airflow_router, prefix="/api/v1")
app.include_router(kafka_router, prefix="/api/v1")
app.include_router(nifi_router, prefix="/api/v1")
app.include_router(s3_router, prefix="/api/v1")
app.include_router(ldap_config_router, prefix="/api/v1")
app.include_router(name_tracker_router, prefix="/api/v1")
app.include_router(ssh_key_router, prefix="/api/v1")
app.include_router(git_repo_router, prefix="/api/v1")
app.include_router(container_registry_router, prefix="/api/v1")
app.include_router(StackService.router(), prefix="/api/v1")


app.include_router(db_router, prefix="/api/v1/database-sources")
