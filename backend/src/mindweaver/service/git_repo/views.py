# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import os
import tempfile
import asyncio
from typing import Optional
from pydantic import BaseModel
from fastapi import Depends
from mindweaver.fw.exc import FieldValidationError
from mindweaver.crypto import decrypt_password
from .service import GitRepoService


class TestConnectionRequest(BaseModel):
    url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    ssh_key_id: Optional[int] = None
    repo_id: Optional[int] = None


async def run_git_ls_remote(
    url: str,
    auth_type: str,
    username: Optional[str] = None,
    password: Optional[str] = None,
    private_key: Optional[str] = None,
) -> tuple[bool, str]:
    """Runs git ls-remote HEAD against the target repo URL to verify connectivity."""
    env = os.environ.copy()
    temp_key_file = None

    try:
        if auth_type == "none":
            cmd = ["git", "ls-remote", url, "HEAD"]
        elif auth_type == "http":
            from urllib.parse import urlparse, urlunparse
            import urllib.parse

            parsed = urlparse(url)
            netloc = parsed.netloc
            if password:
                if username:
                    encoded_user = urllib.parse.quote(username)
                    encoded_pass = urllib.parse.quote(password)
                    netloc = f"{encoded_user}:{encoded_pass}@{netloc}"
                else:
                    encoded_pass = urllib.parse.quote(password)
                    netloc = f"{encoded_pass}@{netloc}"
            test_url = urlunparse(parsed._replace(netloc=netloc))
            cmd = ["git", "ls-remote", test_url, "HEAD"]
        elif auth_type == "ssh":
            if not private_key:
                raise ValueError("SSH Private Key is missing or empty")

            fd, temp_key_file = tempfile.mkstemp()
            try:
                os.write(fd, private_key.encode("utf-8"))
            finally:
                os.close(fd)

            os.chmod(temp_key_file, 0o600)
            env["GIT_SSH_COMMAND"] = (
                f"ssh -i {temp_key_file} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
            )
            cmd = ["git", "ls-remote", url, "HEAD"]
        else:
            raise ValueError(f"Unknown authentication type: {auth_type}")

        # Run process safely
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            err_msg = stderr.decode("utf-8").strip() or "git ls-remote failed"
            if password:
                err_msg = err_msg.replace(password, "******")
            raise ValueError(err_msg)

        return True, "Successfully connected to the Git repository"

    finally:
        if temp_key_file and os.path.exists(temp_key_file):
            try:
                os.remove(temp_key_file)
            except Exception:
                pass


@GitRepoService.service_view(
    method="POST",
    path="/_test-connection",
)
async def test_connection(
    data: TestConnectionRequest,
    svc: GitRepoService = Depends(GitRepoService.get_service),
):
    """
    Test connection to Git repository.
    If repo_id is provided, resolve missing/redacted fields from existing DB record.
    """
    url = data.url
    username = data.username
    password = data.password
    ssh_key_id = data.ssh_key_id

    # Resolve from DB if editing existing connection
    if data.repo_id:
        existing = await svc.get(data.repo_id)
        if existing:
            if not url:
                url = existing.url
            if not username:
                username = existing.username
            if not password or password == "__REDACTED__":
                if existing.password:
                    try:
                        password = decrypt_password(existing.password)
                    except Exception:
                        pass
            if ssh_key_id is None:
                ssh_key_id = existing.ssh_key_id

    if not url:
        raise FieldValidationError(
            field_location=["url"],
            message="Repository URL is required"
        )

    # Dynamically infer authentication type from URL & fields
    url_lower = url.lower()
    is_ssh = url_lower.startswith("git@") or url_lower.startswith("ssh://") or url_lower.startswith("git+ssh://")

    if is_ssh:
        auth_type = "ssh"
    elif username or password or ssh_key_id:
        # If they specified an SSH Key but it's not a standard SSH URL, let's treat it as SSH
        if ssh_key_id:
            auth_type = "ssh"
        else:
            auth_type = "http"
    else:
        auth_type = "none"

    # If SSH auth, fetch the associated SSHKey and decrypt private key
    private_key = None
    if auth_type == "ssh":
        if not ssh_key_id:
            raise FieldValidationError(
                field_location=["ssh_key_id"],
                message="SSH Key is required for SSH authentication"
            )
        from mindweaver.service.ssh_key.service import SSHKeyService
        ssh_key_svc = SSHKeyService(svc.request, svc.session)
        ssh_key_record = await ssh_key_svc.get(ssh_key_id)
        if not ssh_key_record:
            raise FieldValidationError(
                field_location=["ssh_key_id"],
                message="Associated SSH Key not found"
            )
        if ssh_key_record.private_key:
            try:
                private_key = decrypt_password(ssh_key_record.private_key)
            except Exception:
                raise FieldValidationError(
                    field_location=["ssh_key_id"],
                    message="Failed to decrypt the associated SSH private key"
                )

    try:
        success, msg = await run_git_ls_remote(
            url=url,
            auth_type=auth_type,
            username=username,
            password=password,
            private_key=private_key
        )
        return {"status": "success", "message": msg}
    except Exception as e:
        raise FieldValidationError(message=str(e))
