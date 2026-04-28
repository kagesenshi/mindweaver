# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import Request
from mindweaver.platform_service.ranger import RangerPlatform, RangerPlatformService
from mindweaver.fw.model import AsyncSession
from pydantic import ValidationError


@pytest.fixture
def mock_service_dependencies():
    request = MagicMock(spec=Request)
    session = MagicMock(spec=AsyncSession)
    session.exec = AsyncMock()
    return request, session


def test_ranger_resource_defaults():
    """Test default values for Ranger resource limits"""
    model = RangerPlatform(name="test-ranger", title="Test Ranger", project_id=1, database_id=10)
    assert model.cpu_request == 1.0
    assert model.cpu_limit == 2.0
    assert model.mem_request == 2.0
    assert model.mem_limit == 4.0


def test_ranger_validation():
    """Test validation logic for Ranger"""
    # Invalid CPU: request > limit
    with pytest.raises(ValidationError) as excinfo:
        RangerPlatform.model_validate(
            {
                "name": "test-ranger",
                "title": "Test Ranger",
                "project_id": 1,
                "database_id": 10,
                "cpu_request": 3.0,
                "cpu_limit": 2.0,
            }
        )
    assert "CPU request cannot be greater than CPU limit" in str(excinfo.value)


@pytest.mark.asyncio
async def test_ranger_template_vars(mock_service_dependencies):
    request, session = mock_service_dependencies
    svc = RangerPlatformService(request, session)

    model = RangerPlatform(
        name="test-ranger",
        project_id=1,
        database_id=10,
        s3_storage_id=100,
        admin_password="admin",
    )

    # Mock _resolve_namespace
    svc._resolve_namespace = AsyncMock(return_value="test-ns")

    # Mock PgSqlPlatformService
    mock_pgsql_svc = AsyncMock()
    mock_pgsql_model = MagicMock()
    mock_pgsql_model.name = "test-db"
    mock_pgsql_svc.get.return_value = mock_pgsql_model
    
    mock_pgsql_state = MagicMock()
    mock_pgsql_state.active = True
    mock_pgsql_state.db_user = "user"
    mock_pgsql_state.db_name = "ranger"
    mock_pgsql_state.db_pass = "pass"
    mock_pgsql_svc.platform_state.return_value = mock_pgsql_state

    # S3 Configuration Check
    mock_s3_svc = AsyncMock()
    mock_s3_model = MagicMock()
    mock_s3_model.endpoint_url = "http://s3.local"
    mock_s3_model.region = "us-east-1"
    mock_s3_model.access_key = "access"
    mock_s3_model.secret_key = "secret"
    mock_s3_svc.get.return_value = mock_s3_model

    with patch("mindweaver.platform_service.ranger.service.PgSqlPlatformService.get_service", AsyncMock(return_value=mock_pgsql_svc)), \
         patch("mindweaver.platform_service.ranger.service.S3StorageService.get_service", AsyncMock(return_value=mock_s3_svc)):
        
        # Test with default audit_s3_uri (s3://ranger/audit)
        vars = await svc.template_vars(model)
        
        assert vars["name"] == "test-ranger"
        assert vars["db_host"] == "test-db-pooler-rw.test-ns.svc.cluster.local"
        assert vars["db_user"] == "user"
        assert vars["db_pass"] == "pass"
        # s3://ranger/audit -> s3a://ranger/audit + /model.name
        assert vars["audit_hdfs_dest_dir"] == "s3a://ranger/audit/test-ranger"
        assert vars["admin_password"] == "admin"

        # Test with additional_properties
        model.additional_properties = {"ranger.test.prop": "value1", "another.prop": "value2"}
        vars = await svc.template_vars(model)
        assert vars["additional_properties"] == {"ranger.test.prop": "value1", "another.prop": "value2"}

        # Test with custom audit_s3_uri
        model.audit_s3_uri = "s3://my-bucket/my/path"
        vars = await svc.template_vars(model)
        assert vars["audit_hdfs_dest_dir"] == "s3a://my-bucket/my/path/test-ranger"


@pytest.mark.asyncio
async def test_ranger_invalid_db(mock_service_dependencies):
    request, session = mock_service_dependencies
    svc = RangerPlatformService(request, session)

    # Mock PgSql as inactive
    mock_pgsql_svc = AsyncMock()
    mock_pgsql_state = MagicMock()
    mock_pgsql_state.active = False
    mock_pgsql_svc.platform_state.return_value = mock_pgsql_state
    
    mock_pgsql_model = MagicMock()
    mock_pgsql_model.name = "test-db"
    mock_pgsql_svc.get.return_value = mock_pgsql_model

    model = RangerPlatform(
        name="test-ranger",
        project_id=1,
        database_id=10,
    )

    # Mock _resolve_namespace
    svc._resolve_namespace = AsyncMock(return_value="test-ns")

    with patch("mindweaver.platform_service.ranger.service.PgSqlPlatformService.get_service", AsyncMock(return_value=mock_pgsql_svc)):
        with pytest.raises(ValueError, match="is not active"):
            await svc.template_vars(model)
