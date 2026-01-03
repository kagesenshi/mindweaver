from mindweaver.service.base import ProjectScopedNamedBase, ProjectScopedService
from mindweaver.service.k8s_cluster import K8sCluster
from sqlmodel import Field, select
from typing import TypeVar
from sqlmodel.ext.asyncio.session import AsyncSession
import jinja2 as j2
import os
import yaml
import tempfile
import asyncio
import logging
from typing import Annotated, Any
import fastapi
from fastapi import Depends
import kubernetes
from kubernetes import client, config, utils

logger = logging.getLogger(__name__)


class ClusterBase(ProjectScopedNamedBase):
    k8s_cluster_id: int = Field(foreign_key="mw_k8s_cluster.id", index=True)


T = TypeVar("T", bound=ClusterBase)


class ClusterService(ProjectScopedService[T]):
    """Base service for cluster services"""

    template_directory: str | None = None

    async def template_vars(self, model: T) -> dict:
        """returns the variables to be used in the template"""
        return model.model_dump()

    async def apply(self, model: T):
        """used to deploy/upgrade the service"""
        if not self.template_directory:
            raise ValueError(
                f"template_directory not set for {self.__class__.__name__}"
            )

        if not os.path.exists(self.template_directory):
            raise ValueError(
                f"template_directory {self.template_directory} does not exist"
            )

        # Load templates
        env = j2.Environment(loader=j2.FileSystemLoader(self.template_directory))
        templates = env.list_templates()

        rendered_manifests = []
        vars = await self.template_vars(model)

        for template_name in templates:
            if not template_name.endswith((".yaml", ".yml", ".yml.j2", ".yaml.j2")):
                continue
            template = env.get_template(template_name)
            rendered = template.render(**vars)
            rendered_manifests.append(rendered)

        if not rendered_manifests:
            logger.warning(f"No templates found in {self.template_directory}")
            return

        full_manifest = "---\n".join(rendered_manifests)

        # Get kubeconfig
        kubeconfig = await self.kubeconfig(model)

        # Apply to cluster
        await self._apply_to_cluster(kubeconfig, full_manifest)

    async def _apply_to_cluster(self, kubeconfig: str, manifest: str):
        """Applies the manifest to the kubernetes cluster using python kubernetes library"""

        # We need to run this in a thread since kubernetes library is synchronous
        def _apply():
            # Create a temporary file for kubeconfig as some loaders prefer it
            with tempfile.NamedTemporaryFile(mode="w") as kf:
                kf.write(kubeconfig)
                kf.flush()

                k8s_client = config.new_client_from_config(config_file=kf.name)

                # Apply manifest
                # utils.create_from_yaml doesn't have a native 'apply' (UPSERT)
                # so we will use create_from_yaml and handle AlreadyExists if needed.

                with tempfile.NamedTemporaryFile(mode="w") as mf:
                    mf.write(manifest)
                    mf.flush()
                    try:
                        utils.create_from_yaml(k8s_client, mf.name)
                    except utils.FailToCreateError as e:
                        # If some resources already exist, we log it
                        # For a true 'apply', we would need more complex logic.
                        for failure in e.api_exceptions:
                            if failure.status == 409:  # AlreadyExists
                                logger.info(f"Resource already exists: {failure.body}")
                            else:
                                raise

        try:
            await asyncio.to_thread(_apply)
            logger.info("Successfully applied manifests to cluster")
        except Exception as e:
            logger.error(f"Failed to apply manifests: {e}")
            raise RuntimeError(f"Failed to apply manifests to cluster: {e}")

    @classmethod
    def register_views(
        cls, router: fastapi.APIRouter, service_path: str, model_path: str
    ):
        """Register views for the service, adding the apply endpoint"""
        super().register_views(router, service_path, model_path)

        model_class = cls.model_class()
        entity_type = cls.entity_type()
        path_tags = cls.path_tags()

        @router.post(
            f"{model_path}/apply",
            operation_id=f"mw-apply-{entity_type}",
            dependencies=cls.extra_dependencies(),
            tags=path_tags,
        )
        async def apply(
            svc: Annotated[cls, Depends(cls.get_service)],  # type: ignore
            model: Annotated[model_class, Depends(cls.get_model)],  # type: ignore
        ):
            await svc.apply(model)
            return {"status": "success"}

    async def k8s_cluster(self, model: T) -> K8sCluster:
        """returns the associated K8sCluster model"""
        result = await self.session.execute(
            select(K8sCluster).where(K8sCluster.id == model.k8s_cluster_id)
        )
        cluster = result.scalar_one_or_none()
        if not cluster:
            raise ValueError(f"K8sCluster with id {model.k8s_cluster_id} not found")
        return cluster

    async def kubeconfig(self, model: T) -> str:
        """returns the kubeconfig string from the associated cluster"""
        cluster = await self.k8s_cluster(model)
        if not cluster.kubeconfig:
            raise ValueError(f"K8sCluster {cluster.name} has no kubeconfig")
        return cluster.kubeconfig
