# 0012. Service-Specific Permission Architecture

- **Status**: Accepted
- **Date**: 2026-09-22
- **Author**: Antigravity

## Context

MindWeaver uses class-based permission inheritance in `mindweaver.fw.permission`. To allow granular access control for each service and platform service, services require service-specific permission classes and enforcement across their CRUD endpoints and custom views. Furthermore, permissions need clean role boundaries separating full administrative management from read-only access without unnecessary intermediate layers.

## Decision

1. **Service `permission.py` Module Structure**:
   Each service defines a `permission.py` file declaring its class-based permission hierarchy:
   - **Root Management Permission (`Manage`)**:
     The primary management permission class in each service is named `Manage` (e.g., `mindweaver.service.project.permission.Manage`). It inherits from `mindweaver.fw.permission.Permission` with `name = "<service>:manage"` and acts as the root class covering all operations (mutating, operational, and viewing).
   - **Read-Only Permission (`Read`)**:
     `Read` inherits from `Manage` and framework `Read` (`mindweaver.fw.permission.Read`):
     ```python
     class Read(Manage, FwRead):
         name: str = "<service>:read"
     ```
     Granting `<service>:read` (or canonical alias `<Service>Read`) acts as the service-scoped read-only role, conferring access to all read-type actions on the service without granting mutating or execution privileges.
   - **Standard CRUD Actions**:
     - `List(Read, FwList)`: `"<service>:list"`
     - `View(Read, FwView)`: `"<service>:view"`
     - `Write(Manage, FwWrite)`: `"<service>:write"`
     - `Create(Write, FwCreate)`: `"<service>:create"`
     - `Update(Write, FwUpdate)`: `"<service>:update"`
     - `Delete(Write, FwDelete)`: `"<service>:delete"`
     - `Execute(Manage, FwExecute)`: `"<service>:execute"`
   - **Custom Views and Operational Actions**:
     Custom views inherit from either `View` (for read-only queries or status polling like `Refresh`, `CheckAvailability`, `DownloadCert`) or `Execute` (for operational tasks like `TestConnection`, `RenewCertificate`).
   - **Canonical Class Aliases**:
     Canonical class aliases (e.g., `ManageProject = Manage`, `Project = Manage`, `ProjectPermission = Manage`, `ProjectRead = Read`, etc.) are maintained for flexibility and backwards compatibility.

2. **Automatic String Registration**:
   `mindweaver.fw.permission.All.__init_subclass__` automatically registers subclasses with a `name` attribute into `_NAME_TO_PERMISSION` for uniform string resolution (e.g., `"project:manage"`, `"project:read"`).

3. **Service Integration & CRUD Routing**:
   Services configure `permissions = permission` on the service class. `ServiceViewMixin.get_permission(action)` dynamically resolves the permission for standard CRUD endpoints (`list`, `view`, `create`, `update`, `delete`, `execute`), defaulting to framework base classes when unassigned.

4. **Explicit Custom View Dependencies**:
   Custom views explicitly declare their permission requirement via `dependencies=[require(PermClass)]`.

## Consequences

- **Clean Two-Tier RBAC**: Clear distinction between full administrative management (`Manage`) and read-only inspection (`Read`), alongside granular action-level permissions (`Create`, `Update`, `Delete`, `Execute`).
- **Inheritance Compatibility**: Because service permissions inherit from framework classes (`Read`, `Write`, etc.), users with broad framework permissions (e.g., standard `FwRead` for authenticated users) automatically have access to read-only views for all services without explicit service-level grants.
- **Consistent Standardization**: Every service follows the exact same file and hierarchy pattern across the codebase.

## References

- [Mindweaver Constitution (Section 3 & 4)](file:///home/izhar/Projects/mindweaver/.agents/rules/constitution.md)
- [MindWeaver Framework Permission](file:///home/izhar/Projects/mindweaver/backend/src/mindweaver/fw/permission.py)
- [Mindweaver Backend Permissions Skill](file:///home/izhar/Projects/mindweaver/.agents/skills/mw-backend-permission/SKILL.md)

---
SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
SPDX-License-Identifier: AGPLv3+
