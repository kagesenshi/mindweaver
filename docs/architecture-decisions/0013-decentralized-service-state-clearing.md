# 0013. Decentralized Service State Clearing via BaseState Subclasses

- **Status**: Accepted
- **Date**: 2026-10-26
- **Author**: Mohd Izhar Firdaus Bin Ismail

## Context

When a platform service is decommissioned, its runtime state (status, connection endpoints, credentials, node ports, etc.) must be cleared and marked offline. Previously, `PlatformService.clear_state` maintained a hardcoded list of service-specific attributes (`kafka_url`, `airflow_uri`, `query_uri`, `trino_uri`, etc.). This violated open/closed design principles and caused tight coupling between `PlatformService` base and concrete platform services. Furthermore, credentials and custom properties (e.g. `admin_password`) were missed or required ad-hoc overrides on individual service classes (such as in `PgSqlPlatformService`).

## Decision

We delegate all state clearing operations to the service state object (`BaseState` / `DefaultPlatformState` subclass):
1. `BaseState` defines an asynchronous `clear(self)` method (default no-op).
2. `DefaultPlatformState` implements `clear(self)` to reset common `PlatformStateBase` attributes (`status="offline"`, `message="Decommissioned"`, `active=False`, `node_ports=[]`, `cluster_nodes=[]`, `extra_data={}`), add to session, and flush.
3. Specific platform state classes (e.g. `PgSqlState`, `KafkaState`, `AirflowState`, `DorisState`, `TrinoState`, `SupersetState`, `HiveMetastoreState`, `NifiState`) override `clear(self)` to clean up their specific fields (`db_user`, `db_pass`, `kafka_url`, `airflow_uri`, `query_uri`, etc.) and invoke `await super().clear()`.
4. `PlatformService.clear_state(model)` resolves the state class dynamically via `self.get_state_class()` and invokes `await state_instance.clear()`, eliminating all hardcoded service attributes from base.

## Consequences

- **Decoupling**: `PlatformService` has zero knowledge of service-specific state fields.
- **Extensibility**: New platform services and models define their own state cleanup logic in their dedicated `State` class.
- **Atomic Persistence**: Custom fields and base state attributes are modified on the model instance and persisted in a single session flush and refresh.
- **Maintainability**: State handling logic is centralized inside the state classes alongside `get()`.

## References

- [0006. Platform Management (State and Actions)](file:///home/izhar/Projects/mindweaver/docs/architecture-decisions/0006-platform-management.md)
- [Mindweaver Constitution](file:///home/izhar/Projects/mindweaver/.agents/rules/constitution.md)

---
SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
SPDX-License-Identifier: AGPLv3+
