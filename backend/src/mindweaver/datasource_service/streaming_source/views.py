# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from typing import Annotated, Optional
from fastapi import Depends
from ..base import TestConnectionRequest, handle_test_connection, handle_test_connection_no_id
from .service import StreamingSourceService
from .model import StreamingSource


@StreamingSourceService.service_view(method="POST", path="/_test-connection")
async def test_streaming_connection_no_id(
    data: TestConnectionRequest,
    svc: StreamingSourceService = Depends(StreamingSourceService.get_service),
):
    return await handle_test_connection_no_id(svc, data)


@StreamingSourceService.model_view(method="POST", path="/_test-connection")
async def test_streaming_connection(
    svc: Annotated[StreamingSourceService, Depends(StreamingSourceService.get_service)],
    model: Annotated[StreamingSource, Depends(StreamingSourceService.get_model)],
    data: TestConnectionRequest = None,
):
    return await handle_test_connection(svc, model, data)
