# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
from unittest.mock import patch
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
from mindweaver.service.trusted_certs.permission import (
    Manage,
    Read,
    List,
    View,
    Write,
    Create,
    Update,
    Delete,
    Execute,
    Decode,
    ManageTrustedCert,
    ManageTrustedCertPermission,
    TrustedCert,
    TrustedCertPermission,
    TrustedCertRead,
    TrustedCertList,
    TrustedCertView,
    TrustedCertWrite,
    TrustedCertCreate,
    TrustedCertUpdate,
    TrustedCertDelete,
    TrustedCertExecute,
    TrustedCertDecode,
    ManageTrustedCerts,
    ManageTrustedCertsPermission,
    TrustedCerts,
    TrustedCertsPermission,
    TrustedCertsRead,
    TrustedCertsList,
    TrustedCertsView,
    TrustedCertsWrite,
    TrustedCertsCreate,
    TrustedCertsUpdate,
    TrustedCertsDelete,
    TrustedCertsExecute,
    TrustedCertsDecode,
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


def _generate_valid_cert_pem():
    """Generate a valid self-signed certificate PEM for testing."""
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    import datetime

    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "test-ca"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Mindweaver Test Org"),
    ])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1))
        .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=10))
        .sign(private_key, hashes.SHA256())
    )
    return cert.public_bytes(serialization.Encoding.PEM).decode("utf-8")


VALID_CERT = _generate_valid_cert_pem()


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


def test_trusted_cert_permission_hierarchy():
    """Verify TrustedCert permission classes inherit correctly from All, Permission, and fw classes."""
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

    # Custom decode view
    assert issubclass(Decode, View)
    assert issubclass(Decode, Read)
    assert issubclass(Decode, Manage)
    assert issubclass(Decode, FwView)

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

    # Canonical Aliases (TrustedCert*)
    assert ManageTrustedCert is Manage
    assert ManageTrustedCertPermission is Manage
    assert TrustedCert is Manage
    assert TrustedCertPermission is Manage
    assert TrustedCertRead is Read
    assert TrustedCertList is List
    assert TrustedCertView is View
    assert TrustedCertWrite is Write
    assert TrustedCertCreate is Create
    assert TrustedCertUpdate is Update
    assert TrustedCertDelete is Delete
    assert TrustedCertExecute is Execute
    assert TrustedCertDecode is Decode

    # Canonical Aliases (TrustedCerts*)
    assert ManageTrustedCerts is Manage
    assert ManageTrustedCertsPermission is Manage
    assert TrustedCerts is Manage
    assert TrustedCertsPermission is Manage
    assert TrustedCertsRead is Read
    assert TrustedCertsList is List
    assert TrustedCertsView is View
    assert TrustedCertsWrite is Write
    assert TrustedCertsCreate is Create
    assert TrustedCertsUpdate is Update
    assert TrustedCertsDelete is Delete
    assert TrustedCertsExecute is Execute
    assert TrustedCertsDecode is Decode


def test_trusted_cert_permission_string_registration():
    """Verify that TrustedCert permission names are registered in _NAME_TO_PERMISSION via init_subclass."""
    assert _NAME_TO_PERMISSION.get("trusted_cert:manage") is Manage
    assert _NAME_TO_PERMISSION.get("trusted_cert:read") is Read
    assert _NAME_TO_PERMISSION.get("trusted_cert:list") is List
    assert _NAME_TO_PERMISSION.get("trusted_cert:view") is View
    assert _NAME_TO_PERMISSION.get("trusted_cert:write") is Write
    assert _NAME_TO_PERMISSION.get("trusted_cert:create") is Create
    assert _NAME_TO_PERMISSION.get("trusted_cert:update") is Update
    assert _NAME_TO_PERMISSION.get("trusted_cert:delete") is Delete
    assert _NAME_TO_PERMISSION.get("trusted_cert:execute") is Execute
    assert _NAME_TO_PERMISSION.get("trusted_cert:decode") is Decode
    assert "trusted_cert" not in _NAME_TO_PERMISSION
    assert "manage_trusted_cert" not in _NAME_TO_PERMISSION


def test_trusted_cert_check_user_permission_rules():
    """Verify check_user_permission evaluates service permissions accurately."""
    # 1. Superadmin has everything
    superadmin = DummyUser(is_superadmin=True)
    assert check_user_permission(superadmin, Manage)
    assert check_user_permission(superadmin, Read)
    assert check_user_permission(superadmin, List)
    assert check_user_permission(superadmin, Create)
    assert check_user_permission(superadmin, Delete)
    assert check_user_permission(superadmin, Decode)

    # 2. User with Manage permission has all trusted cert actions
    cert_admin = DummyUser(permissions=[Manage])
    assert check_user_permission(cert_admin, Manage)
    assert check_user_permission(cert_admin, Read)
    assert check_user_permission(cert_admin, List)
    assert check_user_permission(cert_admin, View)
    assert check_user_permission(cert_admin, Create)
    assert check_user_permission(cert_admin, Update)
    assert check_user_permission(cert_admin, Delete)
    assert check_user_permission(cert_admin, Decode)

    # 3. User with Read has List, View, Decode, but not mutating or execute actions
    cert_reader = DummyUser(permissions=[Read])
    assert check_user_permission(cert_reader, Read)
    assert check_user_permission(cert_reader, List)
    assert check_user_permission(cert_reader, View)
    assert check_user_permission(cert_reader, Decode)
    assert not check_user_permission(cert_reader, Manage)
    assert not check_user_permission(cert_reader, Write)
    assert not check_user_permission(cert_reader, Create)
    assert not check_user_permission(cert_reader, Update)
    assert not check_user_permission(cert_reader, Delete)
    assert not check_user_permission(cert_reader, Execute)

    # 4. User with Create can create but not update, delete, or decode
    cert_creator = DummyUser(permissions=[Create])
    assert check_user_permission(cert_creator, Create)
    assert not check_user_permission(cert_creator, Write)
    assert not check_user_permission(cert_creator, Manage)
    assert not check_user_permission(cert_creator, Read)
    assert not check_user_permission(cert_creator, List)
    assert not check_user_permission(cert_creator, View)
    assert not check_user_permission(cert_creator, Update)
    assert not check_user_permission(cert_creator, Delete)
    assert not check_user_permission(cert_creator, Decode)

    # 5. User with Decode can decode and view/list (inherits View)
    cert_decoder = DummyUser(permissions=[Decode])
    assert check_user_permission(cert_decoder, Decode)
    assert not check_user_permission(cert_decoder, Create)
    assert not check_user_permission(cert_decoder, Update)
    assert not check_user_permission(cert_decoder, Delete)
    assert not check_user_permission(cert_decoder, Write)

    # 6. Default authenticated user (with FwRead) can list, view, and decode trusted certs
    default_user = DummyUser()
    assert check_user_permission(default_user, List)
    assert check_user_permission(default_user, View)
    assert check_user_permission(default_user, Decode)
    assert not check_user_permission(default_user, Create)
    assert not check_user_permission(default_user, Update)
    assert not check_user_permission(default_user, Delete)


def test_trusted_cert_endpoints_enforce_permissions(client: TestClient, test_project):
    """Verify trusted cert endpoints enforce permissions via HTTP API."""
    settings.enable_auth = True
    with client as c:
        admin_headers = _get_superadmin_headers(c)
        reg_headers = _create_and_login_user(c, admin_headers, "regular_bob")
        proj_id = test_project["id"]

        # 1. Regular user cannot create trusted cert
        resp = c.post(
            "/api/v1/trusted_certs",
            json={
                "name": "perm-cert",
                "title": "Perm Cert",
                "certificate": VALID_CERT,
                "project_id": proj_id,
            },
            headers={"X-Project-ID": str(proj_id), **reg_headers},
        )
        assert resp.status_code == 403
        assert "Permission denied" in resp.text

        # 2. Superadmin can create trusted cert
        resp = c.post(
            "/api/v1/trusted_certs",
            json={
                "name": "perm-cert",
                "title": "Perm Cert",
                "certificate": VALID_CERT,
                "project_id": proj_id,
            },
            headers={"X-Project-ID": str(proj_id), **admin_headers},
        )
        assert resp.status_code == 200, resp.text
        cert_id = resp.json()["data"]["id"]

        # 3. Regular user can view trusted cert
        resp = c.get(
            f"/api/v1/trusted_certs/{cert_id}",
            headers={"X-Project-ID": str(proj_id), **reg_headers},
        )
        assert resp.status_code == 200

        # 4. Regular user can list trusted certs
        resp = c.get(
            "/api/v1/trusted_certs",
            headers={"X-Project-ID": str(proj_id), **reg_headers},
        )
        assert resp.status_code == 200

        # 5. Regular user can decode trusted cert (read view)
        resp = c.get(
            f"/api/v1/trusted_certs/{cert_id}/_decode",
            headers={"X-Project-ID": str(proj_id), **reg_headers},
        )
        assert resp.status_code == 200
        assert "subject" in resp.json()

        # 6. Regular user cannot update trusted cert
        resp = c.put(
            f"/api/v1/trusted_certs/{cert_id}",
            json={"title": "Updated Title"},
            headers={"X-Project-ID": str(proj_id), **reg_headers},
        )
        assert resp.status_code == 403

        # 7. Regular user cannot delete trusted cert
        resp = c.delete(
            f"/api/v1/trusted_certs/{cert_id}",
            headers={
                "X-RESOURCE-NAME": "perm-cert",
                "X-Project-ID": str(proj_id),
                **reg_headers,
            },
        )
        assert resp.status_code == 403


def test_trusted_cert_endpoints_with_granted_permissions(client: TestClient, test_project):
    """Verify users with granted service permissions can access allowed endpoints."""
    settings.enable_auth = True
    with client as c:
        admin_headers = _get_superadmin_headers(c)
        proj_id = test_project["id"]
        manager_headers = _create_and_login_user(c, admin_headers, "cert_manager")
        reader_headers = _create_and_login_user(c, admin_headers, "cert_reader")
        creator_headers = _create_and_login_user(c, admin_headers, "cert_creator")

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
                "/api/v1/trusted_certs",
                json={
                    "name": "mgr-cert",
                    "title": "Mgr Cert",
                    "certificate": VALID_CERT,
                    "project_id": proj_id,
                },
                headers={"X-Project-ID": str(proj_id), **manager_headers},
            )
            assert resp.status_code == 200, resp.text
            created_id = resp.json()["data"]["id"]

            # Can update
            resp = c.put(
                f"/api/v1/trusted_certs/{created_id}",
                json={"title": "Updated Mgr Cert"},
                headers={"X-Project-ID": str(proj_id), **manager_headers},
            )
            assert resp.status_code == 200

            # Can decode
            resp = c.get(
                f"/api/v1/trusted_certs/{created_id}/_decode",
                headers={"X-Project-ID": str(proj_id), **manager_headers},
            )
            assert resp.status_code == 200

            # Can delete
            resp = c.delete(
                f"/api/v1/trusted_certs/{created_id}",
                headers={
                    "X-RESOURCE-NAME": "mgr-cert",
                    "X-Project-ID": str(proj_id),
                    **manager_headers,
                },
            )
            assert resp.status_code == 200

        # 2. User with Read permission (read-only control)
        # Create a cert as admin
        r_resp = c.post(
            "/api/v1/trusted_certs",
            json={
                "name": "view-cert-target",
                "title": "View Target",
                "certificate": VALID_CERT,
                "project_id": proj_id,
            },
            headers={"X-Project-ID": str(proj_id), **admin_headers},
        )
        assert r_resp.status_code == 200
        target_cert_id = r_resp.json()["data"]["id"]

        with patch("mindweaver.fw.permission.get_user_permissions", side_effect=_mock_perms([Read])):
            # Can list
            resp = c.get(
                "/api/v1/trusted_certs",
                headers={"X-Project-ID": str(proj_id), **reader_headers},
            )
            assert resp.status_code == 200

            # Can view
            resp = c.get(
                f"/api/v1/trusted_certs/{target_cert_id}",
                headers={"X-Project-ID": str(proj_id), **reader_headers},
            )
            assert resp.status_code == 200

            # Can decode
            resp = c.get(
                f"/api/v1/trusted_certs/{target_cert_id}/_decode",
                headers={"X-Project-ID": str(proj_id), **reader_headers},
            )
            assert resp.status_code == 200

            # CANNOT create
            resp = c.post(
                "/api/v1/trusted_certs",
                json={
                    "name": "illegal-cert-viewer",
                    "title": "Illegal",
                    "certificate": VALID_CERT,
                    "project_id": proj_id,
                },
                headers={"X-Project-ID": str(proj_id), **reader_headers},
            )
            assert resp.status_code == 403

            # CANNOT update
            resp = c.put(
                f"/api/v1/trusted_certs/{target_cert_id}",
                json={"title": "Updated by viewer"},
                headers={"X-Project-ID": str(proj_id), **reader_headers},
            )
            assert resp.status_code == 403

            # CANNOT delete
            resp = c.delete(
                f"/api/v1/trusted_certs/{target_cert_id}",
                headers={
                    "X-RESOURCE-NAME": "view-cert-target",
                    "X-Project-ID": str(proj_id),
                    **reader_headers,
                },
            )
            assert resp.status_code == 403

        # 3. User with only Create permission
        with patch("mindweaver.fw.permission.get_user_permissions", side_effect=_mock_perms([Create])):
            # Creator can create
            resp = c.post(
                "/api/v1/trusted_certs",
                json={
                    "name": "creator-cert",
                    "title": "Creator Cert",
                    "certificate": VALID_CERT,
                    "project_id": proj_id,
                },
                headers={"X-Project-ID": str(proj_id), **creator_headers},
            )
            assert resp.status_code == 200
            new_id = resp.json()["data"]["id"]

            # Creator CANNOT update
            resp = c.put(
                f"/api/v1/trusted_certs/{new_id}",
                json={"title": "Updated by creator"},
                headers={"X-Project-ID": str(proj_id), **creator_headers},
            )
            assert resp.status_code == 403

            # Creator CANNOT delete
            resp = c.delete(
                f"/api/v1/trusted_certs/{new_id}",
                headers={
                    "X-RESOURCE-NAME": "creator-cert",
                    "X-Project-ID": str(proj_id),
                    **creator_headers,
                },
            )
            assert resp.status_code == 403
