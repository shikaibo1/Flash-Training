# core/ai/universal_ai_evaluator.py
from typing import Dict, Any, List, Optional
from core.ai.doubao_client import get_doubao_client
from utils.logger import logger
import json
import re
import traceback


# 不同技能类型的多智能体配置
SKILL_AGENT_CONFIGS = {
    "演讲": [
        {
            "agent_name": "演讲内容专家",
            "score_dimension": "内容贴合度",
            "prompt_template": """
            你是演讲内容专家，评价用户演讲内容（1-10分）：
            待评估内容：{content}
            参考信息：{reference}
            要求：仅输出「评分（1-10分）|优点|改进点」，各部分用|分隔，优点/改进点简洁（各1-2句话）
            """
        },
        {
            "agent_name": "表达流畅度专家",
            "score_dimension": "表达流畅度",
            "prompt_template": """
            你是表达流畅度专家，评价用户演讲内容（1-10分）：
            待评估内容：{content}
            参考信息：{reference}
            要求：仅输出「评分（1-10分）|优点|改进点」，各部分用|分隔，优点/改进点简洁（各1-2句话）
            """
        },
        {
            "agent_name": "结构逻辑专家",
            "score_dimension": "结构完整性",
            "prompt_template": """
            你是演讲结构专家，评价用户演讲内容（1-10分）：
            待评估内容：{content}
            参考信息：{reference}
            要求：仅输出「评分（1-10分）|优点|改进点」，各部分用|分隔，优点/改进点简洁（各1-2句话）
            """
        }
    ],
    "编程": [
        {
            "agent_name": "代码质量专家",
            "score_dimension": "代码质量",
            "prompt_template": """
            你是代码质量专家，评价用户代码（1-10分）：
            待评估内容：{content}
            参考信息：{reference}
            要求：仅输出「评分（1-10分）|优点|改进点」，各部分用|分隔，优点/改进点简洁（各1-2句话）
            """
        },
        {
            "agent_name": "逻辑正确性专家",
            "score_dimension": "逻辑正确性",
            "prompt_template": """
            你是逻辑正确性专家，评价用户代码（1-10分）：
            待评估内容：{content}
            参考信息：{reference}
            要求：仅输出「评分（1-10分）|优点|改进点」，各部分用|分隔，优点/改进点简洁（各1-2句话）
            """
        },
        {
            "agent_name": "性能优化专家",
            "score_dimension": "性能优化",
            "prompt_template": """
            你是性能优化专家，评价用户代码（1-10分）：
            待评估内容：{content}
            参考信息：{reference}
            要求：仅输出「评分（1-10分）|优点|改进点」，各部分用|分隔，优点/改进点简洁（各1-2句话）
            """
        }
    ],
    "面试": [
        {
            "agent_name": "回答内容专家",
            "score_dimension": "内容质量",
            "prompt_template": """
            你是面试回答内容专家，评价用户回答（1-10分）：
            待评估内容：{content}
            参考信息：{reference}
            要求：仅输出「评分（1-10分）|优点|改进点」，各部分用|分隔，优点/改进点简洁（各1-2句话）
            """
        },
        {
            "agent_name": "表达能力专家",
            "score_dimension": "表达能力",
            "prompt_template": """
            你是表达能力专家，评价用户回答（1-10分）：
            待评估内容：{content}
            参考信息：{reference}
            要求：仅输出「评分（1-10分）|优点|改进点」，各部分用|分隔，优点/改进点简洁（各1-2句话）
            """
        },
        {
            "agent_name": "专业度专家",
            "score_dimension": "专业度",
            "prompt_template": """
            你是专业度专家，评价用户回答（1-10分）：
            待评估内容：{content}
            参考信息：{reference}
            要求：仅输出「评分（1-10分）|优点|改进点」，各部分用|分隔，优点/改进点简洁（各1-2句话）
            """
        }
    ]
}


class UniversalAIEvaluator:
    """
    通用AI评估器，可根据不同技能类型和提示词进行工作
    """
    
    def __init__(self):
        self.client = get_doubao_client()
    
    def generate_content(self, skill_name: str, prompt_template: str, **kwargs) -> Optional[str]:
        """
        通用内容生成功能
        :param skill_name: 技能名称
        :param prompt_template: 提示词模板
        :param kwargs: 模板中使用的参数
        :return: 生成的内容
        """
        try:
            # 安全地格式化提示词，只替换存在的占位符
            formatted_prompt = prompt_template
            placeholders = re.findall(r'\{([^}]+)\}', prompt_template)
            
            for placeholder in placeholders:
                if placeholder in kwargs:
                    formatted_prompt = formatted_prompt.replace(
                        f'{{{placeholder}}}', str(kwargs[placeholder])
                    )
            
            # 替换掉所有未被替换的占位符（防止出现{target_skill_name}这样的错误）
            formatted_prompt = re.sub(r'\{[^}]+\}', '', formatted_prompt)
            
            messages = [
                {"role": "system", "content": f"你是专业的{skill_name}教练"},
                {"role": "user", "content": formatted_prompt}
            ]
            
            response = self.client.think(messages, temperature=0.8, is_json=True)
            
            if not response:
                logger.warning(f"{skill_name}内容生成失败")
                return None
                
            return response.strip()
            
        except Exception as e:
            logger.error(f"{skill_name}内容生成出错: {str(e)}")
            return None
    
    def evaluate_content(self, skill_name: str, content: str, reference: str = "", criteria: List[str] = None, 
                         prompt_template: str = None, **kwargs) -> Dict[str, Any]:
        """
        通用内容评估功能
        :param skill_name: 技能名称
        :param content: 待评估内容
        :param reference: 参考内容（如题目、标准答案等）
        :param criteria: 评估标准列表
        :param prompt_template: 自定义评估提示词模板
        :param kwargs: 其他参数
        :return: 评估结果字典
        """
        try:
            # 调试日志：输出AI接收的内容
            logger.info(f"AI评估接收 - 技能名称: {skill_name}")
            logger.info(f"AI评估接收 - 待评估内容: {content}")
            logger.info(f"AI评估接收 - 参考信息: {reference}")
            
            # 检查是否有针对该技能的多智能体配置
            skill_type = self._get_skill_type(skill_name)
            logger.info(f"AI评估 - 技能类型: {skill_type}")
            
            if skill_type in SKILL_AGENT_CONFIGS and not prompt_template:
                # 使用多智能体评估
                logger.info(f"AI评估 - 使用多智能体评估")
                return self._evaluate_with_multi_agents(skill_type, skill_name, content, reference, **kwargs)
            else:
                # 使用传统评估方法
                logger.info(f"AI评估 - 使用单智能体评估")
                return self._evaluate_with_single_agent(skill_name, content, reference, criteria, prompt_template, **kwargs)
            
        except Exception as e:
            logger.error(f"{skill_name}评估出错: {str(e)}")
            logger.error(traceback.format_exc())
            return self._get_default_evaluation_result(skill_name)
    
    def _get_skill_type(self, skill_name: str) -> str:
        """
        根据技能名称获取技能类型
        """
        skill_name_lower = skill_name.lower()
        # 更准确的技能类型识别
        if any(keyword in skill_name_lower for keyword in ["演讲", "speech", "演说", "表达"]):
            return "演讲"
        elif any(keyword in skill_name_lower for keyword in ["编程", "code", "编程技能", "代码", "coding"]):
            return "编程"
        elif any(keyword in skill_name_lower for keyword in ["面试", "interview", "面試"]):
            return "面试"
        return "通用"
    
    def _evaluate_with_multi_agents(self, skill_type: str, skill_name: str, content: str, reference: str, **kwargs) -> Dict[str, Any]:
        """
        使用多智能体进行评估
        """
        all_strengths = []
        all_improvements = []
        agent_scores = []
        agent_responses = []
        agent_details = []
        
        # 获取该技能类型的智能体配置
        agents = SKILL_AGENT_CONFIGS.get(skill_type, [])
        if not agents:
            logger.warning(f"技能类型 {skill_type} 没有配置智能体")
            return self._get_default_evaluation_result(skill_name)
        
        for agent in agents:
            try:
                # 安全地格式化提示词
                prompt = agent["prompt_template"].format(
                    content=content, 
                    reference=reference or "无"
                )
                
                # 调试日志：输出每个智能体的提示词
                logger.info(f"AI评估 - 智能体: {agent['agent_name']}")
                logger.info(f"AI评估 - 提示词: {prompt}")
                
                messages = [
                    {"role": "system", "content": f"你是专业的{agent['agent_name']}，专注于{agent['score_dimension']}评估"},
                    {"role": "user", "content": prompt}
                ]
                
                response = self.client.think(messages, temperature=0.1)
                
                # 调试日志：输出每个智能体的响应
                logger.info(f"AI评估 - 智能体响应: {agent['agent_name']} - {response}")
                
                # 解析响应
                score, strength, improvement = self._parse_agent_response(response, agent['agent_name'])
                
                agent_scores.append(score)
                all_strengths.append(f"{agent['agent_name']}（{agent['score_dimension']}）：{strength}")
                all_improvements.append(f"{agent['agent_name']}（{agent['score_dimension']}）：{improvement}")
                agent_responses.append(response)
                agent_details.append(f"{agent['agent_name']}({agent['score_dimension']}): {score}")
                
            except Exception as e:
                logger.error(f"{agent['agent_name']}评价失败：{e}")
                logger.error(traceback.format_exc())
                agent_scores.append(6.0)  # 异常默认6分
                all_strengths.append(f"{agent['agent_name']}（{agent['score_dimension']}）：内容基本达标")
                all_improvements.append(f"{agent['agent_name']}（{agent['score_dimension']}）：暂无法精准分析，建议优化细节")
                agent_responses.append("评估失败")
                agent_details.append(f"{agent['agent_name']}({agent['score_dimension']}): 6.0")
        
        # 计算平均分
        avg_score = round(sum(agent_scores) / len(agent_scores), 1) if agent_scores else 6.0
        
        # 过滤空值
        strengths = list(filter(None, all_strengths))
        improvements = list(filter(None, all_improvements))
        
        # 生成AI评论
        ai_comment = self._generate_ai_comment(skill_name, avg_score, strengths, improvements)
        
        # 构建结果
        result = {
            "score": avg_score,
            "strengths": strengths,
            "improvements": improvements,
            "details": f"多智能体评估结果：{', '.join(agent_details)}",
            "aiComment": ai_comment,
            "raw_response": f"多智能体评估：{agent_responses}",
            "evaluation_type": "multi-agent"
        }
        
        return result
    
    def _evaluate_with_single_agent(self, skill_name: str, content: str, reference: str, criteria: List[str], prompt_template: str, **kwargs) -> Dict[str, Any]:
        """
        使用单个智能体进行评估
        """
        try:
            # 如果没有提供自定义模板，则使用默认模板
            if not prompt_template:
                default_criteria = ", ".join(criteria) if criteria else "内容准确性、结构完整性、表达清晰度"
                prompt_template = f"""
                你是专业的{skill_name}评估专家，请评估以下{skill_name}内容：
                
                待评估内容：
                {content}
                
                参考信息：
                {reference}
                
                评估维度：
                {criteria}
                
                请按以下格式输出：
                总分(1-10分)|各项得分详情|优点|改进建议
                """
            else:
                # 如果提供了自定义模板，仍然需要设置default_criteria用于format操作
                default_criteria = ", ".join(criteria) if criteria else "内容准确性、结构完整性、表达清晰度"
            
            # 合并所有参数到一个字典中
            all_format_args = {
                'skill_name': skill_name,
                'content': content,
                'reference': reference,
                'criteria': default_criteria
            }
            all_format_args.update(kwargs)
            
            # 安全地格式化提示词，只替换存在的占位符
            formatted_prompt = prompt_template
            placeholders = re.findall(r'\{([^}]+)\}', prompt_template)
            
            for placeholder in placeholders:
                if placeholder in all_format_args:
                    formatted_prompt = formatted_prompt.replace(
                        f'{{{placeholder}}}', str(all_format_args[placeholder])
                    )
            
            # 替换掉所有未被替换的占位符（防止出现{target_skill_name}这样的错误）
            formatted_prompt = re.sub(r'\{[^}]+\}', '', formatted_prompt)
            
            # 调试日志：输出提示词
            logger.info(f"AI评估接收 - 提示词: {formatted_prompt}")
            
            messages = [
                {"role": "system", "content": f"你是专业的{skill_name}评估专家，提供客观、专业的评估"},
                {"role": "user", "content": formatted_prompt}
            ]
            
            response = self.client.think(messages, temperature=0.3)
            
            # 调试日志：输出AI返回的原始内容
            logger.info(f"AI评估返回 - 原始响应: {response}")
            
            if not response:
                logger.warning(f"{skill_name}评估失败 - 响应为空")
                return self._get_default_evaluation_result(skill_name)
            
            # 解析AI评估结果
            evaluation_result = self._parse_evaluation_result(response, skill_name)
            
            # 添加评估类型标识
            evaluation_result["evaluation_type"] = "single-agent"
            
            return evaluation_result
        except Exception as e:
            logger.error(f"单智能体评估失败: {str(e)}")
            logger.error(traceback.format_exc())
            result = self._get_default_evaluation_result(skill_name)
            result["evaluation_type"] = "single-agent"
            return result
    
    def _parse_agent_response(self, response: str, agent_name: str) -> tuple:
        """
        解析智能体响应
        :param response: 智能体返回的响应
        :param agent_name: 智能体名称
        :return: (score, strength, improvement) 元组
        """
        if not response:
            return 6.0, "内容基本达标", "暂无法精准分析，建议优化细节"
        
        # 清理响应内容
        response = response.strip()
        
        # 尝试按|分隔解析
        if "|" in response:
            parts = response.split("|", 2)
            if len(parts) >= 3:
                # 提取分数
                score_match = re.search(r"\d+(\.\d+)?", parts[0])
                score = float(score_match.group()) if score_match else 6.0
                
                strength = parts[1].strip() or "内容基本达标"
                improvement = parts[2].strip() or "暂无法精准分析，建议优化细节"
                
                return score, strength, improvement
        
        # 如果解析失败，尝试提取关键信息
        score_match = re.search(r"\d+(\.\d+)?", response)
        score = float(score_match.group()) if score_match else 6.0
        
        # 尝试提取优点和改进建议
        strength = "内容基本达标"
        improvement = "暂无法精准分析，建议优化细节"
        
        # 查找包含"优点"或"优势"的部分
        strengths_patterns = [
            r'(优点|优势)[：:](.*?)(?=(改进|不足|建议|$))',
            r'(优点|优势)[:：]\s*(.*?)(?=\n|$)',
            r'优点[:：]?(.*?)改进'
        ]
        
        for pattern in strengths_patterns:
            strengths_match = re.search(pattern, response, re.DOTALL)
            if strengths_match and len(strengths_match.groups()) > 1:
                strength_text = strengths_match.group(2).strip() if len(strengths_match.groups()) > 2 else strengths_match.group(1).strip()
                if strength_text:
                    strength = strength_text
                    break
        
        # 查找包含"改进"或"不足"或"建议"的部分
        improvements_patterns = [
            r'(改进|不足|建议)[：:](.*?)(?=(优点|优势|$))',
            r'(改进|不足|建议)[:：]\s*(.*?)(?=\n|$)',
            r'改进[:：]?(.*?)\n'
        ]
        
        for pattern in improvements_patterns:
            improvements_match = re.search(pattern, response, re.DOTALL)
            if improvements_match and len(improvements_match.groups()) > 1:
                improvement_text = improvements_match.group(2).strip() if len(improvements_match.groups()) > 2 else improvements_match.group(1).strip()
                if improvement_text:
                    improvement = improvement_text
                    break
        
        return score, strength, improvement
    
    def _parse_evaluation_result(self, raw_result: str, skill_name: str) -> Dict[str, Any]:
        """解析AI评估结果"""
        try:
            # 清理原始结果
            raw_result = raw_result.strip()
            
            # 尝试按分隔符解析结果
            parts = raw_result.split('|')
            if len(parts) >= 4:
                total_score = self._extract_score(parts[0])
                
                # 检查第二个部分是否包含原子技能得分详情
                details = parts[1].strip() if len(parts) > 1 else "无详细说明"
                atomic_skill_scores = self._extract_atomic_skill_scores(details)
                
                strengths = [parts[2].strip()] if len(parts) > 2 else ["待评估"]
                improvements = [parts[3].strip()] if len(parts) > 3 else ["待改进"]
                
                # 过滤空值
                strengths = list(filter(None, strengths))
                improvements = list(filter(None, improvements))
                
                # 如果没有找到优点和改进建议，使用默认值
                if not strengths:
                    strengths = [f"{skill_name}内容基本达标"]
                if not improvements:
                    improvements = [f"{skill_name}需要进一步优化"]
                
                ai_comment = self._generate_ai_comment(skill_name, total_score, strengths, improvements)
                
                result = {
                    "score": total_score,
                    "strengths": strengths,
                    "improvements": improvements,
                    "details": details,
                    "aiComment": ai_comment,
                    "raw_response": raw_result
                }
                
                # 如果解析到原子技能得分，则添加到结果中
                if atomic_skill_scores:
                    result["atomic_skill_scores"] = atomic_skill_scores
                
                return result
            else:
                # 尝试从原始文本中提取关键信息
                # 尝试提取分数
                score_match = re.search(r'\d+(\.\d+)?', raw_result)
                score = float(score_match.group()) if score_match else 6.0
                
                # 尝试提取优点和改进建议
                strengths = []
                improvements = []
                
                # 查找包含"优点"或"优势"的部分
                strengths_patterns = [
                    r'(优点|优势)[：:](.*?)(?=(改进|不足|建议|$))',
                    r'(优点|优势)[:：]\s*(.*?)(?=\n|$)',
                    r'优点[:：]?(.*?)改进'
                ]
                
                for pattern in strengths_patterns:
                    strengths_match = re.search(pattern, raw_result, re.DOTALL)
                    if strengths_match and len(strengths_match.groups()) > 1:
                        strength_text = strengths_match.group(2).strip() if len(strengths_match.groups()) > 2 else strengths_match.group(1).strip()
                        if strength_text:
                            strengths = [strength_text]
                            break
                
                # 查找包含"改进"或"不足"或"建议"的部分
                improvements_patterns = [
                    r'(改进|不足|建议)[：:](.*?)(?=(优点|优势|$))',
                    r'(改进|不足|建议)[:：]\s*(.*?)(?=\n|$)',
                    r'改进[:：]?(.*?)\n'
                ]
                
                for pattern in improvements_patterns:
                    improvements_match = re.search(pattern, raw_result, re.DOTALL)
                    if improvements_match and len(improvements_match.groups()) > 1:
                        improvement_text = improvements_match.group(2).strip() if len(improvements_match.groups()) > 2 else improvements_match.group(1).strip()
                        if improvement_text:
                            improvements = [improvement_text]
                            break
                
                # 如果没有找到优点和改进建议，使用默认值
                if not strengths:
                    strengths = [f"{skill_name}内容基本达标"]
                if not improvements:
                    improvements = [f"{skill_name}需要进一步优化"]
                
                ai_comment = self._generate_ai_comment(skill_name, score, strengths, improvements)
                
                # 如果解析失败，使用提取的信息或原始内容作为评论
                return {
                    "score": score,
                    "strengths": strengths,
                    "improvements": improvements,
                    "details": "从评估结果中提取信息",
                    "aiComment": ai_comment,
                    "raw_response": raw_result
                }
        except Exception as e:
            logger.error(f"解析{skill_name}评估结果失败: {str(e)}")
            logger.error(traceback.format_exc())
            result = self._get_default_evaluation_result(skill_name)
            result["raw_response"] = raw_result
            return result
    
    def _generate_ai_comment(self, skill_name: str, score: float, strengths: List[str], improvements: List[str]) -> str:
        """
        生成AI评论
        :param skill_name: 技能名称
        :param score: 评分
        :param strengths: 优点列表
        :param improvements: 改进点列表
        :return: AI评论
        """
        # 根据分数生成不同的评论语气
        if score >= 9:
            tone = "优秀"
        elif score >= 7:
            tone = "良好"
        elif score >= 5:
            tone = "一般"
        else:
            tone = "需要努力"
        
        # 生成优点部分
        strengths_text = "; ".join(strengths) if strengths else "内容基本达标"
        
        # 生成改进部分
        improvements_text = "; ".join(improvements) if improvements else "需要进一步优化"
        
        # 生成评论
        comment = f"本次{skill_name}练习综合评分为{score}分，表现{tone}。核心优点：{strengths_text}；改进方向：{improvements_text}。"
        
        return comment
    
    def _extract_score(self, score_text: str) -> float:
        """从文本中提取分数"""
        try:
            # 查找数字（支持整数和小数）
            match = re.search(r'(\d+\.?\d*)', score_text)
            if match:
                score = float(match.group(1))
                return min(max(score, 0), 10)  # 限制在0-10分范围内
            return 6.0  # 默认分数
        except:
            return 6.0

    def _extract_atomic_skill_scores(self, details: str) -> Dict[str, float]:
        """从详情中提取原子技能得分"""
        try:
            # 查找原子技能得分模式，例如: as_001:8分,as_002:7分,as_003:9分
            pattern = r'(as_\d+):(\d+(?:\.\d+)?)分'
            matches = re.findall(pattern, details)
            
            atomic_scores = {}
            for skill_id, score in matches:
                atomic_scores[skill_id] = float(score)
            
            return atomic_scores
        except Exception as e:
            logger.error(f"解析原子技能得分失败: {str(e)}")
            return {}
    
    def _get_default_evaluation_result(self, skill_name: str) -> Dict[str, Any]:
        """
        获取默认评估结果
        """
        return {
            "score": 6.0,
            "strengths": [f"{skill_name}内容基本达标"],
            "improvements": [f"{skill_name}需要进一步优化"],
            "details": "评估失败，使用默认结果",
            "aiComment": f"{skill_name}评估失败，使用默认结果",
            "raw_response": "评估失败"
        }


# 全局实例
universal_ai_evaluator = UniversalAIEvaluator()