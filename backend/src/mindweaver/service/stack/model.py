# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from typing import Any
from sqlmodel import Field
from sqlalchemy_utils import JSONType
from mindweaver.fw.model import NamedBase


class Stack(NamedBase, table=True):
    __tablename__ = "mw_stack"

    version: str = Field(sa_column_kwargs={"unique": True})
    configuration: dict[str, Any] = Field(default_factory=dict, sa_type=JSONType())

    def get_image_for_component(self, component_name: str, image_key: str = "main") -> tuple[str | None, str | None]:
        """
        Returns (image_url, image_tag) for the given component and image key.
        """
        components = self.configuration.get("components", {})
        comp = components.get(component_name)
        if not comp:
            return None, None
        images = comp.get("images", {})
        img_info = images.get(image_key)
        if not img_info:
            return None, None
        return img_info.get("image"), img_info.get("tag")

    def get_custom_config(self, component_name: str) -> dict[str, Any]:
        """
        Returns custom configuration dict for the given component.
        """
        components = self.configuration.get("components", {})
        comp = components.get(component_name)
        if not comp:
            return {}
        return comp.get("custom_config", {})

    def get_chart_version_for_component(self, component_name: str) -> str | None:
        """
        Returns the chart version for the given component.
        """
        components = self.configuration.get("components", {})
        comp = components.get(component_name)
        if not comp:
            return None
        return comp.get("chart_version")

