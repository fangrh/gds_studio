import { useState, useEffect } from 'react';
import { useParams, Link, useOutletContext, useLocation } from 'react-router-dom';
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

const STATUSES = ['open', 'in_progress', 'resolved', 'closed'];
const PRIORITIES = ['low', 'normal', 'high', 'critical'];

function IssuePanel() {
  const { id } = useParams<{ id: string }>();
  const { buildLink } = useDeepLink();
  const location = useLocation();
  const outletContext = useOutletContext<{ projectId?: number } | null>();
  const projectId = outletContext?.projectId;
  const [issues, setIssues] = useState<IssueListEntry[]>([]);
  const [issue, setIssue] = useState<Issue | null>(null);
  const [commentBody, setCommentBody] = useState('');
  const [statusFilter, setStatusFilter] = useState('open');
  const [editing, setEditing] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editBody, setEditBody] = useState('');
  const [editStatus, setEditStatus] = useState('');
  const [editPriority, setEditPriority] = useState('');

  useEffect(() => {
    const params = new URLSearchParams({ status: statusFilter });
    if (projectId) params.set('project_id', String(projectId));
    fetch(`/api/issues?${params}`)
      .then(r => r.json())
      .then(setIssues);
  }, [statusFilter, projectId]);

  useEffect(() => {
    if (id) {
      fetch(`/api/issues/${id}`)
        .then(r => r.json())
        .then(data => {
          setIssue(data);
          setEditTitle(data.title);
          setEditBody(data.body || '');
          setEditStatus(data.status);
          setEditPriority(data.priority);
          setEditing(false);
        });
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
        project_id: projectId || undefined,
      }),
    });
    if (res.ok) {
      const newIssue = await res.json();
      setIssues(prev => [newIssue, ...prev]);
      (e.target as HTMLFormElement).reset();
    }
  }

  async function handleUpdateIssue() {
    if (!id) return;
    const res = await fetch(`/api/issues/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: editTitle,
        body: editBody,
        status: editStatus,
        priority: editPriority,
      }),
    });
    if (res.ok) {
      const updated = await res.json();
      setIssue(updated);
      setEditing(false);
      setIssues(prev => prev.map(i => i.id === updated.id ? { ...i, status: updated.status, priority: updated.priority, title: updated.title } : i));
    }
  }

  async function handleStatusChange(newStatus: string) {
    if (!id) return;
    const res = await fetch(`/api/issues/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus }),
    });
    if (res.ok) {
      const updated = await res.json();
      setIssue(updated);
      setEditStatus(newStatus);
      setIssues(prev => prev.map(i => i.id === updated.id ? { ...i, status: updated.status } : i));
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
          <Link to={projectId ? `/projects/${projectId}/issues` : '/issues'} style={{ fontSize: '13px', color: '#666' }}>&larr; Back to list</Link>

          {editing ? (
            <div style={{ marginTop: '8px' }}>
              <input value={editTitle} onChange={e => setEditTitle(e.target.value)}
                style={{ fontSize: '18px', fontWeight: 'bold', width: '100%', padding: '4px', border: '1px solid #ccc', borderRadius: '4px' }} />
              <div style={{ display: 'flex', gap: '8px', marginTop: '8px', alignItems: 'center' }}>
                <select value={editStatus} onChange={e => setEditStatus(e.target.value)}
                  style={{ padding: '4px 8px', borderRadius: '12px', fontSize: '12px', border: 'none', color: '#fff', background: STATUS_COLORS[editStatus] || '#999' }}>
                  {STATUSES.map(s => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
                </select>
                <select value={editPriority} onChange={e => setEditPriority(e.target.value)}
                  style={{ padding: '4px 8px', borderRadius: '4px', fontSize: '12px', border: '1px solid #ccc' }}>
                  {PRIORITIES.map(p => <option key={p} value={p}>{p}</option>)}
                </select>
                <button onClick={handleUpdateIssue}
                  style={{ padding: '4px 12px', background: '#4CAF50', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' }}>
                  Save
                </button>
                <button onClick={() => setEditing(false)}
                  style={{ padding: '4px 12px', background: '#eee', border: '1px solid #ccc', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' }}>
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <div style={{ marginTop: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h2 style={{ margin: 0 }}>{issue.title}</h2>
                <button onClick={() => setEditing(true)}
                  style={{ padding: '2px 8px', background: '#f5f5f5', border: '1px solid #ddd', borderRadius: '4px', cursor: 'pointer', fontSize: '11px', color: '#666' }}>
                  Edit
                </button>
              </div>
              <div style={{ display: 'flex', gap: '8px', marginTop: '8px', alignItems: 'center' }}>
                <span style={{
                  padding: '2px 8px', borderRadius: '12px', fontSize: '12px',
                  background: STATUS_COLORS[issue.status] || '#999', color: '#fff',
                }}>
                  {issue.status.replace('_', ' ')}
                </span>
                <span style={{ fontSize: '12px', color: '#666' }}>Priority: {issue.priority}</span>
                {issue.tags.map(tag => (
                  <span key={tag} style={{
                    padding: '2px 6px', borderRadius: '4px', fontSize: '11px',
                    background: '#e0e0e0',
                  }}>{tag}</span>
                ))}
                <span style={{ marginLeft: 'auto', fontSize: '11px', color: '#999' }}>
                  Quick:
                  {STATUSES.filter(s => s !== issue.status).map(s => (
                    <button key={s} onClick={() => handleStatusChange(s)}
                      style={{
                        marginLeft: 4, padding: '1px 6px', fontSize: '10px', cursor: 'pointer',
                        border: '1px solid #ddd', borderRadius: '8px', background: '#fff',
                      }}>
                      {s.replace('_', ' ')}
                    </button>
                  ))}
                </span>
              </div>
            </div>
          )}
        </div>

        <div style={{ flex: 1, overflow: 'auto', padding: '16px' }}>
          <div style={{
            background: '#fff', border: '1px solid #e0e0e0',
            borderRadius: '8px', padding: '16px', marginBottom: '16px',
          }}>
            <h3 style={{ fontSize: '14px', marginBottom: '8px' }}>Description</h3>
            {editing ? (
              <textarea value={editBody} onChange={e => setEditBody(e.target.value)}
                style={{ width: '100%', minHeight: '80px', padding: '8px', border: '1px solid #ccc', borderRadius: '4px', fontSize: '14px', lineHeight: 1.6, resize: 'vertical' }} />
            ) : (
              <p style={{ whiteSpace: 'pre-wrap', fontSize: '14px', lineHeight: 1.6 }}>
                {issue.body}
              </p>
            )}
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
          {STATUSES.map(s => (
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
          <input name="body" placeholder="Description (optional)"
            style={{ flex: '1 1 200px', padding: '8px', border: '1px solid #ccc', borderRadius: '4px', fontSize: '14px' }} />
          <input name="script_path" placeholder="script path (optional)"
            style={{ flex: '1 1 200px', padding: '8px', border: '1px solid #ccc', borderRadius: '4px', fontSize: '14px' }} />
          <select name="priority" defaultValue="normal"
            style={{ padding: '8px', border: '1px solid #ccc', borderRadius: '4px', fontSize: '14px' }}>
            {PRIORITIES.map(p => <option key={p} value={p}>{p}</option>)}
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
        {issues.map(i => (
          <Link
            key={i.id}
            to={projectId ? `/projects/${projectId}/issues/${i.id}` : `/issues/${i.id}`}
            style={{ textDecoration: 'none', color: 'inherit' }}
          >
            <div style={{
              padding: '12px 16px', borderBottom: '1px solid #f0f0f0',
              display: 'flex', alignItems: 'center', gap: '12px',
              cursor: 'pointer',
              transition: 'background 0.15s',
            }}
            onMouseEnter={e => e.currentTarget.style.background = '#f8f8f8'}
            onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
            >
              <span style={{
                padding: '2px 8px', borderRadius: '12px', fontSize: '11px',
                background: STATUS_COLORS[i.status] || '#999', color: '#fff',
                whiteSpace: 'nowrap',
              }}>
                {i.status.replace('_', ' ')}
              </span>
              <span style={{ fontSize: '11px', color: '#999', whiteSpace: 'nowrap' }}>
                #{i.id}
              </span>
              <span style={{ flex: 1, fontSize: '14px' }}>{i.title}</span>
              <span style={{
                fontSize: '11px', padding: '1px 6px', borderRadius: '4px',
                background: i.priority === 'high' || i.priority === 'critical'
                  ? '#ffebee' : '#f5f5f5',
                color: i.priority === 'high' || i.priority === 'critical'
                  ? '#c62828' : '#666',
              }}>
                {i.priority}
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
