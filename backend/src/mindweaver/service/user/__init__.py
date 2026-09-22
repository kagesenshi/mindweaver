# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from .service import UserService, ChangePasswordRequest

router = UserService.router()

__all__ = ["UserService", "ChangePasswordRequest", "router"]
