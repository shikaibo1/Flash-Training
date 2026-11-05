import os
import json
import sys
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
import logging
import uuid
logging.basicConfig(level=logging.INFO)

# 语音处理相关导入（已注释）
# import speech_recognition as sr
# from pydub import AudioSegment
# import io

# 导入现有功能模块
from core.skill.skill_profile_json import load_skill_profiles, update_skill_profile
from core.skill.skill_library_manager import generate_practice_content

# 导入新的API路由
from api.v1.practice_api import router as practice_router

# 导入原子技能管理器
from core.skill.atomic_skill_manager import atomic_skill_manager

# 导入原子技能API路由
from api.v1.atomic_api import router as atomic_router

# 导入知识追踪API路由
from api.v1.knowledge_tracing_api import router as knowledge_tracing_router



app = FastAPI(title="Flash Training API", version="1.0.0")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:8000", "http://127.0.0.1:8000", "*"],  # 允许API文档访问
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据模型
class SkillItem(BaseModel):
    skill_id: str
    skill_name: str
    skill_category: str
    default_difficulty: int

class SkillScoreRequest(BaseModel):
    user_id: str
    skill_name: str
    score: int

class PracticeRecordRequest(BaseModel):
    user_id: str
    skill_id: str
    skill_name: str
    category: str
    difficulty: str
    input_type: str  # voice 或 text
    transcript: str
    score: int
    strengths: list[str]
    improvements: list[str]
    ai_comment: str
    start_time: str
    end_time: str
    # 可选：保存练习时的题目与参考答案（便于回放）
    title: Optional[str] = ""
    description: Optional[str] = ""
    hint: Optional[str] = ""
    example_answer: Optional[str] = ""

# 加载技能数据 (使用新系统，保持向后兼容)
def load_skills():
    # 优先使用新的技能库管理器
    try:
        from core.skill.skill_library_manager import skill_library_manager
        skills = skill_library_manager.get_enabled_skills()
        # 转换为旧格式以保持API兼容性
        return {"skills": [skill for skill in skills]}
    except ImportError:
        # 如果新系统不可用，则回退到默认技能列表
        return {
            "skills": [
                {
                    "skill_id": "skill_speech",
                    "name": "speech",
                    "display_name": "演讲技能练习",
                    "description": "提升公众演讲和表达能力",
                    "enabled": True
                },
                {
                    "skill_id": "skill_interview",
                    "name": "interview",
                    "display_name": "面试技能练习",
                    "description": "提升面试表现和应答能力",
                    "enabled": True
                },
                {
                    "skill_id": "skill_code",
                    "name": "code",
                    "display_name": "编程技能练习",
                    "description": "提升编程能力和代码质量",
                    "enabled": True
                }
            ]
        }

# 练习记录相关工具
def _get_records_file_path():
    # 使用配置文件中的路径，确保一致性
    from config.base_config import config
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    # 从配置中获取路径，如果配置不存在则使用默认路径
    records_path = getattr(config, 'PRACTICE_RECORDS_PATH', "data/practice_records.json")
    return os.path.join(base_dir, records_path)

@app.post("/api/practice/record")
async def save_practice_record(request: PracticeRecordRequest):
    """保存练习记录到 backend/data/practice_records.json（支持 Pydantic v1/v2），并为记录生成唯一 record_id"""
    records_file = _get_records_file_path()
    try:
        # 读取现有记录，兼容文件损坏场景
        if os.path.exists(records_file):
            with open(records_file, "r", encoding="utf-8") as f:
                try:
                    records = json.load(f)
                except Exception:
                    logging.exception("practice_records.json 解析失败，重建文件")
                    records = []
        else:
            records = []

        # 支持 Pydantic v2 的 model_dump 或 Pydantic v1 的 dict()
        try:
            record_data = request.model_dump()
        except Exception:
            record_data = request.dict()

        # 为记录生成唯一 ID（如果已经有 record_id 则保留）
        if not record_data.get("record_id"):
            record_data["record_id"] = str(uuid.uuid4())

        records.append(record_data)

        # 写回文件
        with open(records_file, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)

        logging.info(f"保存练习记录成功: user_id={record_data.get('user_id')}, record_id={record_data.get('record_id')}")
        return {"message": "练习记录保存成功", "record_id": record_data.get("record_id")}

    except Exception as e:
        logging.exception("保存练习记录失败")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/practice/records/{user_id}")
async def get_practice_records(user_id: str):
    """按 user_id 返回历史记录"""
    records_file = _get_records_file_path()
    try:
        if os.path.exists(records_file):
            with open(records_file, "r", encoding="utf-8") as f:
                try:
                    records = json.load(f)
                except Exception:
                    logging.exception("practice_records.json 解析失败")
                    records = []

            # 向后兼容：为没有 record_id 的老记录生成唯一 ID 并写回文件
            updated = False
            for rec in records:
                if not rec.get("record_id"):
                    rec["record_id"] = str(uuid.uuid4())
                    updated = True
            if updated:
                try:
                    with open(records_file, "w", encoding="utf-8") as f:
                        json.dump(records, f, ensure_ascii=False, indent=2)
                except Exception:
                    logging.exception("practice_records.json 写回失败（分配 record_id 后）")

            user_records = [record for record in records if record.get("user_id") == user_id]
            return {"records": user_records}
        else:
            return {"records": []}
    except Exception as e:
        logging.exception("读取练习记录失败")
        raise HTTPException(status_code=500, detail=str(e))

# API 接口
@app.delete("/api/practice/record/{record_id}")
async def delete_practice_record(record_id: str):
    """删除指定 record_id 的练习记录（基于 record_id）"""
    records_file = _get_records_file_path()
    try:
        if os.path.exists(records_file):
            with open(records_file, "r", encoding="utf-8") as f:
                try:
                    records = json.load(f)
                except Exception:
                    logging.exception("practice_records.json 解析失败")
                    records = []
        else:
            raise HTTPException(status_code=404, detail="记录文件不存在")

        new_records = []
        found = False
        for rec in records:
            if rec.get("record_id") == record_id:
                found = True
                continue
            new_records.append(rec)

        if not found:
            raise HTTPException(status_code=404, detail="记录未找到")

        # 写回文件
        with open(records_file, "w", encoding="utf-8") as f:
            json.dump(new_records, f, ensure_ascii=False, indent=2)

        logging.info(f"删除练习记录成功: record_id={record_id}")
        return {"message": "记录删除成功", "record_id": record_id}

    except HTTPException:
        raise
    except Exception as e:
        logging.exception("删除练习记录失败")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/skills")
async def get_skills():
    return load_skills()

@app.get("/api/skills/{skill_id}/practice")
async def get_practice_content(skill_id: str, difficulty: str = "入门"):
    # 生成练习内容
    content = generate_practice_content(skill_id, difficulty)
    return content

@app.get("/api/user/{user_id}/profile")
async def get_user_profile(user_id: str):
    profiles = load_skill_profiles()
    return profiles.get(user_id, {})

# 更新用户技能等级接口
@app.post("/api/user/skill/update")
async def update_user_skill(request: SkillScoreRequest):
    new_difficulty = update_skill_profile(
        user_id=request.user_id,
        skill_name=request.skill_name,
        score=request.score
    )
    return {"new_difficulty": new_difficulty}

# 语音上传接口（已注释）
'''
@app.post("/api/speech/upload")
async def upload_speech(audio: UploadFile = File(...), skill_id: str = Form(...), user_id: str = Form(...)):
    # 保存音频文件到 backend/uploads
    base_dir = os.path.dirname(os.path.abspath(__file__))
    uploads_dir = os.path.join(base_dir, "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    audio_path = os.path.join(uploads_dir, f"{user_id}_{skill_id}_{audio.filename}")
    with open(audio_path, "wb") as buffer:
        buffer.write(await audio.read())
    
    return {"message": "音频上传成功", "audio_path": audio_path} 

# 语音转文字接口
@app.post("/api/speech/transcribe")
async def transcribe_speech(audio: UploadFile = File(...)):
    # 保存音频文件到 backend/uploads（使用项目路径以避免 cwd 问题）
    base_dir = os.path.dirname(os.path.abspath(__file__))
    uploads_dir = os.path.join(base_dir, "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    temp_path = os.path.join(uploads_dir, f"temp_{audio.filename}")
    with open(temp_path, "wb") as buffer:
        content = await audio.read()
        logging.info(f"接收到的音频大小: {len(content)} 字节")
        logging.info(f"音频文件名: {audio.filename}")
        logging.info(f"音频内容类型: {audio.content_type}")
        buffer.write(content)  # 使用已经读取的content，而不是再次读取
    
    try:
        # 验证文件是否存在且大小大于0
        if not os.path.exists(temp_path):
            logging.error(f"临时音频文件不存在: {temp_path}")
            return {"error": "临时文件创建失败", "transcript": ""}
        
        file_size = os.path.getsize(temp_path)
        if file_size == 0:
            logging.error(f"临时音频文件为空: {temp_path}")
            return {"error": "音频文件为空", "transcript": ""}
            
        logging.info(f"临时音频文件大小: {file_size} 字节")
        
        # 使用SpeechRecognition进行语音转文字
        logging.info(f"当前工作目录: {os.getcwd()}")
        logging.info(f"开始识别音频文件: {temp_path}")
        logging.info(f"文件是否存在: {os.path.exists(temp_path)}")
        logging.info(f"文件大小: {os.path.getsize(temp_path)} 字节")
        
        try:
            # 将WebM格式转换为WAV格式
            logging.info(f"开始转换音频格式: {os.path.basename(temp_path)}")
            
            # 读取WebM文件
            audio = AudioSegment.from_file(temp_path, format='webm')
            
            # 转换为WAV格式并保存到内存
            wav_io = io.BytesIO()
            audio.export(wav_io, format='wav')
            wav_io.seek(0)
            
            logging.info(f"音频格式转换完成")
            
            # 创建识别器实例
            r = sr.Recognizer()
            
            # 读取WAV格式的音频数据
            with sr.AudioFile(wav_io) as source:
                # 调整识别器的能量阈值以适应环境噪音
                r.adjust_for_ambient_noise(source)
                # 记录音频数据
                audio_data = r.record(source)
                
            # 使用Google Speech Recognition进行识别
            transcript = r.recognize_google(audio_data, language='zh-CN')
            logging.info(f"识别结果: {transcript}")
            
        except Exception as e:
            logging.error(f"音频格式转换失败: {e}")
            logging.error(f"错误类型: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            
            # 尝试直接使用WebM文件（如果支持的话）
            try:
                r = sr.Recognizer()
                with sr.AudioFile(temp_path) as source:
                    r.adjust_for_ambient_noise(source)
                    audio_data = r.record(source)
                    transcript = r.recognize_google(audio_data, language='zh-CN')
                logging.info(f"直接使用WebM文件识别成功: {transcript}")
            except Exception as e2:
                logging.error(f"直接使用WebM文件识别失败: {e2}")
                
                # 分析错误类型并返回相应提示
                if isinstance(e, sr.UnknownValueError):
                    transcript = "未检测到有效语音内容"
                elif isinstance(e, sr.RequestError):
                    transcript = "语音识别服务不可用，请检查网络连接"
                else:
                    transcript = "语音识别技术问题，请重试"
        
        # 删除临时文件
        os.remove(temp_path)
        
        return {"transcript": transcript}
    except Exception as e:
        # 删除临时文件
        logging.error(f"语音识别失败: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return {"error": str(e), "transcript": ""}
'''


# Note: Atomic skill APIs have been moved to the v1 API structure in atomic_api.py
# The following legacy endpoints were removed to prevent duplicate operation ID warnings:
# - /api/skills/{skill_id}/atomic_skills
# - /api/atomic_skills
# - /api/users/{user_id}/atomic_skills
# - /api/users/{user_id}/atomic_skills/{atomic_skill_id}/score
# - /api/users/{user_id}/atomic_skills/{atomic_skill_id}/score

# 自定义技能创建API
class CustomSkillRequest(BaseModel):
    skill_name: str

@app.post("/api/skills/custom")
async def create_custom_skill(request: CustomSkillRequest):
    """创建自定义技能"""
    try:
        from core.skill.custom_skill_creator import custom_skill_creator
        result = custom_skill_creator.create_custom_skill_from_name(request.skill_name)
        return result
    except Exception as e:
        logging.error(f"创建自定义技能失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 删除技能API
@app.delete("/api/skills/{skill_id}")
async def delete_skill(skill_id: str):
    """删除技能"""
    try:
        from core.skill.skill_library_manager import skill_library_manager
        success = skill_library_manager.delete_skill(skill_id)
        if success:
            return {"success": True, "message": f"技能 {skill_id} 删除成功"}
        else:
            raise HTTPException(status_code=404, detail="技能不存在")
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"删除技能失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Note: Atomic skill APIs have been moved to the v1 API structure in atomic_api.py
# The following legacy endpoints were removed to prevent duplicate operation ID warnings:
# - /api/skills/{skill_id}/atomic_skills
# - /api/atomic_skills
# - /api/users/{user_id}/atomic_skills
# - /api/users/{user_id}/atomic_skills/{atomic_skill_id}/score
# - /api/users/{user_id}/atomic_skills/{atomic_skill_id}/score

# The atomic skill endpoints are now available under /api/v1/atomic/...

# 注册API路由
app.include_router(practice_router)
app.include_router(atomic_router)
app.include_router(knowledge_tracing_router)

# 个性化训练功能已集成到练习系统中，无需单独的API端点
# 练习系统会根据用户原子技能表现自动生成针对性训练

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)