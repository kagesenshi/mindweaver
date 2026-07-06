# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import Request
from pydantic import ValidationError
from mindweaver.platform_service.nifi import NifiPlatform, NifiPlatformService
from mindweaver.fw.model import AsyncSession

@pytest.fixture
def mock_service_dependencies():
    request = MagicMock(spec=Request)
    session = MagicMock(spec=AsyncSession)
    session.exec = AsyncMock()
    session.flush = AsyncMock()
    return request, session

def test_nifi_resource_defaults():
    """Test default values for NiFi resource limits and replicas."""
    model = NifiPlatform(name="test-nifi", title="Test NiFi", project_id=1)
    assert model.replica_count == 1
    assert model.storage_size == "10Gi"
    assert model.cpu_request == 0.5
    assert model.cpu_limit == 2.0
    assert model.mem_request == 2.0
    assert model.mem_limit == 4.0

def test_nifi_cpu_validation():
    """Test that CPU request cannot exceed CPU limit."""
    with pytest.raises(ValidationError) as excinfo:
        NifiPlatform.model_validate(
            {
                "name": "test-nifi",
                "title": "Test NiFi",
                "project_id": 1,
                "cpu_request": 4.0,
                "cpu_limit": 2.0,
            }
        )
    assert "CPU request cannot be greater than CPU limit" in str(excinfo.value)

def test_nifi_mem_validation():
    """Test that memory request cannot exceed memory limit."""
    with pytest.raises(ValidationError) as excinfo:
        NifiPlatform.model_validate(
            {
                "name": "test-nifi",
                "title": "Test NiFi",
                "project_id": 1,
                "mem_request": 8.0,
                "mem_limit": 4.0,
            }
        )
    assert "Memory request cannot be greater than Memory limit" in str(excinfo.value)

@pytest.mark.asyncio
async def test_nifi_template_vars(mock_service_dependencies):
    """Test that template_vars returns expected template variable mappings."""
    request, session = mock_service_dependencies
    svc = NifiPlatformService(request, session)

    model = NifiPlatform(
        name="test-nifi",
        project_id=1,
        replica_count=3,
        storage_size="20Gi",
    )

    svc._resolve_namespace = AsyncMock(return_value="test-ns")
    mock_project = MagicMock(ingress_domain=None)
    mock_project.ldap_config_id = None
    svc.project = AsyncMock(return_value=mock_project)


    vars = await svc.template_vars(model)

    assert vars["name"] == "test-nifi"
    assert vars["namespace"] == "test-ns"
    assert vars["replica_count"] == 3
    assert vars["storage_size"] == "20Gi"

@pytest.mark.asyncio
async def test_nifi_render_manifests(mock_service_dependencies):
    """Test that the ArgoCD Application manifests render correctly without ingress domain."""
    request, session = mock_service_dependencies
    svc = NifiPlatformService(request, session)

    model = NifiPlatform(
        name="test-nifi",
        project_id=1,
        replica_count=3,
        storage_size="20Gi",
        auth_role_mapping=[
            {"entity": "admin@example.com", "role": "Admin"},
            {"entity": "CN=john.doe,OU=Users,O=Example", "role": "Reader"},
        ],
    )

    svc._resolve_namespace = AsyncMock(return_value="test-ns")
    mock_project = MagicMock(ingress_domain=None)
    mock_project.ldap_config_id = None
    svc.project = AsyncMock(return_value=mock_project)


    manifests = await svc.render_manifests(model)

    assert "name: test-nifi" in manifests
    assert "chart: nifi-cluster" in manifests
    assert "repoURL: ghcr.io/konpyutaika/helm-charts" in manifests
    assert "storage: \"20Gi\"" in manifests
    assert "namespace: test-ns" in manifests
    # No ingress domain means no HTTPRoute should be rendered
    assert "HTTPRoute" not in manifests
    # HTTPS listener should be configured
    assert "type: https" in manifests
    assert "containerPort: 8443" in manifests
    # NiFiKop manages PKI internally via create: true + issuerRef (no standalone Certificate)
    assert "kind: Certificate" not in manifests
    assert "create: true" in manifests
    assert "selfsigned-issuer" in manifests
    # Single user configurations and credentials secret assertions
    assert "singleUserConfiguration" in manifests
    assert "test-nifi-single-user-credentials" in manifests
    assert "extraManifests" in manifests
    assert "username: \"admin\"" in manifests
    assert "nifi.security.needClientAuth=false" in manifests
    assert "nifi.security.identity.mapping.pattern.dn.1=^CN=(node-\\\\d+)(,.*)?$" in manifests
    assert "nifi.security.identity.mapping.value.dn.1=$1" in manifests
    assert "nifi.security.identity.mapping.transform.dn.1=NONE" in manifests
    assert "nifi.security.identity.mapping.pattern.dn.2=CN=([^,]*)(?:, (?:O|OU)=.*)?" in manifests
    assert "nifi.security.identity.mapping.value.dn.2=$1" in manifests
    assert "nifi.security.identity.mapping.transform.dn.2=NONE" in manifests
    assert "nifi.flow.configuration.file=/opt/nifi/nifi-current/data/flow.json.gz" in manifests
    assert "nifi.flow.configuration.archive.dir=/opt/nifi/nifi-current/data/archive" in manifests
    assert "nifi.database.directory=/opt/nifi/nifi-current/data/database_repository" in manifests
    assert "nifi.flowfile.repository.directory=/opt/nifi/nifi-current/data/flowfile_repository" in manifests
    assert "nifi.content.repository.directory.default=/opt/nifi/nifi-current/data/content_repository" in manifests
    assert "nifi.provenance.repository.directory.default=/opt/nifi/nifi-current/data/provenance_repository" in manifests
    assert "nifi.state.management.local.provider.directory=/opt/nifi/nifi-current/data/state" in manifests
    # Managed users mapping assertions
    assert "managedAdminUsers:" in manifests
    assert "identity: \"admin@example.com\"" in manifests
    assert "name: \"admin\"" in manifests
    assert "identity: \"node-0\"" in manifests
    assert "identity: \"node-1\"" in manifests
    assert "identity: \"node-2\"" in manifests
    assert "managedReaderUsers:" in manifests
    assert "identity: \"CN=john.doe,OU=Users,O=Example\"" in manifests
    assert "name: \"john.doe\"" in manifests


@pytest.mark.asyncio
async def test_nifi_render_manifests_with_ingress(mock_service_dependencies):
    """Test that the HTTPRoute manifest renders correctly when ingress_domain is set.
    NiFiKop manages PKI internally (create: true + issuerRef); no standalone Certificate resource.
    BackendTLSPolicy references the NiFiKop-managed CA secret ({name}-ca)."""
    request, session = mock_service_dependencies
    svc = NifiPlatformService(request, session)

    model = NifiPlatform(
        name="test-nifi",
        project_id=1,
        replica_count=2,
        storage_size="10Gi",
    )

    svc._resolve_namespace = AsyncMock(return_value="test-ns")
    mock_project = MagicMock(ingress_domain="example.com")
    mock_project.ldap_config_id = None
    svc.project = AsyncMock(return_value=mock_project)


    manifests = await svc.render_manifests(model)

    # NiFiKop manages PKI internally — no standalone Certificate resource in manifests
    assert "kind: Certificate" not in manifests
    # sslSecrets create:true and issuerRef should be present in the ArgoCD App Helm values
    assert "create: true" in manifests
    assert "selfsigned-issuer" in manifests

    # HTTPRoute should route to HTTPS port 8443
    assert "HTTPRoute" in manifests
    assert "name: test-nifi-route" in manifests
    assert "test-nifi.example.com" in manifests
    assert "name: test-nifi-nodeport" in manifests
    assert "port: 8443" in manifests

    # BackendTLSPolicy should be present, referencing the project CA secret
    assert "BackendTLSPolicy" in manifests
    assert "name: test-nifi-tls-policy" in manifests
    assert "hostname: test-nifi-headless.test-ns.svc.cluster.local" in manifests
    # CA cert referenced from the project CA secret (tlsSecretName = {project_name}-ca-secret)
    assert "ca-secret" in manifests

@pytest.mark.asyncio
async def test_nifi_poll_status(mock_service_dependencies):
    """Test that nifi_uri is derived correctly in poll_status."""
    from mindweaver.platform_service.nifi.model import NifiPlatformState
    request, session = mock_service_dependencies
    svc = NifiPlatformService(request, session)

    model = NifiPlatform(
        name="test-nifi",
        project_id=1,
    )

    mock_state = MagicMock(spec=NifiPlatformState)
    mock_state.active = True

    with patch.object(svc, "platform_state", AsyncMock(return_value=mock_state)), \
         patch.object(svc, "kubeconfig", AsyncMock(return_value="mock-kubeconfig")), \
         patch.object(svc, "_resolve_namespace", AsyncMock(return_value="test-ns")):

        node_ports = []
        cluster_nodes = [{"hostname": "node1", "ipv4": "1.2.3.4", "ipv6": None}]

        async def mock_poll(*args):
            return "online", "Healthy", {}, node_ports, cluster_nodes

        with patch("mindweaver.platform_service.nifi.service.asyncio.to_thread", side_effect=mock_poll):
            mock_project = MagicMock()
            mock_project.ingress_domain = "example.com"
            svc.project = AsyncMock(return_value=mock_project)

            await svc.poll_status(model)

            # NiFi URL should be derived using ingress domain
            assert mock_state.nifi_uri == "https://test-nifi.example.com"


@pytest.mark.asyncio
async def test_nifi_decommission(mock_service_dependencies):
    """Test that decommissioning calls super method and deletes the CA secret."""
    request, session = mock_service_dependencies
    svc = NifiPlatformService(request, session)

    model = NifiPlatform(
        name="test-nifi",
        project_id=1,
    )

    # Mock all the external calls / Kubernetes clients
    mock_super_decommission = AsyncMock()
    mock_kubeconfig = AsyncMock(return_value="mock-kubeconfig")
    mock_resolve_namespace = AsyncMock(return_value="test-ns")

    with patch("mindweaver.platform_service.base.PlatformService.decommission", mock_super_decommission), \
         patch.object(svc, "kubeconfig", mock_kubeconfig), \
         patch.object(svc, "_resolve_namespace", mock_resolve_namespace), \
         patch("mindweaver.platform_service.nifi.service.config.new_client_from_config") as mock_new_client, \
         patch("mindweaver.platform_service.nifi.service.client.CoreV1Api") as mock_core_v1_class:

        mock_core_v1 = MagicMock()
        mock_core_v1_class.return_value = mock_core_v1

        await svc.decommission(model)

        # Ensure super.decommission was called
        mock_super_decommission.assert_called_once_with(model)

        # Ensure secret deletion was attempted with the correct name and namespace
        mock_core_v1.delete_namespaced_secret.assert_called_once_with(
            name="test-nifi-ca-secret", namespace="test-ns"
        )


@pytest.mark.asyncio
async def test_nifi_render_manifests_with_ldap(mock_service_dependencies):
    """Test that LDAP configuration is correctly retrieved and rendered in the NiFi manifests."""
    from mindweaver.service.ldap_config.model import LdapConfig
    request, session = mock_service_dependencies
    svc = NifiPlatformService(request, session)

    model = NifiPlatform(
        name="test-nifi",
        project_id=1,
        replica_count=1,
        storage_size="10Gi",
    )

    mock_project = MagicMock(ingress_domain="example.com", ldap_config_id=42)
    svc._resolve_namespace = AsyncMock(return_value="test-ns")
    svc.project = AsyncMock(return_value=mock_project)

    mock_ldap_config = LdapConfig(
        id=42,
        name="test-ldap",
        server_url="ldap://ldap.example.com:389",
        user_search_base="ou=users,dc=example,dc=com",
        user_search_filter="(&(uid={0})(objectClass=person))",
        username_attr="uid",
        verify_ssl=False,
    )
    
    mock_ldap_svc = MagicMock()
    mock_ldap_svc.get = AsyncMock(return_value=mock_ldap_config)
    
    with patch("mindweaver.service.ldap_config.service.LdapConfigService.get_service", AsyncMock(return_value=mock_ldap_svc)):
        manifests = await svc.render_manifests(model)
        
        assert "ldapConfiguration:" in manifests
        assert "enabled: true" in manifests
        assert "url: \"ldap://ldap.example.com:389\"" in manifests
        assert "searchBase: \"ou=users,dc=example,dc=com\"" in manifests
        assert "searchFilter: \"(&amp;(uid={0})(objectClass=person))\"" in manifests
        assert "authenticationStrategy: \"SIMPLE\"" in manifests
        assert "nifi.security.needClientAuth=false" in manifests
        assert "nifi.security.identity.mapping.pattern.dn.1=^CN=(node-\\\\d+)(,.*)?$" in manifests
        assert "nifi.security.identity.mapping.value.dn.1=$1" in manifests
        assert "nifi.security.identity.mapping.transform.dn.1=NONE" in manifests
        assert "nifi.security.identity.mapping.pattern.dn.2=CN=([^,]*)(?:, (?:O|OU)=.*)?" in manifests
        assert "nifi.security.identity.mapping.value.dn.2=$1" in manifests
        assert "nifi.security.identity.mapping.transform.dn.2=NONE" in manifests


def test_nifi_auth_role_mapping_validation():
    """Test validation for auth_role_mapping in NiFi."""
    from mindweaver.platform_service.nifi.model import NifiRoleMapping
    
    # Valid model validation
    model = NifiPlatform.model_validate(
        {
            "name": "test-nifi",
            "title": "Test NiFi",
            "project_id": 1,
            "auth_role_mapping": [NifiRoleMapping(entity="user1", role="Admin")]
        }
    )
    assert model.auth_role_mapping[0]["role"] == "Admin"

    # Invalid role should raise error
    with pytest.raises(ValidationError) as excinfo:
        NifiPlatform.model_validate(
            {
                "name": "test-nifi",
                "title": "Test NiFi",
                "project_id": 1,
                "auth_role_mapping": [{"entity": "user1", "role": "InvalidRole"}]
            }
        )
    assert "Invalid role: InvalidRole" in str(excinfo.value)


def test_nifi_auth_role_mapping_dict_assignment():
    """Test assignment of dict and custom objects to auth_role_mapping."""
    model = NifiPlatform(name="test-nifi", title="Test NiFi", project_id=1)
    model.auth_role_mapping = [{"entity": "user1", "role": "Admin"}]
    
    assert isinstance(model.auth_role_mapping[0], dict)
    assert model.auth_role_mapping[0]["entity"] == "user1"
    assert model.auth_role_mapping[0]["role"] == "Admin"

