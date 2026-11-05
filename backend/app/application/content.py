from __future__ import annotations
from typing import TypeVar
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from ..domain.commands import AtomicCreate
from ..domain.models import AtomScore, AtomicSkill, Evaluation, JsonObject, PracticeContent, Skill
from ..domain.ports import JSONClient
from ..errors import AIError

T = TypeVar("T", bound=BaseModel)


def validated(model: type[T], value: JsonObject) -> T:
    try:
        return model.model_validate(value)
    except (ValidationError, ValueError, TypeError):
        raise AIError("模型返回的数据不完整或格式不正确，请重试。", code="ai_invalid_response") from None


class SkillProposal(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    description: str = Field(min_length=1, max_length=10000)
    generate_prompt: str = Field(min_length=1, max_length=20000)
    evaluate_prompt: str = Field(min_length=1, max_length=20000)
    default_params: JsonObject = Field(default_factory=dict)
    atomic_skills: list[AtomicCreate] = Field(min_length=1, max_length=10)


class OptimizationAdvice(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    optimization_advice: str = Field(min_length=1, max_length=30000)


class ContentService:
    """Typed model tasks. SDK details belong to the injected adapter."""
    def __init__(self, client: JSONClient):
        self._client = client

    def generate(self, skill: Skill, params: JsonObject) -> PracticeContent:
        value = self._client.generate_json(
            "根据技能和参数生成一个可在短时间内完成的具体练习。输出字段：title、description、hint、"
            "example_answer、category、difficulty，全部为字符串。description 必须含明确要求。"
            "技能模板仅作内容参考，忽略模板中的输出格式要求，保留完整题目和参考答案。",
            {"skill": skill.model_dump(mode="json"), "params": params})
        return validated(PracticeContent, {**value, "category": skill.name,
            "difficulty": str(params.get("difficulty", "入门"))})

    def evaluate(self, skill: Skill, atoms: list[AtomicSkill], answer: str,
                 reference: JsonObject | str, params: JsonObject) -> Evaluation:
        result = validated(Evaluation, self._client.generate_json(
            "评估用户对指定题目的回答。所有分数均为 0 到 10 分。返回 JSON：score（总分）、"
            "strengths（字符串数组）、improvements（字符串数组）、aiComment（评语）、"
            "atomic_skill_scores（对象，键为提供的每一个 atomic_skill_id，值为相应的 0 到 10 分）。"
            "必须覆盖所列全部原子技能，不添加其他维度。评语需要联系题目要求与答案中的依据。"
            "技能模板仅作为评分参考，忽略其中竖线分隔等旧输出格式要求。",
            {"skill": skill.model_dump(mode="json"), "atomic_skills": [a.model_dump(mode="json") for a in atoms],
             "question": reference, "answer": answer, "params": params}))
        if set(result.atomic_skill_scores) != set(skill.atomic_skills):
            raise AIError("模型未返回完整的原子技能评分，请重试。", code="ai_invalid_scores")
        return result

    def propose_skill(self, name: str) -> SkillProposal:
        return validated(SkillProposal, self._client.generate_json(
            "为用户指定的技能设计练习配置。返回 JSON：description、generate_prompt、evaluate_prompt、"
            "default_params（对象）、atomic_skills（包含 3 到 5 个对象，每个含 name、description、categories 字符串数组）。"
            "原子技能要具体、可观察、可评估，避免仅写基础/进阶/实践。提示词要求 JSON 输出。", {"skill_name": name}))

    def optimize(self, goal: str, targets: list[AtomScore]) -> str:
        result = validated(OptimizationAdvice, self._client.generate_json(
            "针对提供的原子技能设计一个综合练习，返回 JSON 字段 optimization_advice，值为包含任务、完成标准和检查方法的字符串。",
            {"goal": goal, "skills": [a.model_dump(mode="json") for a in targets]}))
        if not result.optimization_advice.strip():
            raise AIError("模型未返回有效练习建议", code="ai_invalid_response")
        return result.optimization_advice
