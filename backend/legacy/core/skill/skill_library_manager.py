# core/skill/skill_library_manager.py
from typing import Dict, List, Any, Optional
import json
import os
from utils.logger import logger
from core.skill.atomic_skill_manager import atomic_skill_manager
from core.ai.universal_ai_evaluator import universal_ai_evaluator
from core.ai import get_doubao_client


class SkillLibraryManager:
    """
    技能库管理器
    负责管理用户可练习的技能类型，包括预设技能和用户自定义技能
    """
    
    def __init__(self, skills_path: str = "data/skill_library.json"):
        self.skills_path = skills_path
        # 确保数据目录存在
        os.makedirs(os.path.dirname(skills_path), exist_ok=True)
        self._initialize_skill_library_file()
    
    def _initialize_skill_library_file(self):
        """初始化技能库文件"""
        if not os.path.exists(self.skills_path):
            default_skills = {
                "skills": [
                    {
                        "skill_id": "skill_speech",
                        "name": "演讲",
                        "display_name": "演讲技能练习",
                        "description": "提升公众演讲和表达能力",
                        "atomic_skills": ["as_001", "as_002", "as_003"],  # 内容准确性、结构完整性、表达清晰度
                        "generate_prompt": "你是演讲教练，请生成一个适合练习的演讲主题，要求：场景：{scene}，时长：{duration}，关键词：{keyword}。只需输出主题，无需其他内容。",
                        "evaluate_prompt": "你是演讲专家，评估以下演讲稿：\n\n演讲稿：{content}\n\n要求：从内容准确性、结构完整性、表达清晰度等方面进行评估，并按以下格式输出：总分(1-10分)|各项得分详情|优点|改进建议。",
                        "enabled": True,
                        "default_params": {
                            "scene": "职场",
                            "duration": "3分钟",
                            "keyword": ""
                        }
                    },
                    {
                        "skill_id": "skill_interview",
                        "name": "面试",
                        "display_name": "面试技能练习",
                        "description": "提升面试表现和应答能力",
                        "atomic_skills": ["as_001", "as_003", "as_005"],  # 内容准确性、表达清晰度、逻辑合理性
                        "generate_prompt": "你是资深面试官，请生成一道针对{job_type}岗位的面试题，难度：{difficulty}。只需输出题目，无需其他内容。",
                        "evaluate_prompt": "你是面试专家，评估以下面试回答：\n\n回答：{content}\n\n要求：从内容准确性、表达清晰度、逻辑合理性等方面进行评估，并按以下格式输出：总分(1-10分)|各项得分详情|优点|改进建议。",
                        "enabled": True,
                        "default_params": {
                            "job_type": "软件工程师",
                            "difficulty": "中等"
                        }
                    },
                    {
                        "skill_id": "skill_code",
                        "name": "代码",
                        "display_name": "编程技能练习",
                        "description": "提升编程能力和代码质量",
                        "atomic_skills": ["as_001", "as_004", "as_005"],  # 内容准确性、语法规范性、逻辑合理性
                        "generate_prompt": "你是编程导师，请生成一道{language}语言的编程题，难度：{difficulty}，知识点：{topic}。题目应包含：问题描述、输入输出格式、示例。",
                        "evaluate_prompt": "你是代码审查专家，评估以下代码：\n\n代码：{content}\n\n要求：从内容准确性、语法规范性、逻辑合理性等方面进行评估，并按以下格式输出：总分(1-10分)|各项得分详情|优点|改进建议。",
                        "enabled": True,
                        "default_params": {
                            "language": "Python",
                            "difficulty": "中等",
                            "topic": "算法"
                        }
                    }
                ]
            }
            with open(self.skills_path, "w", encoding="utf-8") as f:
                json.dump(default_skills, f, ensure_ascii=False, indent=2)
    
    def load_skills(self) -> List[Dict[str, Any]]:
        """加载所有技能"""
        try:
            with open(self.skills_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("skills", [])
        except Exception as e:
            logger.error(f"加载技能库失败：{e}")
            return []
    
    def save_skills(self, skills: List[Dict[str, Any]]) -> bool:
        """保存技能列表"""
        try:
            data = {"skills": skills}
            with open(self.skills_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"保存技能库失败：{e}")
            return False
    
    def get_skill_by_id(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取技能"""
        all_skills = self.load_skills()
        for skill in all_skills:
            if skill["skill_id"] == skill_id:
                return skill
        return None
    
    def get_enabled_skills(self) -> List[Dict[str, Any]]:
        """获取所有启用的技能"""
        all_skills = self.load_skills()
        return [skill for skill in all_skills if skill.get("enabled", True)]
    
    def add_custom_skill(self, name: str, display_name: str, description: str, 
                        generate_prompt: str, evaluate_prompt: str, 
                        atomic_skills: List[str] = None, default_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        添加自定义技能
        :param name: 技能名称（英文标识）
        :param display_name: 显示名称
        :param description: 技能描述
        :param generate_prompt: 生成内容的提示词模板
        :param evaluate_prompt: 评估内容的提示词模板
        :param atomic_skills: 关联的原子技能ID列表
        :param default_params: 默认参数
        :return: 添加的技能信息
        """
        # 检查技能是否已存在
        all_skills = self.load_skills()
        existing_skill = next((s for s in all_skills if s["name"] == name), None)
        if existing_skill:
            logger.warning(f"技能已存在：{name}")
            return existing_skill
        
        # 如果未提供原子技能，尝试自动匹配
        if not atomic_skills:
            atomic_skills = []
            similar_skills = atomic_skill_manager.find_similar_atomic_skills(description)
            if similar_skills:
                atomic_skills = [skill["atomic_skill_id"] for skill in similar_skills[:3]]  # 最多匹配前3个
            else:
                # 如果没有找到相似技能，使用通用技能
                atomic_skills = ["as_001", "as_003"]  # 内容准确性、表达清晰度
        
        # 生成唯一ID
        skill_id = f"skill_{name.lower()}"
        
        new_skill = {
            "skill_id": skill_id,
            "name": name,
            "display_name": display_name,
            "description": description,
            "atomic_skills": atomic_skills,
            "generate_prompt": generate_prompt,
            "evaluate_prompt": evaluate_prompt,
            "enabled": True,
            "default_params": default_params or {}
        }
        
        all_skills.append(new_skill)
        
        if self.save_skills(all_skills):
            logger.info(f"新增自定义技能成功：{name}")
            return new_skill
        else:
            logger.error(f"新增自定义技能失败：{name}")
            return {}
    
    def update_skill(self, skill_id: str, updates: Dict[str, Any]) -> bool:
        """更新技能信息"""
        all_skills = self.load_skills()
        for i, skill in enumerate(all_skills):
            if skill["skill_id"] == skill_id:
                all_skills[i].update(updates)
                return self.save_skills(all_skills)
        return False
    
    def enable_skill(self, skill_id: str) -> bool:
        """启用技能"""
        return self.update_skill(skill_id, {"enabled": True})
    
    def disable_skill(self, skill_id: str) -> bool:
        """禁用技能"""
        return self.update_skill(skill_id, {"enabled": False})
    
    def delete_skill(self, skill_id: str) -> bool:
        """删除技能"""
        all_skills = self.load_skills()
        filtered_skills = [skill for skill in all_skills if skill["skill_id"] != skill_id]
        if len(filtered_skills) != len(all_skills):
            return self.save_skills(filtered_skills)
        return False
    
    def generate_skill_content(self, skill_id: str, **params) -> Dict[str, Any]:
        """
        为指定技能生成内容
        :param skill_id: 技能ID
        :param params: 生成所需的参数
        :return: 生成的内容，包含title、description、hint、example_answer、category和difficulty字段
        """
        
        skill = self.get_skill_by_id(skill_id)
        if not skill:
            logger.error(f"技能不存在：{skill_id}")
            # 返回默认内容
            return {
                "title": f"{skill_id}练习",
                "description": "请完成相关练习",
                "hint": "加油！你可以的！",
                "example_answer": "这是一个参考答案示例。你可以根据自己的理解进行回答。",
                "category": "通用",
                "difficulty": params.get("difficulty", "入门")
            }
        
        # 获取难度参数
        difficulty = params.get("difficulty", skill.get("default_params", {}).get("difficulty", "入门"))
        
        # 尝试使用技能的generate_prompt模板生成内容
        prompt_template = skill.get("generate_prompt")
        if prompt_template:
            # 合并默认参数
            default_params = skill.get("default_params", {})
            all_params = {**default_params, **params}
            
            # 自动添加target_skill_name参数
            all_params['target_skill_name'] = skill['display_name']
            
            try:
                # 构造专门用于生成完整练习内容的提示词
                enhanced_prompt = f"""
                你是闪练AI的碎片化技能教练，负责根据以下提示词生成完整的练习内容：
                
                {prompt_template}
                
                请根据上述提示词，生成一个完整的练习内容，包含以下部分：
                1. title：一个简洁明了的练习标题
                2. description：详细的练习描述，包括练习目标、要求和背景信息
                3. hint：一个实用的提示，帮助用户完成练习
                4. example_answer：一个高质量的参考答案，展示如何完成这个练习
                5. category：技能类别，使用技能的名称
                
                严格按照以下JSON格式返回，不要添加任何额外内容：
                {{
                    "title": "练习标题",
                    "description": "练习描述",
                    "hint": "提示信息",
                    "example_answer": "参考答案",
                    "category": "{skill.get('name', '通用')}"
                }}
                """
                
                generated_content = universal_ai_evaluator.generate_content(
                    skill_name=skill["display_name"],
                    prompt_template=enhanced_prompt,
                    **all_params
                )
                
                # 尝试解析生成的内容为JSON
                import json
                try:
                    if not generated_content:
                        # 如果生成的内容为空，使用默认值
                        logger.warning(f"自定义prompt生成的内容为空")
                        return {
                            "title": f"{skill['display_name']}练习",
                            "description": skill.get("description", "请完成相关练习"),
                            "hint": "加油！你可以的！",
                            "example_answer": "这是一个参考答案示例。你可以根据自己的理解进行回答。",
                            "category": skill.get("name", "通用"),
                            "difficulty": difficulty
                        }
                    
                    result = json.loads(generated_content)
                    # 确保返回结构完整
                    return {
                        "title": result.get("title", f"{skill['display_name']}练习"),
                        "description": result.get("description", skill.get("description", "请完成相关练习")),
                        "hint": result.get("hint", "加油！你可以的！"),
                        "example_answer": result.get("example_answer", "这是一个参考答案示例。你可以根据自己的理解进行回答。"),
                        "category": result.get("category", skill.get("name", "通用")),
                        "difficulty": difficulty
                    }
                except json.JSONDecodeError:
                    # 如果解析失败，使用生成的内容作为标题，其他字段使用默认值
                    logger.warning(f"自定义prompt生成的内容不是有效的JSON：{generated_content}")
                    return {
                        "title": generated_content or f"{skill['display_name']}练习",
                        "description": skill.get("description", "请完成相关练习"),
                        "hint": "加油！你可以的！",
                        "example_answer": "这是一个参考答案示例。你可以根据自己的理解进行回答。",
                        "category": skill.get("name", "通用"),
                        "difficulty": difficulty
                    }
            except Exception as e:
                logger.error(f"使用自定义prompt生成内容失败：{e}")
                # 失败后使用默认方法
        
        # 如果没有generate_prompt模板或生成失败，为自定义技能生成专属内容
        # 构造专门针对该技能的提示词
        custom_prompt_messages = [
            {
                "role": "system",
                "content": f"""
                你是闪练AI的碎片化技能教练，负责为以下技能生成1-5分钟可完成的练习内容：
                
                技能名称：{skill.get('display_name', '自定义技能')}
                技能描述：{skill.get('description', '无描述')}
                难度：{difficulty}
                
                要求：
                1. 生成一个具体的练习标题（title），与技能内容相关
                2. 生成详细的练习描述（description），包括练习目标、要求和背景信息
                3. 生成一个实用的提示（hint），帮助用户完成练习
                4. 生成一个高质量的参考答案（example_answer），展示如何完成这个练习
                5. 严格按照以下JSON格式返回，不要添加任何额外内容：
                {{
                    "title": "练习标题",
                    "description": "练习描述",
                    "hint": "提示信息",
                    "example_answer": "参考答案",
                    "category": "{skill.get('name', '通用')}"
                }}
                6. description可以包含HTML格式，但不要使用复杂的标签
                """
            },
            {"role": "user", "content": "生成符合要求的练习内容，严格按照指定的JSON格式返回"}
        ]
        
        try:
            from core.ai import get_doubao_client
            doubao_client = get_doubao_client()
            content = doubao_client.think(custom_prompt_messages, temperature=0.8, max_length=None, is_json=True)
            
            import json
            
            if not content:
                # 如果生成的内容为空，使用默认值
                logger.warning(f"豆包客户端生成的内容为空")
                return {
                    "title": f"{skill['display_name']}练习",
                    "description": skill.get("description", "请完成相关练习"),
                    "hint": "加油！你可以的！",
                    "example_answer": "这是一个参考答案示例。你可以根据自己的理解进行回答。",
                    "category": skill.get("name", "通用"),
                    "difficulty": difficulty
                }
            
            result = json.loads(content)
            
            # 确保返回结构完整
            return {
                "title": result.get("title", f"{skill['display_name']}练习"),
                "description": result.get("description", skill.get("description", "请完成相关练习")),
                "hint": result.get("hint", "加油！你可以的！"),
                "example_answer": result.get("example_answer", "这是一个参考答案示例。你可以根据自己的理解进行回答。"),
                "category": result.get("category", skill.get("name", "通用")),
                "difficulty": difficulty
            }
        except Exception as e:
            logger.error(f"为自定义技能生成内容失败：{e}")
            # 最后使用默认方法
            practice_content = generate_practice_content(skill_id, difficulty)
            
            # 确保返回结构完整，适配前端需求
            return {
                "title": practice_content.get("title", f"{skill['display_name']}练习"),
                "description": practice_content.get("description", skill.get("description", "请完成相关练习")),
                "hint": practice_content.get("hint", "加油！你可以的！"),
                "example_answer": practice_content.get("example_answer", "这是一个参考答案示例。你可以根据自己的理解进行回答。"),
                "category": practice_content.get("category", skill.get("name", "通用")),
                "difficulty": practice_content.get("difficulty", difficulty)
            }
    
    def evaluate_skill_content(self, skill_id: str, content: str, reference: str = "", **params) -> Dict[str, Any]:
        """
        评估指定技能的内容
        :param skill_id: 技能ID
        :param content: 待评估内容
        :param reference: 参考信息（如原始问题）
        :param params: 评估所需的参数
        :return: 评估结果
        """
        skill = self.get_skill_by_id(skill_id)
        if not skill:
            logger.error(f"技能不存在：{skill_id}")
            return universal_ai_evaluator._get_default_evaluation_result("未知技能")
        
        # 合并默认参数
        default_params = skill.get("default_params", {})
        all_params = {**default_params, **params}
        
        # 自动添加target_skill_name参数
        all_params['target_skill_name'] = skill['display_name']
        
        # 调试日志：输出技能信息
        logger.info(f"技能库管理器 - 技能ID: {skill_id}")
        logger.info(f"技能库管理器 - 技能名称: {skill['display_name']}")
        logger.info(f"技能库管理器 - 待评估内容: {content}")
        logger.info(f"技能库管理器 - 参考信息: {reference}")
        
        # 尝试使用多智能体评估（不传递prompt_template）
        result = universal_ai_evaluator.evaluate_content(
            skill_name=skill["display_name"],
            content=content,
            reference=reference,  # 传递原始问题作为参考
            **all_params
        )
        
        # 如果是通用评估（非多智能体），则使用技能的评估模板
        if result.get("details") == "从评估结果中提取信息" or "评估失败" in result.get("details", ""):
            prompt_template = skill["evaluate_prompt"]
            logger.info(f"技能库管理器 - 使用技能评估模板: {prompt_template}")
            
            result = universal_ai_evaluator.evaluate_content(
                skill_name=skill["display_name"],
                content=content,
                reference=reference,  # 传递原始问题作为参考
                prompt_template=prompt_template,
                **all_params
            )
        
        return result


def generate_practice_content(skill_id: str, difficulty: str = "入门") -> dict:
    """
    根据skill_id生成相关的练习内容
    返回格式：{"title": "练习标题", "description": "练习描述", "hint": "提示信息", "category": "技能类型"}
    """
    # 获取技能类型
    skill_type = skill_id.split("_")[0]
    
    # 1. 构造豆包AI的对话消息
    if skill_type == "speech":
        prompt_messages = [
            {
                "role": "system",
                "content": f"""
                你是闪练AI的碎片化技能教练，负责生成1-5分钟可完成的即兴演讲练习内容。
                技能ID：{skill_id}
                难度：{difficulty}
                要求：
                1. 生成一个具体的演讲主题（title），简洁明了，适合30秒-1分钟演讲
                2. 生成详细的练习描述（description），包括练习目标、要求和背景信息
                3. 生成一个实用的提示（hint），帮助用户完成练习
                4. 生成一个高质量的参考答案（example_answer），展示如何回答这个问题
                   要求参考答案内容贴合主题，表达流畅，结构完整
                5. 严格按照以下JSON格式返回，不要添加任何额外内容：
                {{
                    "title": "演讲主题",
                    "description": "练习描述",
                    "hint": "提示信息",
                    "example_answer": "参考答案",
                    "category": "演讲"
                }}
                6. description可以包含HTML格式，但不要使用复杂的标签
                """
            },
            {"role": "user", "content": "生成符合要求的演讲练习内容，严格按照指定的JSON格式返回"}
        ]
    elif skill_type == "interview":
        prompt_messages = [
            {
                "role": "system",
                "content": f"""
                你是闪练AI的碎片化技能教练，负责生成1-5分钟可完成的面试模拟练习内容。
                技能ID：{skill_id}
                难度：{difficulty}
                要求：
                1. 生成一个具体的面试问题（title），清晰明确
                2. 生成详细的练习描述（description），包括问题背景、回答要求和考察点
                3. 生成一个实用的提示（hint），帮助用户完成练习
                4. 生成一个高质量的参考答案（example_answer），展示如何回答这个面试问题
                   要求参考答案岗位匹配，表达流畅，逻辑清晰
                5. 严格按照以下JSON格式返回，不要添加任何额外内容：
                {{
                    "title": "面试问题",
                    "description": "练习描述",
                    "hint": "提示信息",
                    "example_answer": "参考答案",
                    "category": "面试"
                }}
                6. description可以包含HTML格式，但不要使用复杂的标签
                """
            },
            {"role": "user", "content": "生成符合要求的面试模拟练习内容，严格按照指定的JSON格式返回"}
        ]
    elif skill_type == "code":
        prompt_messages = [
            {
                "role": "system",
                "content": f"""
                你是闪练AI的碎片化技能教练，负责生成1-5分钟可完成的代码反馈练习内容。
                技能ID：{skill_id}
                难度：{difficulty}
                要求：
                1. 生成一个具体的代码问题（title），简洁明了
                2. 生成详细的练习描述（description），包括问题要求、输入输出格式和代码示例
                3. 生成一个实用的提示（hint），帮助用户完成练习
                4. 生成一个高质量的参考答案（example_answer），展示如何解决这个代码问题
                   要求参考答案代码准确，逻辑清晰，可运行性强
                5. 严格按照以下JSON格式返回，不要添加任何额外内容：
                {{
                    "title": "代码问题",
                    "description": "练习描述",
                    "hint": "提示信息",
                    "example_answer": "参考答案",
                    "category": "代码"
                }}
                6. description可以包含HTML格式，但不要使用复杂的标签
                """
            },
            {"role": "user", "content": "生成符合要求的代码反馈练习内容，严格按照指定的JSON格式返回"}
        ]
    else:
        # 默认生成通用练习内容
        prompt_messages = [
            {
                "role": "system",
                "content": f"""
                你是闪练AI的碎片化技能教练，负责生成1-5分钟可完成的练习内容。
                技能ID：{skill_id}
                难度：{difficulty}
                要求：
                1. 生成一个具体的练习标题（title），简洁明了
                2. 生成详细的练习描述（description），包括练习目标、要求和背景信息
                3. 生成一个实用的提示（hint），帮助用户完成练习
                4. 生成一个高质量的参考答案（example_answer），展示如何完成这个练习
                5. 严格按照以下JSON格式返回，不要添加任何额外内容：
                {{
                    "title": "练习标题",
                    "description": "练习描述",
                    "hint": "提示信息",
                    "example_answer": "参考答案",
                    "category": "通用"
                }}
                6. description可以包含HTML格式，但不要使用复杂的标签
                """
            },
            {"role": "user", "content": "生成符合要求的练习内容，严格按照指定的JSON格式返回"}
        ]

    try:
        doubao_client = get_doubao_client()
        content = doubao_client.think(prompt_messages, temperature=0.8, max_length=None, is_json=True)

        if not content:
            # 如果生成的内容为空，直接返回默认内容
            print(f"生成练习内容失败：内容为空")
            return {
                "title": f"{skill_id}练习",
                "description": "请完成相关练习",
                "hint": "加油！你可以的！",
                "example_answer": "这是一个参考答案示例。你可以根据自己的理解进行回答。",
                "category": "通用",
                "difficulty": difficulty
            }

        result = json.loads(content)
        
        # 空值降级
        if not result.get("title"):
            result["title"] = f"{skill_id}练习"
        if not result.get("description"):
            result["description"] = "请完成相关练习"
        if not result.get("hint"):
            result["hint"] = "加油！你可以的！"
        if not result.get("example_answer"):
            result["example_answer"] = "这是一个参考答案示例。你可以根据自己的理解进行回答。"
        if not result.get("category"):
            result["category"] = "通用"

        # 添加默认的difficulty
        result["difficulty"] = difficulty

        return result

    except Exception as e:
        print(f"生成练习内容失败：{str(e)}")
        # 返回默认内容
        return {
            "title": f"{skill_id}练习",
            "description": "请完成相关练习",
            "hint": "加油！你可以的！",
            "example_answer": "这是一个参考答案示例。你可以根据自己的理解进行回答。",
            "category": "通用",
            "difficulty": difficulty
        }


# 全局实例
skill_library_manager = SkillLibraryManager()