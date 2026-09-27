import { useQuery } from "@tanstack/react-query";
import { getSources } from "../api/endpoints";
import { motion } from "framer-motion";
import { Database, FileCode2, CheckCircle2, XCircle } from "lucide-react";

export default function SourcesPage() {
  const { data, isLoading } = useQuery({ queryKey: ["sources"], queryFn: getSources, retry: false });

  if (isLoading) return <div className="p-4 text-text-muted">Loading...</div>;
  if (!data || !data.sources) return <div className="p-4 text-text-muted">No sources data found.</div>;

  const containerVariants = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.1 } }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    show: { y: 0, opacity: 1, transition: { type: "spring" as const, stiffness: 300, damping: 24 } }
  };

  return (
    <div className="flex flex-col gap-6 h-full">
      <div className="flex items-center gap-4 mb-4">
        <div className="p-3 bg-gradient-to-br from-[#10B981] to-[#34D399] rounded-xl shadow-lg">
          <Database className="w-5 h-5 text-[#0B0F19]" />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Discovered Instructions</h2>
          <p className="text-sm text-text-muted">Sources of agent instructions found in the repository.</p>
        </div>
      </div>
      
      <motion.div variants={containerVariants} initial="hidden" animate="show" className="grid grid-cols-2 gap-6">
        {data.sources.map((src: any, i: number) => (
          <motion.div key={i} variants={itemVariants} className="bg-[#111827]/80 backdrop-blur-md border border-white/5 p-6 rounded-2xl flex flex-col gap-4 hover:border-[#10B981]/50 hover:shadow-[0_0_20px_rgba(16,185,129,0.1)] transition-all group">
            <div className="flex justify-between items-start">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-white/5 rounded-lg border border-white/10 group-hover:border-[#10B981]/30 transition-colors">
                  <FileCode2 className="w-5 h-5 text-[#10B981]" />
                </div>
                <div>
                  <h3 className="font-bold font-mono text-white tracking-tight">{src.path}</h3>
                  <p className="text-xs text-text-muted uppercase tracking-wider font-bold mt-1">Agent Type: <span className="text-[#00D8FF]">{src.agent_type}</span></p>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                {src.exists ? (
                  <div className="flex items-center gap-1.5 px-3 py-1 bg-[#10B981]/10 text-[#10B981] rounded-full text-xs font-bold border border-[#10B981]/20">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    FOUND
                  </div>
                ) : (
                  <div className="flex items-center gap-1.5 px-3 py-1 bg-[#F43F5E]/10 text-[#F43F5E] rounded-full text-xs font-bold border border-[#F43F5E]/20">
                    <XCircle className="w-3.5 h-3.5" />
                    MISSING
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
}
