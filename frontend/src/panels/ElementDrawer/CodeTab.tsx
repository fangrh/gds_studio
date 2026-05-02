import { useEffect, useState } from 'react';

interface CodeTabProps {
  sourceLine: number | null;
  sourceCall: string | null;
  scriptPath: string | null;
  hasSource: boolean;
}

interface SnippetLine {
  num: number;
  text: string;
  highlighted: boolean;
}

interface SourceData {
  script_path: string;
  source_line: number;
  total_lines: number;
  snippet_start: number;
  snippet_end: number;
  snippet: SnippetLine[];
}

export default function CodeTab({ sourceLine, sourceCall, scriptPath, hasSource }: CodeTabProps) {
  const [sourceData, setSourceData] = useState<SourceData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!hasSource || !scriptPath || !sourceLine) return;

    setLoading(true);
    setError(null);
    fetch(`/api/gds/source?script_path=${encodeURIComponent(scriptPath)}&source_line=${sourceLine}`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => {
        if (data.error) {
          setError(data.error);
        } else {
          setSourceData(data);
        }
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [hasSource, scriptPath, sourceLine]);

  if (!hasSource) {
    return (
      <div style={{ padding: '20px 12px', textAlign: 'center' }}>
        <div style={{ fontSize: 13, color: '#888', marginBottom: 4 }}>Source not available</div>
        <div style={{ fontSize: 11, color: '#555' }}>
          This element was not generated from a traced build. Re-build with source tracing to enable this tab.
        </div>
      </div>
    );
  }

  if (loading) {
    return <div style={{ padding: '12px', fontSize: 11, color: '#666' }}>Loading source...</div>;
  }

  if (error) {
    return (
      <div style={{ padding: '12px', fontSize: 11, color: '#f44' }}>
        Error loading source: {error}
      </div>
    );
  }

  if (!sourceData) return null;

  // Extract function name from source call (e.g., "mzi = gf.components.mzi(..." → "gf.components.mzi")
  const callParts = sourceCall?.split('=') || [];
  const callName = callParts.length > 1
    ? callParts[1].trim().split('(')[0].trim()
    : sourceCall?.split('(')[0].trim() || '';

  const fileName = scriptPath?.split('/').pop() || scriptPath || '';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      {/* Breadcrumb */}
      <div style={{
        padding: '6px 12px',
        background: '#252526',
        borderBottom: '1px solid #3c3c3c',
        fontSize: 11,
        color: '#888',
        display: 'flex',
        gap: 6,
        alignItems: 'center',
        flexShrink: 0,
      }}>
        <span style={{ color: '#569cd6' }}>{fileName}</span>
        {callName && (
          <>
            <span style={{ color: '#555' }}>&gt;</span>
            <span style={{ color: '#dcdcaa' }}>{callName}()</span>
          </>
        )}
        <span style={{ color: '#555' }}>&gt;</span>
        <span style={{ color: '#ce9178' }}>line {sourceLine}</span>
      </div>

      {/* Source viewer */}
      <div style={{
        flex: 1,
        overflow: 'auto',
        padding: '4px 0',
        fontFamily: "'Consolas', 'Monaco', 'Courier New', monospace",
        fontSize: 12,
        lineHeight: 1.6,
      }}>
        {sourceData.snippet.map((line) => (
          <div
            key={line.num}
            style={{
              display: 'flex',
              background: line.highlighted ? '#2d4568' : 'transparent',
              borderLeft: line.highlighted ? '2px solid #007acc' : '2px solid transparent',
              padding: '0 8px',
            }}
          >
            <span style={{
              width: 36,
              textAlign: 'right',
              color: line.highlighted ? '#ccc' : '#555',
              paddingRight: 8,
              userSelect: 'none',
              flexShrink: 0,
            }}>
              {line.num}
            </span>
            <span style={{
              color: line.highlighted ? '#e8e8e8' : '#a0a0a0',
              whiteSpace: 'pre',
            }}>
              {line.text}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
