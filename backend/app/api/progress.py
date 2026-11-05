from __future__ import annotations
from fastapi import APIRouter, Query
from ..domain.commands import MasteryRequest, AtomicScoreRequest, OptimizeRequest
from ..domain.models import (UserScores, ScoreValue, ManualScore, MasteryUpdated, UserMastery,
                             AtomMastery, Prediction, LearningCurve, Recommendations, Optimization)
from ..errors import AppError
from .dependencies import Progress
from .responses import Success

router = APIRouter(prefix="/api/v1", tags=["learning-progress"])


@router.get("/atomic/users/{user_id}/skills", response_model=UserScores)
def scores(user_id: str, svc: Progress) -> UserScores:
    return svc.scores(user_id)


@router.get("/atomic/users/{user_id}/skills/{atomic_skill_id}/score", response_model=ScoreValue)
def score(user_id: str, atomic_skill_id: str, svc: Progress) -> ScoreValue:
    return svc.score(user_id, atomic_skill_id)


@router.post("/atomic/users/{user_id}/skills/{atomic_skill_id}/score", response_model=ManualScore)
def manual_score(user_id: str, atomic_skill_id: str, body: AtomicScoreRequest, svc: Progress) -> ManualScore:
    if user_id != body.user_id or atomic_skill_id != body.atomic_skill_id:
        raise AppError("路径与请求中的用户/技能不一致", 422, "identity_mismatch")
    return svc.manual_score(body)


@router.post("/knowledge-tracing/update-mastery", response_model=Success[MasteryUpdated])
def update_mastery(body: MasteryRequest, svc: Progress) -> Success[MasteryUpdated]:
    return Success(data=svc.update_mastery(body))


@router.get("/knowledge-tracing/mastery/all/{user_id}", response_model=Success[UserMastery])
def all_mastery(user_id: str, svc: Progress) -> Success[UserMastery]:
    return Success(data=svc.all_mastery(user_id))


@router.get("/knowledge-tracing/mastery/{user_id}/{atomic_skill_id}", response_model=Success[AtomMastery])
def mastery(user_id: str, atomic_skill_id: str, svc: Progress) -> Success[AtomMastery]:
    return Success(data=svc.mastery(user_id, atomic_skill_id))


@router.get("/knowledge-tracing/predict/{user_id}/{atomic_skill_id}", response_model=Success[Prediction])
def predict(user_id: str, atomic_skill_id: str, svc: Progress) -> Success[Prediction]:
    return Success(data=svc.predict(user_id, atomic_skill_id))


@router.get("/knowledge-tracing/learning-curve/{user_id}/{atomic_skill_id}", response_model=Success[LearningCurve])
def curve(user_id: str, atomic_skill_id: str, svc: Progress, days: int = Query(30, ge=1, le=3650)) -> Success[LearningCurve]:
    return Success(data=svc.curve(user_id, atomic_skill_id, days))


@router.get("/knowledge-tracing/recommendations/{user_id}", response_model=Success[Recommendations])
def recommendations(user_id: str, svc: Progress, top_n: int = Query(3, ge=1, le=50)) -> Success[Recommendations]:
    return Success(data=svc.recommendations(user_id, top_n))


@router.post("/atomic/optimize", response_model=Optimization)
def optimize(body: OptimizeRequest, svc: Progress) -> Optimization:
    return svc.optimize(body)
