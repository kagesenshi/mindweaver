# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from typing import Annotated, Optional
from fastapi import Depends
from ..base import TestConnectionRequest, handle_test_connection, handle_test_connection_no_id
from .service import WebSourceService
from .model import WebSource


@WebSourceService.service_view(method="POST", path="/_test-connection")
async def test_web_connection_no_id(
    data: TestConnectionRequest,
    svc: WebSourceService = Depends(WebSourceService.get_service),
):
    return await handle_test_connection_no_id(svc, data)


@WebSourceService.model_view(method="POST", path="/_test-connection")
async def test_web_connection(
    svc: Annotated[WebSourceService, Depends(WebSourceService.get_service)],
    model: Annotated[WebSource, Depends(WebSourceService.get_model)],
    data: TestConnectionRequest = None,
):
    return await handle_test_connection(svc, model, data)
