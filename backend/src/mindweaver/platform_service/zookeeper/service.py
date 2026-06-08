# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import os
import logging
import asyncio
import tempfile
from typing import Any, Optional
from kubernetes import client, config
from mindweaver.platform_service.base import PlatformService
from mindweaver.fw.model import ts_now

from .model import ZookeeperPlatform, ZookeeperPlatformState

logger = logging.getLogger(__name__)


class ZookeeperPlatformService(PlatformService[ZookeeperPlatform]):
    template_directory: str = os.path.join(os.path.dirname(__file__), "templates")
    state_model: type[ZookeeperPlatformState] = ZookeeperPlatformState

    @classmethod
    def model_class(cls) -> type[ZookeeperPlatform]:
        return ZookeeperPlatform

    @classmethod
    def service_path(cls) -> str:
        return "/platform/zookeeper"

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
                "step": 1,
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

    async def template_vars(self, model: ZookeeperPlatform) -> dict:
        vars = model.model_dump()
        vars["namespace"] = await self._resolve_namespace(model)
        project = await self.project(model)
        vars["ingress_domain"] = project.ingress_domain
        return vars

    async def poll_status(self, model: ZookeeperPlatform):
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
                return status, message, {}, [], [], None

            # 2. Fetch Pod Status
            try:
                pods = core_v1.list_namespaced_pod(
                    namespace=namespace,
                    label_selector=f"release={model.name}",
                )
                if not pods.items:
                    pods = core_v1.list_namespaced_pod(
                        namespace=namespace,
                        label_selector=f"app={model.name}",
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

            # 3. Discover ZooKeeper client service (name-pattern + label, namespace-scoped)
            # The Pravega ZK operator creates services as `{name}-zookeeper-client`
            # (Helm may also label the release as `{name}-zookeeper`, not `{name}`).
            # We list all services in the namespace and find the client service by:
            #   - Name starts with the model name AND contains "client"
            #   - Secondary: label component=client or headless=false
            node_ports = []
            service_name = None
            try:
                services = core_v1.list_namespaced_service(namespace=namespace)
                candidate_svcs = [
                    svc for svc in services.items
                    if svc.metadata.name.startswith(model.name)
                    and "client" in svc.metadata.name
                ]
                if candidate_svcs:
                    # Prefer services labelled component=client or headless=false
                    # (Pravega sets headless=false on the client service)
                    preferred = [
                        s for s in candidate_svcs
                        if (s.metadata.labels or {}).get("component") == "client"
                        or (s.metadata.labels or {}).get("headless") == "false"
                    ]
                    chosen = preferred[0] if preferred else candidate_svcs[0]
                    service_name = chosen.metadata.name
                    if chosen.spec.type == "NodePort":
                        for port in chosen.spec.ports:
                            node_ports.append(
                                {
                                    "name": chosen.metadata.name,
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
                service_name,
            )

        status, message, argo_status, node_ports, cluster_nodes, service_name = (
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
        project = await self.project(model)
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

        # Derive Zookeeper URL (port 2181)
        if status == "online":
            svc_name = service_name or f"{model.name}-client"
            state.zookeeper_url = f"{svc_name}.{namespace}.svc.cluster.local:2181"
            state.zookeeper_url_ipv6 = None
        else:
            state.zookeeper_url = None
            state.zookeeper_url_ipv6 = None

        state.last_heartbeat = ts_now()
        await self.session.flush()
