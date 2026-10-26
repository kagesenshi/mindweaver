# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from mindweaver.platform_service.base import DefaultPlatformState


class KafkaState(DefaultPlatformState):
    """Kafka state representation."""

    async def clear(self):
        """Clears Kafka platform endpoints."""
        state = await self.svc.platform_state(self.model)
        if state:
            state.kafka_url = None
            state.kafka_url_ipv6 = None
        await super().clear()

