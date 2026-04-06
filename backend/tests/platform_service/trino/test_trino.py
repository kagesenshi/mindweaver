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
    assert model.database_source_ids == []
    assert model.hms_ids == []
    assert model.hms_iceberg_ids == []

    # New fields
    assert model.chart_version == "1.41.0"
    assert model.override_image is False
    assert len(model.internal_shared_secret) == 64 # hex of 32 bytes


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
            "database_source_ids": [1],
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
                "database_source_ids": [],
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
        database_source_ids=[20],
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

    # Mock DatabaseSourceService
    mock_ds_svc = AsyncMock()
    mock_ds_model = MagicMock()
    mock_ds_model.name = "mypsql"
    mock_ds_model.engine = "postgresql"
    mock_ds_model.host = "postgres-host"
    mock_ds_model.port = 5432
    mock_ds_model.database = "mydb"
    mock_ds_model.login = "usr"
    mock_ds_model.password = "pass"
    mock_ds_model.parameters = {"param1": "val1"}
    mock_ds_svc.get.return_value = mock_ds_model

    # Mock session.exec for S3StorageService.get
    mock_result = MagicMock()
    mock_result.first.return_value = mock_s3_model
    session.exec.return_value = mock_result

    with patch("mindweaver.platform_service.trino.service.HiveMetastorePlatformService.get_service", AsyncMock(return_value=mock_hms_svc)), \
         patch("mindweaver.platform_service.trino.service.DatabaseSourceService.get_service", AsyncMock(return_value=mock_ds_svc)), \
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
         patch("mindweaver.platform_service.trino.service.DatabaseSourceService.get_service", AsyncMock(return_value=mock_ds_svc)):
        full_manifest = await svc.render_manifests(model)
        
    try:
        docs = list(yaml.safe_load_all(full_manifest))
        assert len(docs) >= 1
    except yaml.parser.ParserError as e:
        pytest.fail(f"YAML parsing failed: {e}")
        
    app_doc = next(d for d in docs if d["kind"] == "Application")
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
    # Verify the additional HTTPS NodePort service is present in the docs
    https_svc = next(d for d in docs if d["kind"] == "Service" and d["metadata"]["name"] == "trino-test-https-nodeport")
    assert https_svc["spec"]["type"] == "NodePort"
    assert https_svc["spec"]["ports"][0]["port"] == 8443


@pytest.mark.asyncio
async def test_trino_override_image_template(mock_service_dependencies):
    """Test that the image block is rendered only when override_image=True"""
    request, session = mock_service_dependencies
    svc = TrinoPlatformService(request, session)
    svc._resolve_namespace = AsyncMock(return_value="trino-ns")
    svc.project = AsyncMock(return_value=MagicMock(ldap_config_id=None))

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
    svc.project = AsyncMock(return_value=MagicMock(ldap_config_id=None))
    svc.project = AsyncMock(return_value=MagicMock(ldap_config_id=None))

    model = TrinoPlatform(
        name="trino-test",
        project_id=1,
        database_source_ids=[1],
    )

    with patch("mindweaver.platform_service.trino.service.DatabaseSourceService.get_service", AsyncMock(return_value=mock_ds_svc)):
        vars = await svc.template_vars(model)

        # Verify only mysql-ds is in catalogs
        catalog_names = [c["catalog"] for c in vars["catalogs"]]
        assert "mysql-ds" in catalog_names

        manifest = await svc.render_manifests(model)
        assert "mysql-ds" in manifest
        assert "web-ds" not in manifest


@pytest.mark.asyncio
async def test_trino_mssql_catalog_rendering(mock_service_dependencies):
    """Test that MSSQL engine is correctly mapped to sqlserver connector and URL"""
    request, session = mock_service_dependencies
    svc = TrinoPlatformService(request, session)
    svc._resolve_namespace = AsyncMock(return_value="trino-ns")
    svc.project = AsyncMock(return_value=MagicMock(ldap_config_id=None))

    # Mock MSSQL Data Source
    ds_mssql = MagicMock()
    ds_mssql.name = "mymssql"
    ds_mssql.engine = "mssql"
    ds_mssql.host = "mssql-host"
    ds_mssql.port = 1433
    ds_mssql.database = "mydb"
    ds_mssql.login = "sa"
    ds_mssql.password = "pass"
    ds_mssql.enable_ssl = False
    ds_mssql.verify_ssl = False
    ds_mssql.parameters = {}

    mock_ds_svc = AsyncMock()
    mock_ds_svc.get.return_value = ds_mssql

    model = TrinoPlatform(
        name="trino-test",
        project_id=1,
        database_source_ids=[1],
    )

    with patch("mindweaver.platform_service.trino.service.DatabaseSourceService.get_service", AsyncMock(return_value=mock_ds_svc)), \
         patch("mindweaver.platform_service.trino.service.decrypt_password", lambda x: x):
        vars = await svc.template_vars(model)

    # Verify mssql-ds is mapped correctly
    mssql_cat = next(c for c in vars["catalogs"] if c["catalog"] == "mymssql")
    assert mssql_cat["properties"]["connector.name"] == "sqlserver"
    # Defaults: enable_ssl=False, verify_ssl=False -> encrypt=false, trustServerCertificate=true
    assert "encrypt=false" in mssql_cat["properties"]["connection-url"]
    assert "trustServerCertificate=true" in mssql_cat["properties"]["connection-url"]
    assert mssql_cat["properties"]["connection-url"] == "jdbc:sqlserver://mssql-host:1433;databaseName=mydb;encrypt=false;trustServerCertificate=true"
    assert mssql_cat["properties"]["connection-user"] == "sa"
    assert mssql_cat["properties"]["connection-password"] == "pass"


@pytest.mark.asyncio
async def test_trino_mssql_ssl_rendering(mock_service_dependencies):
    """Test that MSSQL SSL parameters are correctly mapped"""
    request, session = mock_service_dependencies
    svc = TrinoPlatformService(request, session)
    svc._resolve_namespace = AsyncMock(return_value="trino-ns")
    svc.project = AsyncMock(return_value=MagicMock(ldap_config_id=None))

    # Mock MSSQL Data Source with SSL enabled and verification enabled
    ds_mssql = MagicMock()
    ds_mssql.name = "ssl-mssql"
    ds_mssql.engine = "mssql"
    ds_mssql.host = "mssql-ssl-host"
    ds_mssql.port = 1433
    ds_mssql.database = "mydb"
    ds_mssql.login = "sa"
    ds_mssql.password = "pass"
    ds_mssql.enable_ssl = True
    ds_mssql.verify_ssl = True
    ds_mssql.parameters = {}

    mock_ds_svc = AsyncMock()
    mock_ds_svc.get.return_value = ds_mssql

    model = TrinoPlatform(
        name="trino-test",
        project_id=1,
        database_source_ids=[1],
    )

    with patch("mindweaver.platform_service.trino.service.DatabaseSourceService.get_service", AsyncMock(return_value=mock_ds_svc)), \
         patch("mindweaver.platform_service.trino.service.decrypt_password", lambda x: x):
        vars = await svc.template_vars(model)

    mssql_cat = next(c for c in vars["catalogs"] if c["catalog"] == "ssl-mssql")
    # enable_ssl=True, verify_ssl=True -> encrypt=true, trustServerCertificate=false
    assert "encrypt=true" in mssql_cat["properties"]["connection-url"]
    assert "trustServerCertificate=false" in mssql_cat["properties"]["connection-url"]


from mindweaver.datasource_service.database_source import DatabaseSourceService
from mindweaver.service.ldap_config.model import LdapConfig


@pytest.mark.asyncio
async def test_trino_ldap_rendering(mock_service_dependencies):
    """Test that LDAP configuration is correctly rendered"""
    request, session = mock_service_dependencies
    svc = TrinoPlatformService(request, session)
    svc._resolve_namespace = AsyncMock(return_value="trino-ns")

    model = TrinoPlatform(
        name="trino-ldap-test",
        title="Trino LDAP Test",
        project_id=1,
        hms_ids=[10], # Needs at least one catalog
    )

    # Mock LDAP configuration
    mock_ldap_config = LdapConfig(
        id=5,
        name="test-ldap",
        server_url="ldap://ldap.example.com:389",
        user_search_base="ou=users,dc=example,dc=com",
        user_search_filter="(uid={0})",
        username_attr="uid",
        bind_dn="cn=admin,dc=example,dc=com",
        bind_password="encrypted_pass",
    )

    mock_ldap_svc = AsyncMock()
    mock_ldap_svc.get.return_value = mock_ldap_config

    # Mock HMS service to avoid failure in template_vars
    mock_hms_svc = AsyncMock()
    mock_hms_model = MagicMock()
    mock_hms_model.name = "test-hms"
    mock_hms_model.s3_storage_id = None
    mock_hms_svc.get.return_value = mock_hms_model
    mock_hms_state = MagicMock()
    mock_hms_state.active = True
    mock_hms_state.hms_uri = "thrift://hms:9083"
    mock_hms_svc.platform_state.return_value = mock_hms_state
    mock_hms_svc._resolve_namespace.return_value = "hms-ns"

    model.internal_shared_secret = "test-shared-secret"
    
    # Mock project relationship
    mock_project = MagicMock()
    mock_project.ldap_config_id = 5
    svc.project = AsyncMock(return_value=mock_project)

    with patch("mindweaver.platform_service.trino.service.LdapConfigService.get_service", AsyncMock(return_value=mock_ldap_svc)), \
         patch("mindweaver.platform_service.trino.service.HiveMetastorePlatformService.get_service", AsyncMock(return_value=mock_hms_svc)), \
         patch("mindweaver.platform_service.trino.service.decrypt_password", side_effect=lambda x: x):
        
        vars = await svc.template_vars(model)
        manifest = await svc.render_manifests(model)

    assert "ldap" in vars
    assert vars.get("internal_shared_secret") == "test-shared-secret"
    assert vars["ldap"]["ldap.url"] == "ldap://ldap.example.com:389"
    assert vars["ldap"]["ldap.bind-password"] == "encrypted_pass"
    assert vars["ldap"]["ldap.user-base-dn"] == "ou=users,dc=example,dc=com"
    assert vars["ldap"]["ldap.group-auth-pattern"] == "(uid=${USER})"

    assert "internal-communication.shared-secret=test-shared-secret" in manifest
    assert "authenticationType: PASSWORD" in manifest
    assert "additionalConfigFiles:" in manifest
    assert "password-authenticator.name=ldap" in manifest
    assert "ldap.url=ldap://ldap.example.com:389" in manifest
    assert "ldap.bind-dn=cn=admin,dc=example,dc=com" in manifest
    assert "ldap.bind-password=encrypted_pass" in manifest
    assert "ldap.user-base-dn=ou=users,dc=example,dc=com" in manifest
    assert "ldap.group-auth-pattern=(uid=${USER})" in manifest


@pytest.mark.asyncio
async def test_trino_https_rendering(mock_service_dependencies):
    """Test that HTTPS configuration is correctly rendered"""
    request, session = mock_service_dependencies
    svc = TrinoPlatformService(request, session)
    svc._resolve_namespace = AsyncMock(return_value="trino-ns")

    model = TrinoPlatform(
        name="trino-https-test",
        title="Trino HTTPS Test",
        project_id=1,
        hms_ids=[10], # Needs at least one catalog
    )
    model.internal_shared_secret = "test-shared-secret"

    # Mock HMS service to avoid failure in template_vars
    mock_hms_svc = AsyncMock()
    mock_hms_model = MagicMock()
    mock_hms_model.name = "test-hms"
    mock_hms_model.s3_storage_id = None
    mock_hms_svc.get.return_value = mock_hms_model
    mock_hms_state = MagicMock()
    mock_hms_state.active = True
    mock_hms_state.hms_uri = "thrift://hms:9083"
    mock_hms_svc.platform_state.return_value = mock_hms_state
    mock_hms_svc._resolve_namespace.return_value = "hms-ns"
    svc.project = AsyncMock(return_value=MagicMock(ldap_config_id=None))

    with patch("mindweaver.platform_service.trino.service.HiveMetastorePlatformService.get_service", AsyncMock(return_value=mock_hms_svc)), \
         patch("mindweaver.platform_service.trino.service.decrypt_password", lambda x: x):
        
        manifest = await svc.render_manifests(model)

    docs = list(yaml.safe_load_all(manifest))
    assert len(docs) >= 3  # Application + Certificate + NodePort Service

    # Ensure no local Issuer is created (it's cluster-wide now)
    issuer_kinds = [d["kind"] for d in docs]
    assert "Issuer" not in issuer_kinds
    assert "Secret" not in issuer_kinds  # no keystore-password secret anymore
    
    cert = next(d for d in docs if d["kind"] == "Certificate")
    assert cert["metadata"]["name"] == "trino-https-test-tls"
    assert cert["spec"]["issuerRef"]["name"] == "mindweaver-selfsigned-issuer"
    assert cert["spec"]["issuerRef"]["kind"] == "ClusterIssuer"
    assert "keystores" not in cert["spec"]  # PEM format - no JKS keystore

    # Check additional NodePort service
    service = next(d for d in docs if d["kind"] == "Service" and d["metadata"]["name"] == "trino-https-test-https-nodeport")
    assert service["spec"]["type"] == "NodePort"
    assert service["spec"]["ports"][0]["port"] == 8443
    assert service["spec"]["selector"]["app.kubernetes.io/component"] == "coordinator"

    # Check Application Helm values
    app = next(d for d in docs if d["kind"] == "Application")
    values = yaml.safe_load(app["spec"]["source"]["helm"]["values"])
    
    props = values["additionalConfigProperties"]
    assert "http-server.https.enabled=true" in props
    assert "http-server.https.port=8443" in props
    assert "http-server.https.keystore.path=/etc/trino/tls/tls.pem" in props
    # No keystore.password needed for PEM format
    assert not any("keystore.password" in p for p in props)

    # Verify additionalExposedPorts
    assert "https" in values["coordinator"]["additionalExposedPorts"]
    assert values["coordinator"]["additionalExposedPorts"]["https"]["port"] == 8443

    # Verify initContainer on coordinator and worker combine tls.key + tls.crt
    for role in ["coordinator", "worker"]:
        init_containers = values["initContainers"][role]
        assert len(init_containers) == 1
        assert "tls.pem" in init_containers[0]["command"][2]

        # tls-secret volume (from cert-manager) and certs emptyDir
        volume_names = [v["name"] for v in values[role]["additionalVolumes"]]
        assert "tls-secret" in volume_names
        assert "certs" in volume_names

        # mount the combined certs dir
        assert values[role]["additionalVolumeMounts"][0]["mountPath"] == "/etc/trino/tls"


@pytest.mark.asyncio
async def test_trino_poll_status_with_https_nodeport(mock_service_dependencies):
    """Test that poll_status picks the correct NodePort for the HTTPS service"""
    request, session = mock_service_dependencies
    svc = TrinoPlatformService(request, session)

    # Mock base methods to avoid hitting real logic or requiring complex mocks
    svc._resolve_namespace = AsyncMock(return_value="trino-ns")
    svc.kubeconfig = AsyncMock(return_value="dummy-kubeconfig")
    svc.platform_state = AsyncMock(return_value=MagicMock(active=True))

    model = TrinoPlatform(
        id=1,
        name="trino",
        title="Trino",
        project_id=1,
        hms_ids=[10],
    )

    # Mock environment
    node_ports = [
        {"name": "trino", "port": 8080, "node_port": 30080}, # Default HTTP NodePort
        {"name": "trino-https-nodeport", "port": 8443, "node_port": 30443}, # The one we want
    ]
    cluster_nodes = [{"hostname": "node1", "ipv4": "1.2.3.4"}]

    # Mock template_vars and get_preferred_catalog to avoid heavy lifting
    svc.get_preferred_catalog = AsyncMock(return_value="hive")

    # Call poll_status
    with patch("mindweaver.platform_service.trino.service.asyncio.to_thread") as mock_to_thread:
        mock_to_thread.return_value = ("online", "Healthy", {"argo": "ok"}, node_ports, cluster_nodes)

        await svc.poll_status(model)

        # Verify the state was updated with the correct URI from the https-nodeport service
        state = await svc.platform_state(model)
        assert state.trino_uri == "https://1.2.3.4:30443"

@pytest.mark.asyncio
async def test_trino_internal_shared_secret_visibility(mock_service_dependencies):
    """Test that internal_shared_secret is hidden from form and has a random default"""
    request, session = mock_service_dependencies
    svc = TrinoPlatformService(request, session)
    
    # Check internal_fields
    assert "internal_shared_secret" in svc.internal_fields()
    
    # Check createmodel_class schema - internal_shared_secret should be excluded
    create_model = svc.createmodel_class()
    assert "internal_shared_secret" not in create_model.model_fields
    
    # Check updatemodel_class schema - internal_shared_secret should be excluded
    update_model = svc.updatemodel_class()
    assert "internal_shared_secret" not in update_model.model_fields
    
    # Check random default on model
    model1 = TrinoPlatform(name="t1", project_id=1)
    model2 = TrinoPlatform(name="t2", project_id=1)
    assert model1.internal_shared_secret != model2.internal_shared_secret
    assert len(model1.internal_shared_secret) == 64
