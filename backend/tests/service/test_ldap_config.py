# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def admin_headers():
    return {}  # Auth is disabled in test mode via MINDWEAVER_ENABLE_AUTH=false


@pytest.fixture
def ldap_config_data(test_project):
    return {
        "name": "test-ldap",
        "title": "Test LDAP",
        "server_url": "ldap://ldap.example.com",
        "bind_dn": "cn=admin,dc=example,dc=com",
        "bind_password": "supersecretpassword",
        "user_search_base": "ou=users,dc=example,dc=com",
        "user_search_filter": "(uid={0})",
        "username_attr": "uid",
        "verify_ssl": True
    }


def test_create_ldap_config(client: TestClient, ldap_config_data, admin_headers):
    response = client.post("/api/v1/ldap_configs", json=ldap_config_data, headers=admin_headers)
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["name"] == "test-ldap"
    assert data["server_url"] == "ldap://ldap.example.com"
    # Password should be redacted
    assert data["bind_password"] == "__REDACTED__"


def test_update_ldap_config(client: TestClient, ldap_config_data, admin_headers):
    # Create first
    resp = client.post("/api/v1/ldap_configs", json=ldap_config_data, headers=admin_headers)
    assert resp.status_code == 200
    config_id = resp.json()["data"]["id"]

    # Update without changing password
    update_data = {
        **ldap_config_data,
        "title": "Updated Test LDAP",
        "bind_password": "__REDACTED__"
    }
    resp = client.put(f"/api/v1/ldap_configs/{config_id}", json=update_data, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["title"] == "Updated Test LDAP"
    assert resp.json()["data"]["bind_password"] == "__REDACTED__"

    # Verify password is still the same
    verify_resp = client.post(
        f"/api/v1/ldap_configs/{config_id}/_verify-encrypted",
        json={"bind_password": "supersecretpassword"},
        headers=admin_headers
    )
    assert verify_resp.status_code == 200
    assert verify_resp.json() is True


def test_create_invalid_server_url(client: TestClient, ldap_config_data, admin_headers):
    ldap_config_data["server_url"] = "http://example.com"
    response = client.post("/api/v1/ldap_configs", json=ldap_config_data, headers=admin_headers)
    assert response.status_code == 422
    assert "Server URL must start with ldap://" in response.text


def test_test_connection_view(client: TestClient, admin_headers):
    # Test connection without saving (using mock if possible, but testing basic socket failure since no ldap is running)
    test_data = {
        "server_url": "ldap://localhost:38900",  # something unlikely to be running
        "bind_dn": "cn=admin,dc=example,dc=com",
        "bind_password": "pw",
        "verify_ssl": False
    }
    response = client.post("/api/v1/ldap_configs/_test-connection", json=test_data, headers=admin_headers)
    # It should fail properly, not crash with 500
    assert response.status_code == 422
    # Connection error message from ldap3 typically raises an exception that gets caught and returned as 422
    assert "socket" in response.text.lower() or "communication" in response.text.lower() or "connection" in response.text.lower()
