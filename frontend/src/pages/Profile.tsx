import { User, Settings, Award, Clock, Calendar, BarChart2, Trash2 } from 'lucide-react';
import StreakBadge from '../components/StreakBadge';
import { useEffect, useState } from 'react';
import { practiceApi } from '../lib/api';
import { Link } from 'react-router-dom';
import { calculateStats, durationLabel, parseTimestamp } from '../lib/stats';
import type { PracticeRecord } from '../types';

const Profile = () => {
  const [recentRecords, setRecentRecords] = useState<PracticeRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // Derived stats from records
  const [totalCount, setTotalCount] = useState<number>(0);
  const [totalDurationStr, setTotalDurationStr] = useState<string>('0秒');
  const [avgScore, setAvgScore] = useState<number>(0);
  const [streakDays, setStreakDays] = useState<number>(0);
  const [completedKinds, setCompletedKinds] = useState({ speech: false, code: false });

  // 获取近期练习记录（展示最新 4 条，简化显示）
  useEffect(() => {
    const fetch = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const res = await practiceApi.getRecords('default_user');
        const allRecords = (res.records || []).slice().sort((a, b) => {
          const ta = parseTimestamp(a.start_time || a.end_time).getTime();
          const tb = parseTimestamp(b.start_time || b.end_time).getTime();
          return tb - ta;
        });
        // 最新 4 条作为预览
        setRecentRecords(allRecords.slice(0, 4));

        const stats = calculateStats(allRecords);
        setTotalCount(stats.totalCount);
        setTotalDurationStr(durationLabel(stats.totalSeconds));
        setAvgScore(stats.avgScore);
        setStreakDays(stats.streakDays);
        setCompletedKinds({ speech: allRecords.some(r => r.category === '演讲'),
          code: allRecords.some(r => r.category === '编程' || r.category === '代码') });
      } catch (err) {
        console.error('获取最近练习失败', err);
        setError('获取最近练习失败');
      } finally {
        setIsLoading(false);
      }
    };
    fetch();

    // 监听全局事件，保存/删除成功后自动刷新列表
    const onRecordSaved = () => {
      console.debug('收到 practice:record-saved 事件，刷新最近练习');
      fetch();
    };
    const onRecordDeleted = () => {
      console.debug('收到 practice:record-deleted 事件，刷新最近练习');
      fetch();
    };
    window.addEventListener('practice:record-saved', onRecordSaved as EventListener);
    window.addEventListener('practice:record-deleted', onRecordDeleted as EventListener);
    return () => {
      window.removeEventListener('practice:record-saved', onRecordSaved as EventListener);
      window.removeEventListener('practice:record-deleted', onRecordDeleted as EventListener);
    };
  }, []);

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">个人中心</h1>
        <button className="p-2 text-muted-foreground hover:bg-secondary rounded-lg">
          <Settings size={20} />
        </button>
      </div>

      {/* User Info Card */}
      <div className="bg-card border border-border rounded-xl p-8 flex flex-col md:flex-row items-center gap-8">
        <div className="relative">
          <div className="w-24 h-24 bg-gradient-to-br from-indigo-100 to-purple-100 rounded-full flex items-center justify-center text-4xl font-bold text-primary border-4 border-white shadow-lg">
            学
          </div>
          <div className="absolute bottom-0 right-0 w-8 h-8 bg-emerald-500 rounded-full border-4 border-white flex items-center justify-center">
            <Award size={14} className="text-white" />
          </div>
        </div>
        
        <div className="flex-1 text-center md:text-left space-y-2">
          <h2 className="text-2xl font-bold">本地学习者</h2>
          <p className="text-muted-foreground">根据已保存的练习记录回顾学习进度</p>
          <div className="flex flex-wrap gap-2 justify-center md:justify-start">
             <span className="px-3 py-1 bg-secondary rounded-full text-xs text-muted-foreground">持续学习</span>
          </div>
        </div>

        <div className="flex gap-8 border-t md:border-t-0 md:border-l border-border pt-6 md:pt-0 pl-0 md:pl-8">
           <div className="text-center">
             <div className="text-2xl font-bold text-foreground">{isLoading ? '—' : totalCount}</div>
             <div className="text-xs text-muted-foreground">练习总数</div>
           </div>
           <div className="text-center">
             <div className="text-2xl font-bold text-foreground">{isLoading ? '—' : totalDurationStr}</div>
             <div className="text-xs text-muted-foreground">练习时长</div>
           </div>
           <div className="text-center">
             <div className="text-2xl font-bold text-foreground">{isLoading ? '—' : avgScore}</div>
             <div className="text-xs text-muted-foreground">平均得分</div>
           </div>
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        {/* Streak Card */}
        <div className="md:col-span-1">
          <div className="bg-card border border-border rounded-xl p-6 h-full flex flex-col items-center justify-center gap-4">
            <h3 className="font-semibold text-muted-foreground self-start w-full cursor-default">连续练习</h3>
            <StreakBadge days={streakDays} />
            <p className="text-sm text-center text-muted-foreground mt-2">
              {streakDays >= 15 ? (
                <>已获得 "毅力大师" 徽章 🎉</>
              ) : (
                <>再坚持 {Math.max(1, 15 - streakDays)} 天即可获得 "毅力大师" 徽章！</>
              )}
            </p>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="md:col-span-2 bg-card border border-border rounded-xl p-6">
          <h3 className="font-semibold mb-6 flex items-center gap-2">
            <Clock size={18} className="text-primary" />
            最近练习记录
          </h3>
          <div className="space-y-4">
            {isLoading ? (
              <div className="text-muted-foreground">加载中...</div>
            ) : error ? (
              <div className="text-red-500">{error}</div>
            ) : recentRecords.length === 0 ? (
              <div className="text-muted-foreground">暂无记录，开始第一次练习吧</div>
            ) : (
              recentRecords.map((rec, i) => (
                <Link
                  key={i}
                  to={`/practice/${rec.skill_id}`}
                  state={{ fromHistory: true, record: rec }}
                  className="block no-underline text-inherit"
                >
                  <div className="flex items-center justify-between p-3 hover:bg-secondary/50 rounded-lg transition-colors border border-transparent hover:border-border/50">
                    <div className="flex items-center gap-4">
                       <div className={`w-2 h-12 rounded-full ${
                         (rec.score || 0) >= 90 ? 'bg-emerald-500' : (rec.score || 0) >= 80 ? 'bg-indigo-500' : 'bg-amber-500'
                       }`} />
                       <div>
                         <h4 className="font-medium text-foreground">{rec.title || rec.skill_name}</h4>
                         <div className="flex items-center gap-2 text-xs text-muted-foreground">
                           <span>{new Date(rec.start_time || rec.end_time).toLocaleString()}</span>
                           <span>·</span>
                           <span>{rec.category}</span>
                         </div>
                       </div>
                    </div>
                    <div className="text-right flex items-center gap-3">
                      <div className="text-lg font-bold text-foreground">{rec.score}</div>
                      <div className="text-xs text-muted-foreground">分</div>
                      <button
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          if (!rec.record_id) return;
                          if (!confirm('确定要删除这条记录吗？')) return;
                          practiceApi.deleteRecord(rec.record_id).then(() => {
                            window.dispatchEvent(new CustomEvent('practice:record-deleted'));
                          }).catch(err => {
                            console.error('删除失败', err);
                            alert('删除失败');
                          });
                        }}
                        className="p-1 rounded hover:bg-red-50 text-red-600"
                        title="删除记录"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                </Link>
              ))
            )}
          </div>
        </div>
      </div>
      
      {/* Achievements Mockup */}
      <div className="bg-card border border-border rounded-xl p-6">
         <h3 className="font-semibold mb-6 flex items-center gap-2">
            <Award size={18} className="text-amber-500" />
            成就展柜
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
             {[
               { name: "首次练习", icon: "🌱", active: totalCount > 0 },
               { name: "演讲起步", icon: "🎙️", active: completedKinds.speech },
               { name: "编程起步", icon: "💻", active: completedKinds.code },
               { name: "连续练习7天", icon: "🔥", active: streakDays >= 7 },
             ].map((ach, i) => (
               <div key={i} className={`flex flex-col items-center justify-center p-4 rounded-xl border ${ ach.active ? 'bg-secondary/30 border-border' : 'bg-secondary/10 border-transparent opacity-50 grayscale'}`}>
                 <div className="text-3xl mb-2">{ach.icon}</div>
                 <div className="text-sm font-medium">{ach.name}</div>
               </div>
             ))}
          </div>
      </div>
    </div>
  );
};

export default Profile;
