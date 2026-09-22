# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import logging
from fastapi import Depends
from mindweaver.fw.permission import require
from .service import K8sClusterService
from .state import K8sClusterState
from .permission import Refresh

logger = logging.getLogger(__name__)

# Register state
K8sClusterService.with_state()(K8sClusterState)


@K8sClusterService.model_view("POST", "/_refresh", dependencies=[require(Refresh)])
async def refresh_status_view(
    id: int, svc: K8sClusterService = Depends(K8sClusterService.get_service)
):
    """Manual status refresh view"""
    model = await svc.get(id)
    await svc.poll_status(model)
    return {"status": "success"}


