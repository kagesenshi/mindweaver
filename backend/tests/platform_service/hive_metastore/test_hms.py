# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import Request
from sqlmodel import Session
from mindweaver.platform_service.hive_metastore import HiveMetastorePlatform, HiveMetastorePlatformService
from mindweaver.fw.model import AsyncSession
from pydantic import ValidationError
import yaml


@pytest.fixture
def mock_service_dependencies():
    request = MagicMock(spec=Request)
    session = MagicMock(spec=AsyncSession)
    session.exec = AsyncMock()
    return request, session


def test_hms_resource_defaults():
    """Test default values for HMS resource limits"""
    model = HiveMetastorePlatform(name="test-hms", title="Test HMS", project_id=1, database_id=10)
    assert model.cpu_request == 0.5
    assert model.cpu_limit == 1.0
    assert model.mem_request == 1.0
    assert model.mem_limit == 2.0


def test_hms_override_image_defaults():
    """Test that override_image and chart_version have correct defaults"""
    model = HiveMetastorePlatform(name="test-hms", title="Test HMS", project_id=1, database_id=10)
    assert model.override_image is False
    assert model.chart_version == "0.1.8"


def test_hms_override_image_flag():
    """Test that image field can be set independently of override_image flag"""
    # override_image=False: image is stored but not used in template
    model = HiveMetastorePlatform.model_validate({
        "name": "test-hms",
        "title": "Test HMS",
        "project_id": 1,
        "database_id": 10,
        "override_image": False,
        "image": "ghcr.io/kagesenshi/mindweaver/hive-metastore:v1.0.0",
    })
    assert model.override_image is False
    assert model.image == "ghcr.io/kagesenshi/mindweaver/hive-metastore:v1.0.0"

    # override_image=True: image should be used in template
    model2 = HiveMetastorePlatform.model_validate({
        "name": "test-hms",
        "title": "Test HMS",
        "project_id": 1,
        "database_id": 10,
        "override_image": True,
        "image": "ghcr.io/kagesenshi/mindweaver/hive-metastore:v1.0.0",
    })
    assert model2.override_image is True
    assert model2.image == "ghcr.io/kagesenshi/mindweaver/hive-metastore:v1.0.0"


def test_hms_validation():
    """Test validation logic for HMS"""
    # Valid case
    model = HiveMetastorePlatform.model_validate(
        {
            "name": "test-hms",
            "title": "Test HMS",
            "project_id": 1,
            "database_id": 10,
            "cpu_request": 1.0,
            "cpu_limit": 2.0,
        }
    )
    assert model.cpu_request == 1.0

    # Invalid CPU: request > limit
    with pytest.raises(ValidationError) as excinfo:
        HiveMetastorePlatform.model_validate(
            {
                "name": "test-hms",
                "title": "Test HMS",
                "project_id": 1,
                "database_id": 10,
                "cpu_request": 2.0,
                "cpu_limit": 1.0,
            }
        )
    assert "CPU request cannot be greater than CPU limit" in str(excinfo.value)

    # Missing database config
    with pytest.raises(ValidationError) as excinfo:
        HiveMetastorePlatform.model_validate(
            {
                "name": "test-hms",
                "title": "Test HMS",
                "project_id": 1,
            }
        )
    assert "database_id" in str(excinfo.value)


@pytest.mark.asyncio
async def test_hms_template_rendering(mock_service_dependencies):
    """Test that the HMS templates render correctly"""
    request, session = mock_service_dependencies
    svc = HiveMetastorePlatformService(request, session)

    model = HiveMetastorePlatform(
        name="hms-test",
        title="HMS Test",
        project_id=1,
        database_id=10,
        iceberg_enabled=True,
    )

    # Mock _resolve_namespace
    svc._resolve_namespace = AsyncMock(return_value="hms-ns")

    # Mock PgSqlPlatformService
    mock_pgsql_svc = AsyncMock()
    mock_pgsql_model = MagicMock()
    mock_pgsql_model.name = "test-pgsql"
    mock_pgsql_svc.get.return_value = mock_pgsql_model
    
    mock_pgsql_state = MagicMock()
    mock_pgsql_state.active = True
    mock_pgsql_state.db_user = "hms_user"
    mock_pgsql_state.db_name = "metastore"
    mock_pgsql_state.db_pass = "secret"
    mock_pgsql_svc.platform_state.return_value = mock_pgsql_state

    # Mock S3StorageService
    mock_s3_svc = AsyncMock()
    mock_s3_model = MagicMock()
    mock_s3_model.endpoint_url = "http://minio:9000"
    mock_s3_model.access_key = "access"
    mock_s3_model.secret_key = "secret"
    mock_s3_svc.get.return_value = mock_s3_model

    model.s3_storage_id = 100

    # Mock S3StorageService
    mock_s3_svc = AsyncMock()
    mock_s3_model = MagicMock()
    mock_s3_model.endpoint_url = "http://minio:9000"
    mock_s3_model.access_key = "access"
    mock_s3_model.secret_key = "secret"
    mock_s3_svc.get.return_value = mock_s3_model

    model.s3_storage_id = 100

    # Mock session.exec for S3StorageService.get
    mock_result = MagicMock()
    mock_result.first.return_value = mock_s3_model
    session.exec.return_value = mock_result

    with patch("mindweaver.platform_service.hive_metastore.service.PgSqlPlatformService.get_service", AsyncMock(return_value=mock_pgsql_svc)), \
         patch("mindweaver.platform_service.hive_metastore.service.S3StorageService.get_service", AsyncMock(return_value=mock_s3_svc)):
        # Get template variables
        vars = await svc.template_vars(model)

    assert vars["db_host"] == "test-pgsql-pooler-rw.hms-ns.svc.cluster.local"
    assert vars["db_user"] == "hms_user"
    assert vars["db_name"] == "metastore"
    assert vars["iceberg_enabled"] is True
    assert vars["namespace"] == "hms-ns"
    assert vars["s3_endpoint_url"] == "http://minio:9000"
    assert vars["aws_access_key_id"] == "access"
    assert vars["aws_secret_access_key"] == "secret"

    # Check template rendering logic (basic markers)
    import os
    app_template = os.path.join(svc.template_directory, "10-application.yml.j2")
    with open(app_template, "r") as f:
        content = f.read()
    
    assert "kind: Application" in content
    assert "oci://ghcr.io/kagesenshi/mindweaver/charts" in content
    assert "namespace: {{ namespace }}" in content

    sec_template = os.path.join(svc.template_directory, "01-secret.yml.j2")
    with open(sec_template, "r") as f:
        content = f.read()
    
    assert "kind: Secret" in content
    assert "user: \"{{ db_user }}\"" in content


@pytest.mark.asyncio
async def test_hms_manifest_parsing(mock_service_dependencies):
    """Replicate YAML parsing error by rendering and parsing manifests"""
    request, session = mock_service_dependencies
    svc = HiveMetastorePlatformService(request, session)

    model = HiveMetastorePlatform(
        name="hms-test",
        title="HMS Test",
        project_id=1,
        database_id=10,
        iceberg_enabled=True,
    )

    # Mock _resolve_namespace
    svc._resolve_namespace = AsyncMock(return_value="hms-ns")

    # Mock PgSqlPlatformService
    mock_pgsql_svc = AsyncMock()
    mock_pgsql_model = MagicMock()
    mock_pgsql_model.name = "test-pgsql"
    mock_pgsql_svc.get.return_value = mock_pgsql_model
    
    mock_pgsql_state = MagicMock()
    mock_pgsql_state.active = True
    mock_pgsql_state.db_user = "hms_user"
    mock_pgsql_state.db_name = "metastore"
    mock_pgsql_state.db_pass = "secret-token-123"
    mock_pgsql_svc.platform_state.return_value = mock_pgsql_state

    with patch("mindweaver.platform_service.hive_metastore.service.PgSqlPlatformService.get_service", AsyncMock(return_value=mock_pgsql_svc)):
        # Render manifest
        full_manifest = await svc.render_manifests(model)
    
    # Try to parse all documents - this should fail if joined incorrectly
    try:
        docs = list(yaml.safe_load_all(full_manifest))
        assert len(docs) >= 2
    except yaml.parser.ParserError as e:
        pytest.fail(f"YAML parsing failed: {e}")


@pytest.mark.asyncio
async def test_hms_override_image_template(mock_service_dependencies):
    """Test that the image block is rendered only when override_image=True"""
    request, session = mock_service_dependencies
    svc = HiveMetastorePlatformService(request, session)

    # Mock PgSqlPlatformService dependencies
    mock_pgsql_svc = AsyncMock()
    mock_pgsql_model = MagicMock()
    mock_pgsql_model.name = "test-pgsql"
    mock_pgsql_svc.get.return_value = mock_pgsql_model
    mock_pgsql_state = MagicMock()
    mock_pgsql_state.active = True
    mock_pgsql_state.db_user = "hms_user"
    mock_pgsql_state.db_name = "metastore"
    mock_pgsql_state.db_pass = "secret"
    mock_pgsql_svc.platform_state.return_value = mock_pgsql_state

    # Test with override_image=False: image block should NOT appear
    model_no_override = HiveMetastorePlatform(
        name="hms-test",
        title="HMS Test",
        project_id=1,
        database_id=10,
        override_image=False,
        image="ghcr.io/kagesenshi/mindweaver/hive-metastore:v1.0.0",
        chart_version="0.1.0",
    )
    svc._resolve_namespace = AsyncMock(return_value="hms-ns")

    with patch("mindweaver.platform_service.hive_metastore.service.PgSqlPlatformService.get_service", AsyncMock(return_value=mock_pgsql_svc)):
        manifest_no_override = await svc.render_manifests(model_no_override)

    assert "targetRevision: 0.1.0" in manifest_no_override
    assert "repository:" not in manifest_no_override

    # Test with override_image=True: image block should appear
    model_with_override = HiveMetastorePlatform(
        name="hms-test",
        title="HMS Test",
        project_id=1,
        database_id=10,
        override_image=True,
        image="ghcr.io/kagesenshi/mindweaver/hive-metastore:v1.0.0",
        chart_version="0.1.0",
    )

    with patch("mindweaver.platform_service.hive_metastore.service.PgSqlPlatformService.get_service", AsyncMock(return_value=mock_pgsql_svc)):
        manifest_with_override = await svc.render_manifests(model_with_override)

    assert "repository:" in manifest_with_override
    assert "v1.0.0" in manifest_with_override


@pytest.mark.asyncio
async def test_hms_chart_versions_endpoint():
    """Test the _chart-versions endpoint returns static versions"""
    from mindweaver.platform_service.hive_metastore.views import get_chart_versions
    
    result = await get_chart_versions()
        
    assert "data" in result
    assert isinstance(result["data"], list)
    assert len(result["data"]) > 0
    # Check that it contains at least some of the known versions
    versions = [item["value"] for item in result["data"]]
    assert "0.1.9" in versions
    assert "0.1.8" in versions
    # Ensure items have correct format
    for item in result["data"]:
        assert "label" in item
        assert "value" in item
        assert item["label"] == item["value"]


@pytest.mark.asyncio
async def test_hms_fullname_override(mock_service_dependencies):
    """Test that fullnameOverride is present in the rendered manifest"""
    request, session = mock_service_dependencies
    svc = HiveMetastorePlatformService(request, session)

    model = HiveMetastorePlatform(
        name="my-custom-hms",
        title="Custom HMS",
        project_id=1,
        database_id=10,
    )

    # Mock _resolve_namespace
    svc._resolve_namespace = AsyncMock(return_value="hms-ns")

    # Mock PgSqlPlatformService
    mock_pgsql_svc = AsyncMock()
    mock_pgsql_model = MagicMock()
    mock_pgsql_model.name = "test-pgsql"
    mock_pgsql_svc.get.return_value = mock_pgsql_model
    
    mock_pgsql_state = MagicMock()
    mock_pgsql_state.active = True
    mock_pgsql_state.db_user = "hms_user"
    mock_pgsql_state.db_name = "metastore"
    mock_pgsql_state.db_pass = "secret"
    mock_pgsql_svc.platform_state.return_value = mock_pgsql_state

    with patch("mindweaver.platform_service.hive_metastore.service.PgSqlPlatformService.get_service", AsyncMock(return_value=mock_pgsql_svc)):
        # Render manifest
        manifest = await svc.render_manifests(model)

    assert "fullnameOverride: my-custom-hms" in manifest

