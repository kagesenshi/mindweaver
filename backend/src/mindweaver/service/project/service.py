import logging
from typing import Any

from mindweaver.service import Service, before_create, before_update

from .model import Project

logger = logging.getLogger(__name__)


class ProjectService(Service[Project]):
    @classmethod
    def model_class(cls) -> type[Project]:
        return Project

    @before_create
    async def _set_default_namespace(self, model: Project):
        """Set default k8s_namespace to project name if not provided"""
        if not model.k8s_namespace:
            model.k8s_namespace = model.name

    @before_update
    async def _handle_namespace_update(self, model: Project, data: Project):
        """Handle k8s_namespace update, ensuring it defaults to name if cleared"""
        if hasattr(data, "k8s_namespace") and not data.k8s_namespace:
            data.k8s_namespace = model.name

    @classmethod
    def widgets(cls) -> dict[str, Any]:

        return {
            "description": {"order": 5, "column_span": 2},
            "k8s_namespace": {"order": 6, "column_span": 2, "label": "K8S Namespace"},
            "k8s_cluster_id": {
                "order": 10,
                "label": "K8S Cluster",
            },
        }
