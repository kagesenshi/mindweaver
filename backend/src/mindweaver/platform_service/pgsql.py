from mindweaver.platform_service.base import (
    PlatformBase,
    PlatformService,
    PlatformStateBase,
)
from sqlmodel import Field
from typing import Any, Optional
from pydantic import field_validator, ValidationError, model_validator
from mindweaver.fw.exc import FieldValidationError
import fastapi
from fastapi import Depends
import base64
import logging
import os
import asyncio
import tempfile
from typing import Any, Optional, Annotated
from kubernetes import client, config
import yaml
from mindweaver.service.s3_storage import S3StorageService
from mindweaver.crypto import decrypt_password, encrypt_password
from mindweaver.fw.model import ts_now

logger = logging.getLogger(__name__)


class PgSqlPlatformState(PlatformStateBase, table=True):
    __tablename__ = "mw_pgsql_platform_state"
    platform_id: int = Field(foreign_key="mw_pgsql_platform.id", index=True)

    db_user: Optional[str] = Field(default=None)
    db_pass: Optional[str] = Field(default=None)
    db_name: Optional[str] = Field(default=None)
    db_ca_crt: Optional[str] = Field(default=None)


class PgSqlPlatform(PlatformBase, table=True):
    __tablename__ = "mw_pgsql_platform"

    instances: int = Field(default=3)
    storage_size: str = Field(default="1Gi")
    image: str = Field(default="ghcr.io/cloudnative-pg/postgresql:18")

    # Resource configuration
    cpu_request: float = Field(default=0.5)
    cpu_limit: float = Field(default=1.0)
    mem_request: float = Field(default=1.0)
    mem_limit: float = Field(default=2.0)

    # Backup configuration (using Barman Cloud Object Store)
    enable_backup: bool = Field(default=False)
    backup_destination: str | None = Field(default=None)
    backup_retention_policy: str = Field(default="30d")
    s3_storage_id: int | None = Field(default=None, foreign_key="mw_s3_storage.id")

    @field_validator("backup_destination")
    @classmethod
    def validate_backup_destination(cls, v: str | None) -> str | None:
        if v:
            if not v.startswith("s3://"):
                raise ValueError(
                    "Backup destination must be a valid S3 URI (starts with s3://)"
                )
            if v == "s3://":
                raise ValueError("Backup destination must include a bucket name")
        return v

    @field_validator("instances")
    @classmethod
    def validate_instances(cls, v: int) -> int:
        if v < 1 or v % 2 == 0:
            raise ValueError("Instances must be an odd number (1, 3, 5, ...)")
        return v

    @model_validator(mode="after")
    def validate_resource_limits(self) -> "PgSqlPlatform":
        if self.cpu_request > self.cpu_limit:
            raise ValueError("CPU request cannot be greater than CPU limit")
        if self.mem_request > self.mem_limit:
            raise ValueError("Memory request cannot be greater than Memory limit")
        return self


class PgSqlPlatformService(PlatformService[PgSqlPlatform]):
    template_directory: str = os.path.join(
        os.path.dirname(__file__), "templates", "pgsql"
    )
    state_model: type[PgSqlPlatformState] = PgSqlPlatformState
    _image_catalog_cache: dict | None = None

    @classmethod
    def model_class(cls) -> type[PgSqlPlatform]:
        return PgSqlPlatform

    @classmethod
    def service_path(cls) -> str:
        return "/platform/pgsql"

    @classmethod
    def immutable_fields(cls) -> list[str]:
        return super().immutable_fields() + [
            "storage_size",
            "s3_storage_id",
            "image",
        ]

    @classmethod
    def load_image_catalog(cls) -> dict:
        """Loads the PostgreSQL image catalog from the configuration file."""
        if cls._image_catalog_cache is not None:
            return cls._image_catalog_cache

        config_path = os.path.join(
            os.path.dirname(__file__), "resources", "pgsql", "images.yml"
        )
        if not os.path.exists(config_path):
            cls._image_catalog_cache = {}
            return cls._image_catalog_cache

        with open(config_path, "r") as f:
            data = yaml.safe_load(f) or {}
            cls._image_catalog_cache = data
            return cls._image_catalog_cache

    @classmethod
    def widgets(cls) -> dict[str, Any]:
        catalog = cls.load_image_catalog()
        image_options = []
        for img in catalog.get("images", []):
            val = img["image"]
            label = img.get("label", val)
            image_options.append({"label": label, "value": val})

        return {
            "image": {"order": 5, "type": "select", "options": image_options},
            "instances": {"order": 10, "type": "range", "min": 1, "max": 9, "step": 2},
            "cpu_request": {
                "order": 11,
                "type": "range",
                "min": 0.5,
                "max": 16,
                "step": 0.5,
            },
            "cpu_limit": {
                "order": 12,
                "type": "range",
                "min": 0.5,
                "max": 16,
                "step": 0.5,
            },
            "mem_request": {
                "order": 13,
                "type": "range",
                "min": 1,
                "max": 64,
                "step": 1,
                "label": "Memory Request (Gi)",
            },
            "mem_limit": {
                "order": 14,
                "type": "range",
                "min": 1,
                "max": 64,
                "step": 1,
                "label": "Memory Limit (Gi)",
            },
            "storage_size": {"order": 15},
            "enable_backup": {"order": 16, "type": "boolean"},
            "backup_destination": {"order": 17},
            "backup_retention_policy": {"order": 18},
            "s3_storage_id": {"order": 19},
        }

    async def template_vars(self, model: PgSqlPlatform) -> dict:
        vars = model.model_dump()

        # Parse image catalog and version from model
        image_parts = model.image.split(":")
        if len(image_parts) == 2:
            cat_name, major_version = image_parts
            vars["image_catalog_name"] = cat_name
            vars["image_major_version"] = int(major_version)
        else:
            # Fallback
            vars["image_catalog_name"] = "default"
            vars["image_major_version"] = 15

        vars["image_name"] = model.image

        if model.s3_storage_id:
            s3_svc = S3StorageService(self.request, self.session)
            s3_storage = await s3_svc.get(model.s3_storage_id)
            vars["s3_region"] = s3_storage.region
            vars["s3_access_key"] = s3_storage.access_key
            vars["s3_endpoint_url"] = s3_storage.endpoint_url
            if s3_storage.secret_key:
                try:
                    vars["s3_secret_key"] = decrypt_password(s3_storage.secret_key)
                except Exception:
                    vars["s3_secret_key"] = s3_storage.secret_key
        return vars

    async def validate_data(self, data: Any) -> Any:
        try:
            self.model_class().model_validate(data.model_dump(), from_attributes=True)
        except ValidationError as e:
            error = e.errors()[0]
            msg = error["msg"]
            loc = error["loc"]
            raise FieldValidationError(field_location=list(loc), message=msg)
        return data

    async def clear_state(self, model: PgSqlPlatform):
        """Clears the PostgreSQL platform state."""
        state: PgSqlPlatformState = await self.platform_state(model)
        if not state:
            return

        state.db_user = None
        state.db_pass = None
        state.db_name = None
        state.db_ca_crt = None

        await super().clear_state(model)

    async def poll_status(self, model: PgSqlPlatform):
        """Poll the status of the CNPG cluster."""
        kubeconfig = await self.kubeconfig(model)
        namespace = await self._resolve_namespace(model)

        state = await self.platform_state(model)
        is_active = state.active if state else True

        def _poll(active: bool):
            if kubeconfig is None:
                config.load_incluster_config()
                k8s_client = client.ApiClient()
            else:
                with tempfile.NamedTemporaryFile(mode="w") as kf:
                    kf.write(kubeconfig)
                    kf.flush()
                    k8s_client = config.new_client_from_config(config_file=kf.name)

            custom_api = client.CustomObjectsApi(k8s_client)
            core_v1 = client.CoreV1Api(k8s_client)

            # 1. Fetch CNPG Cluster status
            try:
                cluster = custom_api.get_namespaced_custom_object(
                    group="postgresql.cnpg.io",
                    version="v1",
                    namespace=namespace,
                    plural="clusters",
                    name=model.name,
                )
                status_data = cluster.get("status", {})
                phase = status_data.get("phase", "unknown")
                instances = status_data.get("instances", 0)
                ready_instances = status_data.get("readyInstances", 0)

                status = "online" if phase == "Cluster in healthy state" else "pending"
                if phase == "Degraded":
                    status = "error"

                message = f"Phase: {phase}, Instances: {ready_instances}/{instances}"
            except client.exceptions.ApiException as e:
                if e.status == 404 and not active:
                    status = "offline"
                    message = "Cluster is stopped"
                else:
                    status = "error"
                    message = f"Failed to fetch cluster status: {str(e)}"
                status_data = {}
            except Exception as e:
                status = "error"
                message = f"Failed to fetch cluster status: {str(e)}"
                status_data = {}

            # 2. Fetch NodePort status if any
            node_ports = []
            try:
                services = core_v1.list_namespaced_service(namespace=namespace)
                for svc in services.items:
                    if svc.metadata.name.startswith(model.name):
                        if svc.spec.type == "NodePort":
                            for port in svc.spec.ports:
                                node_ports.append(
                                    {
                                        "name": svc.metadata.name,
                                        "port": port.port,
                                        "node_port": port.node_port,
                                    }
                                )
            except Exception as e:
                logger.error(f"Failed to fetch services: {e}")

            # 3. Fetch Cluster Nodes
            cluster_nodes = []
            try:
                nodes = core_v1.list_node()
                for node in nodes.items:
                    node_info = {"hostname": "unknown", "ipv4": None, "ipv6": None}
                    for addr in node.status.addresses:
                        if addr.type == "Hostname":
                            node_info["hostname"] = addr.address
                        elif addr.type == "InternalIP":
                            if ":" in addr.address:
                                node_info["ipv6"] = addr.address
                            else:
                                node_info["ipv4"] = addr.address
                    cluster_nodes.append(node_info)
            except Exception as e:
                logger.error(f"Failed to fetch nodes: {e}")

            # 4. Fetch DB Credentials from Secret
            db_credentials = {}
            try:
                secret_name = f"{model.name}-app"
                secret = core_v1.read_namespaced_secret(
                    name=secret_name, namespace=namespace
                )
                if secret.data:
                    db_credentials["db_user"] = base64.b64decode(
                        secret.data.get("username", "")
                    ).decode("utf-8")
                    db_credentials["db_name"] = base64.b64decode(
                        secret.data.get("dbname", "")
                    ).decode("utf-8")
                    db_credentials["db_ca_crt"] = base64.b64decode(
                        secret.data.get("ca.crt", "")
                    ).decode("utf-8")

                    password_raw = base64.b64decode(
                        secret.data.get("password", "")
                    ).decode("utf-8")
                    if password_raw:
                        db_credentials["db_pass"] = encrypt_password(password_raw)
            except Exception as e:
                logger.error(f"Failed to fetch secret {model.name}-app: {e}")

            # Try to fetch CA cert from -ca secret if still missing
            if not db_credentials.get("db_ca_crt"):
                try:
                    ca_secret_name = f"{model.name}-ca"
                    ca_secret = core_v1.read_namespaced_secret(
                        name=ca_secret_name, namespace=namespace
                    )
                    if ca_secret.data and "ca.crt" in ca_secret.data:
                        db_credentials["db_ca_crt"] = base64.b64decode(
                            ca_secret.data["ca.crt"]
                        ).decode("utf-8")
                except Exception as e:
                    logger.debug(f"Failed to fetch secret {model.name}-ca: {e}")

            return (
                status,
                message,
                status_data,
                node_ports,
                cluster_nodes,
                db_credentials,
            )

        status, message, extra_data, node_ports, cluster_nodes, db_credentials = (
            await asyncio.to_thread(_poll, is_active)
        )

        # Update state
        state = await self.platform_state(model)
        if not state:
            state = self.state_model(platform_id=model.id)
            self.session.add(state)

        state.status = status
        state.message = message
        state.extra_data = extra_data
        state.node_ports = node_ports
        state.cluster_nodes = cluster_nodes

        if db_credentials:
            state.db_user = db_credentials.get("db_user")
            state.db_pass = db_credentials.get("db_pass")
            state.db_name = db_credentials.get("db_name")
            state.db_ca_crt = db_credentials.get("db_ca_crt")

        state.last_heartbeat = ts_now()

    @classmethod
    def register_views(
        cls, router: fastapi.APIRouter, service_path: str, model_path: str
    ):
        """Register views for the service, overriding the state endpoint to decrypt password"""
        model_class = cls.model_class()
        entity_type = cls.entity_type()
        path_tags = cls.path_tags()

        @router.get(
            f"{model_path}/_state",
            operation_id=f"mw-get-state-{entity_type}-custom",
            dependencies=cls.extra_dependencies(),
            tags=path_tags,
        )
        async def get_state(
            svc: Annotated[cls, Depends(cls.get_service)],
            model: Annotated[model_class, Depends(cls.get_model)],
        ):
            state = await svc.platform_state(model)
            if not state:
                return {}

            # Create a copy to modify
            state_dict = state.model_dump()
            if state.db_pass:
                try:
                    state_dict["db_pass"] = decrypt_password(state.db_pass)
                except Exception:
                    pass
            return state_dict

        super().register_views(router, service_path, model_path)


router = PgSqlPlatformService.router()
