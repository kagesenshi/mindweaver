# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import os
import logging
import asyncio
import tempfile
import base64
from typing import Any, Optional, Literal
from kubernetes import client, config
from pydantic import ValidationError

from mindweaver.fw.exc import FieldValidationError
from mindweaver.fw.service import VALIDATION_MODE
from mindweaver.platform_service.base import PlatformService
from mindweaver.crypto import decrypt_password
from mindweaver.fw.model import ts_now
from mindweaver.platform_service.pgsql.service import PgSqlPlatformService
from mindweaver.service.s3_storage.service import S3StorageService

from .model import HiveMetastorePlatform, HiveMetastorePlatformState
from .state import HiveMetastoreState

logger = logging.getLogger(__name__)


class HiveMetastorePlatformService(PlatformService[HiveMetastorePlatform]):
    template_directory: str = os.path.join(os.path.dirname(__file__), "templates")
    state_model: type[HiveMetastorePlatformState] = HiveMetastorePlatformState

    @classmethod
    def model_class(cls) -> type[HiveMetastorePlatform]:
        return HiveMetastorePlatform

    @classmethod
    def service_path(cls) -> str:
        return "/platform/hive-metastore"


    @classmethod
    def widgets(cls) -> dict[str, Any]:
        return {
            "replica_count": {
                "order": 10,
                "type": "range",
                "min": 1,
                "max": 10,
                "step": 1,
            },
            "cpu_request": {
                "order": 11,
                "type": "range",
                "min": 0.1,
                "max": 16,
                "step": 0.1,
            },
            "cpu_limit": {
                "order": 12,
                "type": "range",
                "min": 0.1,
                "max": 16,
                "step": 0.1,
            },
            "mem_request": {
                "order": 13,
                "type": "range",
                "min": 0.5,
                "max": 64,
                "step": 0.5,
                "label": "Memory Request (Gi)",
            },
            "mem_limit": {
                "order": 14,
                "type": "range",
                "min": 0.5,
                "max": 64,
                "step": 0.5,
                "label": "Memory Limit (Gi)",
            },
            "database_id": {"order": 20, "label": "PostgreSQL"},
            "s3_storage_id": {
                "order": 21,
                "label": "S3 Storage",
            },
            "iceberg_enabled": {
                "order": 30,
                "type": "boolean",
                "label": "Enable IcebergREST Endpoint",
            },
            "disable_s3_cert_checking": {
                "order": 35,
                "type": "boolean",
                "label": "Disable S3 Certificate Checking",
            },
            "warehouse_dir": {"order": 40, "label": "Warehouse Directory"},
        }

    async def template_vars(self, model: HiveMetastorePlatform) -> dict:
        vars = model.model_dump()
        vars["image"], _ = await self.resolve_image(
            model, "hive_metastore", "ghcr.io/kagesenshi/mindweaver/hive-metastore:latest"
        )
        chart_repo, chart_name, chart_version = await self.resolve_chart(
            model, "hive_metastore", "main", "oci://ghcr.io/kagesenshi/mindweaver/charts/hive-metastore", "hive-metastore", "0.1.8"
        )
        vars["chart_repo"] = chart_repo
        vars["chart_name"] = chart_name
        vars["chart_version"] = chart_version
        vars["override_image"] = True
        vars["namespace"] = await self._resolve_namespace(model)


        # Resolve Database Connection
        pgsql_svc = await PgSqlPlatformService.get_service(self.request, self.session)
        pgsql_model = await pgsql_svc.get(model.database_id)
        pgsql_state = await pgsql_svc.platform_state(pgsql_model)

        if not getattr(self, "_decommissioning", False) and (not pgsql_state or not pgsql_state.active):
            raise ValueError(
                f"Managed PostgreSQL cluster {pgsql_model.name} is not active"
            )

        vars["db_host"] = (
            f"{pgsql_model.name}-pooler-rw.{vars['namespace']}.svc.cluster.local"
        )
        vars["db_port"] = 5432
        vars["db_user"] = pgsql_state.db_user if pgsql_state else "app"
        vars["db_name"] = pgsql_state.db_name if pgsql_state else "app"
        db_pass_enc = pgsql_state.db_pass if pgsql_state else ""
        if db_pass_enc:
            try:
                vars["db_pass"] = decrypt_password(db_pass_enc)
            except Exception:
                vars["db_pass"] = db_pass_enc
        else:
            vars["db_pass"] = ""

        # Resolve S3 Storage Connection
        if model.s3_storage_id:
            s3_svc = await S3StorageService.get_service(self.request, self.session)
            s3_model = await s3_svc.get(model.s3_storage_id)
            vars["s3_endpoint_url"] = s3_model.endpoint_url
            vars["s3_region"] = s3_model.region
            vars["s3_use_ssl"] = (
                "true" if s3_model.endpoint_url.startswith("https://") else "false"
            )
            vars["aws_access_key_id"] = s3_model.access_key
            if s3_model.secret_key:
                try:
                    vars["aws_secret_access_key"] = decrypt_password(
                        s3_model.secret_key
                    )
                except Exception:
                    vars["aws_secret_access_key"] = s3_model.secret_key
            else:
                vars["aws_secret_access_key"] = ""

        return vars


# Register the poller class
from .poller import HiveMetastorePoller
