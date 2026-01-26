import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from mindweaver.app import app
from mindweaver.platform_service.base import (
    PlatformBase,
    PlatformService,
    PlatformStateBase,
)


# Define a concrete model for testing
class MockTriggerPlatformModel(PlatformBase, table=True):
    __tablename__ = "mw_mock_trigger_platform_model"


class MockTriggerPlatformState(PlatformStateBase, table=True):
    __tablename__ = "mw_mock_trigger_platform_state"


class MockTriggerPlatformService(PlatformService[MockTriggerPlatformModel]):
    state_model = MockTriggerPlatformState

    @classmethod
    def model_class(cls):
        return MockTriggerPlatformModel


# Register router for testing
# We need to do this BEFORE any tests run to ensure the routes are registered
router = MockTriggerPlatformService.router()
app.include_router(router, prefix="/api/v1")


def test_platform_state_triggers(client: TestClient, test_project):
    # 1. Setup K8sCluster
    cluster_data = {
        "name": "test-cluster-trigger",
        "title": "Test Cluster Trigger",
        "type": "remote",
        "kubeconfig": "apiVersion: v1\nkind: Config\nclusters: []",
        "project_id": test_project["id"],
    }
    resp = client.post(
        "/api/v1/k8s_clusters",
        json=cluster_data,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    cluster_id = resp.json()["data"]["id"]

    # 2. Create Model
    model_data = {
        "name": "trigger-pg",
        "title": "Trigger Postgres",
        "project_id": test_project["id"],
        "k8s_cluster_id": cluster_id,
    }
    resp = client.post(
        "/api/v1/mock_trigger_platform_models",
        json=model_data,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    model_id = resp.json()["data"]["id"]

    # 3. Mock deploy and decommission on the SERVICE class,
    # but we need to mock it on the instance or globally.
    # Since FastAPI creates a new service instance via Depends,
    # patching the class method is usually enough if it's not a static method.

    with patch.object(
        MockTriggerPlatformService, "deploy", return_value=None
    ) as mock_deploy, patch.object(
        MockTriggerPlatformService, "decommission", return_value=None
    ) as mock_decommission:

        # 4. Set active=True (should trigger deploy)
        update_data = {"active": True}
        resp = client.post(
            f"/api/v1/mock_trigger_platform_models/{model_id}/_state",
            json=update_data,
            headers={"X-Project-Id": str(test_project["id"])},
        )
        resp.raise_for_status()
        assert mock_deploy.called
        assert not mock_decommission.called

        mock_deploy.reset_mock()
        mock_decommission.reset_mock()

        # 5. Set active=False (should trigger decommission)
        update_data = {"active": False}
        resp = client.post(
            f"/api/v1/mock_trigger_platform_models/{model_id}/_state",
            json=update_data,
            headers={
                "X-Project-Id": str(test_project["id"]),
                "X-RESOURCE-NAME": "trigger-pg",
            },
        )
        resp.raise_for_status()
        assert mock_decommission.called
        assert not mock_deploy.called

        mock_deploy.reset_mock()
        mock_decommission.reset_mock()

        # 6. Update status only (should NOT trigger anything)
        update_data = {"status": "online"}
        resp = client.post(
            f"/api/v1/mock_trigger_platform_models/{model_id}/_state",
            json=update_data,
            headers={"X-Project-Id": str(test_project["id"])},
        )
        resp.raise_for_status()
        assert not mock_deploy.called
        assert not mock_decommission.called

        # 7. Set active=True again (should trigger deploy again - refresh)
        update_data = {"active": True}
        resp = client.post(
            f"/api/v1/mock_trigger_platform_models/{model_id}/_state",
            json=update_data,
            headers={"X-Project-Id": str(test_project["id"])},
        )
        resp.raise_for_status()
        assert mock_deploy.called
