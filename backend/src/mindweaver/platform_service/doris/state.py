# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from mindweaver.platform_service.base import DefaultPlatformState
from mindweaver.crypto import decrypt_password


class DorisState(DefaultPlatformState):
    """Custom state representation for Apache Doris platform."""

    async def get(self) -> dict:
        """Returns the current runtime state and connection details with credentials."""
        state_dict = await super().get()
        if not state_dict:
            return {}

        state_dict["db_user"] = "root"
        state_dict["admin_user"] = "root"

        admin_pass = self.model.admin_password
        if admin_pass:
            try:
                admin_pass = decrypt_password(admin_pass)
            except Exception:
                admin_pass = self.model.admin_password

        state_dict["db_pass"] = admin_pass
        state_dict["admin_password"] = admin_pass

        return state_dict
