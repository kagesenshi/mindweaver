# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import asyncio
import logging
import tempfile
from kubernetes import client, config
from mindweaver.fw.model import ts_now
from mindweaver.crypto import decrypt_password
from .model import AirflowPlatform
from .service import AirflowPlatformService

logger = logging.getLogger(__name__)


def _derive_airflow_uris(
    status, service_name, ingress_domain, node_ports, cluster_nodes
):
    if status != "online":
        return None, None

    if ingress_domain:
        return f"https://{service_name}.{ingress_domain}", None

    airflow_np = next(
        (
            port
            for port in node_ports
            if port.get("name") == f"{service_name}-api-server"
            and port.get("port") == 8080
            and port.get("node_port")
        ),
        None,
    )
    if not airflow_np:
        return None, None

    node_v4 = next((node for node in cluster_nodes if node.get("ipv4")), None)
    node_v6 = next((node for node in cluster_nodes if node.get("ipv6")), None)
    ipv4_uri = (
        f"http://{node_v4['ipv4']}:{airflow_np['node_port']}" if node_v4 else None
    )
    ipv6_uri = (
        f"http://[{node_v6['ipv6']}]:{airflow_np['node_port']}" if node_v6 else None
    )
    return ipv4_uri, ipv6_uri


@AirflowPlatformService.register_poller()
class AirflowPoller:
    """Poller for Airflow platform service."""

    def __init__(self, service: AirflowPlatformService, model: AirflowPlatform):
        self.service = service
        self.model = model

    async def poll(self):
        """Polls the status of the ArgoCD application and Kubernetes resources."""
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

            # 2. Fetch Pod Status
            try:
                pods = core_v1.list_namespaced_pod(
                    namespace=namespace,
                    label_selector=f"app.kubernetes.io/instance={self.model.name}",
                )
                ready_pods = sum(
                    1
                    for p in pods.items
                    if p.status.phase == "Running"
                    and any(c.ready for c in (p.status.container_statuses or []))
                )
                total_pods = len(pods.items)
                message += f" | Pods: {ready_pods}/{total_pods}"
            except Exception as e:
                logger.error(f"Failed to fetch pods for {self.model.name}: {e}")

            # 3. Fetch NodePorts (for Airflow web UI)
            node_ports = []
            try:
                services = core_v1.list_namespaced_service(namespace=namespace)
                for svc in services.items:
                    if svc.metadata.name.startswith(self.model.name):
                        if svc.spec.type == "NodePort":
                            for port in svc.spec.ports:
                                node_ports.append(
                                    {
                                        "name": svc.metadata.name,
                                        "port": port.port,
                                        "node_port": port.node_port,
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

        # Populate admin credentials
        state.admin_user = "admin"
        state.admin_password = decrypt_password(self.model.admin_password)

        state.airflow_uri, state.airflow_uri_ipv6 = _derive_airflow_uris(
            status,
            self.model.name,
            project.ingress_domain,
            node_ports,
            cluster_nodes,
        )

        state.last_heartbeat = ts_now()
        await self.service.session.flush()
