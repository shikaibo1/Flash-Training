export interface Skill {
  skill_id: string;
  name: string;
  display_name: string;
  description: string;
  atomic_skills: string[];
  generate_prompt: string;
  evaluate_prompt: string;
  enabled: boolean;
  default_params: Record<string, string>;
}

// 原子技能接口
export interface AtomicSkill {
  atomic_skill_id: string;
  name: string;
  description: string;
  categories: string[];
  score?: number;
  current_score?: number;
}

// 自定义技能请求接口
export interface CustomSkillRequest {
  skill_name: string;
}

// 优化请求接口
export interface OptimizationRequest {
  user_id: string;
  atomic_skill_ids: string[];
  optimization_goal: string;
}

export interface SpeechEvaluationRequest {
  draft: string;
  scene: string;
  duration: string;
  keyword?: string;
}

export interface SpeechEvaluationResult {
  draft: string;
  scene: string;
  duration: string;
  total_score: number;
  avg_score: number;
  agent_details: Array<{
    agent_name: string;
    dimension: string;
    score: number;
    advice: string;
  }>;
  comprehensive_advice: string;
}

export interface CodeEvaluationRequest {
  code: string;
  optimize_type: string;
}

export interface PracticeSessionData {
  id: string;
  skillId: string;
  startTime: string;
  endTime?: string;
  score?: number;
}

// 添加练习内容接口
export interface PracticeContent {
  category: string;
  difficulty: string;
  title: string;
  description: string;
  hint?: string;
  example_answer?: string;
}

// 练习记录接口
export interface PracticeRecord {
  title?: string;
  description?: string;
  hint?: string;
  example_answer?: string;
  session_id?: string;
  atomic_skill_scores?: Record<string, number>;
  atomic_skill_names?: Record<string, string>;
  user_id: string;
  skill_id: string;
  skill_name: string;
  category: string;
  difficulty: string;
  input_type: string;  // voice 或 text
  transcript: string;
  score: number;
  strengths: string[];
  improvements: string[];
  ai_comment: string;
  record_id?: string;
  start_time: string;
  end_time: string;
}
