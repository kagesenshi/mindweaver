---
trigger: manual
description: Constitution for this project
---

Title: Mindweaver

objectives:
- provide a management tool for deploying data platform components on kubernetes
- provide a metadata layer which manages core data warehousing, data lake and ai platform 
  metadata such as :
  - list of projects, which is a logical grouping of below components
  - list of data sources and their authentiction
  - list of s3 connections 
  - list of connections to AI model APIs (eg: gemini, openai)
  - list of knowledge base (which will store knowledge used by ai agents)
  - list of AI agents that uses knowledge base
  - list of ingestion jobs and their scheduling
  - list of kubernetes cluster and their kubeconfig (also supports in-cluster)
- platform technologies will be managed by this platform (all of which are created as argocd apps):
  - postgresql (deployed through using cnpg's cluster helm )
  - kafka (deployed through helm)
  - hive metastore (deployment through helm)
  - trino (deployed through helm)
  - airflow (deployed through helm)
  - superset (deployed through helm)
  - nifi (deployed through helm)
- the platform shall use authentication based on OIDC

This project uses following stack:
- flutter (for frontend)
- fastapi (for backend)
- python environment is managed using uv
- this project interacts with kubernetes for service deployment
- this project prefers async rather than sync
- this project uses SQLModel as base ORM

JSON response from backend should follow this rule:
- response JSON from backend should follow JSON:API 1.1 (jsonapi.org) specification as much as possible
- error related JSON response should follow the following standard:
  ```
  class ValidationErrorDetail(pydantic.BaseModel):
      msg: str
      type: str
      loc: list[str]

  class Error(pydantic.BaseModel):
      status: str
      type: str
      detail: str | ValidationErrorDetail
  ``` 

CRUD endpoints should follow this structure:
- `base_prefix` of `/api/v1/{service_name}` for most services
- `base_prefix` of `/api/v1/platform/{service_name}` for services related to platform deployment automation
- create endpoint - `POST {base_prefix}`
- update endpoint - `PUT {base_prefix}/{id}`
- delete endpoint - `DELETE {base_prefix}/{id}`
- read endpoint - `GET {base_prefix}/{id}`
- search endpoint - `GET {base_prefix}`
- additional collection centric views - `{base_prefix}/+{view_name}`
- additional model centric views - `{base_prefix}/{id}/+{view_name}`
- use JSON:API v1.1 spec for outputs
- search endpoint pagination use meta field, include `page_num`, `page_size`, `next_page`, `prev_page` attribute

Feature development approach:
- start with writing unit test in backend, use `TestClient` based testing
- implement feature in backend until test successful (update tests if you made mistake in the test)
- implement frontend.
- frontend unit test is best effort basis, and prefer manual testing by user

Notes:
- command to start backend: `uv run mindweaver run --port 8000` in `backend` folder
- command to start frontend: `flutter run -d chrome` in `frontend` folder
- remember to run `uv run pytest tests` in `backend` after modifying `backend`. You do not have to run this test if you only modifying `frontend`
- remember to add unit tests whenever creating new feature in `backend`
- jinja2 yaml templates should use .yml.j2 extension
- backend rules and data structure should be prioritized over frontend way of reading it. If there's discrepancies, frontend should follow backend and not the other way around.