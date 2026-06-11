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
    session.flush = AsyncMock()
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
    assert model.oidc_enabled is False
    assert model.oidc_client_secret is not None
    assert model.sqllab_enabled is True


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
            SupersetRoleMapping(entity="user@mindweaver.io", role="Gamma"),
            SupersetRoleMapping(entity="user@mindweaver.io", role="sql_lab")
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
        mock_project.ingress_domain = None
        mock_project.name = "myproject"
        svc.project = AsyncMock(return_value=mock_project)

        vars = await svc.template_vars(model)
        manifest = await svc.render_manifests(model)

        assert vars["db_pass"] == "pass"
        assert vars["ldap"]["server_url"] == "ldap://ldap:389"
        assert vars["auth_role_mapping"]["admin@mindweaver.io"] == ["Admin", "Alpha"]
        assert vars["auth_role_mapping"]["user@mindweaver.io"] == ["Gamma", "sql_lab"]
        assert len(vars["datasources"]) == 2
        
        ds_pg = next(ds for ds in vars["datasources"] if ds["database_name"] == "mypsql")
        assert "postgresql+asyncpg://usr:pass@pg-host:5432/mydb" in ds_pg["sqlalchemy_uri"]

        ds_trino = next(ds for ds in vars["datasources"] if ds["database_name"] == "mytrino")
        assert "trino://admin@mytrino.trino-ns.svc.cluster.local:8443" in ds_trino["sqlalchemy_uri"]

        # Verify rendered manifests (Application and Certificate)
        docs = [d for d in yaml.safe_load_all(manifest) if d is not None]
        assert len(docs) == 2
        
        app_doc = next(d for d in docs if d["kind"] == "Application")
        cert_doc = next(d for d in docs if d["kind"] == "Certificate")
        assert cert_doc["metadata"]["name"] == "superset-test-tls"
        assert cert_doc["spec"]["secretName"] == "superset-test-tls"
        assert cert_doc["spec"]["commonName"] == "superset-test.superset-ns.svc.cluster.local"
        
        # 1. Verify Application
        values = yaml.safe_load(app_doc["spec"]["source"]["helm"]["values"])
        assert values["extraEnv"]["REQUESTS_CA_BUNDLE"] == "/etc/ssl/certs/mindweaver-ca.crt"
        assert values["extraEnv"]["SSL_CERT_FILE"] == "/etc/ssl/certs/mindweaver-ca.crt"
        assert values["extraVolumes"][0]["secret"]["secretName"] == "superset-test-tls"
        # Check items in volume
        items = values["extraVolumes"][0]["secret"]["items"]
        assert any(i["key"] == "tls.crt" and i["path"] == "tls.crt" for i in items)
        assert any(i["key"] == "tls.key" and i["path"] == "tls.key" for i in items)
        
        # Check volume mounts
        mounts = [m["mountPath"] for m in values["extraVolumeMounts"]]
        assert "/etc/ssl/certs/mindweaver-ca.crt" in mounts
        assert "/etc/superset/trino-certs/tls.crt" in mounts
        assert "/etc/superset/trino-certs/tls.key" in mounts
        assert values["supersetNode"]["connections"]["db_type"] == "postgresql+asyncpg"
        
        # Verify initscript database auto-cleanup exists in rendered helm values
        assert "initscript" in values["init"]
        assert "superset db upgrade" in values["init"]["initscript"]
        assert "superset import_datasources" in values["init"]["initscript"]
        assert "Cleaning up removed datasources..." in values["init"]["initscript"]
        assert "create_app()" in values["init"]["initscript"]
        assert "app.app_context()" in values["init"]["initscript"]
        assert "db.session.delete" in values["init"]["initscript"]
        assert values["supersetNode"]["connections"]["db_host"] == "my-db-pooler-rw.superset-ns.svc.cluster.local"
        assert values["service"]["type"] == "NodePort"
        assert values["service"]["port"] == 8088
        assert "AUTH_LDAP" in values["configOverrides"]["ldap"]
        assert values["image"]["repository"] == "ghcr.io/kagesenshi/mindweaver/superset"
        assert values["redis"]["image"]["repository"] == "bitnamilegacy/redis"
        assert "AUTH_ROLES_MAPPING" in values["configOverrides"]["role_mapping"]
        assert '"admin@mindweaver.io": ["Admin", "Alpha"]' in values["configOverrides"]["role_mapping"]
        assert '"user@mindweaver.io": ["Gamma", "sql_lab"]' in values["configOverrides"]["role_mapping"]
        
        # 1.1 Verify with override_image = True
        model.override_image = True
        model.image = "my-registry/superset:v1.2.3"
        vars_override = await svc.template_vars(model)
        manifest_override = await svc.render_manifests(model)
        docs_override = [d for d in yaml.safe_load_all(manifest_override) if d is not None]
        app_doc_override = next(d for d in docs_override if d["kind"] == "Application")
        values_override = yaml.safe_load(app_doc_override["spec"]["source"]["helm"]["values"])
        
        assert values_override["image"]["repository"] == "my-registry/superset"
        assert values_override["image"]["tag"] == "v1.2.3"
        
        assert values_override["image"]["tag"] == "v1.2.3"

        # 1.2 Verify with ingress_domain set
        mock_project.ingress_domain = "132.home.kagesenshi.org"
        vars_ingress = await svc.template_vars(model)
        manifest_ingress = await svc.render_manifests(model)
        docs_ingress = [d for d in yaml.safe_load_all(manifest_ingress) if d is not None]
        # Now there should be 3 docs: Application, HTTPRoute, and Certificate
        assert len(docs_ingress) == 3
        route_doc = next(d for d in docs_ingress if d["kind"] == "HTTPRoute")
        assert route_doc["metadata"]["name"] == "superset-test-route"
        assert route_doc["spec"]["hostnames"] == ["superset-test.132.home.kagesenshi.org"]
        assert route_doc["spec"]["rules"][0]["backendRefs"][0]["name"] == "superset-test"
        assert route_doc["spec"]["rules"][0]["backendRefs"][0]["port"] == 8088

        # 1.3 Verify with oidc_enabled = True
        model.oidc_enabled = True
        model.oidc_client_secret = "test-oidc-secret"
        vars_oidc = await svc.template_vars(model)
        manifest_oidc = await svc.render_manifests(model)
        docs_oidc = [d for d in yaml.safe_load_all(manifest_oidc) if d is not None]
        app_doc_oidc = next(d for d in docs_oidc if d["kind"] == "Application")
        values_oidc = yaml.safe_load(app_doc_oidc["spec"]["source"]["helm"]["values"])
        
        assert "AUTH_OAUTH" in values_oidc["configOverrides"]["oidc"]
        assert "OAUTH_PROVIDERS" in values_oidc["configOverrides"]["oidc"]
        assert "CustomSecurityManager" in values_oidc["configOverrides"]["oidc"]
        assert "https://dex.132.home.kagesenshi.org/dex/auth" in values_oidc["configOverrides"]["oidc"]
        assert "http://dex.superset-ns.svc.cluster.local:5556/dex/token" in values_oidc["configOverrides"]["oidc"]
        assert "ENABLE_PROXY_FIX = True" in values_oidc["configOverrides"]["oidc"]
        assert "import trino.auth" in values_oidc["configOverrides"]["oidc"]
        assert "ALLOWED_EXTRA_AUTHENTICATIONS" in values_oidc["configOverrides"]["oidc"]
        # sql_lab role auto-assignment should be rendered because sqllab_enabled is True by default
        assert 'self.find_role("sql_lab")' in values_oidc["configOverrides"]["oidc"]

        # 1.4 Verify behavior when sqllab_enabled = False
        model.sqllab_enabled = False
        vars_no_sqllab = await svc.template_vars(model)
        assert "sql_lab" not in vars_no_sqllab["auth_role_mapping"]["user@mindweaver.io"]

        manifest_no_sqllab = await svc.render_manifests(model)
        docs_no_sqllab = [d for d in yaml.safe_load_all(manifest_no_sqllab) if d is not None]
        app_doc_no_sqllab = next(d for d in docs_no_sqllab if d["kind"] == "Application")
        values_no_sqllab = yaml.safe_load(app_doc_no_sqllab["spec"]["source"]["helm"]["values"])
        assert 'self.find_role("sql_lab")' not in values_no_sqllab["configOverrides"]["oidc"]

        # Verify Trino datasource has extra connecting args when OIDC is enabled
        assert "import_datasources.yaml" in values_oidc["extraConfigs"]
        datasources_yaml = yaml.safe_load(values_oidc["extraConfigs"]["import_datasources.yaml"])
        trino_ds = next(ds for ds in datasources_yaml["databases"] if ds["database_name"] == "mytrino")
        assert trino_ds.get("impersonate_user") is True
        assert "extra" in trino_ds
        extra_data = yaml.safe_load(trino_ds["extra"])
        assert extra_data["engine_params"]["connect_args"]["http_scheme"] == "https"
        assert extra_data["engine_params"]["connect_args"]["verify"] == "/etc/ssl/certs/mindweaver-ca.crt"
        assert extra_data.get("allow_multi_catalog") is True
        
        assert "encrypted_extra" in trino_ds
        encrypted_extra_data = yaml.safe_load(trino_ds["encrypted_extra"])
        assert encrypted_extra_data["auth_method"] == "certificate"
        assert encrypted_extra_data["auth_params"]["cert"] == "/etc/superset/trino-certs/tls.crt"
        assert encrypted_extra_data["auth_params"]["key"] == "/etc/superset/trino-certs/tls.key"

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
            # Test without ingress_domain
            mock_project_no_ingress = MagicMock()
            mock_project_no_ingress.ingress_domain = None
            svc.project = AsyncMock(return_value=mock_project_no_ingress)

            await svc.poll_status(model)
            
            assert mock_state.superset_uri == "http://1.2.3.4:30001"
            assert mock_state.superset_uri_ipv6 == "http://[2001:db8::1]:30001"
            assert mock_state.admin_user == "admin"
            assert mock_state.admin_password is not None

            # Test with ingress_domain
            mock_project_ingress = MagicMock()
            mock_project_ingress.ingress_domain = "132.home.kagesenshi.org"
            svc.project = AsyncMock(return_value=mock_project_ingress)

            await svc.poll_status(model)
            assert mock_state.superset_uri == "https://superset-test.132.home.kagesenshi.org"
            assert mock_state.superset_uri_ipv6 is None
            assert mock_state.extra_data["ingress_domain"] == "132.home.kagesenshi.org"


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
