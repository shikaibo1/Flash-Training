import type { Skill, PracticeContent, PracticeRecord, AtomicSkill, OptimizationRequest } from '../types';

// Backend address only. GPT credentials are stored exclusively in backend/.env.ai.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001/api';
const part = encodeURIComponent;

export class ApiError extends Error {
  constructor(message: string, public status: number, public code?: string) { super(message); }
}

type Envelope<T> = { error: false; msg: string; data: T };
export type SessionData = {
  session_id: string; skill_id: string; content: PracticeContent; start_time: string;
  status: 'active' | 'completed';
  atomic_skill_names?: Record<string, string>;
  answer?: string;
  evaluation_result?: EvaluationData;
};
export type EvaluationData = {
  score: number; strengths: string[]; improvements: string[]; aiComment: string;
  atomic_skill_scores: Record<string, number>;
};
export type Health = {
  status: string; database: string; ai_configured: boolean; ai_model: string; schema_version: number;
};

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const controller = new AbortController();
  // Backend allows a 300s AI timeout plus a 15s database lock wait.
  const timeout = window.setTimeout(() => controller.abort(), 330000);
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: { 'Content-Type': 'application/json', ...options.headers },
      signal: controller.signal,
    });
    const body = await response.json().catch(() => null);
    if (!response.ok) {
      const detail = typeof body?.detail === 'string' ? body.detail
        : body?.msg || (Array.isArray(body?.detail) ? '填写的内容不符合要求，请检查后重试。' : undefined);
      throw new ApiError(detail || `请求失败（${response.status}）`, response.status, body?.code);
    }
    if (!body) throw new ApiError('服务返回了无法读取的数据。', response.status);
    return body;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError('等待响应超时，你的回答已保留，可以重试。', 0, 'request_timeout');
    }
    throw new ApiError('无法连接服务，请确认服务已启动后重试。', 0, 'network_error');
  } finally { window.clearTimeout(timeout); }
}

function post<T>(endpoint: string, value: unknown) {
  return request<T>(endpoint, { method: 'POST', body: JSON.stringify(value) });
}

export const systemApi = { health: () => request<Health>('/health') };

export const skillsApi = {
  getAllSkills: () => request<{ skills: Skill[] }>('/skills'),
  createCustomSkill: (skillName: string) => post<{ skill: Skill; message: string }>('/skills/custom', { skill_name: skillName }),
  deleteSkill: (skillId: string) => request<{ message: string }>(`/skills/${part(skillId)}`, { method: 'DELETE' }),
};

export const atomicApi = {
  getAllAtomicSkills: () => request<{ atomic_skills: AtomicSkill[] }>('/v1/atomic/skills'),
  getUserAtomicSkills: (userId: string) => request<{ user_id: string; atomic_skills: AtomicSkill[] }>(`/v1/atomic/users/${part(userId)}/skills`),
  getAtomicSkillsForSkill: (skillId: string, userId = 'default_user') =>
    request<{ atomic_skills: AtomicSkill[] }>(`/v1/atomic/skills/${part(skillId)}/mapping?user_id=${part(userId)}`),
  generateOptimizationPlan: (value: OptimizationRequest) => post<{ optimization_advice: string }>('/v1/atomic/optimize', value),
};

export const practiceApi = {
  getRecords: (userId: string) => request<{ records: PracticeRecord[] }>(`/practice/records/${part(userId)}`),
  deleteRecord: (recordId: string, userId = 'default_user') =>
    request<{ message: string }>(`/practice/record/${part(recordId)}?user_id=${part(userId)}`, { method: 'DELETE' }),
};

export const practiceV1Api = {
  getSession: (userId: string, sessionId: string) =>
    request<Envelope<SessionData>>(`/v1/practice/sessions/${part(sessionId)}?user_id=${part(userId)}`),
  startPractice: (userId: string, skillId: string, params: Record<string, unknown> = {}) =>
    post<Envelope<SessionData>>('/v1/practice/start', { user_id: userId, skill_id: skillId, params }),
  submitAnswer: (userId: string, sessionId: string, answer: string) =>
    post<Envelope<{ session_id: string; evaluation_result: EvaluationData; record_id: string; status: string }>>(
      '/v1/practice/submit', { user_id: userId, session_id: sessionId, answer }),
  getAvailableSkills: () => request<{ skills: Skill[] }>('/v1/practice/skills'),
};

export type Mastery = { atomic_skill_id: string; name: string; mastery: number; practice_count: number };
export const knowledgeTracingApi = {
  getAllMastery: (userId: string) =>
    request<Envelope<{ user_id: string; atomic_skills: Mastery[] }>>(`/v1/knowledge-tracing/mastery/all/${part(userId)}`),
  getLearningCurve: (userId: string, atomicSkillId: string, days = 30) =>
    request<Envelope<{ learning_curve: { timestamp: string; mastery: number; performance: number }[] }>>(
      `/v1/knowledge-tracing/learning-curve/${part(userId)}/${part(atomicSkillId)}?days=${days}`),
};
