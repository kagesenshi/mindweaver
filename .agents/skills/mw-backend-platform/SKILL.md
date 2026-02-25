---
name: MindWeaver Backend Platform
description: Platform services for managing external resources (Kubernetes, etc.) in MindWeaver.
---
# MindWeaver Backend Platform

Platform services manage external resources (like Kubernetes deployments).

## Creating a New Backend Platform Service

1.  **Define the Platform Model**: Inherit from `PlatformBase`.
    ```python
    from mindweaver.platform_service.base import PlatformBase

    class MyPlatform(PlatformBase, table=True):
        __tablename__ = "my_platform"
        # ... fields
    ```

2.  **Define the State Model**: Inherit from `PlatformStateBase`.
    ```python
    from mindweaver.platform_service.base import PlatformStateBase

    class MyPlatformState(PlatformStateBase, table=True):
        __tablename__ = "my_platform_state"
        # ... status fields
    ```

3.  **Define the Service**: Inherit from `PlatformService`.
    ```python
    from mindweaver.platform_service.base import PlatformService

    class MyPlatformService(PlatformService[MyPlatform]):
        template_directory: str = "/path/to/templates"
        state_model: type[MyPlatformState] = MyPlatformState

        @classmethod
        def model_class(cls):
            return MyPlatform

        async def poll_status(self, model: MyPlatform):
            # Implement logic to check status and update state
            pass
    ```

4.  **Create Templates**: Add Jinja2/YAML templates for Kubernetes manifests in the `template_directory`.

5.  **Register the Router**: As with standard services, register the router in `app.py`. The `PlatformService` adds `_deploy`, `_decommission`, `_state`, and `_refresh` endpoints.
