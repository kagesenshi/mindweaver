# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import asyncio
import base64
import logging
import tempfile
from fastapi import Depends, HTTPException
from kubernetes import client, config
from .service import K8sClusterService
from .state import K8sClusterState
from .model import K8sClusterType

logger = logging.getLogger(__name__)

# Register state
K8sClusterService.with_state()(K8sClusterState)


@K8sClusterService.model_view("POST", "/_refresh")
async def refresh_status_view(
    id: int, svc: K8sClusterService = Depends(K8sClusterService.get_service)
):
    """Manual status refresh view"""
    model = await svc.get(id)
    await svc.poll_status(model)
    return {"status": "success"}


@K8sClusterService.model_view("GET", "/_cert_manager")
async def get_cert_manager_resources(
    id: int, svc: K8sClusterService = Depends(K8sClusterService.get_service)
):
    """Retrieve issuers and certificates from the cluster"""
    model = await svc.get(id)

    def _get_status(item):
        conditions = item.get("status", {}).get("conditions", [])
        for cond in conditions:
            if cond.get("type") == "Ready":
                return "Ready" if cond.get("status") == "True" else f"Not Ready ({cond.get('reason', '')})"
        return "Unknown"

    def _get_resources():
        try:
            if model.type == K8sClusterType.IN_CLUSTER:
                config.load_incluster_config()
            else:
                if not model.kubeconfig:
                    return {"issuers": [], "certificates": []}
                with tempfile.NamedTemporaryFile(mode="w") as kf:
                    kf.write(model.kubeconfig)
                    kf.flush()
                    config.load_kube_config(config_file=kf.name)
        except Exception as e:
            logger.warning(f"Failed to load kubeconfig for cluster {model.name}: {e}")
            return {"issuers": [], "certificates": []}

        custom_api = client.CustomObjectsApi()
        issuers = []
        certificates = []

        # Get Issuers (namespace-scoped)
        try:
            res = custom_api.list_cluster_custom_object(
                group="cert-manager.io",
                version="v1",
                plural="issuers",
            )
            for item in res.get("items", []):
                issuers.append({
                    "name": item["metadata"]["name"],
                    "namespace": item["metadata"].get("namespace", "default"),
                    "kind": "Issuer",
                    "status": _get_status(item),
                })
        except Exception as e:
            logger.warning(f"Failed to list issuers: {e}")

        # Get ClusterIssuers
        try:
            res = custom_api.list_cluster_custom_object(
                group="cert-manager.io",
                version="v1",
                plural="clusterissuers",
            )
            for item in res.get("items", []):
                issuers.append({
                    "name": item["metadata"]["name"],
                    "namespace": None,
                    "kind": "ClusterIssuer",
                    "status": _get_status(item),
                })
        except Exception as e:
            logger.warning(f"Failed to list clusterissuers: {e}")

        # Get Certificates
        try:
            res = custom_api.list_cluster_custom_object(
                group="cert-manager.io",
                version="v1",
                plural="certificates",
            )
            for item in res.get("items", []):
                spec = item.get("spec", {})
                status_info = item.get("status", {})
                certificates.append({
                    "name": item["metadata"]["name"],
                    "namespace": item["metadata"].get("namespace", "default"),
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
            logger.warning(f"Failed to list certificates: {e}")

        return {"issuers": issuers, "certificates": certificates}

    return await asyncio.to_thread(_get_resources)


@K8sClusterService.model_view("GET", "/_issuer_cert")
async def get_issuer_ca_cert(
    id: int,
    name: str,
    kind: str,
    namespace: str | None = None,
    svc: K8sClusterService = Depends(K8sClusterService.get_service),
):
    """Retrieve PEM CA certificate for an issuer"""
    model = await svc.get(id)

    def _get_issuer_cert():
        try:
            if model.type == K8sClusterType.IN_CLUSTER:
                config.load_incluster_config()
            else:
                if not model.kubeconfig:
                    raise ValueError(f"Cluster {model.name} has no kubeconfig")
                with tempfile.NamedTemporaryFile(mode="w") as kf:
                    kf.write(model.kubeconfig)
                    kf.flush()
                    config.load_kube_config(config_file=kf.name)
        except Exception as e:
            logger.error(f"Failed to load kubeconfig for cluster {model.name}: {e}")
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
            # ClusterIssuer secret might reside in cert-manager or namespace where cert-manager runs
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

