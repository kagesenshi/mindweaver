# SPDX-FileCopyrightText: Copyright © 2025 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from pydantic import BaseModel, Field, AnyUrl, ConfigDict
from typing import Generic, Any, Literal
from .hooks import T


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
