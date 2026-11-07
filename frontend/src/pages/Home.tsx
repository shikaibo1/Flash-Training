import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { careerApi, systemApi } from '../lib/api';
import type { Recommendation } from '../types';
export default function Home() {
  const [recommendations, setRecommendations] = useState<Recommendation[] | null>(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [revision, setRevision] = useState(0);

  useEffect(() => {
    let active = true;
    careerApi.recommendations()
      .then(result => { if (active) setRecommendations(result.recommendations); })
      .catch(error => { if (active) setError(error.message); });
    systemApi.health()
      .then(result => {
        if (active && !result.ai_configured) {
          setNotice('AI 尚未配置。可浏览图谱与证据；生成和评估练习需要配置服务。');
        }
      })
      .catch(error => { if (active) setNotice(error.message); });
    return () => { active = false; };
  }, [revision]);

  return <div className="space-y-10 pb-8">
    <section className="rounded-2xl bg-slate-900 text-white p-8 md:p-12 space-y-5">
      <p className="text-indigo-200">职业任务 → 原子技能 → 可观察证据</p>
      <h1 className="text-4xl md:text-5xl font-bold leading-tight">把知识用在工作里，
        <br/>把能力练到能迁移。</h1>
      <p className="max-w-2xl text-slate-300 leading-relaxed">从真实交付任务出发，理解课程知识如何支撑具体行动。在引导、独立和迁移练习中保留原始回答，依据行为证据决定下一步。</p>
      <div className="flex flex-wrap gap-3">
        <Link to="/graph" className="rounded-lg bg-white text-slate-900 px-5 py-3">探索职业能力图谱</Link>
        <Link to="/skills" className="rounded-lg border border-slate-500 px-5 py-3">选择任务</Link>
        <Link to="/learning-curve" className="rounded-lg border border-slate-500 px-5 py-3">我的证据</Link>
      </div>
    </section>
    {notice &&
    <p role="status" className="p-4 bg-amber-50 rounded-lg">{notice}</p>}
    <section className="space-y-4">
      <h2 className="text-2xl font-bold">下一步练什么</h2>
      <p className="text-muted-foreground">规划器根据已有证据与任务关系推荐，不调用模型，也不虚构掌握度。</p>{error &&
      <div role="alert">{error}
        <button className="text-primary" onClick={() => { setError(''); setRevision(v => v + 1); }}>重试</button>
      </div>}{!recommendations && !error &&
      <p role="status">正在读取建议…</p>}{recommendations?.length === 0 &&
      <p>暂无建议，可从任务库自主选择。</p>}
      <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-5">{recommendations?.map(item =>
        <article key={`${item.skill_id}-${item.context}`} className="p-6 border bg-card rounded-xl space-y-3">
          <p className="text-primary text-sm">{item.context}</p>
          <h3 className="text-xl font-semibold">{item.title}</h3>
          <p className="text-muted-foreground">{item.reason}</p>
          <div className="flex flex-wrap gap-3">
            {(['guided', 'independent', 'transfer'] as const).map((mode, index) => (
            <Link
            key={mode}
            className="text-primary font-medium"
            to={`/practice/${encodeURIComponent(item.skill_id)}?mode=${mode}&atoms=${encodeURIComponent(item.target_atomic_ids.join(','))}`}
            >
            {['引导练习', '独立练习', '迁移练习'][index]} →
          </Link>
          ))}
        </div>
      </article>)}
    </div>
  </section>
  <section className="grid md:grid-cols-3 gap-5">{[['引导练习', '主动查看提示与示例，引导模式结果仅作为辅助完成证据。'], ['独立练习', '先提交自己的交付物，再查看评估。'], ['迁移练习', '在另一个任务情境中检验同一行动能力。']].map(([title, description]) =>
    <article key={title} className="border rounded-xl p-5">
      <h2 className="font-semibold mb-2">{title}</h2>
      <p className="text-muted-foreground">{description}</p>
    </article>)}
  </section>
  </div>;
  }
