import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Zap, Home, BookOpen, User, Brain, BarChart } from 'lucide-react';

const Header = () => {
  const location = useLocation();
  
  const isActive = (path: string) => {
    return location.pathname === path ? 'text-primary bg-primary/10' : 'text-muted-foreground hover:text-foreground hover:bg-secondary';
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-background/80 backdrop-blur-md px-6 py-4">
      <div className="flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 group">
          <div className="p-2 bg-primary rounded-lg text-primary-foreground transform group-hover:scale-110 transition-transform duration-300">
            <Brain size={24} />
          </div>
          <span className="text-xl font-bold tracking-tight">闪练 <span className="text-primary font-normal">FlashTrain</span></span>
        </Link>
        
        <nav className="hidden xl:flex items-center gap-2">
          <Link to="/" className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${isActive('/')}`}>
            <Home size={18} />
            <span>首页</span>
          </Link>
          <Link to="/skills" className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${isActive('/skills')}`}>
            <BookOpen size={18} />
            <span>任务库</span>
          </Link>
          <Link to="/graph" className={`px-4 py-2 rounded-lg text-sm ${isActive('/graph')}`}>能力图谱</Link>
          <Link to="/learning-curve" className={`px-4 py-2 rounded-lg text-sm ${isActive('/learning-curve')}`}>能力证据</Link>
          <Link to="/history" className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${isActive('/history')}`}>
            <BarChart size={18} />
            <span>练习记录</span>
          </Link>
          <Link to="/profile" className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${isActive('/profile')}`}>
            <User size={18} />
            <span>我的</span>
          </Link>
        </nav>

        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-orange-50 rounded-full border border-orange-100">
            <Zap size={16} className="text-orange-500 fill-orange-500" />
            <span className="text-sm font-bold text-orange-600">持续学习</span>
          </div>
          <div className="h-10 w-10 rounded-full bg-secondary flex items-center justify-center overflow-hidden border border-border">
             <User className="text-muted-foreground" size={20} />
          </div>
        </div>
      </div>
      <nav aria-label="移动端导航" className="flex xl:hidden items-center flex-wrap gap-2 mt-4 text-sm">
        <Link to="/" className={`px-3 py-2 rounded-lg ${isActive('/')}`}>首页</Link>
        <Link to="/skills" className={`px-3 py-2 rounded-lg ${isActive('/skills')}`}>任务库</Link>
        <Link to="/graph" className={`px-3 py-2 rounded-lg ${isActive('/graph')}`}>图谱</Link>
        <Link to="/learning-curve" className={`px-3 py-2 rounded-lg ${isActive('/learning-curve')}`}>证据</Link>
        <Link to="/history" className={`px-3 py-2 rounded-lg ${isActive('/history')}`}>记录</Link>
        <Link to="/profile" className={`px-3 py-2 rounded-lg ${isActive('/profile')}`}>我的</Link>
      </nav>
    </header>
  );
};

export default Header;
