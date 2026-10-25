# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from unittest.mock import patch, MagicMock
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from mindweaver.config import settings
from mindweaver.platform_service.pgsql import (
    PgSqlPlatformService,
    PgSqlPlatform,
    PgSqlPlatformState,
)
from mindweaver.service.project import Project
from mindweaver.service.k8s_cluster import K8sCluster, K8sClusterType


@pytest.mark.asyncio
async def test_pgsql_poll_status(postgresql_proc, test_project):
    # Setup test database settings for async
    settings.db_host = postgresql_proc.host
    settings.db_port = postgresql_proc.port
    settings.db_name = postgresql_proc.dbname
    settings.db_user = postgresql_proc.user
    settings.db_pass = postgresql_proc.password
    settings.fernet_key = "EFw4cCjDgHhGuZAGlwXmQhXg134ZdHjb9SeqcszWeSU="

    engine = create_async_engine(settings.db_async_uri)

    async with AsyncSession(engine) as session:
        # 1. Update project with K8s info
        project_id = test_project["id"]
        # In this test, test_project is a dict from fixture, but we need to update it in DB
        # However, the fixture usually handles session. Let's just update the model.
        cluster = K8sCluster(
            name="test-cluster-poll",
            title="Test Cluster Poll",
            type=K8sClusterType.REMOTE,
            kubeconfig="apiVersion: v1\nkind: Config",
        )
        session.add(cluster)
        await session.flush()

        from mindweaver.service.project import Project

        db_project = await session.get(Project, project_id)
        db_project.k8s_cluster_id = cluster.id
        session.add(db_project)
        await session.commit()

        # 2. Setup PgSqlPlatform
        platform = PgSqlPlatform(
            name="test-pg-poll",
            title="Test PG Poll",
            project_id=project_id,
        )
        session.add(platform)
        await session.commit()
        await session.refresh(platform)
        platform_id = platform.id

        # 3. Mock Kubernetes API
        with patch("kubernetes.client.CustomObjectsApi") as mock_custom_api, patch(
            "kubernetes.client.CoreV1Api"
        ) as mock_core_v1, patch("kubernetes.config.new_client_from_config"):

            # Mock CNPG Cluster status
            mock_custom_api.return_value.get_namespaced_custom_object.return_value = {
                "status": {
                    "phase": "Cluster in healthy state",
                    "instances": 3,
                    "readyInstances": 3,
                }
            }

            # Mock Service list for NodePort
            mock_svc = MagicMock()
            mock_svc.metadata.name = "test-pg-poll-rw"
            mock_svc.spec.type = "NodePort"
            mock_svc.spec.ports = [MagicMock(port=5432, node_port=30432)]

            mock_core_v1.return_value.list_namespaced_service.return_value.items = [
                mock_svc
            ]

            # 4. Execute poll_status
            class MockRequest:
                headers = {}

            svc = PgSqlPlatformService(MockRequest(), session)
            await svc.poll_status(platform)

            # 5. Verify database update
            stmt = select(PgSqlPlatformState).where(
                PgSqlPlatformState.platform_id == platform_id
            )
            result = await session.exec(stmt)
            state = result.one()

            assert state.status == "online"
            assert "Instances: 3/3" in state.message
            assert state.node_ports[0]["node_port"] == 30432
            assert state.last_heartbeat is not None


@pytest.mark.asyncio
async def test_pgsql_poll_status_cluster_unreachable(postgresql_proc, test_project):
    """Test that when k8s cluster is unreachable, poll_status marks platform as error."""
    settings.db_host = postgresql_proc.host
    settings.db_port = postgresql_proc.port
    settings.db_name = postgresql_proc.dbname
    settings.db_user = postgresql_proc.user
    settings.db_pass = postgresql_proc.password
    settings.fernet_key = "EFw4cCjDgHhGuZAGlwXmQhXg134ZdHjb9SeqcszWeSU="

    engine = create_async_engine(settings.db_async_uri)

    async with AsyncSession(engine) as session:
        project_id = test_project["id"]
        cluster = K8sCluster(
            name="test-cluster-unreach",
            title="Test Cluster Unreachable",
            type=K8sClusterType.REMOTE,
            kubeconfig="apiVersion: v1\nkind: Config",
        )
        session.add(cluster)
        await session.flush()

        from mindweaver.service.project import Project
        db_project = await session.get(Project, project_id)
        db_project.k8s_cluster_id = cluster.id
        session.add(db_project)
        await session.commit()

        platform = PgSqlPlatform(
            name="test-pg-unreach",
            title="Test PG Unreach",
            project_id=project_id,
        )
        session.add(platform)
        await session.flush()
        platform_id = platform.id
        await session.commit()

        # Pre-populate state as online
        state = PgSqlPlatformState(
            platform_id=platform_id,
            status="online",
            active=True,
            message="Running",
        )
        session.add(state)
        await session.commit()

        # Mock custom api failing with connection error
        with patch("kubernetes.client.CustomObjectsApi") as mock_custom_api, \
             patch("kubernetes.config.new_client_from_config"):
            mock_custom_api.return_value.get_namespaced_custom_object.side_effect = Exception("Connection timed out")

            class MockRequest:
                headers = {}

            svc = PgSqlPlatformService(MockRequest(), session)
            model = await session.get(PgSqlPlatform, platform_id)
            await svc.poll_status(model)

            stmt = select(PgSqlPlatformState).where(
                PgSqlPlatformState.platform_id == platform_id
            )
            res = await session.exec(stmt)
            updated_state = res.one()

            assert updated_state.status == "error"
            assert "unreachable" in updated_state.message.lower()
