# 0005. Sensitive Data Handling (Redaction)

- **Status**: Accepted
- **Date**: 2026-02-26
- **Author**: Antigravity

## Context

The application handles sensitive information such as database passwords, API tokens, and secret keys. This data must not be exposed in clear text via API endpoints or user interfaces.

## Decision

We have implemented a strict redaction policy for sensitive fields in the backend.

## Consequences

- **Redaction by Default**: All sensitive fields are replaced with the literal string `__REDACTED__` in GET responses.
- **Updates**: 
    - To preserve the existing value, clients must send `__REDACTED__`.
    - To clear a field, clients must send `__CLEAR__`.
    - Any other value is treated as a new secret and is encrypted before storage.
- **Security**: Reduces the risk of accidental exposure of credentials in logs, browser history, or intercepted traffic.

## References

- [Mindweaver Constitution (Section 5)](file:///home/izhar/Projects/mindweaver/.agent/rules/constitution.md)

---
SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
SPDX-License-Identifier: AGPLv3+
