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


from typing import Any, Optional, Union


def redefine_model(
    name,
    Model: type[BaseModel],
    *,
    exclude: Optional[list[str]] = None,
    optional: Optional[list[str]] = None,
) -> type[BaseModel]:
    """
    Creates a new Pydantic model by redefining an existing one.

    Args:
        name: The name of the new model class.
        Model: The source Pydantic model to base the new one on.
        exclude: A list of field names to remove from the new model.
        optional: A list of field names to make optional in the new model.
            If the list contains the string "__ALL__", all fields in the 
            redefined model will be made optional and default to None.

    Returns:
        A new Pydantic model class with the requested modifications.
    """
    exclude = exclude or []
    optional = optional or []

    make_all_optional = "__ALL__" in optional
    optional_fields = optional if not make_all_optional else []

    from pydantic_core import PydanticUndefined
    from pydantic import Field

    fields = {}
    for fname, field in Model.model_fields.items():
        if fname in exclude:
            continue

        annotation = field.annotation
        
        # Determine the new default/factory
        if make_all_optional or fname in optional_fields:
            # Make it optional for Update model
            is_already_optional = (
                hasattr(annotation, "__origin__")
                and annotation.__origin__ is Union
                and type(None) in annotation.__args__
            )
            if not is_already_optional:
                annotation = Optional[annotation]
            
            new_field = Field(default=None)
        else:
            # Preserve existing default/factory for Create model
            new_field = Field(
                default=field.default,
                default_factory=field.default_factory
            )

        fields[fname] = (annotation, new_field)

    model = create_model(name, __base__=BaseModel, **fields)
    return model


def format_k8s_resource(value: float, unit: str = "") -> str:
    """
    Converts a float value to a Kubernetes-style resource number.
    - If value is an integer (e.g., 1.0), returns "1" + unit.
    - If unit is empty (CPU):
        - If float, returns milli-units (e.g., 0.5 -> "500m").
    - If unit is binary (Ki, Mi, Gi, Ti, Pi, Ei):
        - If float, multiplies by 1024 and moves to next smaller unit.
    - If unit is SI (k, M, G, T, P, E):
        - If float, multiplies by 1000 and moves to next smaller unit.
    """
    if value.is_integer():
        return f"{int(value)}{unit}"

    # Binary units mapping
    binary_units = ["Ki", "Mi", "Gi", "Ti", "Pi", "Ei"]
    # SI units mapping
    si_units = ["k", "M", "G", "T", "P", "E"]

    if unit in binary_units:
        idx = binary_units.index(unit)
        new_value = int(value * 1024)
        if idx == 0:
            return str(new_value)
        return f"{new_value}{binary_units[idx-1]}"

    if unit in si_units:
        idx = si_units.index(unit)
        new_value = int(value * 1000)
        if idx == 0:
            return str(new_value)
        return f"{new_value}{si_units[idx-1]}"

    if not unit:
        # Assume CPU milli-units
        return f"{int(value * 1000)}m"

    # Fallback to string representation if unit is unknown but it's a float
    return str(value) + unit


import secrets
import string


def generate_password(length: int = 18, uri_safe: bool = True) -> str:
    """
    Generate a random password that meets the following requirements:
    - at least 1 lowercase
    - at least 1 uppercase
    - at least 1 number
    - at least 1 symbol
    - minimum length 18 characters
    """
    if length < 4:
        raise ValueError(
            "Password length must be at least 4 to include all required character types"
        )

    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits

    if uri_safe:
        # URI-safe unreserved characters as per RFC 3986: ALPHA / DIGIT / "-" / "." / "_" / "~"
        # We use a subset of safe symbols
        symbols = "-_.~"
    else:
        symbols = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    all_chars = lowercase + uppercase + digits + symbols

    # Ensure at least one of each required type
    password = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(symbols),
    ]

    # Fill the rest of the length
    password += [secrets.choice(all_chars) for _ in range(length - 4)]

    # Shuffle to avoid predictable pattern
    password_list = list(password)
    secrets.SystemRandom().shuffle(password_list)

    return "".join(password_list)
