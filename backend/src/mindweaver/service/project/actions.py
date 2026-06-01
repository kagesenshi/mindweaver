# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import asyncio
import logging
import os
import tempfile
import yaml
from typing import Any
from sqlmodel import select

from mindweaver.fw.action import BaseAction
from mindweaver.service.project.service import ProjectService
from mindweaver.service.k8s_cluster import K8sCluster, K8sClusterType
from mindweaver.service.project_user.model import ProjectLocalUser
from mindweaver.service.ldap_config.service import LdapConfigService
from mindweaver.crypto import decrypt_password

logger = logging.getLogger(__name__)


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
                    "userSearch": {
                        "baseDN": ldap_config.user_search_base,
                        "filter": ldap_config.user_search_filter,
                        "username": ldap_config.username_attr,
                        "idAttr": ldap_config.username_attr,
                        "emailAttr": ldap_config.username_attr,
                        "nameAttr": ldap_config.username_attr,
                    }
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

        gateway_manifest = ""
        if self.model.ingress_domain:
            gateway_manifest = f"""
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: dex-tls
  namespace: {namespace}
spec:
  secretName: dex-tls
  duration: 2160h # 90d
  renewBefore: 360h # 15d
  subject:
    organizations:
      - mindweaver
  isCA: false
  privateKey:
    algorithm: RSA
    encoding: PKCS1
    size: 2048
  usages:
    - server auth
    - client auth
  dnsNames:
    - dex.{self.model.ingress_domain}
  issuerRef:
    name: mindweaver-selfsigned-issuer
    kind: ClusterIssuer
    group: cert-manager.io
---
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: project-gateway
  namespace: {namespace}
spec:
  gatewayClassName: envoy-gateway
  listeners:
    - name: https
      protocol: HTTPS
      port: 443
      hostname: "dex.{self.model.ingress_domain}"
      tls:
        mode: Terminate
        certificateRefs:
          - group: ""
            kind: Secret
            name: dex-tls
---
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: dex-route
  namespace: {namespace}
spec:
  parentRefs:
    - name: project-gateway
  hostnames:
    - "dex.{self.model.ingress_domain}"
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /
      backendRefs:
        - name: dex
          port: 5556
"""

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

        gateway_manifest = f"""
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: dex-tls
  namespace: {namespace}
spec:
  secretName: dex-tls
  duration: 2160h # 90d
  renewBefore: 360h # 15d
  subject:
    organizations:
      - mindweaver
  isCA: false
  privateKey:
    algorithm: RSA
    encoding: PKCS1
    size: 2048
  usages:
    - server auth
    - client auth
  dnsNames:
    - dex.{self.model.ingress_domain}
  issuerRef:
    name: mindweaver-selfsigned-issuer
    kind: ClusterIssuer
    group: cert-manager.io
---
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: project-gateway
  namespace: {namespace}
spec:
  gatewayClassName: envoy-gateway
  listeners:
    - name: https
      protocol: HTTPS
      port: 443
      hostname: "dex.{self.model.ingress_domain}"
      tls:
        mode: Terminate
        certificateRefs:
          - group: ""
            kind: Secret
            name: dex-tls
---
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: dex-route
  namespace: {namespace}
spec:
  parentRefs:
    - name: project-gateway
  hostnames:
    - "dex.{self.model.ingress_domain}"
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /
      backendRefs:
        - name: dex
          port: 5556
---
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: envoy-{self.model.name}
  namespace: {namespace}
spec:
  secretName: envoy-{self.model.name}
  duration: 2160h # 90d
  renewBefore: 360h # 15d
  subject:
    organizations:
      - mindweaver
  isCA: false
  privateKey:
    algorithm: RSA
    encoding: PKCS1
    size: 2048
  usages:
    - server auth
    - client auth
  dnsNames:
    - "{self.model.ingress_domain}"
    - "*.{self.model.ingress_domain}"
  issuerRef:
    name: mindweaver-selfsigned-issuer
    kind: ClusterIssuer
    group: cert-manager.io
"""

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

