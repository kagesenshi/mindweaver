# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from typing import Any
from mindweaver.service.base import ProjectScopedService
from ..base import DataSourceServiceBase
from .model import StreamingSource


class StreamingSourceService(
    DataSourceServiceBase, ProjectScopedService[StreamingSource]
):
    @classmethod
    def model_class(cls) -> type[StreamingSource]:
        return StreamingSource

    @classmethod
    def service_path(cls) -> str:
        return ""

    @classmethod
    def model_path(cls) -> str:
        return "/{id}"

    @classmethod
    def widgets(cls) -> dict[str, Any]:
        widgets = super().widgets()
        widgets.update(
            {
                "broker_type": {
                    "type": "select",
                    "order": 20,
                    "label": "Broker Type",
                    "options": [
                        {"label": "Kafka", "value": "kafka"},
                        {"label": "Kinesis", "value": "kinesis"},
                        {"label": "RabbitMQ", "value": "rabbitmq"},
                    ],
                },
                "bootstrap_servers": {"order": 21, "label": "Bootstrap Servers"},
                "topic": {"order": 22, "label": "Topic"},
                "group_id": {"order": 23, "label": "Group ID"},
                "extra_config": {"order": 102, "type": "key-value"},
            }
        )
        return widgets

    async def perform_test_connection(self, config: dict[str, Any]) -> dict[str, Any]:
        # Placeholder as requested in previous turns
        return {
            "status": "success",
            "message": "Streaming source configuration saved. Connection test not fully implemented.",
        }
