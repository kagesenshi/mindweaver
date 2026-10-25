# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from fastapi.testclient import TestClient
import sqlalchemy.exc as saexc
from mindweaver.fw.service import Service
from mindweaver.fw.exc import ModelValidationError


def test_delete_referenced_resource_fails_with_422(
    client: TestClient, test_cluster: dict, test_project: dict
):
    """
    Test that deleting a resource referenced by another resource
    fails cleanly with HTTP 422 and a helpful error message instead of 500.
    """
    # test_project references test_cluster via k8s_cluster_id
    resp = client.delete(
        f"/api/v1/k8s_clusters/{test_cluster['id']}",
        headers={"X-RESOURCE-NAME": test_cluster["name"]},
    )
    assert resp.status_code == 422
    data = resp.json()
    assert data["status"] == "error"
    assert data["type"] == "validation_error"
    assert len(data["detail"]) > 0
    msg = data["detail"][0]["msg"]
    assert "Cannot delete: resource is still referenced by" in msg
    assert "mw_project" in msg


def test_delete_resource_after_dependent_deleted_succeeds(
    client: TestClient, test_cluster: dict, test_project: dict
):
    """
    Test that once dependent resource is deleted, deleting the parent resource succeeds.
    """
    # Delete the dependent project first
    del_proj = client.delete(
        f"/api/v1/projects/{test_project['id']}",
        headers={"X-RESOURCE-NAME": test_project["name"]},
    )
    assert del_proj.status_code == 200

    # Now delete the cluster
    del_clust = client.delete(
        f"/api/v1/k8s_clusters/{test_cluster['id']}",
        headers={"X-RESOURCE-NAME": test_cluster["name"]},
    )
    assert del_clust.status_code == 200


def test_handle_integrity_error_foreign_key_delete_unit():
    """
    Unit test _handle_integrity_error for foreign key violations in delete actions.
    """
    class DummyService(Service):
        @classmethod
        def model_class(cls):
            return None

    svc = DummyService.__new__(DummyService)

    # 1. PostgreSQL error mentioning table
    orig_exc = Exception(
        'update or delete on table "mw_pgsql_platform" violates foreign key constraint "mw_hive_metastore_platform_database_id_fkey" on table "mw_hive_metastore_platform"\n'
        'DETAIL: Key (id)=(2) is still referenced from table "mw_hive_metastore_platform".'
    )
    err = saexc.IntegrityError(statement="DELETE", params=[], orig=orig_exc)

    with pytest.raises(ModelValidationError) as exc_info:
        svc._handle_integrity_error(err, action="delete")
    assert "Cannot delete: resource is still referenced by" in str(exc_info.value.detail)
    assert "mw_hive_metastore_platform" in str(exc_info.value.detail)

    # 2. Generic SQLite delete foreign key error
    orig_sqlite = Exception("FOREIGN KEY constraint failed")
    err_sqlite = saexc.IntegrityError(statement="DELETE", params=[], orig=orig_sqlite)

    with pytest.raises(ModelValidationError) as exc_info:
        svc._handle_integrity_error(err_sqlite, action="delete")
    assert "Cannot delete: resource is still referenced by other resources" in str(exc_info.value.detail)

    # 3. Insert/update foreign key error (non-delete)
    orig_fk = Exception("insert or update on table violates foreign key constraint")
    err_fk = saexc.IntegrityError(statement="INSERT", params=[], orig=orig_fk)

    with pytest.raises(ModelValidationError) as exc_info:
        svc._handle_integrity_error(err_fk, action=None)
    assert "Referenced record does not exist" in str(exc_info.value.detail)
