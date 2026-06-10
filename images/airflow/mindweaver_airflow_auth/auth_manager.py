# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from __future__ import annotations

import logging
from typing import Any

from flask_appbuilder.const import AUTH_LDAP
from airflow.providers.fab.auth_manager.fab_auth_manager import (
    FabAuthManager,
)
from airflow.providers.fab.auth_manager.models import User

log = logging.getLogger(__name__)


class MindweaverFabAuthManager(FabAuthManager):
    """
    Custom FAB auth manager supporting both LDAP and local DB login.

    Overrides ``create_token`` to use bitwise-AND when checking AUTH_TYPE,
    so LDAP is tried regardless of whether AUTH_TYPE is ``AUTH_LDAP`` alone
    or ``AUTH_LDAP | AUTH_DB``.  Local DB authentication always works as a
    fallback.
    """

    def create_token(
        self, headers: dict[str, str], body: dict[str, Any]
    ) -> User | None:
        if not body.get("username") or not body.get("password"):
            raise ValueError("Username and password must be provided")

        user: User | None = None
        auth_type = self.security_manager.auth_type

        # Try LDAP first if the auth type includes LDAP (bitwise check)
        if auth_type & AUTH_LDAP:
            try:
                user = self.security_manager.auth_user_ldap(
                    body["username"],
                    body["password"],
                    rotate_session_id=False,
                )
            except Exception:
                log.info("LDAP auth failed, falling back to DB auth", exc_info=True)

        # Fall back to local DB auth if LDAP didn't return a user
        if user is None:
            try:
                user = self.security_manager.auth_user_db(
                    body["username"],
                    body["password"],
                    rotate_session_id=False,
                )
            except Exception:
                log.info("DB auth failed", exc_info=True)

        return user
