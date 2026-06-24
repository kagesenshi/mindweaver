# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
import base64
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient


@pytest.fixture
def mock_cert_manager_k8s():
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

        # Mock read_namespaced_secret
        def _mock_read_namespaced_secret(name, namespace):
            if name == "test-ca-secret":
                secret = MagicMock()
                secret.data = {
                    "ca.crt": base64.b64encode(b"FAKE_PEM_CERTIFICATE_DATA").decode("utf-8")
                }
                return secret
            raise Exception("SecretNotFound")

        mock_core.return_value.read_namespaced_secret.side_effect = _mock_read_namespaced_secret

        yield {"custom": mock_custom, "core": mock_core}


def test_get_cert_manager_resources(client: TestClient, test_cluster: dict, mock_cert_manager_k8s):
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
    assert data["pem"] == "FAKE_PEM_CERTIFICATE_DATA"
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


def test_deploy_project_issuer(client: TestClient, test_cluster: dict):
    project = client.post(
        "/api/v1/projects",
        json={
            "name": "project-deploy-issuer-test",
            "title": "Project Deploy Issuer Test",
            "k8s_cluster_id": test_cluster["id"],
        },
    ).json()["data"]

    with patch("asyncio.create_subprocess_exec") as mock_exec:
        mock_proc = MagicMock()
        mock_proc.communicate = AsyncMock(return_value=(b"applied", b""))
        mock_proc.returncode = 0
        mock_exec.return_value = mock_proc

        resp = client.post(f"/api/v1/projects/{project['id']}/_deploy_issuer")
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

        # Verify kubectl command was run
        mock_exec.assert_called_once()
        args = mock_exec.call_args[0]
        assert "kubectl" in args
        assert "apply" in args

