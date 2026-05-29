# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from mindweaver.platform_service.base import DefaultPlatformState
from mindweaver.crypto import decrypt_password
from .model import TrinoPlatformState


class TrinoState(DefaultPlatformState):
    async def get(self):
        state_dict = await super().get()
        if not state_dict:
            return {}
        
        state_dict["db_user"] = "trino"
        admin_pass = "admin"
        if self.model.admin_password:
            try:
                admin_pass = decrypt_password(self.model.admin_password)
            except Exception:
                admin_pass = self.model.admin_password
        state_dict["db_pass"] = admin_pass

        return state_dict

