# api/v1/atomic_api.py
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, List, Any
from core.skill.atomic_skill_manager import atomic_skill_manager
from core.skill.skill_library_manager import skill_library_manager
from core.ai.universal_ai_evaluator import universal_ai_evaluator

router = APIRouter(prefix="/api/v1/atomic", tags=["atomic"])


class OptimizationRequest(BaseModel):
    user_id: str
    atomic_skill_ids: List[str]
    optimization_goal: str = "提升技能"


class ScoreUpdateRequest(BaseModel):
    user_id: str
    atomic_skill_id: str
    score: float


@router.get("/skills")
async def get_all_atomic_skills():
    """获取所有原子技能"""
    atomic_skills = atomic_skill_manager.get_all_atomic_skills_with_scores()
    return {"atomic_skills": atomic_skills}


@router.get("/users/{user_id}/skills")
async def get_user_atomic_skills(user_id: str):
    """获取用户所有原子技能的分数"""
    result = atomic_skill_manager.get_user_all_atomic_skills_scores(user_id)
    return result


@router.post("/users/{user_id}/skills/{atomic_skill_id}/score")
async def update_atomic_skill_score(user_id: str, atomic_skill_id: str, request: ScoreUpdateRequest):
    """更新用户特定原子技能的分数"""
    success = atomic_skill_manager.update_user_atomic_skill_score(
        user_id=user_id,
        atomic_skill_id=atomic_skill_id,
        score=request.score
    )
    
    if not success:
        return {"error": True, "message": "更新分数失败"}
    
    return {"message": "分数更新成功", "user_id": user_id, "atomic_skill_id": atomic_skill_id, "score": request.score}


@router.get("/users/{user_id}/skills/{atomic_skill_id}/score")
async def get_atomic_skill_score(user_id: str, atomic_skill_id: str):
    """获取用户特定原子技能的分数"""
    score = atomic_skill_manager.get_user_atomic_skill_score(user_id, atomic_skill_id)
    return {"user_id": user_id, "atomic_skill_id": atomic_skill_id, "score": score}


@router.get("/skills/{skill_id}/mapping")
async def get_atomic_skills_for_skill(skill_id: str):
    """获取指定技能对应的原子技能"""
    skill = skill_library_manager.get_skill_by_id(skill_id)
    
    if not skill:
        return {"error": True, "message": "技能不存在"}
    
    atomic_skill_ids = skill.get("atomic_skills", [])
    atomic_skills = []
    
    for atomic_id in atomic_skill_ids:
        atomic_skill = atomic_skill_manager.get_atomic_skill_by_id(atomic_id)
        if atomic_skill:
            # 添加当前用户的分数
            user_scores = atomic_skill_manager.get_user_atomic_skill_score("temp_user", atomic_id)  # 实际应用中需要替换为真实用户
            atomic_skill_with_score = atomic_skill.copy()
            atomic_skill_with_score['current_score'] = user_scores
            atomic_skills.append(atomic_skill_with_score)
    
    return {
        "skill_id": skill_id,
        "skill_name": skill.get("display_name", skill.get("name", "")),
        "atomic_skills": atomic_skills
    }


@router.post("/optimize")
async def generate_optimization_plan(request: OptimizationRequest):
    """根据用户原子技能分数生成统合问题以优化分数"""
    # 获取用户原子技能分数
    user_atomic_scores = atomic_skill_manager.get_user_all_atomic_skills_scores(request.user_id)
    
    # 筛选出请求的原子技能
    targeted_skills = []
    for skill in user_atomic_scores["atomic_skills"]:
        if skill["atomic_skill_id"] in request.atomic_skill_ids:
            targeted_skills.append(skill)
    
    # 按分数排序，找出最需要提升的技能
    targeted_skills.sort(key=lambda x: x.get("score", 0))
    lowest_scoring_skills = targeted_skills[:3]  # 选择分数最低的最多3个技能
    
    # 生成优化建议
    optimization_prompt = f"""
    你是一位专业的技能发展顾问。根据以下用户在原子技能方面的表现，请生成一个综合性的练习建议：
    
    用户ID: {request.user_id}
    优化目标: {request.optimization_goal}
    
    需要重点提升的原子技能:
    {chr(10).join([f'- {skill["name"]}: 当前分数 {skill.get("score", 0)}, 描述: {skill["description"]}' for skill in lowest_scoring_skills])}
    
    请提供一个综合性练习任务，能够同时提升以上一个或多个技能，并说明如何通过此任务达到提升效果。
    输出格式：
    1. 练习任务描述
    2. 预期提升的技能
    3. 完成标准
    4. 评估方法
    """
    
    optimization_advice = universal_ai_evaluator.generate_content(
        skill_name="技能优化建议",
        prompt_template=optimization_prompt
    )
    
    return {
        "user_id": request.user_id,
        "targeted_skills": lowest_scoring_skills,
        "optimization_advice": optimization_advice,
        "optimization_goal": request.optimization_goal
    }