import { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { careerApi } from '../lib/api';
import type { EvidenceData, GraphData, GraphNode } from '../types';
import { statusLabels } from '../lib/evidence';
const labels = { role: '职业', task: '任务', atom: '原子能力', knowledge: '课程知识' };
const colors = { role: '#4338ca', task: '#0369a1', atom: '#047857', knowledge: '#a16207' };
const relations = { requires: '需要', supports: '支撑', prerequisite: '前置', contains: '包含' };
export default function KnowledgeGraph() {
  const [graph, setGraph] = useState<GraphData | null>(null);
  const [evidence, setEvidence] = useState<EvidenceData | null>(null);
  const [error, setError] = useState('');
  const [evidenceError, setEvidenceError] = useState('');
  const [revision, setRevision] = useState(0);
  const [query, setQuery] = useState('');
  const [role, setRole] = useState('');
  const [course, setCourse] = useState('');
  const [type, setType] = useState('');
  const [params, setParams] = useSearchParams();
  const selectedId = params.get('node');

  useEffect(() => {
    let active = true;
    careerApi.graph()
      .then(value => { if (active) setGraph(value); })
      .catch(error => { if (active) setError(error.message); });
    careerApi.evidence()
      .then(value => { if (active) setEvidence(value); })
      .catch(error => { if (active) setEvidenceError(error.message); });
    return () => { active = false; };
  }, [revision]);

  const filtered = useMemo(() => {
    if (!graph) return [];
    let allowed: Set<string> | null = null;

    if (role) {
      const tasks = graph.tasks.filter(task => task.role_id === role);
      const atoms = new Set(tasks.flatMap(task => task.atomic_skills));
      const knowledge = new Set(
        graph.atoms.filter(atom => atoms.has(atom.atomic_skill_id)).flatMap(atom => atom.knowledge_ids)
      );
      allowed = new Set([
        `role:${role}`,
        ...tasks.map(task => `task:${task.skill_id}`),
        ...Array.from(atoms, id => `atom:${id}`),
        ...Array.from(knowledge, id => `knowledge:${id}`),
      ]);
    }

    if (course) {
      const knowledge = graph.knowledge.filter(item => item.course === course);
      const knowledgeIds = new Set(knowledge.map(item => item.knowledge_id));
      const atoms = graph.atoms.filter(atom => atom.knowledge_ids.some(id => knowledgeIds.has(id)));
      const atomIds = new Set(atoms.map(atom => atom.atomic_skill_id));
      const tasks = graph.tasks.filter(task => task.atomic_skills.some(id => atomIds.has(id)));
      const courseAllowed = new Set([
        ...knowledge.map(item => `knowledge:${item.knowledge_id}`),
        ...atoms.map(atom => `atom:${atom.atomic_skill_id}`),
        ...tasks.map(task => `task:${task.skill_id}`),
        ...tasks.map(task => `role:${task.role_id}`),
      ]);
      allowed = allowed ? new Set([...allowed].filter(id => courseAllowed.has(id))) : courseAllowed;
    }

    return graph.nodes.filter(node => {
      const matchesScope = !allowed || allowed.has(node.id);
      const matchesType = !type || node.type === type;
      const matchesQuery = `${node.label} ${node.description}`.toLowerCase().includes(query.toLowerCase());
      return matchesScope && matchesType && matchesQuery;
    });
  }, [graph, query, role, course, type]);

  // A focused neighborhood keeps the initial view readable; the list exposes all matches.
  const selected = graph?.nodes.find(node => node.id === selectedId)
    || filtered.find(node => node.type === 'role') || filtered[0];
  const neighborhood = selected && graph
    ? graph.edges.filter(edge => edge.source === selected.id || edge.target === selected.id) : [];
  const visible = selected && graph
    ? [selected, ...graph.nodes.filter(node => node.id !== selected.id
      && neighborhood.some(edge => edge.source === node.id || edge.target === node.id))] : [];
  const visibleIds = new Set(visible.map(node => node.id));
  const edges = graph?.edges.filter(edge => visibleIds.has(edge.source) && visibleIds.has(edge.target)) || [];
  const columns = 3;
  const rows = Math.ceil(visible.length / columns);
  const height = Math.max(200, rows * 110 + 30);
  const position = (id: string) => {
    const index = visible.findIndex(node => node.id === id);
    return { x: 140 + (index % columns) * 290, y: 65 + Math.floor(index / columns) * 110 };
  };
  const select = (node: GraphNode) => setParams({ node: node.id });
  const atom = graph?.atoms.find(item => selected?.type === 'atom'
    && item.atomic_skill_id === selected.reference_id);
  const personal = evidence?.atomic_skills.find(item => item.atomic_skill_id === atom?.atomic_skill_id);
  const relatedTasks = graph?.tasks.filter(task => atom
    ? task.atomic_skills.includes(atom.atomic_skill_id)
    : selected?.type === 'task' && task.skill_id === selected.reference_id) || [];

  return <div className="space-y-6">
    <h1 className="text-3xl font-bold">职业能力图谱</h1>
    <p className="text-muted-foreground">沿“职业—任务—原子能力—课程知识”探索。点击节点查看直接关系与评分依据；箭头从关系起点指向终点。</p>
    <div className="flex flex-wrap gap-3">
      <input aria-label="搜索图谱节点" className="p-3 rounded-lg border bg-card" placeholder="搜索行动、任务或知识" value={query} onChange={e => { setQuery(e.target.value); setParams({}); }}/>
        <select aria-label="职业筛选" className="p-3 border rounded-lg bg-card" value={role} onChange={e => { setRole(e.target.value); setParams({}); }}>
          <option value="">全部职业</option>{graph?.roles.map(item =>
          <option key={item.role_id} value={item.role_id}>{item.name}</option>)}
        </select>
        <select aria-label="课程筛选" className="p-3 border rounded-lg bg-card" value={course} onChange={e => { setCourse(e.target.value); setParams({}); }}>
          <option value="">全部课程</option>{Array.from(new Set(graph?.knowledge.map(item => item.course))).map(item =>
          <option key={item}>{item}</option>)}
        </select>
        <select aria-label="节点类型" className="p-3 border rounded-lg bg-card" value={type} onChange={e => { setType(e.target.value); setParams({}); }}>
          <option value="">全部类型</option>{Object.entries(labels).map(([key, label]) =>
          <option key={key} value={key}>{label}</option>)}
        </select>{selectedId &&
        <button className="text-primary" onClick={() => setParams({})}>回到筛选概览</button>}
      </div>
      {error &&
      <div role="alert">{error}
        <button className="text-primary" onClick={() => { setError(''); setEvidenceError(''); setRevision(v => v + 1); }}>重试</button>
      </div>}{!graph && !error &&
      <p role="status">读取图谱…</p>}{evidenceError &&
      <p role="alert">个人证据暂不可用：{evidenceError}。图谱定义仍可浏览。</p>}
      {graph && <>
        <div className="flex flex-wrap gap-4 text-sm">{Object.entries(labels).map(([key, label]) =>
          <span key={key} style={{ color: colors[key as keyof typeof colors] }}>● {label}</span>)}
        </div>
        <section className="border rounded-xl bg-card p-3 overflow-x-auto" aria-label="可交互关系图">
          <p className="p-2 text-sm text-muted-foreground">{selected ? `${selectedId ? '' : '当前概览：'}${selected.label} 的直接关系（${visible.length} 个节点）；筛选列表含 ${filtered.length} 个匹配节点。` : `筛选到 ${filtered.length} 个节点，概览显示前 ${visible.length} 个；下方列表包含全部匹配结果。`}</p>
          <svg viewBox={`0 0 860 ${height}`} style={{ minWidth: 620, width: '100%' }} role="img" aria-label="职业能力关系图，亦可使用下方节点列表">
            <defs>
              <marker id="graph-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
                <path d="M0,0 L8,4 L0,8" fill="#94a3b8"/>
              </marker>
            </defs>{edges.map((edge, index) => { const start = position(edge.source);
            const end = position(edge.target);
            const dx = end.x - start.x;
            const dy = end.y - start.y;
            const boundaryRatio = Math.max(Math.abs(dx) / 126, Math.abs(dy) / 34);
            const offsetX = dx / boundaryRatio;
            const offsetY = dy / boundaryRatio;
            return <g key={`${edge.source}-${edge.target}-${index}`}>
              <line x1={start.x + offsetX} y1={start.y + offsetY} x2={end.x - offsetX} y2={end.y - offsetY} stroke="#94a3b8" strokeWidth="1.5" markerEnd="url(#graph-arrow)"/>
              <text x={(start.x + end.x) / 2} y={(start.y + end.y) / 2 - 8} textAnchor="middle" fill="#64748b" fontSize="11">{relations[edge.relation]}</text>
            </g>; })}{visible.map(node => { const point = position(node.id); return <g key={node.id} role="button" tabIndex={0} aria-label={`查看${labels[node.type]}：${node.label}`} onClick={() => select(node)} onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); select(node); } }} style={{ cursor: 'pointer' }}>
              <rect x={point.x - 120} y={point.y - 28} width="240" height="56" rx="12" fill={colors[node.type]} stroke={node.id === selectedId ? '#111827' : 'white'} strokeWidth="3"/>
              <text x={point.x} y={point.y - 5} textAnchor="middle" fill="white" fontSize="11">{labels[node.type]}</text>
              <text x={point.x} y={point.y + 14} textAnchor="middle" fill="white" fontSize="13">{node.label.length > 17 ? `${node.label.slice(0, 16)}…` : node.label}</text>{node.type === 'atom' &&
              <text x={point.x} y={point.y + 43} textAnchor="middle" fill="#475569" fontSize="11">{!evidence ? (evidenceError ? '证据不可用' : '读取证据中') : evidence.atomic_skills.find(item => item.atomic_skill_id === node.reference_id)?.contexts.some(item => item.status !== 'unmeasured') ? '已有情境证据 · 点击查看' : '尚未测量'}</text>}
              <title>{node.label}</title>
            </g>; })}
          </svg>
        </section>
        <div className="grid lg:grid-cols-[minmax(0,1fr)_minmax(0,1.3fr)] gap-6">
          <section className="space-y-3">
            <h2 className="text-xl font-semibold">全部匹配节点 · {filtered.length}</h2>{!filtered.length &&
            <p>没有匹配节点，请调整筛选。</p>}
            <div className="max-h-[650px] overflow-y-auto space-y-2">{filtered.map(node =>
              <button key={node.id} onClick={() => select(node)} aria-pressed={node.id === selectedId} className={`w-full text-left p-3 rounded-lg border ${node.id === selectedId ? 'border-primary bg-primary/10' : 'bg-card'}`}>
                <span className="text-xs text-muted-foreground">{labels[node.type]}</span>
                <span className="block font-medium">{node.label}</span></button>)}
            </div>
          </section>
          <section className="border rounded-xl bg-card p-6 space-y-4" aria-live="polite">{selected ? <>
              <p className="text-primary">{labels[selected.type]}</p>
              <h2 className="text-2xl font-bold">{selected.label}</h2>
              <p>{selected.description}</p>{selected.type === 'knowledge' &&
              <p className="text-sm text-primary">课程：{graph.knowledge.find(item => item.knowledge_id === selected.reference_id)?.course}</p>}{atom && <>
                <dl className="space-y-2">
                  <div>
                    <dt className="font-medium">行动</dt>
                    <dd>{atom.action}</dd>
                  </div>
                  <div>
                    <dt className="font-medium">输入</dt>
                    <dd>{atom.input_spec}</dd>
                  </div>
                  <div>
                    <dt className="font-medium">输出</dt>
                    <dd>{atom.output_spec}</dd>
                  </div>
                  <div>
                    <dt className="font-medium">适用边界</dt>
                    <dd>{atom.boundary}</dd>
                  </div>
                </dl>
                <h3 className="font-semibold">可观察评分依据</h3>
                <ul className="list-disc pl-5 space-y-1">{atom.rubric.map(item =>
                  <li key={item}>{item}</li>)}
                </ul>
                <p className="text-sm text-muted-foreground">定义版本 {atom.version} · 情境：{atom.contexts.join('、')}</p>
                <h3 className="font-semibold">我的情境证据</h3>{!evidence &&
                <p>{evidenceError ? '证据无法加载' : '正在加载证据…'}</p>}{personal?.contexts.map(item =>
                <p key={item.context}>{item.context}：{statusLabels[item.status]} · {item.evidence_count} 条证据 · 最近评分 {item.last_score ?? '尚未测量'}</p>)}{personal &&
                <p>{personal.transfer_observed ? '已有跨情境观察' : '尚无跨情境证据'}</p>}
              </>}
              <h3 className="font-semibold">直接关系</h3>{neighborhood.length === 0 &&
              <p>暂无直接关系。</p>}{neighborhood.map((edge, index) => { const source = graph.nodes.find(node => node.id === edge.source);
              const target = graph.nodes.find(node => node.id === edge.target); return <p key={index} className="text-sm">
                <button className="text-primary" onClick={() => source && select(source)}>{source?.label}</button> → {relations[edge.relation]} →
                <button className="text-primary" onClick={() => target && select(target)}>{target?.label}</button></p>; })}
              {relatedTasks.length > 0 && <>
                <h3 className="font-semibold">在任务中练习</h3>{relatedTasks.map(task =>
                <div key={task.skill_id} className="border-t pt-3 space-y-2">
                  <p>{task.display_name} · {task.context}</p>
                  <p className="text-sm text-muted-foreground">交付物：{task.deliverable}</p>
                  <div className="flex flex-wrap gap-3">{['guided','independent','transfer'].map((mode, index) =>
                    <Link key={mode} className="text-primary text-sm" to={`/practice/${encodeURIComponent(task.skill_id)}?mode=${mode}${atom ? `&atoms=${encodeURIComponent(atom.atomic_skill_id)}` : ''}`}>{['引导','独立','迁移'][index]}练习 →</Link>)}
                  </div>
                </div>)}
              </>}
            </> :
            <p>选择节点查看定义、关系和练习入口。</p>}
          </section>
        </div>
      </>}
    </div>;
    }
