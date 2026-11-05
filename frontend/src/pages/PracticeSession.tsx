import { useEffect, useRef, useState } from 'react';
import { Brain, ChevronLeft, RefreshCw } from 'lucide-react';
import { Link, useLocation, useParams } from 'react-router-dom';
import FeedbackPanel from '../components/FeedbackPanel';
import { practiceV1Api } from '../lib/api';
import type { SessionData } from '../lib/api';
import { scoreDimensions } from '../lib/feedback';
import type { ScoreDimension } from '../lib/feedback';
import { sessionCache } from '../lib/sessionCache';
import type { PracticeContent, PracticeRecord } from '../types';

const userId = 'default_user';
type Feedback = { score: number; strengths: string[]; improvements: string[]; aiComment: string; dimensions: ScoreDimension[] };
type Session = SessionData;
// Shares an in-flight request across React effect remounts; no duplicate model requests.
const pendingSessions = new Map<string, Promise<Session>>();

async function obtainSession(skillId: string): Promise<Session> {
  const key = `flash-session:${userId}:${skillId}`;
  const pending = pendingSessions.get(key);
  if (pending) return pending;
  const work = (async () => {
    const saved = sessionCache.read(key);
    if (saved) {
      try {
        const result = await practiceV1Api.getSession(userId, saved);
        if (result.data.status === 'active' || result.data.evaluation_result) return result.data;
      } catch (error) {
        // Only an absent session is discarded. Network/configuration errors stay visible.
        if (!(error instanceof Error) || !('status' in error) || error.status !== 404) throw error;
      }
      sessionCache.remove(key);
    }
    const result = await practiceV1Api.startPractice(userId, skillId);
    sessionCache.write(key, result.data.session_id);
    return result.data as Session;
  })();
  pendingSessions.set(key, work);
  try { return await work; }
  finally { if (pendingSessions.get(key) === work) pendingSessions.delete(key); }
}

const PracticeSession = () => {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const [session, setSession] = useState<Session | null>(null);
  const [content, setContent] = useState<PracticeContent | null>(null);
  const [answer, setAnswer] = useState('');
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [draftNotice, setDraftNotice] = useState('');
  const [showExample, setShowExample] = useState(false);
  const [revision, setRevision] = useState(0);
  const mounted = useRef(false);
  const generation = useRef(0);
  const submitLock = useRef<string | null>(null);
  const historyRecord = (location.state as { fromHistory?: boolean; record?: PracticeRecord } | null)?.fromHistory
    ? (location.state as { record: PracticeRecord }).record : null;

  useEffect(() => {
    mounted.current = true;
    generation.current += 1;
    let active = true;
    setLoading(true);
    setSession(null);
    setContent(null);
    setSubmitting(false);
    setError('');
    setDraftNotice('');
    setFeedback(null);
    setAnswer('');
    setShowExample(false);
    const load = async () => {
      if (historyRecord) {
        setContent({ title: historyRecord.title || historyRecord.skill_name,
          description: historyRecord.description || '', category: historyRecord.category,
          difficulty: historyRecord.difficulty, hint: historyRecord.hint,
          example_answer: historyRecord.example_answer });
        setAnswer(historyRecord.transcript || '');
        setFeedback({ score: historyRecord.score, strengths: historyRecord.strengths || [],
          improvements: historyRecord.improvements || [], aiComment: historyRecord.ai_comment || '',
          dimensions: scoreDimensions(historyRecord.atomic_skill_scores, historyRecord.atomic_skill_names) });
        setLoading(false);
        return;
      }
      try {
        const skills = (await practiceV1Api.getAvailableSkills()).skills;
        const skillId = !id || id === 'random'
          ? skills[Math.floor(Math.random() * skills.length)]?.skill_id : id;
        if (!skillId) throw new Error('暂无可练习的技能，请先在技能库添加。');
        if (!active) return;
        const value = await obtainSession(skillId);
        if (active) {
          setSession(value);
          setContent(value.content);
          if (value.status === 'completed' && value.evaluation_result) {
            const result = value.evaluation_result;
            setAnswer(value.answer || '');
            setFeedback({ score: Math.round(result.score * 10), strengths: result.strengths,
              improvements: result.improvements, aiComment: result.aiComment,
              dimensions: scoreDimensions(result.atomic_skill_scores, value.atomic_skill_names) });
          } else {
            setAnswer(sessionCache.read(`flash-draft:${value.session_id}`) || '');
          }
        }
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : '加载失败，请重试。');
      } finally { if (active) setLoading(false); }
    };
    void load();
    return () => { active = false; mounted.current = false; };
  }, [id, historyRecord, revision]);

  const submit = async () => {
    if (!session || !answer.trim() || submitLock.current === session.session_id) return;
    const requestGeneration = generation.current;
    const requestSessionId = session.session_id;
    submitLock.current = requestSessionId;
    setSubmitting(true);
    setError('');
    try {
      const result = await practiceV1Api.submitAnswer(userId, session.session_id, answer);
      const evaluation = result.data.evaluation_result;
      const cacheKey = `flash-session:${userId}:${session.skill_id}`;
      if (sessionCache.read(cacheKey) === session.session_id) sessionCache.remove(cacheKey);
      sessionCache.remove(`flash-draft:${session.session_id}`);
      window.dispatchEvent(new CustomEvent('practice:record-saved', { detail: { recordId: result.data.record_id } }));
      window.dispatchEvent(new CustomEvent('practice:completed'));
      if (mounted.current && generation.current === requestGeneration) setFeedback({ score: Math.round(evaluation.score * 10),
        strengths: evaluation.strengths, improvements: evaluation.improvements,
        aiComment: evaluation.aiComment,
        dimensions: scoreDimensions(evaluation.atomic_skill_scores, session.atomic_skill_names) });
    } catch (err) {
      // Keep answer and session for retry; a failed request never becomes a fake grade.
      if (mounted.current && generation.current === requestGeneration) setError(err instanceof Error ? err.message : '评估失败，请重试。');
    } finally {
      if (submitLock.current === requestSessionId) submitLock.current = null;
      if (mounted.current && generation.current === requestGeneration) setSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 p-4">
      <Link to="/skills" className="inline-flex items-center gap-2 text-muted-foreground"><ChevronLeft size={20} />返回技能库</Link>
      <div className="bg-card border border-border rounded-xl p-8 space-y-6">
        {loading ? <div className="py-20 flex flex-col items-center gap-4"><Brain className="animate-pulse text-primary" size={40} /><p>正在准备练习...</p></div> : <>
          {error && <div role="alert" className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg space-y-3">
            <p>{error}</p>
            {!content && <button className="underline" onClick={() => setRevision(v => v + 1)}>重试</button>}
          </div>}
          {content && <>
            <span className="text-sm text-primary">{content.category} · {content.difficulty}</span>
            <h1 className="text-3xl font-bold">{content.title}</h1>
            {/* Model text is rendered as text, never injected as executable HTML. */}
            <p className="whitespace-pre-wrap leading-relaxed text-muted-foreground">{content.description}</p>
            {content.hint && <p className="p-4 bg-yellow-50 rounded-lg whitespace-pre-wrap">提示：{content.hint}</p>}
            {content.example_answer && <div>
              <button className="text-primary" onClick={() => setShowExample(v => !v)}>{showExample ? '收起参考答案' : '查看参考答案'}</button>
              {showExample && <p className="mt-3 p-4 bg-blue-50 rounded-lg whitespace-pre-wrap">{content.example_answer}</p>}
            </div>}
            {feedback ? <>
              <div className="p-4 bg-secondary rounded-lg whitespace-pre-wrap"><h2 className="font-semibold mb-2">你的回答</h2>{answer}</div>
              <FeedbackPanel {...feedback} skillCategory={content.category} />
              {historyRecord ? <Link to="/skills" className="text-primary">开始新练习</Link> :
                <button onClick={() => {
                  if (session) sessionCache.remove(`flash-session:${userId}:${session.skill_id}`);
                  setRevision(v => v + 1);
                }} className="inline-flex items-center gap-2 text-primary"><RefreshCw size={18} />再练一道</button>}
            </> : <div className="space-y-4">
              <label htmlFor="response-text" className="block font-medium">请输入你的回答</label>
              <textarea id="response-text" value={answer} onChange={e => {
                setAnswer(e.target.value);
                if (session && !sessionCache.write(`flash-draft:${session.session_id}`, e.target.value)) {
                  setDraftNotice('草稿暂时无法保存，刷新前请复制你的回答。');
                }
              }} maxLength={50000}
                disabled={submitting} className="w-full min-h-56 p-4 border rounded-xl bg-secondary/30 resize-y"
                placeholder="在这里输入你的回答内容..." />
              <div className="flex items-center justify-between gap-4"><span className="text-sm text-muted-foreground">{answer.length} 字符</span>
                <button onClick={submit} disabled={!answer.trim() || submitting || !session}
                  className="px-6 py-3 rounded-xl bg-primary text-white disabled:opacity-50">{submitting ? '正在评估...' : '提交并获取评估'}</button>
              </div>
              <p className="text-xs text-muted-foreground">评估成功后自动保存。评估失败时可保留回答并重试。</p>
              {draftNotice && <p role="status" className="text-sm text-amber-700">{draftNotice}</p>}
            </div>}
          </>}
        </>}
      </div>
    </div>
  );
};

export default PracticeSession;
