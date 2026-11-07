import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { careerApi } from '../lib/api';
import type { GraphData } from '../types';
export default function SkillsLibrary() {
  const [graph, setGraph] = useState<GraphData | null>(null);
  const [query, setQuery] = useState('');
  const [role, setRole] = useState('');
  const [error, setError] = useState('');
  const [revision, setRevision] = useState(0);

  useEffect(() => {
    let active = true;
    careerApi.graph()
      .then(value => { if (active) setGraph(value); })
      .catch(error => { if (active) setError(error.message); });
    return () => { active = false; };
  }, [revision]);

  const tasks = graph?.tasks.filter(task => {
    const matchesRole = !role || task.role_id === role;
    const searchableText = `${task.name} ${task.display_name} ${task.description} ${task.context}`;
    return matchesRole && searchableText.toLowerCase().includes(query.toLowerCase());
  });

  return <div className="space-y-6">
    <h1 className="text-3xl font-bold">职业任务库</h1>
    <p className="text-muted-foreground">每个任务有明确交付物和原子能力。课程知识通过图谱关联到行动，而不是等同于能力。</p>
    <div className="flex flex-wrap gap-3">
      <input aria-label="搜索任务" className="border rounded-lg p-3 bg-card" placeholder="搜索任务、情境" value={query} onChange={e => setQuery(e.target.value)}/>
        <select aria-label="职业筛选" className="border rounded-lg p-3 bg-card" value={role} onChange={e => setRole(e.target.value)}>
          <option value="">全部职业</option>{graph?.roles.map(item =>
          <option key={item.role_id} value={item.role_id}>{item.name}</option>)}
        </select>
        <Link className="p-3 text-primary" to="/graph">查看能力关系图 →</Link>
      </div>
      {error &&
      <div role="alert">{error}
        <button className="text-primary" onClick={() => { setError(''); setRevision(v => v + 1); }}>重试</button>
      </div>}{!graph && !error &&
      <p role="status">加载任务定义…</p>}{tasks?.length === 0 &&
      <p>没有匹配任务，试试其他关键词或职业。</p>}
      <div className="grid lg:grid-cols-2 gap-5">{tasks?.map(task =>
        <article key={task.skill_id} className="p-6 border rounded-xl bg-card space-y-4">
          <p className="text-sm text-primary">{graph?.roles.find(item => item.role_id === task.role_id)?.name} · {task.context}</p>
          <h2 className="text-xl font-semibold">{task.display_name || task.name}</h2>
          <p>{task.task_brief || task.description}</p>
          <p className="text-muted-foreground">交付物：{task.deliverable}</p>
          <div className="flex flex-wrap gap-2">{task.atomic_skills.map(id =>
            <Link key={id} className="text-sm rounded-full bg-secondary px-3 py-1" to={`/graph?node=${encodeURIComponent(`atom:${id}`)}`}>{graph?.atoms.find(atom => atom.atomic_skill_id === id)?.name || id}</Link>)}
          </div>
          <div className="flex flex-wrap gap-3">{(['guided','independent','transfer'] as const).map((mode, index) =>
            <Link key={mode} className="text-primary border rounded-lg px-3 py-2" to={`/practice/${encodeURIComponent(task.skill_id)}?mode=${mode}`}>{['引导练习','独立练习','迁移练习'][index]}</Link>)}
          </div>
        </article>)}
      </div>
      <h2 className="text-2xl font-bold">原子能力定义</h2>
      <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">{graph?.atoms.filter(atom => `${atom.name} ${atom.description}`.toLowerCase().includes(query.toLowerCase())).map(atom =>
        <article key={atom.atomic_skill_id} className="border rounded-xl p-5 space-y-2 bg-card">
          <Link className="font-semibold text-primary" to={`/graph?node=${encodeURIComponent(`atom:${atom.atomic_skill_id}`)}`}>{atom.name}</Link>
          <p>{atom.action}</p>
          <p className="text-sm text-muted-foreground">输入：{atom.input_spec}</p>
          <p className="text-sm text-muted-foreground">输出：{atom.output_spec}</p>
          <p className="text-sm">边界：{atom.boundary}</p>
        </article>)}
      </div>
    </div>;
    }
