# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from mindweaver.service.k8s_cluster.model import K8sCluster, K8sClusterType
from mindweaver.service.project.model import Project
from mindweaver.service.project_user.model import ProjectLocalUser
from mindweaver.service.ldap_config.model import LdapConfig
from mindweaver.service.project.actions import InstallDexAction
from mindweaver.fw.model import get_engine
from sqlmodel.ext.asyncio.session import AsyncSession


@pytest.mark.asyncio
async def test_project_install_dex(client):
    cluster = K8sCluster(
        name="test-cluster-dex-proj",
        title="Test Cluster Dex Proj",
        type=K8sClusterType.REMOTE,
        kubeconfig="fake-kubeconfig",
    )

    engine = get_engine()
    async with AsyncSession(engine, expire_on_commit=False) as session:
        session.add(cluster)
        await session.commit()
        await session.refresh(cluster)

        ldap = LdapConfig(
            name="test-ldap-proj",
            title="Test LDAP Proj",
            server_url="ldap://ldap-proj.example.com",
            user_search_base="ou=users,dc=example,dc=com",
            user_search_filter="(uid={0})",
            username_attr="uid",
        )
        session.add(ldap)
        await session.commit()
        await session.refresh(ldap)

        project = Project(
            name="test-proj-dex",
            title="Test Proj Dex",
            k8s_cluster_id=cluster.id,
            ldap_config_id=ldap.id,
            k8s_namespace="test-proj-dex",
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)

        user = ProjectLocalUser(
            project_id=project.id,
            username="localuser-proj",
            email="local-proj@example.com",
            password_hash_bcrypt="bcrypt_hash_val_proj",
            password_hash_md5="md5_hash_val_proj",
            password_hash_sha256="sha256_hash_val_proj",
            password_hash_sha512="sha512_hash_val_proj",
        )
        session.add(user)
        await session.commit()

        mock_svc = MagicMock()
        mock_svc.session = session
        mock_svc.request = MagicMock()

        with patch("asyncio.create_subprocess_exec") as mock_exec, patch("yaml.safe_dump") as mock_dump:
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.communicate = pytest.importorskip("unittest.mock").AsyncMock(
                return_value=(b"success", b"")
            )
            mock_exec.return_value = mock_proc

            action = InstallDexAction(project, mock_svc)
            action.session = session
            await action.run()

            assert mock_exec.call_count >= 3
            mock_dump.assert_called_once()
            called_values = mock_dump.call_args[0][0]
            assert called_values["config"]["enablePasswordDB"] is True
            assert called_values["config"]["staticPasswords"][0]["username"] == "localuser-proj"
            assert called_values["config"]["staticPasswords"][0]["hash"] == "bcrypt_hash_val_proj"
            assert called_values["config"]["connectors"][0]["type"] == "ldap"
            assert called_values["config"]["connectors"][0]["config"]["host"] == "ldap-proj.example.com:389"


def test_project_install_dex_action_triggers_task(client: TestClient):
    # Create cluster and project
    cluster_data = client.post(
        "/api/v1/k8s_clusters",
        json={
            "name": "dex-cluster-test",
            "title": "Dex Cluster Test",
            "type": "in-cluster",
        },
    ).json()["data"]

    project_data = client.post(
        "/api/v1/projects",
        json={
            "name": "dex-project-test",
            "title": "Dex Project Test",
            "k8s_cluster_id": cluster_data["id"],
            "k8s_namespace": "dex-project-test",
        },
    ).json()["data"]

    with patch(
        "mindweaver.tasks.project_tasks.install_dex_project_task.delay"
    ) as mock_delay:
        resp = client.post(
            f"/api/v1/projects/{project_data['id']}/_actions",
            json={"action": "install_dex"},
        )
        assert resp.status_code == 200
        assert (
            resp.json()["message"]
            == "Dex installation triggered for this project namespace."
        )
        mock_delay.assert_called_once_with(project_data["id"])
