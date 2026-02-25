---
name: MindWeaver Backend Advanced
description: Advanced operations, multi-tenancy, background tasks, and error handling.
---
# MindWeaver Backend Advanced

This skill covers operational concerns and advanced framework features.

## Background Tasks (Celery)

Long-running operations should be offloaded to Celery.

1.  **Define Task**: Use the `@app.task` decorator.
    ```python
    from mindweaver.celery_app import app
    from .base import run_async

    @app.task
    def my_background_task(param: str):
        # Background logic here
        # Use run_async if calling async functions
        pass
    ```

2.  **Trigger Task**: Use `.delay()` or `.apply_async()`.
    ```python
    my_background_task.delay("value")
    ```

## Safe Delete Pattern

To prevent accidental deletions, the API requires a confirmation header `X-RESOURCE-NAME` containing the name of the resource being deleted.

- **Backend**: Handled automatically in the base `Service.delete` method (via verification against `model.name`).
- **Frontend**: Must include the header in the delete request.

```javascript
// Frontend example
await apiClient.delete(`/api/v1/resources/${id}`, {
    headers: { 'X-RESOURCE-NAME': resourceName }
});
```

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

## Advanced Validation

Use `is_valid_name` for standard name validation and raise `ModelValidationError` for business logic failures.

```python
from mindweaver.fw.model import is_valid_name
from mindweaver.fw.exc import ModelValidationError

class MyModel(NamedBase, table=True):
    # ...
    def validate_something(self):
        if not some_condition:
            raise ModelValidationError("Condition not met")
```
