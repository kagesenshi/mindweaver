# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import asyncio
import base64
import logging
import tempfile
from kubernetes import client, config
from mindweaver.crypto import encrypt_password
from mindweaver.fw.model import ts_now
from .model import PgSqlPlatform, PgSqlPlatformState
from .service import PgSqlPlatformService

logger = logging.getLogger(__name__)


@PgSqlPlatformService.register_poller()
class PgSQLPoller:
    """Poller for PgSQL platform service."""

    def __init__(self, service: PgSqlPlatformService, model: PgSqlPlatform):
        self.service = service
        self.model = model

    async def poll(self):
        """Poll the status of the CNPG cluster."""
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

            # 1. Fetch CNPG Cluster status
            try:
                cluster = custom_api.get_namespaced_custom_object(
                    group="postgresql.cnpg.io",
                    version="v1",
                    namespace=namespace,
                    plural="clusters",
                    name=f"{self.model.name}",
                )
                status_data = cluster.get("status", {})
                phase = status_data.get("phase", "unknown")
                instances = status_data.get("instances", 0)
                ready_instances = status_data.get("readyInstances", 0)

                status = "online" if phase == "Cluster in healthy state" else "pending"
                if phase == "Degraded":
                    status = "error"

                message = f"Phase: {phase}, Instances: {ready_instances}/{instances}"
            except client.exceptions.ApiException as e:
                if e.status == 404:
                    if not active:
                        status = "offline"
                        message = "Cluster is stopped"
                    else:
                        # Cluster object doesn't exist yet, but maybe ArgoCD Application does
                        try:
                            custom_api.get_namespaced_custom_object(
                                group="argoproj.io",
                                version="v1alpha1",
                                namespace="argocd",
                                plural="applications",
                                name=self.model.name,
                            )
                            status = "pending"
                            message = "Provisioning resources"
                        except Exception:
                            status = "error"
                            message = f"Failed to fetch cluster status: {str(e)}"
                else:
                    status = "error"
                    message = f"Failed to fetch cluster status: {str(e)}"
                status_data = {}
            except Exception as e:
                status = "error"
                message = f"Failed to fetch cluster status: {str(e)}"
                status_data = {}

            # 2. Fetch NodePort status if any
            node_ports = []
            pgbouncer_port = None
            try:
                services = core_v1.list_namespaced_service(namespace=namespace)
                for svc in services.items:
                    if svc.metadata.name.startswith(self.model.name):
                        if svc.spec.type == "NodePort":
                            for port in svc.spec.ports:
                                entry = {
                                    "name": svc.metadata.name,
                                    "port": port.port,
                                    "node_port": port.node_port,
                                }
                                node_ports.append(entry)
                                if svc.metadata.name == f"{self.model.name}-pgbouncer-nodeport":
                                    pgbouncer_port = port.node_port
            except Exception as e:
                logger.error(f"Failed to fetch services: {e}")

            # 3. Fetch Cluster Nodes
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

            # 4. Fetch DB Credentials from Secret
            db_credentials = {}
            try:
                secret_name = f"{self.model.name}-app"
                secret = core_v1.read_namespaced_secret(
                    name=secret_name, namespace=namespace
                )
                if secret.data:
                    db_credentials["db_user"] = base64.b64decode(
                        secret.data.get("username", "")
                    ).decode("utf-8")
                    db_credentials["db_name"] = base64.b64decode(
                        secret.data.get("dbname", "")
                    ).decode("utf-8")
                    db_credentials["db_ca_crt"] = base64.b64decode(
                        secret.data.get("ca.crt", "")
                    ).decode("utf-8")

                    password_raw = base64.b64decode(
                        secret.data.get("password", "")
                    ).decode("utf-8")
                    if password_raw:
                        db_credentials["db_pass"] = encrypt_password(password_raw)
            except Exception as e:
                logger.error(f"Failed to fetch secret {self.model.name}-app: {e}")

            # Try to fetch CA cert from -ca secret if still missing
            if not db_credentials.get("db_ca_crt"):
                try:
                    ca_secret_name = f"{self.model.name}-ca"
                    ca_secret = core_v1.read_namespaced_secret(
                        name=ca_secret_name, namespace=namespace
                    )
                    if ca_secret.data and "ca.crt" in ca_secret.data:
                        db_credentials["db_ca_crt"] = base64.b64decode(
                            ca_secret.data["ca.crt"]
                        ).decode("utf-8")
                except Exception as e:
                    logger.debug(f"Failed to fetch secret {self.model.name}-ca: {e}")

            # Try to fetch CA cert from -tls secret if still missing
            if not db_credentials.get("db_ca_crt"):
                try:
                    tls_secret_name = f"{self.model.name}-tls"
                    tls_secret = core_v1.read_namespaced_secret(
                        name=tls_secret_name, namespace=namespace
                    )
                    if tls_secret.data and "ca.crt" in tls_secret.data:
                        db_credentials["db_ca_crt"] = base64.b64decode(
                            tls_secret.data["ca.crt"]
                        ).decode("utf-8")
                except Exception as e:
                    logger.debug(f"Failed to fetch secret {self.model.name}-tls: {e}")

            return (
                status,
                message,
                status_data,
                node_ports,
                cluster_nodes,
                db_credentials,
                pgbouncer_port,
            )

        status, message, extra_data, node_ports, cluster_nodes, db_credentials, pgbouncer_port = (
            await asyncio.to_thread(_poll, is_active)
        )

        # Update state
        state = await self.service.platform_state(self.model)
        if not state:
            state = self.service.state_model(platform_id=self.model.id)
            self.service.session.add(state)

        if not state.active:
            # If decommissioned/inactive, only update if it fully transitions to offline
            if status == "offline":
                state.status = "offline"
                state.message = message
            return

        state.status = status
        state.message = message
        if extra_data is None:
            extra_data = {}
        extra_data["namespace"] = namespace
        if pgbouncer_port:
            extra_data["pgbouncer_host"] = f"{self.model.name}-pooler-rw.{namespace}.svc.cluster.local"
        state.extra_data = extra_data
        state.node_ports = node_ports
        state.cluster_nodes = cluster_nodes

        if db_credentials:
            state.db_user = db_credentials.get("db_user")
            state.db_pass = db_credentials.get("db_pass")
            state.db_name = db_credentials.get("db_name")
            state.db_ca_crt = db_credentials.get("db_ca_crt")

        state.last_heartbeat = ts_now()
