# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from typing import Annotated, Optional
from fastapi import Depends
from ..base import TestConnectionRequest, handle_test_connection, handle_test_connection_no_id
from .service import DatabaseSourceService
from .model import DatabaseSource


@DatabaseSourceService.service_view(method="POST", path="/_test-connection")
async def test_db_connection_no_id(
    data: TestConnectionRequest,
    svc: DatabaseSourceService = Depends(DatabaseSourceService.get_service),
):
    return await handle_test_connection_no_id(svc, data)


@DatabaseSourceService.model_view(method="POST", path="/_test-connection")
async def test_db_connection(
    svc: Annotated[DatabaseSourceService, Depends(DatabaseSourceService.get_service)],
    model: Annotated[DatabaseSource, Depends(DatabaseSourceService.get_model)],
    data: TestConnectionRequest = None,
):
    return await handle_test_connection(svc, model, data)
