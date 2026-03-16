# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import os
import secrets
import logging
import asyncio
import tempfile
from typing import Any, Optional
from kubernetes import client, config
from pydantic import ValidationError

from mindweaver.fw.exc import FieldValidationError
from mindweaver.fw.service import before_create
from mindweaver.platform_service.base import PlatformService
from mindweaver.fw.model import ts_now
from mindweaver.platform_service.hive_metastore.service import (
    HiveMetastorePlatformService,
)
from mindweaver.datasource_service import DatabaseSourceService
from mindweaver.service.s3_storage.service import S3StorageService
from mindweaver.service.ldap_config.service import LdapConfigService
from mindweaver.crypto import decrypt_password

from .model import TrinoPlatform, TrinoPlatformState

logger = logging.getLogger(__name__)


class TrinoPlatformService(PlatformService[TrinoPlatform]):
    template_directory: str = os.path.join(os.path.dirname(__file__), "templates")
    state_model: type[TrinoPlatformState] = TrinoPlatformState
    SUPPORTED_CATALOG_DRIVERS = ["postgresql", "mysql", "trino"]

    @classmethod
    def model_class(cls) -> type[TrinoPlatform]:
        return TrinoPlatform

    @classmethod
    def service_path(cls) -> str:
        return "/platform/trino"

    @classmethod
    def redacted_fields(cls) -> list[str]:
        return ["internal_shared_secret"]

    @classmethod
    def widgets(cls) -> dict[str, Any]:
        return {
            "chart_version": {
                "order": 6,
                "label": "Chart Version",
                "type": "select",
                "endpoint": f"{cls.service_path()}/_chart-versions",
            },
            "override_image": {
                "order": 7,
                "label": "Override Image",
                "type": "boolean",
            },
            "image": {"order": 8},
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
            "hms_ids": {
                "order": 20,
                "label": "Hive Metastores",
                "type": "relationship",
                "endpoint": "/api/v1/platform/hive-metastore",
                "field": "id",
                "multiselect": True,
            },
            "hms_iceberg_ids": {
                "order": 21,
                "label": "Iceberg (HMS-backed) Catalogs",
                "type": "relationship",
                "endpoint": "/api/v1/platform/hive-metastore",
                "field": "id",
                "multiselect": True,
            },
            "database_source_ids": {
                "order": 22,
                "label": "Database Sources",
                "type": "relationship",
                "endpoint": "/api/v1/database-sources",
                "field": "id",
                "multiselect": True,
            },
            "ldap_config_id": {
                "order": 30,
                "label": "LDAP Configuration",
                "type": "relationship",
                "endpoint": "/api/v1/ldap_configs",
                "field": "id",
            },
        }

    async def get_preferred_catalog(self, model: TrinoPlatform) -> Optional[str]:
        """
        Determines the preferred catalog for CLI examples.
        Priority: Iceberg > Hive > Data Source
        """
        if model.hms_iceberg_ids:
            hms_svc = await HiveMetastorePlatformService.get_service(
                self.request, self.session
            )
            hms_model = await hms_svc.get(model.hms_iceberg_ids[0])
            return hms_model.name

        if model.hms_ids:
            hms_svc = await HiveMetastorePlatformService.get_service(
                self.request, self.session
            )
            hms_model = await hms_svc.get(model.hms_ids[0])
            return hms_model.name

        if model.database_source_ids:
            ds_svc = await DatabaseSourceService.get_service(self.request, self.session)
            ds_model = await ds_svc.get(model.database_source_ids[0])
            return ds_model.name

        return None

    async def template_vars(self, model: TrinoPlatform) -> dict:
        vars = model.model_dump(exclude=self.redacted_fields())
        vars["namespace"] = await self._resolve_namespace(model)

        # HTTPS is mandatory
        vars["enable_https"] = True

        if model.internal_shared_secret:
            try:
                vars["internal_shared_secret"] = decrypt_password(
                    model.internal_shared_secret
                )
            except Exception:
                vars["internal_shared_secret"] = model.internal_shared_secret

        # 1. Resolve HMS and Data Sources Catalogs
        catalogs = []
        if model.hms_ids:
            hms_svc = await HiveMetastorePlatformService.get_service(
                self.request, self.session
            )
            for hms_id in model.hms_ids:
                hms_model = await hms_svc.get(hms_id)
                hms_state = await hms_svc.platform_state(hms_model)

                if not hms_state or not hms_state.active:
                    raise ValueError(
                        f"Managed Hive Metastore {hms_model.name} is not active"
                    )

                hms_namespace = await hms_svc._resolve_namespace(hms_model)
                hms_uri = (
                    hms_state.hms_uri
                    or f"thrift://{hms_model.name}.{hms_namespace}.svc.cluster.local:9083"
                )

                catalog = {
                    "catalog": hms_model.name,
                    "properties": {
                        "connector.name": "hive",
                        "hive.metastore.uri": hms_uri,
                    },
                }

                if hms_model.s3_storage_id:
                    s3_svc = await S3StorageService.get_service(
                        self.request, self.session
                    )
                    s3_model = await s3_svc.get(hms_model.s3_storage_id)
                    catalog["properties"]["fs.native-s3.enabled"] = "true"
                    catalog["properties"]["s3.endpoint"] = s3_model.endpoint_url

                    # Default region to us-east-1 if empty or if endpoint_url is set (local)
                    s3_region = s3_model.region
                    if not s3_region or not s3_region.strip() or s3_model.endpoint_url:
                        s3_region = "us-east-1"
                    catalog["properties"]["s3.region"] = s3_region

                    catalog["properties"]["s3.aws-access-key"] = s3_model.access_key
                    if s3_model.secret_key:
                        try:
                            catalog["properties"]["s3.aws-secret-key"] = (
                                decrypt_password(s3_model.secret_key)
                            )
                        except Exception:
                            catalog["properties"][
                                "s3.aws-secret-key"
                            ] = s3_model.secret_key
                    catalog["properties"]["s3.path-style-access"] = "true"

                catalogs.append(catalog)

        if model.hms_iceberg_ids:
            hms_svc = await HiveMetastorePlatformService.get_service(
                self.request, self.session
            )
            for hms_id in model.hms_iceberg_ids:
                hms_model = await hms_svc.get(hms_id)
                hms_state = await hms_svc.platform_state(hms_model)

                if not hms_state or not hms_state.active:
                    raise ValueError(
                        f"Managed Hive Metastore {hms_model.name} is not active"
                    )

                hms_namespace = await hms_svc._resolve_namespace(hms_model)
                hms_uri = (
                    hms_state.hms_uri
                    or f"thrift://{hms_model.name}.{hms_namespace}.svc.cluster.local:9083"
                )

                catalog = {
                    "catalog": hms_model.name,
                    "properties": {
                        "connector.name": "iceberg",
                        "hive.metastore.uri": hms_uri,
                    },
                }

                if hms_model.s3_storage_id:
                    s3_svc = await S3StorageService.get_service(
                        self.request, self.session
                    )
                    s3_model = await s3_svc.get(hms_model.s3_storage_id)
                    catalog["properties"]["fs.native-s3.enabled"] = "true"
                    catalog["properties"]["s3.endpoint"] = s3_model.endpoint_url

                    # Default region to us-east-1 if empty or if endpoint_url is set (local)
                    s3_region = s3_model.region
                    if not s3_region or not s3_region.strip() or s3_model.endpoint_url:
                        s3_region = "us-east-1"
                    catalog["properties"]["s3.region"] = s3_region

                    catalog["properties"]["s3.aws-access-key"] = s3_model.access_key
                    if s3_model.secret_key:
                        try:
                            catalog["properties"]["s3.aws-secret-key"] = (
                                decrypt_password(s3_model.secret_key)
                            )
                        except Exception:
                            catalog["properties"][
                                "s3.aws-secret-key"
                            ] = s3_model.secret_key
                    catalog["properties"]["s3.path-style-access"] = "true"

                catalogs.append(catalog)

        # 2. Resolve Database Sources
        if model.database_source_ids:
            ds_svc = await DatabaseSourceService.get_service(self.request, self.session)
            for ds_id in model.database_source_ids:
                ds = await ds_svc.get(ds_id)

                # Default mapping of engines to trino catalog connectors
                # Some typical ones: postgresql -> postgresql, mysql -> mysql
                connector_name = ds.engine

                catalog = {
                    "catalog": ds.name,
                    "properties": {
                        "connector.name": connector_name,
                    },
                }

                # Common properties
                jdbc_prefix = f"jdbc:{ds.engine}://"
                host_port = f"{ds.host}" + (f":{ds.port}" if ds.port else "")
                resource_path = f"/{ds.database}" if ds.database else ""

                if ds.engine in ("postgresql", "mysql"):
                    catalog["properties"][
                        "connection-url"
                    ] = f"{jdbc_prefix}{host_port}{resource_path}"
                    if ds.login:
                        catalog["properties"]["connection-user"] = ds.login
                    if ds.password:
                        try:
                            decrypted = decrypt_password(ds.password)
                            catalog["properties"]["connection-password"] = decrypted
                        except Exception:
                            catalog["properties"]["connection-password"] = ds.password

                # Extend with additional driver parameters
                for param, pval in ds.parameters.items():
                    catalog["properties"][param] = str(pval)

                catalogs.append(catalog)

        vars["catalogs"] = catalogs

        # 3. Resolve LDAP Configuration
        if model.ldap_config_id:
            ldap_svc = await LdapConfigService.get_service(self.request, self.session)
            ldap_config = await ldap_svc.get(model.ldap_config_id)

            ldap_props = {
                "ldap.url": ldap_config.server_url,
                "ldap.allow-insecure": (
                    "true" if not ldap_config.verify_ssl else "false"
                ),
            }

            if ldap_config.bind_dn:
                ldap_props["ldap.bind-dn"] = ldap_config.bind_dn
                if ldap_config.bind_password:
                    try:
                        ldap_props["ldap.bind-password"] = decrypt_password(
                            ldap_config.bind_password
                        )
                    except Exception:
                        ldap_props["ldap.bind-password"] = ldap_config.bind_password

                ldap_props["ldap.user-base-dn"] = ldap_config.user_search_base
                ldap_props["ldap.group-auth-pattern"] = (
                    ldap_config.user_search_filter.replace("{0}", "${USER}")
                )
            else:
                # Direct bind fallback
                # Trino direct bind usually expects a pattern that evaluates to the full DN
                # If we only have base and filter, we can try to guess or use a pattern if provided
                # For now we use the filter as the basis but Trino direct bind name is user-bind-pattern
                dn_pattern = f"{ldap_config.username_attr}=${{USER}},{ldap_config.user_search_base}"
                ldap_props["ldap.user-bind-pattern"] = dn_pattern

            vars["ldap"] = ldap_props

        vars["preferred_catalog"] = await self.get_preferred_catalog(model)

        return vars

    async def validate_data(self, data: Any) -> Any:
        try:
            self.model_class().model_validate(data.model_dump(), from_attributes=True)
        except ValidationError as e:
            error = e.errors()[0]
            raise FieldValidationError(
                field_location=list(error["loc"]), message=error["msg"]
            )

        return await super().validate_data(data)

    async def poll_status(self, model: TrinoPlatform):
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

            # 3. Fetch NodePorts
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
        extra_data["preferred_catalog"] = await self.get_preferred_catalog(model)
        state.extra_data = extra_data
        state.node_ports = node_ports
        state.cluster_nodes = cluster_nodes

        # Derive URIs
        if status == "online" and cluster_nodes:
            trino_np = next(
                (
                    np
                    for np in node_ports
                    if np["name"] == f"{model.name}-https-nodeport"
                ),
                None,
            )
            scheme = "https"
            if trino_np:
                state.trino_uri = (
                    f"{scheme}://{cluster_nodes[0]['ipv4']}:{trino_np['node_port']}"
                )
            else:
                port = 8443
                state.trino_uri = (
                    f"{scheme}://{model.name}.{namespace}.svc.cluster.local:{port}"
                )

        state.last_heartbeat = ts_now()
