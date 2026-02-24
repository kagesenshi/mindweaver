# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from abc import ABC, abstractmethod
from typing import Any, Optional
import socket


class DataSourceDriver(ABC):
    """
    Base class for data source drivers.
    Each driver should implement its own connection testing and URI construction logic.
    """

    def __init__(self, config: dict[str, Any]):
        self.config = config

    @abstractmethod
    async def test_connection(self) -> dict[str, Any]:
        """
        Perform a connection test for the data source.
        Returns a dictionary with 'status' and 'message'.
        """
        pass

    @abstractmethod
    def connection_uri(self) -> str:
        """
        Construct and return the connection URI for the data source.
        """
        pass

    def _tcp_check(self, host: str, port: int, timeout: float = 3.0) -> bool:
        """
        Perform a simple TCP connection check.
        """
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (socket.timeout, socket.error):
            return False

    async def default_test_connection(self) -> dict[str, Any]:
        """
        Default implementation of test_connection using a simple TCP check.
        Requires 'host' and 'port' to be present in the config.
        """
        host = self.config.get("host")
        port = self.config.get("port")

        if not host:
            return {"status": "error", "message": "Host is required for TCP check"}

        if not port:
            return {"status": "error", "message": "Port is required for TCP check"}

        if self._tcp_check(host, int(port)):
            return {
                "status": "success",
                "message": f"TCP connection to {host}:{port} successful",
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to connect to {host}:{port} (TCP check)",
            }
