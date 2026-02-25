# 0010. Custom View Naming Convention

- **Status**: Accepted
- **Date**: 2026-02-26
- **Author**: Antigravity

## Context

To differentiate between standard CRUD resource endpoints and custom business logic views or actions (e.g., test connection, deploy), a clear naming convention is required to avoid collision with resource IDs.

## Decision

All custom view endpoints in both Backend (FastAPI) and Frontend (React providers) must be prefixed with an underscore (`_`).

## Consequences

- **Routing Clarity**: `/api/v1/service/_test-connection` is clearly distinguished from `/api/v1/service/{id}`.
- **Model vs Collection**:
    - Collection-centric: `{base_prefix}/_{view_name}` (e.g., `/_install-argocd`).
    - Model-centric: `{base_prefix}/{id}/_{view_name}` (e.g., `/{id}/_deploy`).
- **Code Consistency**: Frontend providers use the same path structure, simplifying the mapping between services.
- **Avoid Collisions**: Prevents potential conflicts if a resource ID happens to match a custom view name.

## References

- [Mindweaver Constitution (Section 4)](file:///home/izhar/Projects/mindweaver/.agent/rules/constitution.md)

---
SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
SPDX-License-Identifier: AGPLv3+
