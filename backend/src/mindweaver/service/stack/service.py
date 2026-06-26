# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from typing import Any
from mindweaver.fw.service import Service
from .model import Stack


class StackService(Service[Stack]):
    """Service for managing platform deployment stacks."""

    @classmethod
    def model_class(cls) -> type[Stack]:
        return Stack

    @classmethod
    def widgets(cls) -> dict[str, Any]:
        return {
            "version": {
                "order": 3,
                "label": "Stack Version",
                "placeholder": "e.g. v1.0.0",
            },
            "configuration": {
                "order": 4,
                "type": "json",
                "label": "Stack Configuration",
            },
        }
