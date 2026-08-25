# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from mindweaver.celery_app import app
from mindweaver.fw.model import get_engine
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from mindweaver.service.project.service import ProjectService
from mindweaver.service.stack.model import Stack
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


@app.task
def sync_project_integrations_task(project_id: int):
    """Trigger integrations sync for a specific project namespace."""
    logger.info(f"Triggering integrations sync for project {project_id}")
    run_async(_sync_project_integrations_task(project_id))


async def _sync_project_integrations_task(project_id: int):
    engine = get_engine()
    async with AsyncSession(engine) as session:

        class MockRequest:
            headers = {}

        svc = ProjectService(MockRequest(), session)
        try:
            model = await svc.get(project_id)
            from mindweaver.service.project.actions import SyncProjectIntegrationsAction

            action = SyncProjectIntegrationsAction(model, svc)
            await action.run()
            logger.info(f"Successfully synced integrations for project {project_id}")
        except Exception as e:
            logger.error(
                f"Error syncing integrations for project {project_id}: {e}"
            )


@app.task
def sync_trusted_certs_secret_task(project_id: int):
    """Trigger synchronization of the trusted-certs secret for a project."""
    logger.info(f"Triggering trusted-certs secret sync for project {project_id}")
    run_async(_sync_trusted_certs_secret_task(project_id))




async def _sync_trusted_certs_secret_task(project_id: int):
    """Synchronize only the trusted-certs secret to the project's Kubernetes cluster."""
    engine = get_engine()
    async with AsyncSession(engine) as session:
        from mindweaver.service.project.model import Project
        from mindweaver.service.k8s_cluster import K8sCluster
        from mindweaver.service.trusted_certs.model import TrustedCert
        import base64

        try:
            project = await session.get(Project, project_id)
            if not project or not project.k8s_cluster_id:
                logger.warning(
                    f"Project {project_id} or cluster not configured, skipping trusted-certs secret sync"
                )
                return

            cluster = await session.get(K8sCluster, project.k8s_cluster_id)
            if not cluster:
                logger.warning(
                    f"Cluster {project.k8s_cluster_id} not found, skipping trusted-certs secret sync"
                )
                return

            namespace = project.k8s_namespace or project.name

            stmt_certs = select(TrustedCert).where(TrustedCert.project_id == project_id)
            res_certs = await session.exec(stmt_certs)
            certs = res_certs.all()

            trusted_certs = [
                {
                    "name": c.name,
                    "certificate": c.certificate,
                    "certificate_b64": base64.b64encode(c.certificate.encode("utf-8")).decode("utf-8")
                }
                for c in certs
            ]

            from mindweaver.service.project.actions import _get_jinja_env, apply_manifest_to_cluster
            env = _get_jinja_env()
            template = env.get_template("03-trusted-certs.yml.j2")
            manifest = template.render(
                name=project.name,
                namespace=namespace,
                trusted_certs=trusted_certs,
            )

            await apply_manifest_to_cluster(cluster, manifest)
            logger.info(f"Successfully synced trusted-certs secret for project {project_id}")
        except Exception as e:
            logger.error(
                f"Error syncing trusted-certs secret for project {project_id}: {e}"
            )

