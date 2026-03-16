# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from typing import Any
import httpx
from fastapi import HTTPException
from mindweaver.service.base import ProjectScopedService
from ..base import DataSourceServiceBase
from .model import WebSource


class WebSourceService(DataSourceServiceBase, ProjectScopedService[WebSource]):
    @classmethod
    def model_class(cls) -> type[WebSource]:
        return WebSource

    @classmethod
    def service_path(cls) -> str:
        return ""

    @classmethod
    def model_path(cls) -> str:
        return "/{id}"
    @classmethod
    def widgets(cls) -> dict[str, Any]:
        widgets = super().widgets()
        widgets.update({
            "url": {"order": 20, "label": "URL"},
            "allowed_domains": {"order": 21, "label": "Allowed Domains"},
            "user_agent": {"order": 22, "label": "User Agent"},
        })
        return widgets

    async def perform_test_connection(self, config: dict[str, Any]) -> dict[str, Any]:
        url = config.get("url")
        if not url:
            raise HTTPException(status_code=422, detail="URL is required")

        try:
            async with httpx.AsyncClient(
                verify=config.get("verify_ssl", False),
                timeout=10.0,
            ) as client:
                auth = None
                if config.get("login") and config.get("password"):
                    auth = (config["login"], config["password"])

                resp = await client.get(url, auth=auth, follow_redirects=True)
                return {
                    "status": "success",
                    "message": f"Connected to {url}. Status: {resp.status_code}",
                }
        except Exception as e:
            raise HTTPException(
                status_code=422, detail=f"Web connection failed: {str(e)}"
            )
