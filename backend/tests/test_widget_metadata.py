from fastapi.testclient import TestClient
from mindweaver.service.knowledge_db import KnowledgeDBService
import pytest


@pytest.mark.asyncio
async def test_widget_metadata_generation(client: TestClient):
    response = client.get("/api/v1/knowledge_dbs/_create-form")
    assert response.status_code == 200
    data = response.json()
    widgets = data["record"]["widgets"]

    # Preferred Defaults
    # project_id (order 0, span 1)
    assert widgets["project_id"]["order"] == 0
    assert widgets["project_id"]["column_span"] == 1

    # name (order 1, span 1)
    assert widgets["name"]["order"] == 1
    assert widgets["name"]["column_span"] == 1

    # title (order 2, span 2)
    assert widgets["title"]["order"] == 2
    assert widgets["title"]["column_span"] == 2

    # description (order 3, span 2)
    assert widgets["description"]["order"] == 3
    assert widgets["description"]["column_span"] == 2

    # Other fields
    # type (explicitly in widgets overriding inferred select)
    assert widgets["type"]["type"] == "select"
    assert widgets["type"]["order"] >= 100
    assert widgets["type"]["column_span"] == 2
