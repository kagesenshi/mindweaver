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

router = NifiPlatformService.router()

# Register the poller class
from .poller import NifiPoller
