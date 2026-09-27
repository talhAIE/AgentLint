import { useQuery } from "@tanstack/react-query";
import { getRepair } from "../api/endpoints";
import { Light as SyntaxHighlighter } from 'react-syntax-highlighter';
import markdown from 'react-syntax-highlighter/dist/esm/languages/hljs/markdown';
import { vs2015 } from 'react-syntax-highlighter/dist/esm/styles/hljs';

SyntaxHighlighter.registerLanguage('markdown', markdown);

export default function RepairPage() {
  const { data, isLoading } = useQuery({ queryKey: ["repair"], queryFn: getRepair, retry: false });

  if (isLoading) return <div className="p-4 text-text-muted">Loading...</div>;
  if (!data || !data.content) return <div className="p-4 text-text-muted">No repair plan found. Compile policy first.</div>;

  return (
    <div className="flex flex-col gap-6 h-full">
      <h2 className="text-xl font-bold">Repair Plan Preview</h2>
      <div className="flex-1 min-h-0 bg-base rounded border border-border overflow-auto text-sm">
        <SyntaxHighlighter language="markdown" style={vs2015} customStyle={{ margin: 0, padding: '1rem', background: 'transparent' }}>
          {data.content}
        </SyntaxHighlighter>
      </div>
    </div>
  );
}
