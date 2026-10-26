# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from mindweaver.platform_service.base import DefaultPlatformState
from .model import SupersetPlatformState


class SupersetState(DefaultPlatformState):
    """
    State handler for Superset.
    """
    async def get(self):
        state_dict = await super().get()
        if not state_dict:
            return {}
        
        return state_dict

    async def clear(self):
        """Clears Superset URI and credentials."""
        state = await self.svc.platform_state(self.model)
        if state:
            state.superset_uri = None
            state.superset_uri_ipv6 = None
            state.admin_user = None
            state.admin_password = None
        await super().clear()

