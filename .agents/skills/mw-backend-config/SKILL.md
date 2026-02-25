---
name: MindWeaver Backend Configuration
description: Configuring UI widgets, field settings, and handling secrets in MindWeaver.
---
# MindWeaver Backend Configuration

This skill covers how to control field behavior and presentation.

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

## Field Configuration

You can control field behavior and visibility by overriding Service class methods:

-   **`internal_fields()`**: Fields excluded from create/update payloads (e.g., `id`, `uuid`, `created`, `modified`).
-   **`immutable_fields()`**: Fields that cannot be changed after creation (default: `["name"]`).
-   **`hidden_fields()`**: Fields completely hidden from the API (default: `["uuid"]`).
-   **`noninheritable_fields()`**: Fields not copied during updates (default: `["uuid", "modified", "deleted"]`).

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
