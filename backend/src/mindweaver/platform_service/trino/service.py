# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import os
import httpx
import bcrypt
import secrets
import logging
import asyncio
import tempfile
from typing import Any, Optional, Literal
from kubernetes import client, config
from pydantic import ValidationError

from mindweaver.fw.exc import FieldValidationError
from mindweaver.fw.service import before_create, before_delete, VALIDATION_MODE
from mindweaver.platform_service.base import PlatformService
from mindweaver.fw.model import ts_now
from mindweaver.platform_service.hive_metastore.service import (
    HiveMetastorePlatformService,
)
from mindweaver.datasource_service import DatabaseSourceService
from mindweaver.service.s3_storage.service import S3StorageService
from mindweaver.service.ldap_config.service import LdapConfigService
from mindweaver.platform_service.ranger.service import RangerPlatformService
from mindweaver.platform_service.opensearch.service import OpenSearchPlatformService
from mindweaver.crypto import decrypt_password
from mindweaver.fw.util import generate_password

from .model import TrinoPlatform, TrinoPlatformState

logger = logging.getLogger(__name__)


class TrinoPlatformService(PlatformService[TrinoPlatform]):
    template_directory: str = os.path.join(os.path.dirname(__file__), "templates")
    state_model: type[TrinoPlatformState] = TrinoPlatformState
    SUPPORTED_CATALOG_DRIVERS = ["postgresql", "mysql", "trino", "mssql"]

    @classmethod
    def model_class(cls) -> type[TrinoPlatform]:
        return TrinoPlatform

    @classmethod
    def service_path(cls) -> str:
        return "/platform/trino"

    @classmethod
    def internal_fields(cls) -> list[str]:
        return super().internal_fields() + ["internal_shared_secret", "ranger_user_password"]

    @classmethod
    def redacted_fields(cls) -> list[str]:
        return ["internal_shared_secret", "ranger_user_password"]

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
            "process_forwarded": {
                "order": 9,
                "label": "Process X-Forwarded Headers",
                "type": "boolean",
            },
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
            "database_source_ids": {
                "order": 22,
                "label": "Database Sources",
                "type": "relationship",
                "endpoint": "/api/v1/database-sources",
                "field": "id",
                "multiselect": True,
            },
            "ranger_id": {
                "order": 25,
                "label": "Ranger",
                "type": "relationship",
                "endpoint": "/api/v1/platform/ranger",
                "field": "id",
            },
        }

    @before_create(before="_handle_redacted_create")
    async def generate_passwords(self, model: TrinoPlatform):
        """Autogenerate a strong random password for Ranger user to query Trino."""
        if not model.ranger_user_password:
            model.ranger_user_password = generate_password()

    async def get_preferred_catalog(self, model: TrinoPlatform) -> Optional[str]:
        """
        Determines the preferred catalog for CLI examples.
        Priority: Hive/Iceberg (Lakehouse) > Data Source
        """
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
                        "connector.name": "lakehouse",
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
                connector_name = "sqlserver" if ds.engine == "mssql" else ds.engine

                catalog = {
                    "catalog": ds.name,
                    "properties": {
                        "connector.name": connector_name,
                    },
                }

                # Common properties
                if ds.engine == "mssql":
                    jdbc_prefix = "jdbc:sqlserver://"
                    resource_path = f";databaseName={ds.database}" if ds.database else ""
                    encrypt = "true" if ds.enable_ssl else "false"
                    trust_cert = "false" if ds.verify_ssl else "true"
                    resource_path += f";encrypt={encrypt};trustServerCertificate={trust_cert}"
                else:
                    jdbc_prefix = f"jdbc:{ds.engine}://"
                    resource_path = f"/{ds.database}" if ds.database else ""

                host_port = f"{ds.host}" + (f":{ds.port}" if ds.port else "")

                if ds.engine in ("postgresql", "mysql", "mssql"):
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
                    if param.startswith("trino."):
                        catalog["properties"][param.replace("trino.", "", 1)] = str(
                            pval
                        )
                    else:
                        catalog["properties"][param] = str(pval)

                catalogs.append(catalog)

        vars["catalogs"] = catalogs

        # 3. Resolve LDAP Configuration from Project
        project = await self.project(model)
        if project.ldap_config_id:
            ldap_svc = await LdapConfigService.get_service(self.request, self.session)
            ldap_config = await ldap_svc.get(project.ldap_config_id)

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

        # 4. Resolve Ranger Configuration
        if model.ranger_id:
            ranger_svc = await RangerPlatformService.get_service(self.request, self.session)
            ranger_model = await ranger_svc.get(model.ranger_id)
            ranger_state = await ranger_svc.platform_state(ranger_model)

            ranger_ns = await ranger_svc._resolve_namespace(ranger_model)
            ranger_url = f"https://{ranger_model.name}.{ranger_ns}.svc.cluster.local:6080"

            vars["ranger_enabled"] = True
            vars["ranger_url"] = ranger_url
            vars["ranger_service_name"] = model.name

            # OpenSearch auditing config resolution
            if ranger_model.opensearch_id:
                opensearch_svc = await OpenSearchPlatformService.get_service(self.request, self.session)
                opensearch_model = await opensearch_svc.get(ranger_model.opensearch_id)
                opensearch_state = await opensearch_svc.platform_state(opensearch_model)

                if not opensearch_state or not opensearch_state.active:
                    raise ValueError(
                        f"Managed OpenSearch cluster {opensearch_model.name} is not active"
                    )

                opensearch_ns = await opensearch_svc._resolve_namespace(opensearch_model)
                vars["ranger_opensearch_enabled"] = "true"
                vars["ranger_opensearch_host"] = OpenSearchPlatformService.get_internal_host(
                    opensearch_model, opensearch_state, opensearch_ns
                )
                
                opensearch_url = opensearch_state.opensearch_url or ""
                vars["ranger_opensearch_protocol"] = "http" if opensearch_url.startswith("http://") else "https"
                
                opensearch_pass = ""
                if opensearch_state.admin_password:
                    try:
                        opensearch_pass = decrypt_password(opensearch_state.admin_password)
                    except Exception:
                        opensearch_pass = opensearch_state.admin_password
                vars["ranger_opensearch_password"] = opensearch_pass
            else:
                vars["ranger_opensearch_enabled"] = "false"

            # S3 auditing config resolution
            vars["ranger_audit_s3_enabled"] = "false"
        else:
            vars["ranger_enabled"] = False

        # Resolve password authenticators list (LDAP first, then file/local)
        auth_files = []
        if vars.get("ldap"):
            auth_files.append("/etc/trino/ldap.properties")
        if model.ranger_id:
            auth_files.append("/etc/trino/file.properties")
            
            ranger_pass = ""
            if model.ranger_user_password:
                try:
                    ranger_pass = decrypt_password(model.ranger_user_password)
                except Exception:
                    ranger_pass = model.ranger_user_password
            if not ranger_pass:
                ranger_pass = "ranger"
                
            hashed = bcrypt.hashpw(ranger_pass.encode("utf-8"), bcrypt.gensalt(10))
            hashed_str = hashed.decode("utf-8")
            if hashed_str.startswith("$2b$"):
                hashed_str = "$2y$" + hashed_str[4:]
            vars["ranger_trino_password_hash"] = hashed_str

        if auth_files:
            vars["password_authenticator_config_files"] = ",".join(auth_files)

        vars["preferred_catalog"] = await self.get_preferred_catalog(model)

        return vars


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

    async def deploy(self, model: TrinoPlatform):
        """
        Deploys/upgrades the Trino service and automatically creates
        the corresponding service definition in Ranger if linked.
        """
        await super().deploy(model)
        await self._manage_ranger_service(model, "create")

    @before_delete()
    async def delete_ranger_service_on_delete(self, model: TrinoPlatform):
        """
        Deletes the corresponding service definition in Ranger when the Trino platform is deleted.
        """
        await self._manage_ranger_service(model, "delete")

    async def _manage_ranger_service(self, model: TrinoPlatform, action: str):
        """
        Create or delete a Ranger service definition for the Trino instance.
        """
        if not model.ranger_id:
            return

        try:
            ranger_svc = await RangerPlatformService.get_service(self.request, self.session)
            ranger_model = await ranger_svc.get(model.ranger_id)
            ranger_ns = await ranger_svc._resolve_namespace(ranger_model)
            ranger_url = f"https://{ranger_model.name}.{ranger_ns}.svc.cluster.local:6080"
            
            admin_password = ""
            if ranger_model.admin_password:
                try:
                    admin_password = decrypt_password(ranger_model.admin_password)
                except Exception:
                    admin_password = ranger_model.admin_password

            auth = ("admin", admin_password)
            
            async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
                if action == "create":
                    # Check if service already exists
                    url = f"{ranger_url.rstrip('/')}/service/public/v2/api/service/name/{model.name}"
                    existing_id = None
                    try:
                        resp = await client.get(url, auth=auth)
                        if resp.status_code == 200:
                            existing_id = resp.json().get("id")
                            logger.info(f"Ranger service {model.name} already exists with ID {existing_id}. Will update it.")
                    except Exception as e:
                        logger.warning(f"Error checking if Ranger service {model.name} exists: {e}")

                    # Resolve credentials and namespace
                    namespace = await self._resolve_namespace(model)
                    ranger_pass = ""
                    if model.ranger_user_password:
                        try:
                            ranger_pass = decrypt_password(model.ranger_user_password)
                        except Exception:
                            ranger_pass = model.ranger_user_password
                    if not ranger_pass:
                        ranger_pass = "ranger"

                    payload = {
                        "name": model.name,
                        "type": "trino",
                        "configs": {
                            "username": "ranger",
                            "password": ranger_pass,
                            "jdbc.driverClassName": "io.trino.jdbc.TrinoDriver",
                            "jdbc.url": f"jdbc:trino://{model.name}.{namespace}.svc.cluster.local:8443?SSL=true",
                            "ranger.plugin.super.users": "trino,ranger",
                            "commonNameForCertificate": model.name
                        }
                    }

                    if existing_id is not None:
                        payload["id"] = existing_id
                        update_url = f"{ranger_url.rstrip('/')}/service/public/v2/api/service/{existing_id}"
                        resp = await client.put(update_url, json=payload, auth=auth)
                        if resp.status_code not in (200, 201):
                            logger.error(f"Failed to update Ranger service {model.name}: {resp.status_code} - {resp.text}")
                        else:
                            logger.info(f"Successfully updated Ranger service {model.name} in Ranger.")
                    else:
                        create_url = f"{ranger_url.rstrip('/')}/service/public/v2/api/service"
                        resp = await client.post(create_url, json=payload, auth=auth)
                        if resp.status_code not in (200, 201):
                            logger.error(f"Failed to create Ranger service {model.name}: {resp.status_code} - {resp.text}")
                        else:
                            logger.info(f"Successfully created Ranger service {model.name} in Ranger.")

                elif action == "delete":
                    # Delete service
                    url = f"{ranger_url.rstrip('/')}/service/public/v2/api/service/name/{model.name}"
                    resp = await client.delete(url, auth=auth)
                    if resp.status_code not in (200, 204, 404):
                        logger.error(f"Failed to delete Ranger service {model.name}: {resp.status_code} - {resp.text}")
                    else:
                        logger.info(f"Successfully deleted Ranger service {model.name} from Ranger.")

        except Exception as e:
            logger.error(f"Failed to {action} Ranger service for Trino {model.name}: {e}")
