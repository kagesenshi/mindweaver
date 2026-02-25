# 0009. TDD and Testing Strategy

- **Status**: Accepted
- **Date**: 2026-02-26
- **Author**: Antigravity

## Context

To ensure high quality, maintainability, and reliability of the data platform management logic, the project requires a rigorous testing approach.

## Decision

We have adopted a mandatory **Test-Driven Development (TDD)** workflow for backend development. All significant features and bug fixes must start with a failing test case.

## Consequences

- **Backend Priority**: Features are not considered complete until all corresponding `pytest` cases pass.
- **Negative Testing**: Both "happy path" and error scenarios (negative tests) must be covered.
- **Automated Verification**: Full test suites are run via `uv run` locally and in CI to prevent regressions.
- **Documentation**: Tests serve as executable documentation for the intended behavior of services and models.

## References

- [Mindweaver Constitution (Section 3 & 7)](file:///home/izhar/Projects/mindweaver/.agent/rules/constitution.md)

---
SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
SPDX-License-Identifier: AGPLv3+
