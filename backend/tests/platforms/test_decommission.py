# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

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
class MockDecommissionPlatformModel(PlatformBase, table=True):
    __tablename__ = "mw_mock_decommission_platform_model"
    extra_field: str = "hello"


class MockDecommissionPlatformState(PlatformStateBase, table=True):
    __tablename__ = "mw_mock_decommission_platform_state"


# Define a concrete service for testing
class MockDecommissionPlatformService(PlatformService[MockDecommissionPlatformModel]):
    state_model = MockDecommissionPlatformState

    @classmethod
    def model_class(cls):
        return MockDecommissionPlatformModel


# Register router for testing
router = MockDecommissionPlatformService.router()
app.include_router(router, prefix="/api/v1")


def test_platform_service_decommission(client: TestClient, test_project):
    # 1. Update project with K8s info
    project_update = {
        "name": test_project["name"],
        "title": test_project["title"],
        "description": test_project["description"],
        "k8s_cluster_type": "remote",
        "k8s_cluster_kubeconfig": 'apiVersion: v1\nkind: Config\nclusters: []\ncontexts: []\ncurrent-context: ""\nusers: []',
    }
    resp = client.put(
        f"/api/v1/projects/{test_project['id']}",
        json=project_update,
        headers={"X-Project-Id": str(test_project['id'])},
    )
    resp.raise_for_status()

    # 2. Setup Model
    model_data = {
        "name": "test-svc-decomm",
        "title": "Test Svc Decomm",
        "project_id": test_project["id"],
        "project_id": test_project["id"],
        "extra_field": "world",
    }
    resp = client.post(
        "/api/v1/mock_decommission_platform_models",
        json=model_data,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    model_id = resp.json()["data"]["id"]

    # 3. Setup Templates
    with tempfile.TemporaryDirectory() as tmpdir:
        template_file = os.path.join(tmpdir, "deploy.yaml")
        with open(template_file, "w") as f:
            f.write(
                "apiVersion: v1\nkind: Service\nmetadata:\n  name: {{ name }}\n  namespace: default"
            )

        with patch.object(
            MockDecommissionPlatformService, "template_directory", tmpdir
        ):
            # 4. Mock Kubernetes library
            with patch("kubernetes.config.new_client_from_config"), patch(
                "kubernetes.dynamic.DynamicClient"
            ) as mock_dynamic_client_cls:

                mock_dynamic_client = MagicMock()
                mock_dynamic_client_cls.return_value = mock_dynamic_client

                mock_resource = MagicMock()
                mock_dynamic_client.resources.get.return_value = mock_resource

                resp = client.post(
                    f"/api/v1/mock_decommission_platform_models/{model_id}/_decommission",
                    headers={
                        "X-Project-Id": str(test_project["id"]),
                        "X-RESOURCE-NAME": "test-svc-decomm",
                    },
                )
                resp.raise_for_status()

                # Verify kubernetes library was called
                mock_dynamic_client.resources.get.assert_called_with(
                    api_version="v1", kind="Service"
                )
                mock_resource.delete.assert_called_once_with(
                    name="test-svc-decomm", namespace="default"
                )
