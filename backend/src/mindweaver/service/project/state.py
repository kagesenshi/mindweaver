# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from sqlmodel import select, func
from mindweaver.fw.state import BaseState
from .model import ProjectStatus


class ProjectState(BaseState):
    """
    Project state provides an overview of project resources and cluster health.
    """

    async def get(self):
        from mindweaver.platform_service.pgsql import (
            PgSqlPlatform,
            PgSqlPlatformState,
        )

        # Get service counts (legacy from views.py)
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

        # Get cluster status
        stmt_status = select(ProjectStatus).where(
            ProjectStatus.project_id == self.model.id
        )
        result_status = await self.svc.session.exec(stmt_status)
        status_model = result_status.one_or_none()

        status_data = {}
        if status_model:
            status_data = status_model.model_dump(
                exclude={"id", "project_id", "last_update"}
            )
            status_data["last_update"] = status_model.last_update.isoformat()

        return {
            "pgsql": pgsql_count,
            "trino": 0,
            "spark": 0,
            "airflow": 0,
            "cluster": status_data,
        }
