# Backend Development

This guide provides details on how to extend the Mindweaver backend.

## The `fw` Layer

The framework layer (`backend/src/mindweaver/fw/`) provides the standard infrastructure for all services.

### Models (`model.py`)

All database-backed models should use `SQLModel` and inherit from one of the base classes:
- **`NamedBase`**: For resources with a name and ID (ID is the primary key).
- **`ProjectScopedNamedBase`**: For resources that must be associated with a specific project.

### Services (`service.py`)

A `Service` class automatically handles standard CRUD logic. To create a new service:
1.  Inherit from `Service`.
2.  Define the `model` attribute.
3.  Register with the FastAPI app using the provided decorators.

```python
from mindweaver.fw.service import Service, service_view

class MyNewService(Service):
    model = MyNewModel
```

### Hooks

You can inject custom logic into the CRUD lifecycle using hooks:
- `@before_create`
- `@after_create`
- `@before_update`
- `@after_update`
- `@before_delete`
- `@after_delete`

## Platform Services

Platform services manage external components. They inherit from `PlatformService` and typically implement actions like `_deploy` and `_decommission`.

### Manifest Templating

Manifests are stored in `backend/src/mindweaver/templates/` as `.yml.j2` files. Use standard Jinja2 syntax to render these templates within your platform service.

## Sensitive Data Handling

Use `SecretHandlerMixin` to manage sensitive fields.
- Register sensitive fields in `redacted_fields()`.
- The `fw` layer will automatically encrypt these fields on write and redact them on read.

## Database Migrations

Mindweaver uses Alembic for migrations.
- **Generate**: `uv run mindweaver db revision -m "message" --autogenerate`
- **Apply**: `uv run mindweaver db migrate`
