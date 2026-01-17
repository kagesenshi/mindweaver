from mindweaver.platform_service.base import (
    PlatformBase,
    PlatformService,
    PlatformStateBase,
)
from sqlmodel import Field
from typing import Any, Optional
from pydantic import field_validator, ValidationError
from mindweaver.fw.exc import FieldValidationError
import os
import asyncio
import tempfile
from kubernetes import client, config


class PgSqlPlatformState(PlatformStateBase, table=True):
    __tablename__ = "mw_pgsql_platform_state"
    platform_id: int = Field(foreign_key="mw_pgsql_platform.id", index=True)


class PgSqlPlatform(PlatformBase, table=True):
    __tablename__ = "mw_pgsql_platform"

    instances: int = Field(default=3)
    storage_size: str = Field(default="1Gi")

    # Backup configuration (using Barman Cloud Object Store)
    enable_backup: bool = Field(default=False)
    backup_destination: str | None = Field(default=None)
    backup_retention_policy: str = Field(default="30d")
    s3_storage_id: int | None = Field(default=None, foreign_key="mw_s3_storage.id")

    # Extensions
    enable_citus: bool = Field(default=False)
    enable_postgis: bool = Field(default=False)

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


class PgSqlPlatformService(PlatformService[PgSqlPlatform]):
    template_directory: str = os.path.join(
        os.path.dirname(__file__), "templates", "pgsql"
    )
    state_model: type[PgSqlPlatformState] = PgSqlPlatformState

    @classmethod
    def model_class(cls) -> type[PgSqlPlatform]:
        return PgSqlPlatform

    @classmethod
    def service_path(cls) -> str:
        return "/platform/pgsql"

    @classmethod
    def widgets(cls) -> dict[str, Any]:
        return {
            "instances": {"order": 10, "type": "range", "min": 1, "max": 7},
            "storage_size": {"order": 11},
            "enable_backup": {"order": 12, "type": "boolean"},
            "backup_destination": {"order": 13},
            "backup_retention_policy": {"order": 14},
            "s3_storage_id": {"order": 15},
            "enable_citus": {"order": 16},
            "enable_postgis": {"order": 17},
        }

    async def template_vars(self, model: PgSqlPlatform) -> dict:
        vars = model.model_dump()
        if model.s3_storage_id:
            from mindweaver.service.s3_storage import S3StorageService

            s3_svc = S3StorageService(self.request, self.session)
            s3_storage = await s3_svc.get(model.s3_storage_id)
            vars["s3_region"] = s3_storage.region
            vars["s3_access_key"] = s3_storage.access_key
            vars["s3_endpoint_url"] = s3_storage.endpoint_url
            if s3_storage.secret_key:
                from mindweaver.crypto import decrypt_password

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

    async def poll_status(self, model: PgSqlPlatform):
        """Poll the status of the CNPG cluster."""
        kubeconfig = await self.kubeconfig(model)
        namespace = await self._resolve_namespace(model)

        def _poll():
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
                    node_info = {"hostname": "unknown", "ip": "unknown"}
                    for addr in node.status.addresses:
                        if addr.type == "Hostname":
                            node_info["hostname"] = addr.address
                        elif addr.type == "InternalIP":
                            node_info["ip"] = addr.address
                    cluster_nodes.append(node_info)
            except Exception as e:
                logger.error(f"Failed to fetch nodes: {e}")

            return status, message, status_data, node_ports, cluster_nodes

        status, message, extra_data, node_ports, cluster_nodes = (
            await asyncio.to_thread(_poll)
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
        from mindweaver.fw.model import ts_now

        state.last_heartbeat = ts_now()

        await self.session.commit()


router = PgSqlPlatformService.router()
