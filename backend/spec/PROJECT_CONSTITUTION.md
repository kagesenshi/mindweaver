---
trigger: always_on
glob:
description: Constitution for this project
---

# Mindweaver Project Constitution

This document serves as the "constitution" for the Mindweaver project. It defines the core principles, technical standards, and development workflows that all developers and AI agents must follow to maintain consistency, security, and quality across the codebase.

---

## 1. Vision & Objectives

Mindweaver is a management tool for deploying data platform components on Kubernetes. It provides a metadata layer to manage core data warehousing, data lake, and AI platform components.

### Core Objectives:
- **Component Deployment**: Automate the deployment of data platform components (PostgreSQL, Kafka, Trino, Airflow, etc.) on Kubernetes using ArgoCD.
- **Metadata Management**: Provide a centralized layer for managing:
  - Projects (logical groupings of components).
  - Data sources and their authentication.
  - S3 connections.
  - AI model API connections (e.g., Gemini, OpenAI).
  - Knowledge Bases (storing knowledge for AI agents).
  - AI Agents (utilizing Knowledge Bases).
  - Ingestion jobs and their scheduling.
  - Kubernetes clusters and their kubeconfig.
- **Security**: Implement robust authentication based on OIDC and secure handling of sensitive data.
- **Unified Interface**: Provide a seamless experience between the backend API and the Flutter frontend.

---

## 2. Technical Stack

- **Backend**: FastAPI (Python 3.11+)
- **ORM/Database**: SQLModel (SQLAlchemy 2.0 based)
- **Environment Management**: `uv`
- **Frontend**: Flutter (Targeting Web/Desktop)
- **Orchestration**: Kubernetes, ArgoCD
- **Testing**: `pytest` (Backend), Flutter test framework (Frontend)

---

## 3. Core Principles

- **Prioritize Backend**: Backend rules and data structures take precedence. Frontend implementation must match backend expectations.
- **Prefer Async**: The backend architecture is built around Python's `asyncio`. Use `async` for all I/O bound operations.
- **Test-Driven Development (TDD)**: Always start feature development by writing backend unit tests. Features are not complete until tests pass. Whenever making fixes in backend, update
the tests first before implementing the fixes.
- **Strict Data Handling**: Sensitive fields (passports, tokens, secret keys) must never be exposed in plain text via the API.

---

## 4. Backend Development Standards

### API Specification (JSON:API)
- Responses must follow **JSON:API 1.1** specification as much as possible.
- Error responses must use a structured format:
  ```python
  class ValidationErrorDetail(pydantic.BaseModel):
      msg: str
      type: str
      loc: list[str]

  class Error(pydantic.BaseModel):
      status: str
      type: str
      detail: str | ValidationErrorDetail
  ```

### CRUD Naming & Routing
- Base prefixes:
  - Standard services: `/api/v1/{service_name}`
  - Platform deployment services: `/api/v1/platform/{service_name}`
- Endpoints:
  - `POST {base_prefix}`: Create
  - `GET {base_prefix}/{id}`: Read
  - `PUT {base_prefix}/{id}`: Update
  - `DELETE {base_prefix}/{id}`: Delete
  - `GET {base_prefix}`: Search/List (with pagination in `meta`)
- **Custom Views**: Must be prefixed with `+` to differentiate from collection resources or ID-based resources.
  - Collection-centric: `{base_prefix}/+{view_name}` (e.g., `/api/v1/service/+test-connection`)
  - Model-centric: `{base_prefix}/{id}/+{view_name}` (e.g., `/api/v1/platform/pgsql/{id}/+deploy`)
- **Standard Platform Actions**: For platform services, use `+deploy` and `+decommission` for deployment operations.

### Model Definitions
- Use `SQLModel` for all database-backed models.
- Implement field immutability where necessary (e.g., `project_id` or `name` should often be immutable after creation).
- **Form Metadata**: Backend models should specify UI metadata via `sa_column_kwargs` or custom attributes if available:
  - `order`: Integer to control field display sequence (e.g., `project_id` = 1, `name` = 2).
  - `column_span`: Control width in the form layout (e.g., `description` might span full width).
  - `label`: Override the default field name for UI display.
- **Deployment Status**: Platform components should use a state table inheriting from `PlatformStateBase` with `status` (bool) and `active` (bool) columns.
- **Templates**: Kubernetes manifests should use the `.yml.j2` extension (Jinja2).
- **Timezones**: Always use timezone-aware columns in database models.

### Code Quality & Deprecations
- If a deprecation warning appear in backend for newly written work, rectify the warning. ideally there should not be any deprecation warning for newly created work. Granted, sometimes it is not feasible (require major changes), if that happens, advise the developer accordingly

### Modifying Agent Rules
- If you are requested to update rule file in `.agent/rules/` first copy it out into a temporary file in
  project root. Modify it, and then move the modified copy to replace the old file
- Avoid doing in-function imports. Import must always be at top of file 
  unless trying to workaround circular import, or when writing function
  for pickling (eg: pyspark udf, multiprocessing)

---

## 5. Security & Sensitive Data

### Encrypted Fields
- Encrypted fields in the backend must be redacted when returned via GET endpoints. Use the literal string `__REDACTED__`.
- **Updating Encrypted Fields**:
  - To keep the existing value, provide `__REDACTED__` as input.
  - To clear the field, provide `__CLEAR__` as input (backend will set to an empty string).
  - Any other value will be treated as a new value and encrypted.

---

## 6. Frontend Development Standards

### UI/UX Consistency
- **Dynamic Forms**: Use `DynamicForm` for standard CRUD operations and simple data entry. It supports:
  - Automatic rendering from backend JSON schema.
  - Field ordering and column spanning.
  - Label overrides from backend metadata.
- **Custom Forms**: Implement a **Custom Form** (e.g., using `LargeDialog`) if a form requires:
  - Conditional field display (logic-based visibility).
  - Complex validation beyond basic types.
  - Multi-step logic or non-standard submission formats.
  - Specialized widgets not supported by `DynamicForm`.
- **Naming**: Custom view paths in frontend providers must match the `_` prefix used in the backend.

### Backend Synchronization
- Always fetch JSON schema and form metadata from the backend to render dynamic forms.
- Prioritize backend labels and widget configurations; only override in frontend when absolutely necessary for UX.

---

## 7. Development Workflow

1. **Research & Plan**: Understand the requirements and existing patterns.
2. **Backend implementation**:
   - Write `pytest` unit tests in `backend/tests`.
   - Implement models and service logic.
   - Run `uv run pytest tests` to verify.
3. **Frontend Implementation**:
   - Create models and providers.
   - Implement pages/components.
   - Perform manual verification.
4. **Verification**:
   - Run the full unit tests:
     - Backend: `uv run --package mindweaver pytest`

---

## 8. AI Agent Instructions

- **Consult the Rules**: Always check `.agent/rules/` before proposing changes.
- **Be Concise**: When updating code, make targeted edits rather than replacing entire files.
- **Verify**: Never assume code works; run tests and provide proof of verification in walkthroughs.
- **Communicate**: If a design decision is ambiguous, ask the user for clarification before proceeding.
