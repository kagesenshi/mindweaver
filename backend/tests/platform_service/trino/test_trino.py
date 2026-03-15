# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
import yaml
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import Request
from sqlmodel import Session
from pydantic import ValidationError

from mindweaver.platform_service.trino import TrinoPlatform, TrinoPlatformService
from mindweaver.platform_service.hive_metastore import HiveMetastorePlatformState, HiveMetastorePlatform
from mindweaver.fw.model import AsyncSession


@pytest.fixture
def mock_service_dependencies():
    request = MagicMock(spec=Request)
    session = MagicMock(spec=AsyncSession)
    session.exec = AsyncMock()
    return request, session


def test_trino_resource_defaults():
    """Test default values for Trino resource limits"""
    model = TrinoPlatform(name="test-trino", title="Test Trino", project_id=1)
    assert model.cpu_limit == 2.0
    assert model.mem_request == 2.0
    assert model.mem_limit == 4.0
    assert model.data_source_ids == []
    assert model.hms_ids == []
    assert model.hms_iceberg_ids == []

    # New fields
    assert model.chart_version == "1.41.0"
    assert model.override_image is False


def test_trino_validation():
    """Test validation logic for Trino"""
    # Valid case
    model = TrinoPlatform.model_validate(
        {
            "name": "test-trino",
            "title": "Test Trino",
            "project_id": 1,
            "cpu_request": 1.0,
            "cpu_limit": 2.0,
            "data_source_ids": [1],
        }
    )
    assert model.cpu_request == 1.0

    # Invalid CPU: request > limit
    with pytest.raises(ValidationError) as excinfo:
        TrinoPlatform.model_validate(
            {
                "name": "test-trino",
                "title": "Test Trino",
                "project_id": 1,
                "cpu_request": 3.0,
                "cpu_limit": 2.0,
                "hms_ids": [1],
            }
        )
    assert "CPU request cannot be greater than CPU limit" in str(excinfo.value)

    # Invalid Memory: request > limit
    with pytest.raises(ValidationError) as excinfo:
        TrinoPlatform.model_validate(
            {
                "name": "test-trino",
                "title": "Test Trino",
                "project_id": 1,
                "mem_request": 10.0,
                "mem_limit": 5.0,
                "hms_ids": [1],
            }
        )
    assert "Memory request cannot be greater than Memory limit" in str(excinfo.value)

    # Invalid Catalogs: Same HMS for both Hive and Iceberg
    with pytest.raises(ValidationError) as excinfo:
        TrinoPlatform.model_validate(
            {
                "name": "test-trino",
                "title": "Test Trino",
                "project_id": 1,
                "hms_ids": [1],
                "hms_iceberg_ids": [1],
            }
        )
    assert "cannot be used for both Hive and Iceberg catalogs simultaneously" in str(excinfo.value)

    # Invalid Catalogs: No catalogs defined
    with pytest.raises(ValidationError) as excinfo:
        TrinoPlatform.model_validate(
            {
                "name": "test-trino",
                "title": "Test Trino",
                "project_id": 1,
                "hms_ids": [],
                "hms_iceberg_ids": [],
                "data_source_ids": [],
            }
        )
    assert "At least one catalog" in str(excinfo.value)


@pytest.mark.asyncio
async def test_trino_template_rendering(mock_service_dependencies):
    """Test that the Trino templates render correctly with HMS and DataSources"""
    request, session = mock_service_dependencies
    svc = TrinoPlatformService(request, session)

    model = TrinoPlatform(
        name="trino-test",
        title="Trino Test",
        project_id=1,
        hms_ids=[10],
        hms_iceberg_ids=[11],
        data_source_ids=[20],
    )

    # Mock _resolve_namespace
    svc._resolve_namespace = AsyncMock(return_value="trino-ns")

    # Mock HiveMetastorePlatformService
    mock_hms_svc = AsyncMock()
    
    mock_hms_model_10 = MagicMock()
    mock_hms_model_10.name = "test-hms-hive"
    mock_hms_model_10.s3_storage_id = 100
    
    mock_hms_model_11 = MagicMock()
    mock_hms_model_11.name = "test-hms-iceberg-cat"
    mock_hms_model_11.s3_storage_id = 100
    
    mock_hms_svc.get.side_effect = lambda id: mock_hms_model_10 if id == 10 else mock_hms_model_11
    mock_hms_svc._resolve_namespace.return_value = "hms-ns"

    # Mock S3StorageService
    mock_s3_svc = AsyncMock()
    mock_s3_model = MagicMock()
    mock_s3_model.endpoint_url = "http://minio:9000"
    mock_s3_model.access_key = "access"
    mock_s3_model.secret_key = "secret"
    mock_s3_model.region = "us-east-1"
    mock_s3_svc.get.return_value = mock_s3_model
    
    mock_hms_state = MagicMock()
    mock_hms_state.active = True
    mock_hms_state.hms_uri = "thrift://hms-internal:9083"
    mock_hms_svc.platform_state.return_value = mock_hms_state

    # Mock DataSourceService
    mock_ds_svc = AsyncMock()
    mock_ds_model = MagicMock()
    mock_ds_model.name = "mypsql"
    mock_ds_model.driver = "postgresql"
    mock_ds_model.host = "postgres-host"
    mock_ds_model.port = 5432
    mock_ds_model.resource = "mydb"
    mock_ds_model.login = "usr"
    mock_ds_model.password = "pass"
    mock_ds_model.parameters = {"param1": "val1"}
    mock_ds_svc.get.return_value = mock_ds_model

    # Mock session.exec for S3StorageService.get
    mock_result = MagicMock()
    mock_result.first.return_value = mock_s3_model
    session.exec.return_value = mock_result

    with patch("mindweaver.platform_service.trino.service.HiveMetastorePlatformService.get_service", AsyncMock(return_value=mock_hms_svc)), \
         patch("mindweaver.platform_service.trino.service.DataSourceService.get_service", AsyncMock(return_value=mock_ds_svc)), \
         patch("mindweaver.platform_service.trino.service.S3StorageService.get_service", AsyncMock(return_value=mock_s3_svc)):
        
        vars = await svc.template_vars(model)

    assert "hms_uri" not in vars
    assert "iceberg_uri" not in vars
    assert len(vars["catalogs"]) == 3
    assert vars["preferred_catalog"] == "test-hms-iceberg-cat" # Iceberg has priority
    
    # Check HMS catalog
    hms_cat = next(c for c in vars["catalogs"] if c["catalog"] == "test-hms-hive")
    assert hms_cat["properties"]["connector.name"] == "hive"
    assert hms_cat["properties"]["hive.metastore.uri"] == "thrift://hms-internal:9083"
    assert hms_cat["properties"]["fs.native-s3.enabled"] == "true"
    assert hms_cat["properties"]["s3.endpoint"] == "http://minio:9000"
    assert hms_cat["properties"]["s3.aws-access-key"] == "access"
    assert hms_cat["properties"]["s3.aws-secret-key"] == "secret"
    assert hms_cat["properties"]["s3.path-style-access"] == "true"

    # Check HMS Iceberg catalog
    iceberg_cat = next(c for c in vars["catalogs"] if c["catalog"] == "test-hms-iceberg-cat")
    assert iceberg_cat["properties"]["connector.name"] == "iceberg"
    assert iceberg_cat["properties"]["hive.metastore.uri"] == "thrift://hms-internal:9083"
    assert iceberg_cat["properties"]["fs.native-s3.enabled"] == "true"
    assert iceberg_cat["properties"]["s3.endpoint"] == "http://minio:9000"
    assert iceberg_cat["properties"]["s3.aws-access-key"] == "access"
    assert iceberg_cat["properties"]["s3.aws-secret-key"] == "secret"
    assert iceberg_cat["properties"]["s3.path-style-access"] == "true"

    # Check PG catalog
    pg_cat = next(c for c in vars["catalogs"] if c["catalog"] == "mypsql")
    assert pg_cat["properties"]["connector.name"] == "postgresql"
    assert "jdbc:postgresql://postgres-host:5432/mydb" in pg_cat["properties"]["connection-url"]
    assert pg_cat["properties"]["connection-user"] == "usr"
    assert pg_cat["properties"]["connection-password"] == "pass"

    # Render manifest
    with patch("mindweaver.platform_service.trino.service.HiveMetastorePlatformService.get_service", AsyncMock(return_value=mock_hms_svc)), \
         patch("mindweaver.platform_service.trino.service.DataSourceService.get_service", AsyncMock(return_value=mock_ds_svc)):
        full_manifest = await svc.render_manifests(model)
        
    try:
        docs = list(yaml.safe_load_all(full_manifest))
        assert len(docs) >= 1
    except yaml.parser.ParserError as e:
        pytest.fail(f"YAML parsing failed: {e}")
        
    app_doc = docs[0]
    assert app_doc["kind"] == "Application"
    assert app_doc["spec"]["destination"]["namespace"] == "trino-ns"
    values_yaml_str = app_doc["spec"]["source"]["helm"]["values"]
    values = yaml.safe_load(values_yaml_str)
    
    assert "test-hms-hive" in values["catalogs"]
    assert "test-hms-iceberg-cat" in values["catalogs"]
    assert "mypsql" in values["catalogs"]
    
    hive_props = values["catalogs"]["test-hms-hive"]
    assert "connector.name=hive" in hive_props
    assert "hive.metastore.uri=thrift://hms-internal:9083" in hive_props

    iceberg_props = values["catalogs"]["test-hms-iceberg-cat"]
    assert "connector.name=iceberg" in iceberg_props
    assert "hive.metastore.uri=thrift://hms-internal:9083" in iceberg_props

    assert "jdbc:postgresql://postgres-host:5432/mydb" in values["catalogs"]["mypsql"]
    
    assert values["service"]["type"] == "NodePort"


@pytest.mark.asyncio
async def test_trino_override_image_template(mock_service_dependencies):
    """Test that the image block is rendered only when override_image=True"""
    request, session = mock_service_dependencies
    svc = TrinoPlatformService(request, session)
    svc._resolve_namespace = AsyncMock(return_value="trino-ns")

    # Test with override_image=False: image block should NOT appear
    model_no_override = TrinoPlatform(
        name="trino-test",
        title="Trino Test",
        project_id=1,
        override_image=False,
        image="custom/trino:v1.0.0",
        chart_version="1.41.0",
    )

    manifest_no_override = await svc.render_manifests(model_no_override)

    assert "targetRevision: 1.41.0" in manifest_no_override
    assert "repository:" not in manifest_no_override

    # Test with override_image=True: image block should appear
    model_with_override = TrinoPlatform(
        name="trino-test",
        title="Trino Test",
        project_id=1,
        override_image=True,
        image="custom/trino:v1.0.0",
        chart_version="1.41.0",
    )

    manifest_with_override = await svc.render_manifests(model_with_override)

    assert "repository:" in manifest_with_override
    assert "v1.0.0" in manifest_with_override
    assert "custom/trino" in manifest_with_override


@pytest.mark.asyncio
async def test_trino_chart_versions_endpoint():
    """Test the _chart-versions endpoint returns static versions"""
    from mindweaver.platform_service.trino.views import get_chart_versions

    result = await get_chart_versions()

    assert "data" in result
    assert result["data"] == [
        {"label": "1.41.0", "value": "1.41.0"},
    ]


@pytest.mark.asyncio
async def test_trino_catalog_filtering(mock_service_dependencies):
    """Test that only supported catalog drivers are rendered"""
    request, session = mock_service_dependencies
    svc = TrinoPlatformService(request, session)
    svc._resolve_namespace = AsyncMock(return_value="trino-ns")

    # Mock Data Sources: one supported, one unsupported
    ds_supported = MagicMock()
    ds_supported.name = "mysql-ds"
    ds_supported.driver = "mysql"
    ds_supported.host = "mysql-host"
    ds_supported.port = 3306
    ds_supported.resource = "db"
    ds_supported.login = "user"
    ds_supported.password = "pass"
    ds_supported.parameters = {}

    ds_unsupported = MagicMock()
    ds_unsupported.name = "web-ds"
    ds_unsupported.driver = "web"

    mock_ds_svc = AsyncMock()
    mock_ds_svc.get.side_effect = lambda id: ds_supported if id == 1 else ds_unsupported

    model = TrinoPlatform(
        name="trino-test",
        project_id=1,
        data_source_ids=[1, 2],
    )

    with patch("mindweaver.platform_service.trino.service.DataSourceService.get_service", AsyncMock(return_value=mock_ds_svc)):
        vars = await svc.template_vars(model)

        # Verify only mysql-ds is in catalogs
        catalog_names = [c["catalog"] for c in vars["catalogs"]]
        assert "mysql-ds" in catalog_names
        assert "web-ds" not in catalog_names

        manifest = await svc.render_manifests(model)
        assert "mysql-ds" in manifest
        assert "web-ds" not in manifest
