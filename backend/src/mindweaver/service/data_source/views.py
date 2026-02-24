# SPDX-FileCopyrightText: Copyright © 2025 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from typing import Any, Optional, Annotated
from pydantic import BaseModel
from fastapi import Depends
from mindweaver.crypto import decrypt_password, EncryptionError
from .service import DataSourceService, DataSource


class TestConnectionRequest(BaseModel):
    # Allow overriding fields for testing "dirty" state, effectively optional
    driver: Optional[str] = None
    type: Optional[str] = None  # Alias for driver used in tests
    host: Optional[str] = None
    port: Optional[int] = None
    resource: Optional[str] = None
    login: Optional[str] = None
    password: Optional[str] = None
    api_key: Optional[str] = None  # Alias for password used in tests
    enable_ssl: Optional[bool] = None
    verify_ssl: Optional[bool] = None
    parameters: Optional[dict[str, Any]] = None

    def get_driver(self) -> Optional[str]:
        return self.driver or self.type

    def get_password(self) -> Optional[str]:
        return self.password or self.api_key


@DataSourceService.service_view(
    method="POST",
    path="/_test-connection",
)
async def test_connection_no_id(
    data: TestConnectionRequest,
    svc: DataSourceService = Depends(DataSourceService.get_service),
):
    """
    Test connection to a data source without a saved record.
    """
    config = {
        "driver": data.get_driver(),
        "host": data.host,
        "port": data.port,
        "resource": data.resource,
        "login": data.login,
        "password": data.get_password(),
        "enable_ssl": data.enable_ssl,
        "verify_ssl": data.verify_ssl,
        "parameters": data.parameters or {},
    }
    return await svc.perform_test_connection(config)


@DataSourceService.model_view(
    method="POST",
    path="/_test-connection",
)
async def test_connection(
    svc: Annotated[DataSourceService, Depends(DataSourceService.get_service)],
    model: Annotated[DataSource, Depends(DataSourceService.get_model)],
    data: TestConnectionRequest = None,
):
    """
    Test connection to a data source.
    Uses stored configuration, optionally overridden by provided data.
    """
    existing = model

    # Merge existing with overrides
    config = {
        "driver": existing.driver,
        "host": existing.host,
        "port": existing.port,
        "resource": existing.resource,
        "login": existing.login,
        "password": existing.password,
        "enable_ssl": existing.enable_ssl,
        "verify_ssl": existing.verify_ssl,
        "parameters": existing.parameters or {},
    }

    if data:
        overrides = data.model_dump(exclude_unset=True)
        # Handle special field mappings for overrides
        if data.type:
            overrides["driver"] = data.type
        if data.api_key:
            overrides["password"] = data.api_key

        for k, v in overrides.items():
            if v is not None:
                config[k] = v

    # Decrypt password if it's from DB and hasn't been overridden
    is_using_stored_password = not data or (
        data.password is None and data.api_key is None
    )

    if is_using_stored_password and existing.password:
        try:
            config["password"] = decrypt_password(existing.password)
        except EncryptionError:
            pass

    return await svc.perform_test_connection(config)
