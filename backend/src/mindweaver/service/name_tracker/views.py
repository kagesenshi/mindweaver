# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from fastapi import Depends
from typing import Annotated
from mindweaver.fw.permission import require
from .service import NameTrackerService
from .permission import CheckAvailability


@NameTrackerService.service_view(
    method="GET",
    path="/_check-availability",
    dependencies=[require(CheckAvailability)],
)
async def check_availability_view(
    name: str,
    svc: Annotated[NameTrackerService, Depends(NameTrackerService.get_service)],
) -> dict:
    """
    Endpoint for checking name availability.
    """
    is_available = await svc.check_availability(name)
    return {"available": is_available}
