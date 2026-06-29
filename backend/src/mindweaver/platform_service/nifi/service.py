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
from mindweaver.crypto import decrypt_password
from mindweaver.service.ldap_config.service import LdapConfigService
from .model import NifiPlatform, NifiPlatformState


logger = logging.getLogger(__name__)


class NifiPlatformService(PlatformService[NifiPlatform]):
    template_directory: str = os.path.join(os.path.dirname(__file__), "templates")
    state_model: type[NifiPlatformState] = NifiPlatformState

    @classmethod
    def model_class(cls) -> type[NifiPlatform]:
        """Returns the NifiPlatform model class."""
        return NifiPlatform

    @classmethod
    def service_path(cls) -> str:
        """Returns the base API path for this service."""
        return "/platform/nifi"


    @classmethod
    def widgets(cls) -> dict[str, Any]:
        """Returns the DynamicForm widgets configuration for UI fields."""
        return {
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

    async def template_vars(self, model: NifiPlatform) -> dict:
        """Resolves template variables required to render Helm/K8s manifests."""
        vars = model.model_dump()
        vars["image"], vars["image_tag"] = await self.resolve_image(
            model, "nifi", "apache/nifi", "2.9.0"
        )
        chart_repo, chart_name, chart_version = await self.resolve_chart(
            model, "nifi", "main", "ghcr.io/konpyutaika/helm-charts", "nifi-cluster", "1.17.0"
        )
        vars["chart_repo"] = chart_repo
        vars["chart_name"] = chart_name
        vars["chart_version"] = chart_version
        # NiFi templates check override_image in some legacy contexts or we can just set it to True
        vars["override_image"] = True
        vars["namespace"] = await self._resolve_namespace(model)
        project = await self.project(model)
        vars["ingress_domain"] = project.ingress_domain

        
        # Resolve LDAP Configuration from Project
        ldap_config_id = getattr(project, "ldap_config_id", None)
        if ldap_config_id and "mock" not in str(type(ldap_config_id)).lower():
            ldap_svc = await LdapConfigService.get_service(self.request, self.session)
            ldap_config = await ldap_svc.get(ldap_config_id)
            vars["ldap_enabled"] = True
            vars["ldap_url"] = ldap_config.server_url
            vars["ldap_search_base"] = ldap_config.user_search_base
            vars["ldap_search_filter"] = ldap_config.user_search_filter
            vars["ldap_user_dn_pattern"] = f"{ldap_config.username_attr}={{0}},{ldap_config.user_search_base}"
            
            if ldap_config.bind_dn:
                vars["ldap_manager_dn"] = ldap_config.bind_dn
                if ldap_config.bind_password:
                    try:
                        bind_pass = decrypt_password(ldap_config.bind_password)
                    except Exception:
                        bind_pass = ldap_config.bind_password
                    vars["ldap_manager_password"] = bind_pass
            
            if ldap_config.group_search_base:
                vars["ldap_group_search_base"] = ldap_config.group_search_base
            if ldap_config.group_search_filter:
                vars["ldap_group_search_filter"] = ldap_config.group_search_filter
            if ldap_config.group_member_attr:
                vars["ldap_group_role_attribute"] = ldap_config.group_member_attr
                
            if ldap_config.server_url.startswith("ldaps://"):
                vars["ldap_authentication_strategy"] = "LDAPS"
            else:
                vars["ldap_authentication_strategy"] = "SIMPLE"
                
        return vars


    async def decommission(self, model: NifiPlatform):
        """Decommissions the NiFi cluster and cleans up its CA secret."""
        await super().decommission(model)

        kubeconfig = await self.kubeconfig(model)
        namespace = await self._resolve_namespace(model)
        secret_name = f"{model.name}-ca-secret"

        def _delete_secret():
            if kubeconfig is None:
                config.load_incluster_config()
                k8s_client = client.ApiClient()
            else:
                with tempfile.NamedTemporaryFile(mode="w") as kf:
                    kf.write(kubeconfig)
                    kf.flush()
                    k8s_client = config.new_client_from_config(config_file=kf.name)

            core_v1 = client.CoreV1Api(k8s_client)
            try:
                core_v1.delete_namespaced_secret(name=secret_name, namespace=namespace)
                logger.info(f"Deleted CA secret {secret_name} in namespace {namespace}")
            except client.exceptions.ApiException as e:
                if e.status == 404:
                    logger.info(f"CA secret {secret_name} in namespace {namespace} not found, skipping")
                else:
                    logger.error(f"Failed to delete CA secret {secret_name}: {e}")
                    raise

        try:
            await asyncio.to_thread(_delete_secret)
        except Exception as e:
            logger.error(f"Failed to delete CA secret {secret_name} during decommissioning: {e}")

    async def poll_status(self, model: NifiPlatform):
        """Polls cluster status (via ArgoCD application and k8s pods) and updates NifiPlatformState."""
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
                # NiFi pods are managed by NiFiKop and use nifi_cr label
                pods = core_v1.list_namespaced_pod(
                    namespace=namespace,
                    label_selector=f"nifi_cr={model.name}",
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
                                        "protocol": "https" if port.port == 8443 else "http",
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
        project = await self.project(model)
        if extra_data is None:
            extra_data = {}
        extra_data["namespace"] = namespace
        extra_data["ingress_domain"] = project.ingress_domain
        state.extra_data = extra_data
        state.node_ports = node_ports
        state.cluster_nodes = cluster_nodes

        # Derive NiFi HTTPS URL (NiFi always runs on HTTPS port 8443)
        if status == "online":
            if project.ingress_domain:
                state.nifi_uri = f"https://{model.name}.{project.ingress_domain}"
            elif cluster_nodes:
                nifi_np = next(
                    (np for np in node_ports if np["port"] == 8443), None
                )
                if nifi_np:
                    node_v4 = next((n for n in cluster_nodes if n["ipv4"]), None)
                    if node_v4:
                        state.nifi_uri = f"https://{node_v4['ipv4']}:{nifi_np['node_port']}"
                    else:
                        state.nifi_uri = f"https://{model.name}.{namespace}.svc.cluster.local:8443"
                else:
                    state.nifi_uri = f"https://{model.name}.{namespace}.svc.cluster.local:8443"
            else:
                state.nifi_uri = f"https://{model.name}.{namespace}.svc.cluster.local:8443"
        else:
            state.nifi_uri = None

        state.last_heartbeat = ts_now()
        await self.session.flush()
