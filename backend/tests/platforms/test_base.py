import pytest
from fastapi.testclient import TestClient
from mindweaver.app import app
from mindweaver.platform_service.base import (
    PlatformBase,
    PlatformService,
    PlatformStateBase,
)
from mindweaver.service.k8s_cluster import K8sCluster
from mindweaver.service.project import Project
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
    f"{SamplePlatformService.model_path()}/test/cluster_name",
    tags=["Test"],
)
async def api_test_cluster_name(
    model: Annotated[SamplePlatformModel, Depends(SamplePlatformService.get_model)],
    svc: Annotated[SamplePlatformService, Depends(SamplePlatformService.get_service)],
):
    """Internal endpoint for testing k8s_cluster method"""
    cluster = await svc.k8s_cluster(model)
    return {"cluster_name": cluster.name}


app.include_router(router, prefix="/api/v1")


def test_cluster_service_api(client: TestClient, test_project):
    # 1. Create a K8sCluster
    cluster_data = {
        "name": "test-cluster",
        "title": "Test Cluster",
        "type": "remote",
        "kubeconfig": "test-kubeconfig-content",
        "project_id": test_project["id"],
    }
    resp = client.post(
        "/api/v1/k8s_clusters",
        json=cluster_data,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    cluster_id = resp.json()["data"]["id"]

    # 2. Create a Sample Cluster Service Model
    svc_data = {
        "name": "my-svc",
        "title": "My Service",
        "k8s_cluster_id": cluster_id,
        "project_id": test_project["id"],
    }
    resp = client.post(
        "/api/v1/sample_platform_models",
        json=svc_data,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    svc_id = resp.json()["data"]["id"]

    # 3. Test k8s_cluster retrieval via API
    resp = client.get(
        f"/api/v1/sample_platform_models/{svc_id}/test/cluster_name",
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    assert resp.json()["cluster_name"] == "test-cluster"

    # 4. Test kubeconfig retrieval via API
    resp = client.get(
        f"/api/v1/sample_platform_models/{svc_id}/test/kubeconfig",
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    assert resp.json()["kubeconfig"] == "test-kubeconfig-content"


def test_cluster_service_kubeconfig_missing_api(client: TestClient, test_project):
    # 1. Create a K8sCluster without kubeconfig
    cluster_data = {
        "name": "no-config-cluster",
        "title": "No Config Cluster",
        "type": "remote",
        "kubeconfig": None,
        "project_id": test_project["id"],
    }
    resp = client.post(
        "/api/v1/k8s_clusters",
        json=cluster_data,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    cluster_id = resp.json()["data"]["id"]

    # 2. Create a Sample Cluster Service Model
    svc_data = {
        "name": "bad-svc",
        "title": "Bad Service",
        "k8s_cluster_id": cluster_id,
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
