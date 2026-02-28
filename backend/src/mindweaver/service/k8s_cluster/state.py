# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from sqlmodel import select
from mindweaver.fw.state import BaseState
from .model import K8sClusterStatus


class K8sClusterState(BaseState):
    """
    Cluster state provides an overview of cluster health.
    """

    async def get(self):
        # Get cluster status
        stmt_status = select(K8sClusterStatus).where(
            K8sClusterStatus.k8s_cluster_id == self.model.id
        )
        result_status = await self.svc.session.exec(stmt_status)
        status_model = result_status.one_or_none()

        status_data = {}
        if status_model:
            status_data = status_model.model_dump(
                exclude={"id", "k8s_cluster_id", "last_update"}
            )
            status_data["last_update"] = status_model.last_update.isoformat()

        return status_data
