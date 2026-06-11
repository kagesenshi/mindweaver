# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import logging
from sqlmodel import select
from mindweaver.fw.service import Service
from .model import NameTracker

logger = logging.getLogger(__name__)


class NameTrackerService(Service[NameTracker]):
    """Service for managing NameTracker data and checking name availability."""

    @classmethod
    def model_class(cls) -> type[NameTracker]:
        """Return the model class managed by this service."""
        return NameTracker

    @classmethod
    def service_path(cls) -> str:
        """Override service path to keep it singular and clean."""
        return "/name-tracker"

    async def check_availability(self, name: str) -> bool:
        """
        Check if a name is available (returns True if not in use).
        """
        stmt = select(NameTracker).where(NameTracker.name == name)
        result = await self.session.exec(stmt)
        return result.first() is None
