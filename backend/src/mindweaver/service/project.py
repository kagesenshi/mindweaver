import enum
from typing import Any, Optional, Annotated
from . import NamedBase
from . import Service, before_create, before_update
from sqlmodel import Field, Column, select, func
from sqlalchemy import String, Enum as SQLEnum
import fastapi
from fastapi import Depends


class K8sClusterType(enum.StrEnum):
    IN_CLUSTER = "in-cluster"
    REMOTE = "remote"


class Project(NamedBase, table=True):
    __tablename__ = "mw_project"
    description: str = Field(default="", nullable=True)
    k8s_namespace: Optional[str] = Field(
        default=None, sa_type=String(length=32), nullable=True
    )

    k8s_cluster_type: K8sClusterType = Field(
        default=K8sClusterType.REMOTE,
        sa_column=Column(
            SQLEnum(
                K8sClusterType,
                native_enum=False,
                values_callable=lambda x: [i.value for i in x],
            ),
            nullable=False,
            server_default=K8sClusterType.REMOTE.value,
        ),
    )
    k8s_cluster_kubeconfig: Optional[str] = Field(default=None, sa_type=String)


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
            "k8s_cluster_type": {
                "order": 10,
                "type": "select",
                "options": [
                    {"label": "In-Cluster", "value": "in-cluster"},
                    {"label": "Remote", "value": "remote"},
                ],
                "label": "K8s Cluster Type",
            },
            "k8s_cluster_kubeconfig": {
                "order": 11,
                "type": "textarea",
                "column_span": 2,
                "label": "Kubeconfig",
            },
        }

    @classmethod
    def register_views(
        cls, router: fastapi.APIRouter, service_path: str, model_path: str
    ):
        model_class = cls.model_class()
        entity_type = cls.entity_type()
        path_tags = cls.path_tags()

        @router.get(
            f"{model_path}/_state",
            operation_id=f"mw-get-state-{entity_type}",
            dependencies=cls.extra_dependencies(),
            tags=path_tags,
        )
        async def get_state(
            svc: Annotated[cls, Depends(cls.get_service)],
            model: Annotated[model_class, Depends(cls.get_model)],
        ):
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
                .where(PgSqlPlatform.project_id == model.id)
                .where(PgSqlPlatformState.active == True)
            )

            result = await svc.session.exec(stmt)
            pgsql_count = result.one_or_none() or 0

            return {"pgsql": pgsql_count, "trino": 0, "spark": 0, "airflow": 0}

        super().register_views(router, service_path, model_path)


router = ProjectService.router()
