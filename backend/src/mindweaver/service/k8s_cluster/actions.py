# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import asyncio
import logging
import tempfile
import os
import yaml
import jinja2 as j2
from kubernetes import client, config

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

    def _get_kubernetes_clients(self):
        """Helper to load kubernetes config and return clients"""
        if self.model.type == K8sClusterType.IN_CLUSTER:
            config.load_incluster_config()
            return client.CoreV1Api(), client.ApiextensionsV1Api()
        else:
            if not self.model.kubeconfig:
                raise ValueError(f"Cluster {self.model.name} has no kubeconfig")
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as kf:
                kf.write(self.model.kubeconfig)
                kf.flush()
                temp_name = kf.name
            try:
                api_client = config.new_client_from_config(config_file=temp_name)
                return client.CoreV1Api(api_client), client.ApiextensionsV1Api(api_client)
            finally:
                try:
                    os.unlink(temp_name)
                except Exception:
                    pass

    async def _wait_for_crd_and_namespace(self, crd_names: list[str], namespace: str = None, timeout: int = 60):
        """Wait for specified CRDs and optionally a namespace to be registered and exist"""
        logger.info(f"Waiting for CRDs {crd_names} and namespace {namespace} to be ready...")
        try:
            core_api, ext_api = self._get_kubernetes_clients()
        except Exception as e:
            logger.warning(f"Could not load kubernetes clients to wait: {e}")
            return

        for _ in range(int(timeout / 2)):
            try:
                ns_ready = True
                if namespace:
                    try:
                        core_api.read_namespace(namespace)
                    except Exception:
                        ns_ready = False
                
                crds_ready = True
                for crd in crd_names:
                    try:
                        ext_api.read_custom_resource_definition(crd)
                    except Exception:
                        crds_ready = False
                        break
                
                if ns_ready and crds_ready:
                    logger.info("CRDs and namespace are ready!")
                    return
            except Exception as e:
                logger.warning(f"Error checking CRDs/namespace: {e}")
            await asyncio.sleep(2)
        logger.warning(f"Timed out waiting for CRDs {crd_names} and namespace {namespace}")

    async def _apply_template(self, template_name: str, **kwargs):
        """Load, render and apply a manifest template from the templates directory"""
        template_dir = os.path.join(os.path.dirname(__file__), "templates")
        env = j2.Environment(loader=j2.FileSystemLoader(template_dir))
        template = env.get_template(template_name)
        manifest = template.render(**kwargs)
        await self._apply_yaml(manifest)

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
            if repo_url and not repo_url.startswith("oci://"):
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
        """Install Cert Manager to the cluster using ArgoCD Application"""
        logger.info(f"Installing Cert Manager for cluster {self.model.name}")

        await self._apply_template("cert-manager.yml.j2")


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
        """Install CNPG Operator to the cluster using ArgoCD Application"""
        logger.info(f"Installing CNPG Operator for cluster {self.model.name}")

        await self._apply_template("cnpg.yml.j2")


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

        await self._wait_for_crd_and_namespace(
            ["clusterissuers.cert-manager.io", "certificates.cert-manager.io"],
            "cert-manager"
        )

        await self._apply_template("self-signed-issuer.yml.j2")




@K8sClusterService.register_action("install_envoy_gateway")
class InstallEnvoyGatewayAction(InstallArgoCDAction):

    async def available(self) -> bool:
        stmt = select(K8sClusterStatus).where(
            K8sClusterStatus.k8s_cluster_id == self.model.id
        )
        result = await self.session.exec(stmt)
        status = result.one_or_none()
        return not (status and status.envoy_gateway_installed)

    async def __call__(self, **kwargs):
        from mindweaver.tasks.k8s_cluster_status import install_envoy_gateway_task

        # Set status to installed immediately so UI reflects it
        stmt = select(K8sClusterStatus).where(
            K8sClusterStatus.k8s_cluster_id == self.model.id
        )
        result = await self.session.exec(stmt)
        status_model = result.one_or_none()
        if not status_model:
            status_model = K8sClusterStatus(k8s_cluster_id=self.model.id)
            self.session.add(status_model)
        status_model.envoy_gateway_installed = True
        await self.session.flush()

        install_envoy_gateway_task.delay(self.model.id)
        return {
            "status": "success",
            "message": "Envoy Gateway installation triggered and status being refreshed.",
        }

    async def run(self):
        """Install Envoy Gateway to the cluster using ArgoCD Application and configured service type"""
        logger.info(f"Installing Envoy Gateway for cluster {self.model.name}")

        await self._apply_template("envoy-gateway.yml.j2")

        await self._wait_for_crd_and_namespace(
            ["envoyproxies.gateway.envoyproxy.io", "gatewayclasses.gateway.networking.k8s.io"],
            "envoy-gateway-system"
        )

        # Deploy global GatewayClass and EnvoyProxy resources
        logger.info("Applying global Envoy GatewayClass and EnvoyProxy configuration")
        await self._apply_template("envoy-gateway-config.yml.j2", service_type=self.model.envoy_gateway_service_type)


@K8sClusterService.register_action("sync_core_integrations")
class SyncCoreIntegrationsAction(InstallArgoCDAction):

    async def available(self) -> bool:
        """Check if action is available"""
        stmt = select(K8sClusterStatus).where(
            K8sClusterStatus.k8s_cluster_id == self.model.id
        )
        result = await self.session.exec(stmt)
        status = result.one_or_none()
        if status and status.status == "offline":
            return False
        return True

    async def __call__(self, **kwargs):
        """Invoke the action asynchronously via Celery task"""
        from mindweaver.tasks.k8s_cluster_status import sync_core_integrations_task

        # Set status flags to True immediately so UI shows sync in progress or active states
        stmt = select(K8sClusterStatus).where(
            K8sClusterStatus.k8s_cluster_id == self.model.id
        )
        result = await self.session.exec(stmt)
        status_model = result.one_or_none()
        if not status_model:
            status_model = K8sClusterStatus(k8s_cluster_id=self.model.id)
            self.session.add(status_model)
        await self.session.flush()

        sync_core_integrations_task.delay(self.model.id)
        return {
            "status": "success",
            "message": "Core integrations synchronization triggered.",
        }

    async def run(self):
        """Execute the sync workflow sequentially to install or update all integrations"""
        logger.info(f"Syncing core integrations for cluster {self.model.name}")
        
        stmt = select(K8sClusterStatus).where(
            K8sClusterStatus.k8s_cluster_id == self.model.id
        )
        result = await self.session.exec(stmt)
        status = result.one_or_none()
        if not status:
            return

        # 1. Install ArgoCD if missing
        if not status.argocd_installed:
            logger.info("Sync: Installing ArgoCD...")
            from .actions import InstallArgoCDAction
            action = InstallArgoCDAction(self.model, self.svc)
            action.session = self.session
            await action.run()
            status.argocd_installed = True
            await self.session.flush()

        # 2. Deploy/update Cert Manager Application manifest
        logger.info("Sync: Deploying/updating Cert Manager...")
        from .actions import InstallCertManagerAction
        action = InstallCertManagerAction(self.model, self.svc)
        action.session = self.session
        await action.run()
        status.cert_manager_installed = True
        await self.session.flush()

        # 3. Deploy/update CNPG Operator Application manifest
        logger.info("Sync: Deploying/updating CNPG Operator...")
        from .actions import InstallCNPGAction
        action = InstallCNPGAction(self.model, self.svc)
        action.session = self.session
        await action.run()
        status.cnpg_installed = True
        await self.session.flush()

        # 4. Deploy/update Envoy Gateway or update config if envoy gateway is already installed
        logger.info("Sync: Deploying/updating Envoy Gateway config...")
        from .actions import InstallEnvoyGatewayAction
        action = InstallEnvoyGatewayAction(self.model, self.svc)
        action.session = self.session
        await action.run()
        status.envoy_gateway_installed = True
        await self.session.flush()

        # 5. Deploy/update Self-signed Issuer
        logger.info("Sync: Deploying/updating Self-signed Issuer...")
        from .actions import InstallSelfSignedIssuerAction
        action = InstallSelfSignedIssuerAction(self.model, self.svc)
        action.session = self.session
        await action.run()
        status.cluster_issuer_installed = True
        await self.session.flush()

        # 6. Deploy/update Solr Operator Application manifest
        logger.info("Sync: Deploying/updating Solr Operator...")
        from .actions import InstallSolrOperatorAction
        action = InstallSolrOperatorAction(self.model, self.svc)
        action.session = self.session
        await action.run()
        status.solr_operator_installed = True
        await self.session.flush()

        # 7. Deploy/update Kafka Operator Application manifest
        logger.info("Sync: Deploying/updating Kafka Operator...")
        from .actions import InstallKafkaOperatorAction
        action_kafka = InstallKafkaOperatorAction(self.model, self.svc)
        action_kafka.session = self.session
        await action_kafka.run()
        status.kafka_operator_installed = True
        await self.session.flush()


@K8sClusterService.register_action("install_solr_operator")
class InstallSolrOperatorAction(InstallArgoCDAction):

    async def available(self) -> bool:
        """Check if Solr Operator action is available (not installed yet)"""
        stmt = select(K8sClusterStatus).where(
            K8sClusterStatus.k8s_cluster_id == self.model.id
        )
        result = await self.session.exec(stmt)
        status = result.one_or_none()
        return not (status and status.solr_operator_installed)

    async def __call__(self, **kwargs):
        """Call method to queue Solr Operator installation task asynchronously"""
        from mindweaver.tasks.k8s_cluster_status import install_solr_operator_task

        stmt = select(K8sClusterStatus).where(
            K8sClusterStatus.k8s_cluster_id == self.model.id
        )
        result = await self.session.exec(stmt)
        status_model = result.one_or_none()
        if not status_model:
            status_model = K8sClusterStatus(k8s_cluster_id=self.model.id)
            self.session.add(status_model)
        status_model.solr_operator_installed = True
        await self.session.flush()

        install_solr_operator_task.delay(self.model.id)
        return {
            "status": "success",
            "message": "Solr Operator installation triggered and status being refreshed.",
        }

    async def run(self):
        """Install Solr Operator to the cluster using ArgoCD Application"""
        logger.info(f"Installing Solr Operator for cluster {self.model.name}")

        await self._apply_template("solr-operator.yml.j2")


@K8sClusterService.register_action("install_kafka_operator")
class InstallKafkaOperatorAction(InstallArgoCDAction):

    async def available(self) -> bool:
        """Check if Kafka Operator action is available (not installed yet)"""
        stmt = select(K8sClusterStatus).where(
            K8sClusterStatus.k8s_cluster_id == self.model.id
        )
        result = await self.session.exec(stmt)
        status = result.one_or_none()
        return not (status and status.kafka_operator_installed)

    async def __call__(self, **kwargs):
        """Call method to queue Kafka Operator installation task asynchronously"""
        from mindweaver.tasks.k8s_cluster_status import install_kafka_operator_task

        stmt = select(K8sClusterStatus).where(
            K8sClusterStatus.k8s_cluster_id == self.model.id
        )
        result = await self.session.exec(stmt)
        status_model = result.one_or_none()
        if not status_model:
            status_model = K8sClusterStatus(k8s_cluster_id=self.model.id)
            self.session.add(status_model)
        status_model.kafka_operator_installed = True
        await self.session.flush()

        install_kafka_operator_task.delay(self.model.id)
        return {
            "status": "success",
            "message": "Kafka Operator installation triggered and status being refreshed.",
        }

    async def run(self):
        """Install Strimzi Kafka Operator to the cluster using ArgoCD Application"""
        logger.info(f"Installing Kafka Operator for cluster {self.model.name}")

        await self._apply_template("kafka-operator.yml.j2")




