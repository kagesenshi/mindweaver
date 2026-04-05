# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from .service import RangerPlatformService
from .state import RangerState
from .model import RangerPlatform, RangerPlatformState

# Bind state and generate router
RangerPlatformService.with_state()(RangerState)
router = RangerPlatformService.router()

__all__ = ["RangerPlatformService", "RangerPlatform", "RangerPlatformState", "router"]
