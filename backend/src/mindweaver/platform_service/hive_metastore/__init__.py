# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from .service import HiveMetastorePlatformService
from .state import HiveMetastoreState
from .model import HiveMetastorePlatform, HiveMetastorePlatformState
from . import views  # noqa: F401

# Bind state and generate router
HiveMetastorePlatformService.with_state()(HiveMetastoreState)
router = HiveMetastorePlatformService.router()

__all__ = ["HiveMetastorePlatformService", "HiveMetastorePlatform", "HiveMetastorePlatformState", "router"]
