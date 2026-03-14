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
    assert model.cpu_request == 0.5
    assert model.cpu_limit == 2.0
    assert model.mem_request == 2.0
    assert model.mem_limit == 4.0
    assert model.keda_enabled is True
    assert model.keda_min_replicas == 1
    assert model.keda_max_replicas == 10
    assert model.data_source_ids == []
    assert model.hms_ids == []
    assert model.hms_iceberg_ids == []


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
            }
        )
    assert "CPU request cannot be greater than CPU limit" in str(excinfo.value)

    # Invalid KEDA: min > max
    with pytest.raises(ValidationError) as excinfo:
        TrinoPlatform.model_validate(
            {
                "name": "test-trino",
                "title": "Test Trino",
                "project_id": 1,
                "keda_enabled": True,
                "keda_min_replicas": 5,
                "keda_max_replicas": 2,
            }
        )
    assert "KEDA minimum replicas cannot be greater than maximum replicas" in str(excinfo.value)


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
        hms_iceberg_ids=[10],
        data_source_ids=[20],
        keda_enabled=True,
        keda_min_replicas=2,
        keda_max_replicas=5,
    )

    # Mock _resolve_namespace
    svc._resolve_namespace = AsyncMock(return_value="trino-ns")

    # Mock HiveMetastorePlatformService
    mock_hms_svc = AsyncMock()
    mock_hms_model = MagicMock()
    mock_hms_model.name = "test-hms"
    mock_hms_model.iceberg_enabled = True
    mock_hms_model.iceberg_port = 9001
    mock_hms_model.s3_storage_id = 100
    mock_hms_svc.get.return_value = mock_hms_model
    mock_hms_svc._resolve_namespace.return_value = "hms-ns"

    # Mock S3StorageService
    mock_s3_svc = AsyncMock()
    mock_s3_model = MagicMock()
    mock_s3_model.endpoint_url = "http://minio:9000"
    mock_s3_model.access_key = "access"
    mock_s3_model.secret_key = "secret"
    mock_s3_svc.get.return_value = mock_s3_model
    
    mock_hms_state = MagicMock()
    mock_hms_state.active = True
    mock_hms_state.hms_uri = "thrift://hms-internal:9083"
    mock_hms_state.iceberg_uri = "http://iceberg-internal:9001"
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
    
    # Check HMS catalog
    hms_cat = next(c for c in vars["catalogs"] if c["catalog"] == "test-hms")
    assert hms_cat["properties"]["connector.name"] == "hive"
    assert hms_cat["properties"]["hive.metastore.uri"] == "thrift://hms-internal:9083"
    assert hms_cat["properties"]["hive.s3.endpoint"] == "http://minio:9000"
    assert hms_cat["properties"]["hive.s3.aws-access-key"] == "access"
    assert hms_cat["properties"]["hive.s3.aws-secret-key"] == "secret"
    assert hms_cat["properties"]["hive.s3.path-style-access"] == "true"

    # Check HMS Iceberg catalog
    iceberg_cat = next(c for c in vars["catalogs"] if c["catalog"] == "test-hms-iceberg")
    assert iceberg_cat["properties"]["connector.name"] == "iceberg"
    assert iceberg_cat["properties"]["hive.metastore.uri"] == "thrift://hms-internal:9083"
    assert iceberg_cat["properties"]["iceberg.s3.endpoint"] == "http://minio:9000"
    assert iceberg_cat["properties"]["iceberg.s3.aws-access-key"] == "access"
    assert iceberg_cat["properties"]["iceberg.s3.aws-secret-key"] == "secret"
    assert iceberg_cat["properties"]["iceberg.s3.path-style-access"] == "true"

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
    
    assert values["server"]["keda"]["enabled"] is True
    assert values["server"]["keda"]["minReplicas"] == 2
    assert values["server"]["keda"]["maxReplicas"] == 5
    
    assert "test-hms" in values["catalogs"]
    assert "test-hms-iceberg" in values["catalogs"]
    assert "mypsql" in values["catalogs"]
    
    hive_props = yaml.safe_load(values["catalogs"]["test-hms"].replace("\n", "\n  "))
    assert hive_props is None or isinstance(hive_props, str) or isinstance(hive_props, dict) 
    assert "connector.name=hive" in values["catalogs"]["test-hms"]
    assert "hive.metastore.uri=thrift://hms-internal:9083" in values["catalogs"]["test-hms"]

    iceberg_props = yaml.safe_load(values["catalogs"]["test-hms-iceberg"].replace("\n", "\n  "))
    assert iceberg_props is None or isinstance(iceberg_props, str) or isinstance(iceberg_props, dict) 
    assert "connector.name=iceberg" in values["catalogs"]["test-hms-iceberg"]
    assert "hive.metastore.uri=thrift://hms-internal:9083" in values["catalogs"]["test-hms-iceberg"]

    assert "jdbc:postgresql://postgres-host:5432/mydb" in values["catalogs"]["mypsql"]
