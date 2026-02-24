# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from fastapi import Depends
from sqlmodel import select
from .service import ProjectService
from .model import Project, ProjectStatus
from .state import ProjectState

# Register state
ProjectService.with_state()(ProjectState)


@ProjectService.model_view("POST", "/_refresh")
async def refresh_status_view(
    id: int, svc: ProjectService = Depends(ProjectService.get_service)
):
    """Manual status refresh view"""
    model = await svc.get(id)
    await svc.poll_status(model)
    return {"status": "success"}
