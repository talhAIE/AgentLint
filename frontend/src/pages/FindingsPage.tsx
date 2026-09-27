import { useQuery } from "@tanstack/react-query";
import { getFindings } from "../api/endpoints";
import { motion } from "framer-motion";
import { AlertTriangle, AlertOctagon, Info, ChevronRight, FileCode2, Search } from "lucide-react";

export default function FindingsPage() {
  const { data, isLoading } = useQuery({ queryKey: ["findings"], queryFn: getFindings, retry: false });

  if (isLoading) return <div className="p-4 text-text-muted">Loading...</div>;
  if (!data) return <div className="p-4 text-text-muted">No findings data found.</div>;

  const severityColors: Record<string, any> = {
    critical: { bg: "from-[#F43F5E] to-[#F43F5E]/80", border: "border-[#F43F5E]/30", text: "text-[#F43F5E]", icon: AlertOctagon },
    high: { bg: "from-[#F97316] to-[#F97316]/80", border: "border-[#F97316]/30", text: "text-[#F97316]", icon: AlertTriangle },
    medium: { bg: "from-[#F59E0B] to-[#F59E0B]/80", border: "border-[#F59E0B]/30", text: "text-[#F59E0B]", icon: AlertTriangle },
    low: { bg: "from-[#10B981] to-[#10B981]/80", border: "border-[#10B981]/30", text: "text-[#10B981]", icon: Info },
    info: { bg: "from-[#3B82F6] to-[#3B82F6]/80", border: "border-[#3B82F6]/30", text: "text-[#3B82F6]", icon: Info },
  };

  const findingsArray = data.findings || [];

  const containerVariants = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.05 } }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    show: { y: 0, opacity: 1, transition: { type: "spring" as const, stiffness: 300, damping: 24 } }
  };

  return (
    <div className="flex flex-col gap-6 h-full">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-gradient-to-br from-[#8B5CF6] to-[#A78BFA] rounded-xl shadow-lg">
            <Search className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white tracking-tight">Findings Database</h2>
            <p className="text-sm text-text-muted">Detailed list of {findingsArray.length} issues identified in the source code.</p>
          </div>
        </div>
      </div>
      
      <motion.div variants={containerVariants} initial="hidden" animate="show" className="grid gap-4">
        {findingsArray.map((f: any) => {
          const style = severityColors[f.severity] || severityColors.info;
          const Icon = style.icon;
          return (
            <motion.div key={f.id} variants={itemVariants} className={`bg-[#111827]/80 backdrop-blur-md border ${style.border} p-6 rounded-2xl flex flex-col gap-4 hover:bg-[#1E293B]/90 transition-all group shadow-lg`}>
              <div className="flex gap-4">
                <div className={`mt-1 p-3 rounded-xl bg-gradient-to-br ${style.bg} shadow-lg shrink-0`}>
                  <Icon className="w-5 h-5 text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-2">
                    <span className={`text-xs font-black uppercase tracking-widest ${style.text}`}>{f.severity}</span>
                    <span className="text-xs text-text-muted font-mono bg-white/5 px-2 py-0.5 rounded border border-white/10">{f.id}</span>
                  </div>
                  <h3 className="text-xl font-bold text-white mb-2 group-hover:text-[#00D8FF] transition-colors">{f.title}</h3>
                  <p className="text-text-muted text-sm leading-relaxed">{f.explanation}</p>
                </div>
              </div>

              {f.instruction_rules && f.instruction_rules.length > 0 && (
                <div className="ml-16 mt-2 pt-4 border-t border-white/5">
                  <div className="flex items-center gap-2 mb-3">
                    <FileCode2 className="w-4 h-4 text-text-muted" />
                    <span className="text-[10px] font-bold text-text-muted uppercase tracking-widest">Affected Rules</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {f.instruction_rules.map((rule: string) => (
                      <span key={rule} className="text-xs bg-[#0B0F19] text-[#00D8FF] font-medium px-3 py-1.5 rounded-lg border border-[#00D8FF]/20 flex items-center gap-1 group-hover:border-[#00D8FF]/50 transition-colors shadow-[0_0_10px_rgba(0,216,255,0.05)]">
                        <ChevronRight className="w-3 h-3 opacity-50" />
                        {rule}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </motion.div>
          );
        })}
      </motion.div>
    </div>
  );
}
