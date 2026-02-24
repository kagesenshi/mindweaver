# SPDX-FileCopyrightText: Copyright © 2025 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from pydantic import BaseModel, Field, create_model, AnyUrl, ConfigDict
import fastapi
from fastapi import Depends, Header
import sqlalchemy as sa
from uuid import UUID
from sqlmodel import SQLModel, Session, select
from sqlmodel.ext.asyncio.session import AsyncSession
import sqlalchemy.exc as saexc
from .model import AsyncSession, ts_now, NamedBase
from .exc import ModelValidationError, AlreadyExistError
import enum
import abc
import jinja2 as j2
from .exc import NotFoundError
from .util import camel_to_snake
import graphlib
import inspect
import re
import asyncio
from fastapi import HTTPException
from mindweaver.crypto import encrypt_password, EncryptionError
from typing import Generic, TypeVar, Any, Literal, Annotated, Union, List, Dict
from mindweaver.fw.action import ActionRequest, BaseAction
from mindweaver.fw.state import BaseState

T = TypeVar("T", bound=NamedBase)
S = TypeVar("S", bound=SQLModel)


class ErrorDetail(BaseModel):
    loc: list[Any] = Field(default_factory=list)
    msg: str | None = None
    type: str | None = None


class ValidationErrorDetail(BaseModel):
    msg: str
    type: str
    loc: list[str]


class Error(BaseModel):
    status: str
    type: str
    detail: list[ValidationErrorDetail] | ValidationErrorDetail | str


STATUSES = Literal["success", "error"]


class BaseResult(BaseModel):
    detail: list[ErrorDetail] | None = None
    status: STATUSES = "success"


class Result(BaseResult, Generic[T]):
    data: T


class FormSchema(BaseModel):
    jsonschema: dict[str, Any]
    widgets: dict[str, Any]
    immutable_fields: list[str]
    internal_fields: list[str]


class FormResult(BaseResult):
    data: FormSchema


class PaginationMeta(BaseModel):
    page_num: int | None = None
    page_size: int | None = None
    next_page: AnyUrl | None = None
    prev_page: AnyUrl | None = None


class ListResult(BaseResult, Generic[T]):
    data: list[T] | None = None
    meta: PaginationMeta | None = None

    model_config = ConfigDict(populate_by_name=True)


def redefine_model(name, Model: type[BaseModel], *, exclude=None) -> type[BaseModel]:
    exclude = exclude or []

    fields = {
        fname: (field.annotation, field)
        for fname, field in Model.model_fields.items()
        if fname not in exclude
    }

    model = create_model(name, **fields)
    return model


def before_create(func=None, *, before=None, after=None):
    def decorator(f):
        sig = inspect.signature(f)
        if len(sig.parameters) != 2:
            raise TypeError(
                f"before_create hook must accept 2 arguments (self, data), got {len(sig.parameters)}"
            )
        f._is_before_create_hook = True
        f._hook_before = [before] if isinstance(before, str) else (before or [])
        f._hook_after = [after] if isinstance(after, str) else (after or [])
        return f

    if func:
        return decorator(func)
    return decorator


def after_create(func=None, *, before=None, after=None):
    def decorator(f):
        sig = inspect.signature(f)
        if len(sig.parameters) != 2:
            raise TypeError(
                f"after_create hook must accept 2 arguments (self, model), got {len(sig.parameters)}"
            )
        f._is_after_create_hook = True
        f._hook_before = [before] if isinstance(before, str) else (before or [])
        f._hook_after = [after] if isinstance(after, str) else (after or [])
        return f

    if func:
        return decorator(func)
    return decorator


def before_update(func=None, *, before=None, after=None):
    def decorator(f):
        sig = inspect.signature(f)
        if len(sig.parameters) != 3:
            raise TypeError(
                f"before_update hook must accept 3 arguments (self, model, data), got {len(sig.parameters)}"
            )
        f._is_before_update_hook = True
        f._hook_before = [before] if isinstance(before, str) else (before or [])
        f._hook_after = [after] if isinstance(after, str) else (after or [])
        return f

    if func:
        return decorator(func)
    return decorator


def after_update(func=None, *, before=None, after=None):
    def decorator(f):
        sig = inspect.signature(f)
        if len(sig.parameters) != 2:
            raise TypeError(
                f"after_update hook must accept 2 arguments (self, model), got {len(sig.parameters)}"
            )
        f._is_after_update_hook = True
        f._hook_before = [before] if isinstance(before, str) else (before or [])
        f._hook_after = [after] if isinstance(after, str) else (after or [])
        return f

    if func:
        return decorator(func)
    return decorator


def before_delete(func=None, *, before=None, after=None):
    def decorator(f):
        sig = inspect.signature(f)
        if len(sig.parameters) != 2:
            raise TypeError(
                f"before_delete hook must accept 2 arguments (self, model), got {len(sig.parameters)}"
            )
        f._is_before_delete_hook = True
        f._hook_before = [before] if isinstance(before, str) else (before or [])
        f._hook_after = [after] if isinstance(after, str) else (after or [])
        return f

    if func:
        return decorator(func)
    return decorator


def after_delete(func=None, *, before=None, after=None):
    def decorator(f):
        sig = inspect.signature(f)
        if len(sig.parameters) != 2:
            raise TypeError(
                f"after_delete hook must accept 2 arguments (self, model), got {len(sig.parameters)}"
            )
        f._is_after_delete_hook = True
        f._hook_before = [before] if isinstance(before, str) else (before or [])
        f._hook_after = [after] if isinstance(after, str) else (after or [])
        return f

    if func:
        return decorator(func)
    return decorator


def _sort_hooks(hooks: list[Any]) -> list[Any]:
    if not hooks:
        return []

    graph = {h.__name__: set() for h in hooks}
    name_to_hook = {h.__name__: h for h in hooks}

    for hook in hooks:
        # Handle 'after' dependencies: hook depends on other (other -> hook)
        for other_name in hook._hook_after:
            if other_name in graph:
                graph[hook.__name__].add(other_name)

        # Handle 'before' dependencies: other depends on hook (hook -> other)
        for other_name in hook._hook_before:
            if other_name in graph:
                graph[other_name].add(hook.__name__)

    ts = graphlib.TopologicalSorter(graph)
    try:
        sorted_names = list(ts.static_order())
    except graphlib.CycleError as e:
        raise ValueError(f"Circular dependency detected in hooks: {e.args[1]}")

    return [name_to_hook[name] for name in sorted_names]


class SecretHandlerMixin:
    """
    Mixin for services that handle sensitive fields that should be redacted
    when returned to the client and encrypted when stored in the database.
    """

    @classmethod
    def redacted_fields(cls) -> list[str]:
        """
        Return a list of field names that should be redacted/encrypted.
        """
        return []

    @before_create
    async def _handle_redacted_create(self, model: S):
        for field in self.redacted_fields():
            val = getattr(model, field, None)
            if val:
                try:
                    setattr(model, field, encrypt_password(val))
                except EncryptionError as e:
                    raise HTTPException(
                        status_code=500, detail=f"Failed to encrypt {field}: {str(e)}"
                    )

    @before_update
    async def _handle_redacted_update(self, model: S, data: NamedBase):
        data_dict = data.model_dump(exclude_unset=True)
        for field in self.redacted_fields():
            if field in data_dict:
                val = data_dict[field]
                if val == "__REDACTED__":
                    # Keep existing value (set data field to current model value)
                    setattr(data, field, getattr(model, field))
                elif val == "__CLEAR__":
                    setattr(data, field, "")
                elif val:
                    try:
                        setattr(data, field, encrypt_password(val))
                    except EncryptionError as e:
                        raise HTTPException(
                            status_code=500,
                            detail=f"Failed to encrypt {field}: {str(e)}",
                        )

    async def post_process_model(self, model: S) -> S:
        """
        Redact sensitive fields before returning to client.
        Creates a copy to avoid modifying the session model.
        """
        if hasattr(super(), "post_process_model"):
            model = await super().post_process_model(model)

        redacted_fields = self.redacted_fields()
        if not redacted_fields:
            return model

        # Check if any field needs redaction
        has_sensitive_data = any(
            getattr(model, field, None) for field in redacted_fields
        )
        if not has_sensitive_data:
            return model

        # Create a copy and redact
        model_dict = model.model_dump()
        for field in redacted_fields:
            if model_dict.get(field):
                model_dict[field] = "__REDACTED__"

        return model.__class__.model_validate(model_dict)


class Service(Generic[S], abc.ABC):
    _before_create_hooks: list[Any] = []
    _after_create_hooks: list[Any] = []
    _before_update_hooks: list[Any] = []
    _after_update_hooks: list[Any] = []
    _before_delete_hooks: list[Any] = []
    _after_delete_hooks: list[Any] = []
    _registry: Dict[str, type["Service"]] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._before_create_hooks = []
        cls._after_create_hooks = []
        cls._before_update_hooks = []
        cls._after_update_hooks = []
        cls._before_delete_hooks = []
        cls._after_delete_hooks = []

        # Collect hooks from MRO in reverse order (base to child)
        # Use a dict to avoid duplicates and respect definition order within class
        collected_before_create = {}
        collected_after_create = {}
        collected_before_update = {}
        collected_after_update = {}
        collected_before_delete = {}
        collected_after_delete = {}

        for base in reversed(cls.mro()):
            # We want to collect hooks from all base classes that might have them,
            # not just those inheriting from Service (like mixins).
            if base is object:
                continue

            for attr_name, attr in base.__dict__.items():
                if getattr(attr, "_is_before_create_hook", False):
                    collected_before_create[attr_name] = attr
                if getattr(attr, "_is_after_create_hook", False):
                    collected_after_create[attr_name] = attr
                if getattr(attr, "_is_before_update_hook", False):
                    collected_before_update[attr_name] = attr
                if getattr(attr, "_is_after_update_hook", False):
                    collected_after_update[attr_name] = attr
                if getattr(attr, "_is_before_delete_hook", False):
                    collected_before_delete[attr_name] = attr
                if getattr(attr, "_is_after_delete_hook", False):
                    collected_after_delete[attr_name] = attr

        cls._before_create_hooks = _sort_hooks(list(collected_before_create.values()))
        cls._after_create_hooks = _sort_hooks(list(collected_after_create.values()))
        cls._before_update_hooks = _sort_hooks(list(collected_before_update.values()))
        cls._after_update_hooks = _sort_hooks(list(collected_after_update.values()))
        cls._before_delete_hooks = _sort_hooks(list(collected_before_delete.values()))
        cls._after_delete_hooks = _sort_hooks(list(collected_after_delete.values()))

        # Register service by table name
        if not abc.ABC in cls.__bases__:
            # Use getattr to avoid potential issues with classmethods in some Python versions/contexts
            model_class_method = getattr(cls, "model_class", None)
            if model_class_method and not getattr(
                model_class_method, "__isabstractmethod__", False
            ):
                model_class = cls.model_class()
                if hasattr(model_class, "__tablename__"):
                    Service._registry[model_class.__tablename__] = cls

    @classmethod
    @abc.abstractmethod
    def model_class(cls) -> type[S]:
        """
        Provide SQLModel class for this service to interact with
        """
        raise NotImplementedError("model_class must be implemented")

    @classmethod
    def createmodel_class(cls) -> type[BaseModel]:
        """
        This function provide a Pydantic model based on schema class,
        with internal fields and immutable fields removed
        for use in create view/operation
        """
        model_class = cls.model_class()
        schema_class = cls.schema_class()
        return redefine_model(
            f"Create {model_class.__name__}",
            schema_class,
            exclude=cls.internal_fields(),
        )

    @classmethod
    def updatemodel_class(cls) -> type[BaseModel]:
        """
        This function provide a Pydantic model based on schema class,
        with internal fields and immutable fields removed
        for use in update view/operation
        """
        model_class = cls.model_class()
        schema_class = cls.schema_class()
        return redefine_model(
            f"Update {model_class.__name__}",
            schema_class,
            exclude=cls.internal_fields(),
        )

    @classmethod
    def schema_class(cls) -> type[NamedBase]:
        """
        This function provide schema class for use in forms. By default it will use model class.
        Override this if you need to use a different schema in forms
        """
        return cls.model_class()

    @classmethod
    def service_path(cls) -> str:
        return f"/{cls.entity_type()}s"

    @classmethod
    def model_path(cls) -> str:
        return f"{cls.service_path()}/{{id}}"

    @classmethod
    def internal_fields(cls) -> list[str]:
        # fields that are internal to the system , can be exposed to the user, but user should
        # not be able to set or change the values of this field.
        return ["uuid", "id", "created", "modified"]

    @classmethod
    def hidden_fields(cls) -> list[str]:
        return ["uuid"]

    @classmethod
    def noninheritable_fields(cls) -> list[str]:
        return ["uuid", "modified", "deleted"]

    @classmethod
    def immutable_fields(cls) -> list[str]:
        # fields that can't be updated after object has been created
        return ["name"]

    @classmethod
    def urn_namespace(cls) -> str:
        model_class = cls.model_class()
        return model_class.__module__.split(".")[0]

    @classmethod
    def entity_type(cls) -> str:
        model_class = cls.model_class()
        return camel_to_snake(model_class.__name__)

    @classmethod
    def get_state_class(cls) -> type[BaseState] | None:
        """Returns the registered state class for this service and its bases."""
        for base in cls.__mro__:
            if (
                "_state_class" in base.__dict__
                and base.__dict__["_state_class"] is not None
            ):
                return base.__dict__["_state_class"]
        return None

    @classmethod
    def with_state(cls):
        """Decorator to register a state class on the service."""

        def decorator(state_cls: type[BaseState]):
            cls._state_class = state_cls
            return state_cls

        return decorator

    @classmethod
    def get_actions(cls) -> dict[str, type[BaseAction]]:
        """Returns all registered actions for this class and its bases."""
        actions = {}
        for base in reversed(cls.__mro__):
            if "_actions" in base.__dict__ and isinstance(
                base.__dict__["_actions"], dict
            ):
                actions.update(base.__dict__["_actions"])
        return actions

    @classmethod
    def register_action(cls, name: str):
        """Decorator to register a new action on the service."""

        def decorator(cls_func):
            if "_actions" not in cls.__dict__:
                cls._actions = {}
            if name in cls._actions:
                raise ValueError(
                    f"Action '{name}' is already registered on {cls.__name__}"
                )
            cls._actions[name] = cls_func
            return cls_func

        return decorator

    @classmethod
    def get_custom_views(cls) -> list[dict]:
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
    def get_widgets(cls) -> Dict[str, Any]:
        """
        Infer widgets from model fields (relationships and enums).
        """
        widgets = {}
        model_class = cls.model_class()

        for name, field in model_class.model_fields.items():
            # Default metadata
            field_metadata = {
                "order": 100 + list(model_class.model_fields.keys()).index(name),
                "column_span": 2,
            }

            # Handle Relationships
            if hasattr(field, "json_schema_extra") and field.json_schema_extra:
                # This might not be the best way to detect relationship if not using Relationship()
                pass

            # Check for foreign keys in FieldInfo
            if (
                hasattr(field, "foreign_key")
                and field.foreign_key
                and isinstance(field.foreign_key, str)
            ):
                table_name = field.foreign_key.split(".")[0]
                if table_name in Service._registry:
                    target_svc = Service._registry[table_name]
                    field_metadata.update(
                        {
                            "type": "relationship",
                            "endpoint": f"/api/v1{target_svc.service_path()}",
                            "field": "id",
                        }
                    )

            # Handle Enums
            annotation = field.annotation
            # Handle Optional[Enum]
            if hasattr(annotation, "__origin__") and annotation.__origin__ is Union:
                args = annotation.__args__
                for arg in args:
                    if (
                        isinstance(arg, type)
                        and issubclass(arg, enum.Enum)
                        and arg is not type(None)
                    ):
                        annotation = arg
                        break

            if isinstance(annotation, type) and issubclass(annotation, enum.Enum):
                options = []
                for item in annotation:
                    label = item.value.replace("-", " ").replace("_", " ").title()
                    options.append({"value": item.value, "label": label})
                field_metadata.update(
                    {
                        "type": "select",
                        "options": options,
                    }
                )

            # Preferred Defaults
            if name == "project_id":
                field_metadata.update({"order": 0, "column_span": 1})
            elif name == "name":
                field_metadata.update({"order": 1, "column_span": 1})
            elif name == "title":
                field_metadata.update({"order": 2, "column_span": 2})
            elif name == "description":
                field_metadata.update({"order": 3, "column_span": 2})

            # Ensure 'type' is present if we are adding it to widgets
            if name in ["project_id", "name", "title", "description"]:
                if "type" not in field_metadata:
                    field_metadata["type"] = "text"
                widgets[name] = field_metadata
            elif "type" in field_metadata:
                widgets[name] = field_metadata

        # Merge with manual widgets
        manual_widgets = cls.widgets()
        for name, meta in manual_widgets.items():
            if name in widgets:
                widgets[name].update(meta)
            else:
                # If not in inferred widgets, we still need basic order/span if missing
                if "order" not in meta:
                    meta["order"] = 999
                if "column_span" not in meta:
                    meta["column_span"] = 2
                widgets[name] = meta

        # Post-process for labels, especially relationship fields ending with ID
        for name, meta in widgets.items():
            if meta.get("type") == "relationship" and "label" not in meta:
                label_text = name
                for suffix in ["_ids", "_id", "ids", "id"]:
                    if label_text.lower().endswith(suffix):
                        label_text = label_text[: -len(suffix)]
                        break
                label_text = label_text.replace("_", " ").strip()
                label_text = label_text.title()
                # Fix common acronyms
                label_text = (
                    label_text.replace("K8s", "K8S")
                    .replace("Db", "DB")
                    .replace("Url", "URL")
                )
                meta["label"] = label_text

        return widgets

    @classmethod
    def widgets(cls) -> Dict[str, Any]:
        """
        Override this to manually define or override widgets.
        """
        return {}

    def __init__(self, request: fastapi.Request, session: AsyncSession):
        self.request = request
        self.session = session

    def urn(self, model: NamedBase):
        namespace = self.urn_namespace()
        entity_type = self.entity_type()
        urn = f"urn:{namespace}:{entity_type}:uuid:{model.uuid}"
        return urn

    def get_project_id(self) -> int | None:
        """Get project ID from request header."""
        project_id = self.request.headers.get("X-Project-ID")
        if project_id:
            try:
                return int(project_id)
            except ValueError:
                pass
        return None

    async def create(self, data: NamedBase) -> S:
        model_class = self.__class__.model_class()
        data = await self.validate_data(data)
        parsed_data = data.model_dump(exclude=self.internal_fields())
        if not parsed_data:
            raise ValueError("No data provided")

        # Inject project_id if available and model supports it
        project_id = self.get_project_id()
        if project_id and hasattr(model_class, "project_id"):
            parsed_data["project_id"] = project_id

        model = model_class(**parsed_data)

        # Execute before_create hooks
        for hook in self._before_create_hooks:
            await hook(self, model)

        self.session.add(model)
        try:
            await self.session.flush()
        except saexc.IntegrityError as e:
            self._handle_integrity_error(e)
        await self.session.refresh(model)

        # Execute after_create hooks
        for hook in self._after_create_hooks:
            await hook(self, model)

        return model

    async def get(self, model_id: int) -> S:
        model_class = self.__class__.model_class()
        filter = model_class.id == model_id

        # Filter by project_id if available and model supports it
        project_id = self.get_project_id()
        if project_id and hasattr(model_class, "project_id"):
            filter &= model_class.project_id == project_id

        result = await self.session.exec(select(model_class).where(filter))
        obj = result.first()
        if not obj:
            raise NotFoundError(message=f"{model_class.__name__}({model_id})")
        return obj

    async def all(self) -> list[S]:
        model_class = self.__class__.model_class()
        stmt = select(model_class).order_by(model_class.id.asc())

        # Filter by project_id if available and model supports it
        project_id = self.get_project_id()
        if project_id and hasattr(model_class, "project_id"):
            stmt = stmt.where(model_class.project_id == project_id)

        models = await self.session.exec(stmt)
        return list(models.all())

    async def update(self, model_id: int, data: NamedBase) -> S:

        data = await self.validate_data(data)
        model = await self.get(model_id)  # get() already filters by project_id

        # Execute before_update hooks
        for hook in self._before_update_hooks:
            await hook(self, model, data)

        # Check for immutable fields
        immutable_fields = self.immutable_fields()
        if immutable_fields:
            update_data = data.model_dump(exclude_unset=True)
            for field in immutable_fields:
                if field in update_data:
                    new_val = update_data[field]
                    old_val = getattr(model, field)
                    if new_val != old_val:
                        raise ModelValidationError(
                            message=f"Field '{field}' is immutable"
                        )

        model_class = self.model_class()
        newdata = model.model_dump(exclude=self.noninheritable_fields())
        newdata.update(data.model_dump(exclude_unset=True))
        newdata["modified"] = ts_now()
        model.sqlmodel_update(newdata)
        try:
            await self.session.flush()
        except saexc.IntegrityError as e:
            self._handle_integrity_error(e)
        await self.session.refresh(model)

        # Execute after_update hooks
        for hook in self._after_update_hooks:
            await hook(self, model)

        return model

    async def delete(self, model_id: int):
        model = await self.get(model_id)  # get() already filters by project_id

        # Execute before_delete hooks
        for hook in self._before_delete_hooks:
            await hook(self, model)

        await self.session.delete(model)
        await self.session.flush()

        # Execute after_delete hooks
        for hook in self._after_delete_hooks:
            await hook(self, model)

    async def search(self, *, offset=0, limit=10, sa_filters=None, **filters):
        model_class = self.__class__.model_class()
        filter = sa.literal(1) == 1
        if sa_filters and filters:
            raise ValueError("Cannot use both sa_filters and filters")
        for field_name, value in filters.items():
            filter &= getattr(model_class, field_name) == value
        if sa_filters:
            filter &= sa_filters

        # Filter by project_id if available and model supports it
        project_id = self.get_project_id()
        if project_id and hasattr(model_class, "project_id"):
            filter &= model_class.project_id == project_id

        models = await self.session.exec(
            select(model_class)
            .where(filter)
            .order_by(model_class.id.asc())
            .offset(offset)
            .limit(limit)
        )
        return models

    async def validate_data(self, data: NamedBase) -> NamedBase:
        """
        Validate incoming data before create or update.
        Specifically, check if relationship fields point to records in the same project.
        """
        project_id = self.get_project_id()
        model_class = self.model_class()

        # Only apply scope validation if this model is project-scoped
        if project_id and hasattr(model_class, "project_id"):
            for field_name, field_info in model_class.model_fields.items():
                # Check if this is a foreign key
                if (
                    hasattr(field_info, "foreign_key")
                    and field_info.foreign_key
                    and isinstance(field_info.foreign_key, str)
                ):
                    # Retrieve the value from the incoming data
                    val = getattr(data, field_name, None)
                    if val is None:
                        continue

                    table_name = field_info.foreign_key.split(".")[0]
                    if table_name in Service._registry:
                        target_svc_cls = Service._registry[table_name]
                        target_model_class = target_svc_cls.model_class()

                        # Validate if the target model is project-scoped by checking its MRO
                        # to avoid circular imports.
                        is_scoped = any(
                            base.__name__
                            in ("ProjectScopedBase", "ProjectScopedNamedBase")
                            for base in target_model_class.__mro__
                        )

                        if is_scoped:
                            target_svc = await target_svc_cls.get_service(
                                self.request, self.session
                            )
                            try:
                                # target_svc.get(val) will naturally filter by project_id from headers
                                await target_svc.get(val)
                            except NotFoundError:
                                raise ModelValidationError(
                                    message=f"Referenced {target_model_class.__name__} (id={val}) in field '{field_name}' does not exist or belongs to another project"
                                )
        return data

    async def post_process_model(self, model: S) -> S:
        """
        Post-process model before returning it to the client.
        Default is identity. Override this to redact sensitive fields.
        """
        return model

    def _handle_integrity_error(self, e: saexc.IntegrityError):
        msg = str(e.orig)

        # Postgres (asyncpg) / SQLite generic handling
        if (
            "UNIQUE constraint failed" in msg
            or "UniqueViolationError" in msg
            or "duplicate key value" in msg
        ):
            # Try to extract the field/key name
            if "duplicate key value violates unique constraint" in msg:
                # Postgres style: ... violates unique constraint "..." Detail: Key (name)=(asd) already exists.
                match = re.search(r"Key \((.*?)\)=\(.*\) already exists", msg)
                if match:
                    field = match.group(1)
                    raise ModelValidationError(
                        message=f"Value for '{field}' already exists"
                    )

            parts = msg.split(":")
            if len(parts) > 1:
                field = parts[1].strip().split(".")[-1]
                raise ModelValidationError(
                    message=f"Value for '{field}' already exists"
                )
            raise ModelValidationError(message="Unique constraint failed")

        elif (
            "NOT NULL constraint failed" in msg
            or "NotNullViolationError" in msg
            or "violates not-null constraint" in msg
        ):
            if "violates not-null constraint" in msg:
                # Postgres style: null value in column "project_id" ... violates not-null constraint
                match = re.search(r'column "(.*?)"', msg)
                if match:
                    field = match.group(1)
                    raise ModelValidationError(message=f"Field '{field}' is required")

            parts = msg.split(":")
            if len(parts) > 1:
                field = parts[1].strip().split(".")[-1]
                raise ModelValidationError(message=f"Field '{field}' is required")
            raise ModelValidationError(message="Required field missing")

        elif (
            "FOREIGN KEY constraint failed" in msg
            or "ForeignKeyViolationError" in msg
            or "violates foreign key constraint" in msg
        ):
            raise ModelValidationError(message="Referenced record does not exist")

        # Fallback to a cleaner version of the raw message
        clean_msg = msg.split(":", 1)[-1].strip() if ":" in msg else msg
        raise ModelValidationError(message=clean_msg)

    @classmethod
    async def get_model(cls, request: fastapi.Request, db: AsyncSession, id: int) -> S:
        svc = await cls.get_service(request, db)
        return await svc.get(id)

    @classmethod
    async def get_service(cls, request: fastapi.Request, db: AsyncSession):
        return cls(request, db)

    @classmethod
    def router(cls) -> fastapi.APIRouter:
        if not getattr(cls, "_router", None):
            router = fastapi.APIRouter()
            cls.register_views(router, cls.service_path(), cls.model_path())
            cls._router = router
        return cls._router

    @classmethod
    def extra_dependencies(cls):
        return []

    @classmethod
    def path_tags(cls):
        return [cls.model_class().__name__]

    @classmethod
    def register_views(
        cls, router: fastapi.APIRouter, service_path: str, model_path: str
    ):
        """Register views for the service."""
        # Implement view registration logic here

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
                raise fastapi.HTTPException(
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
                    raise fastapi.HTTPException(
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
