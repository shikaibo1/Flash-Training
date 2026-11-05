from __future__ import annotations
from typing import Annotated
from fastapi import Depends, Request
from ..application.skills import SkillService
from ..application.practice import PracticeService
from ..application.progress import ProgressService
from ..application.records import RecordService


def skill_service(request: Request) -> SkillService:
    return request.app.state.services.skills


def practice_service(request: Request) -> PracticeService:
    return request.app.state.services.practice


def progress_service(request: Request) -> ProgressService:
    return request.app.state.services.progress


def record_service(request: Request) -> RecordService:
    return request.app.state.services.records


Skills = Annotated[SkillService, Depends(skill_service)]
Practice = Annotated[PracticeService, Depends(practice_service)]
Progress = Annotated[ProgressService, Depends(progress_service)]
Records = Annotated[RecordService, Depends(record_service)]
