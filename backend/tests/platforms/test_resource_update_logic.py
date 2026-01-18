import pytest
import kubernetes
from unittest.mock import MagicMock, patch, AsyncMock
from mindweaver.platform_service.base import (
    PlatformService,
    PlatformBase,
    PlatformStateBase,
)


# Define a concrete model for testing
class MockUpdatePlatformModel(PlatformBase, table=True):
    __tablename__ = "mw_mock_update_platform_model"


class MockUpdatePlatformState(PlatformStateBase, table=True):
    __tablename__ = "mw_mock_update_platform_state"


# Define a concrete service for testing
class MockUpdatePlatformService(PlatformService[MockUpdatePlatformModel]):
    state_model = MockUpdatePlatformState

    @classmethod
    def model_class(cls):
        return MockUpdatePlatformModel


@pytest.mark.asyncio
async def test_deploy_to_cluster_updates_on_409():
    """
    Test that _deploy_to_cluster attempts to patch a resource if create returns 409 (AlreadyExists).
    """
    svc = MockUpdatePlatformService(MagicMock(), MagicMock())

    kubeconfig = 'apiVersion: v1\nkind: Config\nclusters: []\ncontexts: []\ncurrent-context: ""\nusers: []'
    manifest = "apiVersion: v1\nkind: Namespace\nmetadata:\n  name: test-ns"

    with patch("kubernetes.config.new_client_from_config") as mock_new_client, patch(
        "kubernetes.dynamic.DynamicClient"
    ) as mock_dynamic_client, patch("kubernetes.client.CoreV1Api") as mock_core_v1:

        # Configure mocks
        mock_resource = mock_dynamic_client.return_value.resources.get.return_value
        mock_resource.namespaced = False

        # Simulate 409 Conflict on create
        mock_resource.create.side_effect = kubernetes.client.exceptions.ApiException(
            status=409
        )

        # Call the private method (or deploy)
        await svc._deploy_to_cluster(kubeconfig, manifest, "default")

        # Assertions
        assert mock_resource.create.called
        # This is what we want to fail initially and then pass after the fix
        assert (
            mock_resource.patch.called
        ), "resource.patch() should be called if create() fails with 409"

        # Verify patch was called with Merge Patch
        args, kwargs = mock_resource.patch.call_args
        assert kwargs.get("content_type") == "application/merge-patch+json"
