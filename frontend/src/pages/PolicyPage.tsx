import { useQuery } from "@tanstack/react-query";
import { getPolicy } from "../api/endpoints";
import { Light as SyntaxHighlighter } from 'react-syntax-highlighter';
import yaml from 'react-syntax-highlighter/dist/esm/languages/hljs/yaml';
import { vs2015 } from 'react-syntax-highlighter/dist/esm/styles/hljs';

SyntaxHighlighter.registerLanguage('yaml', yaml);

export default function PolicyPage() {
  const { data, isLoading } = useQuery({ queryKey: ["policy"], queryFn: getPolicy, retry: false });

  if (isLoading) return <div className="p-4 text-text-muted">Loading...</div>;
  if (!data) return <div className="p-4 text-text-muted">No policy data found. Compile policy first.</div>;

  // Convert to YAML string
  const yamlString = "definition_of_done:\n" + 
    (data.definition_of_done || []).map((x: string) => `  - ${x}`).join("\n") +
    "\ntooling:\n" +
    Object.entries(data.tooling || {}).map(([k, v]) => `  ${k}: ${v}`).join("\n");

  return (
    <div className="flex flex-col gap-6 h-full">
      <h2 className="text-xl font-bold">Canonical Policy</h2>
      <div className="flex-1 min-h-0 bg-base rounded border border-border overflow-auto text-sm">
        <SyntaxHighlighter language="yaml" style={vs2015} customStyle={{ margin: 0, padding: '1rem', background: 'transparent' }}>
          {yamlString}
        </SyntaxHighlighter>
      </div>
    </div>
  );
}
