# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from mindweaver.celery_app import app
from mindweaver.fw.model import get_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from mindweaver.service.project.service import ProjectService
from mindweaver.config import logger
from .base import run_async


@app.task
def install_dex_project_task(project_id: int):
    """Trigger Dex installation for a specific project namespace."""
    logger.info(f"Triggering Dex installation for project {project_id}")
    run_async(_install_dex_project_task(project_id))


async def _install_dex_project_task(project_id: int):
    engine = get_engine()
    async with AsyncSession(engine) as session:

        class MockRequest:
            headers = {}

        svc = ProjectService(MockRequest(), session)
        try:
            model = await svc.get(project_id)
            from mindweaver.service.project.actions import InstallDexAction

            action = InstallDexAction(model, svc)
            await action.run()
            # No dynamic state model database update needed as health state is dynamic
            logger.info(f"Successfully installed Dex for project {project_id}")
        except Exception as e:
            logger.error(
                f"Error installing Dex for project {project_id}: {e}"
            )
