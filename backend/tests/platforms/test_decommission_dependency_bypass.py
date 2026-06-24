# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def mock_k8s_config():
    """Mock kubernetes config loading globally for these tests to avoid parsing dummy kubeconfig."""
    with patch("kubernetes.config.new_client_from_config") as mock_new_client, \
         patch("kubernetes.config.load_incluster_config") as mock_load_incluster, \
         patch("kubernetes.client.ApiClient") as mock_api_client:
        yield


@pytest.fixture(autouse=True)
def setup_project_kubeconfig(client: TestClient, test_project, test_cluster):
    """Ensure the test project and cluster have a valid structure for kubeconfig."""
    cluster_update = {
        "name": test_cluster["name"],
        "title": test_cluster["title"],
        "type": "remote",
        "kubeconfig": 'apiVersion: v1\nkind: Config\nclusters: []\ncontexts: []\ncurrent-context: ""\nusers: []',
    }
    resp = client.put(
        f"/api/v1/k8s_clusters/{test_cluster['id']}",
        json=cluster_update,
    )
    resp.raise_for_status()

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
        headers={"X-Project-Id": str(test_project['id'])},
    )
    resp.raise_for_status()


def test_airflow_decommission_dependency_inactive(client: TestClient, test_project):
    """Test that Airflow decommissioning succeeds when PostgreSQL dependency is inactive."""
    with patch("mindweaver.platform_service.base.PlatformService._deploy_to_cluster"), \
         patch("mindweaver.platform_service.base.PlatformService._decommission_from_cluster"), \
         patch("mindweaver.platform_service.pgsql.service.PgSqlPlatformService.poll_status"), \
         patch("mindweaver.platform_service.airflow.service.AirflowPlatformService.poll_status"):

        # 1. Create PostgreSQL dependency
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

        # Set PostgreSQL state to active=False (inactive)
        resp = client.post(
            f"/api/v1/platform/pgsql/{pgsql_id}/_state",
            json={"status": "offline", "active": False},
            headers={
                "X-Project-Id": str(test_project["id"]),
                "X-RESOURCE-NAME": "airflow-db",
            },
        )
        resp.raise_for_status()

        # Create Airflow Platform referencing the inactive PostgreSQL
        airflow_data = {
            "name": "my-airflow",
            "title": "My Airflow",
            "project_id": test_project["id"],
            "platform_pgsql_id": pgsql_id,
        }
        resp = client.post(
            "/api/v1/platform/airflow",
            json=airflow_data,
            headers={"X-Project-Id": str(test_project["id"])},
        )
        resp.raise_for_status()
        airflow_id = resp.json()["data"]["id"]

        # Try to deploy Airflow -> should fail because PG is inactive
        with pytest.raises(ValueError, match="is not active"):
            client.post(
                f"/api/v1/platform/airflow/{airflow_id}/_deploy",
                headers={"X-Project-Id": str(test_project["id"])},
            )

        # Decommission Airflow -> should succeed because dependencies check is bypassed during decommissioning
        resp = client.post(
            f"/api/v1/platform/airflow/{airflow_id}/_decommission",
            headers={
                "X-Project-Id": str(test_project["id"]),
                "X-RESOURCE-NAME": "my-airflow",
            },
        )
        assert resp.status_code == 200


def test_hms_decommission_dependency_inactive(client: TestClient, test_project):
    """Test that Hive Metastore decommissioning succeeds when PostgreSQL dependency is inactive."""
    with patch("mindweaver.platform_service.base.PlatformService._deploy_to_cluster"), \
         patch("mindweaver.platform_service.base.PlatformService._decommission_from_cluster"), \
         patch("mindweaver.platform_service.pgsql.service.PgSqlPlatformService.poll_status"), \
         patch("mindweaver.platform_service.hive_metastore.service.HiveMetastorePlatformService.poll_status"):

        # 1. Create PostgreSQL dependency
        pgsql_data = {
            "name": "hms-db",
            "title": "HMS PG DB",
            "project_id": test_project["id"],
        }
        resp = client.post(
            "/api/v1/platform/pgsql",
            json=pgsql_data,
            headers={"X-Project-Id": str(test_project["id"])},
        )
        resp.raise_for_status()
        pgsql_id = resp.json()["data"]["id"]

        # Set PostgreSQL state to active=False
        resp = client.post(
            f"/api/v1/platform/pgsql/{pgsql_id}/_state",
            json={"status": "offline", "active": False},
            headers={
                "X-Project-Id": str(test_project["id"]),
                "X-RESOURCE-NAME": "hms-db",
            },
        )
        resp.raise_for_status()

        # Create Hive Metastore Platform
        hms_data = {
            "name": "my-hms",
            "title": "My HMS",
            "project_id": test_project["id"],
            "database_id": pgsql_id,
        }
        resp = client.post(
            "/api/v1/platform/hive-metastore",
            json=hms_data,
            headers={"X-Project-Id": str(test_project["id"])},
        )
        resp.raise_for_status()
        hms_id = resp.json()["data"]["id"]

        # Deploy Hive Metastore -> should fail
        with pytest.raises(ValueError, match="is not active"):
            client.post(
                f"/api/v1/platform/hive-metastore/{hms_id}/_deploy",
                headers={"X-Project-Id": str(test_project["id"])},
            )

        # Decommission Hive Metastore -> should succeed
        resp = client.post(
            f"/api/v1/platform/hive-metastore/{hms_id}/_decommission",
            headers={
                "X-Project-Id": str(test_project["id"]),
                "X-RESOURCE-NAME": "my-hms",
            },
        )
        assert resp.status_code == 200


def test_ranger_decommission_dependency_inactive(client: TestClient, test_project):
    """Test that Ranger decommissioning succeeds when PostgreSQL and Solr dependencies are inactive."""
    with patch("mindweaver.platform_service.base.PlatformService._deploy_to_cluster"), \
         patch("mindweaver.platform_service.base.PlatformService._decommission_from_cluster"), \
         patch("mindweaver.platform_service.pgsql.service.PgSqlPlatformService.poll_status"), \
         patch("mindweaver.platform_service.solr.service.SolrPlatformService.poll_status"), \
         patch("mindweaver.platform_service.ranger.service.RangerPlatformService.poll_status"):

        # 1. Create PostgreSQL dependency
        pgsql_data = {
            "name": "ranger-db",
            "title": "Ranger PG DB",
            "project_id": test_project["id"],
        }
        resp = client.post(
            "/api/v1/platform/pgsql",
            json=pgsql_data,
            headers={"X-Project-Id": str(test_project["id"])},
        )
        resp.raise_for_status()
        pgsql_id = resp.json()["data"]["id"]

        resp = client.post(
            f"/api/v1/platform/pgsql/{pgsql_id}/_state",
            json={"status": "offline", "active": False},
            headers={
                "X-Project-Id": str(test_project["id"]),
                "X-RESOURCE-NAME": "ranger-db",
            },
        )
        resp.raise_for_status()

        # 2. Create Solr dependency
        solr_data = {
            "name": "ranger-solr",
            "title": "Ranger Solr",
            "project_id": test_project["id"],
        }
        resp = client.post(
            "/api/v1/platform/solr",
            json=solr_data,
            headers={"X-Project-Id": str(test_project["id"])},
        )
        resp.raise_for_status()
        solr_id = resp.json()["data"]["id"]

        resp = client.post(
            f"/api/v1/platform/solr/{solr_id}/_state",
            json={"status": "offline", "active": False},
            headers={
                "X-Project-Id": str(test_project["id"]),
                "X-RESOURCE-NAME": "ranger-solr",
            },
        )
        resp.raise_for_status()

        # Create Ranger Platform
        ranger_data = {
            "name": "my-ranger",
            "title": "My Ranger",
            "project_id": test_project["id"],
            "database_id": pgsql_id,
            "solr_id": solr_id,
        }
        resp = client.post(
            "/api/v1/platform/ranger",
            json=ranger_data,
            headers={"X-Project-Id": str(test_project["id"])},
        )
        resp.raise_for_status()
        ranger_id = resp.json()["data"]["id"]

        # Deploy Ranger -> should fail
        with pytest.raises(ValueError, match="is not active"):
            client.post(
                f"/api/v1/platform/ranger/{ranger_id}/_deploy",
                headers={"X-Project-Id": str(test_project["id"])},
            )

        # Decommission Ranger -> should succeed
        resp = client.post(
            f"/api/v1/platform/ranger/{ranger_id}/_decommission",
            headers={
                "X-Project-Id": str(test_project["id"]),
                "X-RESOURCE-NAME": "my-ranger",
            },
        )
        assert resp.status_code == 200


def test_trino_decommission_dependency_inactive(client: TestClient, test_project):
    """Test that Trino decommissioning succeeds when Hive Metastore and Solr dependencies are inactive."""
    with patch("mindweaver.platform_service.base.PlatformService._deploy_to_cluster"), \
         patch("mindweaver.platform_service.base.PlatformService._decommission_from_cluster"), \
         patch("mindweaver.platform_service.pgsql.service.PgSqlPlatformService.poll_status"), \
         patch("mindweaver.platform_service.hive_metastore.service.HiveMetastorePlatformService.poll_status"), \
         patch("mindweaver.platform_service.solr.service.SolrPlatformService.poll_status"), \
         patch("mindweaver.platform_service.trino.service.TrinoPlatformService.poll_status"):

        # 1. Create Hive Metastore dependency
        # First we need pgsql for HMS
        pgsql_data = {
            "name": "trino-hms-db",
            "title": "Trino HMS PG DB",
            "project_id": test_project["id"],
        }
        resp = client.post(
            "/api/v1/platform/pgsql",
            json=pgsql_data,
            headers={"X-Project-Id": str(test_project["id"])},
        )
        resp.raise_for_status()
        pgsql_id = resp.json()["data"]["id"]

        # Set PostgreSQL state to active=True so we can create HMS
        resp = client.post(
            f"/api/v1/platform/pgsql/{pgsql_id}/_state",
            json={"status": "online", "active": True},
            headers={
                "X-Project-Id": str(test_project["id"]),
                "X-RESOURCE-NAME": "trino-hms-db",
            },
        )
        resp.raise_for_status()

        hms_data = {
            "name": "trino-hms",
            "title": "Trino HMS",
            "project_id": test_project["id"],
            "database_id": pgsql_id,
        }
        resp = client.post(
            "/api/v1/platform/hive-metastore",
            json=hms_data,
            headers={"X-Project-Id": str(test_project["id"])},
        )
        resp.raise_for_status()
        hms_id = resp.json()["data"]["id"]

        # Set HMS state to active=False
        resp = client.post(
            f"/api/v1/platform/hive-metastore/{hms_id}/_state",
            json={"status": "offline", "active": False},
            headers={
                "X-Project-Id": str(test_project["id"]),
                "X-RESOURCE-NAME": "trino-hms",
            },
        )
        resp.raise_for_status()

        # 2. Create Solr dependency
        solr_data = {
            "name": "trino-solr",
            "title": "Trino Solr",
            "project_id": test_project["id"],
        }
        resp = client.post(
            "/api/v1/platform/solr",
            json=solr_data,
            headers={"X-Project-Id": str(test_project["id"])},
        )
        resp.raise_for_status()
        solr_id = resp.json()["data"]["id"]

        resp = client.post(
            f"/api/v1/platform/solr/{solr_id}/_state",
            json={"status": "offline", "active": False},
            headers={
                "X-Project-Id": str(test_project["id"]),
                "X-RESOURCE-NAME": "trino-solr",
            },
        )
        resp.raise_for_status()

        # Create Trino Platform
        trino_data = {
            "name": "my-trino",
            "title": "My Trino",
            "project_id": test_project["id"],
            "hms_ids": [hms_id],
            "solr_id": solr_id,
        }
        resp = client.post(
            "/api/v1/platform/trino",
            json=trino_data,
            headers={"X-Project-Id": str(test_project["id"])},
        )
        resp.raise_for_status()
        trino_id = resp.json()["data"]["id"]

        # Deploy Trino -> should fail
        with pytest.raises(ValueError, match="is not active"):
            client.post(
                f"/api/v1/platform/trino/{trino_id}/_deploy",
                headers={"X-Project-Id": str(test_project["id"])},
            )

        # Decommission Trino -> should succeed
        resp = client.post(
            f"/api/v1/platform/trino/{trino_id}/_decommission",
            headers={
                "X-Project-Id": str(test_project["id"]),
                "X-RESOURCE-NAME": "my-trino",
            },
        )
        assert resp.status_code == 200


def test_superset_decommission_dependency_inactive(client: TestClient, test_project):
    """Test that Superset decommissioning succeeds when PostgreSQL dependency is inactive."""
    with patch("mindweaver.platform_service.base.PlatformService._deploy_to_cluster"), \
         patch("mindweaver.platform_service.base.PlatformService._decommission_from_cluster"), \
         patch("mindweaver.platform_service.pgsql.service.PgSqlPlatformService.poll_status"), \
         patch("mindweaver.platform_service.superset.service.SupersetPlatformService.poll_status"):

        # 1. Create PostgreSQL dependency
        pgsql_data = {
            "name": "superset-db",
            "title": "Superset PG DB",
            "project_id": test_project["id"],
        }
        resp = client.post(
            "/api/v1/platform/pgsql",
            json=pgsql_data,
            headers={"X-Project-Id": str(test_project["id"])},
        )
        resp.raise_for_status()
        pgsql_id = resp.json()["data"]["id"]

        # Set PostgreSQL state to active=False
        resp = client.post(
            f"/api/v1/platform/pgsql/{pgsql_id}/_state",
            json={"status": "offline", "active": False},
            headers={
                "X-Project-Id": str(test_project["id"]),
                "X-RESOURCE-NAME": "superset-db",
            },
        )
        resp.raise_for_status()

        # Create Superset Platform
        superset_data = {
            "name": "my-superset",
            "title": "My Superset",
            "project_id": test_project["id"],
            "platform_pgsql_id": pgsql_id,
        }
        resp = client.post(
            "/api/v1/platform/superset",
            json=superset_data,
            headers={"X-Project-Id": str(test_project["id"])},
        )
        resp.raise_for_status()
        superset_id = resp.json()["data"]["id"]

        # Deploy Superset -> should fail
        with pytest.raises(ValueError, match="is not active"):
            client.post(
                f"/api/v1/platform/superset/{superset_id}/_deploy",
                headers={"X-Project-Id": str(test_project["id"])},
            )

        # Decommission Superset -> should succeed
        resp = client.post(
            f"/api/v1/platform/superset/{superset_id}/_decommission",
            headers={
                "X-Project-Id": str(test_project["id"]),
                "X-RESOURCE-NAME": "my-superset",
            },
        )
        assert resp.status_code == 200
