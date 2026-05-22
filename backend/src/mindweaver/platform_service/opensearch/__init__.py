# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from .service import OpenSearchPlatformService
from .model import OpenSearchPlatform, OpenSearchPlatformState
from .state import OpenSearchState

OpenSearchPlatformService.with_state()(OpenSearchState)
router = OpenSearchPlatformService.router()

__all__ = [
    "OpenSearchPlatformService",
    "OpenSearchPlatform",
    "OpenSearchPlatformState",
    "router",
]
