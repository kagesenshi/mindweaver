# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from fastapi import Depends
from sqlmodel import select
from .service import ProjectService
from .model import Project
from .state import ProjectState

# Register state
ProjectService.with_state()(ProjectState)
