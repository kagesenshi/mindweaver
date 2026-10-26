# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from mindweaver.platform_service.base import DefaultPlatformState
from .model import HiveMetastorePlatformState


class HiveMetastoreState(DefaultPlatformState):
    async def get(self):
        state_dict = await super().get()
        if not state_dict:
            return {}
        
        # Add any additional state processing here if needed
        return state_dict

    async def clear(self):
        """Clears Hive Metastore endpoints."""
        state = await self.svc.platform_state(self.model)
        if state:
            state.hms_uri = None
            state.iceberg_uri = None
        await super().clear()

