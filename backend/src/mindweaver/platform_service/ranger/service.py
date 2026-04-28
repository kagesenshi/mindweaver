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
from mindweaver.platform_service.pgsql.service import PgSqlPlatformService
from mindweaver.service.s3_storage.service import S3StorageService

from .model import RangerPlatform, RangerPlatformState

logger = logging.getLogger(__name__)


class RangerPlatformService(PlatformService[RangerPlatform]):
    template_directory: str = os.path.join(os.path.dirname(__file__), "templates")
    state_model: type[RangerPlatformState] = RangerPlatformState

    @classmethod
    def model_class(cls) -> type[RangerPlatform]:
        return RangerPlatform

    @classmethod
    def service_path(cls) -> str:
        return "/platform/ranger"

    @classmethod
    def redacted_fields(cls) -> list[str]:
        return super().redacted_fields() + [
            "admin_password",
            "keyadmin_password",
            "tagsync_password",
            "usersync_password",
        ]

    @classmethod
    def internal_fields(cls) -> list[str]:
        return super().internal_fields() + [
            "admin_password",
            "keyadmin_password",
            "tagsync_password",
            "usersync_password",
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
            "replica_count": {
                "order": 10,
                "type": "range",
                "min": 1,
                "max": 10,
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
            "database_id": {"order": 20, "label": "PostgreSQL"},
            "s3_storage_id": {
                "order": 21,
                "label": "S3 Storage (Audit)",
            },
            "audit_s3_uri": {
                "order": 22,
                "label": "Audit S3 Location",
                "type": "s3-path",
                "storage_field": "s3_storage_id",
            },
            "additional_properties": {
                "order": 100,
                "label": "Additional Properties",
                "type": "key-value",
            },
        }

    @before_create(before="_handle_redacted_create")
    async def generate_passwords(self, model: RangerPlatform):
        """Autogenerate random passwords for Ranger components."""
        model.admin_password = generate_password()
        model.keyadmin_password = generate_password()
        model.tagsync_password = generate_password()
        model.usersync_password = generate_password()

    async def template_vars(self, model: RangerPlatform) -> dict:
        vars = model.model_dump()
        vars["namespace"] = await self._resolve_namespace(model)

        # Resolve Database Connection
        pgsql_svc = await PgSqlPlatformService.get_service(self.request, self.session)
        pgsql_model = await pgsql_svc.get(model.database_id)
        pgsql_state = await pgsql_svc.platform_state(pgsql_model)

        if not pgsql_state or not pgsql_state.active:
            raise ValueError(
                f"Managed PostgreSQL cluster {pgsql_model.name} is not active"
            )

        vars["db_host"] = (
            f"{pgsql_model.name}-pooler-rw.{vars['namespace']}.svc.cluster.local"
        )
        vars["db_port"] = 5432
        vars["db_user"] = pgsql_state.db_user
        vars["db_name"] = pgsql_state.db_name
        if pgsql_state.db_pass:
            try:
                vars["db_pass"] = decrypt_password(pgsql_state.db_pass)
            except Exception:
                vars["db_pass"] = pgsql_state.db_pass

        # Resolve S3 Storage Connection for Audits
        if model.s3_storage_id:
            s3_svc = await S3StorageService.get_service(self.request, self.session)
            s3_model = await s3_svc.get(model.s3_storage_id)
            vars["s3_endpoint_url"] = s3_model.endpoint_url
            vars["s3_region"] = s3_model.region
            vars["aws_access_key_id"] = s3_model.access_key
            if s3_model.secret_key:
                try:
                    vars["aws_secret_access_key"] = decrypt_password(
                        s3_model.secret_key
                    )
                except Exception:
                    vars["aws_secret_access_key"] = s3_model.secret_key
            else:
                vars["aws_secret_access_key"] = ""
            
        # Set DB root user/pass to be the same as db_user/pass for managed DBs
        vars["db_root_user"] = vars.get("db_user")
        vars["db_root_pass"] = vars.get("db_pass")

        # Parse audit_s3_uri to construct s3a:// URI for Ranger
        # Format: s3://bucket/path -> s3a://bucket/path
        uri = model.audit_s3_uri or "s3://ranger/audit"
        if uri.startswith("s3://"):
            s3a_uri = "s3a://" + uri[5:]
        else:
            s3a_uri = uri
        
        vars["audit_hdfs_dest_dir"] = f"{s3a_uri}/{model.name}"

        # Decrypt passwords
        for pwd_field in ["admin_password", "keyadmin_password", "tagsync_password", "usersync_password"]:
            pwd_val = getattr(model, pwd_field)
            if pwd_val:
                try:
                    vars[pwd_field] = decrypt_password(pwd_val)
                except Exception:
                    vars[pwd_field] = pwd_val

        return vars

    async def poll_status(self, model: RangerPlatform):
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
                    if svc.metadata.name == model.name:
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

        # Derive Ranger URL
        if status == "online" and cluster_nodes:
            ranger_np = next((np for np in node_ports if np["port"] == 6080), None)
            if ranger_np:
                state.ranger_url = (
                    f"http://{cluster_nodes[0]['ipv4']}:{ranger_np['node_port']}"
                )
            else:
                state.ranger_url = f"http://{model.name}.{namespace}.svc.cluster.local:6080"

        # Populating passwords for UI display
        state.admin_password = model.admin_password
        state.keyadmin_password = model.keyadmin_password
        state.tagsync_password = model.tagsync_password
        state.usersync_password = model.usersync_password
        state.last_heartbeat = ts_now()

        await self.session.flush()


