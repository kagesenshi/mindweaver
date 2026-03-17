# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from .service import SupersetPlatformService
from .state import SupersetState
from .model import SupersetPlatform, SupersetPlatformState

# Bind state and generate router
SupersetPlatformService.with_state()(SupersetState)
router = SupersetPlatformService.router()

__all__ = ["SupersetPlatformService", "SupersetPlatform", "SupersetPlatformState", "router"]
