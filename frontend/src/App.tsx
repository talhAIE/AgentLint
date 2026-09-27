import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { LayoutDashboard, Database, Search, FileText, ShieldCheck, Wrench, CheckCircle2, Rocket, Sparkles } from "lucide-react";
import OverviewPage from "./pages/OverviewPage";
import SourcesPage from "./pages/SourcesPage";
import FindingsPage from "./pages/FindingsPage";
import EvidencePage from "./pages/EvidencePage";
import PolicyPage from "./pages/PolicyPage";
import RepairPage from "./pages/RepairPage";
import VerificationPage from "./pages/VerificationPage";
import TechBackground from "./components/TechBackground";

const queryClient = new QueryClient();

function NavLink({ to, icon: Icon, badge, children }: { to: string, icon: any, badge?: number, children: React.ReactNode }) {
  const location = useLocation();
  const isActive = location.pathname === to;
  return (
    <Link 
      to={to} 
      className={`flex items-center justify-between px-4 py-3 rounded-2xl transition-all duration-300 ${
        isActive 
          ? "bg-[#00D8FF] text-[#0B0F19] shadow-[0_4px_15px_rgba(0,216,255,0.4)]" 
          : "text-text-muted hover:text-white hover:bg-white/5"
      }`}
    >
      <div className="flex items-center gap-4">
        <Icon className={`w-5 h-5 ${isActive ? "text-[#0B0F19]" : ""}`} />
        <span className="font-semibold text-sm">{children}</span>
      </div>
      {badge !== undefined && (
        <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${isActive ? 'bg-[#0B0F19] text-white' : 'bg-[#6D28D9] text-white'}`}>
          {badge}
        </span>
      )}
    </Link>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="relative flex h-screen w-full font-sans overflow-hidden bg-[#0B0F19] text-white">
          <TechBackground />
          
          {/* Sidebar */}
          <div className="relative z-10 w-72 bg-[#0F172A] border-r border-white/5 p-6 flex flex-col h-full overflow-hidden shadow-2xl">
            {/* Logo */}
            <div className="flex items-center gap-3 mb-10 pl-2">
              <div className="w-10 h-10 rounded-xl bg-[#00D8FF] flex items-center justify-center shadow-[0_0_20px_rgba(0,216,255,0.4)] shrink-0">
                <ShieldCheck className="w-6 h-6 text-[#0B0F19]" />
              </div>
              <div>
                <h1 className="text-2xl font-black text-white tracking-tight leading-none">AgentLint</h1>
                <p className="text-[10px] text-text-muted font-medium mt-1 uppercase tracking-widest">Smarter Code. Healthier Agents.</p>
              </div>
            </div>
            
            <nav className="flex flex-col gap-2 flex-1">
              <NavLink to="/" icon={LayoutDashboard}>Overview</NavLink>
              <NavLink to="/sources" icon={Database}>Sources</NavLink>
              <NavLink to="/findings" icon={Search} badge={27}>Findings</NavLink>
              <NavLink to="/evidence" icon={FileText}>Evidence</NavLink>
              <NavLink to="/policy" icon={ShieldCheck}>Policy</NavLink>
              <NavLink to="/repair" icon={Wrench}>Repair</NavLink>
              <NavLink to="/verification" icon={CheckCircle2}>Verification</NavLink>
            </nav>
            
            {/* Bottom abstract shape */}
            <div className="absolute bottom-0 left-0 w-full h-48 pointer-events-none opacity-40">
              <svg viewBox="0 0 200 200" className="absolute bottom-0 w-full h-full text-[#00D8FF]">
                <path fill="currentColor" d="M0,200 L0,150 C50,180 100,100 200,160 L200,200 Z" opacity="0.2" />
                <path fill="currentColor" d="M0,200 L0,170 C60,200 120,120 200,180 L200,200 Z" opacity="0.1" />
              </svg>
            </div>

            <div className="relative z-10 mt-auto flex flex-col gap-3 pt-6 border-t border-white/5">
              <button 
                onClick={async () => {
                  try {
                    await fetch('/demo/load/inconsistent-js-repo', { method: 'POST' });
                    window.location.reload();
                  } catch (e) {
                    console.error(e);
                  }
                }}
                className="group relative overflow-hidden bg-[#1E293B] hover:bg-[#2D3748] text-sm py-3 px-4 rounded-xl text-left transition-all border border-white/10 hover:border-[#00D8FF]/50 hover:shadow-[0_0_15px_rgba(0,216,255,0.2)] flex items-center justify-between"
              >
                <div className="flex items-center gap-3 relative z-10">
                  <Rocket className="w-4 h-4 text-[#00D8FF]" />
                  <div>
                    <div className="text-[10px] text-text-muted uppercase font-bold tracking-wider mb-0.5">Development</div>
                    <div className="font-semibold text-white">Load Demo Repo</div>
                  </div>
                </div>
                <div className="absolute inset-0 bg-gradient-to-r from-[#00D8FF]/0 via-[#00D8FF]/10 to-[#00D8FF]/0 -translate-x-full group-hover:animate-[shimmer_2s_infinite]" />
              </button>
            </div>
          </div>

          {/* Main content */}
          <div className="relative z-10 flex-1 flex flex-col min-w-0 bg-transparent h-full overflow-hidden">
            {/* Topbar */}
            <div className="px-10 pt-10 pb-6 shrink-0 flex items-start justify-between">
              <div>
                <h2 className="text-4xl font-bold text-white mb-2">Dashboard</h2>
                <p className="text-text-muted">Here's a quick overview of your repository health and findings.</p>
              </div>
              <div className="flex items-center gap-2 text-right">
                <div className="text-sm">
                  <p className="text-text-muted">Better code</p>
                  <p className="font-medium text-white">Builds a brighter future</p>
                </div>
                <Sparkles className="w-5 h-5 text-[#00D8FF]" />
              </div>
            </div>
            
            {/* Page content */}
            <div className="px-10 pb-10 overflow-auto flex-1">
              <Routes>
                <Route path="/" element={<OverviewPage />} />
                <Route path="/sources" element={<SourcesPage />} />
                <Route path="/findings" element={<FindingsPage />} />
                <Route path="/evidence" element={<EvidencePage />} />
                <Route path="/policy" element={<PolicyPage />} />
                <Route path="/repair" element={<RepairPage />} />
                <Route path="/verification" element={<VerificationPage />} />
              </Routes>
            </div>
          </div>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
