# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import os
import logging
import asyncio
import tempfile
from typing import Any, Optional
from kubernetes import client, config
from mindweaver.platform_service.base import PlatformService
from mindweaver.fw.model import ts_now

from .model import KafkaPlatform, KafkaPlatformState

logger = logging.getLogger(__name__)


class KafkaPlatformService(PlatformService[KafkaPlatform]):
    """Platform service for Apache Kafka."""

    template_directory: str = os.path.join(os.path.dirname(__file__), "templates")
    state_model: type[KafkaPlatformState] = KafkaPlatformState

    @classmethod
    def model_class(cls) -> type[KafkaPlatform]:
        """Returns the model class managed by this service."""
        return KafkaPlatform

    @classmethod
    def service_path(cls) -> str:
        """Returns the REST path prefix for this service."""
        return "/platform/kafka"


    @classmethod
    def widgets(cls) -> dict[str, Any]:
        """Provides UI configuration widgets for metadata rendering."""
        return {
            "storage_size": {"order": 7, "label": "Storage Size"},
            "replica_count": {
                "order": 10,
                "type": "range",
                "min": 1,
                "max": 9,
                "step": 1,
            },
            "cpu_request": {
                "order": 11,
                "type": "range",
                "min": 0.1,
                "max": 16,
                "step": 0.1,
            },
            "cpu_limit": {
                "order": 12,
                "type": "range",
                "min": 0.1,
                "max": 16,
                "step": 0.1,
            },
            "mem_request": {
                "order": 13,
                "type": "range",
                "min": 0.5,
                "max": 64,
                "step": 0.5,
                "label": "Memory Request (Gi)",
            },
            "mem_limit": {
                "order": 14,
                "type": "range",
                "min": 0.5,
                "max": 64,
                "step": 0.5,
                "label": "Memory Limit (Gi)",
            },
            "additional_properties": {
                "order": 100,
                "label": "Additional Properties",
                "type": "key-value",
            },
        }

    async def template_vars(self, model: KafkaPlatform) -> dict:
        """Resolves template variables required for rendering manifests."""
        vars = model.model_dump()
        vars["image"], vars["image_tag"] = await self.resolve_image(
            model,
            "kafka",
            "quay.io/strimzi/kafka",
            "0.41.0-kafka-3.7.0",
        )
        chart_repo, chart_name, chart_version = await self.resolve_chart(
            model,
            "kafka",
            "main",
            "https://github.com/kagesenshi/mindweaver.git",
            "charts/kafka",
            "main",
        )
        vars["chart_repo"] = chart_repo
        vars["chart_name"] = chart_name
        vars["chart_version"] = chart_version
        vars["override_image"] = True
        vars["namespace"] = await self._resolve_namespace(model)
        project = await self.project(model)
        vars["ingress_domain"] = project.ingress_domain
        return vars


router = KafkaPlatformService.router()

# Register the poller class
from .poller import KafkaPoller
