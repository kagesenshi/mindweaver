# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from fastapi import Depends
from sqlmodel import select
from .service import ProjectService
from .model import Project
from .state import ProjectState

# Register state
ProjectService.with_state()(ProjectState)


@ProjectService.model_view("POST", "/_refresh")
async def refresh_project_status_view(
    id: int, svc: ProjectService = Depends(ProjectService.get_service)
):
    """Manual project status refresh view"""
    from mindweaver.service.k8s_cluster.service import K8sClusterService
    model = await svc.get(id)
    if model.k8s_cluster_id:
        cluster_svc = K8sClusterService(svc.request, svc.session)
        cluster_model = await cluster_svc.get(model.k8s_cluster_id)
        await cluster_svc.poll_status(cluster_model)
    return {"status": "success"}

