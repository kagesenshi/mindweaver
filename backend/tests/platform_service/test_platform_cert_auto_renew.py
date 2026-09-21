# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import base64
import datetime
from unittest.mock import MagicMock, patch
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.x509.oid import NameOID

from mindweaver.fw.cert_manager import (
    validate_and_reissue_certificate,
    reconcile_manifest_certificates,
    reissue_certificate,
)


def generate_test_ca(common_name: str = "Test CA", expired: bool = False):
    """Generate a test CA key and certificate."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
    now = datetime.datetime.now(datetime.timezone.utc)
    if expired:
        not_before = now - datetime.timedelta(days=30)
        not_after = now - datetime.timedelta(days=1)
    else:
        not_before = now - datetime.timedelta(days=1)
        not_after = now + datetime.timedelta(days=365)

    builder = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(not_before)
        .not_valid_after(not_after)
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), critical=False)
    )
    cert = builder.sign(key, hashes.SHA256())
    return key, cert


def generate_test_cert(
    common_name: str,
    ca_key: rsa.RSAPrivateKey,
    ca_cert: x509.Certificate,
    expired: bool = False,
):
    """Generate a test certificate signed by the given CA."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
    now = datetime.datetime.now(datetime.timezone.utc)
    if expired:
        not_before = now - datetime.timedelta(days=30)
        not_after = now - datetime.timedelta(days=1)
    else:
        not_before = now - datetime.timedelta(days=1)
        not_after = now + datetime.timedelta(days=90)

    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(ca_cert.subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(not_before)
        .not_valid_after(not_after)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), critical=False)
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()),
            critical=False,
        )
    )
    cert = builder.sign(ca_key, hashes.SHA256())
    return key, cert


def test_reissue_certificate():
    """Test that reissue_certificate deletes the secret and certificate requests."""
    k8s_client = MagicMock()
    core_api = MagicMock()
    custom_api = MagicMock()

    with patch("kubernetes.client.CoreV1Api", return_value=core_api), \
         patch("kubernetes.client.CustomObjectsApi", return_value=custom_api):
        
        custom_api.list_namespaced_custom_object.return_value = {
            "items": [
                {
                    "metadata": {
                        "name": "trino-tls-req1",
                        "ownerReferences": [{"name": "trino-tls", "kind": "Certificate"}],
                    }
                },
                {
                    "metadata": {
                        "name": "other-cert-req",
                        "ownerReferences": [{"name": "other-cert", "kind": "Certificate"}],
                    }
                },
            ]
        }

        reissue_certificate(k8s_client, "test-ns", "trino-tls", "trino-tls-secret")

        core_api.delete_namespaced_secret.assert_called_once_with("trino-tls-secret", "test-ns")
        custom_api.delete_namespaced_custom_object.assert_called_once_with(
            group="cert-manager.io",
            version="v1",
            namespace="test-ns",
            plural="certificaterequests",
            name="trino-tls-req1",
        )


def test_validate_and_reissue_valid_cert():
    """Test that a valid certificate signed by the active CA is not reissued."""
    k8s_client = MagicMock()
    core_api = MagicMock()

    ca_key, ca_cert = generate_test_ca("Test CA")
    _, leaf_cert = generate_test_cert("trino.test-ns.svc.cluster.local", ca_key, ca_cert)

    ca_pem = ca_cert.public_bytes(serialization.Encoding.PEM)
    leaf_pem = leaf_cert.public_bytes(serialization.Encoding.PEM)

    ca_secret = MagicMock()
    ca_secret.data = {"tls.crt": base64.b64encode(ca_pem).decode("utf-8")}

    leaf_secret = MagicMock()
    leaf_secret.data = {"tls.crt": base64.b64encode(leaf_pem).decode("utf-8")}

    def mock_read_secret(name, ns):
        if name == "test-ca-secret":
            return ca_secret
        if name == "trino-tls-secret":
            return leaf_secret
        return None

    core_api.read_namespaced_secret.side_effect = mock_read_secret

    with patch("kubernetes.client.CoreV1Api", return_value=core_api), \
         patch("mindweaver.fw.cert_manager.reissue_certificate") as mock_reissue:
        
        reissued = validate_and_reissue_certificate(
            k8s_client, "test-ns", "trino-tls", "trino-tls-secret", "test-ca-secret"
        )

        assert reissued is False
        mock_reissue.assert_not_called()


def test_validate_and_reissue_rotated_ca():
    """Test that a leaf certificate signed by an old/rotated CA triggers reissuance."""
    k8s_client = MagicMock()
    core_api = MagicMock()

    old_ca_key, old_ca_cert = generate_test_ca("Old CA")
    new_ca_key, new_ca_cert = generate_test_ca("New CA")

    # Leaf signed by OLD CA
    _, leaf_cert = generate_test_cert("trino.test-ns.svc.cluster.local", old_ca_key, old_ca_cert)

    # Active cluster secret has NEW CA
    new_ca_pem = new_ca_cert.public_bytes(serialization.Encoding.PEM)
    leaf_pem = leaf_cert.public_bytes(serialization.Encoding.PEM)

    ca_secret = MagicMock()
    ca_secret.data = {"tls.crt": base64.b64encode(new_ca_pem).decode("utf-8")}

    leaf_secret = MagicMock()
    leaf_secret.data = {"tls.crt": base64.b64encode(leaf_pem).decode("utf-8")}

    def mock_read_secret(name, ns):
        if name == "test-ca-secret":
            return ca_secret
        if name == "trino-tls-secret":
            return leaf_secret
        return None

    core_api.read_namespaced_secret.side_effect = mock_read_secret

    with patch("kubernetes.client.CoreV1Api", return_value=core_api), \
         patch("mindweaver.fw.cert_manager.reissue_certificate") as mock_reissue:
        
        reissued = validate_and_reissue_certificate(
            k8s_client, "test-ns", "trino-tls", "trino-tls-secret", "test-ca-secret"
        )

        assert reissued is True
        assert mock_reissue.called
        call_args = mock_reissue.call_args
        assert call_args[0][:4] == (k8s_client, "test-ns", "trino-tls", "trino-tls-secret")


def test_validate_and_reissue_expired_cert():
    """Test that an expired leaf certificate triggers reissuance."""
    k8s_client = MagicMock()
    core_api = MagicMock()

    ca_key, ca_cert = generate_test_ca("Test CA")
    _, leaf_cert = generate_test_cert("trino.test-ns.svc.cluster.local", ca_key, ca_cert, expired=True)

    ca_pem = ca_cert.public_bytes(serialization.Encoding.PEM)
    leaf_pem = leaf_cert.public_bytes(serialization.Encoding.PEM)

    ca_secret = MagicMock()
    ca_secret.data = {"tls.crt": base64.b64encode(ca_pem).decode("utf-8")}

    leaf_secret = MagicMock()
    leaf_secret.data = {"tls.crt": base64.b64encode(leaf_pem).decode("utf-8")}

    def mock_read_secret(name, ns):
        if name == "test-ca-secret":
            return ca_secret
        if name == "trino-tls-secret":
            return leaf_secret
        return None

    core_api.read_namespaced_secret.side_effect = mock_read_secret

    with patch("kubernetes.client.CoreV1Api", return_value=core_api), \
         patch("mindweaver.fw.cert_manager.reissue_certificate") as mock_reissue:
        
        reissued = validate_and_reissue_certificate(
            k8s_client, "test-ns", "trino-tls", "trino-tls-secret", "test-ca-secret"
        )

        assert reissued is True
        assert mock_reissue.called
        call_args = mock_reissue.call_args
        assert call_args[0][:4] == (k8s_client, "test-ns", "trino-tls", "trino-tls-secret")


def test_reconcile_manifest_certificates():
    """Test reconcile_manifest_certificates scans YAML documents and validates Certificate resources."""
    manifest = """
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: trino-tls
  namespace: my-project
spec:
  secretName: trino-tls-secret
  issuerRef:
    name: my-project-selfsigned-issuer
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: trino-coordinator
"""
    k8s_client = MagicMock()
    custom_api = MagicMock()

    custom_api.get_namespaced_custom_object.return_value = {
        "spec": {
            "ca": {
                "secretName": "my-project-ca-secret"
            }
        }
    }

    with patch("kubernetes.client.CustomObjectsApi", return_value=custom_api), \
         patch("mindweaver.fw.cert_manager.validate_and_reissue_certificate") as mock_validate:
        
        mock_validate.return_value = True

        reconcile_manifest_certificates(k8s_client, "my-project", manifest)

        assert mock_validate.called
        call_kwargs = mock_validate.call_args[1]
        assert call_kwargs["namespace"] == "my-project"
        assert call_kwargs["cert_name"] == "trino-tls"
        assert call_kwargs["secret_name"] == "trino-tls-secret"
        assert call_kwargs["ca_secret_name"] == "my-project-ca-secret"
