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
from mindweaver.fw.util import sanitize_label_value

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


def _render_gateway_manifests(model, namespace: str, service_type: str = "LoadBalancer", nodeport: Optional[int] = None) -> str:
    """Render Gateway and Certificate manifests from YAML templates."""
    # Handle older test calls passing nodeport as the 3rd positional argument
    if isinstance(service_type, int):
        nodeport = service_type
        service_type = "NodePort"

    vars = {
        "name": model.name,
        "namespace": namespace,
        "ingress_domain": model.ingress_domain,
        "service_type": service_type,
        "nodeport": nodeport,
    }

    env = _get_jinja_env()
    templates = sorted(env.list_templates())
    rendered = []
    for template_name in templates:
        if not template_name.endswith((".yaml", ".yml", ".yml.j2", ".yaml.j2")) or "dex-app" in template_name or "03-trusted-certs" in template_name:
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
        Action is available only if the project is associated with a cluster and dex is enabled.
        """
        from mindweaver.config import settings
        if not settings.enable_dex:
            return False
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
                redirect_uris.append(f"https://{sp.name}.{self.model.ingress_domain}/api/v1/database/oauth2/")
                redirect_uris.append(f"http://{sp.name}.{self.model.ingress_domain}/api/v1/database/oauth2/")
            else:
                redirect_uris.append("http://localhost:8088/oauth-authorized/dex")
                redirect_uris.append("http://localhost:8088/api/v1/database/oauth2/")
            
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

        # Find active Airflow platforms with oidc_enabled
        from mindweaver.platform_service.airflow.model import AirflowPlatform
        stmt_airflow = select(AirflowPlatform).where(
            AirflowPlatform.project_id == self.model.id,
            AirflowPlatform.oidc_enabled == True
        )
        res_airflow = await self.session.exec(stmt_airflow)
        airflow_platforms = res_airflow.all()
        for af in airflow_platforms:
            redirect_uris = []
            if self.model.ingress_domain:
                redirect_uris.append(f"https://{af.name}.{self.model.ingress_domain}/auth/oauth-authorized/dex")
                redirect_uris.append(f"http://{af.name}.{self.model.ingress_domain}/auth/oauth-authorized/dex")
                redirect_uris.append(f"https://{af.name}.{self.model.ingress_domain}/api/v1/database/oauth2/")
                redirect_uris.append(f"http://{af.name}.{self.model.ingress_domain}/api/v1/database/oauth2/")
            else:
                redirect_uris.append("http://localhost:8080/oauth-authorized/dex")
                redirect_uris.append("http://localhost:8080/api/v1/database/oauth2/")

            secret_val = ""
            if af.oidc_client_secret:
                try:
                    secret_val = decrypt_password(af.oidc_client_secret)
                except Exception:
                    secret_val = af.oidc_client_secret

            static_clients.append({
                "id": af.name,
                "name": f"Airflow {af.name}",
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
                self.model, namespace, self.model.envoy_gateway_service_type, self.model.envoy_nodeport
            )

        # 6. Install Dex using ArgoCD Application
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

            async def run_kubectl_simple(*args):
                cmd = ["kubectl"]
                if kubeconfig_path:
                    cmd.extend(["--kubeconfig", kubeconfig_path])
                cmd.extend(args)
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await proc.communicate()
                if proc.returncode != 0:
                    raise RuntimeError(f"Kubectl command failed: {stderr.decode()}")
                return stdout.decode()

            # Render and apply Dex ArgoCD Application manifest
            chart_repo, chart_name, chart_version = "https://charts.dexidp.io", "dex", "0.24.1"
            if self.model.stack_id:
                from mindweaver.service.stack.model import Stack
                try:
                    stmt = select(Stack).where(Stack.id == self.model.stack_id)
                    res = await self.session.exec(stmt)
                    stack = res.one_or_none()
                    if stack:
                        r, c, v = stack.get_chart_for_component("dex", "main")
                        if r or c or v:
                            chart_repo = r or chart_repo
                            chart_name = c or chart_name
                            chart_version = v or chart_version
                except Exception as e:
                    logger.warning(f"Failed to resolve dex chart from stack: {e}")

            env = _get_jinja_env()
            template = env.get_template("dex-app.yml.j2")
            dex_manifest = template.render(
                name=self.model.name,
                project_name=self.model.name,
                namespace=namespace,
                dex_values=yaml.safe_dump(dex_values),
                project_title=sanitize_label_value(self.model.title),
                service_title="Dex",
                chart_repo=chart_repo,
                chart_name=chart_name,
                chart_version=chart_version,
            )

            await run_kubectl(dex_manifest)

            if gateway_manifest:
                # Ensure the dex certificate secret is recreated if deleted
                await run_kubectl_simple(
                    "delete", "certificate", "-n", namespace,
                    "dex-tls", "--ignore-not-found"
                )
                await run_kubectl(gateway_manifest)

        finally:
            if temp_kf:
                try:
                    os.unlink(temp_kf.name)
                except Exception:
                    pass
async def apply_manifest_to_cluster(cluster: K8sCluster, manifest: str) -> None:
    """Apply a Kubernetes manifest to a cluster using kubectl."""
    if not manifest.strip():
        return
    kubeconfig_path = None
    temp_kf = None
    temp_m = None
    try:
        if cluster.type == K8sClusterType.REMOTE:
            if not cluster.kubeconfig:
                raise ValueError(f"Cluster {cluster.name} has no kubeconfig")
            temp_kf = tempfile.NamedTemporaryFile(mode="w", delete=False)
            temp_kf.write(cluster.kubeconfig)
            temp_kf.flush()
            temp_kf.close()
            kubeconfig_path = temp_kf.name

        temp_m = tempfile.NamedTemporaryFile(mode="w", delete=False)
        temp_m.write(manifest)
        temp_m.flush()
        temp_m.close()

        cmd = ["kubectl"]
        if kubeconfig_path:
            cmd.extend(["--kubeconfig", kubeconfig_path])
        cmd.extend(["apply", "--server-side", "--force-conflicts", "-f", temp_m.name])

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
        if temp_kf:
            try:
                os.unlink(temp_kf.name)
            except Exception:
                pass


def generate_trust_stores(custom_certs_list: list[str], project_ca_cert: str = "") -> tuple[str, bytes]:
    import os
    system_bundle = ""
    paths = [
        "/etc/ssl/certs/ca-certificates.crt",
        "/etc/pki/tls/certs/ca-bundle.crt",
        "/etc/ssl/ca-bundle.pem",
        "/etc/ssl/cert.pem",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                with open(p, "r") as f:
                    system_bundle = f.read()
                break
            except Exception:
                continue

    if not system_bundle:
        try:
            import certifi
            with open(certifi.where(), "r") as f:
                system_bundle = f.read()
        except Exception:
            pass

    pem_parts = []
    if system_bundle:
        pem_parts.append(system_bundle)
    if project_ca_cert:
        pem_parts.append(project_ca_cert)
    for cert in custom_certs_list:
        pem_parts.append(cert)

    merged_pem = "\n".join(part.strip() for part in pem_parts if part.strip())

    import datetime
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives.serialization import pkcs12

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "mindweaver-truststore")])
    dummy_cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
    ).not_valid_after(
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)
    ).sign(key, hashes.SHA256())

    ca_certs = []
    for part in merged_pem.split("-----END CERTIFICATE-----"):
        part = part.strip()
        if not part:
            continue
        pem_str = part + "\n-----END CERTIFICATE-----"
        try:
            ca_cert = x509.load_pem_x509_certificate(pem_str.encode("utf-8"))
            ca_certs.append(ca_cert)
        except Exception:
            continue

    p12_data = pkcs12.serialize_key_and_certificates(
        name=b"truststore",
        key=key,
        cert=dummy_cert,
        cas=ca_certs,
        encryption_algorithm=serialization.BestAvailableEncryption(b"changeit")
    )

    return merged_pem, p12_data


@ProjectService.register_action("sync_project_integrations")
class SyncProjectIntegrationsAction(BaseAction):
    """
    Action to sync project integrations: create ArgoCD project, deploy self-signed issuer, and deploy gateway.
    """

    async def available(self) -> bool:
        return self.model.k8s_cluster_id is not None and bool(self.model.ingress_domain)

    async def __call__(self, **kwargs):
        from mindweaver.tasks.project_tasks import sync_project_integrations_task

        sync_project_integrations_task.delay(self.model.id)
        return {
            "status": "success",
            "message": "Project integrations synchronization triggered.",
        }

    async def run(self):
        logger.info(f"Syncing integrations for project {self.model.name}")

        stmt_cluster = select(K8sCluster).where(K8sCluster.id == self.model.k8s_cluster_id)
        res_cluster = await self.session.exec(stmt_cluster)
        cluster = res_cluster.one()

        namespace = self.model.k8s_namespace or self.model.name

        # 1. Check/Persist nodeport
        if not self.model.envoy_nodeport:
            existing_port = await _get_existing_nodeport(cluster, namespace)
            if existing_port:
                self.model.envoy_nodeport = existing_port
                self.session.add(self.model)
                await self.session.commit()
                await self.session.refresh(self.model)

        # 2. Render templates
        env = _get_jinja_env()
        
        # 2a. ArgoCD Project
        argocd_project_template = env.get_template("00-argocd-project.yml.j2")
        argocd_project_manifest = argocd_project_template.render(
            name=self.model.name,
            namespace=namespace,
        )

        # 2b. Issuer
        issuer_template = env.get_template("02-self-signed-issuer.yml.j2")
        issuer_manifest = issuer_template.render(
            name=self.model.name,
            namespace=namespace,
        )

        # 2c. Gateway
        gateway_manifest = ""
        if self.model.ingress_domain:
            gateway_manifest = _render_gateway_manifests(
                self.model, namespace, self.model.envoy_gateway_service_type, self.model.envoy_nodeport
            )

        # 2d. Trusted Certificates Secret
        from mindweaver.service.trusted_certs.model import TrustedCert
        import base64
        stmt_certs = select(TrustedCert).where(TrustedCert.project_id == self.model.id)
        res_certs = await self.session.exec(stmt_certs)
        certs = res_certs.all()
        trusted_certs = [
            {
                "name": c.name,
                "certificate": c.certificate,
                "certificate_b64": base64.b64encode(c.certificate.encode("utf-8")).decode("utf-8")
            }
            for c in certs
        ]

        # Fetch project CA certificate if it exists in Kubernetes
        project_ca_cert = ""
        try:
            from kubernetes import client, config
            if cluster.type == K8sClusterType.IN_CLUSTER:
                config.load_incluster_config()
            else:
                if cluster.kubeconfig:
                    with tempfile.NamedTemporaryFile(mode="w", delete=False) as kf:
                        kf.write(cluster.kubeconfig)
                        kf.flush()
                        config.load_kube_config(config_file=kf.name)
                        os.unlink(kf.name)
            core_api = client.CoreV1Api()
            ca_secret_name = f"{self.model.name}-ca-secret"
            secret_ca = core_api.read_namespaced_secret(ca_secret_name, namespace)
            if secret_ca and secret_ca.data:
                pem_b64 = secret_ca.data.get("ca.crt") or secret_ca.data.get("tls.crt")
                if pem_b64:
                    project_ca_cert = base64.b64decode(pem_b64).decode("utf-8")
        except Exception as e:
            logger.warning(f"Could not fetch project CA cert from {self.model.name}-ca-secret: {e}")

        custom_certs_list = [c.certificate for c in certs]
        merged_pem, p12_data = generate_trust_stores(custom_certs_list, project_ca_cert)

        ca_certificates_b64 = base64.b64encode(merged_pem.encode("utf-8")).decode("utf-8")
        truststore_b64 = base64.b64encode(p12_data).decode("utf-8")
        
        trusted_certs_template = env.get_template("03-trusted-certs.yml.j2")
        trusted_certs_manifest = trusted_certs_template.render(
            name=self.model.name,
            namespace=namespace,
            trusted_certs=trusted_certs,
            ca_certificates_b64=ca_certificates_b64,
            truststore_b64=truststore_b64,
        )

        # 3. Apply manifests
        await apply_manifest_to_cluster(cluster, argocd_project_manifest)
        await apply_manifest_to_cluster(cluster, issuer_manifest)
        if trusted_certs_manifest:
            await apply_manifest_to_cluster(cluster, trusted_certs_manifest)
        if gateway_manifest:
            await apply_manifest_to_cluster(cluster, gateway_manifest)


