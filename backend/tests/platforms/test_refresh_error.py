# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from mindweaver.platform_service.pgsql import PgSqlPlatformService


def test_refresh_missing_greenlet_error(client: TestClient, test_project):
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

    # create platform
    model_data = {
        "name": "refresh-pg",
        "title": "Refresh Postgres",
        "project_id": test_project["id"],
        "instances": 3,
        "storage_size": "1Gi",
    }
    resp = client.post(
        "/api/v1/platform/pgsql",
        json=model_data,
        headers={"X-Project-Id": str(test_project["id"])},
    )
    resp.raise_for_status()
    model_id = resp.json()["data"]["id"]

    # Mock poll_status to commit and expire everything
    async def mock_poll_status(self, model):
        await self.session.commit()

    with patch.object(
        PgSqlPlatformService, "poll_status", autospec=True, side_effect=mock_poll_status
    ):
        resp = client.post(
            f"/api/v1/platform/pgsql/{model_id}/_refresh",
            headers={"X-Project-Id": str(test_project["id"])},
        )
        # This is where it should fail if the bug exists
        assert resp.status_code == 200
