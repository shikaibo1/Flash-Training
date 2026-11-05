import { Zap } from 'lucide-react';

interface StreakBadgeProps {
  days: number;
}

const StreakBadge = ({ days }: StreakBadgeProps) => {
  return (
    <div className="flex flex-col items-center justify-center p-4 rounded-xl bg-gradient-to-br from-orange-50 to-amber-50 border border-orange-100 dark:from-orange-950/30 dark:to-amber-950/30 dark:border-orange-900/50">
      <div className="p-3 bg-orange-100 rounded-full mb-2 dark:bg-orange-900/50">
        <Zap className="text-orange-500 fill-orange-500" size={24} />
      </div>
      <span className="text-2xl font-bold text-orange-600 dark:text-orange-400">{days}</span>
      <span className="text-xs text-orange-600/70 font-medium uppercase tracking-wider dark:text-orange-400/70">连续打卡</span>
    </div>
  );
};

export default StreakBadge;