# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from mindweaver.platform_service.base import DefaultPlatformState
from mindweaver.crypto import decrypt_password


class SolrState(DefaultPlatformState):
    async def get(self):
        """Returns the platform state, decrypting credentials if present."""
        state_dict = await super().get()
        if not state_dict:
            return {}

        state = await self.svc.platform_state(self.model)
        if state:
            val = getattr(state, "admin_password", None)
            if val:
                try:
                    state_dict["admin_password"] = decrypt_password(val)
                except Exception:
                    pass
        return state_dict
