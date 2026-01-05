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
- **Metadata Management**: Provide a centralized layer for managing projects, data sources, S3 connections, AI model APIs, knowledge bases, and AI agents.
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
- **Custom Views**: Must be prefixed with `+` to differentiate from collection resources (e.g., `/api/v1/service/+test-connection`).

### Model Definitions
- Use `SQLModel` for all database-backed models.
- Implement field immutability where necessary (e.g., `project_id` or `name` should often be immutable after creation).
- Template files for Kubernetes manifests should use the `.yml.j2` extension (Jinja2).

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
- Use the `DynamicForm` widget for simple data entry tasks.
- **Complex Requirements**: If a form requires conditional display, password widget, JSON field that require submission as dict instead of string, multi-step logic, or complex validation, implement a **Custom Form** rather than forcing it into a dynamic form.
- Custom view paths in frontend providers must match the `+` prefix used in the backend.

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
