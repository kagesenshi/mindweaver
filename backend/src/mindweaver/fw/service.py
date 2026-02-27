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
from .hooks import (
    before_create,
    after_create,
    before_update,
    after_update,
    before_delete,
    after_delete,
    _sort_hooks,
    S,
    T,
)
from .mixins.secrethandler import SecretHandlerMixin
from .mixins.hashinghandler import HashingHandlerMixin
from .mixins.actionhandler import ActionHandlerMixin
from .mixins.formhandler import FormHandlerMixin
from .mixins.serviceview import ServiceViewMixin
from .mixins.servicestate import ServiceStateMixin
from .registry import SERVICE_REGISTRY
from .schema import (
    ErrorDetail,
    ValidationErrorDetail,
    Error,
    BaseResult,
    Result,
    FormSchema,
    FormResult,
    PaginationMeta,
    ListResult,
)
from .util import camel_to_snake, redefine_model

import enum
import abc
import jinja2 as j2
from .exc import NotFoundError
import re
import asyncio
from fastapi import HTTPException
from typing import Generic, Any, Annotated, List, Dict
from mindweaver.fw.action import ActionRequest, BaseAction
from mindweaver.fw.state import BaseState
from mindweaver.crypto import encrypt_password, EncryptionError


class Service(
    Generic[S],
    SecretHandlerMixin,
    HashingHandlerMixin,
    ActionHandlerMixin,
    FormHandlerMixin,
    ServiceViewMixin,
    ServiceStateMixin,
    abc.ABC,
):
    _before_create_hooks: list[Any] = []
    _after_create_hooks: list[Any] = []
    _before_update_hooks: list[Any] = []
    _after_update_hooks: list[Any] = []
    _before_delete_hooks: list[Any] = []
    _after_delete_hooks: list[Any] = []

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
                    SERVICE_REGISTRY[model_class.__tablename__] = cls

    @classmethod
    @abc.abstractmethod
    def model_class(cls) -> type[S]:
        """
        Provide SQLModel class for this service to interact with
        """
        raise NotImplementedError("model_class must be implemented")

    @classmethod
    def service_path(cls) -> str:
        return f"/{cls.entity_type()}s"

    @classmethod
    def model_path(cls) -> str:
        return f"{cls.service_path()}/{{id}}"

    @classmethod
    def urn_namespace(cls) -> str:
        model_class = cls.model_class()
        return model_class.__module__.split(".")[0]

    @classmethod
    def entity_type(cls) -> str:
        model_class = cls.model_class()
        return camel_to_snake(model_class.__name__)

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
                    if table_name in SERVICE_REGISTRY:
                        target_svc_cls = SERVICE_REGISTRY[table_name]
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
