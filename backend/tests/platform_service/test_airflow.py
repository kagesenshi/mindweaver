# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from mindweaver.app import app
from mindweaver.platform_service.airflow.service import AirflowPlatformService
from mindweaver.platform_service.airflow.model import AirflowPlatform
from mindweaver.crypto import encrypt_password, decrypt_password


def test_airflow_platform_crud(client: TestClient, test_project):
    # 1. Update Project with K8s info
    project_update = {
        "name": test_project["name"],
        "title": test_project["title"],
        "description": test_project["description"],
        "k8s_cluster_id": test_project["k8s_cluster_id"],
        "k8s_cluster_type": "remote",
        "k8s_cluster_kubeconfig": 'apiVersion: v1\nkind: Config\nclusters: []\ncontexts: []\ncurrent-context: ""\nusers: []',
    }
    resp = client.put(
        f"/api/v1/projects/{test_project['id']}",
        json=project_update,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()

    # 1.1 Create pgsql platform (dependency for Airflow)
    pgsql_data = {
        "name": "airflow-db",
        "title": "Airflow PG DB",
        "project_id": test_project["id"],
    }
    resp = client.post(
        "/api/v1/platform/pgsql",
        json=pgsql_data,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    pgsql_id = resp.json()["data"]["id"]

    # 1.2 Create SSH Key
    ssh_data = {
        "name": "airflow-ssh",
        "title": "Airflow SSH",
        "project_id": test_project["id"],
        "algorithm": "rsa",
        "key_size": 4096,
    }
    resp = client.post(
        "/api/v1/ssh_keys",
        json=ssh_data,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()

    # 1.3 Create Git repository with SSH
    git_data = {
        "name": "dags-repo",
        "title": "DAGs Repo",
        "project_id": test_project["id"],
        "url": "git@github.com:myorg/dags.git",
        "ssh_key_id": resp.json()["data"]["id"],
    }
    resp = client.post(
        "/api/v1/git_repos",
        json=git_data,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    git_repo_id = resp.json()["data"]["id"]

    # 2. Create Airflow Platform referencing the Git Repo
    airflow_data = {
        "name": "my-airflow",
        "title": "My Airflow",
        "project_id": test_project["id"],
        "platform_pgsql_id": pgsql_id,
        "dags_git_sync_enabled": True,
        "git_repo_id": git_repo_id,
    }
    resp = client.post(
        "/api/v1/platform/airflow",
        json=airflow_data,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    airflow_id = resp.json()["data"]["id"]
    assert resp.json()["data"]["git_repo_id"] == git_repo_id

    # 3. Read
    resp = client.get(
        f"/api/v1/platform/airflow/{airflow_id}",
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    assert resp.json()["data"]["git_repo_id"] == git_repo_id

    # 4. Update
    update_data = {
        "name": "my-airflow",
        "title": "My Airflow Updated",
        "project_id": test_project["id"],
        "platform_pgsql_id": pgsql_id,
        "dags_git_sync_enabled": True,
        "git_repo_id": git_repo_id,
        "dags_git_branch": "develop",
    }
    resp = client.put(
        f"/api/v1/platform/airflow/{airflow_id}",
        json=update_data,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    assert resp.json()["data"]["title"] == "My Airflow Updated"
    assert resp.json()["data"]["dags_git_branch"] == "develop"

    # 5. Delete
    resp = client.delete(
        f"/api/v1/platform/airflow/{airflow_id}",
        headers={
            "X-Project-Id": str(test_project["id"]),
            "X-RESOURCE-NAME": "my-airflow",
        },
    )
    resp.raise_for_status()


def test_airflow_platform_git_repo_validation(client: TestClient, test_project):
    # 1. Update Project with K8s info
    project_update = {
        "name": test_project["name"],
        "title": test_project["title"],
        "description": test_project["description"],
        "k8s_cluster_id": test_project["k8s_cluster_id"],
        "k8s_cluster_type": "remote",
        "k8s_cluster_kubeconfig": 'apiVersion: v1\nkind: Config\nclusters: []\ncontexts: []\ncurrent-context: ""\nusers: []',
    }
    resp = client.put(
        f"/api/v1/projects/{test_project['id']}",
        json=project_update,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()

    # Create project 2 programmatically
    proj2_data = {
        "name": "project-2",
        "title": "Project 2",
        "description": "Another test project",
        "k8s_cluster_id": test_project["k8s_cluster_id"],
    }
    resp = client.post("/api/v1/projects", json=proj2_data)
    resp.raise_for_status()
    project_2 = resp.json()["data"]

    # 1.1 Setup PG DB in project 1
    pgsql_data = {
        "name": "airflow-db-val",
        "title": "Airflow PG DB Validation",
        "project_id": test_project["id"],
    }
    resp = client.post(
        "/api/v1/platform/pgsql",
        json=pgsql_data,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    pgsql_id = resp.json()["data"]["id"]

    # 2. Setup GitRepo in project 2 (cross-project)
    git_data = {
        "name": "dags-repo-cross",
        "title": "DAGs Repo Cross",
        "project_id": project_2["id"],
        "url": "https://github.com/myorg/dags.git",
        "username": "user",
        "password": "pwd",
    }
    resp = client.post(
        "/api/v1/git_repos",
        json=git_data,
        headers={"X-Project-Id": str(project_2["id"])},
    )
    resp.raise_for_status()
    cross_git_repo_id = resp.json()["data"]["id"]

    # 3. Try to create Airflow in project 1 referencing GitRepo from project 2
    airflow_data = {
        "name": "my-airflow-cross",
        "title": "My Airflow Cross",
        "project_id": test_project["id"],
        "platform_pgsql_id": pgsql_id,
        "dags_git_sync_enabled": True,
        "git_repo_id": cross_git_repo_id,
    }
    resp = client.post(
        "/api/v1/platform/airflow",
        json=airflow_data,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    assert resp.status_code == 422
    assert "belongs to another project" in resp.json()["detail"][0]["msg"]


@pytest.mark.asyncio
async def test_airflow_template_vars_git_sync(client: TestClient, test_project):
    # Mock services/DB calls for template_vars test
    from mindweaver.platform_service.airflow.service import AirflowPlatformService
    from mindweaver.service.git_repo.model import GitRepo
    from mindweaver.service.ssh_key.model import SSHKey
    from mindweaver.platform_service.pgsql.model import PgSqlPlatform, PgSqlPlatformState
    from mindweaver.service.project.model import Project

    mock_request = MagicMock()
    mock_request.headers = {"X-Project-Id": str(test_project["id"])}
    mock_session = AsyncMock()

    # Create mock pgsql service, pgsql platform, pgsql state, project
    mock_pgsql = PgSqlPlatform(id=1, name="my-pgsql", project_id=test_project["id"])
    mock_pgsql_state = PgSqlPlatformState(
        platform_id=1,
        active=True,
        db_user="app",
        db_name="app",
        db_pass=encrypt_password("secret_pass"),
        extra_data={"pgbouncer_host": "pgbouncer-host"},
    )
    mock_project = Project(id=test_project["id"], name="test-proj", ingress_domain="test.domain")

    # Mock services
    svc = AirflowPlatformService(mock_request, mock_session)
    svc._resolve_namespace = AsyncMock(return_value="airflow-ns")
    svc.project = AsyncMock(return_value=mock_project)

    # Mock foreign key resolution dependencies
    mock_pgsql_svc = MagicMock()
    mock_pgsql_svc.get = AsyncMock(return_value=mock_pgsql)
    mock_pgsql_svc.platform_state = AsyncMock(return_value=mock_pgsql_state)

    # Inject mock service getters
    from mindweaver.platform_service.pgsql.service import PgSqlPlatformService
    from mindweaver.service.git_repo.service import GitRepoService
    from mindweaver.service.ssh_key.service import SSHKeyService

    # Setup Airflow model
    airflow_model = AirflowPlatform(
        name="test-airflow",
        title="Test Airflow",
        project_id=test_project["id"],
        platform_pgsql_id=1,
        dags_git_sync_enabled=True,
        git_repo_id=10,
        dags_git_branch="main",
        dags_git_subpath="dags",
    )

    # 1. Test Git Repo with Username/Password
    mock_git_repo = GitRepo(
        id=10,
        name="my-http-repo",
        project_id=test_project["id"],
        url="https://github.com/org/repo.git",
        username="git-username",
        password=encrypt_password("git-token"),
    )
    mock_git_svc = MagicMock()
    mock_git_svc.get = AsyncMock(return_value=mock_git_repo)

    async def get_service_mock(req, sess):
        if req == mock_request and sess == mock_session:
            return mock_pgsql_svc
        return MagicMock()

    async def get_service_git_mock(req, sess):
        return mock_git_svc

    with patch.object(PgSqlPlatformService, "get_service", new=get_service_mock), \
         patch.object(GitRepoService, "get_service", new=get_service_git_mock):
        vars_res = await svc.template_vars(airflow_model)
        assert vars_res["dags_git_sync_enabled"] is True
        assert vars_res["dags_git_repo"] == "https://github.com/org/repo.git"
        assert vars_res["git_repo"]["username"] == "git-username"
        assert vars_res["git_repo"]["password"] == "git-token"
        assert vars_res["ssh_key"] is None

    # 2. Test Git Repo with SSH Key
    mock_git_repo_ssh = GitRepo(
        id=10,
        name="my-ssh-repo",
        project_id=test_project["id"],
        url="git@github.com:org/repo.git",
        ssh_key_id=20,
    )
    mock_git_svc.get = AsyncMock(return_value=mock_git_repo_ssh)

    mock_ssh_key = SSHKey(
        id=20,
        name="my-key",
        project_id=test_project["id"],
        private_key=encrypt_password("ssh-private-key-data"),
        public_key="ssh-rsa-pubkey",
    )
    mock_ssh_svc = MagicMock()
    mock_ssh_svc.get = AsyncMock(return_value=mock_ssh_key)

    async def get_service_ssh_mock(req, sess):
        return mock_ssh_svc

    with patch.object(PgSqlPlatformService, "get_service", new=get_service_mock), \
         patch.object(GitRepoService, "get_service", new=get_service_git_mock), \
         patch.object(SSHKeyService, "get_service", new=get_service_ssh_mock):
        vars_res = await svc.template_vars(airflow_model)
        assert vars_res["dags_git_sync_enabled"] is True
        assert vars_res["dags_git_repo"] == "git@github.com:org/repo.git"
        assert vars_res["ssh_key"]["private_key"] == "ssh-private-key-data"
        assert vars_res["ssh_key"]["public_key"] == "ssh-rsa-pubkey"
