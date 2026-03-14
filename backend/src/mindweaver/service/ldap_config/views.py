# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import fastapi
from fastapi import HTTPException, Depends
from typing import Optional, Annotated
from pydantic import BaseModel

from mindweaver.config import settings
from mindweaver.crypto import decrypt_password, EncryptionError
from mindweaver.fw.exc import FieldValidationError, MindWeaverError
from .service import LdapConfigService, LdapConfig


class VerifyEncryptedRequest(BaseModel):
    bind_password: str


class TestConnectionRequest(BaseModel):
    server_url: Optional[str] = None
    bind_dn: Optional[str] = None
    bind_password: Optional[str] = None
    verify_ssl: Optional[bool] = None
    storage_id: Optional[int] = None


if settings.enable_test_views:

    @LdapConfigService.model_view(
        method="POST",
        path="/_verify-encrypted",
        operation_id=f"mw-verify-encrypted-{LdapConfigService.entity_type()}",
    )
    async def verify_encrypted(
        svc: Annotated[LdapConfigService, Depends(LdapConfigService.get_service)],
        model: Annotated[LdapConfig, Depends(LdapConfigService.get_model)],
        data: VerifyEncryptedRequest,
    ) -> bool:
        return svc.verify_bind_password(model, data.bind_password)


@LdapConfigService.service_view(
    method="POST",
    path="/_test-connection",
)
async def test_connection(
    data: TestConnectionRequest,
    svc: LdapConfigService = Depends(LdapConfigService.get_service),
):
    """
    Test connection to LDAP server.
    """
    server_url = data.server_url
    bind_dn = data.bind_dn
    bind_password = data.bind_password
    verify_ssl = data.verify_ssl

    if data.storage_id:
        existing = await svc.get(data.storage_id)
        if (
            existing
            and existing.bind_password
            and (not bind_password or bind_password == "__REDACTED__")
        ):
            try:
                bind_password = decrypt_password(existing.bind_password)
            except EncryptionError:
                pass

        if verify_ssl is None:
            verify_ssl = existing.verify_ssl

    try:
        if not server_url:
            raise ValueError("Server URL is required")

        if verify_ssl is None:
            verify_ssl = True

        # Optional: Test actual LDAP bind if ldap3 is available
        try:
            import ldap3
            
            # Setup server
            tls = None
            if server_url.startswith("ldaps://") or not verify_ssl:
                import ssl
                tls = ldap3.Tls(validate=ssl.CERT_REQUIRED if verify_ssl else ssl.CERT_NONE)
                
            server = ldap3.Server(server_url, get_info=ldap3.ALL, tls=tls, connect_timeout=5)
            
            # Try connecting and binding
            if bind_dn and bind_password:
                conn = ldap3.Connection(server, user=bind_dn, password=bind_password, auto_bind=True, receive_timeout=5)
                conn.unbind()
                message = f"Successfully connected and bound to LDAP server at '{server_url}'"
            else:
                conn = ldap3.Connection(server, auto_bind=True, receive_timeout=5)
                conn.unbind()
                message = f"Successfully connected anonymously to LDAP server at '{server_url}'"

            return {
                "status": "success",
                "message": message,
            }
        except ImportError:
            # If ldap3 not installed, fallback to basic socket testing
            import socket
            from urllib.parse import urlparse
            
            parsed = urlparse(server_url)
            host = parsed.hostname
            # Default LDAP port
            port = parsed.port or (636 if server_url.startswith("ldaps") else 389)
            
            if not host:
                raise ValueError(f"Invalid server URL format: {server_url}")

            with socket.create_connection((host, port), timeout=5):
                pass
                
            return {
                "status": "success",
                "message": f"Successfully opened socket to LDAP server at '{server_url}' (ldap3 not installed, bind not verified)",
            }

    except MindWeaverError:
        raise
    except Exception as e:
        raise FieldValidationError(message=str(e))
