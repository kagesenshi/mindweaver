# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import os
import logging
import asyncio
import tempfile
import base64
from typing import Any, Optional
from kubernetes import client, config
from mindweaver.platform_service.base import PlatformService
from mindweaver.crypto import decrypt_password, encrypt_password
from mindweaver.fw.model import ts_now
from mindweaver.fw.util import generate_password
from mindweaver.fw.hooks import before_create

from .model import SolrPlatform, SolrPlatformState
from mindweaver.platform_service.zookeeper.service import ZookeeperPlatformService

logger = logging.getLogger(__name__)


class SolrPlatformService(PlatformService[SolrPlatform]):
    template_directory: str = os.path.join(os.path.dirname(__file__), "templates")
    state_model: type[SolrPlatformState] = SolrPlatformState

    @before_create(before="_handle_redacted_create")
    async def generate_passwords(self, model: SolrPlatform):
        """Autogenerate random password for Solr admin if not provided."""
        if not model.admin_password:
            model.admin_password = generate_password()

    @classmethod
    def model_class(cls) -> type[SolrPlatform]:
        return SolrPlatform

    @classmethod
    def service_path(cls) -> str:
        return "/platform/solr"

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
            "zookeeper_id": {
                "order": 15,
                "label": "Zookeeper",
                "type": "relationship",
                "endpoint": "/api/v1/platform/zookeeper",
                "field": "id",
            },
        }

    @classmethod
    def get_internal_host(
        cls,
        model: SolrPlatform,
        state: Optional[SolrPlatformState],
        namespace: str,
    ) -> str:
        """Returns the internal service hostname with port for Solr."""
        service_name = None
        if state and isinstance(getattr(state, "extra_data", None), dict):
            service_name = state.extra_data.get("service_name")
        if not service_name or not (service_name.endswith("-headless") or service_name == model.name):
            service_name = f"{model.name}-solrcloud-headless"
        return f"{service_name}.{namespace}.svc.cluster.local:8983"

    async def template_vars(self, model: SolrPlatform) -> dict:
        vars = model.model_dump()
        vars["namespace"] = await self._resolve_namespace(model)
        project = await self.project(model)
        vars["ingress_domain"] = project.ingress_domain

        # Decrypt password
        if model.admin_password:
            try:
                decrypted = decrypt_password(model.admin_password)
            except Exception:
                decrypted = model.admin_password
            vars["admin_password"] = decrypted

        # Resolve external Zookeeper connection string if linked.
        # The actual client service name is discovered at runtime by poll_status
        # via label-based lookup, so we read it from state rather than guessing.
        if model.zookeeper_id:
            zk_svc = await ZookeeperPlatformService.get_service(self.request, self.session)
            zk_model = await zk_svc.get(model.zookeeper_id)
            zk_state = await zk_svc.platform_state(zk_model)

            if not zk_state or not zk_state.active:
                raise ValueError(
                    f"Zookeeper cluster '{zk_model.name}' is not active. "
                    "Please deploy it before deploying Solr."
                )

            if not zk_state.zookeeper_url:
                raise ValueError(
                    f"Zookeeper cluster '{zk_model.name}' has not been polled yet "
                    "(zookeeper_url is empty). Wait for the status poller to run, "
                    "or use Refresh on the ZooKeeper page, then retry."
                )

            vars["zookeeper_connection_string"] = zk_state.zookeeper_url
        else:
            vars["zookeeper_connection_string"] = None

        return vars

    async def poll_status(self, model: SolrPlatform):
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
                    label_selector=f"solrcloud={model.name}",
                )
                if not pods.items:
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

            # 3. Fetch NodePorts for UI and find main service name
            node_ports = []
            service_name = None
            try:
                services = core_v1.list_namespaced_service(namespace=namespace)
                for svc in services.items:
                    instance_label = svc.metadata.labels.get("solrcloud") if svc.metadata.labels else None
                    if (
                        (
                            svc.metadata.name == model.name
                            or svc.metadata.name.endswith("-headless")
                            or svc.metadata.name.endswith("-nodeport")
                        )
                        and (
                            svc.metadata.name.startswith(model.name)
                            or instance_label == model.name
                        )
                    ):
                        has_8983 = any(p.port == 8983 for p in (svc.spec.ports or []))
                        if has_8983 and not svc.metadata.name.endswith("-nodeport"):
                            service_name = svc.metadata.name

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

            # 5. Fetch generated credentials from Secrets.
            # The Solr Operator splits credentials across two secrets:
            #   - {name}-solrcloud-security-bootstrap: admin and solr user passwords
            #   - {name}-solrcloud-basic-auth: k8s-oper password
            admin_password = None
            k8s_oper_password = None
            solr_user_password = None
            try:
                bootstrap_secret = core_v1.read_namespaced_secret(
                    name=f"{model.name}-solrcloud-security-bootstrap",
                    namespace=namespace,
                )
                if bootstrap_secret.data:
                    logger.debug(
                        f"Bootstrap secret keys for {model.name}: "
                        f"{list(bootstrap_secret.data.keys())}"
                    )
                    encoded_admin = (
                        bootstrap_secret.data.get("admin")
                        or bootstrap_secret.data.get("admin-password")
                    )
                    if encoded_admin:
                        admin_password = base64.b64decode(encoded_admin).decode("utf-8")
                    encoded_solr_user = (
                        bootstrap_secret.data.get("solr")
                        or bootstrap_secret.data.get("solr-password")
                    )
                    if encoded_solr_user:
                        solr_user_password = base64.b64decode(encoded_solr_user).decode("utf-8")
            except Exception as e:
                logger.debug(f"Could not fetch bootstrap secret for {model.name}: {e}")

            try:
                basic_auth_secret = core_v1.read_namespaced_secret(
                    name=f"{model.name}-solrcloud-basic-auth",
                    namespace=namespace,
                )
                if basic_auth_secret.data:
                    logger.debug(
                        f"Basic-auth secret keys for {model.name}: "
                        f"{list(basic_auth_secret.data.keys())}"
                    )
                    # The basic-auth secret uses standard k8s opaque secret format:
                    # 'username' holds the literal username (k8s-oper), 'password' holds the password.
                    encoded_k8s_oper_pw = basic_auth_secret.data.get("password")
                    if encoded_k8s_oper_pw:
                        k8s_oper_password = base64.b64decode(encoded_k8s_oper_pw).decode("utf-8")
                    else:
                        logger.warning(
                            f"'password' key not found in basic-auth secret for {model.name}. "
                            f"Available keys: {list(basic_auth_secret.data.keys())}"
                        )
            except Exception as e:
                logger.debug(f"Could not fetch basic-auth secret for {model.name}: {e}")

            return (
                status,
                message,
                argo_app.get("status", {}),
                node_ports,
                cluster_nodes,
                service_name,
                admin_password,
                k8s_oper_password,
                solr_user_password,
            )

        status, message, argo_status, node_ports, cluster_nodes, service_name, admin_password, k8s_oper_password, solr_user_password = (
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

        # Derive Solr URL (default API port is 8983)
        if status == "online":
            svc_name = service_name or f"{model.name}-solrcloud-headless"
            state.solr_internal_url = f"https://{svc_name}.{namespace}.svc.cluster.local:8983"

            if project.ingress_domain:
                state.solr_url = f"https://{model.name}.{project.ingress_domain}"
                state.solr_url_ipv6 = None
            elif cluster_nodes:
                solr_np = next((np for np in node_ports if np["port"] == 8983), None)
                if solr_np:
                    node_v4 = next((n for n in cluster_nodes if n["ipv4"]), None)
                    if node_v4:
                        state.solr_url = (
                            f"https://{node_v4['ipv4']}:{solr_np['node_port']}"
                        )
                    else:
                        state.solr_url = None

                    node_v6 = next((n for n in cluster_nodes if n["ipv6"]), None)
                    if node_v6:
                        state.solr_url_ipv6 = (
                            f"https://[{node_v6['ipv6']}]:{solr_np['node_port']}"
                        )
                    else:
                        state.solr_url_ipv6 = None
                else:
                    state.solr_url = state.solr_internal_url
                    state.solr_url_ipv6 = None
            else:
                state.solr_url = state.solr_internal_url
                state.solr_url_ipv6 = None
        else:
            state.solr_url = None
            state.solr_url_ipv6 = None
            state.solr_internal_url = None

        if admin_password:
            model.admin_password = encrypt_password(admin_password)
        if k8s_oper_password:
            state.k8s_oper_password = encrypt_password(k8s_oper_password)
        if solr_user_password:
            state.solr_user_password = encrypt_password(solr_user_password)

        state.admin_password = model.admin_password
        state.last_heartbeat = ts_now()

        await self.session.flush()
