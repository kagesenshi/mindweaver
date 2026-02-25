# 0004. Kubernetes Orchestration (ArgoCD)

- **Status**: Accepted
- **Date**: 2026-02-26
- **Author**: Antigravity

## Context

Mindweaver's primary function is to manage and deploy data platform components on Kubernetes. We need a reliable mechanism to manage the lifecycle of these components, ensuring they match the desired state defined in metadata.

## Decision

We have selected **ArgoCD** as the orchestration and GitOps engine for component deployment.

## Consequences

- **GitOps for Apps**: Leverage industry-standard GitOps patterns for application deployment.
- **State Management**: ArgoCD automatically handles synchronization and detects drift between desired and actual cluster states.
- **Cleanup**: Integration with ArgoCD finalizers ensures that deleting a parent Application resource also cleans up all child resources (e.g., PostgreSQL clusters).
- **Remote Cluster Support**: Ability to manage applications across multiple Kubernetes clusters from a central control plane.

## References

- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)

---
SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
SPDX-License-Identifier: AGPLv3+
