"use client"

import React, { useState, useEffect } from 'react';
import { knowledgeTracingApi } from '../lib/api';
import type { Mastery } from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Progress } from './ui/progress';
import { Button } from './ui/button';
import LearningCurve from './LearningCurve';

interface MasteryDashboardProps {
  userId: string;
}

const MasteryDashboard: React.FC<MasteryDashboardProps> = ({ userId }) => {
  const [masteryData, setMasteryData] = useState<Mastery[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSkill, setSelectedSkill] = useState<string | null>(null);

  // 添加一个状态变量来触发数据刷新
  const [refreshKey, setRefreshKey] = useState(0);

  // 手动刷新数据的函数
  const refreshMasteryData = () => {
    setRefreshKey(prev => prev + 1);
  };

  useEffect(() => {
    const fetchMasteryData = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await knowledgeTracingApi.getAllMastery(userId);
        if (response.error) {
          throw new Error(response.msg);
        }
        setMasteryData(response.data.atomic_skills);
        // 默认选择第一个技能
        if (response.data.atomic_skills.length > 0) {
          setSelectedSkill(response.data.atomic_skills[0].atomic_skill_id);
        }
      } catch (err) {
        console.error('获取掌握度数据失败:', err);
        setError('获取掌握度数据失败');
      } finally {
        setLoading(false);
      }
    };

    if (userId) {
      fetchMasteryData();
    }
  }, [userId, refreshKey]);

  // 监听全局练习完成事件，自动刷新数据
  useEffect(() => {
    const handlePracticeCompleted = () => {
      refreshMasteryData();
    };

    // 监听全局事件
    window.addEventListener('practice:completed', handlePracticeCompleted);

    // 组件卸载时移除事件监听器
    return () => {
      window.removeEventListener('practice:completed', handlePracticeCompleted);
    };
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center p-8">加载中...</div>;
  }

  if (error) {
    return <div className="flex items-center justify-center p-8 text-red-500">{error}</div>;
  }

  if (masteryData.length === 0) {
    return <div className="flex items-center justify-center p-8 text-gray-500">暂无掌握度数据</div>;
  }

  return (
    <div className="w-full space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>知识掌握度仪表盘</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {masteryData.map((skill) => (
              <div key={skill.atomic_skill_id} className="border rounded-lg p-4">
                <div className="flex justify-between items-center mb-2">
                  <h4 className="font-medium">{skill.name}</h4>
                  <span className="text-sm font-semibold">
                    {Math.round(skill.mastery * 100)}%
                  </span>
                </div>
                <Progress value={skill.mastery * 100} className="h-2 mb-2" />
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full mt-2"
                  onClick={() => setSelectedSkill(skill.atomic_skill_id)}
                >
                  查看详情
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {selectedSkill && (
        <LearningCurve
          userId={userId}
          atomicSkillId={selectedSkill}
          days={30}
        />
      )}
    </div>
  );
};

export default MasteryDashboard;
