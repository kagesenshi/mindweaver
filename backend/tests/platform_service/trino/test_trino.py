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


@pytest.fixture
def mock_service_dependencies():
    request = MagicMock(spec=Request)
    session = MagicMock(spec=Session)
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
    assert model.hms_id is None


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
        hms_id=10,
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
    mock_hms_svc.get.return_value = mock_hms_model
    mock_hms_svc._resolve_namespace.return_value = "hms-ns"
    
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

    with patch("mindweaver.platform_service.trino.service.HiveMetastorePlatformService.get_service", AsyncMock(return_value=mock_hms_svc)), \
         patch("mindweaver.platform_service.trino.service.DataSourceService.get_service", AsyncMock(return_value=mock_ds_svc)):
        
        vars = await svc.template_vars(model)

    assert vars["hms_uri"] == "thrift://hms-internal:9083"
    assert vars["iceberg_uri"] == "http://iceberg-internal:9001"
    assert len(vars["catalogs"]) == 1
    cat = vars["catalogs"][0]
    assert cat["catalog"] == "mypsql"
    assert cat["properties"]["connector.name"] == "postgresql"
    assert "jdbc:postgresql://postgres-host:5432/mydb" in cat["properties"]["connection-url"]
    assert cat["properties"]["connection-user"] == "usr"
    assert cat["properties"]["connection-password"] == "pass"

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
    
    assert "hive" in values["catalogs"]
    assert "mypsql" in values["catalogs"]
    
    hive_props = yaml.safe_load(values["catalogs"]["hive"].replace("\n", "\n  "))
    assert hive_props is None or isinstance(hive_props, str) or isinstance(hive_props, dict) 
    # Because it is a multiline string in values.yaml, PyYAML will just load the string containing properties of the catalog.
    assert "connector.name=hive" in values["catalogs"]["hive"]
    assert "hive.metastore.uri=thrift://hms-internal:9083" in values["catalogs"]["hive"]

    assert "jdbc:postgresql://postgres-host:5432/mydb" in values["catalogs"]["mypsql"]
