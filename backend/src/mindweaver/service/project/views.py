# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from fastapi import Depends
from sqlmodel import select
from .service import ProjectService
from .model import Project
from .state import ProjectState

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


