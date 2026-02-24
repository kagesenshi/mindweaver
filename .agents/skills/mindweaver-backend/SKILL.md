---
name: MindWeaver Backend Development
description: Guide for creating backend services, platform services, widget configuration, and tests in MindWeaver.
---
# MindWeaver Backend Development

This document outlines core skills for working with the MindWeaver backend.

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

## Custom Actions

Services support registering custom actions (e.g., triggering a backup) using the `@register_action` decorator and inheriting from `BaseAction`.

1.  **Define the Action**: Inherit from `mindweaver.fw.action.BaseAction` and implement the `__call__` method. You can also override the `available` method to control when the action is available.
2.  **Register the Action**: Decorate the action class with `@MyService.register_action("action_name")`.

```python
from mindweaver.fw.action import BaseAction

@MyService.register_action("my_action")
class MyCustomAction(BaseAction):
    async def available(self) -> bool:
        # Check if action should be available for the given model instance
        return True

    async def __call__(self, **kwargs):
        # Implement the action logic
        # self.model contains the current model instance
        # self.svc contains the service instance
        return {"status": "success", "message": f"Action executed for {self.model.name}"}
```

## Custom Views (Endpoints)

You can easily register additional endpoints at the service level or the model level using decorators on your service class.

-   **`@service_view(method, path, **kwargs)`**: Registers a custom endpoint at the service level (e.g., `/api/v1/my_models/my-custom-path`).
-   **`@model_view(method, path, **kwargs)`**: Registers a custom endpoint at the model level, where the path automatically includes the model's ID (e.g., `/api/v1/my_models/{id}/my-custom-path`).

```python
class MyService(Service[MyModel]):
    @classmethod
    def model_class(cls):
        return MyModel

@MyService.service_view("POST", "/bulk-update", description="Bulk update operation")
async def bulk_update_endpoint():
    # Accessible via POST /api/v1/my_models/bulk-update
    return {"status": "bulk updating"}

@MyService.model_view("GET", "/status")
async def get_model_status():
    # Accessible via GET /api/v1/my_models/{id}/status
    return {"status": "running"}
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

## Hooks Mechanism

Services support lifecycle hooks for custom logic during CRUD operations. Decorate methods with:

-   `@before_create` / `@after_create`
-   `@before_update` / `@after_update`
-   `@before_delete` / `@after_delete`

Hooks accept arguments depending on the event (e.g., `(self, model)` or `(self, model, data)`).

```python
from mindweaver.fw.service import before_create

class MyService(Service[MyModel]):
    @before_create
    async def validate_custom_logic(self, model: MyModel):
        if model.some_field == "invalid":
            raise ValueError("Invalid value")
```

Hooks are topologically sorted if dependencies (`before=` or `after=` arguments) are specified, allowing complex execution orders.

## Secret Handling

To handle sensitive fields (like passwords or API keys) securely:

1.  Inherit from `SecretHandlerMixin` in your Service.
2.  Override `redacted_fields` to list sensitive field names.

```python
from mindweaver.fw.service import Service, SecretHandlerMixin

class MyService(SecretHandlerMixin, Service[MyModel]):
    @classmethod
    def redacted_fields(cls) -> list[str]:
        return ["password", "api_key"]
```

-   **Encryption**: Fields are automatically encrypted before being stored in the database.
-   **Redaction**: Fields are returned as `__REDACTED__` in API responses.
-   **Updates**: Clients can send `__REDACTED__` (to keep existing value), `__CLEAR__` (to empty it), or a new value (which will be encrypted).

## Project Scoping and Multi-tenancy

The framework supports multi-tenancy via the `X-Project-ID` header.

1.  **Models**: Use `ProjectScopedNamedBase`.
2.  **Services**: The base `Service` automatically:
    -   Filters `get`, `all`, and `search` queries by the project ID found in the header.
    -   Injects `project_id` on creation.
    -   Validates that relationship fields (foreign keys) point to records within the *same* project.

## Field Configuration

You can control field behavior and visibility by overriding Service class methods:

-   **`internal_fields()`**: Fields excluded from create/update payloads (e.g., `id`, `uuid`, `created`, `modified`).
-   **`immutable_fields()`**: Fields that cannot be changed after creation (default: `["name"]`).
-   **`hidden_fields()`**: Fields completely hidden from the API (default: `["uuid"]`).
-   **`noninheritable_fields()`**: Fields not copied during updates (default: `["uuid", "modified", "deleted"]`).

## Error Handling

The framework provides standardized error handling:

-   **`ModelValidationError`**: Raise this for business logic validation failures. It maps to a 422 Unprocessable Entity response.
-   **Integrity Errors**: Database constraints (Unique, Not Null, Foreign Key) are automatically caught and translated into user-friendly `ModelValidationError` messages.

```python
from mindweaver.fw.exc import ModelValidationError

# In a service method or hook
if some_condition:
    raise ModelValidationError(message="Custom validation failed")
```

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
