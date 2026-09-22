# 0012. Service-Specific Permission Architecture

- **Status**: Accepted
- **Date**: 2026-09-22
- **Author**: Antigravity

## Context

MindWeaver uses class-based permission inheritance in `mindweaver.fw.permission`. To allow granular access control for each service and platform service, services require service-specific permission classes and enforcement across their CRUD endpoints and custom views.

## Decision

1. **Service `permission.py`**: Each service and platform service defines a `permission.py` file containing permission classes inheriting from `mindweaver.fw.permission` base classes (`Permission`, `Read`, `Write`, `Execute`, etc.) and the service base permission class.
2. **Auto-registration**: `mindweaver.fw.permission.All.__init_subclass__` automatically registers subclasses with a `name` attribute into `_NAME_TO_PERMISSION` for uniform string resolution.
3. **Service Integration**: Services define `permissions = permission` (or provide permission classes). `ServiceViewMixin.get_permission(action)` dynamically resolves the permission for standard CRUD endpoints (`list`, `view`, `create`, `update`, `delete`, `execute`), defaulting to framework base classes when unassigned.
4. **Explicit Custom View Dependencies**: Custom views explicitly require their corresponding permission using `dependencies=[require(PermClass)]`.

## Consequences

- **Granular RBAC**: Users and roles can be assigned service-scoped permissions (e.g. `ProjectPermission`, `ProjectRead`, `ProjectRefresh`) without losing framework-wide consistency.
- **Inheritance Compatibility**: Because service permissions inherit from framework classes (`Read`, `Write`, etc.), users with broad permissions (e.g., standard `Read` for authenticated users) automatically have access to read-only views for all services without explicit service-level grants.
- **Clean Standardized Pattern**: All services and platform services follow the exact same structure for permissions.

## References

- [Mindweaver Constitution (Section 3 & 4)](file:///home/izhar/Projects/mindweaver/.agents/rules/constitution.md)
- [MindWeaver Framework Permission](file:///home/izhar/Projects/mindweaver/backend/src/mindweaver/fw/permission.py)

---
SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
SPDX-License-Identifier: AGPLv3+
