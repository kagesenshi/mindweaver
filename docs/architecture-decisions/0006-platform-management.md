# 0006. Platform Management (State and Actions)

- **Status**: Accepted
- **Date**: 2026-02-26
- **Author**: Antigravity

## Context

Platform components (like PostgreSQL, Kafka) have complex lifecycles and states (Provisioning, Healthy, Degraded, Decommissioned). We need a unified way to track and control these states.

## Decision

We use a state-based architecture where:
1. Platform components inherit from a common `PlatformStateBase`.
2. Asynchronous actions (e.g., `_deploy`, `_decommission`) are used to trigger state transitions.
3. A polling mechanism (`poll_status`) synchronizes the internal database state with the external reality (e.g., ArgoCD status, Kubernetes resource status).

## Consequences

- **Consistency**: Standardized naming for deployment actions (`_deploy`, `_decommission`) across all platform services.
- **Visibility**: Real-time status reporting in both the UI and API.
- **Resilience**: The backend can recover state information by polling even if a transition event was missed.
- **Decoupling**: The API remains responsive by triggering long-running deployment tasks asynchronously.

## References

- [Mindweaver Constitution (Section 4)](file:///home/izhar/Projects/mindweaver/.agent/rules/constitution.md)

---
SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
SPDX-License-Identifier: AGPLv3+
