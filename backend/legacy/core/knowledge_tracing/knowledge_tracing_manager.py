# core/knowledge_tracing/knowledge_tracing_manager.py
from typing import Dict, List, Any, Optional
import json
import os
import time
from datetime import datetime, timedelta
import numpy as np
from utils.logger import logger
from core.skill.atomic_skill_manager import atomic_skill_manager


class KnowledgeTracingManager:
    """
    知识追踪管理器
    负责管理用户知识点的掌握度追踪、预测和分析
    """
    
    def __init__(self, knowledge_tracing_path: str = "data/knowledge_tracing.json"):
        self.knowledge_tracing_path = knowledge_tracing_path
        # 确保数据目录存在
        os.makedirs(os.path.dirname(knowledge_tracing_path), exist_ok=True)
        self._initialize_knowledge_tracing_file()
    
    def _initialize_knowledge_tracing_file(self):
        """初始化知识追踪文件"""
        if not os.path.exists(self.knowledge_tracing_path):
            default_data = {
                "users": {}
            }
            with open(self.knowledge_tracing_path, "w", encoding="utf-8") as f:
                json.dump(default_data, f, ensure_ascii=False, indent=2)
    
    def load_knowledge_tracing_data(self) -> Dict[str, Any]:
        """加载知识追踪数据"""
        try:
            with open(self.knowledge_tracing_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载知识追踪数据失败：{e}")
            return {"users": {}}
    
    def save_knowledge_tracing_data(self, data: Dict[str, Any]) -> bool:
        """保存知识追踪数据"""
        try:
            with open(self.knowledge_tracing_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存知识追踪数据失败：{e}")
            return False
    
    def update_knowledge_state(self, user_id: str, atomic_skill_id: str, performance: float, timestamp: Optional[str] = None):
        """
        更新用户的知识状态
        :param user_id: 用户ID
        :param atomic_skill_id: 原子技能ID
        :param performance: 表现分数 (0-1)
        :param timestamp: 时间戳，默认为当前时间
        """
        data = self.load_knowledge_tracing_data()
        
        # 确保用户数据存在
        if user_id not in data["users"]:
            data["users"][user_id] = {
                "atomic_skills": {}
            }
        
        user_data = data["users"][user_id]
        
        # 确保原子技能数据存在
        if atomic_skill_id not in user_data["atomic_skills"]:
            user_data["atomic_skills"][atomic_skill_id] = {
                "mastery": 0.0,
                "last_practice_time": None,
                "practice_count": 0,
                "history": []
            }
        
        skill_data = user_data["atomic_skills"][atomic_skill_id]
        
        # 计算时间间隔（如果有历史记录）
        time_interval = 0
        if skill_data["last_practice_time"]:
            last_time = datetime.strptime(skill_data["last_practice_time"], "%Y-%m-%d %H:%M:%S")
            current_time = datetime.strptime(timestamp or time.strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")
            time_interval = (current_time - last_time).total_seconds() / 3600  # 转换为小时
        
        # 更新掌握度
        new_mastery = self._update_mastery(
            current_mastery=skill_data["mastery"],
            performance=performance,
            time_interval=time_interval,
            practice_count=skill_data["practice_count"]
        )
        
        # 更新技能数据
        skill_data["mastery"] = new_mastery
        skill_data["last_practice_time"] = timestamp or time.strftime("%Y-%m-%d %H:%M:%S")
        skill_data["practice_count"] += 1
        
        # 添加历史记录
        skill_data["history"].append({
            "timestamp": skill_data["last_practice_time"],
            "performance": performance,
            "mastery": new_mastery,
            "time_interval": time_interval
        })
        
        # 限制历史记录长度（保留最近100条）
        if len(skill_data["history"]) > 100:
            skill_data["history"] = skill_data["history"][-100:]
        
        # 保存数据
        self.save_knowledge_tracing_data(data)
        
        return new_mastery
    
    def _update_mastery(self, current_mastery: float, performance: float, time_interval: float, practice_count: int) -> float:
        """
        更新掌握度
        基于Temporal IRT模型和遗忘模型
        """
        # 应用遗忘模型
        if time_interval > 0:
            # 遗忘率随时间指数衰减
            forgetting_rate = 0.05  # 每小时遗忘率
            current_mastery = current_mastery * np.exp(-forgetting_rate * time_interval)
        
        # 基于表现更新掌握度
        # 学习率随练习次数增加而降低
        learning_rate = 0.3 / (1 + 0.1 * practice_count)
        
        # 维纳过程更新
        # 表现越好，掌握度增加越多
        mastery_update = learning_rate * (performance - current_mastery)
        
        # 确保掌握度在0-1之间
        new_mastery = current_mastery + mastery_update
        new_mastery = max(0.0, min(1.0, new_mastery))
        
        return new_mastery
    
    def get_user_mastery(self, user_id: str, atomic_skill_id: str) -> float:
        """
        获取用户特定原子技能的掌握度
        """
        data = self.load_knowledge_tracing_data()
        
        if user_id not in data["users"] or atomic_skill_id not in data["users"][user_id]["atomic_skills"]:
            return 0.0
        
        skill_data = data["users"][user_id]["atomic_skills"][atomic_skill_id]
        
        # 检查是否需要应用遗忘（如果距离上次练习时间较长）
        if skill_data["last_practice_time"]:
            last_time = datetime.strptime(skill_data["last_practice_time"], "%Y-%m-%d %H:%M:%S")
            current_time = datetime.now()
            time_interval = (current_time - last_time).total_seconds() / 3600  # 转换为小时
            
            if time_interval > 0:
                # 应用遗忘模型
                forgetting_rate = 0.05
                adjusted_mastery = skill_data["mastery"] * np.exp(-forgetting_rate * time_interval)
                adjusted_mastery = max(0.0, min(1.0, adjusted_mastery))
                return adjusted_mastery
        
        return skill_data["mastery"]
    
    def get_user_all_mastery(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户所有原子技能的掌握度
        """
        data = self.load_knowledge_tracing_data()
        
        if user_id not in data["users"]:
            return {"user_id": user_id, "atomic_skills": []}
        
        user_data = data["users"][user_id]
        atomic_skills = atomic_skill_manager.load_atomic_skills()
        
        result = []
        for skill in atomic_skills:
            skill_id = skill["atomic_skill_id"]
            mastery = self.get_user_mastery(user_id, skill_id)
            
            result.append({
                "atomic_skill_id": skill_id,
                "name": skill["name"],
                "description": skill["description"],
                "categories": skill["categories"],
                "mastery": mastery
            })
        
        return {
            "user_id": user_id,
            "atomic_skills": result
        }
    
    def predict_performance(self, user_id: str, atomic_skill_id: str) -> float:
        """
        预测用户在特定原子技能上的表现
        """
        mastery = self.get_user_mastery(user_id, atomic_skill_id)
        
        # 基于掌握度预测表现
        # 掌握度越高，预测表现越好
        # 添加一些随机噪声模拟不确定性
        noise = np.random.normal(0, 0.1)
        predicted_performance = mastery + noise
        predicted_performance = max(0.0, min(1.0, predicted_performance))
        
        return predicted_performance
    
    def get_learning_curve(self, user_id: str, atomic_skill_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        获取用户在特定原子技能上的学习曲线
        """
        data = self.load_knowledge_tracing_data()
        
        if user_id not in data["users"] or atomic_skill_id not in data["users"][user_id]["atomic_skills"]:
            return []
        
        skill_data = data["users"][user_id]["atomic_skills"][atomic_skill_id]
        history = skill_data["history"]
        
        # 过滤最近指定天数的记录
        cutoff_date = datetime.now() - timedelta(days=days)
        filtered_history = []
        
        for record in history:
            record_date = datetime.strptime(record["timestamp"], "%Y-%m-%d %H:%M:%S")
            if record_date >= cutoff_date:
                filtered_history.append(record)
        
        return filtered_history
    
    def get_skill_dependencies(self) -> Dict[str, List[str]]:
        """
        获取技能依赖关系
        这里使用简单的依赖关系定义，实际应用中可以从配置或数据库中加载
        """
        # 定义技能依赖关系
        dependencies = {
            "as_001": ["as_003", "as_005"],  # 内容准确性依赖表达清晰度和逻辑合理性
            "as_002": ["as_003", "as_005"],  # 结构完整性依赖表达清晰度和逻辑合理性
            "as_003": ["as_005"],             # 表达清晰度依赖逻辑合理性
            "as_004": [],                      # 语法规范性无依赖
            "as_005": []                       # 逻辑合理性无依赖
        }
        return dependencies
    
    def get_skill_recommendations(self, user_id: str, top_n: int = 3) -> List[Dict[str, Any]]:
        """
        获取技能推荐（基于掌握度和依赖关系）
        """
        user_mastery = self.get_user_all_mastery(user_id)
        atomic_skills = user_mastery["atomic_skills"]
        dependencies = self.get_skill_dependencies()
        
        # 计算每个技能的推荐分数
        skill_scores = []
        for skill in atomic_skills:
            skill_id = skill["atomic_skill_id"]
            mastery = skill["mastery"]
            
            # 基础分数：掌握度越低，分数越高
            base_score = 1.0 - mastery
            
            # 考虑依赖关系：如果依赖的技能掌握度高，当前技能的推荐分数会增加
            dependency_score = 0.0
            if skill_id in dependencies:
                for dep_id in dependencies[skill_id]:
                    # 找到依赖技能的掌握度
                    dep_skill = next((s for s in atomic_skills if s["atomic_skill_id"] == dep_id), None)
                    if dep_skill:
                        dependency_score += dep_skill["mastery"] * 0.2  # 依赖技能掌握度的权重
            
            # 综合分数
            total_score = base_score + dependency_score
            
            skill_scores.append({
                **skill,
                "score": total_score,
                "priority": total_score
            })
        
        # 按分数排序，推荐分数高的技能
        sorted_skills = sorted(skill_scores, key=lambda x: x["score"], reverse=True)
        
        # 返回推荐的技能
        recommendations = sorted_skills[:min(top_n, len(sorted_skills))]
        
        return recommendations


# 全局实例
knowledge_tracing_manager = KnowledgeTracingManager()