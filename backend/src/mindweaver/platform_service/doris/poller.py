# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import asyncio
import logging
import tempfile
from kubernetes import client, config
from mindweaver.fw.model import ts_now
from .model import DorisPlatform
from .service import DorisPlatformService

logger = logging.getLogger(__name__)


@DorisPlatformService.register_poller()
class DorisPoller:
    """Poller for Apache Doris platform service."""

    def __init__(self, service: DorisPlatformService, model: DorisPlatform):
        self.service = service
        self.model = model

    async def poll(self):
        """Polls cluster status via ArgoCD application and k8s pods/services and updates DorisPlatformState."""
        kubeconfig = await self.service.kubeconfig(self.model)
        namespace = await self.service._resolve_namespace(self.model)
        state = await self.service.platform_state(self.model)
        is_active = state.active if state else True

        def _poll(active: bool):
            if kubeconfig is None:
                config.load_incluster_config()
                k8s_client = client.ApiClient()
            else:
                with tempfile.NamedTemporaryFile(mode="w") as kf:
                    kf.write(kubeconfig)
                    kf.flush()
                    k8s_client = config.new_client_from_config(config_file=kf.name)

            custom_api = client.CustomObjectsApi(k8s_client)
            core_v1 = client.CoreV1Api(k8s_client)

            # 1. Check ArgoCD Application Status
            try:
                argo_app = custom_api.get_namespaced_custom_object(
                    group="argoproj.io",
                    version="v1alpha1",
                    namespace="argocd",
                    plural="applications",
                    name=self.model.name,
                )
                sync_status = (
                    argo_app.get("status", {}).get("sync", {}).get("status", "Unknown")
                )
                health_status = (
                    argo_app.get("status", {})
                    .get("health", {})
                    .get("status", "Unknown")
                )

                if health_status == "Healthy":
                    status = "online"
                elif health_status in ["Progressing", "Pending"]:
                    status = "pending"
                else:
                    status = "error"

                message = f"Sync: {sync_status}, Health: {health_status}"
            except Exception as e:
                if not active:
                    status = "offline"
                    message = "Decommissioned"
                else:
                    status = "error"
                    message = f"Failed to fetch ArgoCD status: {str(e)}"
                return status, message, {}, [], []

            # 2. Fetch Pod Status for FE and BE
            try:
                pods = core_v1.list_namespaced_pod(namespace=namespace)
                fe_pods = [
                    p for p in pods.items
                    if p.metadata.name.startswith(f"{self.model.name}-fe")
                ]
                be_pods = [
                    p for p in pods.items
                    if p.metadata.name.startswith(f"{self.model.name}-be")
                ]

                fe_ready = sum(
                    1 for p in fe_pods
                    if p.status.phase == "Running" and any(c.ready for c in (p.status.container_statuses or []))
                )
                be_ready = sum(
                    1 for p in be_pods
                    if p.status.phase == "Running" and any(c.ready for c in (p.status.container_statuses or []))
                )

                message += f" | Pods: FE {fe_ready}/{len(fe_pods)}, BE {be_ready}/{len(be_pods)}"
            except Exception as e:
                logger.error(f"Failed to fetch pods for {self.model.name}: {e}")

            # 3. Fetch NodePorts
            node_ports = []
            try:
                services = core_v1.list_namespaced_service(namespace=namespace)
                for svc in services.items:
                    if svc.metadata.name.startswith(self.model.name):
                        if svc.spec.type == "NodePort":
                            for port in svc.spec.ports:
                                protocol = "mysql" if port.port == 9030 else ("https" if port.port == 443 else "http")
                                node_ports.append(
                                    {
                                        "name": svc.metadata.name,
                                        "port": port.port,
                                        "node_port": port.node_port,
                                        "protocol": protocol,
                                    }
                                )
            except Exception as e:
                logger.error(f"Failed to fetch services for {self.model.name}: {e}")

            # 4. Fetch Nodes for IP info
            cluster_nodes = []
            try:
                nodes = core_v1.list_node()
                for node in nodes.items:
                    node_info = {"hostname": "unknown", "ipv4": None, "ipv6": None}
                    for addr in node.status.addresses:
                        if addr.type == "Hostname":
                            node_info["hostname"] = addr.address
                        elif addr.type == "InternalIP":
                            if ":" in addr.address:
                                node_info["ipv6"] = addr.address
                            else:
                                node_info["ipv4"] = addr.address
                    cluster_nodes.append(node_info)
            except Exception as e:
                logger.error(f"Failed to fetch nodes: {e}")

            return (
                status,
                message,
                argo_app.get("status", {}),
                node_ports,
                cluster_nodes,
            )

        status, message, extra_data, node_ports, cluster_nodes = (
            await asyncio.to_thread(_poll, is_active)
        )

        state = await self.service.platform_state(self.model)
        if not state:
            state = self.service.state_model(platform_id=self.model.id)
            self.service.session.add(state)

        if not state.active and status == "offline":
            state.status = "offline"
            state.message = message
            return

        state.status = status
        state.message = message
        project = await self.service.project(self.model)
        if extra_data is None:
            extra_data = {}
        extra_data["namespace"] = namespace
        extra_data["ingress_domain"] = project.ingress_domain
        state.extra_data = extra_data
        state.node_ports = node_ports
        state.cluster_nodes = cluster_nodes

        # Derive Query and HTTP URIs
        if status == "online":
            mysql_np = next((np for np in node_ports if np["port"] == 9030), None)
            http_np = next((np for np in node_ports if np["port"] == 8030), None)
            node_v4 = next((n for n in cluster_nodes if n["ipv4"]), None)

            # Query URI
            if mysql_np and node_v4:
                state.query_uri = f"mysql://root:{self.model.admin_password}@{node_v4['ipv4']}:{mysql_np['node_port']}"
            else:
                state.query_uri = f"mysql://root:{self.model.admin_password}@{self.model.name}-fe-service.{namespace}.svc.cluster.local:9030"

            # HTTP URI
            if project.ingress_domain:
                state.fe_http_uri = f"https://{self.model.name}.{project.ingress_domain}"
            elif http_np and node_v4:
                state.fe_http_uri = f"http://{node_v4['ipv4']}:{http_np['node_port']}"
            else:
                state.fe_http_uri = f"http://{self.model.name}-fe-service.{namespace}.svc.cluster.local:8030"
        else:
            state.query_uri = None
            state.fe_http_uri = None

        state.admin_user = "root"
        state.admin_password = self.model.admin_password
        state.last_heartbeat = ts_now()
        await self.service.session.flush()
