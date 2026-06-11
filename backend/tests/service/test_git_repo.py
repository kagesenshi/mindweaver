# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch


def test_git_repo_crud(client: TestClient, test_project):
    """
    Test standard CRUD operations for GitRepo model without auth_type.
    """
    # Create
    payload = {
        "name": "my-repo",
        "title": "My Repo",
        "url": "https://github.com/my-org/my-repo.git",
        "username": "my-user",
        "password": "my-password",
        "project_id": test_project["id"],
    }
    resp = client.post(
        "/api/v1/git_repos",
        json=payload,
        headers={"X-Project-ID": str(test_project["id"])}
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["name"] == "my-repo"
    assert data["password"] == "__REDACTED__"

    # Read/List
    resp = client.get(
        "/api/v1/git_repos",
        headers={"X-Project-ID": str(test_project["id"])}
    )
    assert resp.status_code == 200
    records = resp.json()["data"]
    assert len(records) > 0

    # Update
    update_payload = {
        "title": "My Updated Repo",
        "password": "__REDACTED__"
    }
    resp = client.put(
        f"/api/v1/git_repos/{data['id']}",
        json=update_payload,
        headers={"X-Project-ID": str(test_project["id"])}
    )
    assert resp.status_code == 200
    updated_data = resp.json()["data"]
    assert updated_data["title"] == "My Updated Repo"


@patch("asyncio.create_subprocess_exec")
def test_git_repo_test_connection_success(mock_subprocess, client: TestClient, test_project):
    """
    Test successful connection test with inferred none auth.
    """
    # Mock git ls-remote output
    mock_process = AsyncMock()
    mock_process.returncode = 0
    mock_process.communicate.return_value = (b"some-commit-sha\tHEAD\n", b"")
    mock_subprocess.return_value = mock_process

    payload = {
        "url": "https://github.com/my-org/my-repo.git",
    }
    resp = client.post(
        "/api/v1/git_repos/_test-connection",
        json=payload,
        headers={"X-Project-ID": str(test_project["id"])}
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "success"
    assert "Successfully connected" in data["message"]


@patch("asyncio.create_subprocess_exec")
def test_git_repo_test_connection_failure(mock_subprocess, client: TestClient, test_project):
    """
    Test failed connection test for GitRepo.
    """
    # Mock git ls-remote error output
    mock_process = AsyncMock()
    mock_process.returncode = 128
    mock_process.communicate.return_value = (b"", b"fatal: repository not found")
    mock_subprocess.return_value = mock_process

    payload = {
        "url": "https://github.com/my-org/non-existent.git",
    }
    resp = client.post(
        "/api/v1/git_repos/_test-connection",
        json=payload,
        headers={"X-Project-ID": str(test_project["id"])}
    )
    assert resp.status_code == 422, resp.text
    err = resp.json()
    assert err["type"] == "validation_error"
