# api/v1/practice_api.py
import asyncio
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from core.practice.unified_practice_manager import unified_practice_manager
from core.skill.skill_library_manager import skill_library_manager
from utils.logger import logger

router = APIRouter(prefix="/api/v1/practice", tags=["practice"])


class StartPracticeRequest(BaseModel):
    user_id: str
    skill_id: str
    params: Dict[str, Any] = {}


class SubmitAnswerRequest(BaseModel):
    user_id: str
    session_id: str
    answer: str


class AddCustomSkillRequest(BaseModel):
    name: str
    display_name: str
    description: str
    generate_prompt: str
    evaluate_prompt: str
    atomic_skills: Optional[List[str]] = None
    default_params: Optional[Dict[str, Any]] = {}


class GenerateContentRequest(BaseModel):
    skill_id: str
    params: Dict[str, Any] = {}


class EvaluateContentRequest(BaseModel):
    skill_id: str
    content: str
    reference: str = ""
    params: Dict[str, Any] = {}

class CreateCustomSkillRequest(BaseModel):
    skill_name: str


@router.post("/start")
async def start_practice(request: StartPracticeRequest):
    """开始一次练习会话"""
    result = unified_practice_manager.start_practice_session(
        user_id=request.user_id,
        skill_id=request.skill_id,
        **request.params
    )
    return result


@router.post("/submit")
async def submit_answer(request: SubmitAnswerRequest):
    """提交练习答案"""
    result = unified_practice_manager.submit_answer(
        user_id=request.user_id,
        session_id=request.session_id,
        answer=request.answer
    )
    return result


@router.get("/history/{user_id}")
async def get_practice_history(user_id: str, skill_id: str = None):
    """获取用户练习历史"""
    history = unified_practice_manager.get_user_practice_history(
        user_id=user_id,
        skill_id=skill_id
    )
    return {"history": history}


@router.get("/progress/{user_id}/{skill_id}")
async def get_skill_progress(user_id: str, skill_id: str):
    """获取用户在特定技能上的进步情况"""
    progress = unified_practice_manager.get_skill_progress(
        user_id=user_id,
        skill_id=skill_id
    )
    return progress


@router.get("/skills")
async def get_available_skills():
    """获取所有可用技能"""
    skills = skill_library_manager.get_enabled_skills()
    return {"skills": skills}


@router.post("/skills/custom")
async def add_custom_skill(request: AddCustomSkillRequest):
    """添加自定义技能"""
    skill = skill_library_manager.add_custom_skill(
        name=request.name,
        display_name=request.display_name,
        description=request.description,
        generate_prompt=request.generate_prompt,
        evaluate_prompt=request.evaluate_prompt,
        atomic_skills=request.atomic_skills,
        default_params=request.default_params
    )
    return {"skill": skill}


@router.post("/generate")
async def generate_content(request: GenerateContentRequest):
    """为指定技能生成内容"""
    # 在线程池中执行同步的生成方法，避免阻塞事件循环
    content = await asyncio.to_thread(
        skill_library_manager.generate_skill_content,
        skill_id=request.skill_id,
        **request.params
    )
    return {"content": content}


@router.post("/evaluate")
async def evaluate_content(request: EvaluateContentRequest):
    """评估指定技能的内容"""
    # 调试日志：输出 API 接收到的请求内容
    logger.debug(f"API 接收 - 技能 ID: {request.skill_id}")
    logger.debug(f"API 接收 - 待评估内容：{request.content}")
    logger.debug(f"API 接收 - 参考信息：{request.reference}")
    logger.debug(f"API 接收 - 参数：{request.params}")
    logger.info(f"API 接收 - 技能 ID: {request.skill_id}")
    logger.info(f"API 接收 - 待评估内容：{request.content}")
    logger.info(f"API 接收 - 参考信息：{request.reference}")
    logger.info(f"API 接收 - 参数：{request.params}")
    
    # 在线程池中执行同步的评估方法，避免阻塞事件循环
    result = await asyncio.to_thread(
        skill_library_manager.evaluate_skill_content,
        skill_id=request.skill_id,
        content=request.content,
        reference=request.reference,
        **request.params
    )
    return {"evaluation": result}


@router.post("/create_custom_skill")
async def create_custom_skill(request: CreateCustomSkillRequest):
    """根据技能名称创建自定义技能，AI 自动生成提示词"""
    from core.skill.custom_skill_creator import custom_skill_creator
    
    result = custom_skill_creator.create_custom_skill_from_name(
        skill_name=request.skill_name
    )
    
    if result["success"]:
        return {"skill": result["skill"], "message": result["message"]}
    else:
        return {"error": result["error"], "message": result["message"]}
