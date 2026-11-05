# core/practice/unified_practice_manager.py
from typing import Dict, List, Any, Optional
import json
import os
import time
import uuid
from datetime import datetime
from utils.logger import logger
from core.skill.skill_library_manager import skill_library_manager
from core.skill.atomic_skill_manager import atomic_skill_manager
from core.skill.skill_profile_json import update_skill_profile, get_skill_profile
from core.knowledge_tracing.knowledge_tracing_manager import knowledge_tracing_manager


class UnifiedPracticeManager:
    """
    统一练习管理器
    管理所有类型的练习活动，基于技能库和原子技能系统
    """
    
    def __init__(self, practice_records_path: str = "data/unified_practice_records.json"):
        self.practice_records_path = practice_records_path
        # 确保数据目录存在
        os.makedirs(os.path.dirname(practice_records_path), exist_ok=True)
        self._initialize_practice_records_file()
    
    def _initialize_practice_records_file(self):
        """初始化练习记录文件"""
        if not os.path.exists(self.practice_records_path):
            with open(self.practice_records_path, "w", encoding="utf-8") as f:
                json.dump([], f)
    
    def load_practice_records(self) -> List[Dict[str, Any]]:
        """加载所有练习记录"""
        try:
            with open(self.practice_records_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载练习记录失败：{e}")
            return []
    
    def save_practice_records(self, records: List[Dict[str, Any]]) -> bool:
        """保存练习记录列表"""
        try:
            with open(self.practice_records_path, "w", encoding="utf-8") as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存练习记录失败：{e}")
            return False
    
    def start_practice_session(self, user_id: str, skill_id: str, **params) -> Dict[str, Any]:
        """
        开始一次练习会话
        :param user_id: 用户ID
        :param skill_id: 技能ID
        :param params: 生成题目所需的参数
        :return: 练习会话信息
        """
        # 获取用户在相关原子技能上的表现，用于生成针对性练习
        question = self._generate_targeted_practice_question(user_id, skill_id, **params)
        if not question:
            logger.error(f"生成练习题目失败：技能ID {skill_id}")
            return {
                "error": True,
                "msg": "生成练习题目失败",
                "data": None
            }
        
        # 创建练习会话记录
        session_id = f"session_{user_id}_{skill_id}_{int(time.time())}"
        session = {
            "session_id": session_id,
            "user_id": user_id,
            "skill_id": skill_id,
            "question": question,
            "start_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "status": "active",
            "attempts": [],
            "final_result": None,
            "params": params  # 保存原始参数，以便在评估时使用
        }
        
        # 保存初始会话记录
        records = self.load_practice_records()
        records.append(session)
        self.save_practice_records(records)
        
        return {
            "error": False,
            "msg": "练习会话开始成功",
            "data": session
        }
    
    def _save_standard_practice_record(self, user_id: str, skill: dict, session: dict, answer: str, evaluation_result: dict, difficulty: str):
        """
        保存与practice_records.json格式一致的标准练习记录
        """
        import os
        import json
        from datetime import datetime
        
        # 标准练习记录文件路径
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        records_file = os.path.join(base_dir, "backend", "data", "practice_records.json")
        
        # 确保目录存在
        os.makedirs(os.path.dirname(records_file), exist_ok=True)
        
        # 读取现有记录
        if os.path.exists(records_file):
            with open(records_file, "r", encoding="utf-8") as f:
                try:
                    records = json.load(f)
                except Exception:
                    records = []
        else:
            records = []
        
        # 构建标准格式的记录
        record = {
            "user_id": user_id,
            "skill_id": skill.get("skill_id", "unknown"),
            "skill_name": skill.get("display_name", "Unknown Skill"),
            "category": "通用",  # 可以根据技能类型动态设置
            "difficulty": difficulty,
            "input_type": "text",
            "transcript": answer,
            "score": int(evaluation_result.get("score", 0) * 10),  # 转换为0-100分制
            "strengths": evaluation_result.get("strengths", []),
            "improvements": evaluation_result.get("improvements", []),
            "ai_comment": evaluation_result.get("aiComment", ""),
            "start_time": session.get("start_time", datetime.now().isoformat()),
            "end_time": session.get("end_time", datetime.now().isoformat()),
            "title": session.get("question", ""),
            "description": f"<p>练习目标：{session.get('question', '')}</p>",
            "hint": "",  # 可以从技能配置中获取提示
            "example_answer": "",  # 可以从技能配置中获取示例答案
            "record_id": str(uuid.uuid4()) if 'uuid' in globals() else str(abs(hash(f"{user_id}_{session['session_id']}_{int(time.time())}")))
        }
        
        # 添加到记录列表
        records.append(record)
        
        # 写回文件
        with open(records_file, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
    
    def _generate_targeted_practice_question(self, user_id: str, skill_id: str, **params):
        """
        根据用户在相关原子技能上的表现生成针对性练习问题
        :param user_id: 用户ID
        :param skill_id: 技能ID
        :param params: 生成题目所需的参数
        :return: 练习题目
        """
        from core.skill.skill_library_manager import skill_library_manager
        from core.ai.universal_ai_evaluator import universal_ai_evaluator
        
        # 获取技能信息
        skill = skill_library_manager.get_skill_by_id(skill_id)
        if not skill:
            logger.error(f"技能不存在：{skill_id}")
            return skill_library_manager.generate_skill_content(skill_id, **params)
        
        # 获取用户在相关原子技能上的表现
        user_atomic_scores = atomic_skill_manager.get_user_all_atomic_skills_scores(user_id)
        
        # 获取该技能关联的原子技能
        skill_atomic_skills = skill.get("atomic_skills", [])
        
        # 找出用户在该技能相关原子技能中最弱的几个
        weak_atomic_skills = []
        for atomic_skill in user_atomic_scores["atomic_skills"]:
            if atomic_skill["atomic_skill_id"] in skill_atomic_skills:
                score = atomic_skill.get("score", 0)
                weak_atomic_skills.append({
                    "id": atomic_skill["atomic_skill_id"],
                    "name": atomic_skill["name"],
                    "description": atomic_skill["description"],
                    "score": score
                })
        
        # 按分数升序排列，找出最需要提升的原子技能
        weak_atomic_skills.sort(key=lambda x: x["score"])
        
        # 取最弱的几个原子技能（最多3个）
        weakest_skills = weak_atomic_skills[:min(3, len(weak_atomic_skills))]
        
        if not weakest_skills:
            # 如果没有找到相关原子技能数据，使用默认方式生成题目
            return skill_library_manager.generate_skill_content(skill_id, **params)
        
        # 使用AI生成针对最薄弱技能的练习题目
        prompt = f"""
        你是专业的{skill['display_name']}教练，请基于以下信息为用户生成一个针对性的练习任务：
        
        用户当前技能水平：
        - {skill['display_name']}相关原子技能表现：
        {chr(10).join([f'  * {s["name"]}(ID: {s["id"]}): {s["score"]}/10分 - {s["description"]}' for s in weakest_skills])}
        
        请生成一个专门针对最薄弱技能（分数最低的原子技能）的练习任务，要求：
        1. 任务要能有效提升最薄弱的原子技能
        2. 难度适中，适合用户当前水平
        3. 具体可操作
        4. 任务内容要与{skill['display_name']}技能相关
        5. 必须包含场景、难度、时长、关键词等具体要素
        
        请直接输出练习任务内容，不要有其他解释。        
        """
        
        # 合并默认参数
        default_params = skill.get("default_params", {})
        all_params = {**default_params, **params}
        
        # 如果用户在某些原子技能上特别薄弱，调整参数以加强这些方面
        weakest_skill = weakest_skills[0]  # 最薄弱的技能
        if weakest_skill["score"] < 5:  # 分数低于5分表示非常薄弱
            # 调整参数以专注于最薄弱的方面
            prompt += f"\n\n特别注意：用户在'{weakest_skill['name']}'方面表现极差({weakest_skill['score']}/10)，本次练习应重点提升这方面。"
        
        question = universal_ai_evaluator.generate_content(
            skill_name=f"{skill['display_name']}个性化训练",
            prompt_template=prompt
        )
        
        if not question:
            # 如果AI生成失败，使用默认方式生成题目
            question = skill_library_manager.generate_skill_content(skill_id, **params)
        
        # 确保返回的是有效的练习题目，而非不完整的内容
        if not question or question.strip() in ['', '练习任务：', '练习任务:', '任务：', '任务:', '题目：', '题目:']:
            # 如果AI返回了不完整的内容，使用默认方式生成题目
            question = skill_library_manager.generate_skill_content(skill_id, **params)
        
        # 如果仍然为空或不完整，返回默认提示
        if not question or question.strip() in ['', '练习任务：', '练习任务:', '任务：', '任务:', '题目：', '题目:']:
            question = f"请完成一个{skill['display_name']}练习，场景：{all_params.get('scene', '通用')}，难度：{all_params.get('difficulty', '中等')}，时长：{all_params.get('duration', '5分钟')}。"
        
        return question
    
    def submit_answer(self, user_id: str, session_id: str, answer: str) -> Dict[str, Any]:
        """
        提交练习答案
        :param user_id: 用户ID
        :param session_id: 练习会话ID
        :param answer: 用户答案
        :return: 评估结果
        """
        # 加载练习记录
        records = self.load_practice_records()
        session = next((r for r in records if r["session_id"] == session_id and r["user_id"] == user_id), None)
        
        if not session:
            return {
                "error": True,
                "msg": "练习会话不存在或不属于当前用户",
                "data": None
            }
        
        if session["status"] != "active":
            return {
                "error": True,
                "msg": "练习会话已结束",
                "data": None
            }
        
        # 获取关联的技能
        skill = skill_library_manager.get_skill_by_id(session["skill_id"])
        if not skill:
            return {
                "error": True,
                "msg": "关联技能不存在",
                "data": None
            }
        
        # 评估答案
        # 使用会话中保存的参数进行评估
        evaluation_result = skill_library_manager.evaluate_skill_content(
            skill_id=session["skill_id"],
            content=answer,
            reference=session["question"],
            **session.get("params", {})  # 使用保存的参数，确保target_skill_name等参数被正确传递
        )
        
        # 记录本次尝试
        attempt = {
            "attempt_id": f"attempt_{len(session['attempts']) + 1}_{int(time.time())}",
            "answer": answer,
            "evaluation": evaluation_result,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        }
        session["attempts"].append(attempt)
        
        # 更新技能档案
        new_difficulty = update_skill_profile(
            user_id=user_id,
            skill_name=skill["display_name"],
            score=int(evaluation_result["score"] * 10)  # 转换为0-100分制
        )
        
        # 根据评估结果更新原子技能分数
        # 从评估结果中提取各项得分信息
        if "atomic_skill_scores" in evaluation_result:
            # 如果评估结果包含原子技能具体得分
            for atomic_skill_id, score in evaluation_result["atomic_skill_scores"].items():
                atomic_skill_manager.update_user_atomic_skill_score(
                    user_id=user_id,
                    atomic_skill_id=atomic_skill_id,
                    score=score
                )
                # 更新知识追踪系统
                knowledge_tracing_manager.update_knowledge_state(
                    user_id=user_id,
                    atomic_skill_id=atomic_skill_id,
                    performance=score
                )
        else:
            # 如果没有详细的原子技能得分，可以根据总体得分按比例分配给相关原子技能
            overall_score = evaluation_result.get("score", 0)
            atomic_skill_ids = skill.get("atomic_skills", [])
            for atomic_skill_id in atomic_skill_ids:
                # 将整体得分作为每个原子技能的得分
                atomic_skill_manager.update_user_atomic_skill_score(
                    user_id=user_id,
                    atomic_skill_id=atomic_skill_id,
                    score=overall_score
                )
                # 更新知识追踪系统
                knowledge_tracing_manager.update_knowledge_state(
                    user_id=user_id,
                    atomic_skill_id=atomic_skill_id,
                    performance=overall_score
                )
        
        # 更新会话状态
        session["final_result"] = evaluation_result
        session["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        session["status"] = "completed"
        
        # 保存更新后的记录
        self.save_practice_records(records)
        
        # 同时保存到标准练习记录文件（与practice_records.json格式一致）
        self._save_standard_practice_record(user_id, skill, session, answer, evaluation_result, new_difficulty)
        
        return {
            "error": False,
            "msg": "答案提交和评估成功",
            "data": {
                "session_id": session_id,
                "question": session["question"],
                "evaluation_result": evaluation_result,
                "new_difficulty": new_difficulty,
                "skill_tip": f"你的{skill['display_name']}技能难度已更新为{new_difficulty}级，继续练习可提升！"
            }
        }
    
    def get_user_practice_history(self, user_id: str, skill_id: str = None) -> List[Dict[str, Any]]:
        """
        获取用户练习历史
        :param user_id: 用户ID
        :param skill_id: 技能ID（可选，如果不提供则返回所有技能的记录）
        :return: 练习历史列表
        """
        records = self.load_practice_records()
        user_records = [r for r in records if r["user_id"] == user_id]
        
        if skill_id:
            user_records = [r for r in user_records if r["skill_id"] == skill_id]
        
        # 按时间倒序排列
        user_records.sort(key=lambda x: x.get("start_time", ""), reverse=True)
        
        return user_records
    
    def get_skill_progress(self, user_id: str, skill_id: str) -> Dict[str, Any]:
        """
        获取用户在特定技能上的进步情况
        :param user_id: 用户ID
        :param skill_id: 技能ID
        :return: 进步情况统计
        """
        records = self.get_user_practice_history(user_id, skill_id)
        
        if not records:
            return {
                "total_sessions": 0,
                "completed_sessions": 0,
                "avg_score": 0,
                "improvement_trend": []
            }
        
        completed_records = [r for r in records if r["status"] == "completed"]
        scores = [r["final_result"]["score"] for r in completed_records if r.get("final_result")]
        
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # 计算进步趋势（最近几次练习的平均分变化）
        recent_sessions = completed_records[:5]  # 最近5次
        recent_scores = [r["final_result"]["score"] for r in recent_sessions if r.get("final_result")]
        
        improvement_trend = []
        if len(recent_scores) >= 2:
            for i in range(1, len(recent_scores)):
                trend = recent_scores[i] - recent_scores[i-1]
                improvement_trend.append(trend)
        
        return {
            "total_sessions": len(records),
            "completed_sessions": len(completed_records),
            "avg_score": round(avg_score, 2),
            "improvement_trend": improvement_trend,
            "latest_score": recent_scores[0] if recent_scores else 0
        }


# 全局实例
unified_practice_manager = UnifiedPracticeManager()