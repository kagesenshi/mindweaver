# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
import yaml
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import Request
from sqlmodel import Session
from pydantic import ValidationError

from mindweaver.platform_service.trino import TrinoPlatform, TrinoPlatformService, TrinoState, TrinoPlatformState
from mindweaver.platform_service.hive_metastore import HiveMetastorePlatformState, HiveMetastorePlatform
from mindweaver.service.s3_storage.model import S3Storage
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
    assert model.disable_s3_cert_checking is False

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

    # Invalid Catalogs: No catalogs defined
    with pytest.raises(ValidationError) as excinfo:
        TrinoPlatform.model_validate(
            {
                "name": "test-trino",
                "title": "Test Trino",
                "project_id": 1,
                "hms_ids": [],
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
        database_source_ids=[20],
        process_forwarded=True,
    )

    # Mock _resolve_namespace
    svc._resolve_namespace = AsyncMock(return_value="trino-ns")

    # Mock HiveMetastorePlatformService
    mock_hms_svc = AsyncMock()
    
    mock_hms_model_10 = MagicMock()
    mock_hms_model_10.name = "test-hms-lakehouse"
    mock_hms_model_10.s3_storage_id = 100
    
    mock_hms_svc.get.side_effect = lambda id: mock_hms_model_10
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
    assert len(vars["catalogs"]) == 2
    assert vars["preferred_catalog"] == "test-hms-lakehouse"
    
    # Check HMS catalog
    hms_cat = next(c for c in vars["catalogs"] if c["catalog"] == "test-hms-lakehouse")
    assert hms_cat["properties"]["connector.name"] == "lakehouse"
    assert hms_cat["properties"]["hive.metastore.uri"] == "thrift://hms-internal:9083"
    assert hms_cat["properties"]["fs.native-s3.enabled"] == "true"
    assert hms_cat["properties"]["s3.endpoint"] == "http://minio:9000"
    assert hms_cat["properties"]["s3.aws-access-key"] == "access"
    assert hms_cat["properties"]["s3.aws-secret-key"] == "secret"
    assert hms_cat["properties"]["s3.path-style-access"] == "true"

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
    
    assert "test-hms-lakehouse" in values["catalogs"]
    assert "mypsql" in values["catalogs"]
    
    hms_props = values["catalogs"]["test-hms-lakehouse"]
    assert "connector.name=lakehouse" in hms_props
    assert "hive.metastore.uri=thrift://hms-internal:9083" in hms_props

    assert "jdbc:postgresql://postgres-host:5432/mydb" in values["catalogs"]["mypsql"]
    
    # Verify process_forwarded is rendered
    assert "http-server.process-forwarded=true" in values["additionalConfigProperties"]

    # Verify access-control.properties and rules.json are rendered
    assert "access-control.name=file" in values["coordinator"]["additionalConfigFiles"]["access-control.properties"]
    import json
    rules = json.loads(values["coordinator"]["additionalConfigFiles"]["rules.json"])
    assert rules["impersonation"][0]["originalUser"] == "CN=.*\\.trino-ns\\.svc\\.cluster\\.local"

    # Verify the additional HTTPS NodePort service is present in the docs
    https_svc = next(d for d in docs if d["kind"] == "Service" and d["metadata"]["name"] == "trino-test-https-nodeport")
    assert https_svc["spec"]["type"] == "NodePort"
    assert https_svc["spec"]["ports"][0]["port"] == 8443


@pytest.mark.asyncio
async def test_trino_override_image_template(mock_service_dependencies):
    """Test that custom image is rendered correctly when resolved from stack"""
    request, session = mock_service_dependencies
    svc = TrinoPlatformService(request, session)
    svc._resolve_namespace = AsyncMock(return_value="trino-ns")
    svc.project = AsyncMock(return_value=MagicMock(ldap_config_id=None))
    svc.resolve_image = AsyncMock(return_value=("custom/trino", "v1.0.0"))

    model = TrinoPlatform(
        name="trino-test",
        title="Trino Test",
        project_id=1,
    )

    manifest = await svc.render_manifests(model)

    assert "targetRevision: 1.41.0" in manifest
    assert "repository: \"custom/trino\"" in manifest
    assert "tag: \"v1.0.0\"" in manifest


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
    assert "http-server.authentication.type=PASSWORD,CERTIFICATE" in manifest
    assert "http-server.authentication.certificate.user-mapping.pattern=.*?(CN=[^,]+).*" in manifest
    assert "additionalConfigFiles:" in manifest
    assert "ldap.properties:" in manifest
    assert "password-authenticator.name=ldap" in manifest
    assert "ldap.url=ldap://ldap.example.com:389" in manifest
    assert "ldap.bind-dn=cn=admin,dc=example,dc=com" in manifest
    assert "ldap.bind-password=encrypted_pass" in manifest
    assert "ldap.user-base-dn=ou=users,dc=example,dc=com" in manifest
    assert "ldap.group-auth-pattern=(uid=${USER})" in manifest
    assert "password-authenticator.config-files=/etc/trino/ldap.properties" in manifest


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
    mock_project = MagicMock(ldap_config_id=None)
    mock_project.name = "mock-project"
    svc.project = AsyncMock(return_value=mock_project)

    with patch("mindweaver.platform_service.trino.service.HiveMetastorePlatformService.get_service", AsyncMock(return_value=mock_hms_svc)), \
         patch("mindweaver.platform_service.trino.service.decrypt_password", lambda x: x):
        
        manifest = await svc.render_manifests(model)

    docs = list(yaml.safe_load_all(manifest))
    assert len(docs) >= 3  # Application + Certificate + NodePort Service

    # Ensure no local Issuer is created (it's cluster-wide now - wait, project-wide)
    issuer_kinds = [d["kind"] for d in docs]
    assert "Issuer" not in issuer_kinds
    assert "Secret" in issuer_kinds
    
    cert = next(d for d in docs if d["kind"] == "Certificate")
    assert cert["metadata"]["name"] == "trino-https-test-tls"
    assert cert["spec"]["issuerRef"]["name"] == "mock-project-selfsigned-issuer"
    assert cert["spec"]["issuerRef"]["kind"] == "Issuer"
    assert "keystores" in cert["spec"]
    assert cert["spec"]["keystores"]["jks"]["create"] is True

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
    assert "http-server.https.truststore.path=/etc/trino/tls/truststore.jks" in props
    assert "http-server.https.truststore.key=changeit" in props
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
    svc.project = AsyncMock(return_value=MagicMock(ingress_domain=None))

    # Call poll_status
    with patch("mindweaver.platform_service.trino.poller.asyncio.to_thread") as mock_to_thread:
        mock_to_thread.return_value = ("online", "Healthy", {"argo": "ok"}, node_ports, cluster_nodes)

        await svc.poll_status(model)

        # Verify the state was updated with the correct URI from the https-nodeport service
        state = await svc.platform_state(model)
        assert state.trino_uri == "https://1.2.3.4:30443"


@pytest.mark.asyncio
async def test_trino_poll_status_with_ingress_domain(mock_service_dependencies):
    """Test that poll_status sets the correct trino_uri when ingress_domain is configured"""
    request, session = mock_service_dependencies
    svc = TrinoPlatformService(request, session)

    svc._resolve_namespace = AsyncMock(return_value="trino-ns")
    svc.kubeconfig = AsyncMock(return_value="dummy-kubeconfig")
    svc.platform_state = AsyncMock(return_value=MagicMock(active=True))
    svc.project = AsyncMock(return_value=MagicMock(ingress_domain="example.com"))

    model = TrinoPlatform(
        id=1,
        name="trino-instance",
        title="Trino Instance",
        project_id=1,
        hms_ids=[10],
    )

    node_ports = []
    cluster_nodes = []

    svc.get_preferred_catalog = AsyncMock(return_value="hive")

    with patch("mindweaver.platform_service.trino.poller.asyncio.to_thread") as mock_to_thread:
        mock_to_thread.return_value = ("online", "Healthy", {"argo": "ok"}, node_ports, cluster_nodes)

        await svc.poll_status(model)

        state = await svc.platform_state(model)
        assert state.trino_uri == "https://trino-instance.example.com"
        assert state.extra_data["ingress_domain"] == "example.com"


@pytest.mark.asyncio
async def test_trino_envoy_route_rendering(mock_service_dependencies):
    """Test that Envoy Gateway HTTPRoute and BackendTLSPolicy are rendered when ingress_domain is set"""
    request, session = mock_service_dependencies
    svc = TrinoPlatformService(request, session)
    svc._resolve_namespace = AsyncMock(return_value="trino-ns")

    model = TrinoPlatform(
        name="trino-envoy",
        title="Trino Envoy",
        project_id=1,
        hms_ids=[10],
    )

    # Mock project with ingress_domain
    mock_project = MagicMock()
    mock_project.ingress_domain = "myproject.local"
    mock_project.ldap_config_id = None
    svc.project = AsyncMock(return_value=mock_project)

    # Mock HMS service
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

    with patch("mindweaver.platform_service.trino.service.HiveMetastorePlatformService.get_service", AsyncMock(return_value=mock_hms_svc)), \
         patch("mindweaver.platform_service.trino.service.decrypt_password", lambda x: x):
        
        manifest = await svc.render_manifests(model)

    docs = list(yaml.safe_load_all(manifest))
    
    # Verify HTTPRoute is present
    route = next(d for d in docs if d.get("kind") == "HTTPRoute")
    assert route["metadata"]["name"] == "trino-envoy-route"
    assert route["spec"]["parentRefs"][0]["name"] == "project-gateway"
    assert route["spec"]["hostnames"][0] == "trino-envoy.myproject.local"
    assert route["spec"]["rules"][0]["backendRefs"][0]["name"] == "trino-envoy"
    assert route["spec"]["rules"][0]["backendRefs"][0]["port"] == 8443

    # Verify BackendTLSPolicy is present
    tls_policy = next(d for d in docs if d.get("kind") == "BackendTLSPolicy")
    assert tls_policy["metadata"]["name"] == "trino-envoy-tls-policy"
    assert tls_policy["spec"]["targetRefs"][0]["name"] == "trino-envoy"
    assert tls_policy["spec"]["validation"]["hostname"] == "trino-envoy.trino-ns.svc.cluster.local"
    assert tls_policy["spec"]["validation"]["caCertificateRefs"][0]["name"] == "trino-envoy-tls"

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


@pytest.mark.asyncio
async def test_trino_catalog_custom_parameters(mock_service_dependencies):
    """Test that trino.* parameters in data source are passed to catalog properties without prefix"""
    request, session = mock_service_dependencies
    svc = TrinoPlatformService(request, session)
    svc._resolve_namespace = AsyncMock(return_value="trino-ns")
    svc.project = AsyncMock(return_value=MagicMock(ldap_config_id=None))

    # Mock Data Source with trino. prefixed parameters
    ds = MagicMock()
    ds.name = "custom-ds"
    ds.engine = "postgresql"
    ds.host = "host"
    ds.port = 5432
    ds.database = "db"
    ds.login = "user"
    ds.password = "pass"
    ds.parameters = {
        "trino.case-insensitive-name-matching": "true",
        "normal-param": "value",
    }

    mock_ds_svc = AsyncMock()
    mock_ds_svc.get.return_value = ds

    model = TrinoPlatform(
        name="trino-test",
        project_id=1,
        database_source_ids=[1],
    )

    with patch(
        "mindweaver.platform_service.trino.service.DatabaseSourceService.get_service",
        AsyncMock(return_value=mock_ds_svc),
    ), patch("mindweaver.platform_service.trino.service.decrypt_password", lambda x: x):
        vars = await svc.template_vars(model)

    catalog = next(c for c in vars["catalogs"] if c["catalog"] == "custom-ds")
    # Verify trino. prefix was stripped
    assert catalog["properties"]["case-insensitive-name-matching"] == "true"
    assert "trino.case-insensitive-name-matching" not in catalog["properties"]
    # Verify normal parameters are kept
    assert catalog["properties"]["normal-param"] == "value"

@pytest.mark.asyncio
async def test_trino_state_credentials(mock_service_dependencies):
    """Test that TrinoState.get returns decrypted admin credentials if admin_password is set."""
    request, session = mock_service_dependencies
    
    # Platform model with admin_password
    model = TrinoPlatform(
        id=1,
        name="trino",
        project_id=1,
        admin_password="admin_secret_pass",
    )
    
    # State model
    state = TrinoPlatformState(platform_id=1, trino_uri="https://trino.local")
    
    # Mock service
    svc = MagicMock()
    svc.platform_state = AsyncMock(return_value=state)
    
    # Patch decrypt_password
    with patch("mindweaver.platform_service.trino.state.decrypt_password", side_effect=lambda x: x):
        t_state = TrinoState(model, svc)
        # Mock DefaultPlatformState.get to return a dict
        with patch("mindweaver.platform_service.base.DefaultPlatformState.get", AsyncMock(return_value={"id": 1, "active": True})):
            res = await t_state.get()
            
    assert res["db_user"] == "trino"
    assert res["db_pass"] == "admin_secret_pass"


@pytest.mark.asyncio
async def test_trino_state_credentials_no_admin(mock_service_dependencies):
    """Test that TrinoState.get returns trino and fallback pass if admin_password is not set."""
    request, session = mock_service_dependencies
    
    # Platform model with no admin_password
    model = TrinoPlatform(
        id=1,
        name="trino",
        project_id=1,
        admin_password=None,
    )
    
    svc = MagicMock()
    svc.platform_state = AsyncMock(return_value=None)
    
    t_state = TrinoState(model, svc)
    with patch("mindweaver.platform_service.base.DefaultPlatformState.get", AsyncMock(return_value={"id": 1, "active": True})):
        res = await t_state.get()
        
    assert res["db_user"] == "trino"
    assert res["db_pass"] == "admin"
@pytest.mark.asyncio
async def test_trino_jwt_rendering(mock_service_dependencies):
    """Test that JWT authentication is correctly rendered in Trino config"""
    request, session = mock_service_dependencies
    svc = TrinoPlatformService(request, session)
    svc._resolve_namespace = AsyncMock(return_value="trino-ns")
    
    # Mock project with LDAP configured to test multiple auth priority rendering
    mock_project = MagicMock()
    mock_project.name = "myproject"
    mock_project.ldap_config_id = None
    mock_project.ingress_domain = None
    svc.project = AsyncMock(return_value=mock_project)

    model = TrinoPlatform(
        name="trino-jwt-test",
        title="Trino JWT Test",
        project_id=1,
        hms_ids=[10],  # Needs at least one catalog
    )

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

    with patch("mindweaver.platform_service.trino.service.HiveMetastorePlatformService.get_service", AsyncMock(return_value=mock_hms_svc)), \
         patch("mindweaver.platform_service.trino.service.decrypt_password", lambda x: x):
        
        vars = await svc.template_vars(model)
        manifest = await svc.render_manifests(model)

    assert vars["jwt_enabled"] is False
    assert "jwt_key_file" not in vars or vars["jwt_key_file"] is None

    docs = list(yaml.safe_load_all(manifest))
    app = next(d for d in docs if d["kind"] == "Application")
    values = yaml.safe_load(app["spec"]["source"]["helm"]["values"])
    
    assert "http-server.authentication.type=PASSWORD,CERTIFICATE" in values["server"]["coordinatorExtraConfig"]
    assert "http-server.authentication.jwt.key-file=" not in values["server"]["coordinatorExtraConfig"]
    assert "additionalLogProperties" in values
    assert "log.properties" not in values["coordinator"]["additionalConfigFiles"]
    assert "-Dlog.enable-console=true" in values["coordinator"]["additionalJVMConfig"]
    assert "-Dlog.enable-console=true" in values["worker"]["additionalJVMConfig"]


@pytest.mark.asyncio
async def test_trino_configurable_rules(mock_service_dependencies):
    """Test that custom rules can be configured and automated rule is merged"""
    import json
    request, session = mock_service_dependencies
    svc = TrinoPlatformService(request, session)
    svc._resolve_namespace = AsyncMock(return_value="trino-ns")
    
    # Mock project
    mock_project = MagicMock(ldap_config_id=None)
    mock_project.name = "test-project"
    svc.project = AsyncMock(return_value=mock_project)

    # 1. Test model validator parses rules as JSON string
    model = TrinoPlatform.model_validate(
        {
            "name": "trino-test",
            "title": "Trino Test",
            "project_id": 1,
            "database_source_ids": [1],
            "rules": '{"catalogs": [{"catalog": "mysql", "allow": "all"}]}'
        }
    )
    assert model.rules == {"catalogs": [{"catalog": "mysql", "allow": "all"}]}

    # 1.5 Test that rules has a default when omitted
    model_default = TrinoPlatform.model_validate(
        {
            "name": "trino-test-default",
            "title": "Trino Test Default",
            "project_id": 1,
            "database_source_ids": [1],
        }
    )
    assert model_default.rules == {"catalogs": [{"catalog": ".*", "allow": "all"}]}

    # Mock DatabaseSourceService
    mock_ds_svc = AsyncMock()
    mock_ds_model = MagicMock()
    mock_ds_model.name = "mysql-ds"
    mock_ds_model.engine = "mysql"
    mock_ds_model.host = "mysql-host"
    mock_ds_model.port = 3306
    mock_ds_model.database = "db"
    mock_ds_model.login = "user"
    mock_ds_model.password = "pass"
    mock_ds_model.parameters = {}
    mock_ds_svc.get.return_value = mock_ds_model

    with patch("mindweaver.platform_service.trino.service.DatabaseSourceService.get_service", AsyncMock(return_value=mock_ds_svc)), \
         patch("mindweaver.platform_service.trino.service.decrypt_password", lambda x: x):
        vars = await svc.template_vars(model)
        
    rules = json.loads(vars["rules_json"])
    
    # Assert custom rules are preserved
    assert rules["catalogs"][0]["catalog"] == "mysql"
    # Assert automated impersonation rule is appended
    assert len(rules["impersonation"]) == 1
    assert rules["impersonation"][0]["originalUser"] == "CN=.*\\.trino-ns\\.svc\\.cluster\\.local"


@pytest.mark.asyncio
async def test_trino_s3_cert_checking(mock_service_dependencies):
    """Test that S3 certificate checking JVM option is added based on disable_s3_cert_checking boolean"""
    request, session = mock_service_dependencies
    svc = TrinoPlatformService(request, session)
    svc._resolve_namespace = AsyncMock(return_value="trino-ns")
    
    mock_project = MagicMock(ldap_config_id=None)
    mock_project.name = "test-project"
    svc.project = AsyncMock(return_value=mock_project)

    # Mock HMS service to satisfy validation and template rendering requirements
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

    # Scenario 1: disable_s3_cert_checking is True
    model_disabled = TrinoPlatform(
        name="trino-disabled-certs",
        title="Trino Disabled Certs",
        project_id=1,
        hms_ids=[10],
        disable_s3_cert_checking=True,
    )

    with patch("mindweaver.platform_service.trino.service.HiveMetastorePlatformService.get_service", AsyncMock(return_value=mock_hms_svc)), \
         patch("mindweaver.platform_service.trino.service.decrypt_password", lambda x: x):
        manifest_disabled = await svc.render_manifests(model_disabled)

    docs_disabled = list(yaml.safe_load_all(manifest_disabled))
    app_disabled = next(d for d in docs_disabled if d["kind"] == "Application")
    values_disabled = yaml.safe_load(app_disabled["spec"]["source"]["helm"]["values"])
    
    # Assert JVM option is present for both coordinator and worker
    assert "-Dcom.amazonaws.sdk.disableCertChecking=true" in values_disabled["coordinator"]["additionalJVMConfig"]
    assert "-Dcom.amazonaws.sdk.disableCertChecking=true" in values_disabled["worker"]["additionalJVMConfig"]

    # Scenario 2: disable_s3_cert_checking is False
    model_enabled = TrinoPlatform(
        name="trino-enabled-certs",
        title="Trino Enabled Certs",
        project_id=1,
        hms_ids=[10],
        disable_s3_cert_checking=False,
    )

    with patch("mindweaver.platform_service.trino.service.HiveMetastorePlatformService.get_service", AsyncMock(return_value=mock_hms_svc)), \
         patch("mindweaver.platform_service.trino.service.decrypt_password", lambda x: x):
        manifest_enabled = await svc.render_manifests(model_enabled)

    docs_enabled = list(yaml.safe_load_all(manifest_enabled))
    app_enabled = next(d for d in docs_enabled if d["kind"] == "Application")
    values_enabled = yaml.safe_load(app_enabled["spec"]["source"]["helm"]["values"])
    
    # Assert JVM option is NOT present for either coordinator or worker
    assert "-Dcom.amazonaws.sdk.disableCertChecking=true" not in values_enabled["coordinator"]["additionalJVMConfig"]
    assert "-Dcom.amazonaws.sdk.disableCertChecking=true" not in values_enabled["worker"]["additionalJVMConfig"]





