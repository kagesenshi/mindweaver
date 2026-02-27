# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import enum
from typing import Any, Dict, List, Union, Type
from pydantic import BaseModel
from ..util import redefine_model
from ..registry import SERVICE_REGISTRY
from ..model import NamedBase


class FormHandlerMixin:
    """
    Mixin for services that handle form generation and field metadata.
    """

    @classmethod
    def schema_class(cls) -> Type[NamedBase]:
        """
        This function provide schema class for use in forms. By default it will use model class.
        Override this if you need to use a different schema in forms
        """
        return cls.model_class()

    @classmethod
    def createmodel_class(cls) -> Type[BaseModel]:
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
    def updatemodel_class(cls) -> Type[BaseModel]:
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
    def internal_fields(cls) -> List[str]:
        # fields that are internal to the system , can be exposed to the user, but user should
        # not be able to set or change the values of this field.
        return ["uuid", "id", "created", "modified"]

    @classmethod
    def hidden_fields(cls) -> List[str]:
        return ["uuid"]

    @classmethod
    def noninheritable_fields(cls) -> List[str]:
        return ["uuid", "modified", "deleted"]

    @classmethod
    def immutable_fields(cls) -> List[str]:
        # fields that can't be updated after object has been created
        return ["name"]

    @classmethod
    def widgets(cls) -> Dict[str, Any]:
        """
        Override this to manually define or override widgets.
        """
        return {}

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

            # Check for foreign keys in FieldInfo
            if (
                hasattr(field, "foreign_key")
                and field.foreign_key
                and isinstance(field.foreign_key, str)
            ):
                table_name = field.foreign_key.split(".")[0]
                if table_name in SERVICE_REGISTRY:
                    target_svc = SERVICE_REGISTRY[table_name]
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
