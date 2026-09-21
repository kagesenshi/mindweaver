# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import logging
import tempfile
import asyncio
import os
import base64
import datetime
import cryptography
from cryptography import x509
from cryptography.x509.oid import NameOID
from pydantic import BaseModel
from fastapi import Depends, HTTPException, Response
from kubernetes import client, config
from sqlmodel import select
from .service import ProjectService
from .model import Project
from .state import ProjectState
from mindweaver.service.k8s_cluster import K8sCluster, K8sClusterType
from mindweaver.service.k8s_cluster.service import K8sClusterService
from mindweaver.service.project.actions import _get_jinja_env
from mindweaver.fw.cert_manager import reissue_certificate

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
        core_api = client.CoreV1Api()
        issuers = []
        certificates = []
        issuer_ca_secrets = {}

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
                ca_sec = item.get("spec", {}).get("ca", {}).get("secretName")
                if ca_sec:
                    issuer_ca_secrets[name] = ca_sec
        except Exception as e:
            logger.warning(f"Failed to list issuers in project namespace {namespace}: {e}")

        # Fetch secrets in namespace for certificate validity evaluation
        secrets_map = {}
        try:
            sec_list = core_api.list_namespaced_secret(namespace=namespace)
            for s in getattr(sec_list, "items", []):
                secrets_map[s.metadata.name] = s
        except Exception as e:
            logger.warning(f"Failed to list secrets in project namespace {namespace}: {e}")

        ca_certs_cache: dict[str, x509.Certificate | None] = {}

        def _get_ca_cert(ca_secret_name: str) -> x509.Certificate | None:
            """Retrieve and parse a CA certificate from secrets cache or API."""
            if ca_secret_name in ca_certs_cache:
                return ca_certs_cache[ca_secret_name]
            sec = secrets_map.get(ca_secret_name)
            if not sec:
                try:
                    sec = core_api.read_namespaced_secret(ca_secret_name, namespace)
                    if sec:
                        secrets_map[ca_secret_name] = sec
                except Exception:
                    pass
            if not sec or not sec.data:
                ca_certs_cache[ca_secret_name] = None
                return None
            raw_b64 = sec.data.get("tls.crt") or sec.data.get("ca.crt")
            if not raw_b64:
                ca_certs_cache[ca_secret_name] = None
                return None
            try:
                raw_bytes = base64.b64decode(raw_b64)
                parsed = x509.load_pem_x509_certificate(raw_bytes)
                ca_certs_cache[ca_secret_name] = parsed
                return parsed
            except Exception as ex:
                logger.warning(f"Failed to parse CA certificate from {ca_secret_name}: {ex}")
                ca_certs_cache[ca_secret_name] = None
                return None

        now = datetime.datetime.now(datetime.timezone.utc)

        def _evaluate_cert_status(item: dict, cm_status: str) -> tuple[str, str | None]:
            """Evaluate the real certificate validity state if cert-manager reported Ready.

            Returns (status_string, status_reason).
            """
            if cm_status != "Ready":
                return cm_status, None

            spec = item.get("spec", {})
            secret_name = spec.get("secretName")
            issuer_name = spec.get("issuerRef", {}).get("name")

            sec = secrets_map.get(secret_name)
            if not sec and secret_name:
                try:
                    sec = core_api.read_namespaced_secret(secret_name, namespace)
                    if sec:
                        secrets_map[secret_name] = sec
                except Exception:
                    pass

            if not sec or not sec.data or not sec.data.get("tls.crt"):
                return "Invalid", "Secret missing or empty"

            try:
                cert_bytes = base64.b64decode(sec.data["tls.crt"])
                leaf_cert = x509.load_pem_x509_certificate(cert_bytes)
            except Exception as ex:
                return "Invalid", f"Failed to parse certificate: {ex}"

            # Check expiration
            if now > leaf_cert.not_valid_after_utc:
                return "Expired", f"Certificate expired on {leaf_cert.not_valid_after_utc.isoformat()}"
            if now < leaf_cert.not_valid_before_utc:
                return "Invalid", f"Certificate not valid until {leaf_cert.not_valid_before_utc.isoformat()}"

            # Check CA and signature
            ca_sec_name = issuer_ca_secrets.get(issuer_name) or f"{model.name}-ca-secret"
            ca_cert = _get_ca_cert(ca_sec_name)
            if ca_cert:
                if now > ca_cert.not_valid_after_utc:
                    return "Invalid", f"Project CA expired on {ca_cert.not_valid_after_utc.isoformat()}"

                # Check AKI vs SKI match if AKI is present
                try:
                    leaf_aki = leaf_cert.extensions.get_extension_for_class(x509.AuthorityKeyIdentifier).value.key_identifier
                    ca_ski = ca_cert.extensions.get_extension_for_class(x509.SubjectKeyIdentifier).value.digest
                    if leaf_aki and ca_ski and leaf_aki != ca_ski:
                        return "Invalid", "Certificate AKI does not match active Project CA SKI. Certificate was issued by an older or different CA."
                except cryptography.x509.ExtensionNotFound:
                    pass

                try:
                    leaf_cert.verify_directly_issued_by(ca_cert)
                except Exception as sig_ex:
                    return "Invalid", f"Signature verification failed against Project CA: {sig_ex}"

            return "Ready", None

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
                cm_status = _get_status(item)
                final_status, status_reason = _evaluate_cert_status(item, cm_status)
                certificates.append({
                    "name": item["metadata"]["name"],
                    "namespace": namespace,
                    "issuer_name": spec.get("issuerRef", {}).get("name"),
                    "issuer_kind": spec.get("issuerRef", {}).get("kind", "Issuer"),
                    "status": final_status,
                    "status_reason": status_reason,
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


def _parse_x509_cert(cert: x509.Certificate, raw_pem: str) -> dict:
    """Parse an X.509 Certificate object into a detailed dictionary."""
    now = datetime.datetime.now(datetime.timezone.utc)

    subject_cn = None
    for attr in cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME):
        subject_cn = attr.value

    issuer_cn = None
    for attr in cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME):
        issuer_cn = attr.value

    dns_names = []
    try:
        san_ext = cert.extensions.get_extension_for_oid(x509.ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
        dns_names = san_ext.value.get_values_for_type(x509.DNSName)
    except x509.ExtensionNotFound:
        pass

    ski = None
    try:
        ski_ext = cert.extensions.get_extension_for_oid(x509.ExtensionOID.SUBJECT_KEY_IDENTIFIER)
        ski = ski_ext.value.key_identifier.hex()
    except x509.ExtensionNotFound:
        pass

    aki = None
    try:
        aki_ext = cert.extensions.get_extension_for_oid(x509.ExtensionOID.AUTHORITY_KEY_IDENTIFIER)
        if aki_ext.value.key_identifier:
            aki = aki_ext.value.key_identifier.hex()
    except x509.ExtensionNotFound:
        pass

    is_ca = False
    try:
        bc_ext = cert.extensions.get_extension_for_oid(x509.ExtensionOID.BASIC_CONSTRAINTS)
        is_ca = bc_ext.value.ca
    except x509.ExtensionNotFound:
        pass

    is_expired = now > cert.not_valid_after_utc or now < cert.not_valid_before_utc
    is_valid_dates = cert.not_valid_before_utc <= now <= cert.not_valid_after_utc

    return {
        "subject": {
            "rfc4514": cert.subject.rfc4514_string(),
            "common_name": subject_cn,
        },
        "issuer": {
            "rfc4514": cert.issuer.rfc4514_string(),
            "common_name": issuer_cn,
        },
        "serial_number": hex(cert.serial_number)[2:].upper(),
        "not_before": cert.not_valid_before_utc.isoformat(),
        "not_after": cert.not_valid_after_utc.isoformat(),
        "is_expired": is_expired,
        "is_valid_dates": is_valid_dates,
        "is_ca": is_ca,
        "dns_names": dns_names,
        "signature_algorithm": cert.signature_algorithm_oid._name,
        "subject_key_identifier": ski,
        "authority_key_identifier": aki,
        "pem": raw_pem,
    }


@ProjectService.model_view("GET", "/_certificate_details")
async def get_project_certificate_details(
    id: int,
    name: str,
    namespace: str | None = None,
    svc: ProjectService = Depends(ProjectService.get_service),
):
    """Retrieve detailed X.509 certificate information, CA information, and validation status."""
    model = await svc.get(id)
    if not model.k8s_cluster_id:
        raise HTTPException(status_code=400, detail="Project has no cluster configured")

    cluster_svc = K8sClusterService(svc.request, svc.session)
    cluster = await cluster_svc.get(model.k8s_cluster_id)
    cert_namespace = namespace or model.k8s_namespace or model.name

    def _get_details():
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
        core_api = client.CoreV1Api()

        try:
            cert_obj = custom_api.get_namespaced_custom_object(
                group="cert-manager.io",
                version="v1",
                namespace=cert_namespace,
                plural="certificates",
                name=name,
            )
        except Exception as e:
            logger.warning(f"Certificate {name} not found in {cert_namespace}: {e}")
            raise HTTPException(status_code=404, detail=f"Certificate '{name}' not found: {e}")

        spec = cert_obj.get("spec", {})
        status_info = cert_obj.get("status", {})
        secret_name = spec.get("secretName")
        issuer_ref = spec.get("issuerRef", {})
        conditions = status_info.get("conditions", [])

        secret = None
        if secret_name:
            try:
                secret = core_api.read_namespaced_secret(secret_name, cert_namespace)
            except Exception:
                secret = None

        if not secret or not secret.data or not secret.data.get("tls.crt"):
            return {
                "name": name,
                "namespace": cert_namespace,
                "secret_name": secret_name,
                "secret_found": False,
                "certificate": None,
                "ca": None,
                "issuer_ref": issuer_ref,
                "conditions": conditions,
                "validation": {
                    "is_valid": False,
                    "status": "NOT_ISSUED",
                    "signature_valid": False,
                    "message": f"Certificate secret '{secret_name}' has not been populated by cert-manager.",
                },
            }

        try:
            tls_crt_bytes = base64.b64decode(secret.data["tls.crt"])
            tls_crt_pem = tls_crt_bytes.decode("utf-8")
            leaf_cert = x509.load_pem_x509_certificate(tls_crt_bytes)
            leaf_info = _parse_x509_cert(leaf_cert, tls_crt_pem)
        except Exception as e:
            return {
                "name": name,
                "namespace": cert_namespace,
                "secret_name": secret_name,
                "secret_found": True,
                "certificate": None,
                "ca": None,
                "issuer_ref": issuer_ref,
                "conditions": conditions,
                "validation": {
                    "is_valid": False,
                    "status": "ERROR",
                    "signature_valid": False,
                    "message": f"Failed to parse leaf certificate: {e}",
                },
            }

        ca_secret_name = f"{model.name}-ca-secret"
        ca_secret_namespace = cert_namespace

        issuer_name = issuer_ref.get("name")
        issuer_kind = issuer_ref.get("kind", "Issuer")
        if issuer_name:
            try:
                if issuer_kind == "ClusterIssuer":
                    issuer_obj = custom_api.get_cluster_custom_object(
                        group="cert-manager.io",
                        version="v1",
                        plural="clusterissuers",
                        name=issuer_name,
                    )
                else:
                    issuer_obj = custom_api.get_namespaced_custom_object(
                        group="cert-manager.io",
                        version="v1",
                        namespace=cert_namespace,
                        plural="issuers",
                        name=issuer_name,
                    )
                spec_ca = issuer_obj.get("spec", {}).get("ca", {})
                if spec_ca.get("secretName"):
                    ca_secret_name = spec_ca.get("secretName")
            except Exception as e:
                logger.debug(f"Could not fetch issuer object {issuer_name}: {e}")

        ca_secret = None
        try:
            ca_secret = core_api.read_namespaced_secret(ca_secret_name, ca_secret_namespace)
        except Exception:
            pass

        ca_cert = None
        ca_info = None

        ca_pem_b64 = None
        if ca_secret and ca_secret.data:
            ca_pem_b64 = ca_secret.data.get("ca.crt") or ca_secret.data.get("tls.crt")
        if not ca_pem_b64 and secret.data.get("ca.crt"):
            ca_pem_b64 = secret.data.get("ca.crt")

        if ca_pem_b64:
            try:
                ca_bytes = base64.b64decode(ca_pem_b64)
                ca_pem = ca_bytes.decode("utf-8")
                ca_cert = x509.load_pem_x509_certificate(ca_bytes)
                ca_info = _parse_x509_cert(ca_cert, ca_pem)
                ca_info["name"] = ca_secret_name
                ca_info["exists"] = True
                ca_info["is_valid"] = ca_info["is_valid_dates"] and ca_info["is_ca"]
            except Exception as e:
                ca_info = {
                    "name": ca_secret_name,
                    "exists": True,
                    "is_valid": False,
                    "is_expired": False,
                    "error": f"Failed to parse CA certificate: {e}",
                }
        else:
            ca_info = {
                "name": ca_secret_name,
                "exists": False,
                "is_valid": False,
                "is_expired": False,
                "error": f"CA secret '{ca_secret_name}' not found.",
            }

        validation = {
            "is_valid": False,
            "signature_valid": False,
            "status": "UNKNOWN",
            "message": "",
            "aki_matches_ski": None,
        }

        if leaf_info.get("authority_key_identifier") and ca_info.get("subject_key_identifier"):
            validation["aki_matches_ski"] = (
                leaf_info["authority_key_identifier"].lower() == ca_info["subject_key_identifier"].lower()
            )

        if not ca_info.get("exists"):
            validation["status"] = "CA_MISSING"
            validation["message"] = f"Project CA secret '{ca_secret_name}' was not found in namespace '{ca_secret_namespace}'."
        elif not ca_info.get("is_valid"):
            validation["status"] = "CA_INVALID"
            if ca_info.get("is_expired"):
                validation["message"] = f"Project CA certificate has expired on {ca_info['not_after']}."
            elif not ca_info.get("is_ca"):
                validation["message"] = "Project CA certificate is missing the BasicConstraints CA flag."
            else:
                validation["message"] = ca_info.get("error") or "Project CA certificate is not currently valid."
        elif leaf_info.get("is_expired"):
            validation["status"] = "EXPIRED"
            validation["message"] = f"Certificate has expired on {leaf_info['not_after']}."
        elif ca_cert:
            try:
                leaf_cert.verify_directly_issued_by(ca_cert)
                validation["signature_valid"] = True
                validation["is_valid"] = True
                validation["status"] = "VALID"
                ca_name = ca_info.get("subject", {}).get("common_name") or ca_secret_name
                validation["message"] = f"Certificate signature is valid and verified against Project CA ({ca_name})."
            except cryptography.exceptions.InvalidSignature:
                validation["signature_valid"] = False
                validation["is_valid"] = False
                validation["status"] = "INVALID_SIGNATURE"
                validation["message"] = (
                    "Cryptographic signature verification failed: Certificate was not signed by the current Project CA. "
                    "The Project CA may have been rotated or reissued without re-issuing this certificate."
                )
            except ValueError as ve:
                validation["signature_valid"] = False
                validation["is_valid"] = False
                validation["status"] = "MISMATCH"
                validation["message"] = f"Certificate issuer does not match Project CA subject: {ve}"
            except Exception as ex:
                validation["signature_valid"] = False
                validation["is_valid"] = False
                validation["status"] = "ERROR"
                validation["message"] = f"Certificate verification failed: {ex}"

        return {
            "name": name,
            "namespace": cert_namespace,
            "secret_name": secret_name,
            "secret_found": True,
            "certificate": leaf_info,
            "ca": ca_info,
            "issuer_ref": issuer_ref,
            "conditions": conditions,
            "validation": validation,
        }

    return await asyncio.to_thread(_get_details)


class RenewCertificateRequest(BaseModel):
    name: str
    namespace: str | None = None


@ProjectService.model_view("POST", "/_renew_certificate")
async def renew_project_certificate(
    id: int,
    req: RenewCertificateRequest,
    svc: ProjectService = Depends(ProjectService.get_service),
):
    """Trigger renewal of a cert-manager certificate by removing its secret and certificate requests."""
    model = await svc.get(id)
    if not model.k8s_cluster_id:
        raise HTTPException(status_code=400, detail="Project has no cluster configured")

    cluster_svc = K8sClusterService(svc.request, svc.session)
    cluster = await cluster_svc.get(model.k8s_cluster_id)
    cert_namespace = req.namespace or model.k8s_namespace or model.name

    def _renew():
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
        core_api = client.CoreV1Api()

        try:
            cert_obj = custom_api.get_namespaced_custom_object(
                group="cert-manager.io",
                version="v1",
                namespace=cert_namespace,
                plural="certificates",
                name=req.name,
            )
        except Exception as e:
            logger.warning(f"Certificate {req.name} not found in {cert_namespace}: {e}")
            raise HTTPException(status_code=404, detail=f"Certificate '{req.name}' not found: {e}")

        spec = cert_obj.get("spec", {})
        secret_name = spec.get("secretName")

        reissue_certificate(
            k8s_client=None,
            namespace=cert_namespace,
            cert_name=req.name,
            secret_name=secret_name,
        )

        return {
            "status": "success",
            "message": f"Renewal initiated for certificate '{req.name}'. New certificate is being issued.",
        }

    return await asyncio.to_thread(_renew)









