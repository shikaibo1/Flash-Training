import { useState, useEffect, useRef } from 'react';
import { Code, Mic, Camera, Briefcase, Search, Filter, Plus, Sparkles } from 'lucide-react';
import SkillCard from '../components/SkillCard';
import { skillsApi, atomicApi } from '../lib/api';
import { Skill, AtomicSkill } from '../types';

const SkillsLibrary = () => {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [atomicSkills, setAtomicSkills] = useState<AtomicSkill[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCustomSkillForm, setShowCustomSkillForm] = useState(false);
  const [customSkillName, setCustomSkillName] = useState('');
  const [creatingSkill, setCreatingSkill] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [error, setError] = useState('');
  
  // 跟踪组件是否已挂载
  const isMounted = useRef(true);

  useEffect(() => {
    isMounted.current = true;
    const fetchSkills = async () => {
      try {
        const [skillsData, atomicSkillsData] = await Promise.all([
          skillsApi.getAllSkills(),
          atomicApi.getAllAtomicSkills()
        ]);
        // 只有在组件仍然挂载时才更新状态
        if (isMounted.current) {
          setSkills(skillsData.skills);
          setAtomicSkills(atomicSkillsData.atomic_skills);
        }
      } catch (error) {
        console.error('Failed to fetch skills:', error);
        if (isMounted.current) setError(error instanceof Error ? error.message : '加载技能失败');
      } finally {
        // 只有在组件仍然挂载时才更新加载状态
        if (isMounted.current) {
          setLoading(false);
        }
      }
    };

    fetchSkills();
    
    // Cleanup 函数：组件卸载时设置标记
    return () => {
      isMounted.current = false;
    };
  }, []);

  // 映射技能图标
  const getIconComponent = (category: string) => {
    switch (category) {
      case '演讲':
        return Mic;
      case '编程':
        return Code;
      case '摄影':
        return Camera;
      case '面试':
        return Briefcase;
      default:
        return Code;
    }
  };

  // 创建自定义技能
  const handleCreateCustomSkill = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customSkillName.trim()) return;

    setCreatingSkill(true);
    setError('');
    try {
      const result = await skillsApi.createCustomSkill(customSkillName);
      if (result.skill && isMounted.current) {
        // 重新获取技能列表
        const updatedSkills = await skillsApi.getAllSkills();
        if (isMounted.current) {
          setSkills(updatedSkills.skills);
          setCustomSkillName('');
          setShowCustomSkillForm(false);
        }
      }
    } catch (error) {
      console.error('Failed to create custom skill:', error);
      if (isMounted.current) setError(error instanceof Error ? error.message : '创建技能失败');
    } finally {
      if (isMounted.current) {
        setCreatingSkill(false);
      }
    }
  };

  // 删除技能
  const handleDeleteSkill = async (skillId: string) => {
    if (!confirm('确定要移除这个技能吗？历史练习记录会保留。')) {
      return;
    }

    try {
      await skillsApi.deleteSkill(skillId);
      // 重新获取技能列表
      const updatedSkills = await skillsApi.getAllSkills();
      if (isMounted.current) {
        setSkills(updatedSkills.skills);
      }
    } catch (error) {
      console.error('Failed to delete skill:', error);
    }
  };

  // 过滤技能
  const filteredSkills = skills.filter(skill => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      skill.name.toLowerCase().includes(query) ||
      skill.display_name.toLowerCase().includes(query) ||
      skill.description.toLowerCase().includes(query)
    );
  });

  return (
    <div className="space-y-8">
      {error && <div role="alert" className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg">{error}</div>}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-foreground">技能原子库</h1>
          <p className="text-muted-foreground mt-1">探索 200+ 个可即时练习的微技能模块</p>
        </div>
        
        <div className="flex items-center gap-2 w-full md:w-auto">
          <div className="flex items-center gap-2 w-full md:w-auto bg-card border border-border rounded-lg px-3 py-2 shadow-sm">
            <Search className="text-muted-foreground" size={20} />
            <input 
              type="text" 
              placeholder="搜索技能 (如: 演讲, Python...)" 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-transparent border-none outline-none text-sm w-full md:w-64 placeholder:text-muted-foreground/70"
            />
          </div>
          <button 
            onClick={() => setShowCustomSkillForm(!showCustomSkillForm)}
            className="px-4 py-2 rounded-lg bg-primary text-primary-foreground font-medium text-sm flex items-center gap-2 hover:bg-primary/90 transition-colors"
          >
            <Plus size={16} />
            自定义技能
          </button>
        </div>
      </div>

      {/* 自定义技能创建表单 */}
      {showCustomSkillForm && (
        <div className="bg-card border border-border rounded-lg p-6 shadow-sm">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Sparkles size={20} className="text-primary" />
            创建自定义技能
          </h2>
          <form onSubmit={handleCreateCustomSkill} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">技能名称</label>
              <input 
                type="text" 
                value={customSkillName}
                onChange={(e) => setCustomSkillName(e.target.value)}
                placeholder="输入技能名称，如：批判性思维"
                className="w-full px-4 py-2 border border-border rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
              />
            </div>
            <div className="flex gap-3">
              <button 
                type="submit" 
                disabled={creatingSkill}
                className="px-6 py-2 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {creatingSkill ? '创建中...' : '创建技能'}
              </button>
              <button 
                type="button" 
                onClick={() => setShowCustomSkillForm(false)}
                className="px-6 py-2 border border-border rounded-lg font-medium hover:bg-secondary transition-colors"
              >
                取消
              </button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <div className="text-center py-12">加载中...</div>
      ) : (
        <>
          <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
            {/* 分类按钮 */}
            <button className="px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap bg-primary text-primary-foreground">
              全部
            </button>
            {/* 动态生成分类 */}
            {Array.from(new Set(skills.map(s => s.name))).map((cat) => (
              <button 
                key={cat}
                className="px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap bg-secondary text-secondary-foreground hover:bg-secondary/80"
              >
                {cat}
              </button>
            ))}
            <button className="ml-auto px-4 py-2 rounded-full border border-border text-sm font-medium flex items-center gap-2 hover:bg-secondary transition-colors">
              <Filter size={16} /> 筛选
            </button>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredSkills.map((skill) => (
              <SkillCard 
                key={skill.skill_id}
                id={skill.skill_id}
                title={skill.display_name}
                category={skill.name}
                duration="3 min"  // 暂时使用固定值，以后可以从API获取
                difficulty="入门"  // 暂时使用固定值，以后可以从API获取
                description={skill.description}
                icon={getIconComponent(skill.name)}
                color="bg-blue-500"  // 暂时使用固定值，以后可以从API获取
                onDelete={handleDeleteSkill}
                showDelete={true}
              />
            ))}
          </div>

          {/* 原子技能展示 */}
          <div className="mt-12">
            <h2 className="text-2xl font-bold mb-6">原子技能</h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {atomicSkills.map((skill) => (
                <div 
                  key={skill.atomic_skill_id}
                  className="bg-card border border-border rounded-lg p-4 hover:shadow-md transition-shadow"
                >
                  <h3 className="font-semibold text-lg mb-2">{skill.name}</h3>
                  <p className="text-muted-foreground text-sm mb-3">{skill.description}</p>
                  <div className="flex flex-wrap gap-2">
                    {skill.categories.map((category, index) => (
                      <span 
                        key={index}
                        className="text-xs px-2 py-1 bg-secondary text-secondary-foreground rounded-full"
                      >
                        {category}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default SkillsLibrary;
