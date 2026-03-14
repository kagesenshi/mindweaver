# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import os
import logging
import asyncio
import tempfile
import base64
from typing import Any, Optional
from kubernetes import client, config
from pydantic import ValidationError
from mindweaver.fw.exc import FieldValidationError
from mindweaver.platform_service.base import PlatformService
from mindweaver.crypto import encrypt_password, decrypt_password
from mindweaver.fw.model import ts_now
from mindweaver.platform_service.pgsql.service import PgSqlPlatformService

from .model import HiveMetastorePlatform, HiveMetastorePlatformState
from .state import HiveMetastoreState

logger = logging.getLogger(__name__)


class HiveMetastorePlatformService(PlatformService[HiveMetastorePlatform]):
    template_directory: str = os.path.join(os.path.dirname(__file__), "templates")
    state_model: type[HiveMetastorePlatformState] = HiveMetastorePlatformState

    @classmethod
    def model_class(cls) -> type[HiveMetastorePlatform]:
        return HiveMetastorePlatform

    @classmethod
    def service_path(cls) -> str:
        return "/platform/hive-metastore"

    @classmethod
    def widgets(cls) -> dict[str, Any]:
        return {
            "image": {"order": 5},
            "replica_count": {"order": 10, "type": "range", "min": 1, "max": 10, "step": 1},
            "cpu_request": {"order": 11, "type": "range", "min": 0.1, "max": 16, "step": 0.1},
            "cpu_limit": {"order": 12, "type": "range", "min": 0.1, "max": 16, "step": 0.1},
            "mem_request": {"order": 13, "type": "range", "min": 0.5, "max": 64, "step": 0.5, "label": "Memory Request (Gi)"},
            "mem_limit": {"order": 14, "type": "range", "min": 0.5, "max": 64, "step": 0.5, "label": "Memory Limit (Gi)"},
            "database_id": {"order": 20, "label": "PostgreSQL"},
            "iceberg_enabled": {"order": 30, "type": "boolean"},
            "iceberg_port": {"order": 31},
        }

    async def template_vars(self, model: HiveMetastorePlatform) -> dict:
        vars = model.model_dump()
        vars["namespace"] = await self._resolve_namespace(model)

        # Resolve Database Connection
        pgsql_svc = await PgSqlPlatformService.get_service(self.request, self.session)
        pgsql_model = await pgsql_svc.get(model.database_id)
        pgsql_state = await pgsql_svc.platform_state(pgsql_model)

        if not pgsql_state or not pgsql_state.active:
            raise ValueError(f"Managed PostgreSQL cluster {pgsql_model.name} is not active")

        vars["db_host"] = f"{pgsql_model.name}-rw.{vars['namespace']}.svc.cluster.local"
        vars["db_port"] = 5432
        vars["db_user"] = pgsql_state.db_user
        vars["db_name"] = pgsql_state.db_name
        if pgsql_state.db_pass:
            try:
                vars["db_pass"] = decrypt_password(pgsql_state.db_pass)
            except Exception:
                vars["db_pass"] = pgsql_state.db_pass

        return vars

    async def validate_data(self, data: Any) -> Any:
        try:
            self.model_class().model_validate(data.model_dump(), from_attributes=True)
        except ValidationError as e:
            error = e.errors()[0]
            raise FieldValidationError(field_location=list(error["loc"]), message=error["msg"])

        return await super().validate_data(data)

    async def poll_status(self, model: HiveMetastorePlatform):
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
            apps_v1 = client.AppsV1Api(k8s_client)
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
                sync_status = argo_app.get("status", {}).get("sync", {}).get("status", "Unknown")
                health_status = argo_app.get("status", {}).get("health", {}).get("status", "Unknown")
                
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
                    label_selector=f"app.kubernetes.io/instance={model.name}"
                )
                ready_pods = sum(1 for p in pods.items if p.status.phase == "Running" and any(c.ready for c in (p.status.container_statuses or [])))
                total_pods = len(pods.items)
                message += f" | Pods: {ready_pods}/{total_pods}"
            except Exception as e:
                logger.error(f"Failed to fetch pods for {model.name}: {e}")

            # 3. Fetch NodePorts
            node_ports = []
            try:
                services = core_v1.list_namespaced_service(namespace=namespace)
                for svc in services.items:
                    if svc.metadata.name.startswith(model.name):
                        if svc.spec.type == "NodePort":
                            for port in svc.spec.ports:
                                node_ports.append({
                                    "name": svc.metadata.name,
                                    "port": port.port,
                                    "node_port": port.node_port,
                                })
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

            return status, message, argo_app.get("status", {}), node_ports, cluster_nodes

        status, message, extra_data, node_ports, cluster_nodes = await asyncio.to_thread(_poll, is_active)

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

        # Derive URIs
        if status == "online" and cluster_nodes:
            # HMS Port (9083) usually ClusterIP, but if NodePort exists we can show it
            hms_np = next((np for np in node_ports if "hms" in np["name"]), None)
            if hms_np:
                state.hms_uri = f"thrift://{cluster_nodes[0]['ipv4']}:{hms_np['node_port']}"
            else:
                state.hms_uri = f"thrift://{model.name}.{namespace}.svc.cluster.local:9083"

            if model.iceberg_enabled:
                ice_np = next((np for np in node_ports if "iceberg" in np["name"]), None)
                if ice_np:
                    state.iceberg_uri = f"http://{cluster_nodes[0]['ipv4']}:{ice_np['node_port']}"
                else:
                    state.iceberg_uri = f"http://{model.name}-iceberg.{namespace}.svc.cluster.local:{model.iceberg_port}"

        state.last_heartbeat = ts_now()


HiveMetastorePlatformService.with_state()(HiveMetastoreState)
router = HiveMetastorePlatformService.router()
