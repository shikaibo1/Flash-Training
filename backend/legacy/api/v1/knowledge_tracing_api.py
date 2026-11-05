# api/v1/knowledge_tracing_api.py
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from core.knowledge_tracing.knowledge_tracing_manager import knowledge_tracing_manager
from utils.logger import logger

router = APIRouter(prefix="/api/v1/knowledge-tracing", tags=["knowledge-tracing"])


class UpdateMasteryRequest(BaseModel):
    user_id: str
    atomic_skill_id: str
    performance: float
    timestamp: Optional[str] = None


class GetMasteryRequest(BaseModel):
    user_id: str
    atomic_skill_id: str


class GetLearningCurveRequest(BaseModel):
    user_id: str
    atomic_skill_id: str
    days: int = 30


@router.post("/update-mastery")
async def update_mastery(request: UpdateMasteryRequest):
    """更新用户的知识掌握度"""
    try:
        new_mastery = knowledge_tracing_manager.update_knowledge_state(
            user_id=request.user_id,
            atomic_skill_id=request.atomic_skill_id,
            performance=request.performance,
            timestamp=request.timestamp
        )
        return {
            "error": False,
            "msg": "掌握度更新成功",
            "data": {
                "atomic_skill_id": request.atomic_skill_id,
                "new_mastery": new_mastery
            }
        }
    except Exception as e:
        logger.error(f"更新掌握度失败：{e}")
        return {
            "error": True,
            "msg": "掌握度更新失败",
            "data": None
        }


@router.get("/mastery/all/{user_id}")
async def get_all_mastery(user_id: str):
    """获取用户所有原子技能的掌握度"""
    try:
        mastery_data = knowledge_tracing_manager.get_user_all_mastery(user_id)
        return {
            "error": False,
            "msg": "获取所有掌握度成功",
            "data": mastery_data
        }
    except Exception as e:
        logger.error(f"获取所有掌握度失败：{e}")
        return {
            "error": True,
            "msg": "获取所有掌握度失败",
            "data": None
        }


@router.get("/mastery/{user_id}/{atomic_skill_id}")
async def get_mastery(user_id: str, atomic_skill_id: str):
    """获取用户特定原子技能的掌握度"""
    try:
        mastery = knowledge_tracing_manager.get_user_mastery(user_id, atomic_skill_id)
        return {
            "error": False,
            "msg": "获取掌握度成功",
            "data": {
                "atomic_skill_id": atomic_skill_id,
                "mastery": mastery
            }
        }
    except Exception as e:
        logger.error(f"获取掌握度失败：{e}")
        return {
            "error": True,
            "msg": "获取掌握度失败",
            "data": None
        }


@router.get("/predict/{user_id}/{atomic_skill_id}")
async def predict_performance(user_id: str, atomic_skill_id: str):
    """预测用户在特定原子技能上的表现"""
    try:
        predicted_performance = knowledge_tracing_manager.predict_performance(user_id, atomic_skill_id)
        return {
            "error": False,
            "msg": "预测表现成功",
            "data": {
                "atomic_skill_id": atomic_skill_id,
                "predicted_performance": predicted_performance
            }
        }
    except Exception as e:
        logger.error(f"预测表现失败：{e}")
        return {
            "error": True,
            "msg": "预测表现失败",
            "data": None
        }


@router.get("/learning-curve/{user_id}/{atomic_skill_id}")
async def get_learning_curve(user_id: str, atomic_skill_id: str, days: int = 30):
    """获取用户在特定原子技能上的学习曲线"""
    try:
        learning_curve = knowledge_tracing_manager.get_learning_curve(user_id, atomic_skill_id, days)
        return {
            "error": False,
            "msg": "获取学习曲线成功",
            "data": {
                "atomic_skill_id": atomic_skill_id,
                "learning_curve": learning_curve,
                "days": days
            }
        }
    except Exception as e:
        logger.error(f"获取学习曲线失败：{e}")
        return {
            "error": True,
            "msg": "获取学习曲线失败",
            "data": None
        }


@router.get("/recommendations/{user_id}")
async def get_recommendations(user_id: str, top_n: int = 3):
    """获取技能推荐"""
    try:
        recommendations = knowledge_tracing_manager.get_skill_recommendations(user_id, top_n)
        return {
            "error": False,
            "msg": "获取推荐成功",
            "data": {
                "recommendations": recommendations,
                "top_n": top_n
            }
        }
    except Exception as e:
        logger.error(f"获取推荐失败：{e}")
        return {
            "error": True,
            "msg": "获取推荐失败",
            "data": None
        }