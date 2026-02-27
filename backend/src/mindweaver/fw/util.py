# SPDX-FileCopyrightText: Copyright © 2025 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import re
from typing import Any
from pydantic import BaseModel, create_model


def camel_to_snake(name):
    # Insert underscores before uppercase letters that follow lowercase letters or digits
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    # Insert underscores before uppercase letters that follow lowercase letters
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def redefine_model(name, Model: type[BaseModel], *, exclude=None) -> type[BaseModel]:
    """
    This function provide a Pydantic model based on schema class,
    with specified fields removed.
    """
    exclude = exclude or []

    fields = {
        fname: (field.annotation, field)
        for fname, field in Model.model_fields.items()
        if fname not in exclude
    }

    model = create_model(name, **fields)
    return model
