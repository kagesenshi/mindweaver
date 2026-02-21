import pytest
from fastapi.testclient import TestClient
from mindweaver.app import app
from mindweaver.platform_service.base import (
    PlatformBase,
    PlatformService,
    PlatformStateBase,
)
from mindweaver.service.project import Project, K8sClusterType
from typing import Annotated
from fastapi import Depends


# Define a concrete model for testing
class SamplePlatformModel(PlatformBase, table=True):
    __tablename__ = "mw_sample_platform_model"


class SamplePlatformState(PlatformStateBase, table=True):
    __tablename__ = "mw_sample_platform_state"


# Define a concrete service for testing
class SamplePlatformService(PlatformService[SamplePlatformModel]):
    state_model = SamplePlatformState

    @classmethod
    def model_class(cls):
        return SamplePlatformModel


# Register router for testing
router = SamplePlatformService.router()


@router.get(
    f"{SamplePlatformService.model_path()}/test/kubeconfig",
    tags=["Test"],
)
async def api_test_kubeconfig(
    model: Annotated[SamplePlatformModel, Depends(SamplePlatformService.get_model)],
    svc: Annotated[SamplePlatformService, Depends(SamplePlatformService.get_service)],
):
    """Internal endpoint for testing kubeconfig method"""
    return {"kubeconfig": await svc.kubeconfig(model)}


@router.get(
    f"{SamplePlatformService.model_path()}/test/project_name",
    tags=["Test"],
)
async def api_test_project_name(
    model: Annotated[SamplePlatformModel, Depends(SamplePlatformService.get_model)],
    svc: Annotated[SamplePlatformService, Depends(SamplePlatformService.get_service)],
):
    """Internal endpoint for testing project method"""
    project = await svc.project(model)
    return {"project_name": project.name}


app.include_router(router, prefix="/api/v1")


def test_cluster_service_api(client: TestClient, test_project):
    # 1. Update project with K8s info
    project_update = {
        "name": test_project["name"],
        "title": test_project["title"],
        "description": test_project["description"],
        "k8s_cluster_type": "remote",
        "k8s_cluster_kubeconfig": "test-kubeconfig-content",
    }
    resp = client.put(
        f"/api/v1/projects/{test_project['id']}",
        json=project_update,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()

    # 2. Create a Sample Cluster Service Model
    svc_data = {
        "name": "my-svc",
        "title": "My Service",
        "project_id": test_project["id"],
    }
    resp = client.post(
        "/api/v1/sample_platform_models",
        json=svc_data,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    svc_id = resp.json()["data"]["id"]

    # 3. Test project retrieval via API
    resp = client.get(
        f"/api/v1/sample_platform_models/{svc_id}/test/project_name",
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    assert resp.json()["project_name"] == "test-project"

    # 4. Test kubeconfig retrieval via API
    resp = client.get(
        f"/api/v1/sample_platform_models/{svc_id}/test/kubeconfig",
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    assert resp.json()["kubeconfig"] == "test-kubeconfig-content"


def test_cluster_service_kubeconfig_missing_api(client: TestClient, test_project):
    # 1. Update project with K8s info but WITHOUT kubeconfig
    project_update = {
        "name": test_project["name"],
        "title": test_project["title"],
        "description": test_project["description"],
        "k8s_cluster_type": "remote",
        "k8s_cluster_kubeconfig": None,
    }
    resp = client.put(
        f"/api/v1/projects/{test_project['id']}",
        json=project_update,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()

    # 2. Create a Sample Cluster Service Model
    svc_data = {
        "name": "bad-svc",
        "title": "Bad Service",
        "project_id": test_project["id"],
    }
    resp = client.post(
        "/api/v1/sample_platform_models",
        json=svc_data,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    svc_id = resp.json()["data"]["id"]

    # 3. Test kubeconfig retrieval failure via API
    # Since the method raises ValueError and TestClient propagates it, we use pytest.raises
    with pytest.raises(ValueError, match="has no kubeconfig"):
        client.get(
            f"/api/v1/sample_platform_models/{svc_id}/test/kubeconfig",
            headers={"X-Project-Id": str(test_project["id"])},
        )
