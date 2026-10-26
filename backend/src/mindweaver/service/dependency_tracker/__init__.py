# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from .model import DependencyTracker
from .service import DependencyTrackerService
import mindweaver.service.dependency_tracker.views

router = DependencyTrackerService.router()

__all__ = ["DependencyTracker", "DependencyTrackerService", "router"]
