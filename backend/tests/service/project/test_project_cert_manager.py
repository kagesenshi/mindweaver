# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import base64
import datetime
from unittest.mock import MagicMock, patch, AsyncMock
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from fastapi.testclient import TestClient
import pytest


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
def mock_cert_manager_k8s():
    ca_key, ca_cert = generate_ca("Test Project CA")
    ca_pem = ca_cert.public_bytes(serialization.Encoding.PEM).decode("utf-8")

    _, leaf_cert = generate_cert("test-cert", ca_key, ca_cert, ["example.com"])
    leaf_pem = leaf_cert.public_bytes(serialization.Encoding.PEM).decode("utf-8")

    with patch(
        "kubernetes.config.load_incluster_config"
    ), patch(
        "kubernetes.config.load_kube_config"
    ), patch(
        "kubernetes.client.CustomObjectsApi"
    ) as mock_custom, patch(
        "kubernetes.client.CoreV1Api"
    ) as mock_core:

        # Mock list_namespaced_custom_object return value for issuers/certificates
        def _mock_list_namespaced_custom_object(group, version, namespace, plural):
            if plural == "issuers":
                return {
                    "items": [
                        {
                            "metadata": {"name": f"{namespace}-bootstrap-issuer", "namespace": namespace},
                            "status": {
                                "conditions": [{"type": "Ready", "status": "True"}]
                            },
                        },
                        {
                            "metadata": {"name": f"{namespace}-selfsigned-issuer", "namespace": namespace},
                            "spec": {
                                "ca": {"secretName": "test-ca-secret"}
                            },
                            "status": {
                                "conditions": [{"type": "Ready", "status": "True"}]
                            },
                        },
                        {
                            "metadata": {"name": "some-other-issuer", "namespace": namespace},
                            "status": {
                                "conditions": [{"type": "Ready", "status": "True"}]
                            },
                        }
                    ]
                }
            elif plural == "certificates":
                return {
                    "items": [
                        {
                            "metadata": {"name": "test-cert", "namespace": namespace},
                            "spec": {
                                "issuerRef": {"name": f"{namespace}-selfsigned-issuer", "kind": "Issuer"},
                                "dnsNames": ["example.com"],
                                "secretName": "test-cert-secret",
                            },
                            "status": {
                                "notAfter": "2026-12-31T23:59:59Z",
                                "notBefore": "2026-01-01T00:00:00Z",
                                "conditions": [{"type": "Ready", "status": "True"}],
                            },
                        }
                    ]
                }
            return {"items": []}

        # Mock get_namespaced_custom_object
        def _mock_get_namespaced_custom_object(group, version, namespace, plural, name):
            if name.endswith("selfsigned-issuer"):
                return {
                    "metadata": {"name": name, "namespace": namespace},
                    "spec": {
                        "ca": {"secretName": "test-ca-secret"}
                    }
                }
            elif name == "test-non-ca-issuer":
                return {
                    "metadata": {"name": "test-non-ca-issuer", "namespace": namespace},
                    "spec": {
                        "selfSigned": {}
                    }
                }
            raise Exception("NotFound")

        mock_custom.return_value.list_namespaced_custom_object.side_effect = _mock_list_namespaced_custom_object
        mock_custom.return_value.get_namespaced_custom_object.side_effect = _mock_get_namespaced_custom_object

        # Mock secrets
        ca_secret = MagicMock()
        ca_secret.metadata.name = "test-ca-secret"
        ca_secret.data = {
            "ca.crt": base64.b64encode(ca_pem.encode("utf-8")).decode("utf-8"),
            "tls.crt": base64.b64encode(ca_pem.encode("utf-8")).decode("utf-8"),
        }

        cert_secret = MagicMock()
        cert_secret.metadata.name = "test-cert-secret"
        cert_secret.data = {
            "tls.crt": base64.b64encode(leaf_pem.encode("utf-8")).decode("utf-8"),
        }

        # Mock read_namespaced_secret
        def _mock_read_namespaced_secret(name, namespace):
            if name == "test-ca-secret":
                return ca_secret
            elif name == "test-cert-secret":
                return cert_secret
            raise Exception("SecretNotFound")

        mock_core.return_value.read_namespaced_secret.side_effect = _mock_read_namespaced_secret

        def _mock_list_namespaced_secret(namespace):
            res = MagicMock()
            res.items = [ca_secret, cert_secret]
            return res

        mock_core.return_value.list_namespaced_secret.side_effect = _mock_list_namespaced_secret

        yield {
            "custom": mock_custom,
            "core": mock_core,
            "ca_key": ca_key,
            "ca_cert": ca_cert,
            "ca_pem": ca_pem,
            "leaf_cert": leaf_cert,
            "leaf_pem": leaf_pem,
        }


def test_get_cert_manager_resources(client: TestClient, test_cluster: dict, mock_cert_manager_k8s):
    """Test retrieving cert manager resources when certificate is valid."""
    # Create project
    project = client.post(
        "/api/v1/projects",
        json={
            "name": "project-cm-test",
            "title": "Project CM Test",
            "k8s_cluster_id": test_cluster["id"],
        },
    ).json()["data"]

    # Call the endpoint
    resp = client.get(f"/api/v1/projects/{project['id']}/_cert_manager")
    assert resp.status_code == 200
    data = resp.json()

    assert "issuers" in data
    assert "certificates" in data

    issuers = data["issuers"]
    # Should only contain namespaced bootstrap and selfsigned issuers
    assert len(issuers) == 2
    
    issuer_names = [i["name"] for i in issuers]
    assert "project-cm-test-bootstrap-issuer" in issuer_names
    assert "project-cm-test-selfsigned-issuer" in issuer_names
    assert "some-other-issuer" not in issuer_names

    # Check kind mapping
    for i in issuers:
        assert i["kind"] == "Issuer"

    certs = data["certificates"]
    assert len(certs) == 1
    assert certs[0]["name"] == "test-cert"
    assert certs[0]["issuer_name"] == "project-cm-test-selfsigned-issuer"
    assert certs[0]["issuer_kind"] == "Issuer"
    assert certs[0]["status"] == "Ready"
    assert certs[0]["dns_names"] == ["example.com"]
    assert certs[0]["secret_name"] == "test-cert-secret"
    assert certs[0]["not_after"] == "2026-12-31T23:59:59Z"


def test_get_cert_manager_resources_expired_cert(client: TestClient, test_cluster: dict, mock_cert_manager_k8s):
    """Test that an expired certificate shows 'Expired' status instead of 'Ready'."""
    project = client.post(
        "/api/v1/projects",
        json={
            "name": "project-cm-expired",
            "title": "Project CM Expired",
            "k8s_cluster_id": test_cluster["id"],
        },
    ).json()["data"]

    # Generate expired cert
    _, expired_cert = generate_cert(
        "test-cert",
        mock_cert_manager_k8s["ca_key"],
        mock_cert_manager_k8s["ca_cert"],
        ["example.com"],
        expired=True,
    )
    expired_pem = expired_cert.public_bytes(serialization.Encoding.PEM).decode("utf-8")

    expired_secret = MagicMock()
    expired_secret.metadata.name = "test-cert-secret"
    expired_secret.data = {
        "tls.crt": base64.b64encode(expired_pem.encode("utf-8")).decode("utf-8"),
    }

    ca_secret = MagicMock()
    ca_secret.metadata.name = "test-ca-secret"
    ca_secret.data = {
        "ca.crt": base64.b64encode(mock_cert_manager_k8s["ca_pem"].encode("utf-8")).decode("utf-8"),
    }

    mock_cert_manager_k8s["core"].return_value.list_namespaced_secret.side_effect = lambda namespace=None, **kwargs: MagicMock(
        items=[ca_secret, expired_secret]
    )

    resp = client.get(f"/api/v1/projects/{project['id']}/_cert_manager")
    assert resp.status_code == 200
    certs = resp.json()["certificates"]
    assert len(certs) == 1
    assert certs[0]["status"] == "Expired"
    assert certs[0]["status_reason"] is not None
    assert "expired" in certs[0]["status_reason"].lower()


def test_get_cert_manager_resources_invalid_signature(client: TestClient, test_cluster: dict, mock_cert_manager_k8s):
    """Test that a certificate with an invalid signature/rotated CA shows 'Invalid' status instead of 'Ready'."""
    project = client.post(
        "/api/v1/projects",
        json={
            "name": "project-cm-invalid-sig",
            "title": "Project CM Invalid Sig",
            "k8s_cluster_id": test_cluster["id"],
        },
    ).json()["data"]

    # Generate leaf cert with a different/older CA
    other_ca_key, other_ca_cert = generate_ca("Old Project CA")
    _, mismatched_cert = generate_cert(
        "test-cert",
        other_ca_key,
        other_ca_cert,
        ["example.com"],
    )
    mismatched_pem = mismatched_cert.public_bytes(serialization.Encoding.PEM).decode("utf-8")

    mismatched_secret = MagicMock()
    mismatched_secret.metadata.name = "test-cert-secret"
    mismatched_secret.data = {
        "tls.crt": base64.b64encode(mismatched_pem.encode("utf-8")).decode("utf-8"),
    }

    ca_secret = MagicMock()
    ca_secret.metadata.name = "test-ca-secret"
    ca_secret.data = {
        "ca.crt": base64.b64encode(mock_cert_manager_k8s["ca_pem"].encode("utf-8")).decode("utf-8"),
    }

    mock_cert_manager_k8s["core"].return_value.list_namespaced_secret.side_effect = lambda namespace=None, **kwargs: MagicMock(
        items=[ca_secret, mismatched_secret]
    )

    resp = client.get(f"/api/v1/projects/{project['id']}/_cert_manager")
    assert resp.status_code == 200
    certs = resp.json()["certificates"]
    assert len(certs) == 1
    assert certs[0]["status"] == "Invalid"
    assert certs[0]["status_reason"] is not None


def test_get_cert_manager_resources_missing_secret(client: TestClient, test_cluster: dict, mock_cert_manager_k8s):
    """Test that a certificate whose secret is missing shows 'Invalid' status."""
    project = client.post(
        "/api/v1/projects",
        json={
            "name": "project-cm-no-sec",
            "title": "Project CM No Sec",
            "k8s_cluster_id": test_cluster["id"],
        },
    ).json()["data"]

    # Secret list has only CA, missing test-cert-secret
    ca_secret = MagicMock()
    ca_secret.metadata.name = "test-ca-secret"
    ca_secret.data = {
        "ca.crt": base64.b64encode(mock_cert_manager_k8s["ca_pem"].encode("utf-8")).decode("utf-8"),
    }

    mock_cert_manager_k8s["core"].return_value.list_namespaced_secret.side_effect = lambda ns: MagicMock(
        items=[ca_secret]
    )
    mock_cert_manager_k8s["core"].return_value.read_namespaced_secret.side_effect = Exception("NotFound")

    resp = client.get(f"/api/v1/projects/{project['id']}/_cert_manager")
    assert resp.status_code == 200
    certs = resp.json()["certificates"]
    assert len(certs) == 1
    assert certs[0]["status"] == "Invalid"
    assert certs[0]["status_reason"] == "Secret missing or empty"


def test_get_issuer_ca_cert_success(client: TestClient, test_cluster: dict, mock_cert_manager_k8s):
    project = client.post(
        "/api/v1/projects",
        json={
            "name": "project-ca-success",
            "title": "Project CA Success",
            "k8s_cluster_id": test_cluster["id"],
        },
    ).json()["data"]

    # Namespaced Issuer CA cert
    resp = client.get(
        f"/api/v1/projects/{project['id']}/_issuer_cert",
        params={"name": "project-ca-success-selfsigned-issuer", "kind": "Issuer", "namespace": "project-ca-success"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["pem"] == mock_cert_manager_k8s["ca_pem"]
    assert data["filename"] == "project-ca-success-selfsigned-issuer-ca.crt"


def test_get_issuer_ca_cert_failures(client: TestClient, test_cluster: dict, mock_cert_manager_k8s):
    project = client.post(
        "/api/v1/projects",
        json={
            "name": "project-ca-failures",
            "title": "Project CA Failures",
            "k8s_cluster_id": test_cluster["id"],
        },
    ).json()["data"]

    # Non-CA issuer error
    resp = client.get(
        f"/api/v1/projects/{project['id']}/_issuer_cert",
        params={"name": "test-non-ca-issuer", "kind": "Issuer", "namespace": "project-ca-failures"},
    )
    assert resp.status_code == 400
    assert "does not have a CA secretName defined" in resp.json()["detail"]

    # Non-existent issuer
    resp = client.get(
        f"/api/v1/projects/{project['id']}/_issuer_cert",
        params={"name": "non-existent", "kind": "Issuer", "namespace": "project-ca-failures"},
    )
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_deploy_project_issuer(test_cluster: dict):
    from mindweaver.service.project.actions import SyncProjectIntegrationsAction
    from mindweaver.service.project.model import Project
    from mindweaver.fw.model import get_engine
    from sqlmodel.ext.asyncio.session import AsyncSession

    project = Project(
        name="project-deploy-issuer-test",
        title="Project Deploy Issuer Test",
        k8s_cluster_id=test_cluster["id"],
        ingress_domain="issuer-test.local",
    )

    engine = get_engine()
    async with AsyncSession(engine, expire_on_commit=False) as session:
        session.add(project)
        await session.commit()
        await session.refresh(project)

        mock_svc = MagicMock()
        mock_svc.session = session
        mock_svc.request = MagicMock()

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_proc = MagicMock()
            mock_proc.communicate = pytest.importorskip("unittest.mock").AsyncMock(
                return_value=(b"applied", b"")
            )
            mock_proc.returncode = 0
            mock_exec.return_value = mock_proc

            action = SyncProjectIntegrationsAction(project, mock_svc)
            action.session = session
            await action.run()

            # Verify kubectl command was run (ArgoCD project, issuer, and gateway)
            assert mock_exec.call_count >= 1
            args = mock_exec.call_args[0]
            assert "kubectl" in args
            assert "apply" in args


@pytest.mark.asyncio
async def test_deploy_project_trusted_certs(test_cluster: dict):
    from mindweaver.service.project.actions import SyncProjectIntegrationsAction
    from mindweaver.service.project.model import Project
    from mindweaver.service.trusted_certs.model import TrustedCert
    from mindweaver.fw.model import get_engine
    from sqlmodel.ext.asyncio.session import AsyncSession
    import base64

    project = Project(
        name="project-trusted-certs-test",
        title="Project Trusted Certs Test",
        k8s_cluster_id=test_cluster["id"],
        ingress_domain="trusted-certs-test.local",
    )

    engine = get_engine()
    async with AsyncSession(engine, expire_on_commit=False) as session:
        session.add(project)
        await session.commit()
        await session.refresh(project)

        # Create a TrustedCert for the project
        cert = TrustedCert(
            name="test-ca",
            title="Test CA",
            certificate="-----BEGIN CERTIFICATE-----\nMIIDXTCCAkWgAwIBAgIJAO...\n-----END CERTIFICATE-----",
            project_id=project.id,
        )
        session.add(cert)
        await session.commit()

        mock_svc = MagicMock()
        mock_svc.session = session
        mock_svc.request = MagicMock()

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_proc = MagicMock()
            mock_proc.communicate = pytest.importorskip("unittest.mock").AsyncMock(
                return_value=(b"applied", b"")
            )
            mock_proc.returncode = 0
            mock_exec.return_value = mock_proc

            applied_manifests = []
            async def mock_subprocess(*args, **kwargs):
                filepath = args[-1]
                with open(filepath, "r") as f:
                    applied_manifests.append(f.read())
                return mock_proc
            mock_exec.side_effect = mock_subprocess

            action = SyncProjectIntegrationsAction(project, mock_svc)
            action.session = session
            await action.run()

            # Check if any applied manifest contains the trusted-certs Secret
            secret_manifests = [m for m in applied_manifests if "kind: Secret" in m and "name: trusted-certs" in m]
            assert len(secret_manifests) == 1
            manifest = secret_manifests[0]
            assert "test-ca.crt:" in manifest
            # Base64 encoded value of the cert
            b64_val = base64.b64encode(cert.certificate.encode("utf-8")).decode("utf-8")
            assert b64_val in manifest


@pytest.mark.asyncio
async def test_deploy_project_empty_trusted_certs(test_cluster: dict):
    from mindweaver.service.project.actions import SyncProjectIntegrationsAction
    from mindweaver.service.project.model import Project
    from mindweaver.fw.model import get_engine
    from sqlmodel.ext.asyncio.session import AsyncSession

    project = Project(
        name="project-empty-certs-test",
        title="Project Empty Certs Test",
        k8s_cluster_id=test_cluster["id"],
        ingress_domain="empty-certs-test.local",
    )

    engine = get_engine()
    async with AsyncSession(engine, expire_on_commit=False) as session:
        session.add(project)
        await session.commit()
        await session.refresh(project)

        mock_svc = MagicMock()
        mock_svc.session = session
        mock_svc.request = MagicMock()

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_proc = MagicMock()
            mock_proc.communicate = pytest.importorskip("unittest.mock").AsyncMock(
                return_value=(b"applied", b"")
            )
            mock_proc.returncode = 0
            mock_exec.return_value = mock_proc

            applied_manifests = []
            async def mock_subprocess(*args, **kwargs):
                filepath = args[-1]
                with open(filepath, "r") as f:
                    applied_manifests.append(f.read())
                return mock_proc
            mock_exec.side_effect = mock_subprocess

            action = SyncProjectIntegrationsAction(project, mock_svc)
            action.session = session
            await action.run()

            # Verify that the trusted-certs secret is generated and applied
            secret_manifests = [m for m in applied_manifests if "kind: Secret" in m and "name: trusted-certs" in m]
            assert len(secret_manifests) == 1
            manifest = secret_manifests[0]
            assert "ca-certificates.crt" in manifest or "data: {}" in manifest



