import { Play, Clock, Star, ArrowRight, Trash2 } from 'lucide-react';
import { Link } from 'react-router-dom';

export interface SkillCardProps {
  id: string;
  title: string;
  category: string;
  duration: string;
  difficulty: '入门' | '进阶' | '专家';
  description: string;
  icon: React.ElementType;
  color: string;
  onDelete?: (id: string) => void;
  showDelete?: boolean;
}

const SkillCard = ({ id, title, category, duration, difficulty, description, icon: Icon, color, onDelete, showDelete = false }: SkillCardProps) => {
  return (
    <div className="group relative flex flex-col bg-card border border-border rounded-xl p-6 transition-all duration-300 hover:shadow-custom hover:border-primary/30 h-full">
      {showDelete && onDelete && (
        <button 
          onClick={() => onDelete(id)}
          className="absolute top-3 right-3 p-1.5 rounded-full bg-red-50 text-red-500 hover:bg-red-100 transition-colors"
          title="删除技能"
        >
          <Trash2 size={16} />
        </button>
      )}
      
      <div className={`w-12 h-12 rounded-lg flex items-center justify-center mb-4 transition-colors ${color}`}>
        <Icon size={24} className="text-white" />
      </div>
      
      <div className="flex-1">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-primary px-2 py-1 bg-primary/5 rounded-full">{category}</span>
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <Clock size={12} />
            <span>{duration}</span>
          </div>
        </div>
        
        <h3 className="text-lg font-bold text-foreground mb-2 group-hover:text-primary transition-colors">{title}</h3>
        <p className="text-sm text-muted-foreground mb-4 line-clamp-2">{description}</p>
      </div>
      
      <div className="flex items-center justify-between mt-auto pt-4 border-t border-border/50">
        <div className="flex gap-0.5">
          {[1, 2, 3].map((star) => (
            <Star 
              key={star} 
              size={14} 
              className={star <= (difficulty === '入门' ? 1 : difficulty === '进阶' ? 2 : 3) ? "text-amber-400 fill-amber-400" : "text-muted"} 
            />
          ))}
        </div>
        <Link 
          to={`/practice/${id}`}
          className="flex items-center gap-1 text-sm font-medium text-primary hover:gap-2 transition-all"
        >
          开始练习 <ArrowRight size={16} />
        </Link>
      </div>
    </div>
  );
};

export default SkillCard;