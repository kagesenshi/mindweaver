# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from .service import KafkaPlatformService
from .model import KafkaPlatform, KafkaPlatformState
from .state import KafkaState

KafkaPlatformService.with_state()(KafkaState)
router = KafkaPlatformService.router()

__all__ = [
    "KafkaPlatformService",
    "KafkaPlatform",
    "KafkaPlatformState",
    "router",
]
