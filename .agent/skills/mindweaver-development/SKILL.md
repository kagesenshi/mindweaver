---
name: MindWeaver Development
description: Guide for creating backend services, platform services, dynamic forms, widgets, and tests in MindWeaver.
---
# MindWeaver Development

This document outlines core skills for working with the MindWeaver codebase.

## Creating a New Backend Service

To create a new backend service that provides standard CRUD operations:

1.  **Define the Model**: Create a SQLModel class inheriting from `NamedBase` (or `ProjectScopedNamedBase` if it belongs to a project).
    ```python
    from mindweaver.fw.model import NamedBase
    from sqlmodel import Field

    class MyModel(NamedBase, table=True):
        __tablename__ = "my_model"
        some_field: str = Field(default="default")
    ```

2.  **Define the Service**: Create a Service class inheriting from `Service` (or `ProjectScopedService`).
    ```python
    from mindweaver.fw.service import Service

    class MyModelService(Service[MyModel]):
        @classmethod
        def model_class(cls):
            return MyModel
    ```

3.  **Register the Router**: Add the service router to `backend/src/mindweaver/app.py`.
    ```python
    from .service.my_service import MyModelService
    # ...
    app.include_router(MyModelService.router(), prefix="/api/v1")
    ```

This automatically provides endpoints for `GET`, `POST`, `PUT`, `DELETE`, and list operations, along with dynamic form schemas.

## Creating a New Backend Platform Service

Platform services manage external resources (like Kubernetes deployments).

1.  **Define the Platform Model**: Inherit from `PlatformBase`.
    ```python
    from mindweaver.platform_service.base import PlatformBase

    class MyPlatform(PlatformBase, table=True):
        __tablename__ = "my_platform"
        # ... fields
    ```

2.  **Define the State Model**: Inherit from `PlatformStateBase`.
    ```python
    from mindweaver.platform_service.base import PlatformStateBase

    class MyPlatformState(PlatformStateBase, table=True):
        __tablename__ = "my_platform_state"
        # ... status fields
    ```

3.  **Define the Service**: Inherit from `PlatformService`.
    ```python
    from mindweaver.platform_service.base import PlatformService

    class MyPlatformService(PlatformService[MyPlatform]):
        template_directory: str = "/path/to/templates"
        state_model: type[MyPlatformState] = MyPlatformState

        @classmethod
        def model_class(cls):
            return MyPlatform

        async def poll_status(self, model: MyPlatform):
            # Implement logic to check status and update state
            pass
    ```

4.  **Create Templates**: Add Jinja2/YAML templates for Kubernetes manifests in the `template_directory`.

5.  **Register the Router**: As with standard services, register the router in `app.py`. The `PlatformService` adds `_deploy`, `_decommission`, `_state`, and `_refresh` endpoints.

## Creating a Dynamic Form

The frontend `DynamicForm` component renders forms based on schemas provided by the backend.

1.  **Backend Support**: The `Service` class automatically generates JSON schemas and widget metadata via `_create-form` and `_edit-form` endpoints.
2.  **Frontend Usage**:
    ```jsx
    import DynamicForm from '../components/DynamicForm';

    <DynamicForm
        entityPath="/api/v1/my_models"
        mode="create" // or "edit"
        onSuccess={(data) => console.log('Created:', data)}
    />
    ```

## Using Widgets

Widgets control how fields are rendered in the dynamic form. The backend infers widgets from model fields, but you can override them.

### Automatic Inference
-   **Text**: Default for String fields.
-   **Number**: Default for Integer/Float fields.
-   **Boolean**: Default for Boolean fields.
-   **Select**: Default for Enum fields.
-   **Relationship**: Default for Foreign Keys (e.g., fields ending in `_id`).
-   **Textarea**: Default for fields named `description`, `config`, `prompt`, `sql`.

### Manual Configuration
Override the `widgets()` class method in your Service to customize widgets.

```python
@classmethod
def widgets(cls) -> Dict[str, Any]:
    return {
        "my_field": {"type": "range", "min": 0, "max": 10},
        "other_field": {"order": 1, "column_span": 2}
    }
```

### Available Widgets

| Widget Type | Description | Configuration Options |
| :--- | :--- | :--- |
| `text` | Single line text input | `label`, `default_value` |
| `textarea` | Multi-line text area | `label`, `rows` (implicit) |
| `number` / `integer` | Numeric input | `label`, `step` |
| `boolean` | Toggle switch | `label` |
| `select` | Dropdown menu | `options` (list of strings or `[{label, value}]`) |
| `relationship` | Select from related records | `endpoint` (API URL), `multiselect` (bool), `field` (display field) |
| `range` | Slider control | `min`, `max`, `step` |
| `password` | Password input | |
| `key-value` | Dynamic list of key-value pairs | |

**Common Metadata:**
-   `order`: Integer to control field order (lower is first).
-   `column_span`: `1` (half width) or `2` (full width).
-   `label`: Custom label text.

## Creating Unit Tests in Backend

Tests are located in `backend/tests` and use `pytest`.

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

3.  **Running Tests**:
    ```bash
    uv run --package mindweaver pytest backend/tests
    ```
