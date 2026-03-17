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
from mindweaver.fw.model import ts_now
from mindweaver.platform_service.pgsql.service import PgSqlPlatformService
from mindweaver.service.ldap_config.service import LdapConfigService
from mindweaver.datasource_service import DatabaseSourceService
from mindweaver.platform_service.trino.service import TrinoPlatformService
from mindweaver.crypto import decrypt_password

from .model import SupersetPlatform, SupersetPlatformState

logger = logging.getLogger(__name__)


class SupersetPlatformService(PlatformService[SupersetPlatform]):
    template_directory: str = os.path.join(os.path.dirname(__file__), "templates")
    state_model: type[SupersetPlatformState] = SupersetPlatformState

    @classmethod
    def model_class(cls) -> type[SupersetPlatform]:
        return SupersetPlatform

    @classmethod
    def service_path(cls) -> str:
        return "/platform/superset"

    @classmethod
    def internal_fields(cls) -> list[str]:
        return super().internal_fields() + ["admin_password", "superset_secret_key"]

    @classmethod
    def redacted_fields(cls) -> list[str]:
        return ["admin_password", "superset_secret_key"]

    @classmethod
    def widgets(cls) -> dict[str, Any]:
        return {
            "chart_version": {
                "order": 5,
                "label": "Chart Version",
                "type": "select",
                # Need to implement _chart-versions view if we want dynamic list
                "options": [
                    {"label": "0.15.0", "value": "0.15.0"},
                ],
            },
            "override_image": {
                "order": 6,
                "label": "Override Image",
                "type": "boolean",
            },
            "image": {
                "order": 7,
                "label": "Custom Image",
                "type": "string",
            },
            "platform_pgsql_id": {
                "order": 10,
                "label": "PostgreSQL Metadata DB",
                "type": "relationship",
                "endpoint": "/api/v1/platform/pgsql",
                "field": "id",
            },
            "ldap_config_id": {
                "order": 11,
                "label": "LDAP Configuration",
                "type": "relationship",
                "endpoint": "/api/v1/ldap_configs",
                "field": "id",
            },
            "database_source_ids": {
                "order": 20,
                "label": "Database Sources",
                "type": "relationship",
                "endpoint": "/api/v1/database-sources",
                "field": "id",
                "multiselect": True,
            },
            "trino_ids": {
                "order": 21,
                "label": "Trino Platforms",
                "type": "relationship",
                "endpoint": "/api/v1/platform/trino",
                "field": "id",
                "multiselect": True,
            },
            "cpu_request": {
                "order": 30,
                "type": "range",
                "min": 0.1,
                "max": 8,
                "step": 0.1,
            },
            "cpu_limit": {
                "order": 31,
                "type": "range",
                "min": 0.1,
                "max": 16,
                "step": 0.1,
            },
            "mem_request": {
                "order": 32,
                "type": "range",
                "min": 0.5,
                "max": 32,
                "step": 0.5,
                "label": "Memory Request (Gi)",
            },
            "mem_limit": {
                "order": 33,
                "type": "range",
                "min": 0.5,
                "max": 64,
                "step": 0.5,
                "label": "Memory Limit (Gi)",
            },
            "auth_role_mapping": {
                "order": 25,
                "label": "Auth Role Mapping",
                "type": "auth-role-mapping",
                "roles": ["Admin", "Alpha", "Gamma", "sql_lab", "Public"],
            },
        }

    async def template_vars(self, model: SupersetPlatform) -> dict:
        vars = model.model_dump()
        vars["namespace"] = await self._resolve_namespace(model)

        # 0. Decrypt internal secrets
        for field in self.redacted_fields():
            val = getattr(model, field, None)
            if val:
                try:
                    vars[field] = decrypt_password(val)
                except Exception:
                    vars[field] = val

        # 1. Resolve PostgreSQL
        pgsql_svc = await PgSqlPlatformService.get_service(self.request, self.session)
        pgsql_model = await pgsql_svc.get(model.platform_pgsql_id)
        pgsql_state = await pgsql_svc.platform_state(pgsql_model)

        if not pgsql_state or not pgsql_state.active:
            raise ValueError(f"Selected PostgreSQL {pgsql_model.name} is not active")

        # 1.1 Determine Host and Port
        # Prefer pgbouncer if host is available in extra_data
        vars["db_host"] = pgsql_state.extra_data.get("pgbouncer_host")
        if vars["db_host"]:
            vars["db_port"] = 5432  # Default pgbouncer port in our templates
        else:
            # Fallback to direct cluster service
            pgsql_ns = await pgsql_svc._resolve_namespace(pgsql_model)
            vars["db_host"] = f"{pgsql_model.name}-rw.{pgsql_ns}.svc.cluster.local"
            vars["db_port"] = 5432

        # 1.2 Credentials
        vars["db_user"] = pgsql_state.db_user or "app"
        vars["db_name"] = pgsql_state.db_name or "app"

        db_pass_enc = pgsql_state.db_pass or ""
        if db_pass_enc:
            try:
                vars["db_pass"] = decrypt_password(db_pass_enc)
            except Exception:
                vars["db_pass"] = db_pass_enc
        else:
            vars["db_pass"] = ""

        # 2. Resolve LDAP
        if model.ldap_config_id:
            ldap_svc = await LdapConfigService.get_service(self.request, self.session)
            ldap_config = await ldap_svc.get(model.ldap_config_id)
            vars["ldap"] = ldap_config.model_dump()
            if ldap_config.bind_password:
                try:
                    vars["ldap"]["bind_password"] = decrypt_password(
                        ldap_config.bind_password
                    )
                except Exception:
                    vars["ldap"]["bind_password"] = ldap_config.bind_password

        # 3. Resolve Data Sources
        datasources = []
        if model.database_source_ids:
            ds_svc = await DatabaseSourceService.get_service(self.request, self.session)
            for ds_id in model.database_source_ids:
                ds = await ds_svc.get(ds_id)
                engine = ds.engine
                if engine == "postgresql":
                    engine = "postgresql+asyncpg"
                sqlalchemy_uri = f"{engine}://{ds.login}:{decrypt_password(ds.password) if ds.password else ''}@{ds.host}:{ds.port}/{ds.database}"
                datasources.append(
                    {
                        "database_name": ds.name,
                        "sqlalchemy_uri": sqlalchemy_uri,
                        "expose_in_sqllab": True,
                    }
                )

        if model.trino_ids:
            trino_svc = await TrinoPlatformService.get_service(
                self.request, self.session
            )
            for trino_id in model.trino_ids:
                trino_model = await trino_svc.get(trino_id)
                trino_state = await trino_svc.platform_state(trino_model)
                if trino_state and trino_state.active:
                    # Use internal URI for Superset -> Trino communication
                    trino_namespace = await trino_svc._resolve_namespace(trino_model)
                    sqlalchemy_uri = f"trino://admin@{trino_model.name}.{trino_namespace}.svc.cluster.local:8443/"
                    datasources.append(
                        {
                            "database_name": trino_model.name,
                            "sqlalchemy_uri": sqlalchemy_uri,
                            "expose_in_sqllab": True,
                        }
                    )

        vars["datasources"] = datasources

        # 4. Handle custom image
        vars["override_image"] = model.override_image
        vars["image"] = model.image

        # 5. Merge auth_role_mapping by entity
        merged_mapping = {}
        for m in model.auth_role_mapping:
            # Handle both object and dict for resilience
            entity = getattr(m, "entity", None) or (m.get("entity") if isinstance(m, dict) else None)
            role = getattr(m, "role", None) or (m.get("role") if isinstance(m, dict) else None)
            
            if not entity or not role:
                continue

            if entity not in merged_mapping:
                merged_mapping[entity] = []
            if role not in merged_mapping[entity]:
                merged_mapping[entity].append(role)
        vars["auth_role_mapping"] = merged_mapping

        return vars

    async def poll_status(self, model: SupersetPlatform):
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

            # 3. Fetch NodePorts (for Superset UI)
            node_ports = []
            try:
                services = core_v1.list_namespaced_service(namespace=namespace)
                for svc in services.items:
                    if svc.metadata.name.startswith(model.name):
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

        # Populate admin credentials
        state.admin_user = "admin"
        state.admin_password = decrypt_password(model.admin_password)

        # Derive Superset URI
        if status == "online" and cluster_nodes:
            superset_np = next(
                (np for np in node_ports if np["name"] == model.name), None
            )
            if superset_np:
                # Find first node with IPv4
                node_v4 = next((n for n in cluster_nodes if n["ipv4"]), None)
                if node_v4:
                    state.superset_uri = (
                        f"http://{node_v4['ipv4']}:{superset_np['node_port']}"
                    )

                # Find first node with IPv6
                node_v6 = next((n for n in cluster_nodes if n["ipv6"]), None)
                if node_v6:
                    state.superset_uri_ipv6 = (
                        f"http://[{node_v6['ipv6']}]:{superset_np['node_port']}"
                    )
            else:
                state.superset_uri = (
                    f"http://{model.name}.{namespace}.svc.cluster.local:8088"
                )

        state.last_heartbeat = ts_now()
