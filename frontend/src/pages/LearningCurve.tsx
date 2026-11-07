import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { careerApi } from '../lib/api';
import type { EvidenceData } from '../types';
import { statusLabels } from '../lib/evidence';
export default function LearningCurve() {
  const [evidence, setEvidence] = useState<EvidenceData | null>(null);
  const [error, setError] = useState('');
  const [revision, setRevision] = useState(0);

  useEffect(() => {
    let active = true;
    careerApi.evidence()
      .then(value => { if (active) setEvidence(value); })
      .catch(error => { if (active) setError(error.message); });
    return () => { active = false; };
  }, [revision]);

  return <div className="space-y-6">
    <h1 className="text-3xl font-bold">能力证据档案</h1>
    <p className="text-muted-foreground">按情境保存可观察的行为证据。一次高分不代表掌握；尚未测量也不等于零分。跨情境证据不等于所有情境均可迁移。</p>
    {error &&
    <div role="alert">{error}
      <button className="text-primary" onClick={() => { setError(''); setRevision(v => v + 1); }}>重试</button>
    </div>}
    {!evidence && !error &&
    <p role="status">正在读取证据…</p>}
    <div className="grid md:grid-cols-2 gap-4">{evidence?.atomic_skills.map(atom =>
      <article key={atom.atomic_skill_id} className="bg-card border rounded-xl p-5 space-y-3">
        <Link className="font-semibold text-primary" to={`/graph?node=${encodeURIComponent(`atom:${atom.atomic_skill_id}`)}`}>{atom.name}</Link>
        <p className="text-sm">{atom.transfer_observed ? '已观察到跨情境表现' : '尚无跨情境证据'}</p>{atom.contexts.map(context =>
        <div key={context.context} className="border-t pt-3 text-sm">
          <p className="font-medium">{context.context} · {statusLabels[context.status]}</p>
          <p className="text-muted-foreground">证据 {context.evidence_count} 条 · 独立证据 {context.independent_count} 条 · 最近评分 {context.last_score == null ? '未测量' : context.last_score}</p>{context.last_practice_time &&
          <p>{new Date(context.last_practice_time).toLocaleString()}</p>}
        </div>)}
      </article>)}
    </div>
    <h2 className="text-2xl font-bold">最近观察</h2>{evidence?.recent_evidence.length === 0 &&
    <p>还没有评估证据。
      <Link className="text-primary" to="/skills">选择职业任务开始</Link></p>}
    {evidence?.recent_evidence.map((item, index) =>
    <article key={`${item.session_id}-${item.atomic_skill_id}-${index}`} className="bg-card border rounded-xl p-5 space-y-2">
      <h3 className="font-semibold">{evidence.atomic_skills.find(atom => atom.atomic_skill_id === item.atomic_skill_id)?.name || item.atomic_skill_id} · {item.context}</h3>
      <p>{item.status === 'not_observable' ? '本次不可观察' : `本次评分：${item.score ?? '未评分'}`} · {item.assistance_used ? '使用了辅助' : '未记录辅助'}</p>{item.quote &&
      <blockquote className="border-l-4 pl-4 whitespace-pre-wrap">{item.quote}
      </blockquote>}
      <p>{item.reason}</p>
      <p className="text-primary">下一步：{item.next_action}</p>
    </article>)}
  </div>;
  }
