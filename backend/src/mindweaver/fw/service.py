from pydantic import BaseModel, Field, create_model, AnyUrl
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
from typing import Generic, TypeVar, Any, Literal, Annotated, Union, List, Dict

T = TypeVar("T", bound=NamedBase)
S = TypeVar("S", bound=SQLModel)


class ErrorDetail(BaseModel):
    loc: list[Any] = Field(default_factory=list)
    msg: str | None = None
    type: str | None = None


STATUSES = Literal["success", "error"]


class BaseResult(BaseModel):
    detail: list[ErrorDetail] | None = None
    status: STATUSES = "success"


class Result(BaseResult, Generic[T]):
    record: T


class PaginationMeta(BaseModel):
    page_num: int | None = None
    page_size: int | None = None
    next_page: AnyUrl | None = None
    prev_page: AnyUrl | None = None


class ListResult(BaseResult, Generic[T]):
    records: list[T] | None = None
    meta: PaginationMeta | None = None


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
            if not issubclass(base, Service):
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
            try:
                model_class = cls.model_class()
                if hasattr(model_class, "__tablename__"):
                    Service._registry[model_class.__tablename__] = cls
            except (NotImplementedError, AttributeError):
                pass

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
    def get_widgets(cls) -> Dict[str, Any]:
        """
        Infer widgets from model fields (relationships and enums).
        """
        widgets = {}
        model_class = cls.model_class()

        for name, field in model_class.model_fields.items():
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
                    widgets[name] = {
                        "type": "relationship",
                        "endpoint": f"/api/v1{target_svc.service_path()}",
                        "field": "id",
                    }

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
                widgets[name] = {
                    "type": "select",
                    "options": options,
                }

        # Merge with manual widgets
        widgets.update(cls.widgets())
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

        result = await self.session.execute(select(model_class).where(filter))
        obj = result.first()
        if not obj:
            raise NotFoundError(message=f"{model_class.__name__}({model_id})")
        return obj[0]

    async def all(self) -> list[S]:
        model_class = self.__class__.model_class()
        stmt = select(model_class)

        # Filter by project_id if available and model supports it
        project_id = self.get_project_id()
        if project_id and hasattr(model_class, "project_id"):
            stmt = stmt.where(model_class.project_id == project_id)

        models = await self.session.execute(stmt)
        return [i[0] for i in models.all()]

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

        models = await self.session.execute(
            select(model_class).where(filter).offset(offset).limit(limit)
        )
        return models

    async def validate_data(self, data: NamedBase) -> NamedBase:
        # raise error if fail
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
                import re

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
                import re

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
            return {"records": await svc.all()}

        @router.get(
            f"{service_path}/+create-form",
            operation_id=f"mw-create-form-{entity_type}",
            dependencies=extra_deps,
            tags=path_tags,
        )
        async def get_create_form() -> dict:
            return {
                "jsonschema": CreateModel.model_json_schema(),
                "widgets": cls.get_widgets(),
                "immutable_fields": cls.immutable_fields(),
                "internal_fields": cls.internal_fields(),
            }

        if UpdateModel.model_fields:

            @router.get(
                f"{service_path}/+edit-form",
                operation_id=f"mw-edit-form-{entity_type}",
                dependencies=extra_deps,
                tags=path_tags,
            )
            async def get_edit_form() -> dict:
                return {
                    "jsonschema": UpdateModel.model_json_schema(),
                    "widgets": cls.get_widgets(),
                    "immutable_fields": cls.immutable_fields(),
                    "internal_fields": cls.internal_fields(),
                }

        @router.post(
            service_path,
            operation_id=f"mw-create-{entity_type}",
            dependencies=cls.extra_dependencies(),
            tags=path_tags,
        )
        async def create(svc: Annotated[cls, Depends(cls.get_service)], data: CreateModel) -> Result[model_class]:  # type: ignore
            created_model = await svc.create(data)
            return {"record": created_model}

        @router.get(
            model_path,
            operation_id=f"mw-get-{entity_type}",
            dependencies=cls.extra_dependencies(),
            tags=path_tags,
        )
        async def get(model: Annotated[model_class, Depends(cls.get_model)]) -> Result[model_class]:  # type: ignore
            return {"record": model}

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
                return {"record": updated_model}

        @router.delete(
            model_path,
            operation_id=f"mw-delete-{entity_type}",
            dependencies=cls.extra_dependencies(),
            tags=path_tags,
        )
        async def delete(
            svc: Annotated[cls, Depends(cls.get_service)],  # type: ignore
            model: Annotated[model_class, Depends(cls.get_model)],
        ) -> BaseResult:  # type: ignore
            await svc.delete(model.id)
            return {"status": "success"}
