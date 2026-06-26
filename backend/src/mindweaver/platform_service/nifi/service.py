# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import os
import logging
import asyncio
import tempfile
import base64
import random
import string
import yaml
from typing import Any, Optional
from kubernetes import client, config
from mindweaver.platform_service.base import PlatformService, _get_jinja_env
from mindweaver.fw.model import ts_now
from mindweaver.crypto import decrypt_password
from mindweaver.fw.service import before_create, before_delete
from mindweaver.fw.util import generate_password
from mindweaver.service.ldap_config.service import LdapConfigService
from mindweaver.platform_service.ranger.service import RangerPlatformService
from mindweaver.platform_service.solr.service import SolrPlatformService
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
    def internal_fields(cls) -> list[str]:
        """Fields internally managed and not exposed."""
        return super().internal_fields() + ["ranger_user_password"]

    @classmethod
    def redacted_fields(cls) -> list[str]:
        """Sensitive fields redacted in API output."""
        return ["ranger_user_password"]

    @classmethod
    def widgets(cls) -> dict[str, Any]:
        """Returns the DynamicForm widgets configuration for UI fields."""
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
            "ranger_id": {
                "order": 25,
                "label": "Ranger",
                "type": "relationship",
                "endpoint": "/api/v1/platform/ranger",
                "field": "id",
            },
            "additional_properties": {
                "order": 100,
                "label": "Additional Properties",
                "type": "key-value",
            },
        }

    @before_create(before="_handle_redacted_create")
    async def generate_passwords(self, model: NifiPlatform):
        """Autogenerate a strong random password for Ranger user."""
        if not model.ranger_user_password:
            model.ranger_user_password = generate_password()

    async def template_vars(self, model: NifiPlatform) -> dict:
        """Resolves template variables required to render Helm/K8s manifests."""
        vars = model.model_dump(exclude=self.redacted_fields())
        if not model.override_image:
            vars["image"] = "ghcr.io/kagesenshi/mindweaver/nifi"
            vars["image_tag"] = "2.9.0-rev.0"
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

        # Resolve Ranger Configuration
        if model.ranger_id:
            ranger_svc = await RangerPlatformService.get_service(self.request, self.session)
            ranger_model = await ranger_svc.get(model.ranger_id)
            ranger_state = await ranger_svc.platform_state(ranger_model)

            ranger_ns = await ranger_svc._resolve_namespace(ranger_model)
            ranger_url = f"https://{ranger_model.name}.{ranger_ns}.svc.cluster.local:6080"

            vars["ranger_enabled"] = True
            vars["ranger_url"] = ranger_url
            vars["ranger_service_name"] = model.name

            # Solr auditing config resolution
            if ranger_model.solr_id:
                solr_svc = await SolrPlatformService.get_service(self.request, self.session)
                solr_model = await solr_svc.get(ranger_model.solr_id)
                solr_state = await solr_svc.platform_state(solr_model)

                if not getattr(self, "_decommissioning", False) and (not solr_state or not solr_state.active):
                    raise ValueError(
                        f"Managed Solr cluster {solr_model.name} is not active"
                    )

                solr_ns = await solr_svc._resolve_namespace(solr_model)
                vars["ranger_solr_enabled"] = "true"
                vars["ranger_solr_url"] = f"https://{solr_model.name}-ranger-noauth.{solr_ns}.svc.cluster.local:8443/solr/ranger_audits"
                vars["ranger_solr_password"] = ""
            else:
                vars["ranger_solr_enabled"] = "false"

            vars["ranger_audit_s3_enabled"] = "false"
        else:
            vars["ranger_enabled"] = False
                
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

    async def render_manifests(self, model: NifiPlatform) -> str:
        """
        Renders the manifests from the template directory, excluding
        the ranger-sync-job.yaml.j2 template and ranger_sync.py script.
        """
        if not self.template_directory:
            raise ValueError(
                f"template_directory not set for {self.__class__.__name__}"
            )

        if not os.path.exists(self.template_directory):
            raise ValueError(
                f"template_directory {self.template_directory} does not exist"
            )

        # Load templates
        env = _get_jinja_env(self.template_directory)
        templates = env.list_templates()

        rendered_manifests = []
        vars = await self.template_vars(model)

        for template_name in templates:
            if not template_name.endswith((".yaml", ".yml", ".yml.j2", ".yaml.j2")):
                continue
            # Exclude ranger-sync-job.yaml.j2
            if "ranger-sync-job.yaml.j2" in template_name:
                continue
            template = env.get_template(template_name)
            rendered = template.render(**vars)
            rendered_manifests.append(rendered)

        if not rendered_manifests:
            logger.warning(f"No templates found in {self.template_directory}")
            return ""

        return "---\n" + "\n---\n".join(rendered_manifests)

    async def deploy(self, model: NifiPlatform):
        """
        Deploys/upgrades the NiFi service and automatically creates
        the corresponding service definition in Ranger if linked.
        """
        db_updated = False
        if model.ranger_id and not model.ranger_user_password:
            model.ranger_user_password = generate_password()
            db_updated = True
        if db_updated:
            self.session.add(model)
            coro = self.session.flush()
            if asyncio.iscoroutine(coro):
                await coro

        await super().deploy(model)
        await self._manage_ranger_service(model, "create")

    @before_delete()
    async def delete_ranger_service_on_delete(self, model: NifiPlatform):
        """
        Deletes the corresponding service definition in Ranger when the NiFi platform is deleted.
        """
        await self._manage_ranger_service(model, "delete")

    async def _manage_ranger_service(self, model: NifiPlatform, action: str):
        """
        Create or delete a Ranger service definition for the NiFi instance using an in-cluster Job.
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

            auth_str = f"admin:{admin_password}"
            auth_base64 = base64.b64encode(auth_str.encode()).decode()

            # Load the python sync script from templates
            script_path = os.path.join(self.template_directory, "ranger_sync.py")
            with open(script_path, "r") as sf:
                script_content = sf.read()

            # Generate random suffix for Job name uniqueness
            rand_suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=5))
            job_name = f"{model.name}-ranger-sync-{rand_suffix}"

            # Render the Job template
            env = _get_jinja_env(self.template_directory)
            job_template = env.get_template("ranger-sync-job.yaml.j2")
            rendered_job = job_template.render(
                job_name=job_name,
                namespace=namespace,
                ranger_sync_script=script_content,
                ranger_url=ranger_url,
                ranger_auth_b64=auth_base64,
                service_name=model.name,
                action=action,
                ranger_pass=ranger_pass
            )

            job_body = yaml.safe_load(rendered_job)

            kubeconfig = await self.kubeconfig(model)
            if kubeconfig is None:
                config.load_incluster_config()
                k8s_client = client.ApiClient()
            else:
                with tempfile.NamedTemporaryFile(mode="w") as kf:
                    kf.write(kubeconfig)
                    kf.flush()
                    k8s_client = config.new_client_from_config(config_file=kf.name)

            batch_v1 = client.BatchV1Api(k8s_client)

            # Deploy Job
            logger.info(f"Creating Ranger sync job {job_name} in namespace {namespace}...")
            batch_v1.create_namespaced_job(namespace=namespace, body=job_body)

            # Poll for Job completion
            success = False
            for _ in range(15):
                await asyncio.sleep(2)
                try:
                    job_status = batch_v1.read_namespaced_job_status(name=job_name, namespace=namespace)
                    if job_status.status.succeeded:
                        logger.info(f"Ranger sync job {job_name} succeeded.")
                        success = True
                        break
                    if job_status.status.failed:
                        logger.error(f"Ranger sync job {job_name} failed.")
                        break
                except Exception as poll_err:
                    logger.warning(f"Error checking job status for {job_name}: {poll_err}")

            # Clean up the Job if successful, otherwise leave it for debugging
            if success:
                try:
                    batch_v1.delete_namespaced_job(name=job_name, namespace=namespace, propagation_policy="Background")
                except Exception as delete_err:
                    logger.warning(f"Failed to delete sync job {job_name}: {delete_err}")
            else:
                logger.error(f"Sync job {job_name} did not succeed. Leaving the Job in-cluster for debugging.")

        except Exception as e:
            logger.error(f"Failed to {action} Ranger service for NiFi {model.name}: {e}")

