# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from typing import Any
import httpx
from fastapi import HTTPException
from mindweaver.service.base import ProjectScopedService
from ..base import DataSourceServiceBase
from .model import APISource


class APISourceService(DataSourceServiceBase, ProjectScopedService[APISource]):
    @classmethod
    def model_class(cls) -> type[APISource]:
        return APISource

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
            "base_url": {"order": 20, "label": "Base URL"},
            "api_type": {
                "type": "select",
                "order": 21,
                "label": "API Type",
                "options": [
                    {"label": "REST", "value": "rest"},
                    {"label": "GraphQL", "value": "graphql"},
                    {"label": "SOAP", "value": "soap"},
                ],
            },
            "auth_type": {
                "type": "select",
                "order": 22,
                "label": "Auth Type",
                "options": [
                    {"label": "None", "value": "none"},
                    {"label": "Basic Auth", "value": "basic"},
                    {"label": "Bearer Token", "value": "bearer"},
                    {"label": "API Key", "value": "api_key"},
                ],
            },
            "headers": {"order": 101, "type": "key-value"},
        })
        return widgets

    async def perform_test_connection(self, config: dict[str, Any]) -> dict[str, Any]:
        url = config.get("base_url")
        if not url:
            raise HTTPException(status_code=422, detail="Base URL is required")

        try:
            async with httpx.AsyncClient(
                verify=config.get("verify_ssl", False),
                timeout=10.0,
            ) as client:
                headers = {}
                auth = None
                auth_type = config.get("auth_type", "none")
                
                if auth_type == "basic" and config.get("login") and config.get("password"):
                    auth = (config["login"], config["password"])
                elif auth_type == "bearer" and config.get("password"):
                    headers["Authorization"] = f"Bearer {config['password']}"
                elif auth_type == "api_key" and config.get("password"):
                    header_name = config.get("parameters", {}).get("api_key_header", "X-API-Key")
                    headers[header_name] = config["password"]

                resp = await client.get(url, auth=auth, headers=headers, follow_redirects=True)
                return {
                    "status": "success",
                    "message": f"Connected to API {url}. Status: {resp.status_code}",
                }
        except Exception as e:
            raise HTTPException(
                status_code=422, detail=f"API connection failed: {str(e)}"
            )
