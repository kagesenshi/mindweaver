# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from sqlmodel import Field
from typing import Optional
from mindweaver.platform_service.base import PlatformStateBase, DefaultPlatformState
from mindweaver.crypto import decrypt_password


class PgSqlPlatformState(PlatformStateBase, table=True):
    __tablename__ = "mw_pgsql_platform_state"
    platform_id: int = Field(foreign_key="mw_pgsql_platform.id", index=True)

    db_user: Optional[str] = Field(default=None)
    db_pass: Optional[str] = Field(default=None)
    db_name: Optional[str] = Field(default=None)
    db_ca_crt: Optional[str] = Field(default=None)


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
