# SPDX-FileCopyrightText: Copyright © 2025 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from sqlmodel import select, func
from mindweaver.fw.state import BaseState
from .service import ProjectService


@ProjectService.with_state()
class ProjectState(BaseState):
    async def get(self):
        from mindweaver.platform_service.pgsql import (
            PgSqlPlatform,
            PgSqlPlatformState,
        )

        stmt = (
            select(func.count(PgSqlPlatform.id))
            .join(
                PgSqlPlatformState,
                PgSqlPlatform.id == PgSqlPlatformState.platform_id,
                isouter=True,
            )
            .where(PgSqlPlatform.project_id == self.model.id)
            .where(PgSqlPlatformState.active == True)
        )

        result = await self.svc.session.exec(stmt)
        pgsql_count = result.one_or_none() or 0

        return {"pgsql": pgsql_count, "trino": 0, "spark": 0, "airflow": 0}
