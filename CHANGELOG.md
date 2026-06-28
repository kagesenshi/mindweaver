<!--
SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
SPDX-License-Identifier: AGPLv3+
-->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.3] - 2026-06-29

### Added
- Initial MVP release offering core framework orchestration capabilities to deploy and manage data platform components on Kubernetes, including:
  - **PostgreSQL**: High-availability relational database service.
  - **Apache Kafka**: Event streaming platform.
  - **Apache Airflow**: Workflow orchestration engine.
  - **Trino**: Distributed SQL query engine.
  - **Hive Metastore**: Centralized schema metadata repository.
  - **Apache NiFi**: Data integration and routing system.
  - **Elasticsearch**: Search, analytics, and indexing engine.
  - **Apache Superset**: Data exploration and visualization dashboard.
- Out-of-the-box SSL/TLS support configured across all deployed services.
- Metadata management for Projects, K8S Clusters, S3 Connections, Git Repositories, LDAP Configurations, and Container Registries.

### Changed
- Centralized user authentication framework. Authorization support is currently omitted as Apache Ranger was determined to be unsuitable for the architecture.
- **Breaking:** Database migrations have been reset. You will need to drop all existing tables and rerun the migrations.
