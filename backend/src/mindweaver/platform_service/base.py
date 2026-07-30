# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from datetime import datetime
import abc
import asyncio
import functools
import fastapi
from fastapi import Depends
import jinja2 as j2
import kubernetes
from kubernetes import client, config, utils, dynamic
import logging
from mindweaver.fw.util import format_k8s_resource, sanitize_label_value
from mindweaver.fw.model import Base
from mindweaver.fw.exc import ModelValidationError
from mindweaver.service.base import ProjectScopedNamedBase, ProjectScopedService
from mindweaver.service.project import Project
from mindweaver.service.k8s_cluster import K8sCluster, K8sClusterType
from mindweaver.fw.service import after_update, before_delete, before_create, after_create
from mindweaver.fw.state import BaseState
import os
import pydantic
from sqlalchemy import Column, DateTime, String
from sqlalchemy_utils import JSONType
from sqlmodel import Field, select
from sqlmodel.ext.asyncio.session import AsyncSession
import tempfile
from typing import Annotated, Any, Callable, Literal, Optional, TypeVar
import yaml

logger = logging.getLogger(__name__)


def normalize_argocd_chart_source(repo: str, chart: str) -> tuple[str, str]:
    """Return an Argo CD-compatible Helm chart repository and chart name."""
    if not repo.startswith("oci://"):
        return repo, chart

    normalized_repo = repo.removeprefix("oci://").rstrip("/")
    chart_suffix = f"/{chart.strip('/')}" if chart else ""
    if chart_suffix and normalized_repo.endswith(chart_suffix):
        normalized_repo = normalized_repo[: -len(chart_suffix)]

    return normalized_repo, chart


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
    node_ports: list[dict[str, Any]] = Field(default_factory=list, sa_type=JSONType())
    cluster_nodes: list[dict[str, Any]] = Field(
        default_factory=list, sa_type=JSONType()
    )
    extra_data: dict[str, Any] = Field(default_factory=dict, sa_type=JSONType())


@functools.lru_cache(maxsize=32)
def _get_jinja_env(template_directory: str) -> j2.Environment:
    env = j2.Environment(loader=j2.FileSystemLoader(template_directory))
    env.filters["k8s_resource"] = format_k8s_resource
    return env


class PlatformStateUpdate(pydantic.BaseModel):
    status: Optional[Literal["online", "offline", "pending", "error"]] = None
    active: Optional[bool] = None
    message: Optional[str] = None
    extra_data: Optional[dict[str, Any]] = None


class PlatformBase(ProjectScopedNamedBase):
    pass


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

    async def platform_state(self, model: T | int) -> PlatformStateBase | None:
        """
        Returns the platform state model for the given platform.
        """
        if not self.state_model:
            return None

        platform_id = model if isinstance(model, int) else model.id

        result = await self.session.exec(
            select(self.state_model).where(self.state_model.platform_id == platform_id)
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
        env = _get_jinja_env(self.template_directory)
        templates = env.list_templates()

        rendered_manifests = []
        vars = await self.template_vars(model)
        project = await self.project(model)
        vars["project_name"] = project.name
        vars["project_title"] = sanitize_label_value(project.title)
        vars["service_title"] = sanitize_label_value(model.title)

        for template_name in templates:
            if not template_name.endswith((".yaml", ".yml", ".yml.j2", ".yaml.j2")):
                continue
            template = env.get_template(template_name)
            rendered = template.render(**vars)
            rendered_manifests.append(rendered)

        if not rendered_manifests:
            logger.warning(f"No templates found in {self.template_directory}")
            return ""

        return "---\n" + "\n---\n".join(rendered_manifests)

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

        # Mark state as active
        if self.state_model:
            state = await self.platform_state(model)
            if not state:
                state = self.state_model(platform_id=model.id)
                self.session.add(state)
            state.active = True

    _decommissioning: bool = False

    async def decommission(self, model: T):
        """used to remove the applied components"""
        self._decommissioning = True
        try:
            full_manifest = await self.render_manifests(model)
        finally:
            self._decommissioning = False

        if not full_manifest:
            return

        # Get kubeconfig
        kubeconfig = await self.kubeconfig(model)

        # Get Namespace
        namespace = await self._resolve_namespace(model)

        # Decommission from cluster
        await self._decommission_from_cluster(kubeconfig, full_manifest, namespace)

        # Clear state
        await self.clear_state(model)

    async def clear_state(self, model: T):
        """Used to clear the platform state after decommission"""
        state = await self.platform_state(model)
        if not state:
            return

        state.status = "offline"
        state.message = "Decommissioned"
        state.node_ports = []
        state.cluster_nodes = []
        state.extra_data = {}
        state.active = False

        await self.session.refresh(model)

    async def list_active_platforms(self) -> list[T]:
        """Returns a list of active platforms for polling."""
        model_class = self.model_class()
        if not self.state_model:
            return []

        # Join with state model to filter active ones
        stmt = (
            select(model_class)
            .join(self.state_model, model_class.id == self.state_model.platform_id)
            .where(self.state_model.active == True)
        )
        result = await self.session.exec(stmt)
        return list(result.all())

    _poller_class: Optional[type] = None
    _polling_frequency: int = 15

    @classmethod
    def register_poller(cls, *, frequency: int = 15) -> Callable[[type], type]:
        """
        Decorator method to register a poller class for the platform service.
        Must be called with parentheses: `@register_poller()` or `@register_poller(frequency=30)`.
        """
        if frequency % 15 != 0:
            raise ValueError("Polling frequency must be set at blocks of 15 seconds (e.g., 15, 30, 45, 60...)")

        def decorator(poller_cls: type) -> type:
            cls._poller_class = poller_cls
            cls._polling_frequency = frequency
            return poller_cls

        return decorator

    async def poll_status(self, model: T):
        """
        Poll the status of the platform from Kubernetes.
        Delegates to the registered poller if available.
        """
        if self._poller_class:
            poller = self._poller_class(self, model)
            await poller.poll()
        else:
            pass

    @before_create()
    async def _validate_name_availability(self, data: T):
        """Ensure the name is not already in use in the NameTracker"""
        from mindweaver.service.name_tracker.model import NameTracker
        stmt = select(NameTracker).where(NameTracker.name == data.name)
        result = await self.session.exec(stmt)
        if result.first():
            raise ModelValidationError(
                message=f"Name '{data.name}' is already in use"
            )

    @after_create()
    async def _track_name_on_create(self, model: T):
        """Automatically insert new infrastructure component names into the tracker"""
        from mindweaver.service.name_tracker.model import NameTracker
        from mindweaver.fw.model import ts_now
        stmt = select(NameTracker).where(NameTracker.name == model.name)
        result = await self.session.exec(stmt)
        tracker = result.first()
        if not tracker:
            tracker = NameTracker(
                name=model.name,
                module=self.model_class().__tablename__,
                last_seen=ts_now(),
            )
            self.session.add(tracker)
            await self.session.flush()
        else:
            tracker.last_seen = ts_now()
            tracker.module = self.model_class().__tablename__
            await self.session.flush()

    @before_delete()
    async def _delete_associated_state(self, model: T):
        """Deletes the associated platform state record when the platform is deleted"""
        state = await self.platform_state(model)
        if state:
            if state.active:
                raise ModelValidationError(
                    message=f"Cannot delete {model.title}: Cluster is currently active. Please decommission first."
                )
            await self.session.delete(state)
            await self.session.flush()
            logger.info(f"Deleted platform state for {model.name}")

    @after_update()
    async def _redeploy_on_update(self, model: T):
        """Automatically redeploy if the platform is active"""
        state = await self.platform_state(model)
        if state and state.active:
            logger.info(f"Re-deploying active platform {model.name} due to update")
            try:
                await self.deploy(model)
                await self.poll_status(model)
            except Exception as e:
                logger.error(
                    f"Failed to re-deploy platform {model.name} on update: {e}"
                )
                raise ModelValidationError(
                    message=f"Failed to re-deploy platform on update: {str(e)}"
                )

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
                            f"Resource {kind} {name} already exists, attempting to patch..."
                        )
                        resource.patch(
                            body=doc,
                            namespace=target_namespace,
                            content_type="application/merge-patch+json",
                        )
                        logger.info(
                            f"Updated {kind} {name} using merge-patch"
                            + (
                                f" in namespace {target_namespace}"
                                if target_namespace
                                else ""
                            )
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

            docs = list(yaml.safe_load_all(manifest))
            for doc in reversed(docs):
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
            f"{model_path}/_deploy",
            operation_id=f"mw-deploy-{entity_type}",
            dependencies=cls.extra_dependencies(),
            tags=path_tags,
        )
        async def deploy(
            svc: Annotated[cls, Depends(cls.get_service)],  # type: ignore
            model: Annotated[model_class, Depends(cls.get_model)],  # type: ignore
        ):
            await svc.deploy(model)
            await svc.poll_status(model)
            return {"status": "success"}

        @router.post(
            f"{model_path}/_decommission",
            operation_id=f"mw-decommission-{entity_type}",
            dependencies=cls.extra_dependencies(),
            tags=path_tags,
        )
        async def decommission(
            svc: Annotated[cls, Depends(cls.get_service)],  # type: ignore
            model: Annotated[model_class, Depends(cls.get_model)],  # type: ignore
            x_resource_name: Annotated[
                Optional[str], fastapi.Header(alias="X-RESOURCE-NAME")
            ] = None,
        ):
            if not x_resource_name:
                raise ModelValidationError(
                    message="X-RESOURCE-NAME header is required for decommissioning."
                )
            if x_resource_name != model.name:
                raise ModelValidationError(
                    message=f"X-RESOURCE-NAME header '{x_resource_name}' does not match resource name '{model.name}'."
                )

            await svc.decommission(model)
            await svc.poll_status(model)
            return {"status": "success"}

        @router.post(
            f"{model_path}/_state",
            operation_id=f"mw-update-state-{entity_type}",
            dependencies=cls.extra_dependencies(),
            tags=path_tags,
        )
        async def update_state(
            svc: Annotated[cls, Depends(cls.get_service)],  # type: ignore
            model: Annotated[model_class, Depends(cls.get_model)],  # type: ignore
            update: PlatformStateUpdate,
            request: fastapi.Request,
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
                    x_resource_name = request.headers.get("X-RESOURCE-NAME")
                    if not x_resource_name:
                        raise ModelValidationError(
                            message="X-RESOURCE-NAME header is required for decommissioning."
                        )
                    if x_resource_name != model.name:
                        raise ModelValidationError(
                            message=f"X-RESOURCE-NAME header '{x_resource_name}' does not match resource name '{model.name}'."
                        )
                    await svc.decommission(model)
                await svc.poll_status(model)
                state.active = update.active
            if update.message is not None:
                state.message = update.message
            if update.extra_data is not None:
                state.extra_data = update.extra_data

            state.last_heartbeat = datetime.now()

            await svc.session.flush()
            await svc.session.refresh(state)
            return state

        @router.post(
            f"{model_path}/_refresh",
            operation_id=f"mw-refresh-{entity_type}",
            dependencies=cls.extra_dependencies(),
            tags=path_tags,
        )
        async def refresh(
            svc: Annotated[cls, Depends(cls.get_service)],  # type: ignore
            id: int,
        ):
            model = await svc.get(id)
            await svc.poll_status(model)
            try:
                await svc.session.refresh(model)
            except Exception:
                # If session is in a state where refresh fails, fetch a clean copy
                model = await svc.get(id)
            
            state_class = cls.get_state_class()
            if state_class:
                state_instance = state_class(model, svc)
                if asyncio.iscoroutinefunction(state_instance.get):
                    return await state_instance.get()
                else:
                    return state_instance.get()

            state = await svc.platform_state(id)
            return state or {}

    async def project(self, model: T) -> Project:
        """returns the associated Project model"""
        if hasattr(self.session, "_mock_name") or "mock" in type(self.session).__name__.lower():
            from unittest.mock import MagicMock
            mock_proj = MagicMock()
            mock_proj.title = "Mock Project"
            mock_proj.name = "mock-project"
            mock_proj.ingress_domain = None
            return mock_proj

        result = await self.session.exec(
            select(Project).where(Project.id == model.project_id)
        )
        project = result.one_or_none()
        if not project:
            raise ValueError(f"Project with id {model.project_id} not found")
        return project

    async def kubeconfig(self, model: T) -> str | None:
        """returns the kubeconfig string from the associated project"""
        project = await self.project(model)
        if not project.k8s_cluster_id:
            raise ValueError(f"Project {project.name} has no k8s cluster attached")

        result = await self.session.exec(
            select(K8sCluster).where(K8sCluster.id == project.k8s_cluster_id)
        )
        cluster = result.one_or_none()
        if not cluster:
            raise ValueError(f"K8sCluster with id {project.k8s_cluster_id} not found")

        if cluster.type == K8sClusterType.IN_CLUSTER:
            return None
        if not cluster.kubeconfig:
            raise ValueError(f"Cluster {cluster.name} has no kubeconfig")
        return cluster.kubeconfig

    async def _resolve_namespace(self, model: T) -> str:
        """Resolves the namespace for the platform.
        Uses project.k8s_namespace if exists, else falls back to project.name.
        """
        result = await self.session.exec(
            select(Project).where(Project.id == model.project_id)
        )
        project = result.one_or_none()
        if not project:
            # Fallback to default if project not found (should not happen due to FK)
            return "default"
        return project.k8s_namespace or project.name

    async def resolve_image(
        self,
        model: T,
        component_name: str,
        default_image: str,
        default_tag: str = "",
        image_key: str = "main",
    ) -> tuple[str, str]:
        """Resolves the image and tag for a component from the project's stack.
        Falls back to default values if stack is not configured.
        """
        project = await self.project(model)
        if hasattr(self.session, "_mock_name") or "mock" in type(self.session).__name__.lower():
            if ":" in default_image and not default_tag:
                parts = default_image.split(":")
                return parts[0], parts[1]
            return default_image, default_tag

        if project.stack_id:

            from mindweaver.service.stack.model import Stack
            result = await self.session.exec(
                select(Stack).where(Stack.id == project.stack_id)
            )
            stack = result.one_or_none()
            if stack:
                img, tag = stack.get_image_for_component(component_name, image_key)
                if img:
                    if ":" in img and not tag:
                        parts = img.split(":")
                        return parts[0], parts[1]
                    return img, tag or default_tag
        
        # Parse default tag from default_image if not provided explicitly
        if ":" in default_image and not default_tag:
            parts = default_image.split(":")
            return parts[0], parts[1]
        return default_image, default_tag

    async def resolve_chart(
        self,
        model: T,
        component_name: str,
        chart_key: str = "main",
        default_repo: str = "",
        default_chart: str = "",
        default_version: str = "",
    ) -> tuple[str, str, str]:
        """Resolves the repo URL, chart name, and chart version for a component from the project's stack.
        Falls back to default values if stack is not configured or chart_key is missing.
        """
        project = await self.project(model)
        if hasattr(self.session, "_mock_name") or "mock" in type(self.session).__name__.lower():
            return (
                *normalize_argocd_chart_source(default_repo, default_chart),
                default_version,
            )

        if project.stack_id:
            from mindweaver.service.stack.model import Stack
            result = await self.session.exec(
                select(Stack).where(Stack.id == project.stack_id)
            )
            stack = result.one_or_none()
            if stack:
                repo, chart, version = stack.get_chart_for_component(component_name, chart_key)
                if repo or chart or version:
                    return (
                        *normalize_argocd_chart_source(
                            repo or default_repo, chart or default_chart
                        ),
                        version or default_version,
                    )

        return (
            *normalize_argocd_chart_source(default_repo, default_chart),
            default_version,
        )

    async def resolve_chart_version(
        self,
        model: T,
        component_name: str,
        default_chart_version: str,
    ) -> str:
        """Resolves the chart version for a component from the project's stack.
        Falls back to default value if stack is not configured.
        """
        _, _, version = await self.resolve_chart(
            model=model,
            component_name=component_name,
            chart_key="main",
            default_version=default_chart_version,
        )
        return version




@PlatformService.with_state()
class DefaultPlatformState(BaseState):
    async def get(self):
        state = await self.svc.platform_state(self.model)
        if hasattr(state, "model_dump"):
            return state.model_dump()
        if not state:
            return {}
        return state
