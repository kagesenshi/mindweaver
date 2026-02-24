# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import asyncio
import logging
import tempfile
import os

from sqlmodel import select
from mindweaver.fw.action import BaseAction
from .service import ProjectService
from .model import Project, ProjectStatus, K8sClusterType

logger = logging.getLogger(__name__)


@ProjectService.register_action("install_argocd")
class InstallArgoCDAction(BaseAction):

    async def available(self) -> bool:
        # Only available if not already installed
        stmt = select(ProjectStatus).where(ProjectStatus.project_id == self.model.id)
        result = await self.session.exec(stmt)
        status = result.one_or_none()
        return not (status and status.argocd_installed)

    async def __call__(self, **kwargs):
        from mindweaver.tasks.project_status import install_argocd_task

        # Set status to installed immediately so UI reflects it
        stmt = select(ProjectStatus).where(ProjectStatus.project_id == self.model.id)
        result = await self.session.exec(stmt)
        status_model = result.one_or_none()
        if not status_model:
            status_model = ProjectStatus(project_id=self.model.id)
            self.session.add(status_model)
        status_model.argocd_installed = True
        await self.session.flush()

        install_argocd_task.delay(self.model.id)
        return {
            "status": "success",
            "message": "ArgoCD installation triggered and status being refreshed.",
        }

    async def run(self):
        """Install ArgoCD to the cluster using Helm chart"""
        logger.info(f"Installing ArgoCD for project {self.model.name}")

        repo_url = "https://argoproj.github.io/argo-helm"
        release_name = "argocd"
        namespace = "argocd"
        chart_name = "argo/argo-cd"

        kubeconfig_path = None
        temp_kf = None

        try:
            if self.model.k8s_cluster_type == K8sClusterType.REMOTE:
                if not self.model.k8s_cluster_kubeconfig:
                    raise ValueError(f"Project {self.model.name} has no kubeconfig")
                temp_kf = tempfile.NamedTemporaryFile(mode="w", delete=False)
                temp_kf.write(self.model.k8s_cluster_kubeconfig)
                temp_kf.flush()
                temp_kf.close()
                kubeconfig_path = temp_kf.name

            async def run_helm(*args):
                cmd = ["helm"]
                if kubeconfig_path:
                    cmd.extend(["--kubeconfig", kubeconfig_path])
                cmd.extend(args)
                logger.debug(f"Running Helm command: {' '.join(cmd)}")
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await proc.communicate()
                if proc.returncode != 0:
                    raise RuntimeError(f"Helm command failed: {stderr.decode()}")
                return stdout.decode()

            # Ensure repo is added
            await run_helm("repo", "add", "argo", repo_url)
            await run_helm("repo", "update")

            # Install ArgoCD
            await run_helm(
                "upgrade",
                "--install",
                release_name,
                chart_name,
                "--namespace",
                namespace,
                "--create-namespace",
                "--wait",
            )

            logger.info(f"ArgoCD installed successfully for project {self.model.name}")

        finally:
            if temp_kf:
                try:
                    os.unlink(temp_kf.name)
                except Exception:
                    pass
