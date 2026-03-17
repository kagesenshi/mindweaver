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
