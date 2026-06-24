# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from .service import NifiPlatformService
from .model import NifiPlatform, NifiPlatformState
from .state import NifiState

NifiPlatformService.with_state()(NifiState)
router = NifiPlatformService.router()

__all__ = [
    "NifiPlatformService",
    "NifiPlatform",
    "NifiPlatformState",
    "router",
]
