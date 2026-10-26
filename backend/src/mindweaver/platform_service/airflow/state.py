# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from mindweaver.platform_service.base import DefaultPlatformState
from .model import AirflowPlatformState


class AirflowState(DefaultPlatformState):
    """
    State handler for Airflow.
    """
    async def get(self):
        state_dict = await super().get()
        if not state_dict:
            return {}

        return state_dict

    async def clear(self):
        """Clears Airflow endpoints and credentials."""
        state = await self.svc.platform_state(self.model)
        if state:
            state.airflow_uri = None
            state.airflow_uri_ipv6 = None
            state.admin_user = None
            state.admin_password = None
        await super().clear()

