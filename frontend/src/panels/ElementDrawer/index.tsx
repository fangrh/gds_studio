import { useEffect, useState, useCallback } from 'react';
import CodeTab from './CodeTab';

interface ElementDrawerProps {
  elementIndex: number;
  elementLayer: string;
  sourceLine: number | null;
  sourceCall: string | null;
  scriptPath: string | null;
  onClose: () => void;
}

interface Issue {
  id: number;
  title: string;
  status: string;
  body: string | null;
  created_at: string | null;
}

type Tab = 'issues' | 'code';

export default function ElementDrawer({
  elementIndex,
  elementLayer,
  sourceLine,
  sourceCall,
  scriptPath,
  onClose,
}: ElementDrawerProps) {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [loading, setLoading] = useState(false);
  const [input, setInput] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>('issues');

  const fetchIssues = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/issues?element_id=${elementIndex}&cell_name=top_cell`);
      if (res.ok) {
        setIssues(await res.json());
      }
    } catch {
      // ignore fetch errors
    } finally {
      setLoading(false);
    }
  }, [elementIndex]);

  useEffect(() => {
    fetchIssues();
  }, [fetchIssues]);

  const handleCreate = async () => {
    if (!input.trim() || submitting) return;
    setSubmitting(true);
    try {
      const title = `Issue on ${elementLayer} element #${elementIndex}`;
      const res = await fetch('/api/issues', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title,
          body: input.trim(),
          linked_elements: [{
            element_id: elementIndex,
            layer: elementLayer,
            cell_name: 'top_cell',
          }],
        }),
      });
      if (res.ok) {
        setInput('');
        fetchIssues();
      }
    } catch {
      // ignore
    } finally {
      setSubmitting(false);
    }
  };

  const statusColor: Record<string, string> = {
    open: '#4ec94e',
    in_progress: '#d4a017',
    resolved: '#569cd6',
    closed: '#888',
  };

  const hasSource = sourceLine !== null && scriptPath !== null;

  return (
    <div style={{
      position: 'absolute',
      bottom: 0,
      left: 0,
      right: 0,
      height: 280,
      borderTop: '2px solid #007acc',
      background: '#1e1e1e',
      display: 'flex',
      flexDirection: 'column',
      zIndex: 10,
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '4px 12px',
        background: '#252526',
        borderBottom: '1px solid #3c3c3c',
      }}>
        <span style={{ fontSize: 12, color: '#ccc' }}>
          Element #{elementIndex} ({elementLayer}){' '}
          <span style={{ color: '#007acc' }}>{issues.length} issue{issues.length !== 1 ? 's' : ''}</span>
        </span>
        <button
          onClick={onClose}
          style={{
            background: 'none', border: 'none', color: '#888', cursor: 'pointer',
            fontSize: 14, padding: '0 4px',
          }}
        >
          x
        </button>
      </div>

      {/* Tab bar */}
      <div style={{
        display: 'flex',
        background: '#252526',
        borderBottom: '1px solid #3c3c3c',
      }}>
        <button
          onClick={() => setActiveTab('issues')}
          style={{
            background: activeTab === 'issues' ? '#1e1e1e' : 'transparent',
            border: 'none',
            borderBottom: activeTab === 'issues' ? '2px solid #007acc' : '2px solid transparent',
            color: activeTab === 'issues' ? '#fff' : '#888',
            padding: '6px 16px',
            cursor: 'pointer',
            fontSize: 12,
            fontFamily: 'inherit',
          }}
        >
          Issues
        </button>
        <button
          onClick={() => setActiveTab('code')}
          style={{
            background: activeTab === 'code' ? '#1e1e1e' : 'transparent',
            border: 'none',
            borderBottom: activeTab === 'code' ? '2px solid #007acc' : '2px solid transparent',
            color: activeTab === 'code' ? '#fff' : '#888',
            padding: '6px 16px',
            cursor: 'pointer',
            fontSize: 12,
            fontFamily: 'inherit',
          }}
        >
          Code
        </button>
      </div>

      {/* Tab content */}
      <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        {activeTab === 'issues' && (
          <>
            <div style={{ flex: 1, overflowY: 'auto', padding: '8px 12px' }}>
              {loading && <div style={{ fontSize: 11, color: '#666' }}>Loading...</div>}
              {!loading && issues.length === 0 && (
                <div style={{ fontSize: 11, color: '#666' }}>No issues for this element</div>
              )}
              {issues.map((issue) => (
                <div key={issue.id} style={{
                  background: '#252526',
                  border: '1px solid #3c3c3c',
                  borderRadius: 4,
                  padding: '6px 10px',
                  marginBottom: 6,
                  fontSize: 12,
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 2 }}>
                    <span style={{ color: '#ccc', fontWeight: 600, fontSize: 11 }}>
                      #{issue.id} {issue.title}
                    </span>
                    <span style={{
                      padding: '1px 6px',
                      borderRadius: 3,
                      fontSize: 10,
                      color: statusColor[issue.status] || '#888',
                      background: `${statusColor[issue.status] || '#888'}20`,
                    }}>
                      {issue.status}
                    </span>
                  </div>
                  {issue.body && (
                    <div style={{ color: '#888', fontSize: 11, lineHeight: 1.3 }}>
                      {issue.body.length > 120 ? issue.body.slice(0, 120) + '...' : issue.body}
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div style={{
              display: 'flex',
              gap: 8,
              padding: '8px 12px',
              borderTop: '1px solid #333',
              background: '#252526',
            }}>
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') handleCreate(); }}
                placeholder={`Describe issue with element #${elementIndex}...`}
                style={{
                  flex: 1,
                  background: '#3c3c3c',
                  border: '1px solid #555',
                  color: '#ccc',
                  padding: '6px 10px',
                  borderRadius: 3,
                  fontSize: 12,
                  outline: 'none',
                  fontFamily: 'inherit',
                }}
              />
              <button
                onClick={handleCreate}
                disabled={submitting || !input.trim()}
                style={{
                  background: submitting ? '#555' : '#007acc',
                  color: '#fff',
                  border: 'none',
                  padding: '6px 14px',
                  borderRadius: 3,
                  fontSize: 12,
                  cursor: submitting ? 'not-allowed' : 'pointer',
                  fontFamily: 'inherit',
                }}
              >
                {submitting ? 'Creating...' : 'Create Issue'}
              </button>
            </div>
          </>
        )}

        {activeTab === 'code' && (
          <CodeTab
            sourceLine={sourceLine}
            sourceCall={sourceCall}
            scriptPath={scriptPath}
            hasSource={hasSource}
          />
        )}
      </div>
    </div>
  );
}
