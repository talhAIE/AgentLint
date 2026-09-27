import { useQuery } from "@tanstack/react-query";
import { getEvidence } from "../api/endpoints";
import { motion } from "framer-motion";
import { Fingerprint, Code, Terminal, Package, Info } from "lucide-react";

export default function EvidencePage() {
  const { data, isLoading } = useQuery({ queryKey: ["evidence"], queryFn: getEvidence, retry: false });

  if (isLoading) return <div className="p-4 text-text-muted">Loading...</div>;
  if (!data) return <div className="p-4 text-text-muted">No evidence data found.</div>;

  const evidenceArray = data.evidence || [];
  const grouped = evidenceArray.reduce((acc: any, item: any) => {
    if (!acc[item.category]) acc[item.category] = [];
    acc[item.category].push(item);
    return acc;
  }, {});

  const categoryIcons: Record<string, any> = {
    commands: Terminal,
    dependencies: Package,
    frameworks: Code,
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.1 } }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    show: { y: 0, opacity: 1, transition: { type: "spring" as const, stiffness: 300, damping: 24 } }
  };

  return (
    <div className="flex flex-col gap-8 h-full">
      <div className="flex items-center gap-4 mb-2">
        <div className="p-3 bg-gradient-to-br from-[#3B82F6] to-[#60A5FA] rounded-xl shadow-lg">
          <Fingerprint className="w-5 h-5 text-white" />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Repository Evidence</h2>
          <p className="text-sm text-text-muted">Ground truth data extracted directly from the repository source code.</p>
        </div>
      </div>
      
      <motion.div variants={containerVariants} initial="hidden" animate="show" className="flex flex-col gap-6">
        {Object.entries(grouped).map(([cat, items]: any) => {
          const CatIcon = categoryIcons[cat.toLowerCase()] || Info;
          return (
            <motion.div key={cat} variants={itemVariants} className="bg-[#111827]/80 backdrop-blur-md border border-white/5 rounded-2xl overflow-hidden shadow-lg">
              <div className="bg-[#1E293B]/80 px-6 py-4 border-b border-white/5 flex items-center gap-3">
                <CatIcon className="w-4 h-4 text-[#00D8FF]" />
                <h3 className="font-bold text-white uppercase tracking-widest text-sm">{cat.replace("_", " ")}</h3>
                <div className="ml-auto bg-white/10 px-2.5 py-0.5 rounded-full text-xs font-bold text-text-muted">{items.length}</div>
              </div>
              <div className="p-6 flex flex-col gap-4">
                {items.map((item: any) => (
                  <div key={item.id} className="grid grid-cols-12 gap-6 items-start border-b border-white/5 pb-4 last:border-0 last:pb-0 group">
                    <div className="col-span-3">
                      <span className="font-mono text-sm text-[#00D8FF] font-bold tracking-tight bg-[#00D8FF]/10 px-2 py-1 rounded inline-block">{item.key}</span>
                    </div>
                    <div className="col-span-3">
                      <span className="font-mono text-sm text-white font-medium bg-white/5 px-2 py-1 rounded inline-block border border-white/10 group-hover:border-white/30 transition-colors">{item.value}</span>
                    </div>
                    <div className="col-span-6 text-sm text-text-muted leading-relaxed flex items-center h-full">
                      {item.explanation}
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          );
        })}
      </motion.div>
    </div>
  );
}
