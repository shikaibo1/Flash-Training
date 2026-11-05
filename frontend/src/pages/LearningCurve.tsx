import { BarChart3, ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';
import MasteryDashboard from '../components/MasteryDashboard';

const LearningCurve = () => {
  return (
    <div className="space-y-6 pb-10">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link to="/" className="flex items-center gap-2 text-muted-foreground hover:text-primary transition-colors">
          <ArrowLeft size={20} />
          <span>返回首页</span>
        </Link>
      </div>

      {/* Learning Curve Section */}
      <section>
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <BarChart3 className="text-primary" />
            知识掌握度追踪
          </h1>
        </div>
        <MasteryDashboard userId="default_user" />
      </section>
    </div>
  );
};

export default LearningCurve;