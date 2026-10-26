---
name: MindWeaver Dependency Tracker
description: How to define and track service dependencies in MindWeaver platform services and modules.
---
# MindWeaver Dependency Tracker

The `dependency_tracker` tracks dependency chains between services (e.g., Hive Metastore depending on PostgreSQL, Trino depending on Hive Metastore) to prevent upstream dependencies from being decommissioned while dependent services are still active.

---

## 1. How Dependency Tracking Works

When a `PlatformService` is deployed (`deploy()`), the dependency tracker automatically inspects the service's widgets to identify all relationship widgets. For each relationship:
- An entry is inserted into `mw_dependency_tracker` containing:
  - `service_uuid`, `service_name`, `service_type`: The consumer service.
  - `dependency_uuid`, `dependency_name`, `dependency_type`: The provider service.
  - `relationship`: The field name of the relationship (e.g., `database_id`, `hms_ids`).
- If the relationship is multi-select, **one entry is created for each selected dependency**.
- When the consumer service is decommissioned, its dependency entries are automatically removed from `mw_dependency_tracker`.
- When an upstream service attempts to decommission, it queries `dependency_tracker.get_active_dependents()`. If any active services depend on it, decommissioning is blocked with a `ModelValidationError`.

> [!IMPORTANT]
> `force=True` on decommission bypasses Kubernetes communication errors, but **MUST NOT** bypass active service dependencies. Upstream dependencies can only be decommissioned once all consumer services are decommissioned or set to `active=False`.

---

## 2. Defining Dependencies in Future Modules

Future services define their dependencies via model fields and service widgets. The dependency tracker automatically discovers them without any custom hook code.

### Option A: Foreign Key on Model (Single-Select)

If the dependency is a direct single foreign key:

```python
# model.py
from sqlmodel import Field
from mindweaver.platform_service.base import PlatformBase

class MyPlatform(PlatformBase, table=True):
    __tablename__ = "mw_my_platform"

    # Define foreign key to target platform table
    database_id: int = Field(foreign_key="mw_pgsql_platform.id")
```

`FormHandlerMixin.get_widgets()` automatically infers:
- `type: "relationship"`
- `endpoint: "/api/v1/platform/pgsql"`
- `field: "id"`

You can optionally override label and ordering in `service.py`:
```python
# service.py
@classmethod
def widgets(cls) -> dict[str, Any]:
    return {
        "database_id": {
            "order": 20,
            "label": "PostgreSQL Database",
        }
    }
```

---

### Option B: Explicit Widget Definition (Single or Multi-Select)

For relationships without explicit foreign keys (or when multi-select is required):

```python
# model.py
from typing import Optional
from sqlmodel import Field
from sqlalchemy_utils import JSONType
from mindweaver.platform_service.base import PlatformBase

class MyPlatform(PlatformBase, table=True):
    __tablename__ = "mw_my_platform"

    # Single-select target ID
    platform_pgsql_id: Optional[int] = Field(default=None)

    # Multi-select list of IDs (stored as JSON)
    hms_ids: list[int] = Field(default_factory=list, sa_type=JSONType())
```

In `service.py`, define them in `widgets()`:

```python
# service.py
@classmethod
def widgets(cls) -> dict[str, Any]:
    return {
        # Single-select relationship
        "platform_pgsql_id": {
            "order": 10,
            "label": "PostgreSQL Metadata DB",
            "type": "relationship",
            "endpoint": "/api/v1/platform/pgsql",
            "field": "id",
        },
        # Multi-select relationship
        "hms_ids": {
            "order": 20,
            "label": "Hive Metastores",
            "type": "relationship",
            "endpoint": "/api/v1/platform/hive-metastore",
            "field": "id",
            "multiselect": True,
        },
    }
```

---

## 3. Configuration Conventions & Rules

1. **Widget Type**: The widget dictionary **must** have `"type": "relationship"`.
2. **Endpoint**: The widget dictionary **must** specify the API endpoint of the target service (e.g., `"/api/v1/platform/pgsql"`, `"/api/v1/s3_storages"`).
3. **Lookup Field**: The `field` key defines which column on the target model matches the stored value (defaults to `"id"`).
4. **Multi-Select**: Set `"multiselect": True` (or store value as `list`/`set`/`tuple`). One row in `mw_dependency_tracker` will be created for every item in the list.
5. **Automatically Excluded Fields**: `project_id`, `id`, and `uuid` are container and tenancy fields; they are ignored during dependency tracking.
6. **Service Type Convention**:
   - `service_type` is automatically derived from `cls.service_path()`.
   - Examples:
     - `/platform/pgsql` -> `pgsql`
     - `/platform/hive-metastore` -> `hive_metastore`
     - `/platform/trino` -> `trino`
     - `/s3_storages` -> `s3_storage`
   - To override, define:
     ```python
     @classmethod
     def service_type(cls) -> str:
         return "custom_type"
     ```

---

## 4. Testing Dependencies for New Modules

When adding a new module with dependencies, always write unit tests verifying:

1. **Tracking on Deploy**: Deploying the new service creates entries in `/api/v1/dependency-tracker`.
2. **Block Decommissioning**: Attempting to decommission upstream dependencies fails with `422 Unprocessable Entity` (`ModelValidationError`).
3. **Unblock after Decommissioning**: Decommissioning the new service clears its entries from `dependency_tracker`, allowing upstream dependencies to decommission cleanly.

### Example Test Pattern

```python
def test_my_service_dependency_lifecycle(client: TestClient, test_project):
    # 1. Deploy upstream dependency
    pg_resp = client.post("/api/v1/platform/pgsql", json=pg_data, headers=headers)
    pg_id = pg_resp.json()["data"]["id"]
    client.post(f"/api/v1/platform/pgsql/{pg_id}/_deploy", headers=headers)

    # 2. Deploy consumer service
    my_resp = client.post(
        "/api/v1/platform/my-service",
        json={"name": "my-svc", "database_id": pg_id, "project_id": test_project["id"]},
        headers=headers,
    )
    my_id = my_resp.json()["data"]["id"]
    client.post(f"/api/v1/platform/my-service/{my_id}/_deploy", headers=headers)

    # 3. Upstream decommission must fail
    fail_decom = client.post(
        f"/api/v1/platform/pgsql/{pg_id}/_decommission",
        headers={**headers, "X-RESOURCE-NAME": "pg-test"},
    )
    assert fail_decom.status_code == 422
    assert "my-svc" in fail_decom.text

    # 4. Decommission consumer first
    client.post(
        f"/api/v1/platform/my-service/{my_id}/_decommission",
        headers={**headers, "X-RESOURCE-NAME": "my-svc"},
    )

    # 5. Upstream decommission now succeeds
    ok_decom = client.post(
        f"/api/v1/platform/pgsql/{pg_id}/_decommission",
        headers={**headers, "X-RESOURCE-NAME": "pg-test"},
    )
    assert ok_decom.status_code == 200
```
