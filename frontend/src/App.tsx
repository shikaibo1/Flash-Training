import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { lazy, Suspense } from "react";
import Header from "./components/Header";

const KnowledgeGraph = lazy(() => import("./pages/KnowledgeGraph"));
const Home = lazy(() => import("./pages/Home"));
const SkillsLibrary = lazy(() => import("./pages/SkillsLibrary"));
const PracticeSession = lazy(() => import("./pages/PracticeSession"));
const Profile = lazy(() => import("./pages/Profile"));
const PracticeHistory = lazy(() => import("./pages/PracticeHistory"));
const LearningCurve = lazy(() => import("./pages/LearningCurve"));

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <BrowserRouter>
      <div className="min-h-screen flex flex-col items-center bg-background">
        <div className="w-full max-w-[1440px] flex flex-col min-h-screen shadow-2xl bg-background border-x border-border/50">
          <Header />
          <main className="flex-1 w-full p-6 md:p-8 overflow-y-auto">
            <Suspense fallback={<div role="status" className="py-12 text-center text-muted-foreground">正在加载页面...</div>}>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/graph" element={<KnowledgeGraph />} />
              <Route path="/skills" element={<SkillsLibrary />} />
              <Route path="/practice/:id" element={<PracticeSession />} />
              <Route path="/practice" element={<PracticeSession />} />
              <Route path="/profile" element={<Profile />} />
              <Route path="/history" element={<PracticeHistory />} />
              <Route path="/learning-curve" element={<LearningCurve />} />
              <Route path="*" element={<div className="py-12 text-center"><h1 className="text-2xl font-bold">页面不存在</h1><a className="text-primary" href="/">返回首页</a></div>} />
            </Routes>
            </Suspense>
          </main>
        </div>
      </div>
    </BrowserRouter>
  </QueryClientProvider>
);

export default App;
