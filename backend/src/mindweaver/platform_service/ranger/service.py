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
from mindweaver.platform_service.solr.service import SolrPlatformService
from mindweaver.service.ldap_config.service import LdapConfigService

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
            "solr_id": {
                "order": 21,
                "label": "Solr",
                "type": "relationship",
                "endpoint": "/api/v1/platform/solr",
                "field": "id",
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
        project = await self.project(model)
        vars["ingress_domain"] = project.ingress_domain

        # Force HTTPS / SSL for Ranger Admin
        additional_props = vars.setdefault("additional_properties", {})
        additional_props.setdefault("policymgr_http_enabled", "false")
        additional_props.setdefault("policymgr_https_keystore_file", "/etc/ranger/tls/keystore.jks")
        additional_props.setdefault("policymgr_https_keystore_password", "changeit")
        additional_props.setdefault("policymgr_https_keystore_keyalias", "certificate")

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



        # Resolve Solr Connection for Audits
        if model.solr_id:
            solr_svc = await SolrPlatformService.get_service(self.request, self.session)
            solr_model = await solr_svc.get(model.solr_id)
            solr_state = await solr_svc.platform_state(solr_model)

            if not solr_state or not solr_state.active:
                raise ValueError(
                    f"Managed Solr cluster {solr_model.name} is not active"
                )

            solr_ns = await solr_svc._resolve_namespace(solr_model)
            solr_host = SolrPlatformService.get_internal_host(
                solr_model, solr_state, solr_ns
            )

            solr_pass = ""
            if solr_state.admin_password:
                try:
                    solr_pass = decrypt_password(solr_state.admin_password)
                except Exception:
                    solr_pass = solr_state.admin_password

            additional_props = vars.setdefault("additional_properties", {})
            # Make sure we don't overwrite user custom properties if they exist
            additional_props.setdefault("audit_store", "solr")
            additional_props.setdefault("audit_solr_urls", f"https://{solr_host}:8983/solr/ranger_audits")
            if solr_pass:
                additional_props.setdefault("xasecure.audit.solr.is.basicauth.enabled", "true")
                additional_props.setdefault("ranger.audit.solr.basic.auth.user", "solr")
                additional_props.setdefault("ranger.audit.solr.basic.auth.password", solr_pass)
            
        # Set DB root user/pass to be the same as db_user/pass for managed DBs
        vars["db_root_user"] = vars.get("db_user")
        vars["db_root_pass"] = vars.get("db_pass")

        # Resolve LDAP Configuration from Project
        if project.ldap_config_id:
            ldap_svc = await LdapConfigService.get_service(self.request, self.session)
            ldap_config = await ldap_svc.get(project.ldap_config_id)
            
            additional_props = vars.setdefault("additional_properties", {})
            additional_props.setdefault("authentication_method", "LDAP")
            additional_props.setdefault("xa_ldap_url", ldap_config.server_url)
            
            if ldap_config.bind_dn:
                additional_props.setdefault("xa_ldap_bind_dn", ldap_config.bind_dn)
                if ldap_config.bind_password:
                    try:
                        bind_pass = decrypt_password(ldap_config.bind_password)
                    except Exception:
                        bind_pass = ldap_config.bind_password
                    additional_props.setdefault("xa_ldap_bind_password", bind_pass)
            
            additional_props.setdefault("xa_ldap_base_dn", ldap_config.user_search_base)
            additional_props.setdefault("xa_ldap_userDNpattern", f"{ldap_config.username_attr}={{0}},{ldap_config.user_search_base}")
            additional_props.setdefault("xa_ldap_userSearchFilter", ldap_config.user_search_filter)
            
            if ldap_config.group_search_base:
                additional_props.setdefault("xa_ldap_groupSearchBase", ldap_config.group_search_base)
            if ldap_config.group_search_filter:
                additional_props.setdefault("xa_ldap_groupSearchFilter", ldap_config.group_search_filter)
            if ldap_config.group_member_attr:
                additional_props.setdefault("xa_ldap_groupRoleAttribute", ldap_config.group_member_attr)

            # UserSync configuration
            additional_props.setdefault("SYNC_SOURCE", "ldap")
            additional_props.setdefault("SYNC_LDAP_URL", ldap_config.server_url)
            if ldap_config.bind_dn:
                additional_props.setdefault("SYNC_LDAP_BIND_DN", ldap_config.bind_dn)
                if ldap_config.bind_password:
                    try:
                        bind_pass = decrypt_password(ldap_config.bind_password)
                    except Exception:
                        bind_pass = ldap_config.bind_password
                    additional_props.setdefault("SYNC_LDAP_BIND_PASSWORD", bind_pass)
            
            if ldap_config.user_search_base:
                additional_props.setdefault("SYNC_LDAP_SEARCH_BASE", ldap_config.user_search_base)
                additional_props.setdefault("SYNC_LDAP_USER_SEARCH_BASE", ldap_config.user_search_base)
            if ldap_config.user_search_filter:
                sync_user_filter = ldap_config.user_search_filter.replace("{0}", "*")
                additional_props.setdefault("SYNC_LDAP_USER_SEARCH_FILTER", sync_user_filter)
            additional_props.setdefault("SYNC_LDAP_USER_NAME_ATTRIBUTE", ldap_config.username_attr)
            
            if ldap_config.group_search_base:
                additional_props.setdefault("SYNC_GROUP_SEARCH_BASE", ldap_config.group_search_base)
                additional_props.setdefault("SYNC_GROUP_OBJECT_CLASS", "groupofnames")
                additional_props.setdefault("SYNC_GROUP_NAME_ATTRIBUTE", "cn")
            if ldap_config.group_search_filter:
                sync_group_filter = ldap_config.group_search_filter.replace("{0}", "*")
                additional_props.setdefault("SYNC_GROUP_SEARCH_FILTER", sync_group_filter)
            if ldap_config.group_member_attr:
                additional_props.setdefault("SYNC_GROUP_MEMBER_ATTRIBUTE_NAME", ldap_config.group_member_attr)
            
            # Disable delta sync to avoid Operations Error (e.g. uSNChanged) on OpenLDAP
            additional_props.setdefault("SYNC_LDAP_DELTASYNC", "false")
            # Set referral to ignore to avoid referral chasing errors in AD/LDAP
            additional_props.setdefault("SYNC_LDAP_REFERRAL", "ignore")



        # Decrypt passwords
        for pwd_field in ["admin_password", "keyadmin_password", "tagsync_password", "usersync_password"]:
            pwd_val = getattr(model, pwd_field)
            if pwd_val:
                try:
                    vars[pwd_field] = decrypt_password(pwd_val)
                except Exception:
                    vars[pwd_field] = pwd_val

        return vars

    async def get_ranger_url(self, model: RangerPlatform) -> str:
        """
        Get the Ranger URL for a given RangerPlatform model.
        Resolves to the active state URL, or falls back to the cluster local DNS URL.
        """
        state = await self.platform_state(model)
        if state and state.ranger_url:
            return state.ranger_url
        
        namespace = await self._resolve_namespace(model)
        return f"https://{model.name}.{namespace}.svc.cluster.local:6080"

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
        project = await self.project(model)
        if extra_data is None:
            extra_data = {}
        extra_data["namespace"] = namespace
        extra_data["ingress_domain"] = project.ingress_domain
        state.extra_data = extra_data
        state.node_ports = node_ports
        state.cluster_nodes = cluster_nodes

        # Derive Ranger URL
        if status == "online":
            if project.ingress_domain:
                state.ranger_url = f"https://{model.name}.{project.ingress_domain}"
                state.ranger_url_ipv6 = None
            elif cluster_nodes:
                ranger_np = next((np for np in node_ports if np["port"] == 6080), None)
                if ranger_np:
                    # Find first node with IPv4
                    node_v4 = next((n for n in cluster_nodes if n["ipv4"]), None)
                    if node_v4:
                        state.ranger_url = (
                            f"https://{node_v4['ipv4']}:{ranger_np['node_port']}"
                        )
                    else:
                        state.ranger_url = None

                    # Find first node with IPv6
                    node_v6 = next((n for n in cluster_nodes if n["ipv6"]), None)
                    if node_v6:
                        state.ranger_url_ipv6 = (
                            f"https://[{node_v6['ipv6']}]:{ranger_np['node_port']}"
                        )
                    else:
                        state.ranger_url_ipv6 = None
                else:
                    state.ranger_url = f"https://{model.name}.{namespace}.svc.cluster.local:6080"
                    state.ranger_url_ipv6 = None
            else:
                state.ranger_url = f"https://{model.name}.{namespace}.svc.cluster.local:6080"
                state.ranger_url_ipv6 = None
        else:
            state.ranger_url = None
            state.ranger_url_ipv6 = None

        # Populating passwords for UI display
        state.admin_password = model.admin_password
        state.keyadmin_password = model.keyadmin_password
        state.tagsync_password = model.tagsync_password
        state.usersync_password = model.usersync_password
        state.last_heartbeat = ts_now()

        await self.session.flush()


