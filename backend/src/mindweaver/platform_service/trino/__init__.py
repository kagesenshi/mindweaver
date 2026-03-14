# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from .service import TrinoPlatformService
from .state import TrinoState
from .model import TrinoPlatform, TrinoPlatformState
from . import views  # noqa: F401

# Bind state and generate router
TrinoPlatformService.with_state()(TrinoState)
router = TrinoPlatformService.router()

__all__ = ["TrinoPlatformService", "TrinoPlatform", "TrinoPlatformState", "router"]
