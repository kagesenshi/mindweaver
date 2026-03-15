# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import asyncio
import logging
import tempfile
import os

from sqlmodel import select
from mindweaver.fw.action import BaseAction
from .service import K8sClusterService
from .model import K8sCluster, K8sClusterStatus, K8sClusterType

logger = logging.getLogger(__name__)


@K8sClusterService.register_action("install_argocd")
class InstallArgoCDAction(BaseAction):

    async def available(self) -> bool:
        # Only available if not already installed
        stmt = select(K8sClusterStatus).where(
            K8sClusterStatus.k8s_cluster_id == self.model.id
        )
        result = await self.session.exec(stmt)
        status = result.one_or_none()
        return not (status and status.argocd_installed)

    async def __call__(self, **kwargs):
        from mindweaver.tasks.k8s_cluster_status import install_argocd_task

        # Set status to installed immediately so UI reflects it
        stmt = select(K8sClusterStatus).where(
            K8sClusterStatus.k8s_cluster_id == self.model.id
        )
        result = await self.session.exec(stmt)
        status_model = result.one_or_none()
        if not status_model:
            status_model = K8sClusterStatus(k8s_cluster_id=self.model.id)
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
        logger.info(f"Installing ArgoCD for cluster {self.model.name}")

        repo_url = "https://argoproj.github.io/argo-helm"
        release_name = "argocd"
        namespace = "argocd"
        chart_name = "argo/argo-cd"

        await self._install_helm_chart(
            repo_name="argo",
            repo_url=repo_url,
            release_name=release_name,
            chart_name=chart_name,
            namespace=namespace,
        )

    async def _install_helm_chart(
        self,
        repo_name: str,
        repo_url: str,
        release_name: str,
        chart_name: str,
        namespace: str,
        set_vals: dict[str, str] = None,
        create_namespace: bool = True,
    ):
        kubeconfig_path = None
        temp_kf = None

        try:
            if self.model.type == K8sClusterType.REMOTE:
                if not self.model.kubeconfig:
                    raise ValueError(f"Cluster {self.model.name} has no kubeconfig")
                temp_kf = tempfile.NamedTemporaryFile(mode="w", delete=False)
                temp_kf.write(self.model.kubeconfig)
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
            await run_helm("repo", "add", repo_name, repo_url)
            await run_helm("repo", "update")

            # Install
            args = [
                "upgrade",
                "--install",
                release_name,
                chart_name,
                "--namespace",
                namespace,
                "--wait",
            ]
            if create_namespace:
                args.append("--create-namespace")

            if set_vals:
                for k, v in set_vals.items():
                    args.extend(["--set", f"{k}={v}"])

            await run_helm(*args)

        finally:
            if temp_kf:
                try:
                    os.unlink(temp_kf.name)
                except Exception:
                    pass


@K8sClusterService.register_action("install_cert_manager")
class InstallCertManagerAction(InstallArgoCDAction):

    async def available(self) -> bool:
        # Only available if not already installed
        stmt = select(K8sClusterStatus).where(
            K8sClusterStatus.k8s_cluster_id == self.model.id
        )
        result = await self.session.exec(stmt)
        status = result.one_or_none()
        return not (status and status.cert_manager_installed)

    async def __call__(self, **kwargs):
        from mindweaver.tasks.k8s_cluster_status import install_cert_manager_task

        # Set status to installed immediately so UI reflects it
        stmt = select(K8sClusterStatus).where(
            K8sClusterStatus.k8s_cluster_id == self.model.id
        )
        result = await self.session.exec(stmt)
        status_model = result.one_or_none()
        if not status_model:
            status_model = K8sClusterStatus(k8s_cluster_id=self.model.id)
            self.session.add(status_model)
        status_model.cert_manager_installed = True
        await self.session.flush()

        install_cert_manager_task.delay(self.model.id)
        return {
            "status": "success",
            "message": "Cert Manager installation triggered and status being refreshed.",
        }

    async def run(self):
        """Install Cert Manager to the cluster using Helm chart"""
        logger.info(f"Installing Cert Manager for cluster {self.model.name}")

        await self._install_helm_chart(
            repo_name="jetstack",
            repo_url="https://charts.jetstack.io",
            release_name="cert-manager",
            chart_name="jetstack/cert-manager",
            namespace="cert-manager",
            set_vals={"installCRDs": "true"},
        )


@K8sClusterService.register_action("install_cnpg_operator")
class InstallCNPGAction(InstallArgoCDAction):

    async def available(self) -> bool:
        # Only available if not already installed
        stmt = select(K8sClusterStatus).where(
            K8sClusterStatus.k8s_cluster_id == self.model.id
        )
        result = await self.session.exec(stmt)
        status = result.one_or_none()
        return not (status and status.cnpg_installed)

    async def __call__(self, **kwargs):
        from mindweaver.tasks.k8s_cluster_status import install_cnpg_operator_task

        # Set status to installed immediately so UI reflects it
        stmt = select(K8sClusterStatus).where(
            K8sClusterStatus.k8s_cluster_id == self.model.id
        )
        result = await self.session.exec(stmt)
        status_model = result.one_or_none()
        if not status_model:
            status_model = K8sClusterStatus(k8s_cluster_id=self.model.id)
            self.session.add(status_model)
        status_model.cnpg_installed = True
        await self.session.flush()

        install_cnpg_operator_task.delay(self.model.id)
        return {
            "status": "success",
            "message": "CNPG Operator installation triggered and status being refreshed.",
        }

    async def run(self):
        """Install CNPG Operator to the cluster using Helm chart"""
        logger.info(f"Installing CNPG Operator for cluster {self.model.name}")

        await self._install_helm_chart(
            repo_name="cnpg",
            repo_url="https://cloudnative-pg.github.io/charts",
            release_name="cnpg",
            chart_name="cnpg/cloudnative-pg",
            namespace="cnpg-system",
        )


@K8sClusterService.register_action("install_self_signed_issuer")
class InstallSelfSignedIssuerAction(InstallArgoCDAction):

    async def available(self) -> bool:
        # Only available if cert-manager is installed and issuer is not
        stmt = select(K8sClusterStatus).where(
            K8sClusterStatus.k8s_cluster_id == self.model.id
        )
        result = await self.session.exec(stmt)
        status = result.one_or_none()
        return status and status.cert_manager_installed and not status.cluster_issuer_installed

    async def __call__(self, **kwargs):
        from mindweaver.tasks.k8s_cluster_status import install_self_signed_issuer_task

        # Set status to installed immediately so UI reflects it
        stmt = select(K8sClusterStatus).where(
            K8sClusterStatus.k8s_cluster_id == self.model.id
        )
        result = await self.session.exec(stmt)
        status_model = result.one_or_none()
        if not status_model:
            status_model = K8sClusterStatus(k8s_cluster_id=self.model.id)
            self.session.add(status_model)
        status_model.cluster_issuer_installed = True
        await self.session.flush()

        install_self_signed_issuer_task.delay(self.model.id)
        return {
            "status": "success",
            "message": "Self-signed ClusterIssuer installation triggered.",
        }

    async def run(self):
        """Install self-signed ClusterIssuer to the cluster"""
        logger.info(f"Installing Self-signed ClusterIssuer for cluster {self.model.name}")

        manifest = """
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: mindweaver-selfsigned-issuer
spec:
  selfSigned: {}
"""
        await self._apply_yaml(manifest)

    async def _apply_yaml(self, manifest: str):
        kubeconfig_path = None
        temp_kf = None
        temp_manifest = None

        try:
            if self.model.type == K8sClusterType.REMOTE:
                if not self.model.kubeconfig:
                    raise ValueError(f"Cluster {self.model.name} has no kubeconfig")
                temp_kf = tempfile.NamedTemporaryFile(mode="w", delete=False)
                temp_kf.write(self.model.kubeconfig)
                temp_kf.flush()
                temp_kf.close()
                kubeconfig_path = temp_kf.name

            temp_manifest = tempfile.NamedTemporaryFile(mode="w", delete=False)
            temp_manifest.write(manifest)
            temp_manifest.flush()
            temp_manifest.close()

            cmd = ["kubectl"]
            if kubeconfig_path:
                cmd.extend(["--kubeconfig", kubeconfig_path])
            cmd.extend(["apply", "-f", temp_manifest.name])

            logger.debug(f"Running kubectl command: {' '.join(cmd)}")
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                raise RuntimeError(f"Kubectl command failed: {stderr.decode()}")
            return stdout.decode()

        finally:
            for f in [temp_kf, temp_manifest]:
                if f:
                    try:
                        os.unlink(f.name)
                    except Exception:
                        pass
