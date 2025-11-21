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
                base_url=self.base_url,
                timeout=self.timeout
            )
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def list_all(self, endpoint: str) -> List[Dict[str, Any]]:
        """List all records from an endpoint.
        
        Args:
            endpoint: API endpoint path (e.g., '/ai_agents')
            
        Returns:
            List of records
        """
        client = await self._get_client()
        response = await client.get(endpoint)
        response.raise_for_status()
        data = response.json()
        return data.get("records", [])
    
    async def get(self, endpoint: str, record_id: int) -> Dict[str, Any]:
        """Get a single record by ID.
        
        Args:
            endpoint: API endpoint path (e.g., '/ai_agents')
            record_id: Record ID
            
        Returns:
            Record data
        """
        client = await self._get_client()
        response = await client.get(f"{endpoint}/{record_id}")
        response.raise_for_status()
        data = response.json()
        return data.get("record", {})
    
    async def create(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record.
        
        Args:
            endpoint: API endpoint path (e.g., '/ai_agents')
            data: Record data to create
            
        Returns:
            Created record
        """
        client = await self._get_client()
        response = await client.post(endpoint, json=data)
        response.raise_for_status()
        result = response.json()
        return result.get("record", {})
    
    async def update(self, endpoint: str, record_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing record.
        
        Args:
            endpoint: API endpoint path (e.g., '/ai_agents')
            record_id: Record ID
            data: Updated record data
            
        Returns:
            Updated record
        """
        client = await self._get_client()
        response = await client.put(f"{endpoint}/{record_id}", json=data)
        response.raise_for_status()
        result = response.json()
        return result.get("record", {})
    
    async def delete(self, endpoint: str, record_id: int) -> bool:
        """Delete a record.
        
        Args:
            endpoint: API endpoint path (e.g., '/ai_agents')
            record_id: Record ID
            
        Returns:
            True if successful
        """
        client = await self._get_client()
        response = await client.delete(f"{endpoint}/{record_id}")
        response.raise_for_status()
        result = response.json()
        return result.get("status") == "success"


# Service-specific clients
class AIAgentClient:
    """Client for AI Agent API endpoints."""
    
    def __init__(self, client: APIClient = None):
        self.client = client or APIClient()
        self.endpoint = "/ai_agents"
    
    async def list_all(self) -> List[Dict[str, Any]]:
        return await self.client.list_all(self.endpoint)
    
    async def get(self, agent_id: int) -> Dict[str, Any]:
        return await self.client.get(self.endpoint, agent_id)
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self.client.create(self.endpoint, data)
    
    async def update(self, agent_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self.client.update(self.endpoint, agent_id, data)
    
    async def delete(self, agent_id: int) -> bool:
        return await self.client.delete(self.endpoint, agent_id)


class ChatClient:
    """Client for Chat API endpoints."""
    
    def __init__(self, client: APIClient = None):
        self.client = client or APIClient()
        self.endpoint = "/chats"
    
    async def list_all(self) -> List[Dict[str, Any]]:
        return await self.client.list_all(self.endpoint)
    
    async def get(self, chat_id: int) -> Dict[str, Any]:
        return await self.client.get(self.endpoint, chat_id)
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self.client.create(self.endpoint, data)
    
    async def update(self, chat_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self.client.update(self.endpoint, chat_id, data)
    
    async def delete(self, chat_id: int) -> bool:
        return await self.client.delete(self.endpoint, chat_id)


class KnowledgeDBClient:
    """Client for Knowledge DB API endpoints."""
    
    def __init__(self, client: APIClient = None):
        self.client = client or APIClient()
        self.endpoint = "/knowledge_dbs"
    
    async def list_all(self) -> List[Dict[str, Any]]:
        return await self.client.list_all(self.endpoint)
    
    async def get(self, db_id: int) -> Dict[str, Any]:
        return await self.client.get(self.endpoint, db_id)
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self.client.create(self.endpoint, data)
    
    async def update(self, db_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self.client.update(self.endpoint, db_id, data)
    
    async def delete(self, db_id: int) -> bool:
        return await self.client.delete(self.endpoint, db_id)


class DataSourceClient:
    """Client for Data Source API endpoints."""
    
    def __init__(self, client: APIClient = None):
        self.client = client or APIClient()
        self.endpoint = "/data_sources"
    
    async def list_all(self) -> List[Dict[str, Any]]:
        return await self.client.list_all(self.endpoint)
    
    async def get(self, source_id: int) -> Dict[str, Any]:
        return await self.client.get(self.endpoint, source_id)
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self.client.create(self.endpoint, data)
    
    async def update(self, source_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self.client.update(self.endpoint, source_id, data)
    
    async def delete(self, source_id: int) -> bool:
        return await self.client.delete(self.endpoint, source_id)


# Global client instance
_api_client = APIClient()

# Service clients
ai_agent_client = AIAgentClient(_api_client)
chat_client = ChatClient(_api_client)
knowledge_db_client = KnowledgeDBClient(_api_client)
data_source_client = DataSourceClient(_api_client)
