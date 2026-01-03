from mindweaver.cluster_service.base import ClusterBase, ClusterService
from sqlmodel import Field
import os


class PgSqlCluster(ClusterBase, table=True):
    __tablename__ = "mw_pgsql_cluster"

    instances: int = Field(default=3)
    storage_size: str = Field(default="1Gi")

    # Backup configuration (using Barman Cloud Object Store)
    backup_destination: str | None = Field(default=None)
    backup_retention_policy: str = Field(default="30d")
    s3_storage_id: int | None = Field(default=None, foreign_key="mw_s3_storage.id")

    # Extensions
    enable_citus: bool = Field(default=False)
    enable_postgis: bool = Field(default=False)


class PgSqlClusterService(ClusterService[PgSqlCluster]):
    template_directory: str = os.path.join(
        os.path.dirname(__file__), "templates", "pgsql"
    )

    @classmethod
    def model_class(cls) -> type[PgSqlCluster]:
        return PgSqlCluster

    @classmethod
    def service_path(cls) -> str:
        return "/cluster/pgsql"

    async def template_vars(self, model: PgSqlCluster) -> dict:
        vars = model.model_dump()
        if model.s3_storage_id:
            from mindweaver.service.s3_storage import S3StorageService

            s3_svc = S3StorageService(self.request, self.session)
            s3_storage = await s3_svc.get(model.s3_storage_id)
            for k, v in s3_storage.parameters.items():
                vars[f"s3_{k}"] = v
        return vars


router = PgSqlClusterService.router()
