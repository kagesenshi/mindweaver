# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import base64
import datetime
from unittest.mock import patch, MagicMock
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from fastapi.testclient import TestClient


def generate_ca(common_name: str = "Test Project CA", days: int = 365, expired: bool = False):
    """Generate a CA private key and certificate."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
    now = datetime.datetime.now(datetime.timezone.utc)
    if expired:
        not_before = now - datetime.timedelta(days=days + 10)
        not_after = now - datetime.timedelta(days=1)
    else:
        not_before = now - datetime.timedelta(days=1)
        not_after = now + datetime.timedelta(days=days)

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


def generate_cert(
    common_name: str,
    ca_key: rsa.RSAPrivateKey,
    ca_cert: x509.Certificate,
    dns_names: list[str] | None = None,
    days: int = 90,
    expired: bool = False,
):
    """Generate a leaf certificate signed by the given CA."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
    now = datetime.datetime.now(datetime.timezone.utc)
    if expired:
        not_before = now - datetime.timedelta(days=days + 10)
        not_after = now - datetime.timedelta(days=1)
    else:
        not_before = now - datetime.timedelta(days=1)
        not_after = now + datetime.timedelta(days=days)

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
    if dns_names:
        san = [x509.DNSName(name) for name in dns_names]
        builder = builder.add_extension(x509.SubjectAlternativeName(san), critical=False)

    cert = builder.sign(ca_key, hashes.SHA256())
    return key, cert


@pytest.fixture
def cert_env():
    """Create test certificates and CAs for testing."""
    ca_key, ca_cert = generate_ca("project-cert-test-ca")
    other_ca_key, other_ca_cert = generate_ca("other-ca")
    expired_ca_key, expired_ca_cert = generate_ca("expired-ca", expired=True)

    _, valid_cert = generate_cert(
        "service.project-cert-test.example.com",
        ca_key,
        ca_cert,
        dns_names=["service.project-cert-test.example.com", "*.project-cert-test.example.com"],
    )
    _, foreign_cert = generate_cert(
        "service.project-cert-test.example.com",
        other_ca_key,
        other_ca_cert,
        dns_names=["service.project-cert-test.example.com"],
    )
    _, expired_cert = generate_cert(
        "expired.project-cert-test.example.com",
        ca_key,
        ca_cert,
        expired=True,
    )

    return {
        "ca_key": ca_key,
        "ca_cert": ca_cert,
        "other_ca_key": other_ca_key,
        "other_ca_cert": other_ca_cert,
        "expired_ca_key": expired_ca_key,
        "expired_ca_cert": expired_ca_cert,
        "valid_cert": valid_cert,
        "foreign_cert": foreign_cert,
        "expired_cert": expired_cert,
    }


def test_get_certificate_details_valid(client: TestClient, test_cluster: dict, cert_env: dict):
    """Test retrieving details and validating a genuine certificate signed by the project CA."""
    from cryptography.hazmat.primitives import serialization

    project = client.post(
        "/api/v1/projects",
        json={
            "name": "project-cert-test",
            "title": "Project Cert Test",
            "k8s_cluster_id": test_cluster["id"],
        },
    ).json()["data"]

    namespace = project["name"]
    ca_pem = cert_env["ca_cert"].public_bytes(serialization.Encoding.PEM).decode("utf-8")
    cert_pem = cert_env["valid_cert"].public_bytes(serialization.Encoding.PEM).decode("utf-8")

    with patch("kubernetes.config.load_incluster_config"), patch(
        "kubernetes.config.load_kube_config"
    ), patch("kubernetes.client.CustomObjectsApi") as mock_custom, patch(
        "kubernetes.client.CoreV1Api"
    ) as mock_core:

        def _mock_get_namespaced_custom_object(group, version, namespace, plural, name, **kwargs):
            if plural == "certificates" and name == "test-service-cert":
                return {
                    "metadata": {"name": name, "namespace": namespace},
                    "spec": {
                        "issuerRef": {"name": f"{namespace}-selfsigned-issuer", "kind": "Issuer"},
                        "secretName": "test-service-cert-secret",
                        "dnsNames": ["service.project-cert-test.example.com", "*.project-cert-test.example.com"],
                    },
                    "status": {
                        "conditions": [{"type": "Ready", "status": "True", "message": "Certificate is up to date"}],
                        "notBefore": "2026-01-01T00:00:00Z",
                        "notAfter": "2026-12-31T23:59:59Z",
                    },
                }
            if plural == "issuers" and name == f"{namespace}-selfsigned-issuer":
                return {
                    "metadata": {"name": name, "namespace": namespace},
                    "spec": {"ca": {"secretName": f"{namespace}-ca-secret"}},
                }
            raise Exception("NotFound")

        def _mock_read_namespaced_secret(name, ns):
            secret = MagicMock()
            if name == "test-service-cert-secret":
                secret.data = {
                    "tls.crt": base64.b64encode(cert_pem.encode("utf-8")).decode("utf-8"),
                }
                return secret
            if name == f"{namespace}-ca-secret":
                secret.data = {
                    "ca.crt": base64.b64encode(ca_pem.encode("utf-8")).decode("utf-8"),
                }
                return secret
            raise Exception("SecretNotFound")

        mock_custom.return_value.get_namespaced_custom_object.side_effect = _mock_get_namespaced_custom_object
        mock_core.return_value.read_namespaced_secret.side_effect = _mock_read_namespaced_secret

        resp = client.get(
            f"/api/v1/projects/{project['id']}/_certificate_details",
            params={"name": "test-service-cert", "namespace": namespace},
        )
        assert resp.status_code == 200
        data = resp.json()

        # Certificate fields
        assert data["certificate"]["subject"]["common_name"] == "service.project-cert-test.example.com"
        assert "service.project-cert-test.example.com" in data["certificate"]["dns_names"]
        assert data["certificate"]["is_expired"] is False
        assert data["certificate"]["authority_key_identifier"] is not None

        # CA fields
        assert data["ca"]["exists"] is True
        assert data["ca"]["is_valid"] is True
        assert data["ca"]["is_expired"] is False
        assert data["ca"]["subject"]["common_name"] == "project-cert-test-ca"

        # Validation status
        assert data["validation"]["is_valid"] is True
        assert data["validation"]["signature_valid"] is True
        assert data["validation"]["status"] == "VALID"
        assert "verified" in data["validation"]["message"].lower()


def test_get_certificate_details_mismatched_signature(client: TestClient, test_cluster: dict, cert_env: dict):
    """Test retrieving details when certificate was signed by another CA."""
    from cryptography.hazmat.primitives import serialization

    project = client.post(
        "/api/v1/projects",
        json={
            "name": "project-cert-mismatch",
            "title": "Project Cert Mismatch",
            "k8s_cluster_id": test_cluster["id"],
        },
    ).json()["data"]

    namespace = project["name"]
    ca_pem = cert_env["ca_cert"].public_bytes(serialization.Encoding.PEM).decode("utf-8")
    foreign_cert_pem = cert_env["foreign_cert"].public_bytes(serialization.Encoding.PEM).decode("utf-8")

    with patch("kubernetes.config.load_incluster_config"), patch(
        "kubernetes.config.load_kube_config"
    ), patch("kubernetes.client.CustomObjectsApi") as mock_custom, patch(
        "kubernetes.client.CoreV1Api"
    ) as mock_core:

        def _mock_get_namespaced_custom_object(group, version, namespace, plural, name, **kwargs):
            if plural == "certificates":
                return {
                    "metadata": {"name": name, "namespace": namespace},
                    "spec": {
                        "issuerRef": {"name": f"{namespace}-selfsigned-issuer", "kind": "Issuer"},
                        "secretName": "test-service-cert-secret",
                    },
                    "status": {"conditions": []},
                }
            if plural == "issuers":
                return {
                    "metadata": {"name": name, "namespace": namespace},
                    "spec": {"ca": {"secretName": f"{namespace}-ca-secret"}},
                }
            raise Exception("NotFound")

        def _mock_read_namespaced_secret(name, ns):
            secret = MagicMock()
            if name == "test-service-cert-secret":
                secret.data = {
                    "tls.crt": base64.b64encode(foreign_cert_pem.encode("utf-8")).decode("utf-8"),
                }
                return secret
            if name == f"{namespace}-ca-secret":
                secret.data = {
                    "ca.crt": base64.b64encode(ca_pem.encode("utf-8")).decode("utf-8"),
                }
                return secret
            raise Exception("SecretNotFound")

        mock_custom.return_value.get_namespaced_custom_object.side_effect = _mock_get_namespaced_custom_object
        mock_core.return_value.read_namespaced_secret.side_effect = _mock_read_namespaced_secret

        resp = client.get(
            f"/api/v1/projects/{project['id']}/_certificate_details",
            params={"name": "test-service-cert", "namespace": namespace},
        )
        assert resp.status_code == 200
        data = resp.json()

        assert data["validation"]["is_valid"] is False
        assert data["validation"]["signature_valid"] is False
        assert data["validation"]["status"] in ("INVALID_SIGNATURE", "MISMATCH")


def test_get_certificate_details_expired_cert(client: TestClient, test_cluster: dict, cert_env: dict):
    """Test retrieving details when the leaf certificate is expired."""
    from cryptography.hazmat.primitives import serialization

    project = client.post(
        "/api/v1/projects",
        json={
            "name": "project-cert-exp",
            "title": "Project Cert Exp",
            "k8s_cluster_id": test_cluster["id"],
        },
    ).json()["data"]

    namespace = project["name"]
    ca_pem = cert_env["ca_cert"].public_bytes(serialization.Encoding.PEM).decode("utf-8")
    expired_cert_pem = cert_env["expired_cert"].public_bytes(serialization.Encoding.PEM).decode("utf-8")

    with patch("kubernetes.config.load_incluster_config"), patch(
        "kubernetes.config.load_kube_config"
    ), patch("kubernetes.client.CustomObjectsApi") as mock_custom, patch(
        "kubernetes.client.CoreV1Api"
    ) as mock_core:

        def _mock_get_namespaced_custom_object(group, version, namespace, plural, name, **kwargs):
            if plural == "certificates":
                return {
                    "metadata": {"name": name, "namespace": namespace},
                    "spec": {
                        "issuerRef": {"name": f"{namespace}-selfsigned-issuer", "kind": "Issuer"},
                        "secretName": "test-service-cert-secret",
                    },
                    "status": {"conditions": []},
                }
            if plural == "issuers":
                return {
                    "metadata": {"name": name, "namespace": namespace},
                    "spec": {"ca": {"secretName": f"{namespace}-ca-secret"}},
                }
            raise Exception("NotFound")

        def _mock_read_namespaced_secret(name, ns):
            secret = MagicMock()
            if name == "test-service-cert-secret":
                secret.data = {
                    "tls.crt": base64.b64encode(expired_cert_pem.encode("utf-8")).decode("utf-8"),
                }
                return secret
            if name == f"{namespace}-ca-secret":
                secret.data = {
                    "ca.crt": base64.b64encode(ca_pem.encode("utf-8")).decode("utf-8"),
                }
                return secret
            raise Exception("SecretNotFound")

        mock_custom.return_value.get_namespaced_custom_object.side_effect = _mock_get_namespaced_custom_object
        mock_core.return_value.read_namespaced_secret.side_effect = _mock_read_namespaced_secret

        resp = client.get(
            f"/api/v1/projects/{project['id']}/_certificate_details",
            params={"name": "test-service-cert", "namespace": namespace},
        )
        assert resp.status_code == 200
        data = resp.json()

        assert data["certificate"]["is_expired"] is True
        assert data["validation"]["is_valid"] is False
        assert data["validation"]["status"] == "EXPIRED"


def test_get_certificate_details_expired_ca(client: TestClient, test_cluster: dict, cert_env: dict):
    """Test retrieving details when the Project CA itself is expired."""
    from cryptography.hazmat.primitives import serialization

    project = client.post(
        "/api/v1/projects",
        json={
            "name": "project-ca-exp",
            "title": "Project CA Exp",
            "k8s_cluster_id": test_cluster["id"],
        },
    ).json()["data"]

    namespace = project["name"]
    expired_ca_pem = cert_env["expired_ca_cert"].public_bytes(serialization.Encoding.PEM).decode("utf-8")
    cert_pem = cert_env["valid_cert"].public_bytes(serialization.Encoding.PEM).decode("utf-8")

    with patch("kubernetes.config.load_incluster_config"), patch(
        "kubernetes.config.load_kube_config"
    ), patch("kubernetes.client.CustomObjectsApi") as mock_custom, patch(
        "kubernetes.client.CoreV1Api"
    ) as mock_core:

        def _mock_get_namespaced_custom_object(group, version, namespace, plural, name, **kwargs):
            if plural == "certificates":
                return {
                    "metadata": {"name": name, "namespace": namespace},
                    "spec": {
                        "issuerRef": {"name": f"{namespace}-selfsigned-issuer", "kind": "Issuer"},
                        "secretName": "test-service-cert-secret",
                    },
                    "status": {"conditions": []},
                }
            if plural == "issuers":
                return {
                    "metadata": {"name": name, "namespace": namespace},
                    "spec": {"ca": {"secretName": f"{namespace}-ca-secret"}},
                }
            raise Exception("NotFound")

        def _mock_read_namespaced_secret(name, ns):
            secret = MagicMock()
            if name == "test-service-cert-secret":
                secret.data = {
                    "tls.crt": base64.b64encode(cert_pem.encode("utf-8")).decode("utf-8"),
                }
                return secret
            if name == f"{namespace}-ca-secret":
                secret.data = {
                    "ca.crt": base64.b64encode(expired_ca_pem.encode("utf-8")).decode("utf-8"),
                }
                return secret
            raise Exception("SecretNotFound")

        mock_custom.return_value.get_namespaced_custom_object.side_effect = _mock_get_namespaced_custom_object
        mock_core.return_value.read_namespaced_secret.side_effect = _mock_read_namespaced_secret

        resp = client.get(
            f"/api/v1/projects/{project['id']}/_certificate_details",
            params={"name": "test-service-cert", "namespace": namespace},
        )
        assert resp.status_code == 200
        data = resp.json()

        assert data["ca"]["is_expired"] is True
        assert data["ca"]["is_valid"] is False
        assert data["validation"]["is_valid"] is False
        assert data["validation"]["status"] == "CA_INVALID"


def test_get_certificate_details_missing_secret(client: TestClient, test_cluster: dict):
    """Test when cert-manager Certificate exists but secret has not yet been populated."""
    project = client.post(
        "/api/v1/projects",
        json={
            "name": "project-cert-notready",
            "title": "Project Cert Not Ready",
            "k8s_cluster_id": test_cluster["id"],
        },
    ).json()["data"]

    namespace = project["name"]

    with patch("kubernetes.config.load_incluster_config"), patch(
        "kubernetes.config.load_kube_config"
    ), patch("kubernetes.client.CustomObjectsApi") as mock_custom, patch(
        "kubernetes.client.CoreV1Api"
    ) as mock_core:

        def _mock_get_namespaced_custom_object(group, version, namespace, plural, name, **kwargs):
            if plural == "certificates":
                return {
                    "metadata": {"name": name, "namespace": namespace},
                    "spec": {
                        "issuerRef": {"name": f"{namespace}-selfsigned-issuer", "kind": "Issuer"},
                        "secretName": "pending-secret",
                    },
                    "status": {"conditions": [{"type": "Issuing", "status": "True", "message": "Waiting on order"}]},
                }
            raise Exception("NotFound")

        mock_custom.return_value.get_namespaced_custom_object.side_effect = _mock_get_namespaced_custom_object
        mock_core.return_value.read_namespaced_secret.side_effect = Exception("SecretNotFound")

        resp = client.get(
            f"/api/v1/projects/{project['id']}/_certificate_details",
            params={"name": "pending-cert", "namespace": namespace},
        )
        assert resp.status_code == 200
        data = resp.json()

        assert data["secret_found"] is False
        assert data["certificate"] is None
        assert data["validation"]["status"] == "NOT_ISSUED"


def test_get_certificate_details_cluster_no_kubeconfig(client: TestClient):
    """Test calling endpoint when cluster has no kubeconfig."""
    cluster = client.post(
        "/api/v1/k8s_clusters",
        json={
            "name": "cluster-no-kc",
            "title": "Cluster No KC",
            "type": "remote",
            "kubeconfig": "",
        },
    ).json()["data"]
    project = client.post(
        "/api/v1/projects",
        json={
            "name": "project-no-kc",
            "title": "Project No KC",
            "k8s_cluster_id": cluster["id"],
        },
    ).json()["data"]

    resp = client.get(
        f"/api/v1/projects/{project['id']}/_certificate_details",
        params={"name": "some-cert", "namespace": "project-no-kc"},
    )
    assert resp.status_code == 400
    assert "has no kubeconfig" in resp.json()["detail"]


def test_get_certificate_details_not_found(client: TestClient, test_cluster: dict):
    """Test calling endpoint when certificate does not exist."""
    project = client.post(
        "/api/v1/projects",
        json={
            "name": "project-cert-404",
            "title": "Project Cert 404",
            "k8s_cluster_id": test_cluster["id"],
        },
    ).json()["data"]

    with patch("kubernetes.config.load_incluster_config"), patch(
        "kubernetes.config.load_kube_config"
    ), patch("kubernetes.client.CustomObjectsApi") as mock_custom, patch(
        "kubernetes.client.CoreV1Api"
    ):
        mock_custom.return_value.get_namespaced_custom_object.side_effect = Exception("NotFound")

        resp = client.get(
            f"/api/v1/projects/{project['id']}/_certificate_details",
            params={"name": "non-existent-cert", "namespace": project["name"]},
        )
        assert resp.status_code == 404


def test_renew_certificate_success(client: TestClient, test_cluster: dict):
    """Test renewing a certificate by deleting secret and certificate requests."""
    project = client.post(
        "/api/v1/projects",
        json={
            "name": "project-renew-test",
            "title": "Project Renew Test",
            "k8s_cluster_id": test_cluster["id"],
        },
    ).json()["data"]

    namespace = project["name"]

    with patch("kubernetes.config.load_incluster_config"), patch(
        "kubernetes.config.load_kube_config"
    ), patch("kubernetes.client.CustomObjectsApi") as mock_custom, patch(
        "kubernetes.client.CoreV1Api"
    ) as mock_core:

        def _mock_get_namespaced_custom_object(group, version, namespace, plural, name, **kwargs):
            if plural == "certificates" and name == "test-cert":
                return {
                    "metadata": {"name": name, "namespace": namespace},
                    "spec": {
                        "secretName": "test-cert-secret",
                        "issuerRef": {"name": f"{namespace}-selfsigned-issuer", "kind": "Issuer"},
                    },
                }
            raise Exception("NotFound")

        def _mock_list_namespaced_custom_object(group, version, namespace, plural, **kwargs):
            if plural == "certificaterequests":
                return {
                    "items": [
                        {
                            "metadata": {
                                "name": "test-cert-1",
                                "annotations": {"cert-manager.io/certificate-name": "test-cert"},
                            }
                        }
                    ]
                }
            return {"items": []}

        mock_custom.return_value.get_namespaced_custom_object.side_effect = _mock_get_namespaced_custom_object
        mock_custom.return_value.list_namespaced_custom_object.side_effect = _mock_list_namespaced_custom_object

        resp = client.post(
            f"/api/v1/projects/{project['id']}/_renew_certificate",
            json={"name": "test-cert", "namespace": namespace},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "renew" in data["message"].lower()

        # Check that secret deletion was called
        mock_core.return_value.delete_namespaced_secret.assert_called_once_with(
            "test-cert-secret", namespace
        )
        # Check that certificate request deletion was called
        mock_custom.return_value.delete_namespaced_custom_object.assert_called_once_with(
            group="cert-manager.io",
            version="v1",
            namespace=namespace,
            plural="certificaterequests",
            name="test-cert-1",
        )


def test_renew_certificate_not_found(client: TestClient, test_cluster: dict):
    """Test renewing a non-existent certificate."""
    project = client.post(
        "/api/v1/projects",
        json={
            "name": "project-renew-404",
            "title": "Project Renew 404",
            "k8s_cluster_id": test_cluster["id"],
        },
    ).json()["data"]

    with patch("kubernetes.config.load_incluster_config"), patch(
        "kubernetes.config.load_kube_config"
    ), patch("kubernetes.client.CustomObjectsApi") as mock_custom, patch(
        "kubernetes.client.CoreV1Api"
    ):
        mock_custom.return_value.get_namespaced_custom_object.side_effect = Exception("NotFound")

        resp = client.post(
            f"/api/v1/projects/{project['id']}/_renew_certificate",
            json={"name": "non-existent-cert", "namespace": project["name"]},
        )
        assert resp.status_code == 404


