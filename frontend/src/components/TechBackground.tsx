

export default function TechBackground() {
  return (
    <div className="fixed inset-0 z-0 overflow-hidden pointer-events-none" style={{ backgroundColor: '#0B0F19' }}>
      {/* Top right gradient glow */}
      <div className="absolute top-0 right-0 w-[800px] h-[600px] bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-[#1e3a8a]/20 via-[#0B0F19]/0 to-transparent" />
      
      {/* Abstract wave lines (top right) */}
      <svg className="absolute top-0 right-0 w-1/2 h-64 opacity-30" viewBox="0 0 1000 200" preserveAspectRatio="none">
        <path d="M0,0 C300,100 600,0 1000,100 L1000,0 Z" fill="none" stroke="url(#wave-gradient)" strokeWidth="2" />
        <path d="M0,50 C300,150 600,50 1000,150 L1000,0 Z" fill="none" stroke="url(#wave-gradient-2)" strokeWidth="1" />
        <defs>
          <linearGradient id="wave-gradient" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#00D8FF" stopOpacity="0" />
            <stop offset="100%" stopColor="#8B5CF6" stopOpacity="1" />
          </linearGradient>
          <linearGradient id="wave-gradient-2" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#3B82F6" stopOpacity="0" />
            <stop offset="100%" stopColor="#00D8FF" stopOpacity="1" />
          </linearGradient>
        </defs>
      </svg>
    </div>
  );
}
