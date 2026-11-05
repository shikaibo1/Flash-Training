from __future__ import annotations
from fastapi import APIRouter
from ..domain.commands import SkillCreate, SkillPatch, AtomicCreate, CustomSkillRequest
from ..domain.models import SkillMapping
from .dependencies import Skills, Progress
from .responses import (SkillsResponse, SkillResponse, CustomSkillResponse, AtomsResponse,
                        AtomResponse, MessageResponse)

router = APIRouter(prefix="/api", tags=["skills"])


@router.get("/skills", response_model=SkillsResponse)
@router.get("/v1/practice/skills", response_model=SkillsResponse)
def skills(svc: Skills) -> SkillsResponse:
    return SkillsResponse(skills=svc.list(enabled_only=True))


@router.get("/v1/skills", response_model=SkillsResponse)
def all_skills(svc: Skills) -> SkillsResponse:
    return SkillsResponse(skills=svc.list())


@router.get("/v1/skills/{skill_id}", response_model=SkillResponse)
def skill(skill_id: str, svc: Skills) -> SkillResponse:
    return SkillResponse(skill=svc.get(skill_id))


@router.post("/v1/skills", status_code=201, response_model=SkillResponse)
@router.post("/v1/practice/skills/custom", status_code=201, response_model=SkillResponse)
def create_skill(body: SkillCreate, svc: Skills) -> SkillResponse:
    return SkillResponse(skill=svc.create(body))


@router.patch("/v1/skills/{skill_id}", response_model=SkillResponse)
def update_skill(skill_id: str, body: SkillPatch, svc: Skills) -> SkillResponse:
    return SkillResponse(skill=svc.update(skill_id, body))


@router.delete("/skills/{skill_id}", response_model=MessageResponse)
@router.delete("/v1/skills/{skill_id}", response_model=MessageResponse)
def delete_skill(skill_id: str, svc: Skills) -> MessageResponse:
    svc.delete(skill_id)
    return MessageResponse(message="技能已移除，历史练习仍保留")


@router.post("/skills/custom", status_code=201, response_model=CustomSkillResponse)
@router.post("/v1/practice/create_custom_skill", status_code=201, response_model=CustomSkillResponse)
def custom_skill(body: CustomSkillRequest, svc: Skills) -> CustomSkillResponse:
    return CustomSkillResponse(skill=svc.custom(body.skill_name))


@router.get("/v1/atomic/skills", response_model=AtomsResponse)
def atoms(svc: Skills) -> AtomsResponse:
    return AtomsResponse(atomic_skills=svc.atoms())


@router.post("/v1/atomic/skills", status_code=201, response_model=AtomResponse)
def create_atom(body: AtomicCreate, svc: Skills) -> AtomResponse:
    return AtomResponse(atomic_skill=svc.create_atom(body))


@router.get("/v1/atomic/skills/{skill_id}/mapping", response_model=SkillMapping)
def mapping(skill_id: str, svc: Progress, user_id: str = "default_user") -> SkillMapping:
    return svc.mapping(user_id, skill_id)
