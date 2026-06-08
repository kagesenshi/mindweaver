# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from .service import SolrPlatformService
from .model import SolrPlatform, SolrPlatformState
from .state import SolrState

SolrPlatformService.with_state()(SolrState)
router = SolrPlatformService.router()

__all__ = [
    "SolrPlatformService",
    "SolrPlatform",
    "SolrPlatformState",
    "router",
]
