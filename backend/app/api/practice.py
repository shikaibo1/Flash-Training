from __future__ import annotations
from typing import NoReturn
from fastapi import APIRouter
from ..domain.commands import StartRequest, SubmitRequest, GenerateRequest, EvaluateRequest
from ..domain.models import PracticeContent, SessionStarted, SessionDetails, Submission, SkillProgress, UserProfile
from ..errors import AppError
from .dependencies import Practice, Records
from .responses import (Success, ErrorResponse, ContentResponse, EvaluationResponse,
                        HistoryResponse, RecordsResponse, MessageResponse)

router = APIRouter(prefix="/api", tags=["practice"])


@router.post("/v1/practice/start", status_code=201, response_model=Success[SessionStarted])
def start(body: StartRequest, svc: Practice) -> Success[SessionStarted]:
    return Success(data=svc.start(body.user_id, body.skill_id, body.params))


@router.get("/v1/practice/sessions/{session_id}", response_model=Success[SessionDetails], response_model_exclude_unset=True)
def get_session(session_id: str, user_id: str, svc: Practice) -> Success[SessionDetails]:
    return Success(error=False, msg="成功", data=svc.session_details(user_id, session_id))


@router.post("/v1/practice/submit", response_model=Success[Submission])
def submit(body: SubmitRequest, svc: Practice) -> Success[Submission]:
    return Success(data=svc.submit(body.user_id, body.session_id, body.answer))


@router.post("/v1/practice/generate", response_model=ContentResponse)
def generate(body: GenerateRequest, svc: Practice) -> ContentResponse:
    return ContentResponse(content=svc.generate(body.skill_id, body.params))


@router.get("/skills/{skill_id}/practice", response_model=PracticeContent)
def legacy_generate(skill_id: str, svc: Practice, difficulty: str = "入门") -> PracticeContent:
    return svc.generate(skill_id, {"difficulty": difficulty})


@router.post("/v1/practice/evaluate", response_model=EvaluationResponse)
def evaluate(body: EvaluateRequest, svc: Practice) -> EvaluationResponse:
    return EvaluationResponse(evaluation=svc.evaluate(body.skill_id, body.content, body.reference, body.params))


@router.get("/v1/practice/history/{user_id}", response_model=HistoryResponse)
def history(user_id: str, svc: Practice, skill_id: str | None = None) -> HistoryResponse:
    return HistoryResponse(history=svc.history(user_id, skill_id))


@router.get("/v1/practice/progress/{user_id}/{skill_id}", response_model=SkillProgress)
def progress(user_id: str, skill_id: str, svc: Records) -> SkillProgress:
    return svc.progress(user_id, skill_id)


@router.get("/practice/records/{user_id}", response_model=RecordsResponse, response_model_exclude_unset=True)
def records(user_id: str, svc: Records) -> RecordsResponse:
    return RecordsResponse(records=svc.list(user_id))


@router.delete("/practice/record/{record_id}", response_model=MessageResponse)
def delete_record(record_id: str, user_id: str, svc: Records) -> MessageResponse:
    svc.delete(user_id, record_id)
    return MessageResponse(message="记录已从列表隐藏；学习过程保留供检查")


@router.post("/practice/record", deprecated=True, response_model=ErrorResponse, status_code=410)
@router.post("/user/skill/update", deprecated=True, response_model=ErrorResponse, status_code=410)
def retired_score_write() -> NoReturn:
    raise AppError("请通过 /api/v1/practice/start 与 /submit 完成练习；不再接收客户端直接填写的评分。",
                   410, "legacy_score_write_retired")


@router.get("/user/{user_id}/profile", response_model=UserProfile)
def profile(user_id: str, svc: Records) -> UserProfile:
    return svc.profile(user_id)
