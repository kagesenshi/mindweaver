# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import httpx
from typing import Optional
from pydantic import BaseModel
from fastapi import Depends
from mindweaver.fw.exc import FieldValidationError
from mindweaver.crypto import decrypt_password
from .service import ContainerRegistryService


class TestConnectionRequest(BaseModel):
    url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    registry_id: Optional[int] = None


async def run_oci_login_check(
    url: str,
    username: str,
    password: str,
) -> tuple[bool, str]:
    """Runs a login test against the OCI registry using HTTP token auth handshake."""
    # Normalize URL scheme
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    from urllib.parse import urlparse
    parsed = urlparse(url)
    netloc = parsed.netloc

    # Handle standard docker hub alias
    if netloc == "docker.io":
        netloc = "registry-1.docker.io"
        url = url.replace("docker.io", "registry-1.docker.io")

    v2_url = f"{url.rstrip('/')}/v2/"

    async with httpx.AsyncClient(verify=False) as client:
        try:
            resp = await client.get(v2_url)
        except Exception as e:
            return False, f"Failed to connect to registry: {e}"

        if resp.status_code == 200:
            return True, "Successfully connected (No authentication required)"

        if resp.status_code == 401:
            auth_header = resp.headers.get("www-authenticate")
            if not auth_header:
                # Fallback to direct Basic Auth
                resp = await client.get(v2_url, auth=(username, password))
                if resp.status_code == 200:
                    return True, "Successfully connected using Basic Authentication"
                return False, f"Authentication failed: {resp.status_code}"

            if auth_header.startswith("Bearer"):
                params = {}
                for part in auth_header[7:].split(","):
                    if "=" in part:
                        k, v = part.split("=", 1)
                        params[k.strip()] = v.strip().strip('"')

                realm = params.get("realm")
                service = params.get("service")
                if not realm:
                    return False, "Invalid Www-Authenticate header from registry"

                token_params = {"service": service} if service else {}
                token_params["scope"] = "repository:library/hello-world:pull"  # standard testing scope

                try:
                    token_resp = await client.get(realm, params=token_params, auth=(username, password))
                except Exception as e:
                    return False, f"Failed to fetch authentication token: {e}"

                if token_resp.status_code != 200:
                    return False, f"Failed to authenticate: {token_resp.status_code} {token_resp.text}"

                token_data = token_resp.json()
                token = token_data.get("token") or token_data.get("access_token")
                if not token:
                    return False, "Registry token response did not contain a token"

                # Verify token
                headers = {"Authorization": f"Bearer {token}"}
                resp = await client.get(v2_url, headers=headers)
                if resp.status_code == 200:
                    return True, "Successfully connected using Token Authentication"
                return False, f"Token verification failed: {resp.status_code}"
            else:
                resp = await client.get(v2_url, auth=(username, password))
                if resp.status_code == 200:
                    return True, "Successfully connected using Basic Authentication"
                return False, f"Authentication failed: {resp.status_code}"

        return False, f"Unexpected registry response: {resp.status_code}"


@ContainerRegistryService.service_view(
    method="POST",
    path="/_test-connection",
)
async def test_connection(
    data: TestConnectionRequest,
    svc: ContainerRegistryService = Depends(ContainerRegistryService.get_service),
):
    """
    Test connection to Container Registry.
    If registry_id is provided, resolve missing/redacted fields from existing DB record.
    """
    url = data.url
    username = data.username
    password = data.password

    if data.registry_id:
        existing = await svc.get(data.registry_id)
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

    if not url:
        raise FieldValidationError(
            field_location=["url"],
            message="Registry URL is required"
        )
    if not username:
        raise FieldValidationError(
            field_location=["username"],
            message="Username is required"
        )
    if not password:
        raise FieldValidationError(
            field_location=["password"],
            message="Password/Token is required"
        )

    try:
        success, msg = await run_oci_login_check(
            url=url,
            username=username,
            password=password,
        )
        if not success:
            raise FieldValidationError(message=msg)
        return {"status": "success", "message": msg}
    except Exception as e:
        raise FieldValidationError(message=str(e))
