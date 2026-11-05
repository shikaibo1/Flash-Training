# core/skill/custom_skill_creator.py
from typing import Dict, Any
import json
import re
from core.ai.universal_ai_evaluator import UniversalAIEvaluator
from core.skill.skill_library_manager import skill_library_manager
from utils.logger import logger


class CustomSkillCreator:
    """
    自定义技能创建器
    用户只需输入技能名称，AI自动生成相关提示词和其他配置
    """

    def __init__(self):
        self.ai_evaluator = UniversalAIEvaluator()

    def create_custom_skill_from_name(self, skill_name: str) -> Dict[str, Any]:
        """
        根据技能名称创建自定义技能
        :param skill_name: 用户输入的技能名称
        :return: 创建的技能信息
        """
        try:
            # 修改模板中的占位符，避免与方法参数冲突
            description_template = "请为{target_skill_name}技能提供一个简洁准确的描述，说明这个技能的作用和用途。只需输出描述，不要其他内容。"
            skill_description = self.ai_evaluator.generate_content(
                skill_name="技能描述生成",
                prompt_template=description_template,
                target_skill_name=skill_name
            )

            # 如果AI描述生成失败，使用默认描述
            if skill_description is None:
                skill_description = f"提升{skill_name}相关技能的练习模块"

            # AI生成生成提示词模板
            generate_prompt_template = """你是{target_skill_name}教练，请生成一个适合练习的{target_skill_name}主题或任务，要求：
场景：{{scene}}，
难度：{{difficulty}}，
时长：{{duration}}，
关键词：{{keyword}}。

只需输出具体的练习主题或任务，无需其他内容。"""

            # AI生成评估提示词模板
            evaluate_prompt_template = """你是{target_skill_name}专家，评估以下{target_skill_name}内容：

{target_skill_name}内容：{{content}}

要求：从内容准确性、结构完整性、表达清晰度、{target_skill_name}专业性等方面进行评估，
并按以下格式输出：总分(1-10分)|各项得分详情|优点|改进建议。"""

            # 尝试AI生成默认参数，如果失败使用默认值
            default_params = {
                "scene": "通用",
                "difficulty": "中等",
                "duration": "5分钟",
                "keyword": ""
            }

            try:
                default_params_template = """请为{target_skill_name}技能推荐合适的默认参数，以JSON格式输出：
{
  "scene": "默认场景",
  "difficulty": "默认难度",
  "duration": "默认时长",
  "keyword": "默认关键词"
}

只需要输出JSON，不要其他内容。"""

                default_params_raw = self.ai_evaluator.generate_content(
                    skill_name="参数生成",
                    prompt_template=default_params_template,
                    target_skill_name=skill_name
                )

                if default_params_raw:
                    json_match = re.search(r'\{.*\}', default_params_raw, re.DOTALL)
                    if json_match:
                        default_params = json.loads(json_match.group())
            except Exception as e:
                logger.warning(f"参数生成失败，使用默认参数: {e}")

            # 创建技能显示名称
            display_name = f"{skill_name}技能练习"

            # 为新技能分解出新的原子技能
            atomic_skills_recommendation = self._decompose_skill_to_atomic_skills(skill_name, skill_description)

            # 添加到技能库
            custom_skill = skill_library_manager.add_custom_skill(
                name=skill_name.replace(" ", "_").replace("-", "_").lower(),
                display_name=display_name,
                description=skill_description,
                generate_prompt=generate_prompt_template,
                evaluate_prompt=evaluate_prompt_template,
                atomic_skills=atomic_skills_recommendation,
                default_params=default_params
            )

            logger.info(f"自定义技能创建成功: {skill_name}")
            return {
                "success": True,
                "skill": custom_skill,
                "message": f"{skill_name}技能创建成功"
            }

        except Exception as e:
            logger.error(f"自定义技能创建失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"创建{skill_name}技能时发生错误"
            }

    def _decompose_skill_to_atomic_skills(self, skill_name: str, skill_description: str) -> list:
        """
        将技能分解为多个原子技能
        :param skill_name: 技能名称
        :param skill_description: 技能描述
        :return: 原子技能ID列表
        """
        from core.skill.atomic_skill_manager import atomic_skill_manager

        # 使用AI将技能分解为多个原子技能
        decomposition_prompt = f"""
        请将{skill_name}技能分解为3-5个基本的原子技能评估维度。
        每个原子技能应代表{skill_name}技能的一个核心评估方面。

        请按以下JSON格式输出：
        [
          {{
            "name": "原子技能名称",
            "description": "原子技能详细描述",
            "category": "{skill_name}相关"
          }},
          {{
            "name": "原子技能名称",
            "description": "原子技能详细描述",
            "category": "{skill_name}相关"
          }}
        ]

        重要：只输出JSON数组，不要其他解释或文字。
        """

        try:
            logger.info(f"正在将技能'{skill_name}'分解为原子技能...")
            ai_response = self.ai_evaluator.generate_content(
                skill_name="技能分解",
                prompt_template=decomposition_prompt
            )

            logger.debug(f"AI技能分解响应: {ai_response}")

            if ai_response:
                # 尝试提取JSON
                json_match = re.search(r'\[.*?\]', ai_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    try:
                        atomic_skills_data = json.loads(json_str)

                        atomic_skill_ids = []
                        for atomic_skill in atomic_skills_data:
                            name = atomic_skill.get('name', '').strip()
                            description = atomic_skill.get('description', '').strip()
                            category = atomic_skill.get('category', f'{skill_name}相关')

                            if name and description:
                                # 检查是否与现有原子技能相似（防止重复创建）
                                similar_existing = atomic_skill_manager.find_similar_atomic_skills(description,
                                                                                                   threshold=0.8)

                                if similar_existing:
                                    # 如果存在相似的原子技能，使用现有的
                                    logger.info(f"发现相似原子技能，使用现有技能替代: {similar_existing[0]['name']}")
                                    atomic_skill_ids.append(similar_existing[0]['atomic_skill_id'])
                                else:
                                    # 创建新的原子技能
                                    new_atomic_skill = atomic_skill_manager.add_atomic_skill(
                                        name=name,
                                        description=description,
                                        categories=[category]
                                    )
                                    if new_atomic_skill:
                                        atomic_skill_ids.append(new_atomic_skill['atomic_skill_id'])

                        if atomic_skill_ids:
                            logger.info(f"成功分解技能为原子技能IDs: {atomic_skill_ids}")
                            return atomic_skill_ids
                        else:
                            logger.warning("AI分解未产生有效的原子技能，使用通用技能")
                    except json.JSONDecodeError as e:
                        logger.warning(f"AI分解的原子技能JSON格式无效: {e}")
                        logger.debug(f"AI响应内容: {ai_response}")
                else:
                    logger.warning(f"未能从AI响应中提取JSON: {ai_response}")
            else:
                logger.warning("AI分解技能失败，AI返回空响应")

        except Exception as e:
            logger.error(f"技能分解过程中出错: {e}")

        # 如果AI分解失败，尝试基于技能名称生成通用原子技能
        logger.info("尝试基于技能名称生成原子技能...")
        return self._generate_atomic_skills_by_name(skill_name)

    def _generate_atomic_skills_by_name(self, skill_name: str) -> list:
        """
        基于技能名称生成原子技能
        :param skill_name: 技能名称
        :return: 原子技能ID列表
        """
        from core.skill.atomic_skill_manager import atomic_skill_manager

        # 为技能生成标准的评估维度
        default_atomic_skills = [
            {
                "name": f"{skill_name}基础",
                "description": f"{skill_name}技能的基础要求和核心要素",
                "category": skill_name
            },
            {
                "name": f"{skill_name}进阶",
                "description": f"{skill_name}技能的进阶能力和高级技巧",
                "category": skill_name
            },
            {
                "name": f"{skill_name}实践",
                "description": f"{skill_name}技能的实际应用和效果",
                "category": skill_name
            }
        ]

        atomic_skill_ids = []
        for atomic_skill in default_atomic_skills:
            name = atomic_skill['name']
            description = atomic_skill['description']
            category = atomic_skill['category']

            # 检查是否与现有原子技能相似
            similar_existing = atomic_skill_manager.find_similar_atomic_skills(description, threshold=0.8)

            if similar_existing:
                # 如果存在相似的原子技能，使用现有的
                logger.info(f"发现相似原子技能，使用现有技能替代: {similar_existing[0]['name']}")
                atomic_skill_ids.append(similar_existing[0]['atomic_skill_id'])
            else:
                # 创建新的原子技能
                new_atomic_skill = atomic_skill_manager.add_atomic_skill(
                    name=name,
                    description=description,
                    categories=[category]
                )
                if new_atomic_skill:
                    atomic_skill_ids.append(new_atomic_skill['atomic_skill_id'])

        if atomic_skill_ids:
            logger.info(f"基于技能名称生成的原子技能IDs: {atomic_skill_ids}")
            return atomic_skill_ids

        # 如果都失败了，返回通用技能
        logger.info("返回通用原子技能")
        return ["as_001", "as_003"]  # 内容准确性、表达清晰度


# 创建全局实例
custom_skill_creator = CustomSkillCreator()