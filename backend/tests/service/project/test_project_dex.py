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


@pytest.mark.asyncio
async def test_project_install_dex_with_ingress_domain(client):
    cluster = K8sCluster(
        name="test-cluster-dex-ingress",
        title="Test Cluster Dex Ingress",
        type=K8sClusterType.REMOTE,
        kubeconfig="fake-kubeconfig",
    )

    engine = get_engine()
    async with AsyncSession(engine, expire_on_commit=False) as session:
        session.add(cluster)
        await session.commit()
        await session.refresh(cluster)

        project = Project(
            name="test-proj-dex-ingress",
            title="Test Proj Dex Ingress",
            k8s_cluster_id=cluster.id,
            k8s_namespace="test-proj-dex-ingress",
            ingress_domain="ingress.test.local",
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)

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

            # Verify helm was executed, and also kubectl apply was executed
            assert mock_exec.call_count >= 4
            called_values = mock_dump.call_args[0][0]
            assert called_values["config"]["issuer"] == "https://dex.ingress.test.local/dex"

            calls = [call[0] for call in mock_exec.call_args_list]
            found_kubectl = False
            for call_args in calls:
                if "kubectl" in call_args and "apply" in call_args:
                    found_kubectl = True
            assert found_kubectl


@pytest.mark.asyncio
async def test_project_deploy_gateway(client):
    from mindweaver.service.project.actions import DeployGatewayAction

    cluster = K8sCluster(
        name="test-cluster-gw",
        title="Test Cluster GW",
        type=K8sClusterType.REMOTE,
        kubeconfig="fake-kubeconfig",
    )

    engine = get_engine()
    async with AsyncSession(engine, expire_on_commit=False) as session:
        session.add(cluster)
        await session.commit()
        await session.refresh(cluster)

        project = Project(
            name="test-proj-gw",
            title="Test Proj GW",
            k8s_cluster_id=cluster.id,
            k8s_namespace="test-proj-gw",
            ingress_domain="gw.test.local",
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)

        mock_svc = MagicMock()
        mock_svc.session = session
        mock_svc.request = MagicMock()

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.communicate = pytest.importorskip("unittest.mock").AsyncMock(
                return_value=(b"success", b"")
            )
            mock_exec.return_value = mock_proc

            action = DeployGatewayAction(project, mock_svc)
            action.session = session
            await action.run()

            # Verify kubectl was executed to apply gateway resources
            assert mock_exec.call_count >= 1
            calls = [call[0] for call in mock_exec.call_args_list]
            found_kubectl = False
            for call_args in calls:
                if "kubectl" in call_args and "apply" in call_args:
                    found_kubectl = True
            assert found_kubectl


def test_project_deploy_gateway_action_triggers_task(client: TestClient):
    # Create cluster and project with ingress_domain
    cluster_data = client.post(
        "/api/v1/k8s_clusters",
        json={
            "name": "gw-cluster-test",
            "title": "GW Cluster Test",
            "type": "in-cluster",
        },
    ).json()["data"]

    project_data = client.post(
        "/api/v1/projects",
        json={
            "name": "gw-project-test",
            "title": "GW Project Test",
            "k8s_cluster_id": cluster_data["id"],
            "k8s_namespace": "gw-project-test",
            "ingress_domain": "gw-test.domain",
        },
    ).json()["data"]

    with patch(
        "mindweaver.tasks.project_tasks.deploy_gateway_project_task.delay"
    ) as mock_delay:
        resp = client.post(
            f"/api/v1/projects/{project_data['id']}/_actions",
            json={"action": "deploy_gateway"},
        )
        assert resp.status_code == 200
        assert (
            resp.json()["message"]
            == "Project Envoy Gateway deployment triggered."
        )
        mock_delay.assert_called_once_with(project_data["id"])


@pytest.mark.asyncio
async def test_project_deploy_gateway_with_nodeport(client):
    from mindweaver.service.project.actions import DeployGatewayAction

    cluster = K8sCluster(
        name="test-cluster-gw-np",
        title="Test Cluster GW NP",
        type=K8sClusterType.REMOTE,
        kubeconfig="fake-kubeconfig",
    )

    engine = get_engine()
    async with AsyncSession(engine, expire_on_commit=False) as session:
        session.add(cluster)
        await session.commit()
        await session.refresh(cluster)

        project = Project(
            name="test-proj-gw-np",
            title="Test Proj GW NP",
            k8s_cluster_id=cluster.id,
            k8s_namespace="test-proj-gw-np",
            ingress_domain="gw-np.test.local",
            envoy_nodeport=32111,
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)

        mock_svc = MagicMock()
        mock_svc.session = session
        mock_svc.request = MagicMock()

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.communicate = pytest.importorskip("unittest.mock").AsyncMock(
                return_value=(b"success", b"")
            )
            mock_exec.return_value = mock_proc

            action = DeployGatewayAction(project, mock_svc)
            action.session = session
            await action.run()

            # Verify that the generated manifest includes EnvoyProxy and references it in the Gateway
            assert mock_exec.call_count >= 1
            calls = [call[0] for call in mock_exec.call_args_list]
            
            # Find the manifest content applied
            # The manifest string is written to a tempfile, so let's check what was written
            # We can inspect the tempfile content or mock run_kubectl
            # But we can also check the helper directly, or verify via mocking tempfile
            
            # Let's test the helper directly to be extremely clean and robust
            from mindweaver.service.project.actions import _generate_gateway_manifest
            manifest = _generate_gateway_manifest(project, "test-proj-gw-np", 32111)
            assert "EnvoyProxy" in manifest
            assert "project-envoy-proxy-config" in manifest
            assert "nodePort: 32111" in manifest
            assert "infrastructure:" in manifest
            assert "parametersRef:" in manifest


@pytest.mark.asyncio
async def test_project_deploy_gateway_dynamic_nodeport_capture(client):
    from mindweaver.service.project.actions import DeployGatewayAction

    cluster = K8sCluster(
        name="test-cluster-gw-dyn",
        title="Test Cluster GW DYN",
        type=K8sClusterType.REMOTE,
        kubeconfig="fake-kubeconfig",
    )

    engine = get_engine()
    async with AsyncSession(engine, expire_on_commit=False) as session:
        session.add(cluster)
        await session.commit()
        await session.refresh(cluster)

        project = Project(
            name="test-proj-gw-dyn",
            title="Test Proj GW DYN",
            k8s_cluster_id=cluster.id,
            k8s_namespace="test-proj-gw-dyn",
            ingress_domain="gw-dyn.test.local",
            envoy_nodeport=None, # Not set
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)

        mock_svc = MagicMock()
        mock_svc.session = session
        mock_svc.request = MagicMock()

        with patch("asyncio.create_subprocess_exec") as mock_exec, \
             patch("mindweaver.service.project.actions._get_existing_nodeport", return_value=32222) as mock_get_np:
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.communicate = pytest.importorskip("unittest.mock").AsyncMock(
                return_value=(b"success", b"")
            )
            mock_exec.return_value = mock_proc

            action = DeployGatewayAction(project, mock_svc)
            action.session = session
            await action.run()

            # The helper should have been called and the value saved to the DB
            mock_get_np.assert_called_once()
            
            # Fetch the project from the DB again to verify it has been updated
            db_project = await session.get(Project, project.id)
            assert db_project.envoy_nodeport == 32222


def test_download_haproxy_cert_view(client: TestClient):

    # Create cluster and project
    cluster_data = client.post(
        "/api/v1/k8s_clusters",
        json={
            "name": "cert-cluster-test",
            "title": "Cert Cluster Test",
            "type": "in-cluster",
        },
    ).json()["data"]

    project_data = client.post(
        "/api/v1/projects",
        json={
            "name": "cert-project-test",
            "title": "Cert Project Test",
            "k8s_cluster_id": cluster_data["id"],
            "k8s_namespace": "cert-project-test",
            "ingress_domain": "cert-test.domain",
        },
    ).json()["data"]

    # Test secret not found (returns 404)
    with patch("kubernetes.config.load_incluster_config"), \
         patch("kubernetes.config.load_kube_config"), \
         patch("kubernetes.client.CoreV1Api.read_namespaced_secret", side_effect=Exception("Not found")):
        resp = client.get(f"/api/v1/projects/{project_data['id']}/_download-haproxy-cert")
        assert resp.status_code == 404

    # Test successful download
    import base64
    mock_secret = MagicMock()
    mock_secret.data = {
        "tls.crt": base64.b64encode(b"MOCK CERTIFICATE CONTENT").decode("utf-8"),
        "tls.key": base64.b64encode(b"MOCK PRIVATE KEY CONTENT").decode("utf-8"),
    }
    with patch("kubernetes.config.load_incluster_config"), \
         patch("kubernetes.config.load_kube_config"), \
         patch("kubernetes.client.CoreV1Api.read_namespaced_secret", return_value=mock_secret):
        resp = client.get(f"/api/v1/projects/{project_data['id']}/_download-haproxy-cert")
        assert resp.status_code == 200
        assert resp.headers["Content-Disposition"] == f"attachment; filename=envoy-{project_data['name']}.pem"
        assert b"MOCK CERTIFICATE CONTENT" in resp.content
        assert b"MOCK PRIVATE KEY CONTENT" in resp.content



