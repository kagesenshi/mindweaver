# SPDX-FileCopyrightText: Copyright © 2025 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from .service import ProjectService
from .model import Project
import mindweaver.service.project.views
import mindweaver.service.project.actions


router = ProjectService.router()

__all__ = ["ProjectService", "Project", "router"]
