# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from mindweaver.celery_app import app
from mindweaver.fw.model import get_engine
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from mindweaver.service.project.service import ProjectService
from mindweaver.service.stack.model import Stack
from mindweaver.config import logger
from .base import run_async


@app.task
def install_dex_project_task(project_id: int):
    """Trigger Dex installation for a specific project namespace."""
    logger.info(f"Triggering Dex installation for project {project_id}")
    run_async(_install_dex_project_task(project_id))


async def _install_dex_project_task(project_id: int):
    engine = get_engine()
    async with AsyncSession(engine) as session:

        class MockRequest:
            headers = {}

        svc = ProjectService(MockRequest(), session)
        try:
            model = await svc.get(project_id)
            from mindweaver.service.project.actions import InstallDexAction

            action = InstallDexAction(model, svc)
            await action.run()
            # No dynamic state model database update needed as health state is dynamic
            logger.info(f"Successfully installed Dex for project {project_id}")
        except Exception as e:
            logger.error(
                f"Error installing Dex for project {project_id}: {e}"
            )


@app.task
def sync_project_integrations_task(project_id: int):
    """Trigger integrations sync for a specific project namespace."""
    logger.info(f"Triggering integrations sync for project {project_id}")
    run_async(_sync_project_integrations_task(project_id))


async def _sync_project_integrations_task(project_id: int):
    engine = get_engine()
    async with AsyncSession(engine) as session:

        class MockRequest:
            headers = {}

        svc = ProjectService(MockRequest(), session)
        try:
            model = await svc.get(project_id)
            from mindweaver.service.project.actions import SyncProjectIntegrationsAction

            action = SyncProjectIntegrationsAction(model, svc)
            await action.run()
            logger.info(f"Successfully synced integrations for project {project_id}")
        except Exception as e:
            logger.error(
                f"Error syncing integrations for project {project_id}: {e}"
            )


@app.task
def sync_trusted_certs_secret_task(project_id: int):
    """Trigger synchronization of the trusted-certs secret for a project."""
    logger.info(f"Triggering trusted-certs secret sync for project {project_id}")
    run_async(_sync_trusted_certs_secret_task(project_id))


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
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.serialization import pkcs12

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
        key=None,
        cert=None,
        cas=ca_certs,
        encryption_algorithm=serialization.BestAvailableEncryption(b"changeit")
    )

    return merged_pem, p12_data


async def _sync_trusted_certs_secret_task(project_id: int):
    """Synchronize only the trusted-certs secret to the project's Kubernetes cluster."""
    engine = get_engine()
    async with AsyncSession(engine) as session:
        from mindweaver.service.project.model import Project
        from mindweaver.service.k8s_cluster import K8sCluster
        from mindweaver.service.trusted_certs.model import TrustedCert
        import base64

        try:
            project = await session.get(Project, project_id)
            if not project or not project.k8s_cluster_id:
                logger.warning(
                    f"Project {project_id} or cluster not configured, skipping trusted-certs secret sync"
                )
                return

            cluster = await session.get(K8sCluster, project.k8s_cluster_id)
            if not cluster:
                logger.warning(
                    f"Cluster {project.k8s_cluster_id} not found, skipping trusted-certs secret sync"
                )
                return

            namespace = project.k8s_namespace or project.name

            # Fetch project CA certificate if it exists in Kubernetes
            project_ca_cert = ""
            try:
                from kubernetes import client, config
                import tempfile
                if cluster.type == "in-cluster":
                    config.load_incluster_config()
                else:
                    with tempfile.NamedTemporaryFile(mode="w") as kf:
                        kf.write(cluster.kubeconfig)
                        kf.flush()
                        config.load_kube_config(config_file=kf.name)
                core_api = client.CoreV1Api()
                ca_secret_name = f"{project.name}-ca-secret"
                secret_ca = core_api.read_namespaced_secret(ca_secret_name, namespace)
                if secret_ca and secret_ca.data:
                    pem_b64 = secret_ca.data.get("ca.crt") or secret_ca.data.get("tls.crt")
                    if pem_b64:
                        project_ca_cert = base64.b64decode(pem_b64).decode("utf-8")
            except Exception as e:
                logger.warning(f"Could not fetch project CA cert from {project.name}-ca-secret: {e}")

            stmt_certs = select(TrustedCert).where(TrustedCert.project_id == project_id)
            res_certs = await session.exec(stmt_certs)
            certs = res_certs.all()
            
            custom_certs_list = [c.certificate for c in certs]
            merged_pem, p12_data = generate_trust_stores(custom_certs_list, project_ca_cert)

            ca_certificates_b64 = base64.b64encode(merged_pem.encode("utf-8")).decode("utf-8")
            truststore_b64 = base64.b64encode(p12_data).decode("utf-8")

            trusted_certs = [
                {
                    "name": c.name,
                    "certificate": c.certificate,
                    "certificate_b64": base64.b64encode(c.certificate.encode("utf-8")).decode("utf-8")
                }
                for c in certs
            ]

            from mindweaver.service.project.actions import _get_jinja_env, apply_manifest_to_cluster
            env = _get_jinja_env()
            template = env.get_template("03-trusted-certs.yml.j2")
            manifest = template.render(
                name=project.name,
                namespace=namespace,
                trusted_certs=trusted_certs,
                ca_certificates_b64=ca_certificates_b64,
                truststore_b64=truststore_b64,
            )

            await apply_manifest_to_cluster(cluster, manifest)
            logger.info(f"Successfully synced trusted-certs secret for project {project_id}")
        except Exception as e:
            logger.error(
                f"Error syncing trusted-certs secret for project {project_id}: {e}"
            )

