# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from typing import Annotated, Optional
from fastapi import Depends
from ..base import TestConnectionRequest, handle_test_connection, handle_test_connection_no_id
from .service import APISourceService
from .model import APISource


@APISourceService.service_view(method="POST", path="/_test-connection")
async def test_api_connection_no_id(
    data: TestConnectionRequest,
    svc: APISourceService = Depends(APISourceService.get_service),
):
    return await handle_test_connection_no_id(svc, data)


@APISourceService.model_view(method="POST", path="/_test-connection")
async def test_api_connection(
    svc: Annotated[APISourceService, Depends(APISourceService.get_service)],
    model: Annotated[APISource, Depends(APISourceService.get_model)],
    data: TestConnectionRequest = None,
):
    return await handle_test_connection(svc, model, data)
