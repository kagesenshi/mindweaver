from mindweaver.platform_service.base import PlatformBase, PlatformService
from sqlmodel import Field
from typing import Any
import os


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


class PgSqlPlatformService(PlatformService[PgSqlPlatform]):
    template_directory: str = os.path.join(
        os.path.dirname(__file__), "templates", "pgsql"
    )

    @classmethod
    def model_class(cls) -> type[PgSqlPlatform]:
        return PgSqlPlatform

    @classmethod
    def service_path(cls) -> str:
        return "/platform/pgsql"

    @classmethod
    def widgets(cls) -> dict[str, Any]:
        return {
            "instances": {"order": 10},
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
            for k, v in s3_storage.parameters.items():
                vars[f"s3_{k}"] = v
        return vars


router = PgSqlPlatformService.router()
