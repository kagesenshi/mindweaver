# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
import base64
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def mock_cert_manager_k8s():
    with patch(
        "mindweaver.service.k8s_cluster.views.config.load_incluster_config"
    ), patch(
        "mindweaver.service.k8s_cluster.views.client.CustomObjectsApi"
    ) as mock_custom, patch(
        "mindweaver.service.k8s_cluster.views.client.CoreV1Api"
    ) as mock_core:

        # Mock list_cluster_custom_object return value for issuers
        def _mock_list_cluster_custom_object(group, version, plural):
            if plural == "issuers":
                return {
                    "items": [
                        {
                            "metadata": {"name": "test-issuer", "namespace": "default"},
                            "status": {
                                "conditions": [{"type": "Ready", "status": "True"}]
                            },
                        }
                    ]
                }
            elif plural == "clusterissuers":
                return {
                    "items": [
                        {
                            "metadata": {"name": "test-clusterissuer"},
                            "status": {
                                "conditions": [{"type": "Ready", "status": "False", "reason": "Expired"}]
                            },
                        }
                    ]
                }
            elif plural == "certificates":
                return {
                    "items": [
                        {
                            "metadata": {"name": "test-cert", "namespace": "default"},
                            "spec": {
                                "issuerRef": {"name": "test-issuer", "kind": "Issuer"},
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

        # Mock get_cluster_custom_object and get_namespaced_custom_object
        def _mock_get_cluster_custom_object(group, version, plural, name):
            if name == "test-clusterissuer":
                return {
                    "metadata": {"name": "test-clusterissuer"},
                    "spec": {
                        "ca": {"secretName": "test-ca-secret"}
                    }
                }
            elif name == "test-non-ca-issuer":
                return {
                    "metadata": {"name": "test-non-ca-issuer"},
                    "spec": {
                        "selfSigned": {}
                    }
                }
            raise Exception("NotFound")

        def _mock_get_namespaced_custom_object(group, version, plural, namespace, name):
            if name == "test-issuer":
                return {
                    "metadata": {"name": "test-issuer", "namespace": namespace},
                    "spec": {
                        "ca": {"secretName": "test-ca-secret"}
                    }
                }
            raise Exception("NotFound")

        mock_custom.return_value.list_cluster_custom_object.side_effect = _mock_list_cluster_custom_object
        mock_custom.return_value.get_cluster_custom_object.side_effect = _mock_get_cluster_custom_object
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


def test_get_cert_manager_resources(client: TestClient, mock_cert_manager_k8s):
    # Create cluster
    cluster = client.post(
        "/api/v1/k8s_clusters",
        json={
            "name": "cm-test",
            "title": "CM Test",
            "type": "in-cluster",
        },
    ).json()["data"]

    # Call the endpoint
    resp = client.get(f"/api/v1/k8s_clusters/{cluster['id']}/_cert_manager")
    assert resp.status_code == 200
    data = resp.json()

    assert "issuers" in data
    assert "certificates" in data

    issuers = data["issuers"]
    assert len(issuers) == 2
    assert issuers[0]["name"] == "test-issuer"
    assert issuers[0]["kind"] == "Issuer"
    assert issuers[0]["status"] == "Ready"
    assert issuers[1]["name"] == "test-clusterissuer"
    assert issuers[1]["kind"] == "ClusterIssuer"
    assert issuers[1]["status"] == "Not Ready (Expired)"

    certs = data["certificates"]
    assert len(certs) == 1
    assert certs[0]["name"] == "test-cert"
    assert certs[0]["issuer_name"] == "test-issuer"
    assert certs[0]["issuer_kind"] == "Issuer"
    assert certs[0]["status"] == "Ready"
    assert certs[0]["dns_names"] == ["example.com"]
    assert certs[0]["secret_name"] == "test-cert-secret"
    assert certs[0]["not_after"] == "2026-12-31T23:59:59Z"


def test_get_issuer_ca_cert_success(client: TestClient, mock_cert_manager_k8s):
    cluster = client.post(
        "/api/v1/k8s_clusters",
        json={
            "name": "ca-test-success",
            "title": "CA Test Success",
            "type": "in-cluster",
        },
    ).json()["data"]

    # ClusterIssuer CA cert
    resp = client.get(
        f"/api/v1/k8s_clusters/{cluster['id']}/_issuer_cert",
        params={"name": "test-clusterissuer", "kind": "ClusterIssuer"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["pem"] == "FAKE_PEM_CERTIFICATE_DATA"
    assert data["filename"] == "test-clusterissuer-ca.crt"

    # Namespaced Issuer CA cert
    resp = client.get(
        f"/api/v1/k8s_clusters/{cluster['id']}/_issuer_cert",
        params={"name": "test-issuer", "kind": "Issuer", "namespace": "default"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["pem"] == "FAKE_PEM_CERTIFICATE_DATA"
    assert data["filename"] == "test-issuer-ca.crt"


def test_get_issuer_ca_cert_failures(client: TestClient, mock_cert_manager_k8s):
    cluster = client.post(
        "/api/v1/k8s_clusters",
        json={
            "name": "ca-test-failures",
            "title": "CA Test Failures",
            "type": "in-cluster",
        },
    ).json()["data"]

    # Non-CA issuer error
    resp = client.get(
        f"/api/v1/k8s_clusters/{cluster['id']}/_issuer_cert",
        params={"name": "test-non-ca-issuer", "kind": "ClusterIssuer"},
    )
    assert resp.status_code == 400
    assert "does not have a CA secretName defined" in resp.json()["detail"]

    # Non-existent issuer
    resp = client.get(
        f"/api/v1/k8s_clusters/{cluster['id']}/_issuer_cert",
        params={"name": "non-existent", "kind": "Issuer", "namespace": "default"},
    )
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"]
