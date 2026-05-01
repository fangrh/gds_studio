import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useDeepLink } from '../../hooks/useDeepLink';
import CommentThread from '../../components/CommentThread';
import GdsEmbed from '../../components/GdsEmbed';

interface LinkedElement {
  id: number;
  cell_name: string;
  element_id: number;
  layer: string;
  bbox: string;
  deep_link_url: string;
}

interface Comment {
  id: number;
  author_type: string;
  body: string;
  agent_model?: string;
  created_at: string;
}

interface Issue {
  id: number;
  title: string;
  body: string;
  status: string;
  priority: string;
  tags: string[];
  script_path?: string;
  linked_elements: LinkedElement[];
  comments: Comment[];
  created_at: string;
}

interface IssueListEntry {
  id: number;
  title: string;
  status: string;
  priority: string;
  created_at: string;
}

const STATUS_COLORS: Record<string, string> = {
  open: '#2196F3',
  in_progress: '#FF9800',
  resolved: '#4CAF50',
  closed: '#9E9E9E',
};

function IssuePanel() {
  const { id } = useParams<{ id: string }>();
  const { buildLink } = useDeepLink();
  const [issues, setIssues] = useState<IssueListEntry[]>([]);
  const [issue, setIssue] = useState<Issue | null>(null);
  const [commentBody, setCommentBody] = useState('');
  const [statusFilter, setStatusFilter] = useState('open');

  useEffect(() => {
    fetch(`/api/issues?status=${statusFilter}`)
      .then(r => r.json())
      .then(setIssues);
  }, [statusFilter]);

  useEffect(() => {
    if (id) {
      fetch(`/api/issues/${id}`)
        .then(r => r.json())
        .then(setIssue);
    } else {
      setIssue(null);
    }
  }, [id]);

  async function handleCreateIssue(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const res = await fetch('/api/issues', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: form.get('title'),
        body: form.get('body'),
        priority: form.get('priority') || 'normal',
        script_path: form.get('script_path') || undefined,
      }),
    });
    if (res.ok) {
      const newIssue = await res.json();
      setIssues(prev => [newIssue, ...prev]);
      (e.target as HTMLFormElement).reset();
    }
  }

  async function handleAddComment() {
    if (!id || !commentBody.trim()) return;
    const res = await fetch('/api/comments', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        target_type: 'issue',
        target_id: parseInt(id),
        body: commentBody,
      }),
    });
    if (res.ok) {
      const comment = await res.json();
      setIssue(prev => prev ? { ...prev, comments: [...prev.comments, comment] } : null);
      setCommentBody('');
    }
  }

  if (id && issue) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        <div style={{ padding: '16px', borderBottom: '1px solid #e0e0e0' }}>
          <Link to="/issues" style={{ fontSize: '13px', color: '#666' }}>&larr; Back to list</Link>
          <h2 style={{ marginTop: '8px' }}>{issue.title}</h2>
          <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
            <span style={{
              padding: '2px 8px', borderRadius: '12px', fontSize: '12px',
              background: STATUS_COLORS[issue.status] || '#999', color: '#fff',
            }}>
              {issue.status}
            </span>
            <span style={{ fontSize: '12px', color: '#666' }}>Priority: {issue.priority}</span>
            {issue.tags.map(tag => (
              <span key={tag} style={{
                padding: '2px 6px', borderRadius: '4px', fontSize: '11px',
                background: '#e0e0e0',
              }}>{tag}</span>
            ))}
          </div>
        </div>

        <div style={{ flex: 1, overflow: 'auto', padding: '16px' }}>
          <div style={{
            background: '#fff', border: '1px solid #e0e0e0',
            borderRadius: '8px', padding: '16px', marginBottom: '16px',
          }}>
            <h3 style={{ fontSize: '14px', marginBottom: '8px' }}>Description</h3>
            <p style={{ whiteSpace: 'pre-wrap', fontSize: '14px', lineHeight: 1.6 }}>
              {issue.body}
            </p>
          </div>

          {issue.script_path && (
            <div style={{
              background: '#fff', border: '1px solid #e0e0e0',
              borderRadius: '8px', padding: '16px', marginBottom: '16px',
            }}>
              <h3 style={{ fontSize: '14px', marginBottom: '8px' }}>Script</h3>
              <code style={{ fontSize: '13px' }}>{issue.script_path}</code>
            </div>
          )}

          {issue.linked_elements.length > 0 && (
            <div style={{
              background: '#fff', border: '1px solid #e0e0e0',
              borderRadius: '8px', padding: '16px', marginBottom: '16px',
            }}>
              <h3 style={{ fontSize: '14px', marginBottom: '8px' }}>Linked Elements</h3>
              {issue.linked_elements.map(el => (
                <div key={el.id} style={{ marginBottom: '8px' }}>
                  <Link
                    to={buildLink({
                      gds: issue.script_path?.replace('scripts/', '').replace('.py', '') || '',
                      cell: el.cell_name,
                      elem: el.element_id,
                      layer: el.layer,
                      bbox: el.bbox,
                    })}
                    style={{ fontSize: '13px', color: '#1976D2' }}
                  >
                    {el.cell_name} / elem:{el.element_id} ({el.layer})
                  </Link>
                  <GdsEmbed deepLinkUrl={el.deep_link_url} />
                </div>
              ))}
            </div>
          )}

          <CommentThread
            comments={issue.comments}
            onAddComment={handleAddComment}
            commentBody={commentBody}
            onCommentChange={setCommentBody}
          />
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ padding: '16px', borderBottom: '1px solid #e0e0e0' }}>
        <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
          {['open', 'in_progress', 'resolved', 'closed'].map(s => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              style={{
                padding: '4px 12px', border: '1px solid #ccc', borderRadius: '16px',
                fontSize: '12px', cursor: 'pointer',
                background: statusFilter === s ? STATUS_COLORS[s] : '#fff',
                color: statusFilter === s ? '#fff' : '#333',
              }}
            >
              {s.replace('_', ' ')}
            </button>
          ))}
        </div>

        <form onSubmit={handleCreateIssue} style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <input name="title" placeholder="Issue title" required
            style={{ flex: '1 1 200px', padding: '8px', border: '1px solid #ccc', borderRadius: '4px', fontSize: '14px' }} />
          <input name="script_path" placeholder="script path (optional)"
            style={{ flex: '1 1 200px', padding: '8px', border: '1px solid #ccc', borderRadius: '4px', fontSize: '14px' }} />
          <select name="priority" defaultValue="normal"
            style={{ padding: '8px', border: '1px solid #ccc', borderRadius: '4px', fontSize: '14px' }}>
            <option value="low">Low</option>
            <option value="normal">Normal</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
          <button type="submit" style={{
            padding: '8px 16px', background: '#1976D2', color: '#fff',
            border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '14px',
          }}>
            Create Issue
          </button>
        </form>
      </div>

      <div style={{ flex: 1, overflow: 'auto' }}>
        {issues.map(issue => (
          <Link
            key={issue.id}
            to={`/issues/${issue.id}`}
            style={{ textDecoration: 'none', color: 'inherit' }}
          >
            <div style={{
              padding: '12px 16px', borderBottom: '1px solid #f0f0f0',
              display: 'flex', alignItems: 'center', gap: '12px',
            }}>
              <span style={{
                padding: '2px 8px', borderRadius: '12px', fontSize: '11px',
                background: STATUS_COLORS[issue.status] || '#999', color: '#fff',
                whiteSpace: 'nowrap',
              }}>
                {issue.status}
              </span>
              <span style={{ fontSize: '11px', color: '#999', whiteSpace: 'nowrap' }}>
                #{issue.id}
              </span>
              <span style={{ flex: 1, fontSize: '14px' }}>{issue.title}</span>
              <span style={{
                fontSize: '11px', padding: '1px 6px', borderRadius: '4px',
                background: issue.priority === 'high' || issue.priority === 'critical'
                  ? '#ffebee' : '#f5f5f5',
                color: issue.priority === 'high' || issue.priority === 'critical'
                  ? '#c62828' : '#666',
              }}>
                {issue.priority}
              </span>
            </div>
          </Link>
        ))}
        {issues.length === 0 && (
          <p style={{ textAlign: 'center', color: '#999', marginTop: '32px' }}>
            No {statusFilter.replace('_', ' ')} issues
          </p>
        )}
      </div>
    </div>
  );
}

export default IssuePanel;
