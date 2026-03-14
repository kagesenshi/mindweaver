# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from mindweaver.platform_service.base import DefaultPlatformState
from .model import TrinoPlatformState


class TrinoState(DefaultPlatformState):
    async def get(self):
        state_dict = await super().get()
        if not state_dict:
            return {}
        
        # Add any additional state processing here if needed
        return state_dict
