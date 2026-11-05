# core/skill/atomic_skill_manager.py
from typing import Dict, List, Any, Optional
import json
import os
from utils.logger import logger
from difflib import SequenceMatcher


class AtomicSkillManager:
    """
    原子技能管理器
    负责管理原子技能的增删改查、相似度匹配等功能
    """
    
    def __init__(self, atomic_skills_path: str = "data/atomic_skills.json", user_atomic_scores_path: str = "data/user_atomic_scores.json"):
        self.atomic_skills_path = atomic_skills_path
        self.user_atomic_scores_path = user_atomic_scores_path
        # 确保数据目录存在
        os.makedirs(os.path.dirname(atomic_skills_path), exist_ok=True)
        os.makedirs(os.path.dirname(user_atomic_scores_path), exist_ok=True)
        self._initialize_atomic_skills_file()
        self._initialize_user_atomic_scores_file()
    
    def _initialize_atomic_skills_file(self):
        """初始化原子技能文件"""
        if not os.path.exists(self.atomic_skills_path):
            default_atomic_skills = {
                "atomic_skills": [
                    {
                        "atomic_skill_id": "as_001",
                        "name": "内容准确性",
                        "description": "内容准确无误，符合事实和逻辑",
                        "categories": ["通用"]
                    },
                    {
                        "atomic_skill_id": "as_002",
                        "name": "结构完整性",
                        "description": "内容结构完整，有清晰的开头、中间和结尾",
                        "categories": ["写作", "演讲", "报告"]
                    },
                    {
                        "atomic_skill_id": "as_003",
                        "name": "表达清晰度",
                        "description": "表达清晰易懂，逻辑连贯",
                        "categories": ["通用"]
                    },
                    {
                        "atomic_skill_id": "as_004",
                        "name": "语法规范性",
                        "description": "语法、拼写、标点符号使用正确",
                        "categories": ["写作", "代码"]
                    },
                    {
                        "atomic_skill_id": "as_005",
                        "name": "逻辑合理性",
                        "description": "逻辑推理合理，前后一致",
                        "categories": ["通用"]
                    }
                ]
            }
            with open(self.atomic_skills_path, "w", encoding="utf-8") as f:
                json.dump(default_atomic_skills, f, ensure_ascii=False, indent=2)
    
    def _initialize_user_atomic_scores_file(self):
        """初始化用户原子技能分数文件"""
        if not os.path.exists(self.user_atomic_scores_path):
            default_scores = {}
            with open(self.user_atomic_scores_path, "w", encoding="utf-8") as f:
                json.dump(default_scores, f, ensure_ascii=False, indent=2)
    
    def load_atomic_skills(self) -> List[Dict[str, Any]]:
        """加载所有原子技能"""
        try:
            with open(self.atomic_skills_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("atomic_skills", [])
        except Exception as e:
            logger.error(f"加载原子技能失败：{e}")
            return []
    
    def save_atomic_skills(self, atomic_skills: List[Dict[str, Any]]) -> bool:
        """保存原子技能列表"""
        try:
            data = {"atomic_skills": atomic_skills}
            with open(self.atomic_skills_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存原子技能失败：{e}")
            return False
    
    def find_similar_atomic_skills(self, skill_description: str, threshold: float = 0.6) -> List[Dict[str, Any]]:
        """
        查找相似的原子技能
        :param skill_description: 新技能的描述
        :param threshold: 相似度阈值
        :return: 相似的原子技能列表
        """
        all_skills = self.load_atomic_skills()
        similar_skills = []
        
        for skill in all_skills:
            similarity = self._calculate_similarity(skill_description, skill["description"])
            if similarity >= threshold:
                similar_skills.append({
                    "skill": skill,
                    "similarity": similarity
                })
        
        # 按相似度降序排列
        similar_skills.sort(key=lambda x: x["similarity"], reverse=True)
        return [item["skill"] for item in similar_skills]
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """计算两个字符串的相似度"""
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    def add_atomic_skill(self, name: str, description: str, categories: List[str]) -> Dict[str, Any]:
        """
        添加新的原子技能
        :param name: 技能名称
        :param description: 技能描述
        :param categories: 所属类别列表
        :return: 添加的原子技能信息
        """
        all_skills = self.load_atomic_skills()
        
        # 生成唯一ID
        max_id = 0
        for skill in all_skills:
            try:
                skill_id_num = int(skill["atomic_skill_id"].split("_")[1])
                max_id = max(max_id, skill_id_num)
            except:
                continue
        
        new_skill_id = f"as_{str(max_id + 1).zfill(3)}"
        
        new_skill = {
            "atomic_skill_id": new_skill_id,
            "name": name,
            "description": description,
            "categories": categories
        }
        
        all_skills.append(new_skill)
        
        if self.save_atomic_skills(all_skills):
            logger.info(f"新增原子技能成功：{name}")
            return new_skill
        else:
            logger.error(f"新增原子技能失败：{name}")
            return {}
    
    def merge_similar_skills(self, new_skill_desc: str, existing_skills: List[Dict[str, Any]], 
                           threshold: float = 0.8) -> Optional[Dict[str, Any]]:
        """
        合并相似的原子技能
        :param new_skill_desc: 新技能描述
        :param existing_skills: 现有技能列表
        :param threshold: 合并阈值
        :return: 如果找到足够相似的技能则返回它，否则返回None
        """
        for skill in existing_skills:
            similarity = self._calculate_similarity(new_skill_desc, skill["description"])
            if similarity >= threshold:
                logger.info(f"找到相似原子技能，建议合并：{skill['name']} (相似度: {similarity:.2f})")
                return skill
        return None
    
    def get_atomic_skill_by_id(self, atomic_skill_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取原子技能"""
        all_skills = self.load_atomic_skills()
        for skill in all_skills:
            if skill["atomic_skill_id"] == atomic_skill_id:
                return skill
        return None
    
    def update_atomic_skill(self, atomic_skill_id: str, updates: Dict[str, Any]) -> bool:
        """更新原子技能信息"""
        all_skills = self.load_atomic_skills()
        for i, skill in enumerate(all_skills):
            if skill["atomic_skill_id"] == atomic_skill_id:
                all_skills[i].update(updates)
                return self.save_atomic_skills(all_skills)
        return False
    
    def remove_atomic_skill(self, atomic_skill_id: str) -> bool:
        """移除原子技能"""
        all_skills = self.load_atomic_skills()
        filtered_skills = [skill for skill in all_skills if skill["atomic_skill_id"] != atomic_skill_id]
        if len(filtered_skills) != len(all_skills):
            return self.save_atomic_skills(filtered_skills)
        return False
    
    def get_user_atomic_skill_score(self, user_id: str, atomic_skill_id: str) -> float:
        """获取用户特定原子技能的分数"""
        try:
            with open(self.user_atomic_scores_path, "r", encoding="utf-8") as f:
                scores = json.load(f)
            
            user_scores = scores.get(user_id, {})
            return user_scores.get(atomic_skill_id, 0.0)
        except Exception as e:
            logger.error(f"获取用户原子技能分数失败：{e}")
            return 0.0
    
    def update_user_atomic_skill_score(self, user_id: str, atomic_skill_id: str, score: float):
        """更新用户特定原子技能的分数"""
        try:
            with open(self.user_atomic_scores_path, "r", encoding="utf-8") as f:
                scores = json.load(f)
        except Exception:
            scores = {}
        
        if user_id not in scores:
            scores[user_id] = {}
        
        scores[user_id][atomic_skill_id] = score
        
        try:
            with open(self.user_atomic_scores_path, "w", encoding="utf-8") as f:
                json.dump(scores, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存用户原子技能分数失败：{e}")
            return False
    
    def get_all_atomic_skills_with_scores(self) -> List[Dict[str, Any]]:
        """获取所有原子技能及其基础信息"""
        atomic_skills = self.load_atomic_skills()
        return atomic_skills
    
    def get_user_all_atomic_skills_scores(self, user_id: str) -> Dict[str, Any]:
        """获取用户所有原子技能的分数"""
        try:
            with open(self.user_atomic_scores_path, "r", encoding="utf-8") as f:
                scores = json.load(f)
            
            user_scores = scores.get(user_id, {})
            
            # 获取所有原子技能的基本信息
            atomic_skills = self.load_atomic_skills()
            
            # 合并基本信息和分数
            result = []
            for skill in atomic_skills:
                skill_info = skill.copy()
                skill_info['score'] = user_scores.get(skill['atomic_skill_id'], 0.0)
                result.append(skill_info)
            
            return {
                "user_id": user_id,
                "atomic_skills": result
            }
        except Exception as e:
            logger.error(f"获取用户所有原子技能分数失败：{e}")
            return {"user_id": user_id, "atomic_skills": []}


# 全局实例
atomic_skill_manager = AtomicSkillManager()