from datetime import datetime
import abc
import asyncio
import fastapi
from fastapi import Depends
import jinja2 as j2
import kubernetes
from kubernetes import client, config, utils
import logging
from mindweaver.fw.model import Base
from mindweaver.service.base import ProjectScopedNamedBase, ProjectScopedService
from mindweaver.service.k8s_cluster import K8sCluster
import os
from sqlalchemy import Column, DateTime, String
from sqlalchemy_utils import JSONType
from sqlmodel import Field, select
from sqlmodel.ext.asyncio.session import AsyncSession
import tempfile
from typing import Annotated, Any, Literal, Optional, TypeVar
import yaml

logger = logging.getLogger(__name__)


class PlatformStateBase(Base):
    """Base class for platform deployment status tracking"""

    platform_id: int = Field(index=True)
    status: Literal["online", "offline", "pending", "error"] = Field(
        default="pending", index=True, sa_type=String()
    )
    active: bool = Field(default=True)
    message: Optional[str] = Field(default=None)
    last_heartbeat: Optional[datetime] = Field(
        default=None, sa_type=DateTime(timezone=True)
    )
    extra_data: dict[str, Any] = Field(default_factory=dict, sa_type=JSONType())


class PlatformBase(ProjectScopedNamedBase):
    k8s_cluster_id: int = Field(foreign_key="mw_k8s_cluster.id", index=True)


T = TypeVar("T", bound=PlatformBase)


class PlatformService(ProjectScopedService[T], abc.ABC):
    """Base service for cluster services"""

    template_directory: str | None = None
    state_model: type[PlatformStateBase] | None = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if abc.ABC not in cls.__bases__:
            if cls.state_model is None:
                raise TypeError(f"Class {cls.__name__} must define state_model")

    async def platform_state(self, model: T) -> PlatformStateBase | None:
        """
        Returns the platform state model for the given platform.
        """
        if not self.state_model:
            return None

        result = await self.session.exec(
            select(self.state_model).where(self.state_model.platform_id == model.id)
        )
        return result.one_or_none()

    async def template_vars(self, model: T) -> dict:
        """returns the variables to be used in the template"""
        return model.model_dump()

    async def render_manifests(self, model: T) -> str:
        """renders the manifests from the template directory"""
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
            return ""

        return "---\n".join(rendered_manifests)

    async def deploy(self, model: T):
        """used to deploy/upgrade the service"""
        full_manifest = await self.render_manifests(model)
        if not full_manifest:
            return

        # Get kubeconfig
        kubeconfig = await self.kubeconfig(model)

        # Deploy to cluster
        await self._deploy_to_cluster(kubeconfig, full_manifest)

    async def decommission(self, model: T):
        """used to remove the applied components"""
        full_manifest = await self.render_manifests(model)
        if not full_manifest:
            return

        # Get kubeconfig
        kubeconfig = await self.kubeconfig(model)

        # Decommission from cluster
        await self._decommission_from_cluster(kubeconfig, full_manifest)

    async def _deploy_to_cluster(self, kubeconfig: str, manifest: str):
        """Deploys the manifest to the kubernetes cluster using python kubernetes library"""

        # We need to run this in a thread since kubernetes library is synchronous
        def _deploy():
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
            await asyncio.to_thread(_deploy)
            logger.info("Successfully deployed manifests to cluster")
        except Exception as e:
            logger.error(f"Failed to deploy manifests: {e}")
            raise RuntimeError(f"Failed to deploy manifests to cluster: {e}")

    async def _decommission_from_cluster(self, kubeconfig: str, manifest: str):
        """Removes the resources defined in the manifest from the kubernetes cluster"""

        def _decommission():
            with tempfile.NamedTemporaryFile(mode="w") as kf:
                kf.write(kubeconfig)
                kf.flush()

                k8s_client = config.new_client_from_config(config_file=kf.name)
                from kubernetes import dynamic

                dynamic_client = dynamic.DynamicClient(k8s_client)

                for doc in yaml.safe_load_all(manifest):
                    if not doc:
                        continue

                    kind = doc.get("kind")
                    api_version = doc.get("apiVersion")
                    metadata = doc.get("metadata", {})
                    name = metadata.get("name")
                    namespace = metadata.get("namespace")

                    if not kind or not name:
                        continue

                    try:
                        resource = dynamic_client.resources.get(
                            api_version=api_version, kind=kind
                        )
                        resource.delete(name=name, namespace=namespace)
                        logger.info(
                            f"Deleted {kind} {name}"
                            + (f" in namespace {namespace}" if namespace else "")
                        )
                    except kubernetes.client.exceptions.ApiException as e:
                        if e.status == 404:
                            logger.info(
                                f"Resource {kind} {name}"
                                + (f" in namespace {namespace}" if namespace else "")
                                + " not found, skipping"
                            )
                        else:
                            logger.error(f"Failed to delete {kind} {name}: {e}")
                            raise
                    except Exception as e:
                        logger.error(f"Error deleting {kind} {name}: {e}")
                        raise

        try:
            await asyncio.to_thread(_decommission)
            logger.info("Successfully decommissioned resources from cluster")
        except Exception as e:
            logger.error(f"Failed to decommission resources: {e}")
            raise RuntimeError(f"Failed to decommission resources from cluster: {e}")

    @classmethod
    def register_views(
        cls, router: fastapi.APIRouter, service_path: str, model_path: str
    ):
        """Register views for the service, adding the deploy endpoint"""
        super().register_views(router, service_path, model_path)

        model_class = cls.model_class()
        entity_type = cls.entity_type()
        path_tags = cls.path_tags()

        @router.post(
            f"{model_path}/+deploy",
            operation_id=f"mw-deploy-{entity_type}",
            dependencies=cls.extra_dependencies(),
            tags=path_tags,
        )
        async def deploy(
            svc: Annotated[cls, Depends(cls.get_service)],  # type: ignore
            model: Annotated[model_class, Depends(cls.get_model)],  # type: ignore
        ):
            await svc.deploy(model)
            return {"status": "success"}

        @router.post(
            f"{model_path}/+decommission",
            operation_id=f"mw-decommission-{entity_type}",
            dependencies=cls.extra_dependencies(),
            tags=path_tags,
        )
        async def decommission(
            svc: Annotated[cls, Depends(cls.get_service)],  # type: ignore
            model: Annotated[model_class, Depends(cls.get_model)],  # type: ignore
        ):
            await svc.decommission(model)
            return {"status": "success"}

    async def k8s_cluster(self, model: T) -> K8sCluster:
        """returns the associated K8sCluster model"""
        result = await self.session.exec(
            select(K8sCluster).where(K8sCluster.id == model.k8s_cluster_id)
        )
        cluster = result.one_or_none()
        if not cluster:
            raise ValueError(f"K8sCluster with id {model.k8s_cluster_id} not found")
        return cluster

    async def kubeconfig(self, model: T) -> str:
        """returns the kubeconfig string from the associated cluster"""
        cluster = await self.k8s_cluster(model)
        if not cluster.kubeconfig:
            raise ValueError(f"K8sCluster {cluster.name} has no kubeconfig")
        return cluster.kubeconfig
