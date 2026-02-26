# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.2] - Unreleased

## [0.1.1] - 2026-02-27

### Added
- Support for local credentials, including environment-based default admin login.
- Introduced `is_superadmin` flag for user management. Restricted user service operations to superadmins only.

### Changed
- Refactored authentication implementation to the framework (`fw`) for consistent usage across services.
- Centralized password hashing logic into a reusable mixin.
- **Breaking:** Alembic migration history has been reset to allow for a clean slate. Please clear the database and migrate again.

### Fixed
- Fixes to the login screen and various UI components.
- Fixes cluster status polling issue after switching to ArgoCD

## [0.1.0] - 2026-02-26

- Initial release with core framework and postgresql service
