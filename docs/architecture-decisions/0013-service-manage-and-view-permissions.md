# 0013. Service Manage and View Permission Partitioning

- **Status**: Accepted
- **Date**: 2026-09-22
- **Author**: Antigravity

## Context

Service-level permissions previously defined a root base class named after the service (e.g. `Project`). When creating role templates or assigning coarse-grained permissions, roles often need clear separation between full administrative management (`Manage<Service>`) and read-only inspection (`View<Service>`).

## Decision

1. **Manage Permission**: The primary service management permission is renamed to `Manage<Service>` (e.g., `ManageProject`). It inherits from `mindweaver.fw.permission.Permission` and serves as the root class for mutating (`Write`), operational (`Execute`), and read actions.
2. **View Permission**: A distinct `View<Service>` class (e.g., `ViewProject`) inherits from `Manage<Service>`. All read-only and inspection actions (`Read`, `List`, `View`, `Refresh`, `DownloadCert`, `CertManager`, `CertificateDetails`, etc.) inherit from `View<Service>` (and framework `Read`/`View`/`List`). Status refresh actions are considered view-type permissions as they poll and sync read status.
3. **Inheritance & Isolation**:
   - Granting `Manage<Service>` covers all operations (mutating, operational, and viewing).
   - Granting `View<Service>` covers all view-type actions, but strictly excludes `Write`, `Create`, `Update`, `Delete`, and `Execute` actions.
4. **Aliases and Lookup**: Canonical aliases (e.g. `Project = ManageProject`, `ProjectPermission = ManageProject`) and string names (e.g. `project:manage`, `manage_project`, `project`, `project:view_project`, `view_project`) are maintained in `_NAME_TO_PERMISSION` for uniform resolution.

## Consequences

- Clean and explicit role definition: users or roles can be granted read-only observer access via `View<Service>` or administrative access via `Manage<Service>`.
- Full backwards compatibility with existing references and string lookup keys.

## References

- [Mindweaver Constitution (Section 3 & 4)](file:///home/izhar/Projects/mindweaver/.agents/rules/constitution.md)
- [Mindweaver Service Permission Architecture (ADR 0012)](file:///home/izhar/Projects/mindweaver/docs/architecture-decisions/0012-service-permission-architecture.md)
- [Project Permission Definition](file:///home/izhar/Projects/mindweaver/backend/src/mindweaver/service/project/permission.py)

---
SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
SPDX-License-Identifier: AGPLv3+
