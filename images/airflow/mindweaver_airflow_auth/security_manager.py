# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from __future__ import annotations

import logging

from airflow.providers.fab.auth_manager.security_manager.override import (
    FabAirflowSecurityManagerOverride,
)
from airflow.providers.fab.auth_manager.models import User

log = logging.getLogger(__name__)


class MindweaverFabAirflowSecurityManagerOverride(FabAirflowSecurityManagerOverride):
    """
    Custom security manager that falls back to local DB auth when LDAP fails.

    This allows users created by the createUserJob (e.g. ``admin``) to log in
    even when ``AUTH_TYPE`` is ``AUTH_LDAP``.
    """

    def auth_user_ldap(self, username: str, password: str, rotate_session_id: bool = True) -> User | None:
        user = super().auth_user_ldap(username, password, rotate_session_id=rotate_session_id)
        if user is not None:
            return user

        log.info("LDAP auth failed for %s, falling back to DB auth", username)
        return self.auth_user_db(username, password, rotate_session_id=rotate_session_id)
