# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from mindweaver.platform_service.base import (
    PlatformBase,
    PlatformService,
)
from mindweaver.fw.service import VALIDATION_MODE
from sqlmodel import Field
from typing import Any, Optional, Literal
from pydantic import field_validator, ValidationError, model_validator
from mindweaver.fw.exc import FieldValidationError
import base64
import logging
import os
import asyncio
import tempfile
from kubernetes import client, config
import yaml
from mindweaver.service.s3_storage import S3StorageService
from mindweaver.crypto import encrypt_password, decrypt_password
from mindweaver.fw.model import ts_now

from .state import PgSqlState

logger = logging.getLogger(__name__)


from .model import PgSqlPlatform, PgSqlPlatformState


class PgSqlPlatformService(PlatformService[PgSqlPlatform]):
    template_directory: str = os.path.join(os.path.dirname(__file__), "templates")
    state_model: type[PgSqlPlatformState] = PgSqlPlatformState

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
        ]

    @classmethod
    def widgets(cls) -> dict[str, Any]:
        return {
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
            "backup_schedule": {"order": 17, "label": "Backup Schedule (Cron)"},
            "backup_destination": {"order": 18},
            "backup_retention_policy": {"order": 19},
            "s3_storage_id": {"order": 20},
            "pgbouncer_pool_mode": {
                "order": 25,
                "label": "PgBouncer Pool Mode",
                "type": "select",
                "options": [
                    {"label": "Transaction (recommended)", "value": "transaction"},
                    {"label": "Session", "value": "session"},
                    {"label": "Statement", "value": "statement"},
                ],
            },
            "pgbouncer_pool_size": {
                "order": 26,
                "label": "PgBouncer Pool Size",
                "type": "range",
                "min": 10,
                "max": 500,
                "step": 10,
            },
        }

    async def template_vars(self, model: PgSqlPlatform) -> dict:
        vars = model.model_dump()

        # Resolve namespace
        vars["namespace"] = await self._resolve_namespace(model)

        chart_repo, chart_name, chart_version = await self.resolve_chart(
            model, "pgsql", "main", "https://cloudnative-pg.github.io/charts", "cluster", "0.5.0"
        )
        vars["chart_repo"] = chart_repo
        vars["chart_name"] = chart_name
        vars["chart_version"] = chart_version

        # Parse image catalog and version from model
        image_resolved, tag_resolved = await self.resolve_image(
            model, "pgsql", "ghcr.io/cloudnative-pg/postgresql:18"
        )
        vars["image_name"] = f"{image_resolved}:{tag_resolved}"
        if tag_resolved.isdigit():
            vars["image_catalog_name"] = image_resolved
            vars["image_major_version"] = int(tag_resolved)
        else:
            vars["image_catalog_name"] = "default"
            vars["image_major_version"] = 18


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

PgSqlPlatformService.with_state()(PgSqlState)
router = PgSqlPlatformService.router()

# Register the poller class
from .poller import PgSQLPoller
