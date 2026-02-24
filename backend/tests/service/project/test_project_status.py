# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from unittest.mock import MagicMock, patch, call
from fastapi.testclient import TestClient
from sqlmodel import select, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from mindweaver.service.project.model import ProjectStatus
from mindweaver.config import settings


@pytest.fixture
def mock_k8s():
    with patch(
        "mindweaver.service.project.service.config.load_incluster_config"
    ), patch("mindweaver.service.project.service.client.CoreV1Api") as mock_core, patch(
        "mindweaver.service.project.service.client.VersionApi"
    ) as mock_version:

        # Mock Version
        mock_v = MagicMock()
        mock_v.git_version = "v1.27.0"
        mock_version.return_value.get_code.return_value = mock_v

        # Mock Nodes
        mock_node = MagicMock()
        mock_node.metadata.name = "node-1"
        mock_node.status.conditions = [MagicMock(type="Ready", status="True")]
        mock_node.status.capacity = {"cpu": "2", "memory": "4Gi"}

        mock_nodes_list = MagicMock()
        mock_nodes_list.items = [mock_node]
        mock_core.return_value.list_node.return_value = mock_nodes_list

        # Mock Services (ArgoCD)
        mock_svc = MagicMock()
        mock_svc.metadata.name = "argocd-server"
        mock_svc_list = MagicMock()
        mock_svc_list.items = [mock_svc]
        mock_core.return_value.list_service_for_all_namespaces.return_value = (
            mock_svc_list
        )

        # Mock Pods (ArgoCD version)
        mock_pod = MagicMock()
        mock_pod.metadata.labels = {"app.kubernetes.io/version": "v2.8.0"}
        mock_pod_list = MagicMock()
        mock_pod_list.items = [mock_pod]
        mock_core.return_value.list_pod_for_all_namespaces.return_value = mock_pod_list

        # Mock Secrets (Helm Release)
        mock_secret = MagicMock()
        mock_secret.metadata.name = "sh.helm.release.v1.argocd.v1"
        mock_secret_list = MagicMock()
        mock_secret_list.items = [mock_secret]
        mock_core.return_value.list_secret_for_all_namespaces.return_value = (
            mock_secret_list
        )

        yield {"core": mock_core, "version": mock_version}


def test_poll_project_status(client: TestClient, mock_k8s):
    # Create project
    p1 = client.post(
        "/api/v1/projects",
        json={
            "name": "poll-test",
            "title": "Poll Test",
            "k8s_cluster_type": "in-cluster",
        },
    ).json()["data"]

    # Trigger refresh
    resp = client.post(f"/api/v1/projects/{p1['id']}/_refresh")
    assert resp.status_code == 200

    # Check state
    resp_state = client.get(f"/api/v1/projects/{p1['id']}/_state")
    assert resp_state.status_code == 200
    data = resp_state.json()

    cluster = data["cluster"]
    assert cluster["status"] == "online"
    assert cluster["k8s_version"] == "v1.27.0"
    assert cluster["node_count"] == 1
    assert cluster["cpu_total"] == 2.0
    assert cluster["ram_total"] == 4.0
    assert cluster["argocd_installed"] is True
    assert cluster["argocd_version"] == "v2.8.0"


@pytest.mark.asyncio
async def test_install_argocd(postgresql_proc, test_project):
    from mindweaver.service.project.service import ProjectService
    from mindweaver.service.project.model import Project, K8sClusterType

    settings.db_host = postgresql_proc.host
    settings.db_port = postgresql_proc.port
    settings.db_name = postgresql_proc.dbname
    settings.db_user = postgresql_proc.user
    settings.db_pass = postgresql_proc.password
    settings.fernet_key = "EFw4cCjDgHhGuZAGlwXmQhXg134ZdHjb9SeqcszWeSU="

    engine = create_async_engine(settings.db_async_uri)

    async with AsyncSession(engine) as session:
        project_id = test_project["id"]
        # Reload project in current session
        project = await session.get(Project, project_id)
        project.k8s_cluster_type = K8sClusterType.REMOTE
        project.k8s_cluster_kubeconfig = "fake-kubeconfig"
        session.add(project)
        await session.commit()
        await session.refresh(project)

        class MockRequest:
            headers = {}

        svc = ProjectService(MockRequest(), session)

        from mindweaver.service.project.actions import InstallArgoCDAction

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.communicate = pytest.importorskip("unittest.mock").AsyncMock(
                return_value=(b"success", b"")
            )
            mock_exec.return_value = mock_proc

            action = InstallArgoCDAction(project, svc)
            await action.run()

            # Verify helm repo add
            # Verify helm upgrade --install
            assert mock_exec.call_count >= 3  # add, update, upgrade

            calls = [call[0] for call in mock_exec.call_args_list]
            found_upgrade = False
            for call_args in calls:
                if "upgrade" in call_args and "--install" in call_args:
                    found_upgrade = True
                    assert "argocd" in call_args
                    assert "argo/argo-cd" in call_args
                    assert "--kubeconfig" in call_args

            assert found_upgrade


def test_poll_project_status_error(client: TestClient):

    with patch(
        "mindweaver.service.project.service.config.load_incluster_config",
        side_effect=Exception("K8S Error"),
    ):
        # Create project
        p1 = client.post(
            "/api/v1/projects",
            json={
                "name": "error-test",
                "title": "Error Test",
                "k8s_cluster_type": "in-cluster",
            },
        ).json()["data"]

        # Trigger refresh
        client.post(f"/api/v1/projects/{p1['id']}/_refresh")

        # Check state
        resp_state = client.get(f"/api/v1/projects/{p1['id']}/_state")
        data = resp_state.json()
        assert data["cluster"]["status"] == "error"
        assert data["cluster"]["message"] == "K8S Error"


def test_install_argocd_action_triggers_task(client: TestClient):
    # Create project
    p1 = client.post(
        "/api/v1/projects",
        json={
            "name": "task-test",
            "title": "Task Test",
            "k8s_cluster_type": "in-cluster",
        },
    ).json()["data"]

    with patch(
        "mindweaver.tasks.project_status.install_argocd_task.delay"
    ) as mock_delay:
        resp = client.post(
            f"/api/v1/projects/{p1['id']}/_actions", json={"action": "install_argocd"}
        )
        assert resp.status_code == 200
        assert (
            resp.json()["message"]
            == "ArgoCD installation triggered and status being refreshed."
        )
        mock_delay.assert_called_once_with(p1["id"])

        # Verify status updated immediately in DB
        resp_state = client.get(f"/api/v1/projects/{p1['id']}/_state")
        assert resp_state.json()["cluster"]["argocd_installed"] is True
