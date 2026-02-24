# SPDX-FileCopyrightText: Copyright © 2025 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

from . import NamedBase, Base
from .base import ProjectScopedNamedBase, ProjectScopedService
from sqlalchemy import String
from sqlalchemy_utils import JSONType
from sqlmodel import Field, Relationship
from typing import Any, Optional, List


class EntityAttribute(Base, table=True):
    __tablename__ = "mw_entity_attribute"
    name: str = Field(index=True)
    data_type: str = Field(default="string")  # string, number, boolean, date, etc.
    required: bool = Field(default=False)

    entity_type_id: Optional[int] = Field(default=None, foreign_key="mw_entity_type.id")
    entity_type: Optional["EntityType"] = Relationship(back_populates="attributes")


class RelationshipAttribute(Base, table=True):
    __tablename__ = "mw_relationship_attribute"
    name: str = Field(index=True)
    data_type: str = Field(default="string")
    required: bool = Field(default=False)

    relationship_type_id: Optional[int] = Field(
        default=None, foreign_key="mw_relationship_type.id"
    )
    relationship_type: Optional["RelationshipType"] = Relationship(
        back_populates="attributes"
    )


class EntityType(Base, table=True):
    __tablename__ = "mw_entity_type"
    name: str = Field(index=True)
    description: str = Field(default="", sa_type=String())

    ontology_id: Optional[int] = Field(default=None, foreign_key="mw_ontology.id")
    ontology: Optional["Ontology"] = Relationship(back_populates="entity_types")

    attributes: List[EntityAttribute] = Relationship(
        back_populates="entity_type",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class RelationshipType(Base, table=True):
    __tablename__ = "mw_relationship_type"
    name: str = Field(index=True)
    description: str = Field(default="", sa_type=String())
    source_entity_type: str = Field(default="")  # Name of source entity type
    target_entity_type: str = Field(default="")  # Name of target entity type

    ontology_id: Optional[int] = Field(default=None, foreign_key="mw_ontology.id")
    ontology: Optional["Ontology"] = Relationship(back_populates="relationship_types")

    attributes: List[RelationshipAttribute] = Relationship(
        back_populates="relationship_type",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class Ontology(ProjectScopedNamedBase, table=True):
    __tablename__ = "mw_ontology"
    description: str = Field(default="", sa_type=String())

    entity_types: List[EntityType] = Relationship(
        back_populates="ontology",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    relationship_types: List[RelationshipType] = Relationship(
        back_populates="ontology",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class OntologyService(ProjectScopedService[Ontology]):
    @classmethod
    def model_class(cls) -> type[Ontology]:
        return Ontology

    @classmethod
    def service_path(cls) -> str:
        return "/ontologies"


router = OntologyService.router()
