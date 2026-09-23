# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from mindweaver.config import settings
from mindweaver.fw.permission import (
    All,
    Permission,
    Read as FwRead,
    Write as FwWrite,
    List as FwList,
    View as FwView,
    Create as FwCreate,
    Update as FwUpdate,
    Delete as FwDelete,
    Execute as FwExecute,
    check_user_permission,
    _NAME_TO_PERMISSION,
)
from mindweaver.service.s3_storage.permission import (
    Manage,
    Read,
    List,
    View,
    Write,
    Create,
    Update,
    Delete,
    Execute,
    TestConnection,
    FsRead,
    FsWrite,
    ManageS3Storage,
    ManageS3StoragePermission,
    S3Storage,
    S3StoragePermission,
    S3StorageRead,
    S3StorageList,
    S3StorageView,
    S3StorageWrite,
    S3StorageCreate,
    S3StorageUpdate,
    S3StorageDelete,
    S3StorageExecute,
    S3StorageTestConnection,
    S3StorageFsRead,
    S3StorageFsWrite,
    ManageS3,
    ManageS3Permission,
    S3,
    S3Permission,
    S3Read,
    S3List,
    S3View,
    S3Write,
    S3Create,
    S3Update,
    S3Delete,
    S3Execute,
    S3TestConnection,
    S3FsRead,
    S3FsWrite,
)


class DummyUser:
    """Mock user class for permission testing."""

    def __init__(self, is_superadmin: bool = False, permissions: list | None = None):
        """Initialize mock user with superadmin status and permissions list."""
        self.is_superadmin = is_superadmin
        self.permissions = permissions


@pytest.fixture(autouse=True)
def setup_settings():
    """Save and restore auth-related settings around each test."""
    old_admin_user = settings.default_admin_username
    old_admin_pass = settings.default_admin_password
    old_enable_auth = settings.enable_auth
    settings.default_admin_username = "admin"
    settings.default_admin_password = "password123"
    yield
    settings.default_admin_username = old_admin_user
    settings.default_admin_password = old_admin_pass
    settings.enable_auth = old_enable_auth


def _get_superadmin_headers(c: TestClient) -> dict:
    """Login as admin superuser and return authorization headers."""
    login_resp = c.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "password123"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_and_login_user(
    c: TestClient, admin_headers: dict, username: str, permissions: list | None = None
) -> dict:
    """Create a user with specified permissions and return auth headers."""
    user_resp = c.post(
        "/api/v1/users",
        json={
            "name": username,
            "title": "Engineer",
            "email": f"{username}@example.com",
            "password": "password123",
            "display_name": username.capitalize(),
            "is_superadmin": False,
        },
        headers=admin_headers,
    )
    assert user_resp.status_code == 200

    login_resp = c.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "password123"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_s3_storage_permission_hierarchy():
    """Verify S3Storage permission classes inherit correctly from All, Permission, and fw classes."""
    assert issubclass(Manage, Permission)
    assert issubclass(Manage, All)

    # Read hierarchy (inherits from Manage and FwRead)
    assert issubclass(Read, Manage)
    assert issubclass(Read, FwRead)
    assert issubclass(List, Read)
    assert issubclass(List, Manage)
    assert issubclass(List, FwList)
    assert issubclass(View, Read)
    assert issubclass(View, Manage)
    assert issubclass(View, FwView)

    # Write hierarchy (inherits from Manage)
    assert issubclass(Write, Manage)
    assert not issubclass(Write, Read)
    assert issubclass(Write, FwWrite)
    assert issubclass(Create, Write)
    assert not issubclass(Create, Read)
    assert issubclass(Create, FwCreate)
    assert issubclass(Update, Write)
    assert not issubclass(Update, Read)
    assert issubclass(Update, FwUpdate)
    assert issubclass(Delete, Write)
    assert not issubclass(Delete, Read)
    assert issubclass(Delete, FwDelete)

    # Execute hierarchy (inherits from Manage)
    assert issubclass(Execute, Manage)
    assert not issubclass(Execute, Read)
    assert issubclass(Execute, FwExecute)
    assert issubclass(TestConnection, Execute)
    assert not issubclass(TestConnection, Read)

    # Custom S3 filesystem permissions
    assert issubclass(FsRead, View)
    assert issubclass(FsRead, Read)
    assert issubclass(FsRead, Manage)
    assert not issubclass(FsRead, Write)

    assert issubclass(FsWrite, Write)
    assert issubclass(FsWrite, Manage)
    assert not issubclass(FsWrite, Read)
    assert not issubclass(FsWrite, View)

    # Canonical Aliases (S3Storage*)
    assert ManageS3Storage is Manage
    assert ManageS3StoragePermission is Manage
    assert S3Storage is Manage
    assert S3StoragePermission is Manage
    assert S3StorageRead is Read
    assert S3StorageList is List
    assert S3StorageView is View
    assert S3StorageWrite is Write
    assert S3StorageCreate is Create
    assert S3StorageUpdate is Update
    assert S3StorageDelete is Delete
    assert S3StorageExecute is Execute
    assert S3StorageTestConnection is TestConnection
    assert S3StorageFsRead is FsRead
    assert S3StorageFsWrite is FsWrite

    # Canonical Aliases (S3*)
    assert ManageS3 is Manage
    assert ManageS3Permission is Manage
    assert S3 is Manage
    assert S3Permission is Manage
    assert S3Read is Read
    assert S3List is List
    assert S3View is View
    assert S3Write is Write
    assert S3Create is Create
    assert S3Update is Update
    assert S3Delete is Delete
    assert S3Execute is Execute
    assert S3TestConnection is TestConnection
    assert S3FsRead is FsRead
    assert S3FsWrite is FsWrite


def test_s3_storage_permission_string_registration():
    """Verify that S3Storage permission names are registered in _NAME_TO_PERMISSION via init_subclass."""
    assert _NAME_TO_PERMISSION.get("s3_storage:manage") is Manage
    assert _NAME_TO_PERMISSION.get("s3_storage:read") is Read
    assert _NAME_TO_PERMISSION.get("s3_storage:list") is List
    assert _NAME_TO_PERMISSION.get("s3_storage:view") is View
    assert _NAME_TO_PERMISSION.get("s3_storage:write") is Write
    assert _NAME_TO_PERMISSION.get("s3_storage:create") is Create
    assert _NAME_TO_PERMISSION.get("s3_storage:update") is Update
    assert _NAME_TO_PERMISSION.get("s3_storage:delete") is Delete
    assert _NAME_TO_PERMISSION.get("s3_storage:execute") is Execute
    assert _NAME_TO_PERMISSION.get("s3_storage:test_connection") is TestConnection
    assert _NAME_TO_PERMISSION.get("s3_storage:fs_read") is FsRead
    assert _NAME_TO_PERMISSION.get("s3_storage:fs_write") is FsWrite
    # Verify manual aliases are not registered as string names
    assert "s3_storage" not in _NAME_TO_PERMISSION
    assert "manage_s3_storage" not in _NAME_TO_PERMISSION
    assert "view_s3_storage" not in _NAME_TO_PERMISSION


def test_s3_storage_check_user_permission_rules():
    """Verify check_user_permission evaluates service permissions accurately."""
    # 1. Superadmin has everything
    superadmin = DummyUser(is_superadmin=True)
    assert check_user_permission(superadmin, Manage)
    assert check_user_permission(superadmin, Read)
    assert check_user_permission(superadmin, List)
    assert check_user_permission(superadmin, View)
    assert check_user_permission(superadmin, Create)
    assert check_user_permission(superadmin, Update)
    assert check_user_permission(superadmin, Delete)
    assert check_user_permission(superadmin, Execute)
    assert check_user_permission(superadmin, TestConnection)
    assert check_user_permission(superadmin, FsRead)
    assert check_user_permission(superadmin, FsWrite)

    # 2. User with Manage permission has all s3_storage actions
    s3_admin = DummyUser(permissions=[Manage])
    assert check_user_permission(s3_admin, Manage)
    assert check_user_permission(s3_admin, Read)
    assert check_user_permission(s3_admin, List)
    assert check_user_permission(s3_admin, View)
    assert check_user_permission(s3_admin, Create)
    assert check_user_permission(s3_admin, Update)
    assert check_user_permission(s3_admin, Delete)
    assert check_user_permission(s3_admin, Execute)
    assert check_user_permission(s3_admin, TestConnection)
    assert check_user_permission(s3_admin, FsRead)
    assert check_user_permission(s3_admin, FsWrite)

    # 3. User with S3StorageRead has List, View, and FsRead, but not mutating or execute actions
    s3_reader = DummyUser(permissions=[Read])
    assert check_user_permission(s3_reader, Read)
    assert check_user_permission(s3_reader, List)
    assert check_user_permission(s3_reader, View)
    assert check_user_permission(s3_reader, FsRead)
    assert not check_user_permission(s3_reader, Manage)
    assert not check_user_permission(s3_reader, Write)
    assert not check_user_permission(s3_reader, Create)
    assert not check_user_permission(s3_reader, Update)
    assert not check_user_permission(s3_reader, Delete)
    assert not check_user_permission(s3_reader, Execute)
    assert not check_user_permission(s3_reader, TestConnection)
    assert not check_user_permission(s3_reader, FsWrite)

    # 4. User with S3StorageWrite has mutating actions and FsWrite, but not Read, View, List, TestConnection
    s3_writer = DummyUser(permissions=[Write])
    assert check_user_permission(s3_writer, Write)
    assert check_user_permission(s3_writer, Create)
    assert check_user_permission(s3_writer, Update)
    assert check_user_permission(s3_writer, Delete)
    assert check_user_permission(s3_writer, FsWrite)
    assert not check_user_permission(s3_writer, Read)
    assert not check_user_permission(s3_writer, List)
    assert not check_user_permission(s3_writer, View)
    assert not check_user_permission(s3_writer, FsRead)
    assert not check_user_permission(s3_writer, TestConnection)

    # 5. User with TestConnection can test connection but cannot do other actions
    tester = DummyUser(permissions=[TestConnection])
    assert check_user_permission(tester, TestConnection)
    assert not check_user_permission(tester, List)
    assert not check_user_permission(tester, Create)
    assert not check_user_permission(tester, Delete)
    assert not check_user_permission(tester, FsRead)
    assert not check_user_permission(tester, FsWrite)

    # 6. User with FsRead can read S3 files but not write or manage
    fs_reader = DummyUser(permissions=[FsRead])
    assert check_user_permission(fs_reader, FsRead)
    assert not check_user_permission(fs_reader, FsWrite)
    assert not check_user_permission(fs_reader, Create)
    assert not check_user_permission(fs_reader, Delete)
    assert not check_user_permission(fs_reader, TestConnection)

    # 7. User with FsWrite can upload/delete S3 files but not read or manage
    fs_writer = DummyUser(permissions=[FsWrite])
    assert check_user_permission(fs_writer, FsWrite)
    assert not check_user_permission(fs_writer, FsRead)
    assert not check_user_permission(fs_writer, Create)
    assert not check_user_permission(fs_writer, Delete)
    assert not check_user_permission(fs_writer, TestConnection)

    # 8. Default authenticated user (with FwRead) can list, view, and fs_read s3 storages
    default_user = DummyUser()
    assert check_user_permission(default_user, List)
    assert check_user_permission(default_user, View)
    assert check_user_permission(default_user, FsRead)
    assert not check_user_permission(default_user, Create)
    assert not check_user_permission(default_user, Update)
    assert not check_user_permission(default_user, Delete)
    assert not check_user_permission(default_user, TestConnection)
    assert not check_user_permission(default_user, FsWrite)


def test_s3_storage_endpoints_enforce_permissions(client: TestClient, test_project):
    """Verify s3 storage endpoints enforce permissions via HTTP API."""
    settings.enable_auth = True
    with client as c:
        admin_headers = _get_superadmin_headers(c)
        reg_headers = _create_and_login_user(c, admin_headers, "regular_s3_user")
        proj_id = test_project["id"]

        s3_payload = {
            "name": "test-perm-s3",
            "title": "Test Perm S3",
            "region": "us-east-1",
            "access_key": "AKIAIOSFODNN7EXAMPLE",
            "secret_key": "supersecretkey123",
            "project_id": proj_id,
        }

        # 1. Regular user cannot create S3 storage
        resp = c.post(
            "/api/v1/s3_storages",
            json=s3_payload,
            headers={"X-Project-ID": str(proj_id), **reg_headers},
        )
        assert resp.status_code == 403
        assert "Permission denied" in resp.text

        # 2. Superadmin can create S3 storage
        resp = c.post(
            "/api/v1/s3_storages",
            json=s3_payload,
            headers={"X-Project-ID": str(proj_id), **admin_headers},
        )
        assert resp.status_code == 200, resp.text
        storage_id = resp.json()["data"]["id"]

        # 3. Regular user can view S3 storage
        resp = c.get(
            f"/api/v1/s3_storages/{storage_id}",
            headers={"X-Project-ID": str(proj_id), **reg_headers},
        )
        assert resp.status_code == 200

        # 4. Regular user can list S3 storages
        resp = c.get(
            "/api/v1/s3_storages",
            headers={"X-Project-ID": str(proj_id), **reg_headers},
        )
        assert resp.status_code == 200

        # 5. Regular user cannot update S3 storage
        resp = c.put(
            f"/api/v1/s3_storages/{storage_id}",
            json={"title": "Updated Title"},
            headers={"X-Project-ID": str(proj_id), **reg_headers},
        )
        assert resp.status_code == 403

        # 6. Regular user cannot delete S3 storage
        resp = c.delete(
            f"/api/v1/s3_storages/{storage_id}",
            headers={
                "X-RESOURCE-NAME": "test-perm-s3",
                "X-Project-ID": str(proj_id),
                **reg_headers,
            },
        )
        assert resp.status_code == 403

        # 7. Regular user cannot trigger test connection
        resp = c.post(
            "/api/v1/s3_storages/_test-connection",
            json={"region": "us-east-1", "access_key": "AKIAIOSFODNN7EXAMPLE"},
            headers={"X-Project-ID": str(proj_id), **reg_headers},
        )
        assert resp.status_code == 403
        assert "Permission denied for 's3_storage:test_connection'" in resp.text

        # 8. Regular user cannot perform mutating filesystem operations (POST _fs)
        resp = c.post(
            f"/api/v1/s3_storages/{storage_id}/_fs?action=rm&bucket=test&key=dummy.txt",
            headers={"X-Project-ID": str(proj_id), **reg_headers},
        )
        assert resp.status_code == 403
        assert "Permission denied for 's3_storage:fs_write'" in resp.text

        # 9. Regular user can perform read filesystem operations (GET _fs)
        with patch("boto3.client") as mock_boto:
            mock_client = MagicMock()
            mock_boto.return_value = mock_client
            mock_client.list_buckets.return_value = {"Buckets": []}
            resp = c.get(
                f"/api/v1/s3_storages/{storage_id}/_fs?action=ls",
                headers={"X-Project-ID": str(proj_id), **reg_headers},
            )
            assert resp.status_code == 200


def test_s3_storage_endpoints_with_granted_permissions(client: TestClient, test_project):
    """Verify users with granted service permissions can access allowed endpoints."""
    settings.enable_auth = True
    with client as c:
        admin_headers = _get_superadmin_headers(c)
        proj_id = test_project["id"]
        manager_headers = _create_and_login_user(c, admin_headers, "s3_manager")
        reader_headers = _create_and_login_user(c, admin_headers, "s3_reader")
        tester_headers = _create_and_login_user(c, admin_headers, "s3_tester")
        fs_writer_headers = _create_and_login_user(c, admin_headers, "s3_fswriter")

        def _mock_perms(custom_perms):
            def _get(u, *args, **kwargs):
                if getattr(u, "is_superadmin", False):
                    return [All]
                return custom_perms
            return _get

        # 1. User with Manage permission (full control)
        with patch("mindweaver.fw.permission.get_user_permissions", side_effect=_mock_perms([Manage])):
            # Can create
            resp = c.post(
                "/api/v1/s3_storages",
                json={
                    "name": "mgr-s3",
                    "title": "Mgr S3",
                    "region": "us-east-1",
                    "access_key": "AKIAMANAGER123",
                    "secret_key": "mgrpass123",
                    "project_id": proj_id,
                },
                headers={"X-Project-ID": str(proj_id), **manager_headers},
            )
            assert resp.status_code == 200, resp.text
            created_id = resp.json()["data"]["id"]

            # Can update
            resp = c.put(
                f"/api/v1/s3_storages/{created_id}",
                json={"title": "Updated Mgr S3"},
                headers={"X-Project-ID": str(proj_id), **manager_headers},
            )
            assert resp.status_code == 200

            # Can test connection
            with patch("boto3.client") as mock_boto:
                mock_client = MagicMock()
                mock_boto.return_value = mock_client
                mock_client.list_buckets.return_value = {"Buckets": []}
                resp = c.post(
                    "/api/v1/s3_storages/_test-connection",
                    json={"region": "us-east-1", "access_key": "AKIAMANAGER123", "storage_id": created_id},
                    headers={"X-Project-ID": str(proj_id), **manager_headers},
                )
                assert resp.status_code == 200
                assert resp.json()["status"] == "success"

            # Can post _fs (rm)
            with patch("boto3.client") as mock_boto:
                mock_client = MagicMock()
                mock_boto.return_value = mock_client
                resp = c.post(
                    f"/api/v1/s3_storages/{created_id}/_fs?action=rm&bucket=test&key=file.txt",
                    headers={"X-Project-ID": str(proj_id), **manager_headers},
                )
                assert resp.status_code == 200
                assert resp.json()["status"] == "success"

            # Can delete
            resp = c.delete(
                f"/api/v1/s3_storages/{created_id}",
                headers={
                    "X-RESOURCE-NAME": "mgr-s3",
                    "X-Project-ID": str(proj_id),
                    **manager_headers,
                },
            )
            assert resp.status_code == 200

        # 2. User with Read permission (read-only control)
        # Create an s3 storage as admin
        r_resp = c.post(
            "/api/v1/s3_storages",
            json={
                "name": "view-s3-target",
                "title": "View Target S3",
                "region": "us-east-1",
                "access_key": "AKIAVIEW123",
                "secret_key": "viewpass123",
                "project_id": proj_id,
            },
            headers={"X-Project-ID": str(proj_id), **admin_headers},
        )
        assert r_resp.status_code == 200
        target_id = r_resp.json()["data"]["id"]

        with patch("mindweaver.fw.permission.get_user_permissions", side_effect=_mock_perms([Read])):
            # Can list
            resp = c.get(
                "/api/v1/s3_storages",
                headers={"X-Project-ID": str(proj_id), **reader_headers},
            )
            assert resp.status_code == 200

            # Can view
            resp = c.get(
                f"/api/v1/s3_storages/{target_id}",
                headers={"X-Project-ID": str(proj_id), **reader_headers},
            )
            assert resp.status_code == 200

            # Can fs_read
            with patch("boto3.client") as mock_boto:
                mock_client = MagicMock()
                mock_boto.return_value = mock_client
                mock_client.list_buckets.return_value = {"Buckets": []}
                resp = c.get(
                    f"/api/v1/s3_storages/{target_id}/_fs?action=ls",
                    headers={"X-Project-ID": str(proj_id), **reader_headers},
                )
                assert resp.status_code == 200

            # CANNOT create
            resp = c.post(
                "/api/v1/s3_storages",
                json={
                    "name": "illegal-reader-s3",
                    "title": "Illegal",
                    "region": "us-east-1",
                    "access_key": "AKIAILLEGAL",
                    "secret_key": "pass",
                    "project_id": proj_id,
                },
                headers={"X-Project-ID": str(proj_id), **reader_headers},
            )
            assert resp.status_code == 403

            # CANNOT update
            resp = c.put(
                f"/api/v1/s3_storages/{target_id}",
                json={"title": "Updated by viewer"},
                headers={"X-Project-ID": str(proj_id), **reader_headers},
            )
            assert resp.status_code == 403

            # CANNOT test connection
            resp = c.post(
                "/api/v1/s3_storages/_test-connection",
                json={"region": "us-east-1", "access_key": "AKIAVIEW123"},
                headers={"X-Project-ID": str(proj_id), **reader_headers},
            )
            assert resp.status_code == 403

            # CANNOT fs_write (rm/put)
            resp = c.post(
                f"/api/v1/s3_storages/{target_id}/_fs?action=rm&bucket=test&key=file.txt",
                headers={"X-Project-ID": str(proj_id), **reader_headers},
            )
            assert resp.status_code == 403

            # CANNOT delete
            resp = c.delete(
                f"/api/v1/s3_storages/{target_id}",
                headers={
                    "X-RESOURCE-NAME": "view-s3-target",
                    "X-Project-ID": str(proj_id),
                    **reader_headers,
                },
            )
            assert resp.status_code == 403

        # 3. User with only TestConnection permission
        with patch("mindweaver.fw.permission.get_user_permissions", side_effect=_mock_perms([TestConnection])):
            # Tester cannot create
            resp = c.post(
                "/api/v1/s3_storages",
                json={
                    "name": "tester-create-s3",
                    "title": "Tester S3",
                    "region": "us-east-1",
                    "access_key": "AKIATESTER123",
                    "secret_key": "testerpass",
                    "project_id": proj_id,
                },
                headers={"X-Project-ID": str(proj_id), **tester_headers},
            )
            assert resp.status_code == 403

            # Tester CAN test connection
            with patch("boto3.client") as mock_boto:
                mock_client = MagicMock()
                mock_boto.return_value = mock_client
                mock_client.list_buckets.return_value = {"Buckets": []}
                resp = c.post(
                    "/api/v1/s3_storages/_test-connection",
                    json={"region": "us-east-1", "access_key": "AKIATESTER123", "storage_id": target_id},
                    headers={"X-Project-ID": str(proj_id), **tester_headers},
                )
                assert resp.status_code == 200
                assert resp.json()["status"] == "success"

        # 4. User with only FsWrite permission
        with patch("mindweaver.fw.permission.get_user_permissions", side_effect=_mock_perms([FsWrite])):
            # FsWriter CAN post _fs (rm)
            with patch("boto3.client") as mock_boto:
                mock_client = MagicMock()
                mock_boto.return_value = mock_client
                resp = c.post(
                    f"/api/v1/s3_storages/{target_id}/_fs?action=rm&bucket=test&key=file.txt",
                    headers={"X-Project-ID": str(proj_id), **fs_writer_headers},
                )
                assert resp.status_code == 200
                assert resp.json()["status"] == "success"

            # FsWriter CANNOT delete the S3 storage record itself
            resp = c.delete(
                f"/api/v1/s3_storages/{target_id}",
                headers={
                    "X-RESOURCE-NAME": "view-s3-target",
                    "X-Project-ID": str(proj_id),
                    **fs_writer_headers,
                },
            )
            assert resp.status_code == 403
