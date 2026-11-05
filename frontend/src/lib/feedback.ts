export type ScoreDimension = { id: string; name: string; score: number };

// Only use values actually returned by the server. Missing values stay missing.
export function scoreDimensions(scores: Record<string, number> = {}, names: Record<string, string> = {}): ScoreDimension[] {
  return Object.entries(scores)
    .filter(([, value]) => typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 10)
    .map(([id, value]) => ({ id, name: names[id] || id, score: Math.round(value * 100) / 10 }));
}
