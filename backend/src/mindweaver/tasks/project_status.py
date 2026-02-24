# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from mindweaver.celery_app import app
from mindweaver.fw.model import get_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from mindweaver.service.project import ProjectService
from mindweaver.config import logger
from .base import run_async


@app.task
def poll_all_projects():
    """Poll all projects for cluster status"""
    logger.info("Starting polling of all projects")
    run_async(_poll_all_projects())


async def _poll_all_projects():
    engine = get_engine()
    async with AsyncSession(engine) as session:

        class MockRequest:
            headers = {}

        svc = ProjectService(MockRequest(), session)
        projects = await svc.all()

        for project in projects:
            poll_project_status.delay(project.id)


@app.task
def poll_project_status(project_id: int):
    """Poll status for a specific project instance."""
    logger.info(f"Polling status for project {project_id}")
    run_async(_poll_project_status(project_id))


async def _poll_project_status(project_id: int):
    engine = get_engine()
    async with AsyncSession(engine) as session:

        class MockRequest:
            headers = {}

        svc = ProjectService(MockRequest(), session)
        try:
            model = await svc.get(project_id)
            await svc.poll_status(model)
            await session.commit()
            logger.info(f"Successfully polled project {project_id}")
        except Exception as e:
            logger.error(f"Error polling project {project_id}: {e}")


@app.task
def install_argocd_task(project_id: int):
    """Trigger ArgoCD installation for a project."""
    logger.info(f"Triggering ArgoCD installation for project {project_id}")
    run_async(_install_argocd_task(project_id))


async def _install_argocd_task(project_id: int):
    engine = get_engine()
    async with AsyncSession(engine) as session:

        class MockRequest:
            headers = {}

        svc = ProjectService(MockRequest(), session)
        try:
            model = await svc.get(project_id)
            from mindweaver.service.project.actions import InstallArgoCDAction

            action = InstallArgoCDAction(model, svc)
            await action.run()
            await svc.poll_status(model)
            await session.commit()
            logger.info(f"Successfully installed ArgoCD for project {project_id}")
        except Exception as e:
            logger.error(f"Error installing ArgoCD for project {project_id}: {e}")
