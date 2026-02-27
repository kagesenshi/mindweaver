# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from fastapi import HTTPException
from sqlmodel import SQLModel
from mindweaver.crypto import encrypt_password, EncryptionError
from ..model import NamedBase
from ..hooks import before_create, before_update, S


class SecretHandlerMixin:
    """
    Mixin for services that handle sensitive fields that should be redacted
    when returned to the client and encrypted when stored in the database.
    """

    @classmethod
    def redacted_fields(cls) -> list[str]:
        """
        Return a list of field names that should be redacted/encrypted.
        """
        return []

    @before_create
    async def _handle_redacted_create(self, model: S):
        for field in self.redacted_fields():
            val = getattr(model, field, None)
            if val:
                try:
                    setattr(model, field, encrypt_password(val))
                except EncryptionError as e:
                    raise HTTPException(
                        status_code=500, detail=f"Failed to encrypt {field}: {str(e)}"
                    )

    @before_update
    async def _handle_redacted_update(self, model: S, data: NamedBase):
        data_dict = data.model_dump(exclude_unset=True)
        for field in self.redacted_fields():
            if field in data_dict:
                val = data_dict[field]
                if val == "__REDACTED__":
                    # Keep existing value (set data field to current model value)
                    setattr(data, field, getattr(model, field))
                elif val == "__CLEAR__":
                    setattr(data, field, "")
                elif val:
                    try:
                        setattr(data, field, encrypt_password(val))
                    except EncryptionError as e:
                        raise HTTPException(
                            status_code=500,
                            detail=f"Failed to encrypt {field}: {str(e)}",
                        )

    async def post_process_model(self, model: S) -> S:
        """
        Redact sensitive fields before returning to client.
        Creates a copy to avoid modifying the session model.
        """
        if hasattr(super(), "post_process_model"):
            model = await super().post_process_model(model)

        redacted_fields = self.redacted_fields()
        if not redacted_fields:
            return model

        # Check if any field needs redaction
        has_sensitive_data = any(
            getattr(model, field, None) for field in redacted_fields
        )
        if not has_sensitive_data:
            return model

        # Create a copy and redact
        model_dict = model.model_dump()
        for field in redacted_fields:
            if field in model_dict:
                model_dict[field] = "__REDACTED__"

        return model.__class__.model_validate(model_dict)
