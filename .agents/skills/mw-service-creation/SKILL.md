---
name: MindWeaver Service Creation
description: Comprehensive guide for creating new platform services in Mindweaver from backend to frontend.
---
# MindWeaver Service Creation

This guide covers the full end-to-end process of creating a new platform service (e.g., Hive Metastore, Trino).

## 1. Backend Implementation

### Define Models (`model.py`)
Inherit from `PlatformBase` and `PlatformStateBase`.
- Use `ProjectScopedNamedBase` for project-scoped resources.
- Include resource limits (CPU/Mem) and specific configuration fields.
- Add `model_validator` for inter-field validation.

### Implement Service (`service.py`)
Inherit from `PlatformService`.
- Specify `template_directory` and `state_model`.
- Implement `poll_status` to track health (usually via ArgoCD Application and Pod status).
- Implement `template_vars` to resolve secrets and connection strings.
- Define `widgets` for the `DynamicForm`. Always use the `type` key for widget types.
    ```python
    @classmethod
    def widgets(cls) -> dict[str, Any]:
        return {
            "password": {"type": "password"},
            "parameters": {"type": "key-value"},
        }
    ```

### Create Templates (`templates/`)
- `10-application.yml.j2`: ArgoCD Application manifest.
- `01-secret.yml.j2`: Kubernetes Secret for credentials.
- Use Jinja2 placeholders matched to `template_vars`.

### Register Router (`app.py`)
- Import the service router and include it in the FastAPI app.

## 2. Frontend Implementation

### Resource Hook (`useResources.js`)
- Add a custom hook (e.g., `useHiveMetastore`) using `apiClient`.
- Implement CRUD operations and state/action fetching.

### Page Components (`Page.jsx`, `ListingView.jsx`, `ServiceView.jsx`)
- **Page**: Main container managing view state (listing vs detail).
- **ListingView**: Use `ListingItem` with a horizontal layout.
- **ServiceView**: Use `DynamicForm` for configuration and show connection info (URIs, credentials).

## 3. Integration & Navigation

### Routing (`main.jsx`)
- Lazy load the new page and add the route to the main router.

### Sidebar (`Sidebar.jsx`)
- Add the new service to `INFRA_ITEMS` with a relevant `lucide-react` icon.

### Home Page (`HomePage.jsx`)
- Integrate the new platform into the "Unified Fleet" overview by fetching its instances and combining them with others.

### Platform Polling (`platform_status.py`)
- Register the new service in `backend/src/mindweaver/tasks/platform_status.py`.
- Add the service class to the `services` list in `poll_all_platforms`.
- Add the service class name to the `mapping` dictionary in `_poll_platform_status`.

## 4. Verification

### Backend Tests
- Create a unit test in `backend/tests/platform_service/`.
- Test model validation and template rendering.
- Run with `uv run --package mindweaver pytest`.

### Frontend Linting
- Run `npm run lint` to ensure no regressions or unused variables.
