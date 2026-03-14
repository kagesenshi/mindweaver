# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import logging
from .service import HiveMetastorePlatformService

logger = logging.getLogger(__name__)


@HiveMetastorePlatformService.service_view(
    method="GET",
    path="/_chart-versions",
    operation_id="mw-hms-chart-versions",
)
async def get_chart_versions() -> dict:
    """
    Return available Hive Metastore chart versions.
    Static list to avoid external authentication complexity.
    """
    versions = [
        {"label": "0.1.6", "value": "0.1.6"},
        {"label": "0.1.5", "value": "0.1.5"},
        {"label": "0.1.4", "value": "0.1.4"},
    ]
    return {"data": versions}
