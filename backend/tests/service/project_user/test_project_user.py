# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import pytest
import hashlib
import bcrypt
from fastapi.testclient import TestClient
from sqlmodel import select
from mindweaver.service.project.model import Project
from mindweaver.service.project_user.model import ProjectLocalUser


def test_project_local_user_crud(client: TestClient, test_project):
    """
    Test CRUD operations for ProjectLocalUser.
    """
    proj_id = test_project["id"]
    headers = {"X-Project-ID": str(proj_id)}

    # 1. Negative Test: Mismatched Passwords
    resp_fail = client.post(
        "/api/v1/project-local-users",
        json={
            "username": "testuser-fail",
            "email": "testuser-fail@example.com",
            "password": "supersecurepassword123",
            "password_confirm": "differentpassword",
            "project_id": proj_id,
        },
        headers=headers,
    )
    assert resp_fail.status_code == 422
    assert "Passwords do not match" in resp_fail.text

    # 2. Create
    resp = client.post(
        "/api/v1/project-local-users",
        json={
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "supersecurepassword123",
            "password_confirm": "supersecurepassword123",
            "project_id": proj_id,
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    user_data = resp.json()["data"]
    assert user_data["username"] == "testuser"
    assert user_data["email"] == "testuser@example.com"
    assert "password" not in user_data

    # Verify hashes in database directly (bypassing API redaction)
    from mindweaver.fw.model import get_engine
    from sqlmodel.ext.asyncio.session import AsyncSession
    import asyncio

    async def get_db_user():
        engine = get_engine()
        async with AsyncSession(engine) as session:
            stmt = select(ProjectLocalUser).where(ProjectLocalUser.id == user_data["id"])
            res = await session.exec(stmt)
            return res.one()

    db_user = asyncio.run(get_db_user())
    assert db_user.username == "testuser"
    # Bcrypt
    assert bcrypt.checkpw("supersecurepassword123".encode("utf-8"), db_user.password_hash_bcrypt.encode("utf-8"))
    # MD5
    assert db_user.password_hash_md5 == hashlib.md5("supersecurepassword123".encode("utf-8")).hexdigest()
    # SHA-256
    assert db_user.password_hash_sha256 == hashlib.sha256("supersecurepassword123".encode("utf-8")).hexdigest()
    # SHA-512
    assert db_user.password_hash_sha512 == hashlib.sha512("supersecurepassword123".encode("utf-8")).hexdigest()

    # 3. Update without changing password (providing __REDACTED__)
    resp_update = client.put(
        f"/api/v1/project-local-users/{user_data['id']}",
        json={
            "username": "testuser-updated",
            "email": "testuser-updated@example.com",
            "password": "__REDACTED__",
            "project_id": proj_id,
        },
        headers=headers,
    )
    assert resp_update.status_code == 200, resp_update.text
    updated_user = resp_update.json()["data"]
    assert updated_user["username"] == "testuser-updated"
    assert updated_user["email"] == "testuser-updated@example.com"

    db_user_after_update = asyncio.run(get_db_user())
    assert db_user_after_update.password_hash_bcrypt == db_user.password_hash_bcrypt

    # 4. Update with new password
    resp_update_pw = client.put(
        f"/api/v1/project-local-users/{user_data['id']}",
        json={
            "username": "testuser-updated",
            "email": "testuser-updated@example.com",
            "password": "newpassword456",
            "password_confirm": "newpassword456",
            "project_id": proj_id,
        },
        headers=headers,
    )
    assert resp_update_pw.status_code == 200, resp_update_pw.text
    db_user_new_pw = asyncio.run(get_db_user())
    assert bcrypt.checkpw("newpassword456".encode("utf-8"), db_user_new_pw.password_hash_bcrypt.encode("utf-8"))
    assert db_user_new_pw.password_hash_bcrypt != db_user.password_hash_bcrypt

    # 5. List
    resp_list = client.get("/api/v1/project-local-users", headers=headers)
    assert resp_list.status_code == 200, resp_list.text
    users = resp_list.json()["data"]
    assert len(users) == 1
    assert users[0]["username"] == "testuser-updated"

    # 6. Delete
    headers_del = {**headers, "X-RESOURCE-NAME": "testuser-updated"}
    resp_del = client.delete(f"/api/v1/project-local-users/{user_data['id']}", headers=headers_del)
    assert resp_del.status_code == 200, resp_del.text

    resp_list_after = client.get("/api/v1/project-local-users", headers=headers)
    assert len(resp_list_after.json()["data"]) == 0

