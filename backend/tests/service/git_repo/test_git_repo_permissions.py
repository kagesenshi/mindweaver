# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from unittest.mock import AsyncMock, patch
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
from mindweaver.service.git_repo.permission import (
    ManageGitRepo,
    ViewGitRepo,
    GitRepo,
    Read,
    List,
    View,
    Write,
    Create,
    Update,
    Delete,
    Execute,
    TestConnection,
    ManageGitRepoPermission,
    ViewGitRepoPermission,
    GitRepoPermission,
    GitRepoRead,
    GitRepoList,
    GitRepoView,
    GitRepoWrite,
    GitRepoCreate,
    GitRepoUpdate,
    GitRepoDelete,
    GitRepoExecute,
    GitRepoTestConnection,
)


class DummyUser:
    """Mock user class for permission testing."""

    def __init__(self, is_superadmin: bool = False, permissions: list | None = None):
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


def test_git_repo_permission_hierarchy():
    """Verify GitRepo permission classes inherit correctly from All, Permission, and fw classes."""
    assert issubclass(ManageGitRepo, Permission)
    assert issubclass(ManageGitRepo, All)

    # ViewGitRepo hierarchy
    assert issubclass(ViewGitRepo, ManageGitRepo)
    assert issubclass(ViewGitRepo, Permission)

    # Read hierarchy (inherits from ViewGitRepo and FwRead)
    assert issubclass(Read, ViewGitRepo)
    assert issubclass(Read, ManageGitRepo)
    assert issubclass(Read, FwRead)
    assert issubclass(List, Read)
    assert issubclass(List, ViewGitRepo)
    assert issubclass(List, FwList)
    assert issubclass(View, Read)
    assert issubclass(View, ViewGitRepo)
    assert issubclass(View, FwView)

    # Write hierarchy (inherits from ManageGitRepo, NOT ViewGitRepo)
    assert issubclass(Write, ManageGitRepo)
    assert not issubclass(Write, ViewGitRepo)
    assert issubclass(Write, FwWrite)
    assert issubclass(Create, Write)
    assert not issubclass(Create, ViewGitRepo)
    assert issubclass(Create, FwCreate)
    assert issubclass(Update, Write)
    assert not issubclass(Update, ViewGitRepo)
    assert issubclass(Update, FwUpdate)
    assert issubclass(Delete, Write)
    assert not issubclass(Delete, ViewGitRepo)
    assert issubclass(Delete, FwDelete)

    # Execute hierarchy (inherits from ManageGitRepo, NOT ViewGitRepo)
    assert issubclass(Execute, ManageGitRepo)
    assert not issubclass(Execute, ViewGitRepo)
    assert issubclass(Execute, FwExecute)
    assert issubclass(TestConnection, Execute)
    assert not issubclass(TestConnection, ViewGitRepo)

    # Aliases
    assert ManageGitRepoPermission is ManageGitRepo
    assert ViewGitRepoPermission is ViewGitRepo
    assert GitRepo is ManageGitRepo
    assert GitRepoPermission is ManageGitRepo
    assert GitRepoRead is Read
    assert GitRepoList is List
    assert GitRepoView is View
    assert GitRepoWrite is Write
    assert GitRepoCreate is Create
    assert GitRepoUpdate is Update
    assert GitRepoDelete is Delete
    assert GitRepoExecute is Execute
    assert GitRepoTestConnection is TestConnection


def test_git_repo_permission_string_registration():
    """Verify that GitRepo permission names are registered in _NAME_TO_PERMISSION via init_subclass."""
    assert _NAME_TO_PERMISSION.get("git_repo:manage") is ManageGitRepo
    assert _NAME_TO_PERMISSION.get("git_repo:view_git_repo") is ViewGitRepo
    assert _NAME_TO_PERMISSION.get("git_repo:read") is Read
    assert _NAME_TO_PERMISSION.get("git_repo:list") is List
    assert _NAME_TO_PERMISSION.get("git_repo:view") is View
    assert _NAME_TO_PERMISSION.get("git_repo:write") is Write
    assert _NAME_TO_PERMISSION.get("git_repo:create") is Create
    assert _NAME_TO_PERMISSION.get("git_repo:update") is Update
    assert _NAME_TO_PERMISSION.get("git_repo:delete") is Delete
    assert _NAME_TO_PERMISSION.get("git_repo:execute") is Execute
    assert _NAME_TO_PERMISSION.get("git_repo:test_connection") is TestConnection
    # Verify manual aliases are not registered
    assert "git_repo" not in _NAME_TO_PERMISSION
    assert "manage_git_repo" not in _NAME_TO_PERMISSION
    assert "view_git_repo" not in _NAME_TO_PERMISSION


def test_git_repo_check_user_permission_rules():
    """Verify check_user_permission evaluates service permissions accurately."""
    # 1. Superadmin has everything
    superadmin = DummyUser(is_superadmin=True)
    assert check_user_permission(superadmin, ManageGitRepo)
    assert check_user_permission(superadmin, ViewGitRepo)
    assert check_user_permission(superadmin, List)
    assert check_user_permission(superadmin, Create)
    assert check_user_permission(superadmin, TestConnection)

    # 2. User with ManageGitRepo permission has all git repo actions
    repo_admin = DummyUser(permissions=[ManageGitRepo])
    assert check_user_permission(repo_admin, ManageGitRepo)
    assert check_user_permission(repo_admin, ViewGitRepo)
    assert check_user_permission(repo_admin, List)
    assert check_user_permission(repo_admin, View)
    assert check_user_permission(repo_admin, Create)
    assert check_user_permission(repo_admin, Update)
    assert check_user_permission(repo_admin, Delete)
    assert check_user_permission(repo_admin, TestConnection)

    # 3. User with ViewGitRepo permission has view-type actions ONLY
    repo_viewer = DummyUser(permissions=[ViewGitRepo])
    assert check_user_permission(repo_viewer, ViewGitRepo)
    assert check_user_permission(repo_viewer, List)
    assert check_user_permission(repo_viewer, View)
    # Mutating / operational actions MUST be denied
    assert not check_user_permission(repo_viewer, ManageGitRepo)
    assert not check_user_permission(repo_viewer, Write)
    assert not check_user_permission(repo_viewer, Create)
    assert not check_user_permission(repo_viewer, Update)
    assert not check_user_permission(repo_viewer, Delete)
    assert not check_user_permission(repo_viewer, Execute)
    assert not check_user_permission(repo_viewer, TestConnection)

    # 4. User with GitRepoRead has List and View, but not mutating or execute actions
    repo_reader = DummyUser(permissions=[Read])
    assert check_user_permission(repo_reader, List)
    assert check_user_permission(repo_reader, View)
    assert not check_user_permission(repo_reader, Create)
    assert not check_user_permission(repo_reader, Update)
    assert not check_user_permission(repo_reader, Delete)
    assert not check_user_permission(repo_reader, TestConnection)

    # 5. User with GitRepoTestConnection can test connection but cannot do other actions
    tester = DummyUser(permissions=[TestConnection])
    assert check_user_permission(tester, TestConnection)
    assert not check_user_permission(tester, List)
    assert not check_user_permission(tester, Create)
    assert not check_user_permission(tester, Delete)

    # 6. Default authenticated user (with FwRead) can list and view git repos
    default_user = DummyUser()
    assert check_user_permission(default_user, List)
    assert check_user_permission(default_user, View)
    assert not check_user_permission(default_user, Create)
    assert not check_user_permission(default_user, TestConnection)


def test_git_repo_endpoints_enforce_permissions(client: TestClient, test_project):
    """Verify git repo endpoints enforce permissions via HTTP API."""
    settings.enable_auth = True
    with client as c:
        admin_headers = _get_superadmin_headers(c)
        reg_headers = _create_and_login_user(c, admin_headers, "regular_alice")
        proj_id = test_project["id"]

        # 1. Regular user cannot create git repo
        resp = c.post(
            "/api/v1/git_repos",
            json={
                "name": "test-repo-perm",
                "title": "Test Perm Git Repo",
                "url": "https://github.com/my-org/my-repo.git",
                "username": "user",
                "password": "pwd",
                "project_id": proj_id,
            },
            headers={"X-Project-ID": str(proj_id), **reg_headers},
        )
        assert resp.status_code == 403
        assert "Permission denied" in resp.text

        # 2. Superadmin can create git repo
        resp = c.post(
            "/api/v1/git_repos",
            json={
                "name": "test-repo-perm",
                "title": "Test Perm Git Repo",
                "url": "https://github.com/my-org/my-repo.git",
                "username": "user",
                "password": "pwd",
                "project_id": proj_id,
            },
            headers={"X-Project-ID": str(proj_id), **admin_headers},
        )
        assert resp.status_code == 200, resp.text
        repo_id = resp.json()["data"]["id"]

        # 3. Regular user can view git repo
        resp = c.get(
            f"/api/v1/git_repos/{repo_id}",
            headers={"X-Project-ID": str(proj_id), **reg_headers},
        )
        assert resp.status_code == 200

        # 4. Regular user can list git repos
        resp = c.get(
            "/api/v1/git_repos",
            headers={"X-Project-ID": str(proj_id), **reg_headers},
        )
        assert resp.status_code == 200

        # 5. Regular user cannot update git repo
        resp = c.put(
            f"/api/v1/git_repos/{repo_id}",
            json={"title": "Updated Title"},
            headers={"X-Project-ID": str(proj_id), **reg_headers},
        )
        assert resp.status_code == 403

        # 6. Regular user cannot delete git repo
        resp = c.delete(
            f"/api/v1/git_repos/{repo_id}",
            headers={
                "X-RESOURCE-NAME": "test-repo-perm",
                "X-Project-ID": str(proj_id),
                **reg_headers,
            },
        )
        assert resp.status_code == 403

        # 7. Regular user cannot trigger test connection
        resp = c.post(
            "/api/v1/git_repos/_test-connection",
            json={"url": "https://github.com/my-org/my-repo.git"},
            headers={"X-Project-ID": str(proj_id), **reg_headers},
        )
        assert resp.status_code == 403
        assert "Permission denied for 'git_repo:test_connection'" in resp.text


def test_git_repo_endpoints_with_granted_permissions(client: TestClient, test_project):
    """Verify users with granted service permissions can access allowed endpoints."""
    settings.enable_auth = True
    with client as c:
        admin_headers = _get_superadmin_headers(c)
        proj_id = test_project["id"]
        manager_headers = _create_and_login_user(c, admin_headers, "repo_manager")
        viewer_headers = _create_and_login_user(c, admin_headers, "repo_viewer")
        tester_headers = _create_and_login_user(c, admin_headers, "conn_tester")

        def _mock_perms(custom_perms):
            def _get(u, *args, **kwargs):
                if getattr(u, "is_superadmin", False):
                    return [All]
                return custom_perms
            return _get

        # 1. User with ManageGitRepo permission (full control)
        with patch("mindweaver.fw.permission.get_user_permissions", side_effect=_mock_perms([ManageGitRepo])):
            # Can create
            resp = c.post(
                "/api/v1/git_repos",
                json={
                    "name": "mgr-repo",
                    "title": "Mgr Git Repo",
                    "url": "https://github.com/org/mgr.git",
                    "username": "u",
                    "password": "p",
                    "project_id": proj_id,
                },
                headers={"X-Project-ID": str(proj_id), **manager_headers},
            )
            assert resp.status_code == 200, resp.text
            created_id = resp.json()["data"]["id"]

            # Can update
            resp = c.put(
                f"/api/v1/git_repos/{created_id}",
                json={"title": "Updated Mgr Git Repo"},
                headers={"X-Project-ID": str(proj_id), **manager_headers},
            )
            assert resp.status_code == 200

            # Can test connection
            with patch("mindweaver.service.git_repo.views.run_git_ls_remote", AsyncMock(return_value=(True, "OK"))):
                resp = c.post(
                    "/api/v1/git_repos/_test-connection",
                    json={"url": "https://github.com/org/mgr.git"},
                    headers={"X-Project-ID": str(proj_id), **manager_headers},
                )
                assert resp.status_code == 200
                assert resp.json()["status"] == "success"

            # Can delete
            resp = c.delete(
                f"/api/v1/git_repos/{created_id}",
                headers={
                    "X-RESOURCE-NAME": "mgr-repo",
                    "X-Project-ID": str(proj_id),
                    **manager_headers,
                },
            )
            assert resp.status_code == 200

        # 2. User with ViewGitRepo permission (view-only control)
        # Create a repo as admin
        r_resp = c.post(
            "/api/v1/git_repos",
            json={
                "name": "view-repo-target",
                "title": "View Target",
                "url": "https://github.com/org/target.git",
                "username": "u",
                "password": "p",
                "project_id": proj_id,
            },
            headers={"X-Project-ID": str(proj_id), **admin_headers},
        )
        assert r_resp.status_code == 200
        target_repo_id = r_resp.json()["data"]["id"]

        with patch("mindweaver.fw.permission.get_user_permissions", side_effect=_mock_perms([ViewGitRepo])):
            # Can list
            resp = c.get(
                "/api/v1/git_repos",
                headers={"X-Project-ID": str(proj_id), **viewer_headers},
            )
            assert resp.status_code == 200

            # Can view
            resp = c.get(
                f"/api/v1/git_repos/{target_repo_id}",
                headers={"X-Project-ID": str(proj_id), **viewer_headers},
            )
            assert resp.status_code == 200

            # CANNOT create
            resp = c.post(
                "/api/v1/git_repos",
                json={
                    "name": "illegal-repo-viewer",
                    "title": "Illegal",
                    "url": "https://github.com/org/illegal.git",
                    "username": "u",
                    "password": "p",
                    "project_id": proj_id,
                },
                headers={"X-Project-ID": str(proj_id), **viewer_headers},
            )
            assert resp.status_code == 403

            # CANNOT update
            resp = c.put(
                f"/api/v1/git_repos/{target_repo_id}",
                json={"title": "Updated by viewer"},
                headers={"X-Project-ID": str(proj_id), **viewer_headers},
            )
            assert resp.status_code == 403

            # CANNOT test connection
            resp = c.post(
                "/api/v1/git_repos/_test-connection",
                json={"url": "https://github.com/org/target.git"},
                headers={"X-Project-ID": str(proj_id), **viewer_headers},
            )
            assert resp.status_code == 403

            # CANNOT delete
            resp = c.delete(
                f"/api/v1/git_repos/{target_repo_id}",
                headers={
                    "X-RESOURCE-NAME": "view-repo-target",
                    "X-Project-ID": str(proj_id),
                    **viewer_headers,
                },
            )
            assert resp.status_code == 403

        # 3. User with only TestConnection permission
        with patch("mindweaver.fw.permission.get_user_permissions", side_effect=_mock_perms([TestConnection])):
            # Tester cannot create
            resp = c.post(
                "/api/v1/git_repos",
                json={
                    "name": "illegal-repo-tester",
                    "title": "Illegal",
                    "url": "https://github.com/org/illegal.git",
                    "username": "u",
                    "password": "p",
                    "project_id": proj_id,
                },
                headers={"X-Project-ID": str(proj_id), **tester_headers},
            )
            assert resp.status_code == 403

            # Tester CAN test connection
            with patch("mindweaver.service.git_repo.views.run_git_ls_remote", AsyncMock(return_value=(True, "OK"))):
                resp = c.post(
                    "/api/v1/git_repos/_test-connection",
                    json={"url": "https://github.com/org/test.git"},
                    headers={"X-Project-ID": str(proj_id), **tester_headers},
                )
                assert resp.status_code == 200
                assert resp.json()["status"] == "success"
