from __future__ import annotations
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field, field_validator
from .models import JsonObject, Score10

Identifier = Annotated[str, Field(min_length=1, max_length=200)]
Performance = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]
FeedbackText = Annotated[str, Field(min_length=1, max_length=5000)]


class RequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class GenerateRequest(RequestModel):
    skill_id: Identifier
    params: JsonObject = Field(default_factory=dict)


class StartRequest(GenerateRequest):
    user_id: Identifier


class SubmitRequest(RequestModel):
    user_id: Identifier
    session_id: Identifier
    answer: str = Field(min_length=1, max_length=50000)


class EvaluateRequest(GenerateRequest):
    content: str = Field(min_length=1, max_length=50000)
    reference: str = Field(default="", max_length=40000)


class SkillCreate(RequestModel):
    name: str = Field(min_length=1, max_length=200)
    display_name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=10000)
    generate_prompt: str = Field(default="", max_length=20000)
    evaluate_prompt: str = Field(default="", max_length=20000)
    atomic_skills: list[Identifier] = Field(default_factory=list, max_length=50)
    default_params: JsonObject = Field(default_factory=dict)


class SkillPatch(RequestModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1, max_length=10000)
    generate_prompt: str | None = Field(default=None, max_length=20000)
    evaluate_prompt: str | None = Field(default=None, max_length=20000)
    enabled: bool | None = None
    atomic_skills: list[Identifier] | None = Field(default=None, max_length=50)
    default_params: JsonObject | None = None

    @field_validator("display_name", "description", "generate_prompt", "evaluate_prompt",
                     "enabled", "atomic_skills", "default_params")
    @classmethod
    def no_explicit_null(cls, value):
        if value is None:
            raise ValueError("Omit a field instead of setting it to null")
        return value


class AtomicCreate(RequestModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=10000)
    categories: list[str] = Field(default_factory=list, max_length=50)


class CustomSkillRequest(RequestModel):
    skill_name: str = Field(min_length=1, max_length=200)


class MasteryRequest(RequestModel):
    user_id: Identifier
    atomic_skill_id: Identifier
    performance: Performance
    timestamp: str | None = None


class AtomicScoreRequest(RequestModel):
    user_id: Identifier
    atomic_skill_id: Identifier
    score: Score10


class OptimizeRequest(RequestModel):
    user_id: Identifier
    atomic_skill_ids: list[Identifier] = Field(min_length=1, max_length=50)
    optimization_goal: str = Field(default="提升技能", min_length=1, max_length=2000)
