import pytest
import os
import tempfile
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from mindweaver.app import app
from mindweaver.platform_service.base import (
    PlatformBase,
    PlatformService,
    PlatformStateBase,
)


# Define a concrete model for testing
class MockApplyPlatformModel(PlatformBase, table=True):
    __tablename__ = "mw_mock_apply_platform_model"
    extra_field: str = "hello"


class MockApplyPlatformState(PlatformStateBase, table=True):
    __tablename__ = "mw_mock_apply_platform_state"


# Define a concrete service for testing
class MockApplyPlatformService(PlatformService[MockApplyPlatformModel]):
    state_model = MockApplyPlatformState

    @classmethod
    def model_class(cls):
        return MockApplyPlatformModel


# Register router for testing
router = MockApplyPlatformService.router()
app.include_router(router, prefix="/api/v1")


def test_platform_service_deploy(client: TestClient, test_project):
    # 1. Setup K8sCluster
    cluster_data = {
        "name": "test-cluster",
        "title": "Test Cluster",
        "type": "remote",
        "kubeconfig": 'apiVersion: v1\nkind: Config\nclusters: []\ncontexts: []\ncurrent-context: ""\nusers: []',
        "project_id": test_project["id"],
    }
    resp = client.post(
        "/api/v1/k8s_clusters",
        json=cluster_data,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    cluster_id = resp.json()["record"]["id"]

    # 2. Setup Model
    model_data = {
        "name": "test-svc",
        "title": "Test Svc",
        "project_id": test_project["id"],
        "k8s_cluster_id": cluster_id,
        "extra_field": "world",
    }
    resp = client.post(
        "/api/v1/mock_apply_platform_models",
        json=model_data,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    model_id = resp.json()["record"]["id"]

    # 3. Setup Templates
    with tempfile.TemporaryDirectory() as tmpdir:
        template_file = os.path.join(tmpdir, "deploy.yaml")
        with open(template_file, "w") as f:
            f.write(
                "apiVersion: v1\nkind: Deployment\nmetadata:\n  name: {{ name }}\nextra: {{ extra_field }}"
            )

        with patch.object(MockApplyPlatformService, "template_directory", tmpdir):
            # 4. Mock Kubernetes library
            with patch(
                "kubernetes.config.new_client_from_config"
            ) as mock_new_client, patch(
                "kubernetes.dynamic.DynamicClient"
            ) as mock_dynamic_client, patch(
                "mindweaver.platform_service.base.client.CoreV1Api"
            ) as mock_core_v1:

                mock_dynamic_client.return_value.resources.get.return_value.namespaced = (
                    True
                )

                resp = client.post(
                    f"/api/v1/mock_apply_platform_models/{model_id}/_deploy",
                    headers={"X-Project-Id": str(test_project["id"])},
                )
                resp.raise_for_status()

                # Verify kubernetes library was called
                mock_new_client.assert_called_once()
                # Verify DynamicClient created resources
                mock_dynamic_client.assert_called_once()
                mock_dynamic_client.return_value.resources.get.return_value.create.assert_called()


def test_platform_service_deploy_missing_dir(client: TestClient, test_project):
    # 1. Setup K8sCluster
    cluster_data = {
        "name": "test-cluster-missing",
        "title": "Test Cluster Missing",
        "type": "remote",
        "kubeconfig": 'apiVersion: v1\nkind: Config\nclusters: []\ncontexts: []\ncurrent-context: ""\nusers: []',
        "project_id": test_project["id"],
    }
    resp = client.post(
        "/api/v1/k8s_clusters",
        json=cluster_data,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    cluster_id = resp.json()["record"]["id"]

    model_data = {
        "name": "test-svc-missing",
        "title": "Test Svc Missing",
        "project_id": test_project["id"],
        "k8s_cluster_id": cluster_id,
    }
    resp = client.post(
        "/api/v1/mock_apply_platform_models",
        json=model_data,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    model_id = resp.json()["record"]["id"]

    with patch.object(
        MockApplyPlatformService, "template_directory", "/non/existent/path"
    ):
        with pytest.raises(ValueError, match="does not exist"):
            client.post(
                f"/api/v1/mock_apply_platform_models/{model_id}/_deploy",
                headers={"X-Project-Id": str(test_project["id"])},
            )
