# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from .service import AirflowPlatformService
from .state import AirflowState
from .model import AirflowPlatform, AirflowPlatformState

# Bind state and generate router
AirflowPlatformService.with_state()(AirflowState)
router = AirflowPlatformService.router()

__all__ = ["AirflowPlatformService", "AirflowPlatform", "AirflowPlatformState", "router"]
