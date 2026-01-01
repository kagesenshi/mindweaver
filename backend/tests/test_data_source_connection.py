"""Tests for data source test_connection endpoint."""

from fastapi.testclient import TestClient
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


def test_data_source_test_connection_api_success(client: TestClient, test_project):
    """Test successful API connection test."""
    with patch("mindweaver.service.data_source.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.get.return_value = mock_response

        test_resp = client.post(
            "/api/v1/data_sources/test_connection",
            headers={"X-Project-Id": str(test_project["id"])},
            json={
                "type": "API",
                "parameters": {
                    "base_url": "https://api.example.com",
                    "api_key": "test_api_key",
                },
                "project_id": test_project["id"],
            },
        )

        assert test_resp.status_code == 200
        data = test_resp.json()
        assert data["status"] == "success"
        assert "200" in data["message"]


def test_data_source_test_connection_database_success(client: TestClient, test_project):
    """Test successful database connection test."""
    with patch("mindweaver.service.data_source.create_engine") as mock_create_engine:
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        mock_connection = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_connection

        test_resp = client.post(
            "/api/v1/data_sources/test_connection",
            headers={"X-Project-Id": str(test_project["id"])},
            json={
                "type": "Database",
                "parameters": {
                    "database_type": "postgresql",
                    "host": "localhost",
                    "port": 5432,
                    "username": "testuser",
                    "password": "testpass",
                },
                "project_id": test_project["id"],
            },
        )

        assert test_resp.status_code == 200
        data = test_resp.json()
        assert data["status"] == "success"
        assert "database" in data["message"].lower()


def test_data_source_test_connection_web_scraper_success(
    client: TestClient, test_project
):
    """Test successful web scraper connection test."""
    with patch("mindweaver.service.data_source.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.get.return_value = mock_response

        test_resp = client.post(
            "/api/v1/data_sources/test_connection",
            headers={"X-Project-Id": str(test_project["id"])},
            json={
                "type": "Web Scraper",
                "parameters": {
                    "start_url": "https://example.com",
                },
                "project_id": test_project["id"],
            },
        )

        assert test_resp.status_code == 200
        data = test_resp.json()
        assert data["status"] == "success"
        assert "200" in data["message"]


def test_data_source_test_connection_file_upload(client: TestClient, test_project):
    """Test file upload connection (should always succeed)."""
    test_resp = client.post(
        "/api/v1/data_sources/test_connection",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "type": "File Upload",
            "parameters": {},
            "project_id": test_project["id"],
        },
    )

    assert test_resp.status_code == 200
    data = test_resp.json()
    assert data["status"] == "success"
    assert "file upload" in data["message"].lower()


def test_data_source_test_connection_api_unreachable(client: TestClient, test_project):
    """Test API connection when URL is unreachable."""
    with patch("mindweaver.service.data_source.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # Mock connection error
        import httpx

        mock_client.get.side_effect = httpx.ConnectError("Connection refused")

        test_resp = client.post(
            "/api/v1/data_sources/test_connection",
            headers={"X-Project-Id": str(test_project["id"])},
            json={
                "type": "API",
                "parameters": {
                    "base_url": "https://invalid-url.example.com",
                    "api_key": "test_key",
                },
                "project_id": test_project["id"],
            },
        )

        assert test_resp.status_code == 400


def test_data_source_test_connection_database_invalid_credentials(
    client: TestClient, test_project
):
    """Test database connection with invalid credentials."""
    with patch("mindweaver.service.data_source.create_engine") as mock_create_engine:
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        # Mock authentication error
        from sqlalchemy.exc import OperationalError

        mock_engine.connect.side_effect = OperationalError(
            "Authentication failed", None, None
        )

        test_resp = client.post(
            "/api/v1/data_sources/test_connection",
            headers={"X-Project-Id": str(test_project["id"])},
            json={
                "type": "Database",
                "parameters": {
                    "database_type": "postgresql",
                    "host": "localhost",
                    "port": 5432,
                    "username": "baduser",
                    "password": "badpass",
                },
                "project_id": test_project["id"],
            },
        )

        assert test_resp.status_code == 400
        data = test_resp.json()
        assert "failed" in data["detail"].lower()


def test_data_source_test_connection_web_scraper_404(client: TestClient, test_project):
    """Test web scraper connection when URL returns 404."""
    with patch("mindweaver.service.data_source.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # Mock 404 response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_client.get.return_value = mock_response

        test_resp = client.post(
            "/api/v1/data_sources/test_connection",
            headers={"X-Project-Id": str(test_project["id"])},
            json={
                "type": "Web Scraper",
                "parameters": {
                    "start_url": "https://example.com/nonexistent",
                },
                "project_id": test_project["id"],
            },
        )

        assert test_resp.status_code == 400
        data = test_resp.json()
        assert "404" in data["detail"]


def test_data_source_test_connection_with_stored_password(
    client: TestClient, test_project
):
    """Test database connection using stored encrypted password."""
    # Create a data source with password
    create_resp = client.post(
        "/api/v1/data_sources",
        headers={"X-Project-Id": str(test_project["id"])},
        json={
            "name": "db-with-password",
            "title": "DB With Password",
            "type": "Database",
            "parameters": {
                "database_type": "postgresql",
                "host": "localhost",
                "port": 5432,
                "username": "testuser",
                "password": "stored_password",
            },
            "project_id": test_project["id"],
        },
    )
    assert create_resp.status_code == 200
    source_id = create_resp.json()["record"]["id"]

    # Test connection without providing password (should use stored one)
    with patch("mindweaver.service.data_source.create_engine") as mock_create_engine:
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        mock_connection = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_connection

        test_resp = client.post(
            "/api/v1/data_sources/test_connection",
            headers={"X-Project-Id": str(test_project["id"])},
            json={
                "type": "Database",
                "source_id": source_id,
                "parameters": {
                    "database_type": "postgresql",
                    "host": "localhost",
                    "port": 5432,
                    "username": "testuser",
                    # No password provided - should use stored one
                },
                "project_id": test_project["id"],
            },
        )

        assert test_resp.status_code == 200
        data = test_resp.json()
        assert data["status"] == "success"


def test_data_source_test_connection_database_different_types(
    client: TestClient, test_project
):
    """Test database connection for different database types."""
    db_types = ["postgresql", "mysql", "mssql"]

    for db_type in db_types:
        with patch(
            "mindweaver.service.data_source.create_engine"
        ) as mock_create_engine:
            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine

            mock_connection = MagicMock()
            mock_engine.connect.return_value.__enter__.return_value = mock_connection

            test_resp = client.post(
                "/api/v1/data_sources/test_connection",
                headers={"X-Project-Id": str(test_project["id"])},
                json={
                    "type": "Database",
                    "parameters": {
                        "database_type": db_type,
                        "host": "localhost",
                        "port": 5432,
                        "username": "testuser",
                        "password": "testpass",
                    },
                    "project_id": test_project["id"],
                },
            )

            assert test_resp.status_code == 200, f"Failed for {db_type}"
            data = test_resp.json()
            assert data["status"] == "success"


def test_data_source_test_connection_api_with_auth_header(
    client: TestClient, test_project
):
    """Test that API connection includes authorization header."""
    with patch("mindweaver.service.data_source.httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.get.return_value = mock_response

        test_resp = client.post(
            "/api/v1/data_sources/test_connection",
            headers={"X-Project-Id": str(test_project["id"])},
            json={
                "type": "API",
                "parameters": {
                    "base_url": "https://api.example.com",
                    "api_key": "test_api_key_12345",
                },
                "project_id": test_project["id"],
            },
        )

        assert test_resp.status_code == 200

        # Verify that the API was called with authorization header
        mock_client.get.assert_called_once()
        call_kwargs = mock_client.get.call_args[1]
        assert "headers" in call_kwargs
        assert "Authorization" in call_kwargs["headers"]
        assert "test_api_key_12345" in call_kwargs["headers"]["Authorization"]
