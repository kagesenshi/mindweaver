---
name: MindWeaver Backend Permissions
description: Defining service permissions, class-based inheritance, and endpoint protection in MindWeaver.
---
# MindWeaver Backend Permissions

This skill covers how to define, structure, and enforce permissions for services and platform services in MindWeaver.

## 1. Permission Architecture Overview

MindWeaver uses a class-based permission system with multiple inheritance defined in `mindweaver.fw.permission`.

### Framework Base Hierarchy
- **`All`**: The root permission class. Superadmins are granted `All`.
  - Subclasses defining `name = "..."` are automatically registered into `_NAME_TO_PERMISSION` for string lookup.
- **`Permission(All)`**: Base class for specific permissions.
- **Read Permissions**:
  - `Read(Permission)`: Base read permission. Default regular authenticated users are granted `Read`.
  - `List(Read)`: Permission to list resources.
  - `View(Read)`: Permission to view single resources or details.
- **Write Permissions**:
  - `Write(Permission)`: Base mutating permission.
  - `Create(Write)`: Permission to create resources.
  - `Update(Write)`: Permission to update resources.
  - `Delete(Write)`: Permission to delete resources.
- **Execute Permissions**:
  - `Execute(Permission)`: Permission to run actions, deploy/decommission platform services, or custom operational tasks.

### Inheritance Principle
Access is granted if the required permission is a subclass of any permission granted to the user:
```python
issubclass(required_permission, granted_permission)
```
Because of multiple inheritance:
- Granting `Read` allows access to `List` and `View` across all services.
- Granting `<Service>Permission` allows all operations for that service.
- Granting `<Service>Read` allows only reading that service.
- Granting `<Service><Action>` allows only that specific action.

---

## 2. Creating `permission.py` for a Service

Each service and platform service must define its permissions in `permission.py` inside its service package (e.g. `mindweaver/service/<service_name>/permission.py` or `mindweaver/platform_service/<service_name>/permission.py`).

### Standard Service Template

```python
# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from mindweaver.fw.permission import (
    Permission,
    Read as FwRead,
    Write as FwWrite,
    List as FwList,
    View as FwView,
    Create as FwCreate,
    Update as FwUpdate,
    Delete as FwDelete,
    Execute as FwExecute,
)


class ManageMyService(Permission):
    """Base permission for all operations on MyService resources."""
    name: str = "myservice:manage"


class ViewMyService(ManageMyService):
    """Permission to perform view-only operations on myservice."""
    name: str = "myservice:view_myservice"


class Read(ViewMyService, FwRead):
    """Permission to perform read-only operations on myservice."""
    name: str = "myservice:read"


class List(Read, FwList):
    """Permission to list myservice resources."""
    name: str = "myservice:list"


class View(Read, FwView):
    """Permission to view a specific myservice resource."""
    name: str = "myservice:view"


class Write(ManageMyService, FwWrite):
    """Permission to perform mutating operations on myservice."""
    name: str = "myservice:write"


class Create(Write, FwCreate):
    """Permission to create a new myservice resource."""
    name: str = "myservice:create"


class Update(Write, FwUpdate):
    """Permission to update an existing myservice resource."""
    name: str = "myservice:update"


class Delete(Write, FwDelete):
    """Permission to delete an existing myservice resource."""
    name: str = "myservice:delete"


class Execute(ManageMyService, FwExecute):
    """Permission to execute myservice actions and platform tasks."""
    name: str = "myservice:execute"


# Custom views or platform operational permissions
class Refresh(View):
    """Permission to refresh myservice status."""
    name: str = "myservice:refresh"


# Canonical Aliases
ManageMyServicePermission = ManageMyService
ViewMyServicePermission = ViewMyService
MyService = ManageMyService
MyServicePermission = ManageMyService
MyServiceRead = Read
MyServiceList = List
MyServiceView = View
MyServiceWrite = Write
MyServiceCreate = Create
MyServiceUpdate = Update
MyServiceDelete = Delete
MyServiceExecute = Execute
MyServiceRefresh = Refresh
```

---

## 3. Wiring Permissions into Service & Views

### Step 1: Assign Permissions to Service
In `service.py`, import the service's `permission` module and set `permissions = permission`:

```python
from . import permission

class MyServiceService(Service[MyService]):
    permissions = permission
    # ...
```

`ServiceViewMixin.get_permission(action)` will automatically wire standard CRUD endpoints (`list`, `create`, `get`, `update`, `delete`) to the service's corresponding permission classes (`List`, `Create`, `View`, `Update`, `Delete`).

### Step 2: Wire Custom Views in `views.py`
Use `require(...)` from `mindweaver.fw.permission` to guard custom service or model views:

```python
from mindweaver.fw.permission import require
from .permission import Refresh, Deploy, Decommission

@MyServiceService.model_view("POST", "/_refresh", dependencies=[require(Refresh)])
async def refresh_view(id: int, svc: MyServiceService = Depends(MyServiceService.get_service)):
    # ...
    return {"status": "success"}
```

> [!NOTE]
> If a custom view does not specify `dependencies`, `ServiceViewMixin` will default to `require(cls.get_permission("execute"))` for `POST`, `PUT`, `PATCH`, `DELETE` methods, and `require(cls.get_permission("view"))` for read methods. However, explicitly specifying the action permission is strongly recommended.

---

## 4. Programmatic Permission Checking

In custom code or Celery tasks, you can check permissions directly:

```python
from mindweaver.fw.permission import check_user_permission, has_permission
from mindweaver.service.project.permission import Refresh

# 1. Sync check using user object:
if not check_user_permission(user, Refresh):
    raise PermissionError("User lacks refresh permission")

# 2. Async check from Request:
if not await has_permission(request, Refresh):
    raise HTTPException(status_code=403, detail="Forbidden")
```

---

## 5. Testing Service Permissions

Always write unit tests for service permissions following TDD principles in `backend/tests/service/<service_name>/test_<service_name>_permissions.py`:

1. **Hierarchy Verification**: Verify that `List`, `Create`, `Refresh`, etc., inherit from both the service root class and framework base classes.
2. **Auto-registration**: Verify that string names (e.g. `"myservice:refresh"`) are registered in `_NAME_TO_PERMISSION`.
3. **Permission Evaluation**: Test with mock users possessing different permissions (`All`, `MyService`, `Read`, `Refresh`).
4. **Endpoint Enforcement**: Test via `TestClient` that regular users without permission receive `403 Forbidden`, while users with permission receive `200 OK`.
