# 0007. Unified Versioning Strategy

- **Status**: Accepted
- **Date**: 2026-02-26
- **Author**: Antigravity

## Context

Managing multiple container images and Helm charts across various folders requires a consistent and automated versioning strategy to ensure compatibility and ease of deployment.

## Decision

We have implemented a unified versioning strategy based on `VERSION.txt` files:
1. A root `VERSION.txt` defines the version for the main application and its primary Helm chart.
2. Component-specific `VERSION.txt` files (e.g., for Hive Metastore) define versions for standalone images.
3. GitHub Actions workflows are configured to read these files and apply the versions to container tags and Helm chart metadata (`version` and `appVersion`).

## Consequences

- **Consistency**: All built artifacts (OCI images, Helm charts) share the same version specified in the source tree.
- **Traceability**: Version numbers in the registry directly correspond to version anchors in the code.
- **Automation**: CI/CD pipelines automatically tag and package artifacts without manual version overrides.
- **Simplicity**: Developers only need to update a text file to trigger a versioned release.

## References

- [Mindweaver Packaging Skill](file:///home/izhar/Projects/mindweaver/.agents/skills/mindweaver-packaging/SKILL.md)

---
SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
SPDX-License-Identifier: AGPLv3+
