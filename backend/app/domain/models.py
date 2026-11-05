from __future__ import annotations
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, JsonValue

JsonObject = dict[str, JsonValue]
Score10 = Annotated[float, Field(ge=0, le=10, allow_inf_nan=False, strict=True)]
FeedbackText = Annotated[str, Field(min_length=1, max_length=5000)]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class AtomicSkill(Model):
    atomic_skill_id: str
    name: str
    description: str
    categories: list[str] = Field(default_factory=list)


class Skill(Model):
    skill_id: str
    name: str
    display_name: str
    description: str
    generate_prompt: str = ""
    evaluate_prompt: str = ""
    enabled: bool = True
    default_params: JsonObject = Field(default_factory=dict)
    atomic_skills: list[str] = Field(default_factory=list)


class StoredContent(BaseModel):
    """Historical snapshots can omit fields; only newly generated content is strict."""
    model_config = ConfigDict(extra="allow", frozen=True)
    title: str = ""
    description: str = ""
    hint: str = ""
    example_answer: str = ""
    category: str = "通用"
    difficulty: str | int | float = "入门"


class PracticeContent(StoredContent):
    model_config = ConfigDict(extra="ignore", frozen=True, str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=500)
    description: str = Field(min_length=1, max_length=20000)
    hint: str = Field(default="", max_length=10000)
    example_answer: str = Field(min_length=1, max_length=30000)
    difficulty: str = "入门"


class Evaluation(Model):
    model_config = ConfigDict(extra="ignore", frozen=True, str_strip_whitespace=True)
    score: Score10
    strengths: list[FeedbackText] = Field(min_length=1, max_length=20)
    improvements: list[FeedbackText] = Field(min_length=1, max_length=20)
    aiComment: str = Field(min_length=1, max_length=10000)
    atomic_skill_scores: dict[str, Score10] = Field(default_factory=dict)


class PracticeSession(Model):
    session_id: str
    user_id: str
    skill_id: str
    content: StoredContent
    skill_snapshot: Skill
    params: JsonObject = Field(default_factory=dict)
    status: Literal["active", "completed"] = "active"
    started_at: str
    completed_at: str | None = None
    # Unstructured values are limited to historical evaluation snapshots.
    result: Evaluation | JsonObject | None = None
    provenance: str = "live"


class PracticeRecord(BaseModel):
    """Canonical columns plus optional historical payload fields; extras are retained."""
    model_config = ConfigDict(extra="allow", frozen=True)
    record_id: str
    user_id: str
    skill_id: str
    score: float = Field(ge=0, le=100, allow_inf_nan=False)
    start_time: str
    end_time: str
    session_id: str | None = None
    skill_name: str = ""
    title: str = ""
    description: str = ""
    hint: str = ""
    example_answer: str = ""
    category: str = ""
    difficulty: str | int | float = ""
    input_type: str = "text"
    transcript: str = ""
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    ai_comment: str = ""
    atomic_skill_scores: dict[str, float] | None = None
    atomic_skill_names: dict[str, str] | None = None
    provenance: str = "live"


class AtomScore(AtomicSkill):
    score: Score10 = 0.0
    current_score: Score10 = 0.0


class AtomMastery(AtomicSkill):
    mastery: float = Field(ge=0, le=1)
    last_practice_time: str | None = None
    practice_count: int = Field(default=0, ge=0)


class MasteryEvent(Model):
    timestamp: str
    performance: float = Field(ge=0, le=1)
    mastery: float = Field(ge=0, le=1)


class SessionStarted(Model):
    session_id: str
    skill_id: str
    question: str
    content: PracticeContent
    start_time: str
    status: Literal["active"] = "active"
    atomic_skill_names: dict[str, str]


class Submission(Model):
    session_id: str
    evaluation_result: Evaluation | JsonObject
    record_id: str | None
    status: Literal["completed"] = "completed"


class SessionDetails(Model):
    session_id: str
    skill_id: str
    status: Literal["active", "completed"]
    content: StoredContent
    start_time: str
    atomic_skill_names: dict[str, str]
    evaluation_result: Evaluation | JsonObject | None = None
    record_id: str | None = None
    answer: str | None = None


class SessionHistory(Model):
    session_id: str
    user_id: str
    skill_id: str
    content: StoredContent
    question: str
    status: Literal["active", "completed"]
    start_time: str
    end_time: str | None
    final_result: Evaluation | JsonObject | None


class SkillStatistics(Model):
    practice_count: int = 0
    avg_score: float = 0.0
    last_score: float
    last_practice_time: str


class UserProfile(Model):
    user_id: str
    skills: dict[str, SkillStatistics]
    legacy_profiles: dict[str, JsonValue]
    score_scale: Literal["0-100"] = "0-100"


class SkillProgress(Model):
    user_id: str
    skill_id: str
    practice_count: int
    avg_score: float
    score_scale: Literal["0-100"] = "0-100"


class Recommendation(Skill):
    mastery: float
    reason: str = "优先巩固掌握度较低的技能"


class UserScores(Model):
    user_id: str
    atomic_skills: list[AtomScore]


class UserMastery(Model):
    user_id: str
    atomic_skills: list[AtomMastery]


class SkillMapping(Model):
    skill_id: str
    skill_name: str
    atomic_skills: list[AtomScore]


class ScoreValue(Model):
    user_id: str
    atomic_skill_id: str
    score: Score10


class ManualScore(ScoreValue):
    source: Literal["manual"] = "manual"
    message: str = "自评已记录，不计入 AI 评估或掌握度"


class MasteryUpdated(Model):
    atomic_skill_id: str
    new_mastery: float
    source: Literal["manual"] = "manual"


class Prediction(Model):
    atomic_skill_id: str
    predicted_performance: float
    method: Literal["exponential_moving_average"] = "exponential_moving_average"
    is_calibrated_prediction: Literal[False] = False


class LearningCurve(Model):
    atomic_skill_id: str
    learning_curve: list[MasteryEvent]
    days: int


class Recommendations(Model):
    recommendations: list[Recommendation]
    top_n: int


class Optimization(Model):
    user_id: str
    targeted_skills: list[AtomScore]
    optimization_advice: str
    optimization_goal: str
