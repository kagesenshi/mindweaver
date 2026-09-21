# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import base64
import datetime
import logging
import yaml
from cryptography import x509
from kubernetes import client

logger = logging.getLogger(__name__)


def reissue_certificate(
    k8s_client: client.ApiClient | None = None,
    namespace: str = "default",
    cert_name: str = "",
    secret_name: str | None = None,
    core_api: client.CoreV1Api | None = None,
    custom_api: client.CustomObjectsApi | None = None,
) -> None:
    """
    Deletes the certificate secret and any associated CertificateRequest resources
    to force cert-manager to re-issue the certificate with current CA credentials.
    """
    if core_api is None:
        core_api = client.CoreV1Api(k8s_client)
    if custom_api is None:
        custom_api = client.CustomObjectsApi(k8s_client)

    # 1. Delete associated secret
    if secret_name:
        try:
            core_api.delete_namespaced_secret(secret_name, namespace)
            logger.info(
                f"Deleted secret '{secret_name}' in namespace '{namespace}' for certificate '{cert_name}'"
            )
        except Exception as e:
            logger.info(
                f"Secret '{secret_name}' in namespace '{namespace}' not found or already deleted: {e}"
            )

    # 2. Delete pending or outdated CertificateRequests for this certificate
    try:
        cr_list = custom_api.list_namespaced_custom_object(
            group="cert-manager.io",
            version="v1",
            namespace=namespace,
            plural="certificaterequests",
        )
        for cr in cr_list.get("items", []):
            cr_name = cr["metadata"]["name"]
            owner_refs = cr.get("metadata", {}).get("ownerReferences", [])
            is_owner = any(
                ref.get("name") == cert_name and ref.get("kind") == "Certificate"
                for ref in owner_refs
            )
            cr_cert_name = (
                cr.get("metadata", {})
                .get("annotations", {})
                .get("cert-manager.io/certificate-name")
            )
            if is_owner or cr_cert_name == cert_name or cr_name.startswith(f"{cert_name}-"):
                try:
                    custom_api.delete_namespaced_custom_object(
                        group="cert-manager.io",
                        version="v1",
                        namespace=namespace,
                        plural="certificaterequests",
                        name=cr_name,
                    )
                    logger.info(
                        f"Deleted CertificateRequest '{cr_name}' in namespace '{namespace}'"
                    )
                except Exception as ex:
                    logger.warning(
                        f"Could not delete CertificateRequest '{cr_name}' in namespace '{namespace}': {ex}"
                    )
    except Exception as e:
        logger.warning(
            f"Failed to list or clean CertificateRequests for '{cert_name}' in namespace '{namespace}': {e}"
        )


def validate_and_reissue_certificate(
    k8s_client: client.ApiClient | None = None,
    namespace: str = "default",
    cert_name: str = "",
    secret_name: str = "",
    ca_secret_name: str = "",
    core_api: client.CoreV1Api | None = None,
    custom_api: client.CustomObjectsApi | None = None,
) -> bool:
    """
    Validates a leaf certificate against the active Project CA.
    If the leaf certificate is expired, corrupted, or not signed by the current CA,
    triggers reissuance by purging the outdated secret and CertificateRequests.

    Returns True if reissuance was triggered, False otherwise.
    """
    if core_api is None:
        core_api = client.CoreV1Api(k8s_client)

    # 1. Read leaf certificate secret
    try:
        leaf_secret = core_api.read_namespaced_secret(secret_name, namespace)
    except Exception:
        # Secret doesn't exist yet; cert-manager will generate it cleanly
        return False

    if not leaf_secret or not getattr(leaf_secret, "data", None):
        return False

    if not isinstance(leaf_secret.data, dict):
        return False

    tls_crt = leaf_secret.data.get("tls.crt")
    if not isinstance(tls_crt, (str, bytes)) or not tls_crt:
        return False

    now = datetime.datetime.now(datetime.timezone.utc)

    try:
        leaf_raw = base64.b64decode(tls_crt)
        leaf_cert = x509.load_pem_x509_certificate(leaf_raw)
    except Exception as ex:
        logger.warning(
            f"Failed to parse leaf certificate '{cert_name}' ({secret_name}) in namespace '{namespace}': {ex}. Reissuing."
        )
        reissue_certificate(
            k8s_client,
            namespace,
            cert_name,
            secret_name,
            core_api=core_api,
            custom_api=custom_api,
        )
        return True

    # Check leaf validity dates
    if now > leaf_cert.not_valid_after_utc or now < leaf_cert.not_valid_before_utc:
        logger.info(
            f"Certificate '{cert_name}' ({secret_name}) is expired or not yet valid. Triggering reissuance."
        )
        reissue_certificate(
            k8s_client,
            namespace,
            cert_name,
            secret_name,
            core_api=core_api,
            custom_api=custom_api,
        )
        return True

    # 2. Read CA secret
    try:
        ca_secret = core_api.read_namespaced_secret(ca_secret_name, namespace)
    except Exception:
        # CA secret not accessible or not created yet
        return False

    if not ca_secret or not getattr(ca_secret, "data", None):
        return False

    if not isinstance(ca_secret.data, dict):
        return False

    ca_b64 = ca_secret.data.get("ca.crt") or ca_secret.data.get("tls.crt")
    if not isinstance(ca_b64, (str, bytes)) or not ca_b64:
        return False

    try:
        ca_raw = base64.b64decode(ca_b64)
        ca_cert = x509.load_pem_x509_certificate(ca_raw)
    except Exception as ex:
        logger.warning(
            f"Failed to parse CA certificate from '{ca_secret_name}' in namespace '{namespace}': {ex}"
        )
        return False

    # Check AKI vs SKI match if both are present
    try:
        leaf_aki = leaf_cert.extensions.get_extension_for_class(
            x509.AuthorityKeyIdentifier
        ).value.key_identifier
        ca_ski = ca_cert.extensions.get_extension_for_class(
            x509.SubjectKeyIdentifier
        ).value.digest
        if leaf_aki and ca_ski and leaf_aki != ca_ski:
            logger.info(
                f"Certificate '{cert_name}' AKI does not match active Project CA SKI. Triggering reissuance."
            )
            reissue_certificate(
                k8s_client,
                namespace,
                cert_name,
                secret_name,
                core_api=core_api,
                custom_api=custom_api,
            )
            return True
    except x509.ExtensionNotFound:
        pass

    # Verify signature directly issued by CA
    try:
        leaf_cert.verify_directly_issued_by(ca_cert)
    except Exception as sig_ex:
        logger.info(
            f"Certificate '{cert_name}' signature verification failed against CA '{ca_secret_name}': {sig_ex}. "
            f"CA may have rotated. Triggering reissuance."
        )
        reissue_certificate(
            k8s_client,
            namespace,
            cert_name,
            secret_name,
            core_api=core_api,
            custom_api=custom_api,
        )
        return True

    return False


def reconcile_manifest_certificates(
    k8s_client: client.ApiClient | None = None,
    default_namespace: str = "default",
    manifest: str = "",
    core_api: client.CoreV1Api | None = None,
    custom_api: client.CustomObjectsApi | None = None,
) -> list[str]:
    """
    Parses manifest documents and validates any cert-manager Certificate resources
    against the active CA issuer, triggering automatic reissuance if needed.

    Returns a list of certificate names that were reissued.
    """
    reissued_certs: list[str] = []
    if core_api is None:
        core_api = client.CoreV1Api(k8s_client)
    if custom_api is None:
        custom_api = client.CustomObjectsApi(k8s_client)

    for doc in yaml.safe_load_all(manifest):
        if not doc or not isinstance(doc, dict):
            continue

        kind = doc.get("kind")
        api_version = doc.get("apiVersion", "")

        if kind != "Certificate" or not api_version.startswith("cert-manager.io/"):
            continue

        metadata = doc.get("metadata", {})
        spec = doc.get("spec", {})

        cert_name = metadata.get("name")
        cert_namespace = metadata.get("namespace") or default_namespace
        secret_name = spec.get("secretName")
        issuer_ref = spec.get("issuerRef", {})
        issuer_name = issuer_ref.get("name")

        if not cert_name or not secret_name or not issuer_name:
            continue

        # Resolve CA secret name for this issuer
        ca_secret_name = None
        try:
            issuer_obj = custom_api.get_namespaced_custom_object(
                group="cert-manager.io",
                version="v1",
                namespace=cert_namespace,
                plural="issuers",
                name=issuer_name,
            )
            ca_secret_name = issuer_obj.get("spec", {}).get("ca", {}).get("secretName")
        except Exception:
            # Fallback heuristic: project self-signed issuer uses `<project>-ca-secret`
            if issuer_name.endswith("-selfsigned-issuer"):
                prefix = issuer_name.rsplit("-selfsigned-issuer", 1)[0]
                ca_secret_name = f"{prefix}-ca-secret"

        if not ca_secret_name:
            continue

        was_reissued = validate_and_reissue_certificate(
            k8s_client,
            namespace=cert_namespace,
            cert_name=cert_name,
            secret_name=secret_name,
            ca_secret_name=ca_secret_name,
            core_api=core_api,
            custom_api=custom_api,
        )
        if was_reissued:
            reissued_certs.append(cert_name)

    return reissued_certs
