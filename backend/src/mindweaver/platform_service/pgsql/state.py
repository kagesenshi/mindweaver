# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from sqlmodel import Field
from typing import Optional
from mindweaver.platform_service.base import PlatformStateBase, DefaultPlatformState
from mindweaver.crypto import decrypt_password


from .model import PgSqlPlatformState


class PgSqlState(DefaultPlatformState):
    async def get(self):
        state_dict = await super().get()
        if not state_dict:
            return {}

        state = await self.svc.platform_state(self.model)
        if state and state.db_pass:
            try:
                state_dict["db_pass"] = decrypt_password(state.db_pass)
            except Exception:
                pass
        return state_dict
