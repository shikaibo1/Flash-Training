import test from 'node:test';
import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
import { join } from 'node:path';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

const load = name => import(pathToFileURL(join(process.env.FLASH_TEST_DIR, `${name}.mjs`)));
const { default: FeedbackPanel } = await load('FeedbackPanel');
const { scoreDimensions } = await load('feedback');
const { calculateStats, parseTimestamp } = await load('stats');
const { sessionCache } = await load('sessionCache');
const feedback = { score: 42, strengths: ['尝试换元'], improvements: ['检查积分限'], aiComment: '需要继续练习' };

test('评分面板显示真实分项，重复渲染结果一致', () => {
  const props = { ...feedback, dimensions: scoreDimensions({ a1: 4.2, a2: 0 }, { a1: '换元', a2: '积分限' }) };
  const first = renderToStaticMarkup(React.createElement(FeedbackPanel, props));
  assert.equal(first, renderToStaticMarkup(React.createElement(FeedbackPanel, props)));
  assert.ok(first.includes('换元') && first.includes('积分限'));
  assert.ok(first.includes('width:42%') && first.includes('width:0%'));
});

test('历史没有分项数据时不生成虚构维度', () => {
  const html = renderToStaticMarkup(React.createElement(FeedbackPanel, feedback));
  assert.ok(html.includes('这条记录未保存分项评分'));
  assert.ok(!html.includes('width:'));
});

test('无效分数不渲染为有效维度，零分保留', () => {
  assert.deepEqual(scoreDimensions({ zero: 0, missing: NaN, invalid: 80, negative: -1 }),
    [{ id: 'zero', name: 'zero', score: 0 }]);
});

test('很久以前的连续学习不算当前连续打卡', () => {
  const stats = calculateStats([{ start_time: '2020-01-01T12:00:00Z', score: 80 },
    { start_time: '2020-01-02T12:00:00Z', score: 90 }], new Date(2026, 10, 6, 12));
  assert.equal(stats.streakDays, 0);
  assert.equal(stats.todayCount, 0);
});

test('连续练习和今日计数按设备当地日历计算', () => {
  const now = new Date(2026, 10, 6, 23, 30);
  const records = [0, 1, 2].map(offset => ({
    start_time: new Date(2026, 10, 6 - offset, 22).toISOString(),
    end_time: new Date(2026, 10, 6 - offset, 22, 1).toISOString(), score: 80,
  }));
  const stats = calculateStats(records, now);
  assert.equal(stats.streakDays, 3);
  assert.equal(stats.todayCount, 1);
  assert.equal(stats.totalSeconds, 180);
  assert.equal(stats.weekSeconds, 180);
});

test('坏日期和负时长不进入练习时长统计', () => {
  const stats = calculateStats([{ start_time: 'invalid', end_time: 'invalid' },
    { start_time: '2026-01-02T12:00:00Z', end_time: '2026-01-01T12:00:00Z' }]);
  assert.equal(stats.totalSeconds, 0);
  assert.equal(parseTimestamp('2026-01-01 12:00:00').toISOString(), '2026-01-01T12:00:00.000Z');
});

test('浏览器存储不可用不会让已成功的请求变成失败', () => {
  const descriptor = Object.getOwnPropertyDescriptor(globalThis, 'sessionStorage');
  Object.defineProperty(globalThis, 'sessionStorage', { configurable: true, get() { throw new Error('Storage denied'); } });
  try {
    assert.equal(sessionCache.read('session'), null);
    assert.equal(sessionCache.write('draft', 'answer'), false);
    assert.doesNotThrow(() => sessionCache.remove('session'));
  } finally {
    if (descriptor) Object.defineProperty(globalThis, 'sessionStorage', descriptor);
    else delete globalThis.sessionStorage;
  }
});
