# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from mindweaver.service.base import ProjectScopedService
from fastapi import HTTPException
from pydantic import ValidationError
from mindweaver.crypto import encrypt_password, decrypt_password, EncryptionError
from mindweaver.fw.exc import FieldValidationError
from typing import Any

from .model import LdapConfig, LdapConfigSchema


class LdapConfigService(ProjectScopedService[LdapConfig]):

    @classmethod
    def model_class(cls) -> type[LdapConfig]:
        return LdapConfig

    @classmethod
    def redacted_fields(cls) -> list[str]:
        return ["bind_password"]

    async def create(self, data: LdapConfig) -> LdapConfig:
        """
        Create a new LDAP storage with validation.
        """
        try:
            LdapConfigSchema(**data.model_dump())
        except ValidationError as e:
            error = e.errors()[0]
            field = error["loc"][0] if error["loc"] else "unknown"
            message = error["msg"]
            raise FieldValidationError(
                field_location=[field],
                message=message,
            )

        return await super().create(data)

    async def update(self, model_id: int, data: LdapConfig) -> LdapConfig:
        """
        Update an existing LDAP storage with validation.
        """
        existing = await self.get(model_id)
        if not existing:
            raise HTTPException(status_code=404, detail="LDAP config not found")

        data_dict = (
            data.model_dump(exclude_unset=True)
            if hasattr(data, "model_dump")
            else dict(data)
        )

        merged_data = existing.model_dump()
        merged_data.update(data_dict)

        secret_is_encrypted = True
        bind_password = data_dict.get("bind_password")
        if bind_password:
            if bind_password == "__CLEAR__":
                merged_data["bind_password"] = ""
            elif bind_password == "__REDACTED__":
                merged_data["bind_password"] = existing.bind_password
            else:
                merged_data["bind_password"] = bind_password
                secret_is_encrypted = False

        try:
            v_data = merged_data.copy()
            if secret_is_encrypted and v_data.get("bind_password"):
                v_data["bind_password"] = "dummy"

            LdapConfigSchema(**v_data)
        except ValidationError as e:
            error = e.errors()[0]
            field = error["loc"][0] if error["loc"] else "unknown"
            message = error["msg"]
            raise FieldValidationError(
                field_location=[field],
                message=message,
            )

        return await super().update(model_id, data)

    def verify_bind_password(self, model: LdapConfig, bind_password: str) -> bool:
        """
        Verify if the provided bind password matches the encrypted one in the model.
        """
        if not model.bind_password:
            return False
        try:
            return decrypt_password(model.bind_password) == bind_password
        except EncryptionError:
            return False

    @classmethod
    def widgets(cls) -> dict[str, Any]:
        return {
            "server_url": {"order": 3, "placeholder": "ldap://example.com:389"},
            "verify_ssl": {"order": 4, "type": "boolean"},
            "bind_dn": {"order": 5, "placeholder": "uid=admin,ou=system,dc=example,dc=com"},
            "bind_password": {"order": 6, "type": "password"},
            "user_search_base": {"order": 7, "placeholder": "ou=users,dc=example,dc=com"},
            "user_search_filter": {"order": 8, "placeholder": "(&(objectClass=inetOrgPerson)(uid={0}))"},
            "username_attr": {"order": 9, "placeholder": "uid"},
            "group_search_base": {"order": 10, "placeholder": "ou=groups,dc=example,dc=com"},
            "group_search_filter": {"order": 11, "placeholder": "(&(objectClass=groupOfNames)(cn={0}))"},
            "group_member_attr": {"order": 12, "placeholder": "member"},
            "user_group_attr": {"order": 13, "placeholder": "memberOf"},
        }

