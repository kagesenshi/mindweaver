# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from mindweaver.platform_service.base import DefaultPlatformState
from mindweaver.crypto import decrypt_password
from .model import TrinoPlatformState


class TrinoState(DefaultPlatformState):
    async def get(self):
        """
        Returns the platform state dictionary with decrypted credentials.
        """
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

        if self.model.ranger_id:
            state_dict["ranger_user"] = "ranger"
            ranger_pass = "ranger"
            if self.model.ranger_user_password:
                try:
                    ranger_pass = decrypt_password(self.model.ranger_user_password)
                except Exception:
                    ranger_pass = self.model.ranger_user_password
            state_dict["ranger_pass"] = ranger_pass

        return state_dict


