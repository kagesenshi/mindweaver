# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from mindweaver.platform_service.base import DefaultPlatformState
from mindweaver.crypto import decrypt_password


class RangerState(DefaultPlatformState):
    async def get(self):
        state_dict = await super().get()
        if not state_dict:
            return {}

        state = await self.svc.platform_state(self.model)
        if state:
            for field in [
                "admin_password",
                "keyadmin_password",
                "tagsync_password",
                "usersync_password",
            ]:
                val = getattr(state, field, None)
                if val:
                    try:
                        state_dict[field] = decrypt_password(val)
                    except Exception:
                        pass
        return state_dict
