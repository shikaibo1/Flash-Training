type StatsRecord = { score?: number; start_time?: string; end_time?: string; category?: string };

// Legacy timestamps without an offset are interpreted as UTC, as in the importer.
export function parseTimestamp(value?: string): Date {
  if (!value) return new Date(NaN);
  const text = /^\d{4}-\d\d-\d\d[ T]\d\d:\d\d/.test(value) && !/(Z|[+-]\d\d:?\d\d)$/i.test(value)
    ? value.replace(' ', 'T') + 'Z' : value;
  return new Date(text);
}

function dayKey(date: Date) {
  return `${date.getFullYear()}-${date.getMonth() + 1}-${date.getDate()}`;
}

export function calculateStats(records: StatsRecord[], now = new Date()) {
  const today = dayKey(now);
  const weekStart = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 6);
  const dates = new Set<string>();
  let totalSeconds = 0, weekSeconds = 0, todayCount = 0;
  for (const record of records) {
    const start = parseTimestamp(record.start_time), end = parseTimestamp(record.end_time);
    if (Number.isFinite(start.getTime()) && start <= now) {
      const date = dayKey(start);
      dates.add(date);
      if (date === today) todayCount += 1;
      if (Number.isFinite(end.getTime()) && end >= start && end <= now) {
        const seconds = Math.floor((end.getTime() - start.getTime()) / 1000);
        totalSeconds += seconds;
        if (start >= weekStart) weekSeconds += seconds;
      }
    }
  }
  const cursor = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  if (!dates.has(dayKey(cursor))) cursor.setDate(cursor.getDate() - 1);
  let streakDays = 0;
  while (dates.has(dayKey(cursor))) {
    streakDays += 1;
    cursor.setDate(cursor.getDate() - 1);
  }
  const scores = records.map(r => r.score).filter((v): v is number => typeof v === 'number' && Number.isFinite(v) && v >= 0 && v <= 100);
  return { totalCount: records.length, totalSeconds, weekSeconds, todayCount, streakDays,
    avgScore: scores.length ? Math.round(scores.reduce((sum, score) => sum + score, 0) / scores.length) : 0 };
}

export function durationLabel(seconds: number): string {
  if (seconds < 60) return `${seconds}秒`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}分`;
  return `${(seconds / 3600).toFixed(1)}小时`;
}
