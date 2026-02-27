# SPDX-FileCopyrightText: Copyright © 2025 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from mindweaver.service import NamedBase
from mindweaver.service.base import ProjectScopedNamedBase, ProjectScopedService
from sqlalchemy import String, Text, Boolean
from sqlalchemy_utils import JSONType
from sqlmodel import Field
from typing import Any, Optional
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from mindweaver.ext.data_source import get_driver_options, get_driver


from .model import DataSource


class DataSourceService(ProjectScopedService[DataSource]):
    @classmethod
    def model_class(cls) -> type[DataSource]:
        return DataSource

    @classmethod
    def widgets(cls) -> dict[str, Any]:
        return {
            "driver": {"type": "select", "options": get_driver_options()},
            "password": {"type": "password"},
            "parameters": {"type": "key-value"},
        }

    @classmethod
    def redacted_fields(cls) -> list[str]:
        return ["password"]

    async def update(self, model_id: int, data: NamedBase) -> DataSource:
        return await super().update(model_id, data)

    async def perform_test_connection(self, config: dict[str, Any]) -> dict[str, Any]:
        """
        Perform the actual connection test logic.
        """
        driver_name = config["driver"].lower() if config["driver"] else ""
        password_to_use = config.get("password")

        try:
            driver = get_driver(driver_name, config)
            if driver:
                # Run connection test via registered driver
                result = await driver.test_connection()
                if result.get("status") == "error":
                    raise ValueError(result.get("message", "Connection test failed"))
                return result

            if driver_name in [
                "postgresql",
                "mysql",
                "mariadb",
                "trino",
                "mongodb",
                "mssql",
                "oracle",
            ]:
                # Database checks using SQLAlchemy
                db_driver_map = {
                    "postgresql": "postgresql+psycopg",
                    "mysql": "mysql+pymysql",
                    "mariadb": "mysql+pymysql",
                    "mssql": "mssql+pyodbc",
                    "oracle": "oracle+cx_oracle",
                    "trino": "trino",
                    "mongodb": "mongodb",
                }

                sa_driver = db_driver_map.get(driver_name, driver_name)

                url_kwargs = {
                    "username": config.get("login"),
                    "password": password_to_use,
                    "host": config.get("host"),
                    "port": config.get("port"),
                    "database": config.get("resource"),
                }

                url_kwargs = {k: v for k, v in url_kwargs.items() if v is not None}
                url = URL.create(drivername=sa_driver, **url_kwargs)

                if config.get("parameters"):
                    url = url.update_query_dict(config["parameters"])

                try:
                    engine = create_engine(url)
                    with engine.connect() as conn:
                        conn.execute(text("SELECT 1"))

                    return {
                        "status": "success",
                        "message": f"Successfully connected to {driver_name}",
                    }
                except Exception as e:
                    raise ValueError(f"Connection failed: {str(e)}")

            else:
                return {
                    "status": "unknown",
                    "message": f"Driver '{driver_name}' connection test not fully implemented, but saved.",
                }

        except Exception as e:
            # Re-raise as HTTPException with 422 to match test expectations
            raise HTTPException(
                status_code=422, detail=f"Connection test failed: {str(e)}"
            )
