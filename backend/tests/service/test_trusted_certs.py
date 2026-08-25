# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from fastapi.testclient import TestClient
from mindweaver.platform_service.trino.service import TrinoPlatformService
from mindweaver.platform_service.trino.model import TrinoPlatform


@pytest.fixture
def anyio_backend():
    return "asyncio"


def generate_valid_cert_pem():
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import rsa
    import datetime

    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "test-ca"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Mindweaver Test Org"),
    ])
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
    ).not_valid_after(
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=10)
    ).sign(private_key, hashes.SHA256())
    
    from cryptography.hazmat.primitives import serialization
    return cert.public_bytes(serialization.Encoding.PEM).decode("utf-8")


VALID_CERT = generate_valid_cert_pem()


def test_trusted_cert_crud(client: TestClient, test_project):
    """
    Test creating, reading, updating, and deleting a TrustedCert.
    """
    # Create valid cert
    payload = {
        "name": "test-ca-cert",
        "title": "Test CA Certificate",
        "certificate": VALID_CERT,
        "project_id": test_project["id"],
    }
    resp = client.post(
        "/api/v1/trusted_certs",
        json=payload,
        headers={"X-Project-ID": str(test_project["id"])}
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["name"] == "test-ca-cert"
    assert data["certificate"] == VALID_CERT

    cert_id = data["id"]

    # Get list
    resp = client.get(
        "/api/v1/trusted_certs",
        headers={"X-Project-ID": str(test_project["id"])}
    )
    assert resp.status_code == 200
    items = resp.json()["data"]
    assert len(items) >= 1
    assert any(i["id"] == cert_id for i in items)

    # Update cert
    update_payload = {
        "title": "Updated Test CA Certificate",
        "project_id": test_project["id"],
    }
    resp = client.put(
        f"/api/v1/trusted_certs/{cert_id}",
        json=update_payload,
        headers={"X-Project-ID": str(test_project["id"])}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["title"] == "Updated Test CA Certificate"

    # Delete cert (X-RESOURCE-NAME header is required)
    resp = client.delete(
        f"/api/v1/trusted_certs/{cert_id}",
        headers={
            "X-Project-ID": str(test_project["id"]),
            "X-RESOURCE-NAME": "test-ca-cert",
        }
    )
    assert resp.status_code == 200


def test_trusted_cert_invalid_format(client: TestClient, test_project):
    """
    Test that invalid PEM certificates raise a validation error.
    """
    payload = {
        "name": "invalid-cert",
        "title": "Invalid Certificate",
        "certificate": "not-a-pem-certificate",
        "project_id": test_project["id"],
    }
    resp = client.post(
        "/api/v1/trusted_certs",
        json=payload,
        headers={"X-Project-ID": str(test_project["id"])}
    )
    assert resp.status_code == 422, resp.text
    err = resp.json()
    assert err["type"] == "validation_error"


@pytest.mark.anyio
async def test_trusted_certs_integration_template_vars(client: TestClient, test_project):
    """
    Test that platform service template_vars correctly retrieves trusted certs.
    """
    # 1. Create trusted cert via API
    payload = {
        "name": "test-integration-cert",
        "title": "Integration Cert",
        "certificate": VALID_CERT,
        "project_id": test_project["id"],
    }
    resp = client.post(
        "/api/v1/trusted_certs",
        json=payload,
        headers={"X-Project-ID": str(test_project["id"])}
    )
    assert resp.status_code == 200, resp.text

    # 2. Fetch via TrinoPlatformService
    from mindweaver.fw.model import get_engine
    from sqlmodel.ext.asyncio.session import AsyncSession
    
    engine = get_engine()
    async with AsyncSession(engine) as session:
        platform = TrinoPlatform(
            name="test-trino",
            title="Test Trino",
            project_id=test_project["id"],
            k8s_cluster_id=1,
        )
        
        svc = TrinoPlatformService(None, session)
        vars = await svc.template_vars(platform)
        
        assert "trusted_certs" in vars
        assert len(vars["trusted_certs"]) == 1
        assert vars["trusted_certs"][0]["name"] == "test-integration-cert"
        assert vars["trusted_certs"][0]["certificate"] == VALID_CERT
        assert vars["trusted_certs"][0]["certificate_b64"] is not None


def test_trusted_certs_decode(client: TestClient, test_project):
    """
    Test the custom _decode endpoint for a trusted certificate.
    """
    # 1. Create cert
    payload = {
        "name": "test-decode-cert",
        "title": "Test Decode Cert",
        "certificate": VALID_CERT,
        "project_id": test_project["id"],
    }
    resp = client.post(
        "/api/v1/trusted_certs",
        json=payload,
        headers={"X-Project-ID": str(test_project["id"])}
    )
    assert resp.status_code == 200, resp.text
    cert_id = resp.json()["data"]["id"]

    # 2. Call decode view
    resp = client.get(
        f"/api/v1/trusted_certs/{cert_id}/_decode",
        headers={"X-Project-ID": str(test_project["id"])}
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "subject" in data
    assert "issuer" in data
    assert "valid_from" in data
    assert "valid_to" in data
    assert data["is_valid"] is not None
    assert "serial_number" in data
    assert "version" in data
    assert "signature_algorithm" in data


def test_trusted_cert_hooks_trigger_sync(client: TestClient, test_project):
    """
    Test that creating, updating, and deleting a TrustedCert triggers the Celery task.
    """
    from unittest.mock import patch

    # Mock the Celery task delay method
    with patch("mindweaver.tasks.project_tasks.sync_trusted_certs_secret_task.delay") as mock_delay:
        # 1. Create a certificate
        payload = {
            "name": "hook-test-ca",
            "title": "Hook Test CA",
            "certificate": VALID_CERT,
            "project_id": test_project["id"],
        }
        resp = client.post(
            "/api/v1/trusted_certs",
            json=payload,
            headers={"X-Project-ID": str(test_project["id"])}
        )
        assert resp.status_code == 200, resp.text
        cert_id = resp.json()["data"]["id"]
        
        # Verify delay was called with the project ID
        assert mock_delay.call_count == 1
        mock_delay.assert_called_with(test_project["id"])
        
        mock_delay.reset_mock()

        # 2. Update the certificate
        update_payload = {
            "title": "Hook Test CA Updated",
            "project_id": test_project["id"],
        }
        resp = client.put(
            f"/api/v1/trusted_certs/{cert_id}",
            json=update_payload,
            headers={"X-Project-ID": str(test_project["id"])}
        )
        assert resp.status_code == 200
        
        # Verify delay was called again
        assert mock_delay.call_count == 1
        mock_delay.assert_called_with(test_project["id"])
        
        mock_delay.reset_mock()

        # 3. Delete the certificate
        resp = client.delete(
            f"/api/v1/trusted_certs/{cert_id}",
            headers={
                "X-Project-ID": str(test_project["id"]),
                "X-RESOURCE-NAME": "hook-test-ca",
            }
        )
        assert resp.status_code == 200
        
        # Verify delay was called for deletion
        assert mock_delay.call_count == 1
        mock_delay.assert_called_with(test_project["id"])


