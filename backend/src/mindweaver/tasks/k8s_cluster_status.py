# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from mindweaver.celery_app import app
from mindweaver.fw.model import get_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from mindweaver.service.k8s_cluster import K8sClusterService
from mindweaver.config import logger
from .base import run_async


@app.task
def poll_all_k8s_clusters():
    """Poll all clusters for status"""
    logger.info("Starting polling of all k8s clusters")
    run_async(_poll_all_k8s_clusters())


async def _poll_all_k8s_clusters():
    engine = get_engine()
    async with AsyncSession(engine) as session:

        class MockRequest:
            headers = {}

        svc = K8sClusterService(MockRequest(), session)
        clusters = await svc.all()

        for cluster in clusters:
            poll_k8s_cluster_status.delay(cluster.id)


@app.task
def poll_k8s_cluster_status(k8s_cluster_id: int):
    """Poll status for a specific cluster instance."""
    logger.info(f"Polling status for k8s cluster {k8s_cluster_id}")
    run_async(_poll_k8s_cluster_status(k8s_cluster_id))


async def _poll_k8s_cluster_status(k8s_cluster_id: int):
    engine = get_engine()
    async with AsyncSession(engine) as session:

        class MockRequest:
            headers = {}

        svc = K8sClusterService(MockRequest(), session)
        try:
            model = await svc.get(k8s_cluster_id)
            await svc.poll_status(model)
            await session.commit()
            logger.info(f"Successfully polled cluster {k8s_cluster_id}")
        except Exception as e:
            logger.error(f"Error polling cluster {k8s_cluster_id}: {e}")


@app.task
def install_argocd_task(k8s_cluster_id: int):
    """Trigger ArgoCD installation for a cluster."""
    logger.info(f"Triggering ArgoCD installation for cluster {k8s_cluster_id}")
    run_async(_install_argocd_task(k8s_cluster_id))


async def _install_argocd_task(k8s_cluster_id: int):
    engine = get_engine()
    async with AsyncSession(engine) as session:

        class MockRequest:
            headers = {}

        svc = K8sClusterService(MockRequest(), session)
        try:
            model = await svc.get(k8s_cluster_id)
            from mindweaver.service.k8s_cluster.actions import InstallArgoCDAction

            action = InstallArgoCDAction(model, svc)
            await action.run()
            await svc.poll_status(model)
            await session.commit()
            logger.info(f"Successfully installed ArgoCD for cluster {k8s_cluster_id}")
        except Exception as e:
            logger.error(f"Error installing ArgoCD for cluster {k8s_cluster_id}: {e}")


@app.task
def install_cert_manager_task(k8s_cluster_id: int):
    """Trigger Cert Manager installation for a cluster."""
    logger.info(f"Triggering Cert Manager installation for cluster {k8s_cluster_id}")
    run_async(_install_cert_manager_task(k8s_cluster_id))


async def _install_cert_manager_task(k8s_cluster_id: int):
    engine = get_engine()
    async with AsyncSession(engine) as session:

        class MockRequest:
            headers = {}

        svc = K8sClusterService(MockRequest(), session)
        try:
            model = await svc.get(k8s_cluster_id)
            from mindweaver.service.k8s_cluster.actions import InstallCertManagerAction

            action = InstallCertManagerAction(model, svc)
            await action.run()
            await svc.poll_status(model)
            await session.commit()
            logger.info(
                f"Successfully installed Cert Manager for cluster {k8s_cluster_id}"
            )
        except Exception as e:
            logger.error(
                f"Error installing Cert Manager for cluster {k8s_cluster_id}: {e}"
            )


@app.task
def install_cnpg_operator_task(k8s_cluster_id: int):
    """Trigger CNPG Operator installation for a cluster."""
    logger.info(f"Triggering CNPG Operator installation for cluster {k8s_cluster_id}")
    run_async(_install_cnpg_operator_task(k8s_cluster_id))


async def _install_cnpg_operator_task(k8s_cluster_id: int):
    engine = get_engine()
    async with AsyncSession(engine) as session:

        class MockRequest:
            headers = {}

        svc = K8sClusterService(MockRequest(), session)
        try:
            model = await svc.get(k8s_cluster_id)
            from mindweaver.service.k8s_cluster.actions import InstallCNPGAction

            action = InstallCNPGAction(model, svc)
            await action.run()
            await svc.poll_status(model)
            await session.commit()
            logger.info(
                f"Successfully installed CNPG Operator for cluster {k8s_cluster_id}"
            )
        except Exception as e:
            logger.error(
                f"Error installing CNPG Operator for cluster {k8s_cluster_id}: {e}"
            )


@app.task
def install_self_signed_issuer_task(k8s_cluster_id: int):
    """Trigger Self-signed ClusterIssuer installation for a cluster."""
    logger.info(
        f"Triggering Self-signed ClusterIssuer installation for cluster {k8s_cluster_id}"
    )
    run_async(_install_self_signed_issuer_task(k8s_cluster_id))


async def _install_self_signed_issuer_task(k8s_cluster_id: int):
    engine = get_engine()
    async with AsyncSession(engine) as session:

        class MockRequest:
            headers = {}

        svc = K8sClusterService(MockRequest(), session)
        try:
            model = await svc.get(k8s_cluster_id)
            from mindweaver.service.k8s_cluster.actions import (
                InstallSelfSignedIssuerAction,
            )

            action = InstallSelfSignedIssuerAction(model, svc)
            await action.run()
            await svc.poll_status(model)
            await session.commit()
            logger.info(
                f"Successfully installed Self-signed ClusterIssuer for cluster {k8s_cluster_id}"
            )
        except Exception as e:
            logger.error(
                f"Error installing Self-signed ClusterIssuer for cluster {k8s_cluster_id}: {e}"
            )
