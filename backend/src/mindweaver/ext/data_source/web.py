from .base import DataSourceDriver
from . import register_driver
from typing import Any
import httpx
from urllib.parse import urlparse


@register_driver(
    "web",
    title="Web / API",
    description="Generic driver for HTTP/HTTPS web endpoints and APIs.",
)
class WebDriver(DataSourceDriver):
    """
    Driver for Web/API data sources.
    Connects to HTTP or HTTPS depending on config.
    """

    def connection_uri(self) -> str:
        """
        Construct and return the connection URI for the web source.
        """
        params = self.config.get("parameters", {})
        host = (
            self.config.get("host") or params.get("base_url") or params.get("start_url")
        )

        if not host:
            return ""

        # Parse host if it's a full URL
        if "://" in host:
            parsed = urlparse(host)
            scheme = parsed.scheme
            host_only = parsed.netloc
            resource_only = parsed.path
            if parsed.query:
                resource_only += f"?{parsed.query}"
        else:
            scheme = "https" if self.config.get("enable_ssl") else "http"
            host_only = host
            resource_only = self.config.get("resource") or ""

        base_url = f"{scheme}://{host_only}"

        # Add port if specified and not already in host_only
        port = self.config.get("port")
        if port and ":" not in host_only:
            base_url += f":{port}"

        if resource_only:
            if not resource_only.startswith("/"):
                base_url += "/"
            base_url += resource_only

        return base_url

    async def test_connection(self) -> dict[str, Any]:
        """
        Perform a connection test using HTTP GET.
        """
        base_url = self.connection_uri()
        if not base_url:
            return {
                "status": "error",
                "message": "Host/URL is required for Web/API source",
            }

        try:
            async with httpx.AsyncClient(
                verify=self.config.get("verify_ssl", False)
            ) as client:
                auth = None
                login = self.config.get("login")
                password = self.config.get("password")

                if login and password:
                    auth = (login, password)

                # Support api_key in parameters if needed (placeholder for now)
                # params = self.config.get("parameters", {})
                # if params.get("api_key"):
                #     pass

                resp = await client.get(
                    base_url, auth=auth, timeout=10.0, follow_redirects=True
                )

                return {
                    "status": "success",
                    "message": f"Connected to {base_url}. Status: {resp.status_code}",
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Web connection failed: {str(e)}",
            }
