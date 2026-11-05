import { Brain, Mic, Code, Camera, Briefcase, ArrowRight, TrendingUp, Sparkles, Target, BarChart3 } from 'lucide-react';
import { Link } from 'react-router-dom';
import SkillCard, { SkillCardProps } from '../components/SkillCard';
import StreakBadge from '../components/StreakBadge';
import MasteryDashboard from '../components/MasteryDashboard';
import { practiceV1Api, practiceApi, systemApi } from '../lib/api';
import { calculateStats, durationLabel } from '../lib/stats';
import { useEffect, useState } from 'react';

const Home = () => {
  const [dailyRecommendations, setDailyRecommendations] = useState<SkillCardProps[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [serviceNotice, setServiceNotice] = useState('');
  const [stats, setStats] = useState<ReturnType<typeof calculateStats> | null>(null);

  useEffect(() => {
    let active = true;
    practiceApi.getRecords('default_user').then(value => {
      if (active) setStats(calculateStats(value.records));
    }).catch(() => { if (active) setServiceNotice('练习统计暂时无法加载，请稍后刷新。'); });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    let active = true;
    systemApi.health().then(health => {
      if (active && !health.ai_configured) setServiceNotice('AI 服务尚未连接，暂时无法生成练习。已有技能和历史记录仍可查看。');
    }).catch(error => { if (active) setServiceNotice(error.message); });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    const fetchSkills = async () => {
      try {
        const skillsResult = await practiceV1Api.getAvailableSkills();
        const skills = skillsResult.skills || [];

        const recommendations: SkillCardProps[] = skills.map((skill, index) => {
          let icon = Mic;
          let color = "bg-indigo-500";
          let duration = "3 min";
          let difficulty: '入门' | '进阶' | '专家' = '入门';

          switch (skill.name) {
            case '演讲':
              icon = Mic;
              color = "bg-indigo-500";
              break;
            case '编程':
              icon = Code;
              color = "bg-blue-500";
              difficulty = '进阶';
              duration = "5 min";
              break;
            case '面试':
              icon = Briefcase;
              color = "bg-pink-500";
              break;
            default:
              icon = Brain;
              color = "bg-emerald-500";
          }

          return {
            id: skill.skill_id,
            title: skill.display_name || skill.name,
            category: skill.name,
            duration: duration,
            difficulty: difficulty,
            description: skill.description || "请完成相关练习",
            icon: icon,
            color: color
          };
        });

        setDailyRecommendations(recommendations);
      } catch (error) {
        console.error('Failed to fetch skills:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSkills();
  }, []);

  return (
    <div className="space-y-10 pb-10">
      {serviceNotice && <div role="status" className="p-4 rounded-lg border border-amber-200 bg-amber-50 text-amber-900">{serviceNotice}</div>}
      {/* Hero Section */}
      <section className="flex flex-col md:flex-row gap-8 items-center justify-between">
        <div className="space-y-4 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-primary/10 text-primary rounded-full text-xs font-semibold uppercase tracking-wider">
            <Sparkles size={14} /> AI 练习 · 学习反馈
          </div>
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight text-foreground">
            你好，学习者。 <br />
            准备好今天的<span className="text-gradient">微技能进化</span>了吗？
          </h1>
          <p className="text-lg text-muted-foreground">
            利用碎片时间选择技能、完成练习，再根据反馈继续巩固。
          </p>
          <div className="flex flex-wrap gap-4 pt-2">
            <Link to="/practice/random" className="px-6 py-3 bg-primary text-white font-medium rounded-xl hover:bg-primary/90 transition-all shadow-lg shadow-primary/25 flex items-center gap-2">
              <Brain size={20} />
              随机开始练习
            </Link>
            <Link to="/skills" className="px-6 py-3 bg-white border border-border text-foreground font-medium rounded-xl hover:bg-secondary transition-all flex items-center gap-2">
              浏览技能库
            </Link>
          </div>
        </div>
        
        {/* Stats Card */}
        <div className="w-full md:w-auto flex flex-row md:flex-col gap-4">
           <Link to="/learning-curve" className="flex-1 p-4 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 text-white border border-indigo-200 flex flex-col items-center justify-center hover:shadow-lg hover:shadow-indigo-200 transition-all">
             <span className="text-sm mb-1">学习曲线</span>
             <span className="text-2xl font-bold">查看详情</span>
           </Link>
           <div className="flex-1 p-4 rounded-xl bg-card border border-border flex flex-col items-center justify-center">
             <span className="text-sm text-muted-foreground mb-1">今日完成练习</span>
             <span className="text-2xl font-bold text-emerald-600">{stats ? stats.todayCount : '—'}</span>
           </div>
        </div>
      </section>

      {/* Daily Recommendations */}
      <section>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Target className="text-primary" />
            可用技能练习
          </h2>
          <Link to="/skills" className="text-sm font-medium text-muted-foreground hover:text-primary flex items-center gap-1 transition-colors">
            全部技能 <ArrowRight size={16} />
          </Link>
        </div>
        
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {isLoading ? (
            <div className="col-span-full text-center py-12">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              <p className="mt-4 text-muted-foreground">加载中...</p>
            </div>
          ) : (
            dailyRecommendations.map((skill) => (
              <SkillCard key={skill.id} {...skill} />
            ))
          )}
        </div>
      </section>

      {/* Progress Overview Section (Simplified) */}
      <section className="bg-gradient-to-br from-slate-900 to-indigo-950 rounded-2xl p-8 text-white relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>
        
        <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-8">
          <div className="space-y-2">
            <h3 className="text-2xl font-bold">回顾你的学习积累</h3>
            <p className="text-indigo-200 max-w-md">
              根据已保存的练习记录查看学习进度，并在学习曲线中回顾原子技能的变化。
            </p>
          </div>
          
          <div className="flex gap-8">
            <div className="text-center">
              <div className="text-3xl font-bold mb-1">{stats ? stats.totalCount : '—'}</div>
              <div className="text-indigo-300 text-sm">已保存练习</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold mb-1">{stats ? durationLabel(stats.weekSeconds) : '—'}</div>
              <div className="text-indigo-300 text-sm">近七天练习时长</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold mb-1">{stats ? stats.avgScore : '—'}</div>
              <div className="text-indigo-300 text-sm">历史平均得分</div>
            </div>
          </div>
        </div>
      </section>


    </div>
  );
};

export default Home;
