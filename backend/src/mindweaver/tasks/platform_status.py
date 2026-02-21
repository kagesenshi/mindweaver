from mindweaver.celery_app import app
from mindweaver.fw.model import get_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from mindweaver.platform_service.base import PlatformService
from mindweaver.platform_service.pgsql import PgSqlPlatformService
from mindweaver.config import logger
from typing import Type
from .base import run_async


@app.task
def poll_all_platforms():
    """Discovers all platform services and triggers polling tasks."""
    logger.info("Starting polling of all platforms")

    # We need to discover all subclasses of PlatformService
    # and for each, find active platforms.

    services = [PgSqlPlatformService]

    for svc_cls in services:
        run_async(_trigger_service_polling(svc_cls))


async def _trigger_service_polling(svc_cls: Type[PlatformService]):
    engine = get_engine()
    async with AsyncSession(engine) as session:
        # Mock request since some service methods might expect it
        # In a worker, we don't have a real request.
        class MockRequest:
            headers = {}

        svc = svc_cls(MockRequest(), session)
        platforms = await svc.list_active_platforms()

        for platform in platforms:
            poll_platform_status.delay(svc_cls.__name__, platform.id)


@app.task
def poll_platform_status(service_class_name: str, platform_id: int):
    """Poll status for a specific platform instance."""
    logger.info(f"Polling status for {service_class_name} instance {platform_id}")
    run_async(_poll_platform_status(service_class_name, platform_id))


async def _poll_platform_status(service_class_name: str, platform_id: int):
    # Dynamically find the service class

    mapping = {"PgSqlPlatformService": PgSqlPlatformService}

    svc_cls = mapping.get(service_class_name)
    if not svc_cls:
        logger.error(f"Service class {service_class_name} not found")
        return

    engine = get_engine()
    async with AsyncSession(engine) as session:

        class MockRequest:
            headers = {}

        svc = svc_cls(MockRequest(), session)
        try:
            model = await svc.get(platform_id)
            await svc.poll_status(model)
            await session.commit()
            logger.info(
                f"Successfully polled {service_class_name} instance {platform_id}"
            )
        except Exception as e:
            logger.error(
                f"Error polling {service_class_name} instance {platform_id}: {e}"
            )
