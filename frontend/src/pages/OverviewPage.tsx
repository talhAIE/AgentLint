import { useQuery } from "@tanstack/react-query";
import { getSources, getFindings } from "../api/endpoints";
import { motion } from "framer-motion";
import { FolderGit2, FileCode2, AlertTriangle, Eye, BarChart2, PieChart } from "lucide-react";

export default function OverviewPage() {
  const { data: sources, isLoading: loadingSources } = useQuery({ queryKey: ["sources"], queryFn: getSources, retry: false });
  const { data: findings, isLoading: loadingFindings } = useQuery({ queryKey: ["findings"], queryFn: getFindings, retry: false });

  if (loadingSources || loadingFindings) return (
    <div className="flex items-center justify-center h-[500px]">
      <div className="animate-pulse flex flex-col items-center gap-4">
        <div className="w-12 h-12 border-4 border-[#00D8FF] border-t-transparent rounded-full animate-spin" />
        <p className="text-[#00D8FF] font-medium tracking-widest">ANALYZING REPOSITORY...</p>
      </div>
    </div>
  );
  if (!sources || !findings) return <div className="p-4 text-text-muted">No scan data found. Run a scan or load a demo.</div>;

  const repoPath = sources.repo_path || "Unknown";
  const numSources = sources.sources?.length || 0;
  
  const findingsArray = findings.findings || [];
  const highCritical = findingsArray.filter((f: any) => f.severity === "high" || f.severity === "critical").length;
  
  const containerVariants = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.1 } }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    show: { y: 0, opacity: 1, transition: { type: "spring" as const, stiffness: 300, damping: 24 } }
  };

  // Fake chart data matching the visual
  const chartData = [
    { id: 'F01', label: 'Code Smells', value: 4, color: 'from-[#00D8FF] to-[#00D8FF]/80' },
    { id: 'F02', label: 'Security Issues', value: 12, color: 'from-[#8B5CF6] to-[#8B5CF6]/80' },
    { id: 'F03', label: 'Performance Issues', value: 11, color: 'from-[#EC4899] to-[#EC4899]/80' },
    { id: 'F04', label: 'Best Practice Violations', value: 3, color: 'from-[#F59E0B] to-[#F59E0B]/80' },
    { id: 'F05', label: 'Maintainability Issues', value: 15, color: 'from-[#10B981] to-[#10B981]/80' },
  ];
  const maxValue = Math.max(...chartData.map(d => d.value));

  return (
    <motion.div variants={containerVariants} initial="hidden" animate="show" className="flex flex-col gap-6 h-full">
      
      {/* Top 4 Cards */}
      <motion.div variants={itemVariants} className="grid grid-cols-4 gap-6">
        
        {/* Card 1: Repository */}
        <div className="relative overflow-hidden bg-gradient-to-br from-[#1E3A8A]/40 to-[#0B0F19] border border-[#1E3A8A] p-6 rounded-2xl flex flex-col justify-between group h-40 shadow-lg">
          <div className="flex items-start gap-4 mb-2">
            <div className="p-3 bg-gradient-to-br from-[#3B82F6] to-[#60A5FA] rounded-xl shadow-lg">
              <FolderGit2 className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-xs font-bold text-[#93C5FD] uppercase tracking-wider mb-1">Repository</h3>
              <p className="text-xl font-bold text-white truncate w-40" title={repoPath}>
                {repoPath.split(/[/\\]/).pop()}
              </p>
            </div>
          </div>
          <p className="text-xs text-text-muted">Last scanned 2 hours ago</p>
          {/* Wave */}
          <div className="absolute -bottom-2 -right-2 w-32 h-16 opacity-50">
            <svg viewBox="0 0 100 50" className="w-full h-full text-[#3B82F6]">
              <path fill="currentColor" d="M0,50 C30,20 60,30 100,10 L100,50 Z" />
            </svg>
          </div>
        </div>
        
        {/* Card 2: Instruction Sources */}
        <div className="relative overflow-hidden bg-gradient-to-br from-[#064E3B]/40 to-[#0B0F19] border border-[#064E3B] p-6 rounded-2xl flex flex-col justify-between group h-40 shadow-lg">
          <div className="flex justify-between items-start">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-gradient-to-br from-[#10B981] to-[#34D399] rounded-xl shadow-lg">
                <FileCode2 className="w-5 h-5 text-white" />
              </div>
              <h3 className="text-xs font-bold text-[#6EE7B7] uppercase tracking-wider mt-1">Instruction Sources</h3>
            </div>
          </div>
          <div className="flex justify-between items-end">
            <p className="text-4xl font-black text-white">{numSources}</p>
            <div className="text-right">
              <p className="text-sm font-bold text-[#10B981]">↑ +0%</p>
              <p className="text-[10px] text-text-muted">vs. last scan</p>
            </div>
          </div>
          {/* Wave */}
          <div className="absolute -bottom-2 -right-2 w-32 h-16 opacity-50">
            <svg viewBox="0 0 100 50" className="w-full h-full text-[#10B981]">
              <path fill="currentColor" d="M0,50 C30,40 50,10 100,20 L100,50 Z" />
            </svg>
          </div>
        </div>
        
        {/* Card 3: High/Critical */}
        <div className="relative overflow-hidden bg-gradient-to-br from-[#831843]/40 to-[#0B0F19] border border-[#831843] p-6 rounded-2xl flex flex-col justify-between group h-40 shadow-lg">
          <div className="flex justify-between items-start">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-gradient-to-br from-[#F43F5E] to-[#FB7185] rounded-xl shadow-lg">
                <AlertTriangle className="w-5 h-5 text-white" />
              </div>
              <h3 className="text-xs font-bold text-[#FDA4AF] uppercase tracking-wider mt-1">High/Critical</h3>
            </div>
          </div>
          <div className="flex justify-between items-end">
            <p className="text-4xl font-black text-white">{highCritical}</p>
            <div className="text-right">
              <p className="text-sm font-bold text-[#F43F5E]">↓ -27%</p>
              <p className="text-[10px] text-text-muted">vs. last scan</p>
            </div>
          </div>
          {/* Wave */}
          <div className="absolute -bottom-2 -right-2 w-32 h-16 opacity-50">
            <svg viewBox="0 0 100 50" className="w-full h-full text-[#F43F5E]">
              <path fill="currentColor" d="M0,50 C40,20 60,30 100,5 L100,50 Z" />
            </svg>
          </div>
        </div>
        
        {/* Card 4: Total Findings */}
        <div className="relative overflow-hidden bg-gradient-to-br from-[#4C1D95]/40 to-[#0B0F19] border border-[#4C1D95] p-6 rounded-2xl flex flex-col justify-between group h-40 shadow-lg">
          <div className="flex justify-between items-start">
            <div className="flex items-start gap-4">
              <div className="p-3 bg-gradient-to-br from-[#8B5CF6] to-[#A78BFA] rounded-xl shadow-lg">
                <Eye className="w-5 h-5 text-white" />
              </div>
              <h3 className="text-xs font-bold text-[#C4B5FD] uppercase tracking-wider mt-1">Total Findings</h3>
            </div>
          </div>
          <div className="flex justify-between items-end">
            <p className="text-4xl font-black text-white">{findingsArray.length}</p>
            <div className="text-right">
              <p className="text-sm font-bold text-[#10B981]">↓ -15%</p>
              <p className="text-[10px] text-text-muted">vs. last scan</p>
            </div>
          </div>
          {/* Wave */}
          <div className="absolute -bottom-2 -right-2 w-32 h-16 opacity-50">
            <svg viewBox="0 0 100 50" className="w-full h-full text-[#8B5CF6]">
              <path fill="currentColor" d="M0,50 C30,30 70,40 100,10 L100,50 Z" />
            </svg>
          </div>
        </div>
      </motion.div>

      {/* Chart Area */}
      <motion.div variants={itemVariants} className="bg-[#111827]/80 backdrop-blur-xl border border-white/5 p-8 rounded-2xl flex-1 flex flex-col min-h-[400px] shadow-2xl relative overflow-hidden">
        
        <div className="flex justify-between items-center mb-10">
          <div className="flex items-center gap-4">
            <div className="p-2 bg-[#00D8FF]/10 rounded-xl">
              <BarChart2 className="w-6 h-6 text-[#00D8FF]" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white mb-1">Findings Types Distribution</h3>
              <p className="text-sm text-text-muted">Breakdown of issues found in your repository</p>
            </div>
          </div>
          
          <div className="flex bg-[#1F2937] p-1 rounded-xl">
            <button className="flex items-center gap-2 px-4 py-2 bg-[#00D8FF] text-[#0B0F19] font-bold rounded-lg text-sm transition-colors shadow-[0_0_15px_rgba(0,216,255,0.3)]">
              <BarChart2 className="w-4 h-4" /> Bar Chart
            </button>
            <button className="flex items-center gap-2 px-4 py-2 text-text-muted hover:text-white rounded-lg text-sm font-medium transition-colors">
              <PieChart className="w-4 h-4" /> Donut Chart
            </button>
          </div>
        </div>

        <div className="flex-1 flex flex-col justify-center gap-8 px-4 relative z-10">
          {chartData.map((data, i) => (
            <div key={data.id} className="flex items-center gap-6">
              {/* Row Icon & Label */}
              <div className="flex items-center gap-3 w-48 shrink-0">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center bg-white/5 border border-white/10 ${data.id === 'F02' ? 'text-[#8B5CF6]' : data.id === 'F01' ? 'text-white' : data.id === 'F03' ? 'text-[#EC4899]' : data.id === 'F04' ? 'text-[#F59E0B]' : 'text-[#00D8FF]'}`}>
                  {/* Dynamic icon mapping can go here, using a dot for now */}
                  <div className="w-2 h-2 rounded-full bg-current" />
                </div>
                <div>
                  <span className="text-white font-bold text-xs mr-2">{data.id}</span>
                  <span className="text-text-muted text-xs">{data.label}</span>
                </div>
              </div>
              
              {/* Bar */}
              <div className="flex-1 h-6 bg-white/5 rounded-full overflow-hidden flex items-center">
                <motion.div 
                  initial={{ width: 0 }}
                  animate={{ width: `${(data.value / maxValue) * 100}%` }}
                  transition={{ duration: 1, delay: i * 0.1, type: "spring" }}
                  className={`h-full bg-gradient-to-r ${data.color} rounded-full`}
                />
              </div>
              
              {/* Value */}
              <div className="w-8 shrink-0 font-bold text-white">
                {data.value}
              </div>
            </div>
          ))}
          
          {/* X Axis labels */}
          <div className="flex justify-between ml-52 mr-10 mt-2 text-[10px] text-text-muted font-mono border-t border-white/5 pt-4">
            <span>0</span>
            <span>2</span>
            <span>4</span>
            <span>6</span>
            <span>8</span>
            <span>10</span>
            <span>14</span>
            <span>16</span>
          </div>
        </div>

        {/* Chart Background Grid Lines */}
        <div className="absolute inset-0 pointer-events-none opacity-20">
          <div className="absolute left-[244px] right-14 top-24 bottom-16 flex justify-between">
            {[0,1,2,3,4,5,6,7].map(i => (
              <div key={i} className="w-px h-full bg-white/20" />
            ))}
          </div>
        </div>

      </motion.div>
    </motion.div>
  );
}
