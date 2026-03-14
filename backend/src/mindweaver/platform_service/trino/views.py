# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import logging
from .service import TrinoPlatformService

logger = logging.getLogger(__name__)


@TrinoPlatformService.service_view(
    method="GET",
    path="/_chart-versions",
    operation_id="mw-trino-chart-versions",
)
async def get_chart_versions() -> dict:
    """
    Return available Trino chart versions.
    Static list to avoid external authentication complexity.
    """
    versions = [
        {"label": "1.41.0", "value": "1.41.0"},
    ]
    return {"data": versions}
