# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from fastapi import Depends
from .service import K8sClusterService
from .state import K8sClusterState

# Register state
K8sClusterService.with_state()(K8sClusterState)


@K8sClusterService.model_view("POST", "/_refresh")
async def refresh_status_view(
    id: int, svc: K8sClusterService = Depends(K8sClusterService.get_service)
):
    """Manual status refresh view"""
    model = await svc.get(id)
    await svc.poll_status(model)
    return {"status": "success"}
