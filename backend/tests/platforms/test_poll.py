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
from mindweaver.service.project import K8sClusterType


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
        from mindweaver.service.project import Project
        db_project = await session.get(Project, project_id)
        db_project.k8s_cluster_type = K8sClusterType.REMOTE
        db_project.k8s_cluster_kubeconfig = "apiVersion: v1\nkind: Config"
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
