from datetime import datetime
import abc
import asyncio
import fastapi
from fastapi import Depends
import jinja2 as j2
import kubernetes
from kubernetes import client, config, utils, dynamic
import logging
from mindweaver.fw.model import Base
from mindweaver.service.base import ProjectScopedNamedBase, ProjectScopedService
from mindweaver.service.k8s_cluster import K8sCluster, K8sClusterType
from mindweaver.service.project import Project
import os
import pydantic
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


class PlatformStateUpdate(pydantic.BaseModel):
    status: Optional[Literal["online", "offline", "pending", "error"]] = None
    active: Optional[bool] = None
    message: Optional[str] = None
    extra_data: Optional[dict[str, Any]] = None


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

        # Get Namespace
        namespace = await self._resolve_namespace(model)

        # Deploy to cluster
        await self._deploy_to_cluster(kubeconfig, full_manifest, namespace)

    async def decommission(self, model: T):
        """used to remove the applied components"""
        full_manifest = await self.render_manifests(model)
        if not full_manifest:
            return

        # Get kubeconfig
        kubeconfig = await self.kubeconfig(model)

        # Get Namespace
        namespace = await self._resolve_namespace(model)

        # Decommission from cluster
        await self._decommission_from_cluster(kubeconfig, full_manifest, namespace)

    async def _deploy_to_cluster(
        self, kubeconfig: str | None, manifest: str, default_namespace: str = "default"
    ):
        """Deploys the manifest to the kubernetes cluster using python kubernetes library"""

        # We need to run this in a thread since kubernetes library is synchronous
        def _deploy():
            if kubeconfig is None:
                config.load_incluster_config()
                k8s_client = client.ApiClient()
            else:
                # Create a temporary file for kubeconfig as some loaders prefer it
                with tempfile.NamedTemporaryFile(mode="w") as kf:
                    kf.write(kubeconfig)
                    kf.flush()

                    k8s_client = config.new_client_from_config(config_file=kf.name)

            dynamic_client = dynamic.DynamicClient(k8s_client)
            core_v1 = client.CoreV1Api(k8s_client)

            # Ensure default namespace exists
            if default_namespace != "default":
                try:
                    core_v1.read_namespace(name=default_namespace)
                except client.exceptions.ApiException as e:
                    if e.status == 404:
                        logger.info(
                            f"Namespace {default_namespace} not found, creating..."
                        )
                        ns_body = client.V1Namespace(
                            metadata=client.V1ObjectMeta(name=default_namespace)
                        )
                        core_v1.create_namespace(body=ns_body)
                        logger.info(f"Namespace {default_namespace} created")
                    else:
                        raise

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

                    # Use provided namespace, or model default if it's a namespaced resource
                    target_namespace = namespace
                    if resource.namespaced and not target_namespace:
                        target_namespace = default_namespace

                    resource.create(body=doc, namespace=target_namespace)
                    logger.info(
                        f"Created {kind} {name}"
                        + (
                            f" in namespace {target_namespace}"
                            if target_namespace
                            else ""
                        )
                    )
                except kubernetes.client.exceptions.ApiException as e:
                    if e.status == 409:  # AlreadyExists
                        logger.info(
                            f"Resource {kind} {name} already exists, skipping create"
                        )
                    else:
                        logger.error(f"Failed to create {kind} {name}: {e}")
                        raise
                except Exception as e:
                    logger.error(f"Error creating {kind} {name}: {e}")
                    raise

        try:
            await asyncio.to_thread(_deploy)
            logger.info("Successfully deployed manifests to cluster")
        except Exception as e:
            logger.error(f"Failed to deploy manifests: {e}")
            raise RuntimeError(f"Failed to deploy manifests to cluster: {e}")

    async def _decommission_from_cluster(
        self, kubeconfig: str | None, manifest: str, default_namespace: str = "default"
    ):
        """Removes the resources defined in the manifest from the kubernetes cluster"""

        def _decommission():
            if kubeconfig is None:
                config.load_incluster_config()
                k8s_client = client.ApiClient()
            else:
                with tempfile.NamedTemporaryFile(mode="w") as kf:
                    kf.write(kubeconfig)
                    kf.flush()

                    k8s_client = config.new_client_from_config(config_file=kf.name)

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

                    # Use provided namespace, or model default if it's a namespaced resource
                    target_namespace = namespace
                    if resource.namespaced and not target_namespace:
                        target_namespace = default_namespace

                    resource.delete(name=name, namespace=target_namespace)
                    logger.info(
                        f"Deleted {kind} {name}"
                        + (
                            f" in namespace {target_namespace}"
                            if target_namespace
                            else ""
                        )
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

        @router.get(
            f"{model_path}/+state",
            operation_id=f"mw-get-state-{entity_type}",
            dependencies=cls.extra_dependencies(),
            tags=path_tags,
        )
        async def get_state(
            svc: Annotated[cls, Depends(cls.get_service)],  # type: ignore
            model: Annotated[model_class, Depends(cls.get_model)],  # type: ignore
        ):
            state = await svc.platform_state(model)
            if not state:
                return {}
            return state

        @router.post(
            f"{model_path}/+state",
            operation_id=f"mw-update-state-{entity_type}",
            dependencies=cls.extra_dependencies(),
            tags=path_tags,
        )
        async def update_state(
            svc: Annotated[cls, Depends(cls.get_service)],  # type: ignore
            model: Annotated[model_class, Depends(cls.get_model)],  # type: ignore
            update: PlatformStateUpdate,
        ):
            if not svc.state_model:
                return {"status": "error", "message": "State model not defined"}

            state = await svc.platform_state(model)
            if not state:
                state = svc.state_model(platform_id=model.id)
                svc.session.add(state)

            if update.status is not None:
                state.status = update.status
            if update.active is not None:
                if update.active:
                    await svc.deploy(model)
                else:
                    await svc.decommission(model)
                state.active = update.active
            if update.message is not None:
                state.message = update.message
            if update.extra_data is not None:
                state.extra_data = update.extra_data

            state.last_heartbeat = datetime.now()

            await svc.session.commit()
            await svc.session.refresh(state)

            return state

    async def k8s_cluster(self, model: T) -> K8sCluster:
        """returns the associated K8sCluster model"""
        result = await self.session.exec(
            select(K8sCluster).where(K8sCluster.id == model.k8s_cluster_id)
        )
        cluster = result.one_or_none()
        if not cluster:
            raise ValueError(f"K8sCluster with id {model.k8s_cluster_id} not found")
        return cluster

    async def kubeconfig(self, model: T) -> str | None:
        """returns the kubeconfig string from the associated cluster"""
        cluster = await self.k8s_cluster(model)
        if cluster.type == K8sClusterType.IN_CLUSTER:
            return None
        if not cluster.kubeconfig:
            raise ValueError(f"K8sCluster {cluster.name} has no kubeconfig")
        return cluster.kubeconfig

    async def _resolve_namespace(self, model: T) -> str:
        """Resolves the namespace for the platform.
        Currently uses the project name.
        """
        result = await self.session.exec(
            select(Project).where(Project.id == model.project_id)
        )
        project = result.one_or_none()
        if not project:
            # Fallback to default if project not found (should not happen due to FK)
            return "default"
        return project.name
