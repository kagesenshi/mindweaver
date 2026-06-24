# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import logging
import tempfile
import asyncio
import os
from fastapi import Depends, HTTPException
from sqlmodel import select
from .service import ProjectService
from .model import Project
from .state import ProjectState
from mindweaver.service.k8s_cluster import K8sCluster, K8sClusterType
from mindweaver.service.k8s_cluster.service import K8sClusterService
from mindweaver.service.project.actions import _get_jinja_env

logger = logging.getLogger(__name__)

# Register state
ProjectService.with_state()(ProjectState)


@ProjectService.model_view("POST", "/_refresh")
async def refresh_project_status_view(
    id: int, svc: ProjectService = Depends(ProjectService.get_service)
):
    """Manual project status refresh view"""
    from mindweaver.service.k8s_cluster.service import K8sClusterService
    model = await svc.get(id)
    if model.k8s_cluster_id:
        cluster_svc = K8sClusterService(svc.request, svc.session)
        cluster_model = await cluster_svc.get(model.k8s_cluster_id)
        await cluster_svc.poll_status(cluster_model)
    return {"status": "success"}


@ProjectService.model_view("GET", "/_download-haproxy-cert")
async def download_haproxy_cert_view(
    id: int, svc: ProjectService = Depends(ProjectService.get_service)
):
    """Retrieve and download the combined self-signed cert + key PEM for HAProxy"""
    import base64
    import tempfile
    import asyncio
    from fastapi import Response, HTTPException
    from kubernetes import client, config
    from mindweaver.service.k8s_cluster import K8sCluster, K8sClusterType
    from mindweaver.service.k8s_cluster.service import K8sClusterService

    model = await svc.get(id)
    if not model.k8s_cluster_id:
        raise HTTPException(status_code=400, detail="Project has no cluster configured")

    cluster_svc = K8sClusterService(svc.request, svc.session)
    cluster = await cluster_svc.get(model.k8s_cluster_id)

    namespace = model.k8s_namespace or model.name
    secret_name = f"envoy-{model.name}"

    def _get_secret_pem():
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
            secret = core_v1.read_namespaced_secret(name=secret_name, namespace=namespace)
            
            tls_crt = secret.data.get("tls.crt")
            tls_key = secret.data.get("tls.key")
            if not tls_crt or not tls_key:
                return None
            
            crt_decoded = base64.b64decode(tls_crt).decode("utf-8")
            key_decoded = base64.b64decode(tls_key).decode("utf-8")
            
            pem = f"{key_decoded}\n{crt_decoded}"
            return pem
        except Exception:
            return None

    pem_content = await asyncio.to_thread(_get_secret_pem)
    if not pem_content:
        raise HTTPException(
            status_code=404, 
            detail=f"Certificate secret '{secret_name}' not found or not ready yet. Please deploy/update the Envoy Gateway."
        )

    return Response(
        content=pem_content,
        media_type="application/x-pem-file",
        headers={"Content-Disposition": f"attachment; filename={secret_name}.pem"}
    )


@ProjectService.model_view("GET", "/_cert_manager")
async def get_project_cert_manager_resources(
    id: int, svc: ProjectService = Depends(ProjectService.get_service)
):
    """Retrieve issuers and certificates from the cluster scoped to the project namespace"""
    import tempfile
    import asyncio
    from kubernetes import client, config
    from mindweaver.service.k8s_cluster import K8sCluster, K8sClusterType
    from mindweaver.service.k8s_cluster.service import K8sClusterService

    model = await svc.get(id)
    if not model.k8s_cluster_id:
        return {"issuers": [], "certificates": []}

    cluster_svc = K8sClusterService(svc.request, svc.session)
    cluster = await cluster_svc.get(model.k8s_cluster_id)
    namespace = model.k8s_namespace or model.name

    def _get_status(item):
        conditions = item.get("status", {}).get("conditions", [])
        for cond in conditions:
            if cond.get("type") == "Ready":
                return "Ready" if cond.get("status") == "True" else f"Not Ready ({cond.get('reason', '')})"
        return "Unknown"

    def _get_resources():
        try:
            if cluster.type == K8sClusterType.IN_CLUSTER:
                config.load_incluster_config()
            else:
                if not cluster.kubeconfig:
                    return {"issuers": [], "certificates": []}
                with tempfile.NamedTemporaryFile(mode="w") as kf:
                    kf.write(cluster.kubeconfig)
                    kf.flush()
                    config.load_kube_config(config_file=kf.name)
        except Exception as e:
            logger.warning(f"Failed to load kubeconfig for cluster {cluster.name}: {e}")
            return {"issuers": [], "certificates": []}

        custom_api = client.CustomObjectsApi()
        issuers = []
        certificates = []

        # Get Issuers (namespace-scoped to project)
        try:
            res = custom_api.list_namespaced_custom_object(
                group="cert-manager.io",
                version="v1",
                namespace=namespace,
                plural="issuers",
            )
            allowed_names = {
                f"{model.name}-bootstrap-issuer",
                f"{model.name}-selfsigned-issuer",
            }
            for item in res.get("items", []):
                name = item["metadata"]["name"]
                if name in allowed_names:
                    issuers.append({
                        "name": name,
                        "namespace": namespace,
                        "kind": "Issuer",
                        "status": _get_status(item),
                    })
        except Exception as e:
            logger.warning(f"Failed to list issuers in project namespace {namespace}: {e}")

        # Get Certificates (namespace-scoped to project)
        try:
            res = custom_api.list_namespaced_custom_object(
                group="cert-manager.io",
                version="v1",
                namespace=namespace,
                plural="certificates",
            )
            for item in res.get("items", []):
                spec = item.get("spec", {})
                status_info = item.get("status", {})
                certificates.append({
                    "name": item["metadata"]["name"],
                    "namespace": namespace,
                    "issuer_name": spec.get("issuerRef", {}).get("name"),
                    "issuer_kind": spec.get("issuerRef", {}).get("kind", "Issuer"),
                    "status": _get_status(item),
                    "dns_names": spec.get("dnsNames", []),
                    "secret_name": spec.get("secretName"),
                    "not_after": status_info.get("notAfter"),
                    "not_before": status_info.get("notBefore"),
                    "conditions": status_info.get("conditions", []),
                })
        except Exception as e:
            logger.warning(f"Failed to list certificates in project namespace {namespace}: {e}")

        return {"issuers": issuers, "certificates": certificates}

    return await asyncio.to_thread(_get_resources)


@ProjectService.model_view("GET", "/_issuer_cert")
async def get_project_issuer_ca_cert(
    id: int,
    name: str,
    kind: str,
    namespace: str | None = None,
    svc: ProjectService = Depends(ProjectService.get_service),
):
    """Retrieve PEM CA certificate for an issuer scoped to project's cluster"""
    import base64
    import tempfile
    import asyncio
    from fastapi import HTTPException
    from kubernetes import client, config
    from mindweaver.service.k8s_cluster import K8sCluster, K8sClusterType
    from mindweaver.service.k8s_cluster.service import K8sClusterService

    model = await svc.get(id)
    if not model.k8s_cluster_id:
        raise HTTPException(status_code=400, detail="Project has no cluster configured")

    cluster_svc = K8sClusterService(svc.request, svc.session)
    cluster = await cluster_svc.get(model.k8s_cluster_id)

    def _get_issuer_cert():
        try:
            if cluster.type == K8sClusterType.IN_CLUSTER:
                config.load_incluster_config()
            else:
                if not cluster.kubeconfig:
                    raise ValueError(f"Cluster {cluster.name} has no kubeconfig")
                with tempfile.NamedTemporaryFile(mode="w") as kf:
                    kf.write(cluster.kubeconfig)
                    kf.flush()
                    config.load_kube_config(config_file=kf.name)
        except Exception as e:
            logger.error(f"Failed to load kubeconfig for cluster {cluster.name}: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to load Kubernetes config: {e}")

        custom_api = client.CustomObjectsApi()
        
        # 1. Fetch Issuer / ClusterIssuer
        try:
            if kind == "ClusterIssuer":
                issuer = custom_api.get_cluster_custom_object(
                    group="cert-manager.io",
                    version="v1",
                    plural="clusterissuers",
                    name=name,
                )
            else:
                issuer = custom_api.get_namespaced_custom_object(
                    group="cert-manager.io",
                    version="v1",
                    plural="issuers",
                    namespace=namespace or "default",
                    name=name,
                )
        except Exception as e:
            logger.error(f"Failed to fetch {kind} {name}: {e}")
            raise HTTPException(status_code=404, detail=f"Issuer '{name}' not found: {e}")

        spec = issuer.get("spec", {})
        secret_name = spec.get("ca", {}).get("secretName")
        if not secret_name:
            raise HTTPException(
                status_code=400,
                detail=f"Issuer '{name}' does not have a CA secretName defined in spec.ca.",
            )

        # 2. Fetch the Secret
        core_api = client.CoreV1Api()
        secret = None
        
        search_namespace = namespace
        if not search_namespace:
            try:
                secret = core_api.read_namespaced_secret(secret_name, "cert-manager")
            except Exception:
                try:
                    secrets = core_api.list_secret_for_all_namespaces(
                        field_selector=f"metadata.name={secret_name}"
                    )
                    if secrets.items:
                        secret = secrets.items[0]
                except Exception as ex:
                    logger.warning(f"Failed to search secret globally: {ex}")
        else:
            try:
                secret = core_api.read_namespaced_secret(secret_name, search_namespace)
            except Exception as e:
                logger.error(f"Failed to read secret {secret_name} in {search_namespace}: {e}")

        if not secret or not secret.data:
            raise HTTPException(
                status_code=404,
                detail=f"Secret '{secret_name}' containing CA cert was not found.",
            )

        # 3. Extract CA cert PEM
        pem_b64 = secret.data.get("ca.crt") or secret.data.get("tls.crt")
        if not pem_b64:
            raise HTTPException(
                status_code=400,
                detail=f"Secret '{secret_name}' does not contain ca.crt or tls.crt keys.",
            )

        try:
            pem_data = base64.b64decode(pem_b64).decode("utf-8")
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to decode base64 certificate data: {e}",
            )

        return {"pem": pem_data, "filename": f"{name}-ca.crt"}

    return await asyncio.to_thread(_get_issuer_cert)


@ProjectService.model_view("POST", "/_deploy_issuer")
async def deploy_project_issuer_view(
    id: int, svc: ProjectService = Depends(ProjectService.get_service)
):
    """Deploy self-signed issuer resources for the project"""
    model = await svc.get(id)
    if not model.k8s_cluster_id:
        raise HTTPException(status_code=400, detail="Project has no cluster configured")

    from mindweaver.service.k8s_cluster.service import K8sClusterService
    cluster_svc = K8sClusterService(svc.request, svc.session)
    cluster = await cluster_svc.get(model.k8s_cluster_id)
    namespace = model.k8s_namespace or model.name

    # Load and render template
    env = _get_jinja_env()
    template = env.get_template("02-self-signed-issuer.yml.j2")
    manifest = template.render(
        name=model.name,
        namespace=namespace,
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

        async def run_kubectl(manifest_content: str):
            temp_m = None
            try:
                temp_m = tempfile.NamedTemporaryFile(mode="w", delete=False)
                temp_m.write(manifest_content)
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

        await run_kubectl(manifest)
    finally:
        if temp_kf:
            try:
                os.unlink(temp_kf.name)
            except Exception:
                pass

    return {"status": "success", "message": "Project issuer deployed successfully."}




