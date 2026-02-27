# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import fastapi
from fastapi import Depends, Header, HTTPException
import asyncio
from typing import Annotated, List, Dict, Any, Type
from ..schema import ListResult, FormResult, Result, BaseResult
from ..exc import ModelValidationError
from ..action import ActionRequest


class ServiceViewMixin:
    """
    Mixin for services that handle custom views.
    """

    _custom_views: List[Dict[str, Any]] = []

    @classmethod
    def get_custom_views(cls) -> List[Dict[str, Any]]:
        """Returns all registered custom views for this class and its bases."""
        views = []
        for base in reversed(cls.__mro__):
            if "_custom_views" in base.__dict__ and isinstance(
                base.__dict__["_custom_views"], list
            ):
                views.extend(base.__dict__["_custom_views"])
        return views

    @classmethod
    def service_view(cls, method: str, path: str, **kwargs):
        """Decorator to register a new service level custom view on the service."""

        def decorator(cls_func):
            if "_custom_views" not in cls.__dict__:
                cls._custom_views = []
            cls._custom_views.append(
                {
                    "type": "service",
                    "method": method,
                    "path": path,
                    "func": cls_func,
                    "kwargs": kwargs,
                }
            )
            return cls_func

        return decorator

    @classmethod
    def model_view(cls, method: str, path: str, **kwargs):
        """Decorator to register a new model level custom view on the service."""

        def decorator(cls_func):
            if "_custom_views" not in cls.__dict__:
                cls._custom_views = []
            cls._custom_views.append(
                {
                    "type": "model",
                    "method": method,
                    "path": path,
                    "func": cls_func,
                    "kwargs": kwargs,
                }
            )
            return cls_func

        return decorator

    @classmethod
    def register_views(
        cls, router: fastapi.APIRouter, service_path: str, model_path: str
    ):
        """Register views for the service."""

        model_class = cls.model_class()
        entity_type = cls.entity_type()

        CreateModel = cls.createmodel_class()
        UpdateModel = cls.updatemodel_class()

        extra_deps = cls.extra_dependencies()

        path_tags = cls.path_tags()

        @router.get(
            service_path,
            operation_id=f"mw-list-{entity_type}",
            dependencies=extra_deps,
            tags=path_tags,
        )
        async def list_all(svc: Annotated[cls, Depends(cls.get_service)]) -> ListResult[model_class]:  # type: ignore
            records = await svc.all()
            return {"data": [await svc.post_process_model(r) for r in records]}

        @router.get(
            f"{service_path}/_create-form",
            operation_id=f"mw-create-form-{entity_type}",
            dependencies=extra_deps,
            tags=path_tags,
        )
        async def get_create_form() -> FormResult:
            return {
                "data": {
                    "jsonschema": CreateModel.model_json_schema(),
                    "widgets": cls.get_widgets(),
                    "immutable_fields": cls.immutable_fields(),
                    "internal_fields": cls.internal_fields(),
                }
            }

        if UpdateModel.model_fields:

            @router.get(
                f"{service_path}/_edit-form",
                operation_id=f"mw-edit-form-{entity_type}",
                dependencies=extra_deps,
                tags=path_tags,
            )
            async def get_edit_form() -> FormResult:
                return {
                    "data": {
                        "jsonschema": UpdateModel.model_json_schema(),
                        "widgets": cls.get_widgets(),
                        "immutable_fields": cls.immutable_fields(),
                        "internal_fields": cls.internal_fields(),
                    }
                }

        @router.post(
            service_path,
            operation_id=f"mw-create-{entity_type}",
            dependencies=cls.extra_dependencies(),
            tags=path_tags,
        )
        async def create(svc: Annotated[cls, Depends(cls.get_service)], data: CreateModel) -> Result[model_class]:  # type: ignore
            created_model = await svc.create(data)
            return {"data": await svc.post_process_model(created_model)}

        @router.get(
            model_path,
            operation_id=f"mw-get-{entity_type}",
            dependencies=cls.extra_dependencies(),
            tags=path_tags,
        )
        async def get(
            svc: Annotated[cls, Depends(cls.get_service)],
            model: Annotated[model_class, Depends(cls.get_model)],
        ) -> Result[model_class]:  # type: ignore
            return {"data": await svc.post_process_model(model)}

        if UpdateModel.model_fields:

            @router.put(
                model_path,
                operation_id=f"mw-update-{entity_type}",
                dependencies=cls.extra_dependencies(),
                tags=path_tags,
            )
            async def update(
                svc: Annotated[cls, Depends(cls.get_service)],  # type: ignore
                model: Annotated[model_class, Depends(cls.get_model)],  # type: ignore
                data: UpdateModel,
            ) -> Result[model_class]:  # type: ignore
                updated_model = await svc.update(model.id, data)
                return {"data": await svc.post_process_model(updated_model)}

        @router.delete(
            model_path,
            operation_id=f"mw-delete-{entity_type}",
            dependencies=cls.extra_dependencies(),
            tags=path_tags,
        )
        async def delete(
            svc: Annotated[cls, Depends(cls.get_service)],  # type: ignore
            model: Annotated[model_class, Depends(cls.get_model)],
            x_resource_name: Annotated[
                str | None, Header(alias="X-RESOURCE-NAME")
            ] = None,
        ) -> BaseResult:  # type: ignore
            if x_resource_name != model.name:
                raise ModelValidationError(
                    message=f"To delete this resource, the header 'X-RESOURCE-NAME' must match the resource name ('{model.name}')"
                )
            await svc.delete(model.id)
            return {"status": "success"}

        state_class = cls.get_state_class()
        if state_class:

            @router.get(
                f"{model_path}/_state",
                operation_id=f"mw-get-state-{entity_type}",
                dependencies=cls.extra_dependencies(),
                tags=path_tags,
            )
            async def get_state(
                svc: Annotated[cls, Depends(cls.get_service)],  # type: ignore
                model: Annotated[model_class, Depends(cls.get_model)],  # type: ignore
            ):
                state_instance = state_class(model, svc)
                if asyncio.iscoroutinefunction(state_instance.get):
                    return await state_instance.get()
                else:
                    return state_instance.get()

        @router.get(
            f"{model_path}/_actions",
            operation_id=f"mw-list-actions-{entity_type}",
            dependencies=cls.extra_dependencies(),
            tags=path_tags,
        )
        async def list_actions(
            svc: Annotated[cls, Depends(cls.get_service)],  # type: ignore
            model: Annotated[model_class, Depends(cls.get_model)],  # type: ignore
        ):
            actions = cls.get_actions()
            available_actions = []
            for name, action_cls in actions.items():
                action_instance = action_cls(model, svc)

                if hasattr(action_instance, "available"):
                    if asyncio.iscoroutinefunction(action_instance.available):
                        is_available = await action_instance.available()
                    else:
                        is_available = action_instance.available()
                    if not is_available:
                        continue

                available_actions.append(name)

            return {"actions": available_actions}

        @router.post(
            f"{model_path}/_actions",
            operation_id=f"mw-execute-action-{entity_type}",
            dependencies=cls.extra_dependencies(),
            tags=path_tags,
        )
        async def execute_action(
            svc: Annotated[cls, Depends(cls.get_service)],  # type: ignore
            model: Annotated[model_class, Depends(cls.get_model)],  # type: ignore
            request: ActionRequest,
        ):
            actions = cls.get_actions()
            if request.action not in actions:
                raise HTTPException(
                    status_code=400, detail=f"Action '{request.action}' not found"
                )

            action_cls = actions[request.action]
            action_instance = action_cls(model, svc)

            if hasattr(action_instance, "available"):
                if asyncio.iscoroutinefunction(action_instance.available):
                    is_available = await action_instance.available()
                else:
                    is_available = action_instance.available()
                if not is_available:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Action '{request.action}' is not available",
                    )

            params = dict(request.parameters)

            if asyncio.iscoroutinefunction(action_instance.__call__):
                return await action_instance(**params)
            else:
                return action_instance(**params)

        for view_spec in cls.get_custom_views():
            func = view_spec["func"]
            method = view_spec["method"]
            path = view_spec["path"]
            view_type = view_spec["type"]
            kwargs = dict(view_spec["kwargs"])

            # Use tags from service if not provided in kwargs
            if "tags" not in kwargs:
                kwargs["tags"] = path_tags

            # Use dependencies from service if not provided in kwargs
            if "dependencies" not in kwargs:
                kwargs["dependencies"] = cls.extra_dependencies()

            if view_type == "service":
                full_path = f"{service_path}{path}"
            else:
                full_path = f"{model_path}{path}"

            router.add_api_route(full_path, func, methods=[method], **kwargs)
