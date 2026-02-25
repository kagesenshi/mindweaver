---
name: MindWeaver Backend Testing
description: Guide for creating and running unit tests for the MindWeaver backend.
---
# MindWeaver Backend Testing

Tests are located in `backend/tests` and use `pytest`.

## Test Structure

1.  **Fixtures**: Use fixtures from `conftest.py`.
    -   `client`: Standard TestClient.
    -   `crud_client`: TestClient with database setup for CRUD operations.
    -   `project_scoped_crud_client`: For testing project-scoped services.

2.  **Example Test**:
    ```python
    def test_my_service_crud(crud_client):
        resp = crud_client.post(
            "/api/v1/my_models",
            json={"name": "test", "some_field": "value"}
        )
        assert resp.status_code == 200
        data = resp.json()["record"]
        assert data["name"] == "test"
    ```

## Running Tests

Run all backend tests:
```bash
uv run --package mindweaver pytest backend/tests
```

Run a specific test file:
```bash
uv run --package mindweaver pytest backend/tests/test_my_service.py
```
