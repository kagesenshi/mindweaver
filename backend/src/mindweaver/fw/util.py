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
