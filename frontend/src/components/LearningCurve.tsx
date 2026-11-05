"use client"

import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { ChartContainer, ChartTooltipContent } from './ui/chart';
import { knowledgeTracingApi } from '../lib/api';

interface LearningCurveProps {
  userId: string;
  atomicSkillId: string;
  days?: number;
}

const LearningCurve: React.FC<LearningCurveProps> = ({ userId, atomicSkillId, days = 30 }) => {
  const [learningCurve, setLearningCurve] = useState<{ timestamp: string; mastery: number; performance: number }[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchLearningCurve = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await knowledgeTracingApi.getLearningCurve(userId, atomicSkillId, days);
        if (response.error) {
          throw new Error(response.msg);
        }
        setLearningCurve(response.data.learning_curve);
      } catch (err) {
        setError('获取学习曲线失败');
        console.error('Error fetching learning curve:', err);
      } finally {
        setLoading(false);
      }
    };

    if (userId && atomicSkillId) {
      fetchLearningCurve();
    }
  }, [userId, atomicSkillId, days]);

  // 准备图表数据
  const chartData = learningCurve.map(item => ({
    date: new Date(item.timestamp).toLocaleDateString(),
    mastery: parseFloat((item.mastery * 100).toFixed(2)), // 转换为百分比
    performance: parseFloat((item.performance * 100).toFixed(2)) // 转换为百分比
  }));

  if (loading) {
    return <div className="flex items-center justify-center p-8">加载中...</div>;
  }

  if (error) {
    return <div className="flex items-center justify-center p-8 text-red-500">{error}</div>;
  }

  if (chartData.length === 0) {
    return <div className="flex items-center justify-center p-8 text-gray-500">暂无学习数据</div>;
  }

  return (
    <div className="w-full p-4 bg-white rounded-lg shadow-sm border">
      <h3 className="text-lg font-medium mb-4">学习曲线</h3>
      <ChartContainer
        config={{
          mastery: {
            label: '掌握度',
            color: '#3b82f6',
          },
          performance: {
            label: '表现',
            color: '#10b981',
          },
        }}
      >
        <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis domain={[0, 100]} label={{ value: '百分比 (%)', angle: -90, position: 'insideLeft' }} />
          <Tooltip content={<ChartTooltipContent />} />
          <Line type="monotone" dataKey="mastery" stroke="#3b82f6" strokeWidth={2} />
          <Line type="monotone" dataKey="performance" stroke="#10b981" strokeWidth={2} />
        </LineChart>
      </ChartContainer>
    </div>
  );
};

export default LearningCurve;
