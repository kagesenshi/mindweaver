# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from fastapi.testclient import TestClient


def test_ssh_key_generation_rsa_default(client: TestClient, test_project):
    """
    Test creating an SSHKey with default settings (RSA 4096).
    """
    payload = {
        "name": "rsa-default",
        "title": "RSA Default Key",
        "project_id": test_project["id"],
    }
    resp = client.post(
        "/api/v1/ssh_keys",
        json=payload,
        headers={"X-Project-ID": str(test_project["id"])}
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["name"] == "rsa-default"
    assert data["private_key"] == "__REDACTED__"
    assert data["public_key"] is not None
    assert "ssh-rsa" in data["public_key"]
    assert data["algorithm"] == "rsa"
    assert data["key_size"] == 4096


def test_ssh_key_generation_rsa_2048(client: TestClient, test_project):
    """
    Test creating an SSHKey with RSA 2048.
    """
    payload = {
        "name": "rsa-2048",
        "title": "RSA 2048 Key",
        "algorithm": "rsa",
        "key_size": 2048,
        "project_id": test_project["id"],
    }
    resp = client.post(
        "/api/v1/ssh_keys",
        json=payload,
        headers={"X-Project-ID": str(test_project["id"])}
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["name"] == "rsa-2048"
    assert "ssh-rsa" in data["public_key"]
    assert data["algorithm"] == "rsa"
    assert data["key_size"] == 2048


def test_ssh_key_generation_ed25519(client: TestClient, test_project):
    """
    Test creating an SSHKey with Ed25519.
    """
    payload = {
        "name": "ed25519-key",
        "title": "Ed25519 Key",
        "algorithm": "ed25519",
        "project_id": test_project["id"],
    }
    resp = client.post(
        "/api/v1/ssh_keys",
        json=payload,
        headers={"X-Project-ID": str(test_project["id"])}
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["name"] == "ed25519-key"
    assert "ssh-ed25519" in data["public_key"]
    assert data["algorithm"] == "ed25519"


def test_ssh_key_invalid_algorithm(client: TestClient, test_project):
    """
    Test that invalid algorithm input returns a validation error.
    """
    payload = {
        "name": "invalid-alg",
        "title": "Invalid Alg Key",
        "algorithm": "xyz",
        "project_id": test_project["id"],
    }
    resp = client.post(
        "/api/v1/ssh_keys",
        json=payload,
        headers={"X-Project-ID": str(test_project["id"])}
    )
    assert resp.status_code == 422, resp.text
    err = resp.json()
    assert err["type"] == "validation_error"
