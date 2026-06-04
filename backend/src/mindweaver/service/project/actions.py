# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import asyncio
import functools
import jinja2 as j2
import logging
import os
import tempfile
import yaml
from typing import Any, Optional
from sqlmodel import select


from mindweaver.fw.action import BaseAction
from mindweaver.service.project.service import ProjectService
from mindweaver.service.k8s_cluster import K8sCluster, K8sClusterType
from mindweaver.service.project_user.model import ProjectLocalUser
from mindweaver.service.ldap_config.service import LdapConfigService
from mindweaver.crypto import decrypt_password

logger = logging.getLogger(__name__)


async def _get_existing_nodeport(cluster, namespace: str) -> Optional[int]:
    """Retrieve existing Envoy HTTPS nodePort if it has been dynamically allocated."""
    from kubernetes import client, config
    def _get():
        try:
            if cluster.type == K8sClusterType.IN_CLUSTER:
                config.load_incluster_config()
            else:
                if not cluster.kubeconfig:
                    return None
                with tempfile.NamedTemporaryFile(mode="w", delete=False) as kf:
                    kf.write(cluster.kubeconfig)
                    kf.flush()
                    config.load_kube_config(config_file=kf.name)
            core_v1 = client.CoreV1Api()
            # Try project namespace first
            try:
                svcs = core_v1.list_namespaced_service(namespace=namespace)
                for svc in svcs.items:
                    if "envoy" in svc.metadata.name or "project-gateway" in svc.metadata.name:
                        for p in svc.spec.ports:
                            if p.port == 443 and getattr(p, "node_port", None):
                                return p.node_port
            except Exception:
                pass

            # Try envoy-gateway-system namespace next
            expected_prefix = f"envoy-{namespace}-project-gateway"
            try:
                eg_svcs = core_v1.list_namespaced_service(namespace="envoy-gateway-system")
                for svc in eg_svcs.items:
                    if svc.metadata.name.startswith(expected_prefix):
                        for p in svc.spec.ports:
                            if p.port == 443 and getattr(p, "node_port", None):
                                return p.node_port
            except Exception:
                pass
        except Exception as e:
            logger.warning(f"Error checking existing nodeport: {e}")
        return None
    return await asyncio.to_thread(_get)


@functools.lru_cache(maxsize=32)
def _get_jinja_env() -> j2.Environment:
    template_directory = os.path.join(os.path.dirname(__file__), "templates")
    env = j2.Environment(loader=j2.FileSystemLoader(template_directory))
    return env


def _render_gateway_manifests(model, namespace: str, nodeport: Optional[int] = None) -> str:
    """Render Gateway and Certificate manifests from YAML templates."""
    vars = {
        "name": model.name,
        "namespace": namespace,
        "ingress_domain": model.ingress_domain,
        "nodeport": nodeport,
    }

    env = _get_jinja_env()
    templates = sorted(env.list_templates())
    rendered = []
    for template_name in templates:
        if not template_name.endswith((".yaml", ".yml", ".yml.j2", ".yaml.j2")):
            continue
        template = env.get_template(template_name)
        rendered.append(template.render(**vars))

    return "\n---\n".join(r for r in rendered if r.strip())



@ProjectService.register_action("install_dex")
class InstallDexAction(BaseAction):
    """
    Action to install and configure Dex OIDC provider on the project namespace.
    """

    async def available(self) -> bool:
        """
        Action is available only if the project is associated with a cluster.
        """
        return self.model.k8s_cluster_id is not None

    async def __call__(self, **kwargs):
        """
        Trigger the Celery background task to install Dex for this project.
        """
        from mindweaver.tasks.project_tasks import install_dex_project_task

        install_dex_project_task.delay(self.model.id)
        return {
            "status": "success",
            "message": "Dex installation triggered for this project namespace.",
        }

    async def run(self):
        """
        Perform the project-scoped Dex Helm installation.
        """
        logger.info(f"Installing Dex for project {self.model.name} in namespace {self.model.k8s_namespace}")

        # 1. Query Cluster
        stmt_cluster = select(K8sCluster).where(K8sCluster.id == self.model.k8s_cluster_id)
        res_cluster = await self.session.exec(stmt_cluster)
        cluster = res_cluster.one()

        # 2. Query project local users
        stmt_user = select(ProjectLocalUser).where(ProjectLocalUser.project_id == self.model.id)
        res_user = await self.session.exec(stmt_user)
        local_users = res_user.all()

        # 3. Find LDAP config associated with this project
        ldap_config = None
        if self.model.ldap_config_id:
            ldap_svc = await LdapConfigService.get_service(self.svc.request, self.session)
            ldap_config = await ldap_svc.get(self.model.ldap_config_id)

        # 4. Construct Dex connectors and staticPasswords config
        connectors = []
        if ldap_config:
            # Parse server url
            url = ldap_config.server_url
            host = url.replace("ldap://", "").replace("ldaps://", "")
            if ":" not in host:
                if url.startswith("ldaps://"):
                    host = f"{host}:636"
                else:
                    host = f"{host}:389"

            insecure_no_ssl = url.startswith("ldap://")

            bind_password = ""
            if ldap_config.bind_password:
                try:
                    bind_password = decrypt_password(ldap_config.bind_password)
                except Exception:
                    bind_password = ldap_config.bind_password

            clean_filter = ldap_config.user_search_filter
            if clean_filter and "{0}" in clean_filter:
                import re
                if re.match(r"^\([\w\-]+=\{0\}\)$", clean_filter.strip()):
                    clean_filter = None
                else:
                    clean_filter = re.sub(r"\([\w\-]+=\{0\}\)", "", clean_filter)
                    clean_filter = clean_filter.replace("(&)", "").strip()
                    if not clean_filter:
                        clean_filter = None

            user_search = {
                "baseDN": ldap_config.user_search_base,
                "username": ldap_config.username_attr,
                "idAttr": ldap_config.username_attr,
                "emailAttr": ldap_config.username_attr,
                "nameAttr": ldap_config.username_attr,
            }
            if clean_filter:
                user_search["filter"] = clean_filter

            connectors.append({
                "type": "ldap",
                "id": "ldap",
                "name": "LDAP",
                "config": {
                    "host": host,
                    "insecureNoSSL": insecure_no_ssl,
                    "insecureSkipVerify": not ldap_config.verify_ssl,
                    "bindDN": ldap_config.bind_dn,
                    "bindPW": bind_password,
                    "userSearch": user_search
                }
            })

        static_passwords = []
        for u in local_users:
            static_passwords.append({
                "email": u.email,
                "hash": u.password_hash_bcrypt,
                "username": u.username,
                "userID": str(u.uuid),
            })

        namespace = self.model.k8s_namespace or self.model.name

        # 5. Build values dict for Dex
        issuer_url = f"http://dex.{namespace}.svc.cluster.local:5556/dex"
        if self.model.ingress_domain:
            issuer_url = f"https://dex.{self.model.ingress_domain}/dex"

        static_clients = []
        # Find active Superset platforms with oidc_enabled
        from mindweaver.platform_service.superset.model import SupersetPlatform
        stmt_superset = select(SupersetPlatform).where(
            SupersetPlatform.project_id == self.model.id,
            SupersetPlatform.oidc_enabled == True
        )
        res_superset = await self.session.exec(stmt_superset)
        superset_platforms = res_superset.all()
        for sp in superset_platforms:
            redirect_uris = []
            if self.model.ingress_domain:
                redirect_uris.append(f"https://{sp.name}.{self.model.ingress_domain}/oauth-authorized/dex")
                redirect_uris.append(f"http://{sp.name}.{self.model.ingress_domain}/oauth-authorized/dex")
            else:
                redirect_uris.append("http://localhost:8088/oauth-authorized/dex")
            
            secret_val = ""
            if sp.oidc_client_secret:
                try:
                    secret_val = decrypt_password(sp.oidc_client_secret)
                except Exception:
                    secret_val = sp.oidc_client_secret
            
            static_clients.append({
                "id": sp.name,
                "name": f"Superset {sp.name}",
                "secret": secret_val,
                "redirectURIs": redirect_uris,
            })

        dex_values = {
            "config": {
                "issuer": issuer_url,
                "storage": {
                    "type": "kubernetes",
                    "config": {
                        "inCluster": True
                    }
                },
                "enablePasswordDB": True,
            }
        }
        if static_passwords:
            dex_values["config"]["staticPasswords"] = static_passwords
        if connectors:
            dex_values["config"]["connectors"] = connectors
        if static_clients:
            dex_values["config"]["staticClients"] = static_clients

        # Check existing nodePort to persist if not set
        if not self.model.envoy_nodeport:
            existing_port = await _get_existing_nodeport(cluster, namespace)
            if existing_port:
                self.model.envoy_nodeport = existing_port
                self.session.add(self.model)
                await self.session.commit()
                await self.session.refresh(self.model)

        gateway_manifest = ""
        if self.model.ingress_domain:
            gateway_manifest = _render_gateway_manifests(
                self.model, namespace, self.model.envoy_nodeport
            )


        # 6. Install Dex using Helm and values file
        kubeconfig_path = None
        temp_kf = None
        temp_values = None

        try:
            if cluster.type == K8sClusterType.REMOTE:
                if not cluster.kubeconfig:
                    raise ValueError(f"Cluster {cluster.name} has no kubeconfig")
                temp_kf = tempfile.NamedTemporaryFile(mode="w", delete=False)
                temp_kf.write(cluster.kubeconfig)
                temp_kf.flush()
                temp_kf.close()
                kubeconfig_path = temp_kf.name

            # Write values to a temporary file
            temp_values = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
            yaml.safe_dump(dex_values, temp_values)
            temp_values.flush()
            temp_values.close()

            async def run_helm(*args):
                cmd = ["helm"]
                if kubeconfig_path:
                    cmd.extend(["--kubeconfig", kubeconfig_path])
                cmd.extend(args)
                logger.debug(f"Running Helm command: {' '.join(cmd)}")
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await proc.communicate()
                if proc.returncode != 0:
                    raise RuntimeError(f"Helm command failed: {stderr.decode()}")
                return stdout.decode()

            # Ensure repo is added
            await run_helm("repo", "add", "dex", "https://charts.dexidp.io")
            await run_helm("repo", "update")

            # Install
            await run_helm(
                "upgrade",
                "--install",
                "dex",
                "dex/dex",
                "--namespace",
                namespace,
                "--create-namespace",
                "--wait",
                "-f",
                temp_values.name,
            )

            if gateway_manifest:
                async def run_kubectl(manifest: str):
                    temp_m = None
                    try:
                        temp_m = tempfile.NamedTemporaryFile(mode="w", delete=False)
                        temp_m.write(manifest)
                        temp_m.flush()
                        temp_m.close()
                        cmd = ["kubectl"]
                        if kubeconfig_path:
                            cmd.extend(["--kubeconfig", kubeconfig_path])
                        cmd.extend(["apply", "-f", temp_m.name])
                        proc = await asyncio.create_subprocess_exec(
                            *cmd,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE,
                        )
                        stdout, stderr = await proc.communicate()
                        if proc.returncode != 0:
                            raise RuntimeError(f"Kubectl command failed: {stderr.decode()}")
                    finally:
                        if temp_m:
                            try:
                                os.unlink(temp_m.name)
                            except Exception:
                                pass

                await run_kubectl(gateway_manifest)

        finally:
            for f in [temp_kf, temp_values]:
                if f:
                    try:
                        os.unlink(f.name)
                    except Exception:
                        pass


@ProjectService.register_action("deploy_gateway")
class DeployGatewayAction(BaseAction):
    """
    Action to deploy Envoy Gateway (Gateway / HTTPRoute) resources for this project.
    """

    async def available(self) -> bool:
        return self.model.k8s_cluster_id is not None and bool(self.model.ingress_domain)

    async def __call__(self, **kwargs):
        from mindweaver.tasks.project_tasks import deploy_gateway_project_task

        deploy_gateway_project_task.delay(self.model.id)
        return {
            "status": "success",
            "message": "Project Envoy Gateway deployment triggered.",
        }

    async def run(self):
        logger.info(f"Deploying Envoy Gateway resources for project {self.model.name}")

        stmt_cluster = select(K8sCluster).where(K8sCluster.id == self.model.k8s_cluster_id)
        res_cluster = await self.session.exec(stmt_cluster)
        cluster = res_cluster.one()

        namespace = self.model.k8s_namespace or self.model.name

        # Check existing nodePort to persist if not set
        if not self.model.envoy_nodeport:
            existing_port = await _get_existing_nodeport(cluster, namespace)
            if existing_port:
                self.model.envoy_nodeport = existing_port
                self.session.add(self.model)
                await self.session.commit()
                await self.session.refresh(self.model)

        gateway_manifest = ""
        if self.model.ingress_domain:
            gateway_manifest = _render_gateway_manifests(
                self.model, namespace, self.model.envoy_nodeport
            )


        kubeconfig_path = None
        temp_kf = None
        try:
            if cluster.type == K8sClusterType.REMOTE:
                if not cluster.kubeconfig:
                    raise ValueError(f"Cluster {cluster.name} has no kubeconfig")
                temp_kf = tempfile.NamedTemporaryFile(mode="w", delete=False)
                temp_kf.write(cluster.kubeconfig)
                temp_kf.flush()
                temp_kf.close()
                kubeconfig_path = temp_kf.name

            async def run_kubectl(manifest: str):
                temp_m = None
                try:
                    temp_m = tempfile.NamedTemporaryFile(mode="w", delete=False)
                    temp_m.write(manifest)
                    temp_m.flush()
                    temp_m.close()
                    cmd = ["kubectl"]
                    if kubeconfig_path:
                        cmd.extend(["--kubeconfig", kubeconfig_path])
                    cmd.extend(["apply", "-f", temp_m.name])
                    proc = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                    )
                    stdout, stderr = await proc.communicate()
                    if proc.returncode != 0:
                        raise RuntimeError(f"Kubectl command failed: {stderr.decode()}")
                finally:
                    if temp_m:
                        try:
                            os.unlink(temp_m.name)
                        except Exception:
                            pass

            await run_kubectl(gateway_manifest)
        finally:
            if temp_kf:
                try:
                    os.unlink(temp_kf.name)
                except Exception:
                    pass

