"""Explicit response contracts, preserving the existing frontend's JSON shapes."""
from __future__ import annotations
from typing import Generic, Literal, TypeVar
from pydantic import BaseModel
from ..domain.models import AtomicSkill, Evaluation, PracticeContent, PracticeRecord, SessionHistory, Skill

T = TypeVar("T")


class Success(BaseModel, Generic[T]):
    error: Literal[False] = False
    msg: str = "成功"
    data: T


class ErrorResponse(BaseModel):
    error: Literal[True] = True
    code: str
    msg: str
    detail: str
    data: None = None


class SkillsResponse(BaseModel):
    skills: list[Skill]


class SkillResponse(BaseModel):
    skill: Skill


class CustomSkillResponse(SkillResponse):
    message: str = "技能创建成功"


class AtomsResponse(BaseModel):
    atomic_skills: list[AtomicSkill]


class AtomResponse(BaseModel):
    atomic_skill: AtomicSkill


class MessageResponse(BaseModel):
    message: str


class ContentResponse(BaseModel):
    content: PracticeContent


class EvaluationResponse(BaseModel):
    evaluation: Evaluation


class HistoryResponse(BaseModel):
    history: list[SessionHistory]


class RecordsResponse(BaseModel):
    records: list[PracticeRecord]


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    database: Literal["sqlite"] = "sqlite"
    schema_version: int
    ai_configured: bool
    ai_api_style: str
    ai_model: str
    mode: Literal["local_single_user"] = "local_single_user"
