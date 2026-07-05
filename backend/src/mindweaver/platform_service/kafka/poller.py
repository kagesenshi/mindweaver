# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import asyncio
import logging
import tempfile
from kubernetes import client, config
from mindweaver.fw.model import ts_now
from .model import KafkaPlatform
from .service import KafkaPlatformService

logger = logging.getLogger(__name__)


@KafkaPlatformService.register_poller()
class KafkaPoller:
    """Poller for Kafka platform service."""

    def __init__(self, service: KafkaPlatformService, model: KafkaPlatform):
        self.service = service
        self.model = model

    async def poll(self):
        """Polls the status of the ArgoCD application and Kubernetes resources."""
        kubeconfig = await self.service.kubeconfig(self.model)
        namespace = await self.service._resolve_namespace(self.model)
        state = await self.service.platform_state(self.model)
        is_active = state.active if state else True

        def _poll(active: bool):
            """Internal synchronous poller that interfaces with K8s API client."""
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
                return status, message, {}, [], [], None

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

            # 3. Discover Kafka service
            node_ports = []
            service_name = None
            try:
                services = core_v1.list_namespaced_service(namespace=namespace)
                candidate_svcs = [
                    svc for svc in services.items
                    if svc.metadata.name.startswith(self.model.name)
                ]
                # Determine primary service name
                bootstrap_svc = next((svc for svc in candidate_svcs if svc.metadata.name == f"{self.model.name}-kafka-bootstrap" or svc.metadata.name == f"{self.model.name}-kafka-external-bootstrap"), None)
                if bootstrap_svc:
                    service_name = bootstrap_svc.metadata.name
                elif candidate_svcs:
                    service_name = next((svc.metadata.name for svc in candidate_svcs if svc.metadata.name == self.model.name or svc.metadata.name.endswith("-kafka")), candidate_svcs[0].metadata.name)

                for svc in candidate_svcs:
                    if svc.spec.type == "NodePort":
                        for port in svc.spec.ports:
                            if not any(np["name"] == svc.metadata.name and np["port"] == port.port for np in node_ports):
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
                service_name,
            )

        status, message, argo_status, node_ports, cluster_nodes, service_name = (
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
        if argo_status is None:
            argo_status = {}
        extra_data = argo_status
        extra_data["namespace"] = namespace
        extra_data["ingress_domain"] = project.ingress_domain
        if service_name:
            extra_data["service_name"] = service_name
        state.extra_data = extra_data
        state.node_ports = node_ports
        state.cluster_nodes = cluster_nodes

        # Derive Kafka URL (port 9092)
        if status == "online":
            svc_name = service_name or self.model.name
            state.kafka_url = f"{svc_name}.{namespace}.svc.cluster.local:9092"
            state.kafka_url_ipv6 = None
        else:
            state.kafka_url = None
            state.kafka_url_ipv6 = None

        state.last_heartbeat = ts_now()
        await self.service.session.flush()
