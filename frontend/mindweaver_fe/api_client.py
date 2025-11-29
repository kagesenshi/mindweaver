"""HTTP client for interacting with the Mindweaver FastAPI backend."""

import httpx
from typing import TypeVar, Generic, Any, Dict, List, Optional
from .config import settings

T = TypeVar("T")


class APIResponse(Generic[T]):
    """Wrapper for API responses."""

    def __init__(self, data: Dict[str, Any]):
        self.status = data.get("status", "success")
        self.detail = data.get("detail")
        self.record = data.get("record")
        self.records = data.get("records")
        self.meta = data.get("meta")


class APIClient:
    """Async HTTP client for Mindweaver API."""

    def __init__(self, base_url: str = None, timeout: int = None):
        self.base_url = base_url or settings.api_base_url
        self.timeout = timeout or settings.api_timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url, timeout=self.timeout
            )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def list_all(
        self, endpoint: str, headers: Dict[str, str] = None
    ) -> List[Dict[str, Any]]:
        """List all records from an endpoint.

        Args:
            endpoint: API endpoint path (e.g., '/ai_agents')
            headers: Optional headers to include in the request

        Returns:
            List of records
        """
        client = await self._get_client()
        response = await client.get(endpoint, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get("records", [])

    async def get(
        self, endpoint: str, record_id: int, headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """Get a single record by ID.

        Args:
            endpoint: API endpoint path (e.g., '/ai_agents')
            record_id: Record ID
            headers: Optional headers to include in the request

        Returns:
            Record data
        """
        client = await self._get_client()
        response = await client.get(f"{endpoint}/{record_id}", headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get("record", {})

    async def create(
        self, endpoint: str, data: Dict[str, Any], headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """Create a new record.

        Args:
            endpoint: API endpoint path (e.g., '/ai_agents')
            data: Record data to create
            headers: Optional headers to include in the request

        Returns:
            Created record
        """
        client = await self._get_client()
        response = await client.post(endpoint, json=data, headers=headers)
        print(response.text)
        response.raise_for_status()
        result = response.json()
        return result.get("record", {})

    async def update(
        self,
        endpoint: str,
        record_id: int,
        data: Dict[str, Any],
        headers: Dict[str, str] = None,
    ) -> Dict[str, Any]:
        """Update an existing record.

        Args:
            endpoint: API endpoint path (e.g., '/ai_agents')
            record_id: Record ID
            data: Updated record data
            headers: Optional headers to include in the request

        Returns:
            Updated record
        """
        client = await self._get_client()
        response = await client.put(
            f"{endpoint}/{record_id}", json=data, headers=headers
        )
        response.raise_for_status()
        result = response.json()
        return result.get("record", {})

    async def delete(
        self, endpoint: str, record_id: int, headers: Dict[str, str] = None
    ) -> bool:
        """Delete a record.

        Args:
            endpoint: API endpoint path (e.g., '/ai_agents')
            record_id: Record ID
            headers: Optional headers to include in the request

        Returns:
            True if successful
        """
        client = await self._get_client()
        response = await client.delete(f"{endpoint}/{record_id}", headers=headers)
        response.raise_for_status()
        result = response.json()
        return result.get("status") == "success"


# Service-specific clients
class AIAgentClient:
    """Client for AI Agent API endpoints."""

    def __init__(self, client: APIClient = None):
        self.client = client or APIClient()
        self.endpoint = "/api/v1/ai_agents"

    async def list_all(self, headers: Dict[str, str] = None) -> List[Dict[str, Any]]:
        return await self.client.list_all(self.endpoint, headers=headers)

    async def get(
        self, agent_id: int, headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        return await self.client.get(self.endpoint, agent_id, headers=headers)

    async def create(
        self, data: Dict[str, Any], headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        return await self.client.create(self.endpoint, data, headers=headers)

    async def update(
        self, agent_id: int, data: Dict[str, Any], headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        return await self.client.update(self.endpoint, agent_id, data, headers=headers)

    async def delete(self, agent_id: int, headers: Dict[str, str] = None) -> bool:
        return await self.client.delete(self.endpoint, agent_id, headers=headers)


class ChatClient:
    """Client for Chat API endpoints."""

    def __init__(self, client: APIClient = None):
        self.client = client or APIClient()
        self.endpoint = "/api/v1/chats"

    async def list_all(self, headers: Dict[str, str] = None) -> List[Dict[str, Any]]:
        return await self.client.list_all(self.endpoint, headers=headers)

    async def get(self, chat_id: int, headers: Dict[str, str] = None) -> Dict[str, Any]:
        return await self.client.get(self.endpoint, chat_id, headers=headers)

    async def create(
        self, data: Dict[str, Any], headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        return await self.client.create(self.endpoint, data, headers=headers)

    async def update(
        self, chat_id: int, data: Dict[str, Any], headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        return await self.client.update(self.endpoint, chat_id, data, headers=headers)

    async def delete(self, chat_id: int, headers: Dict[str, str] = None) -> bool:
        return await self.client.delete(self.endpoint, chat_id, headers=headers)


class KnowledgeDBClient:
    """Client for Knowledge DB API endpoints."""

    def __init__(self, client: APIClient = None):
        self.client = client or APIClient()
        self.endpoint = "/api/v1/knowledge_dbs"

    async def list_all(self, headers: Dict[str, str] = None) -> List[Dict[str, Any]]:
        return await self.client.list_all(self.endpoint, headers=headers)

    async def get(self, db_id: int, headers: Dict[str, str] = None) -> Dict[str, Any]:
        return await self.client.get(self.endpoint, db_id, headers=headers)

    async def create(
        self, data: Dict[str, Any], headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        return await self.client.create(self.endpoint, data, headers=headers)

    async def update(
        self, db_id: int, data: Dict[str, Any], headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        return await self.client.update(self.endpoint, db_id, data, headers=headers)

    async def delete(self, db_id: int, headers: Dict[str, str] = None) -> bool:
        return await self.client.delete(self.endpoint, db_id, headers=headers)


class DataSourceClient:
    """Client for Data Source API endpoints."""

    def __init__(self, client: APIClient = None):
        self.client = client or APIClient()
        self.endpoint = "/api/v1/data_sources"

    async def list_all(self, headers: Dict[str, str] = None) -> List[Dict[str, Any]]:
        return await self.client.list_all(self.endpoint, headers=headers)

    async def get(
        self, source_id: int, headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        return await self.client.get(self.endpoint, source_id, headers=headers)

    async def create(
        self, data: Dict[str, Any], headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        return await self.client.create(self.endpoint, data, headers=headers)

    async def update(
        self, source_id: int, data: Dict[str, Any], headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        return await self.client.update(self.endpoint, source_id, data, headers=headers)

    async def delete(self, source_id: int, headers: Dict[str, str] = None) -> bool:
        return await self.client.delete(self.endpoint, source_id, headers=headers)

    async def test_connection(
        self, data: Dict[str, Any], headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """Test connection to a data source.

        Args:
            data: Data source configuration to test
            headers: Optional headers

        Returns:
            Test result
        """
        client = await self.client._get_client()
        response = await client.post(
            f"{self.endpoint}/test_connection", json=data, headers=headers
        )
        # We don't raise for status here immediately because we want to handle errors gracefully in the UI
        # But the backend raises 400 for connection failures, so we might want to catch that.
        # Actually, let's raise so the caller catches it, or return the error response.
        # The current pattern in this file uses raise_for_status.
        if response.status_code >= 400:
            # Return the error detail if possible
            try:
                return {
                    "status": "error",
                    "message": response.json().get("detail", "Unknown error"),
                }
            except:
                response.raise_for_status()

        return response.json()


class LakehouseStorageClient:
    """Client for Lakehouse Storage API endpoints."""

    def __init__(self, client: APIClient = None):
        self.client = client or APIClient()
        self.endpoint = "/api/v1/lakehouse_storages"

    async def list_all(self, headers: Dict[str, str] = None) -> List[Dict[str, Any]]:
        return await self.client.list_all(self.endpoint, headers=headers)

    async def get(
        self, storage_id: int, headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        return await self.client.get(self.endpoint, storage_id, headers=headers)

    async def create(
        self, data: Dict[str, Any], headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        return await self.client.create(self.endpoint, data, headers=headers)

    async def update(
        self, storage_id: int, data: Dict[str, Any], headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        return await self.client.update(
            self.endpoint, storage_id, data, headers=headers
        )

    async def delete(self, storage_id: int, headers: Dict[str, str] = None) -> bool:
        return await self.client.delete(self.endpoint, storage_id, headers=headers)

    async def test_connection(
        self, data: Dict[str, Any], headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """Test connection to lakehouse storage.

        Args:
            data: Storage configuration to test
            headers: Optional headers

        Returns:
            Test result
        """
        client = await self.client._get_client()
        response = await client.post(
            f"{self.endpoint}/test_connection", json=data, headers=headers
        )
        if response.status_code >= 400:
            # Return the error detail if possible
            try:
                return {
                    "status": "error",
                    "message": response.json().get("detail", "Unknown error"),
                }
            except:
                response.raise_for_status()

        return response.json()


class IngestionClient:
    """Client for Ingestion API endpoints."""

    def __init__(self, client: APIClient = None):
        self.client = client or APIClient()
        self.endpoint = "/api/v1/ingestions"

    async def list_all(self, headers: Dict[str, str] = None) -> List[Dict[str, Any]]:
        return await self.client.list_all(self.endpoint, headers=headers)

    async def get(
        self, ingestion_id: int, headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        return await self.client.get(self.endpoint, ingestion_id, headers=headers)

    async def create(
        self, data: Dict[str, Any], headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        return await self.client.create(self.endpoint, data, headers=headers)

    async def update(
        self, ingestion_id: int, data: Dict[str, Any], headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        return await self.client.update(
            self.endpoint, ingestion_id, data, headers=headers
        )

    async def delete(self, ingestion_id: int, headers: Dict[str, str] = None) -> bool:
        return await self.client.delete(self.endpoint, ingestion_id, headers=headers)

    async def execute_ingestion(
        self, ingestion_id: int, headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """Execute an ingestion manually.

        Args:
            ingestion_id: ID of the ingestion to execute
            headers: Optional headers

        Returns:
            Execution result
        """
        client = await self.client._get_client()
        response = await client.post(
            f"{self.endpoint}/{ingestion_id}/execute", headers=headers
        )
        response.raise_for_status()
        return response.json()

    async def list_runs(
        self, ingestion_id: int, headers: Dict[str, str] = None
    ) -> List[Dict[str, Any]]:
        """List execution runs for an ingestion.

        Args:
            ingestion_id: ID of the ingestion
            headers: Optional headers

        Returns:
            List of runs
        """
        client = await self.client._get_client()
        response = await client.get(
            f"{self.endpoint}/{ingestion_id}/runs", headers=headers
        )
        response.raise_for_status()
        data = response.json()
        return data.get("records", [])


class OntologyClient:
    """Client for Ontology API endpoints."""

    def __init__(self, client: APIClient = None):
        self.client = client or APIClient()
        self.endpoint = "/api/v1/ontologies"

    async def list_all(self, headers: Dict[str, str] = None) -> List[Dict[str, Any]]:
        return await self.client.list_all(self.endpoint, headers=headers)

    async def get(
        self, ontology_id: int, headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        return await self.client.get(self.endpoint, ontology_id, headers=headers)

    async def create(
        self, data: Dict[str, Any], headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        return await self.client.create(self.endpoint, data, headers=headers)

    async def update(
        self, ontology_id: int, data: Dict[str, Any], headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        return await self.client.update(
            self.endpoint, ontology_id, data, headers=headers
        )

    async def delete(self, ontology_id: int, headers: Dict[str, str] = None) -> bool:
        return await self.client.delete(self.endpoint, ontology_id, headers=headers)


class ProjectClient:
    """Client for Project API endpoints."""

    def __init__(self, client: APIClient = None):
        self.client = client or APIClient()
        self.endpoint = "/api/v1/projects"

    async def list_all(self, headers: Dict[str, str] = None) -> List[Dict[str, Any]]:
        return await self.client.list_all(self.endpoint, headers=headers)

    async def get(
        self, project_id: int, headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        return await self.client.get(self.endpoint, project_id, headers=headers)

    async def create(
        self, data: Dict[str, Any], headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        return await self.client.create(self.endpoint, data, headers=headers)

    async def update(
        self, project_id: int, data: Dict[str, Any], headers: Dict[str, str] = None
    ) -> Dict[str, Any]:
        return await self.client.update(
            self.endpoint, project_id, data, headers=headers
        )

    async def delete(self, project_id: int, headers: Dict[str, str] = None) -> bool:
        return await self.client.delete(self.endpoint, project_id, headers=headers)


# Global client instance
_api_client = APIClient()

# Service clients
ai_agent_client = AIAgentClient(_api_client)
chat_client = ChatClient(_api_client)
knowledge_db_client = KnowledgeDBClient(_api_client)
data_source_client = DataSourceClient(_api_client)
lakehouse_storage_client = LakehouseStorageClient(_api_client)
ingestion_client = IngestionClient(_api_client)
ontology_client = OntologyClient(_api_client)
project_client = ProjectClient(_api_client)
