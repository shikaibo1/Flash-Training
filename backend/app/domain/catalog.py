"""Catalog definitions and graph transport independent of learner progress."""
from typing import Literal
from pydantic import Field
from .models import AtomicSkill, Model, Skill


class Role(Model):
    role_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str


class KnowledgeConcept(Model):
    knowledge_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str
    course: str


class GraphNode(Model):
    id: str
    type: Literal['role', 'task', 'atom', 'knowledge']
    label: str
    description: str
    reference_id: str


class GraphEdge(Model):
    source: str
    target: str
    relation: Literal['requires', 'supports', 'prerequisite', 'contains']


class GraphResponse(Model):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    atoms: list[AtomicSkill]
    tasks: list[Skill]
    roles: list[Role]
    knowledge: list[KnowledgeConcept]
