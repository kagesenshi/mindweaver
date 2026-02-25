# 0001. Backend Framework Selection

- **Status**: Accepted
- **Date**: 2026-02-26
- **Author**: Antigravity

## Context

Mindweaver requires a robust, high-performance, and developer-friendly backend framework to manage Kubernetes-based data platform components. The framework needs to support asynchronous operations for I/O bound tasks (like interacting with Kubernetes APIs and databases) and provide strong type safety and validation.

## Decision

We have selected **FastAPI** as the web framework and **SQLModel** (built on top of SQLAlchemy 2.0 and Pydantic) as the ORM/Data Modeling layer.

## Consequences

- **Asynchronous natively**: FastAPI and SQLAlchemy 2.0 (via SQLModel) provide excellent support for `asyncio`, which is critical for our scalability.
- **Type Safety**: Pydantic integration ensures rigorous data validation and automatic Open API documentation.
- **Developer Productivity**: SQLModel allows us to use the same models for both database entities and API schemas, reducing boilerplate.
- **Modern Standards**: Performance is among the best for Python frameworks.

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)

---
SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
SPDX-License-Identifier: AGPLv3+
