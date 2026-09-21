# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from .service import DorisPlatformService
from .state import DorisState
from .model import DorisPlatform, DorisPlatformState

# Bind state and generate router
DorisPlatformService.with_state()(DorisState)
router = DorisPlatformService.router()

# Register the poller class
from .poller import DorisPoller

__all__ = ["DorisPlatformService", "DorisPlatform", "DorisPlatformState", "DorisPoller", "router"]
