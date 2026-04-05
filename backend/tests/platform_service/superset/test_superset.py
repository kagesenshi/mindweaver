# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
import yaml
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import Request
from pydantic import ValidationError

from mindweaver.platform_service.superset.model import SupersetPlatform, SupersetPlatformState, SupersetRoleMapping
from mindweaver.platform_service.superset.service import SupersetPlatformService
from mindweaver.platform_service.pgsql import PgSqlPlatformState
from mindweaver.fw.model import AsyncSession
from mindweaver.service.ldap_config.model import LdapConfig


@pytest.fixture
def mock_service_dependencies():
    request = MagicMock(spec=Request)
    session = MagicMock(spec=AsyncSession)
    session.exec = AsyncMock()
    return request, session


def test_superset_resource_defaults():
    """Test default values for Superset resource limits"""
    model = SupersetPlatform(name="test-superset", title="Test Superset", project_id=1, platform_pgsql_id=1)
    # The defaults are 0.5/2.0 CPU and 2.0/4.0 Memory
    assert model.cpu_request == 0.5
    assert model.cpu_limit == 2.0
    assert model.mem_request == 2.0
    assert model.mem_limit == 4.0
    assert model.chart_version == "0.15.0"
    assert model.override_image is False
    assert model.image == "ghcr.io/kagesenshi/mindweaver/superset:latest"


def test_superset_validation():
    """Test validation logic for Superset"""
    # Valid case
    model = SupersetPlatform.model_validate(
        {
            "name": "test-superset",
            "title": "Test Superset",
            "project_id": 1,
            "platform_pgsql_id": 1,
            "cpu_request": 0.5,
            "cpu_limit": 1.0,
        }
    )
    assert model.cpu_request == 0.5

    # Invalid CPU: request > limit
    with pytest.raises(ValidationError) as excinfo:
        SupersetPlatform.model_validate(
            {
                "name": "test-superset",
                "title": "Test Superset",
                "project_id": 1,
                "platform_pgsql_id": 1,
                "cpu_request": 2.0,
                "cpu_limit": 1.0,
            }
        )
    assert "CPU request cannot be greater than CPU limit" in str(excinfo.value)


def test_superset_auth_role_mapping_validation():
    """Test validation for auth_role_mapping"""
    from mindweaver.platform_service.superset.model import SupersetRoleMapping
    # Valid role
    model = SupersetPlatform(
        name="test-superset",
        title="Test Superset",
        project_id=1,
        platform_pgsql_id=1,
        auth_role_mapping=[SupersetRoleMapping(entity="user1", role="Admin")]
    )
    assert model.auth_role_mapping[0]["role"] == "Admin"

    # Invalid role
    with pytest.raises(ValidationError) as excinfo:
        SupersetRoleMapping(entity="user1", role="InvalidRole")
    assert "Invalid role: InvalidRole" in str(excinfo.value)


def test_superset_auth_role_mapping_dict_assignment():
    """Test that dictionary assignment is converted to SupersetRoleMapping objects"""
    from mindweaver.platform_service.superset.model import SupersetRoleMapping
    model = SupersetPlatform(
        name="test-superset",
        title="Test Superset",
        project_id=1,
        platform_pgsql_id=1
    )
    # Assignment as dict list
    model.auth_role_mapping = [{"entity": "user1", "role": "Admin"}]
    # Should be validated but kept as dict for serialization
    assert isinstance(model.auth_role_mapping[0], dict)
    assert model.auth_role_mapping[0]["entity"] == "user1"


@pytest.mark.asyncio
async def test_superset_template_rendering(mock_service_dependencies):
    """Test that the Superset templates render correctly with dependencies"""
    request, session = mock_service_dependencies
    svc = SupersetPlatformService(request, session)

    # Note: Import here to ensure we patch the class used in service.py
    from mindweaver.platform_service.superset.service import (
        PgSqlPlatformService,
        LdapConfigService,
        DatabaseSourceService,
        TrinoPlatformService
    )

    model = SupersetPlatform(
        name="superset-test",
        title="Superset Test",
        project_id=1,
        platform_pgsql_id=10,
        database_source_ids=[20],
        trino_ids=[30],
        auth_role_mapping=[
            SupersetRoleMapping(entity="admin@mindweaver.io", role="Admin"),
            SupersetRoleMapping(entity="admin@mindweaver.io", role="Alpha"),
            SupersetRoleMapping(entity="user@mindweaver.io", role="Gamma")
        ]
    )

    # Mock _resolve_namespace
    svc._resolve_namespace = AsyncMock(return_value="superset-ns")

    # Mock PgSqlPlatformService
    mock_pgsql_svc = MagicMock(spec=PgSqlPlatformService)
    mock_pgsql_model = MagicMock()
    mock_pgsql_model.name = "my-db"
    mock_pgsql_model.id = 10
    mock_pgsql_svc.get = AsyncMock(return_value=mock_pgsql_model)
    
    # Mock PgSqlPlatformState
    mock_pgsql_state = MagicMock()
    mock_pgsql_state.active = True
    mock_pgsql_state.db_user = "app"
    mock_pgsql_state.db_pass = "pass"
    mock_pgsql_state.db_name = "app"
    mock_pgsql_state.extra_data = {"pgbouncer_host": "my-db-pooler-rw.superset-ns.svc.cluster.local"}
    mock_pgsql_svc.platform_state = AsyncMock(return_value=mock_pgsql_state)
    mock_pgsql_svc._resolve_namespace = AsyncMock(return_value="superset-ns")

    # Mock LdapConfigService
    mock_ldap_svc = MagicMock(spec=LdapConfigService)
    mock_ldap_config = LdapConfig(
        id=5,
        name="test-ldap",
        server_url="ldap://ldap:389",
        user_search_base="ou=users,dc=world",
        user_search_filter="(uid={0})",
        bind_dn="cn=admin,dc=world",
        bind_password="ldap-pass",
        username_attr="uid"
    )
    mock_ldap_svc.get = AsyncMock(return_value=mock_ldap_config)

    # Mock DatabaseSourceService
    mock_ds_svc = MagicMock(spec=DatabaseSourceService)
    mock_ds_model = MagicMock()
    mock_ds_model.name = "mypsql"
    mock_ds_model.engine = "postgresql"
    mock_ds_model.host = "pg-host"
    mock_ds_model.port = 5432
    mock_ds_model.database = "mydb"
    mock_ds_model.login = "usr"
    mock_ds_model.password = "pass"
    mock_ds_model.parameters = {}
    mock_ds_svc.get = AsyncMock(return_value=mock_ds_model)

    # Mock TrinoPlatformService
    mock_trino_svc = MagicMock(spec=TrinoPlatformService)
    mock_trino_model = MagicMock()
    mock_trino_model.name = "mytrino"
    mock_trino_svc.get = AsyncMock(return_value=mock_trino_model)
    mock_trino_state = MagicMock()
    mock_trino_state.active = True
    mock_trino_state.extra_data = {"namespace": "trino-ns"}
    mock_trino_svc.platform_state = AsyncMock(return_value=mock_trino_state)
    mock_trino_svc._resolve_namespace = AsyncMock(return_value="trino-ns")

    with patch("mindweaver.platform_service.superset.service.PgSqlPlatformService") as mock_pg_class, \
         patch("mindweaver.platform_service.superset.service.LdapConfigService") as mock_ldap_class, \
         patch("mindweaver.platform_service.superset.service.DatabaseSourceService") as mock_ds_class, \
         patch("mindweaver.platform_service.superset.service.TrinoPlatformService") as mock_trino_class, \
         patch("mindweaver.platform_service.superset.service.decrypt_password", side_effect=lambda x: x):
        
        mock_pg_class.get_service = AsyncMock(return_value=mock_pgsql_svc)
        mock_ldap_class.get_service = AsyncMock(return_value=mock_ldap_svc)
        mock_ds_class.get_service = AsyncMock(return_value=mock_ds_svc)
        mock_trino_class.get_service = AsyncMock(return_value=mock_trino_svc)
        
        # Mock project relationship
        mock_project = MagicMock()
        mock_project.ldap_config_id = 5
        svc.project = AsyncMock(return_value=mock_project)

        vars = await svc.template_vars(model)
        manifest = await svc.render_manifests(model)

        assert vars["db_pass"] == "pass"
        assert vars["ldap"]["server_url"] == "ldap://ldap:389"
        assert vars["auth_role_mapping"]["admin@mindweaver.io"] == ["Admin", "Alpha"]
        assert vars["auth_role_mapping"]["user@mindweaver.io"] == ["Gamma"]
        assert len(vars["datasources"]) == 2
        
        ds_pg = next(ds for ds in vars["datasources"] if ds["database_name"] == "mypsql")
        assert "postgresql+asyncpg://usr:pass@pg-host:5432/mydb" in ds_pg["sqlalchemy_uri"]

        ds_trino = next(ds for ds in vars["datasources"] if ds["database_name"] == "mytrino")
        assert "trino://admin@mytrino.trino-ns.svc.cluster.local:8443" in ds_trino["sqlalchemy_uri"]

        # Verify rendered manifests (Application)
        docs = list(yaml.safe_load_all(manifest))
        assert len(docs) == 1
        
        app_doc = docs[0]
        assert app_doc["kind"] == "Application"
        
        # 1. Verify Application
        values = yaml.safe_load(app_doc["spec"]["source"]["helm"]["values"])
        assert values["supersetNode"]["connections"]["db_type"] == "postgresql+asyncpg"
        assert values["supersetNode"]["connections"]["db_host"] == "my-db-pooler-rw.superset-ns.svc.cluster.local"
        assert values["service"]["type"] == "NodePort"
        assert values["service"]["port"] == 8088
        assert "AUTH_LDAP" in values["configOverrides"]["ldap"]
        assert values["image"]["repository"] == "ghcr.io/kagesenshi/mindweaver/superset"
        assert values["image"]["tag"] == "5.0.0-rev.3"
        assert values["redis"]["image"]["repository"] == "bitnamilegacy/redis"
        assert "AUTH_ROLES_MAPPING" in values["configOverrides"]["role_mapping"]
        assert '"admin@mindweaver.io": ["Admin", "Alpha"]' in values["configOverrides"]["role_mapping"]
        assert '"user@mindweaver.io": ["Gamma"]' in values["configOverrides"]["role_mapping"]
        
        # 1.1 Verify with override_image = True
        model.override_image = True
        model.image = "my-registry/superset:v1.2.3"
        vars_override = await svc.template_vars(model)
        manifest_override = await svc.render_manifests(model)
        docs_override = list(yaml.safe_load_all(manifest_override))
        app_doc_override = next(d for d in docs_override if d["kind"] == "Application")
        values_override = yaml.safe_load(app_doc_override["spec"]["source"]["helm"]["values"])
        
        assert values_override["image"]["repository"] == "my-registry/superset"
        assert values_override["image"]["tag"] == "v1.2.3"
        
        assert values_override["image"]["tag"] == "v1.2.3"

    # 3. Verify dual-stack URI derivation in poll_status
    # We need a new mock for this as it's a separate concern from template rendering
    mock_state = MagicMock(spec=SupersetPlatformState)
    mock_state.active = True
    
    with patch("mindweaver.platform_service.superset.service.PgSqlPlatformService"), \
         patch("mindweaver.platform_service.superset.service.LdapConfigService"), \
         patch("mindweaver.platform_service.superset.service.DatabaseSourceService"), \
         patch("mindweaver.platform_service.superset.service.TrinoPlatformService"), \
         patch.object(svc, "platform_state", AsyncMock(return_value=mock_state)), \
         patch.object(svc, "kubeconfig", AsyncMock(return_value="mock-kubeconfig")), \
         patch.object(svc, "_resolve_namespace", AsyncMock(return_value="superset-ns")):
        
        # Dual stack cluster nodes
        cluster_nodes_dual = [
            {"hostname": "node1", "ipv4": "1.2.3.4", "ipv6": None},
            {"hostname": "node2", "ipv4": None, "ipv6": "2001:db8::1"}
        ]
        node_ports = [{"name": "superset-test", "port": 8088, "node_port": 30001}]
        
        async def mock_poll(*args):
            return "online", "Healthy", {}, node_ports, cluster_nodes_dual
            
        with patch("mindweaver.platform_service.superset.service.asyncio.to_thread", side_effect=mock_poll), \
             patch("mindweaver.platform_service.superset.service.decrypt_password", side_effect=lambda x: x):
            await svc.poll_status(model)
            
            assert mock_state.superset_uri == "http://1.2.3.4:30001"
            assert mock_state.superset_uri_ipv6 == "http://[2001:db8::1]:30001"
            assert mock_state.admin_user == "admin"
            assert mock_state.admin_password is not None


@pytest.mark.asyncio
async def test_superset_redaction(mock_service_dependencies):
    """Test that sensitive fields are redacted and hidden"""
    request, session = mock_service_dependencies
    svc = SupersetPlatformService(request, session)
    
    # 1. Check internal_fields (hidden from form)
    assert "admin_password" in svc.internal_fields()
    assert "superset_secret_key" in svc.internal_fields()
    
    # 2. Check redacted_fields
    assert "admin_password" in svc.redacted_fields()
    assert "superset_secret_key" in svc.redacted_fields()
    
    # 3. Test post_process_model (API redaction)
    model = SupersetPlatform(
        name="test-redact",
        title="Test Redact",
        project_id=1,
        platform_pgsql_id=1,
        admin_password="secret_pass",
        superset_secret_key="secret_key"
    )
    
    redacted_model = await svc.post_process_model(model)
    assert redacted_model.admin_password == "__REDACTED__"
    assert redacted_model.superset_secret_key == "__REDACTED__"
    assert redacted_model.name == "test-redact"


@pytest.mark.asyncio
async def test_superset_state_view(mock_service_dependencies):
    """Test that the _state view works correctly"""
    request, session = mock_service_dependencies
    svc = SupersetPlatformService(request, session)
    
    model = SupersetPlatform(
        id=1,
        name="test-state",
        title="Test State",
        project_id=1,
        platform_pgsql_id=1
    )
    
    # Mock the state in DB
    from mindweaver.platform_service.superset.model import SupersetPlatformState
    mock_state_db = SupersetPlatformState(
        platform_id=1,
        status="online",
        active=True,
        extra_data={"namespace": "test-ns"}
    )
    
    # Mock platform_state method
    svc.platform_state = AsyncMock(return_value=mock_state_db)
    
    # Test the handler initialization (mimicking register_views logic)
    # We need to ensure the correct class is used.
    from mindweaver.platform_service.superset import SupersetState
    
    state_instance = SupersetState(model, svc)
    state = await state_instance.get()
    
    assert state["status"] == "online"
    assert state["extra_data"]["namespace"] == "test-ns"
