# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from .model import NameTracker
from .service import NameTrackerService
import mindweaver.service.name_tracker.views

router = NameTrackerService.router()

__all__ = ["NameTracker", "NameTrackerService", "router"]
