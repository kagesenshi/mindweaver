# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from sqlmodel import SQLModel
from ..model import NamedBase
from ..hooks import before_create, before_update, S
from ..hash import get_password_hash


class HashingHandlerMixin:
    """
    Mixin for services that handle fields that should be hashed when stored
    in the database and redacted when returned to the client.
    """

    @classmethod
    def hashed_fields(cls) -> list[str]:
        """
        Return a list of field names that should be hashed.
        """
        return []

    @before_create
    async def _handle_hashed_create(self, model: S):
        for field in self.hashed_fields():
            val = getattr(model, field, None)
            if val:
                setattr(model, field, get_password_hash(val))

    @before_update
    async def _handle_hashed_update(self, model: S, data: NamedBase):
        data_dict = data.model_dump(exclude_unset=True)
        for field in self.hashed_fields():
            if field in data_dict:
                val = data_dict[field]
                if val == "__REDACTED__":
                    # Keep existing value (set data field to current model value)
                    setattr(data, field, getattr(model, field))
                elif val == "__CLEAR__":
                    setattr(data, field, "")
                elif val:
                    setattr(data, field, get_password_hash(val))

    async def post_process_model(self, model: S) -> S:
        """
        Redact hashed fields before returning to client.
        """
        if hasattr(super(), "post_process_model"):
            model = await super().post_process_model(model)

        hashed_fields = self.hashed_fields()
        if not hashed_fields:
            return model

        # Check if any field needs redaction
        has_sensitive_data = any(getattr(model, field, None) for field in hashed_fields)
        if not has_sensitive_data:
            return model

        # Create a copy and redact
        model_dict = model.model_dump()
        for field in hashed_fields:
            if field in model_dict:
                model_dict[field] = "__REDACTED__"

        return model.__class__.model_validate(model_dict)
