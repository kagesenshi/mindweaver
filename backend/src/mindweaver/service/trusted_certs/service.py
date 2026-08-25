# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from mindweaver.service.base import ProjectScopedService
from mindweaver.fw.exc import FieldValidationError
from mindweaver.fw.service import after_create, after_update, after_delete
from pydantic import ValidationError
from typing import Any

from .model import TrustedCert, TrustedCertConfig


class TrustedCertService(ProjectScopedService[TrustedCert]):
    """Service for managing trusted certificates."""

    @classmethod
    def model_class(cls) -> type[TrustedCert]:
        """Return the SQLModel class managed by this service."""
        return TrustedCert

    async def create(self, data: TrustedCert) -> TrustedCert:
        """Create a new trusted certificate after validation."""
        try:
            TrustedCertConfig(**data.model_dump())
        except ValidationError as e:
            error = e.errors()[0]
            field = error["loc"][0] if error["loc"] else "unknown"
            message = error["msg"]
            raise FieldValidationError(
                field_location=[field],
                message=message,
            )
        return await super().create(data)

    async def update(self, model_id: int, data: TrustedCert) -> TrustedCert:
        """Update an existing trusted certificate after validation."""
        try:
            # We only validate incoming changes if the field is present/set
            data_dict = (
                data.model_dump(exclude_unset=True)
                if hasattr(data, "model_dump")
                else dict(data)
            )
            if "certificate" in data_dict:
                TrustedCertConfig(certificate=data_dict["certificate"])
        except ValidationError as e:
            error = e.errors()[0]
            field = error["loc"][0] if error["loc"] else "unknown"
            message = error["msg"]
            raise FieldValidationError(
                field_location=[field],
                message=message,
            )
        return await super().update(model_id, data)

    @after_create()
    async def sync_certs_on_create(self, model: TrustedCert):
        """Sync trusted-certs secret immediately upon creation."""
        from mindweaver.tasks.project_tasks import sync_trusted_certs_secret_task
        sync_trusted_certs_secret_task.delay(model.project_id)

    @after_update()
    async def sync_certs_on_update(self, model: TrustedCert):
        """Sync trusted-certs secret immediately upon update."""
        from mindweaver.tasks.project_tasks import sync_trusted_certs_secret_task
        sync_trusted_certs_secret_task.delay(model.project_id)

    @after_delete()
    async def sync_certs_on_delete(self, model: TrustedCert):
        """Sync trusted-certs secret immediately upon deletion."""
        from mindweaver.tasks.project_tasks import sync_trusted_certs_secret_task
        sync_trusted_certs_secret_task.delay(model.project_id)

    @classmethod
    def widgets(cls) -> dict[str, Any]:
        """Return UI widgets for form fields."""
        return {
            "certificate": {
                "order": 3,
                "type": "textarea",
                "label": "Certificate (PEM)",
                "placeholder": "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----",
            }
        }
