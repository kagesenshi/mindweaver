# 0011. Container and Helm Packaging Standards

- **Status**: Accepted
- **Date**: 2026-02-26
- **Author**: Antigravity

## Context

Mindweaver components are distributed as container images and Helm charts. Consistent packaging and registry interaction are vital for predictable deployments.

## Decision

We have established standards for building and pushing artifacts:
1. **GitHub OCI Registry**: All artifacts are pushed to `ghcr.io` under the project namespace.
2. **Helm Charts**: Charts are packaged as OCI artifacts.
3. **Multi-Arch**: Docker images are built to support relevant architectures (typically `linux/amd64`).
4. **AppVersion vs Chart Version**: The `appVersion` in `Chart.yaml` is kept in sync with the container image tag used.

## Consequences

- **Portability**: OCI-compliant artifacts can be consumed by any standard tool.
- **Integration**: Native integration with GitHub Actions and Kubernetes.
- **Discoverability**: Centralized artifact storage in the project repository.
- **Maintainability**: Clear separation between infrastructure (chart version) and application (app version) logic.

## References

- [Mindweaver Packaging Skill](file:///home/izhar/Projects/mindweaver/.agents/skills/mindweaver-packaging/SKILL.md)

---
SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
SPDX-License-Identifier: AGPLv3+
