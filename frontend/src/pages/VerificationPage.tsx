import { useQuery } from "@tanstack/react-query";
import { getVerification } from "../api/endpoints";

export default function VerificationPage() {
  const { data, isLoading } = useQuery({ queryKey: ["verification"], queryFn: getVerification, retry: false });

  if (isLoading) return <div className="p-4 text-text-muted">Loading...</div>;
  if (!data) return <div className="p-4 text-text-muted">No verification results found. Run validate first.</div>;

  const summary = data.summary || { passed: 0, failed: 0, total: 0 };
  const results = data.results || [];

  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-xl font-bold">Verification Results</h2>

      <div className="flex gap-4">
        <div className="bg-surface border border-border p-4 rounded flex-1">
          <h3 className="text-sm text-text-muted">Total Checks</h3>
          <p className="text-lg font-bold">{summary.total}</p>
        </div>
        <div className="bg-surface border border-border p-4 rounded flex-1">
          <h3 className="text-sm text-text-muted">Passed</h3>
          <p className="text-lg font-bold text-pass-green">{summary.passed}</p>
        </div>
        <div className="bg-surface border border-border p-4 rounded flex-1">
          <h3 className="text-sm text-text-muted">Failed</h3>
          <p className={`text-lg font-bold ${summary.failed > 0 ? "text-severity-critical" : "text-text-primary"}`}>
            {summary.failed}
          </p>
        </div>
      </div>

      <div className="flex flex-col gap-4">
        {results.map((r: any, i: number) => (
          <div key={i} className={`bg-surface border p-4 rounded flex flex-col gap-2 ${r.passed ? 'border-border' : 'border-severity-critical'}`}>
            <div className="flex items-center gap-3">
              <span className={`px-2 py-1 text-xs font-bold rounded uppercase ${r.passed ? 'bg-pass-green/20 text-pass-green' : 'bg-severity-critical/20 text-severity-critical'}`}>
                {r.passed ? 'PASS' : 'FAIL'}
              </span>
              <span className="font-medium text-lg">{r.name}</span>
            </div>
            {r.stdout_excerpt && (
              <div className="mt-2 bg-elevated p-3 text-sm font-mono rounded border border-border whitespace-pre-wrap">
                {r.stdout_excerpt}
              </div>
            )}
            {r.stderr_excerpt && (
              <div className="mt-2 bg-severity-critical/10 text-severity-critical p-3 text-sm font-mono rounded border border-severity-critical/30 whitespace-pre-wrap">
                {r.stderr_excerpt}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
