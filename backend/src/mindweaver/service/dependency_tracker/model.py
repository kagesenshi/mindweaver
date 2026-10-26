# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from sqlmodel import Field
from sqlalchemy import String
from mindweaver.fw.model import Base


class DependencyTracker(Base, table=True):
    """
    Model for tracking service dependency chains across platform and infrastructure services.
    """
    __tablename__ = "mw_dependency_tracker"

    service_uuid: str = Field(
        sa_type=String(length=64),
        index=True,
    )
    service_name: str = Field(
        sa_type=String(length=128),
        index=True,
    )
    service_type: str = Field(
        sa_type=String(length=64),
        index=True,
    )
    dependency_uuid: str = Field(
        sa_type=String(length=64),
        index=True,
    )
    dependency_name: str = Field(
        sa_type=String(length=128),
        index=True,
    )
    dependency_type: str = Field(
        sa_type=String(length=64),
        index=True,
    )
    relationship: str = Field(
        sa_type=String(length=64),
        index=True,
    )

    @property
    def name(self) -> str:
        """Name representation of the dependency entry."""
        return f"{self.service_name}->{self.dependency_name}"

    @property
    def relationship_type(self) -> str:
        """Alias for relationship field."""
        return self.relationship

    @relationship_type.setter
    def relationship_type(self, val: str):
        """Set relationship field via alias."""
        self.relationship = val

    @property
    def target_uuid(self) -> str:
        """Alias for dependency_uuid."""
        return self.dependency_uuid

    @target_uuid.setter
    def target_uuid(self, val: str):
        """Set dependency_uuid via alias."""
        self.dependency_uuid = val

    @property
    def target_name(self) -> str:
        """Alias for dependency_name."""
        return self.dependency_name

    @target_name.setter
    def target_name(self, val: str):
        """Set dependency_name via alias."""
        self.dependency_name = val

    @property
    def target_type(self) -> str:
        """Alias for dependency_type."""
        return self.dependency_type

    @target_type.setter
    def target_type(self, val: str):
        """Set dependency_type via alias."""
        self.dependency_type = val

    @property
    def source_uuid(self) -> str:
        """Alias for service_uuid."""
        return self.service_uuid

    @source_uuid.setter
    def source_uuid(self, val: str):
        """Set service_uuid via alias."""
        self.service_uuid = val

    @property
    def source_name(self) -> str:
        """Alias for service_name."""
        return self.service_name

    @source_name.setter
    def source_name(self, val: str):
        """Set service_name via alias."""
        self.service_name = val

    @property
    def source_type(self) -> str:
        """Alias for service_type."""
        return self.service_type

    @source_type.setter
    def source_type(self, val: str):
        """Set service_type via alias."""
        self.service_type = val
