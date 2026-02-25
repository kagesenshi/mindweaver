---
name: MindWeaver Backend Extensions
description: Extending backend services with custom actions, views, hooks, and state.
---
# MindWeaver Backend Extensions

The framework provides several ways to extend the default CRUD behavior.

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

-   **`@service_view(method, path, **kwargs)`**: Registers a custom endpoint at the service level (e.g., `/api/v1/my_models/_bulk-update`).
-   **`@model_view(method, path, **kwargs)`**: Registers a custom endpoint at the model level, where the path automatically includes the model's ID (e.g., `/api/v1/my_models/{id}/_status`).

```python
class MyService(Service[MyModel]):
    @classmethod
    def model_class(cls):
        return MyModel

@MyService.service_view("POST", "/_bulk-update", description="Bulk update operation")
async def bulk_update_endpoint():
    # Accessible via POST /api/v1/my_models/_bulk-update
    return {"status": "bulk updating"}

@MyService.model_view("GET", "/_status")
async def get_model_status():
    # Accessible via GET /api/v1/my_models/{id}/_status
    return {"status": "running"}
```

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

Hooks are topologically sorted if dependencies (`before=` or `after=` arguments) are specified.

## State Management (`@with_state`)

Use the `with_state` decorator to register a state class that handles dynamic status reporting (e.g., fetching real-time data from Kubernetes).

1.  **Define State Class**: Inherit from `mindweaver.fw.state.BaseState`.
2.  **Register on Service**: Use the `@Service.with_state()` decorator.

```python
from mindweaver.fw.state import BaseState

@MyService.with_state()
class MyResourceState(BaseState):
    async def get(self) -> dict:
        # self.model, self.svc, self.session are available
        return {"status": "active", "load": 0.5}
```

The state is automatically exposed via the `GET /api/v1/my_models/{id}/_state` endpoint.

## Dependency Injection in Custom Views

Custom views support FastAPI dependency injection.

```python
from mindweaver.fw.model import AsyncSession

@MyService.service_view("GET", "/_stats")
async def get_stats(session: AsyncSession):
    # session is automatically injected
    pass
```
