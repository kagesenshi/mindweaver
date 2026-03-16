# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from typing import Any
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from mindweaver.service.base import ProjectScopedService
from ..base import DataSourceServiceBase
from .model import DatabaseSource


class DatabaseSourceService(DataSourceServiceBase, ProjectScopedService[DatabaseSource]):
    @classmethod
    def model_class(cls) -> type[DatabaseSource]:
        return DatabaseSource

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
            "engine": {
                "type": "select",
                "order": 20,
                "label": "Engine",
                "options": [
                    {"label": "PostgreSQL", "value": "postgresql"},
                    {"label": "MySQL", "value": "mysql"},
                    {"label": "MariaDB", "value": "mariadb"},
                    {"label": "Trino", "value": "trino"},
                    {"label": "Microsoft SQL Server", "value": "mssql"},
                    {"label": "Oracle", "value": "oracle"},
                    {"label": "MongoDB", "value": "mongodb"},
                ],
            },
            "host": {"order": 21},
            "port": {"order": 22},
            "database": {"order": 23, "label": "Database"},
            "schema_name": {"order": 24, "label": "Schema"},
        })
        return widgets

    async def perform_test_connection(self, config: dict[str, Any]) -> dict[str, Any]:
        engine_name = config.get("engine", "").lower()
        if not engine_name:
            raise HTTPException(status_code=422, detail="Engine is required")

        db_driver_map = {
            "postgresql": "postgresql+psycopg",
            "mysql": "mysql+pymysql",
            "mariadb": "mysql+pymysql",
            "mssql": "mssql+pyodbc",
            "oracle": "oracle+cx_oracle",
            "trino": "trino",
            "mongodb": "mongodb",
        }

        sa_driver = db_driver_map.get(engine_name, engine_name)
        url_kwargs = {
            "username": config.get("login"),
            "password": config.get("password"),
            "host": config.get("host"),
            "port": config.get("port"),
            "database": config.get("database"),
        }
        url_kwargs = {k: v for k, v in url_kwargs.items() if v is not None}
        
        try:
            url = URL.create(drivername=sa_driver, **url_kwargs)
            if config.get("parameters"):
                url = url.update_query_dict(config["parameters"])

            engine = create_engine(url)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            return {
                "status": "success",
                "message": f"Successfully connected to {engine_name}",
            }
        except Exception as e:
            raise HTTPException(
                status_code=422, detail=f"Connection failed: {str(e)}"
            )
