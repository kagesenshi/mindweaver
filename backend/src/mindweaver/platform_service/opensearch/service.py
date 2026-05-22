# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import os
import logging
import asyncio
import tempfile
from typing import Any, Optional
from kubernetes import client, config
from mindweaver.platform_service.base import PlatformService
from mindweaver.crypto import decrypt_password
from mindweaver.fw.model import ts_now
from mindweaver.fw.util import generate_password
from mindweaver.fw.hooks import before_create

from .model import OpenSearchPlatform, OpenSearchPlatformState

logger = logging.getLogger(__name__)


class OpenSearchPlatformService(PlatformService[OpenSearchPlatform]):
    template_directory: str = os.path.join(os.path.dirname(__file__), "templates")
    state_model: type[OpenSearchPlatformState] = OpenSearchPlatformState

    @classmethod
    def model_class(cls) -> type[OpenSearchPlatform]:
        return OpenSearchPlatform

    @classmethod
    def service_path(cls) -> str:
        return "/platform/opensearch"

    @classmethod
    def redacted_fields(cls) -> list[str]:
        return super().redacted_fields() + [
            "admin_password",
        ]

    @classmethod
    def internal_fields(cls) -> list[str]:
        return super().internal_fields() + [
            "admin_password",
        ]

    @classmethod
    def widgets(cls) -> dict[str, Any]:
        return {
            "chart_version": {
                "order": 3,
                "label": "Chart Version",
            },
            "override_image": {
                "order": 4,
                "type": "boolean",
                "label": "Override Image",
            },
            "image": {"order": 5, "label": "Image"},
            "image_tag": {"order": 6, "label": "Image Tag"},
            "storage_size": {"order": 7, "label": "Storage Size"},
            "replica_count": {
                "order": 10,
                "type": "range",
                "min": 1,
                "max": 9,
                "step": 2,
            },
            "cpu_request": {
                "order": 11,
                "type": "range",
                "min": 0.1,
                "max": 16,
                "step": 0.1,
            },
            "cpu_limit": {
                "order": 12,
                "type": "range",
                "min": 0.1,
                "max": 16,
                "step": 0.1,
            },
            "mem_request": {
                "order": 13,
                "type": "range",
                "min": 0.5,
                "max": 64,
                "step": 0.5,
                "label": "Memory Request (Gi)",
            },
            "mem_limit": {
                "order": 14,
                "type": "range",
                "min": 0.5,
                "max": 64,
                "step": 0.5,
                "label": "Memory Limit (Gi)",
            },
            "additional_properties": {
                "order": 100,
                "label": "Additional Properties",
                "type": "key-value",
            },
        }

    @before_create(before="_handle_redacted_create")
    async def generate_passwords(self, model: OpenSearchPlatform):
        """Autogenerate a strong random password for the admin user."""
        model.admin_password = generate_password()

    async def template_vars(self, model: OpenSearchPlatform) -> dict:
        vars = model.model_dump()
        vars["namespace"] = await self._resolve_namespace(model)

        # Decrypt password
        if model.admin_password:
            try:
                vars["admin_password"] = decrypt_password(model.admin_password)
            except Exception:
                vars["admin_password"] = model.admin_password

        return vars

    async def poll_status(self, model: OpenSearchPlatform):
        kubeconfig = await self.kubeconfig(model)
        namespace = await self._resolve_namespace(model)
        state = await self.platform_state(model)
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
                    name=model.name,
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
                    label_selector=f"app.kubernetes.io/instance={model.name}",
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
                logger.error(f"Failed to fetch pods for {model.name}: {e}")

            # 3. Fetch NodePorts for UI
            node_ports = []
            try:
                services = core_v1.list_namespaced_service(namespace=namespace)
                for svc in services.items:
                    instance_label = svc.metadata.labels.get("app.kubernetes.io/instance") if svc.metadata.labels else None
                    if (
                        svc.metadata.name == model.name
                        or svc.metadata.name.startswith(model.name)
                        or svc.metadata.name == f"{model.name}-opensearch"
                        or instance_label == model.name
                    ):
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
                logger.error(f"Failed to fetch services for {model.name}: {e}")

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

        state = await self.platform_state(model)
        if not state:
            state = self.state_model(platform_id=model.id)
            self.session.add(state)

        if not state.active and status == "offline":
            state.status = "offline"
            state.message = message
            return

        state.status = status
        state.message = message
        if extra_data is None:
            extra_data = {}
        extra_data["namespace"] = namespace
        state.extra_data = extra_data
        state.node_ports = node_ports
        state.cluster_nodes = cluster_nodes

        # Derive OpenSearch URL (default API port is 9200)
        if status == "online" and cluster_nodes:
            opensearch_np = next((np for np in node_ports if np["port"] == 9200), None)
            if opensearch_np:
                # Find first node with IPv4
                node_v4 = next((n for n in cluster_nodes if n["ipv4"]), None)
                if node_v4:
                    state.opensearch_url = (
                        f"https://{node_v4['ipv4']}:{opensearch_np['node_port']}"
                    )
                else:
                    state.opensearch_url = None

                # Find first node with IPv6
                node_v6 = next((n for n in cluster_nodes if n["ipv6"]), None)
                if node_v6:
                    state.opensearch_url_ipv6 = (
                        f"https://[{node_v6['ipv6']}]:{opensearch_np['node_port']}"
                    )
                else:
                    state.opensearch_url_ipv6 = None
            else:
                state.opensearch_url = f"https://{model.name}.{namespace}.svc.cluster.local:9200"
                state.opensearch_url_ipv6 = None
        else:
            state.opensearch_url = None
            state.opensearch_url_ipv6 = None

        # Populating passwords for UI display
        state.admin_password = model.admin_password
        state.last_heartbeat = ts_now()

        await self.session.flush()
