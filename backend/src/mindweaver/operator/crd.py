from pydantic import BaseModel, Field
from typing import Literal

Neo4jEdition = Literal["community", "enterprise"]


class Neo4jConfiguration(BaseModel):
    edition: Neo4jEdition = "community"
    config: dict[str, str] = Field(default_factory=dict)
    additionalJvmArguments: list[str] = Field(default_factory=list)


class GraphInfrastructure(BaseModel):

    neo4jConfig: Neo4jConfiguration = Neo4jConfiguration()
    neo4jPasswordSecret: str
