# 0008. Async-First Architecture

- **Status**: Accepted
- **Date**: 2026-02-26
- **Author**: Antigravity

## Context

Interacting with external services (Kubernetes, ArgoCD, Databases) involves significant I/O wait times. A synchronous architecture would block worker threads, limiting concurrency and responsiveness.

## Decision

The backend architecture is built around Python's `asyncio`. Use of `async/await` is mandatory for all I/O bound operations.

## Consequences

- **Concurrency**: Enables the application to handle many concurrent connections with minimal overhead.
- **Responsiveness**: Long-running operations don't block the main event loop, ensuring the API remains responsive.
- **Code Standard**: All service methods and API endpoints must be defined using `async def`.
- **Database**: Use of asynchronous database drivers (e.g., via SQLAlchemy's async support) is required.

## References

- [Mindweaver Constitution (Section 3)](file:///home/izhar/Projects/mindweaver/.agent/rules/constitution.md)

---
SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
SPDX-License-Identifier: AGPLv3+
