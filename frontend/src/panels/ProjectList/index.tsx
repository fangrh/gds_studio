import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

interface Project {
  id: number;
  name: string;
  description: string;
  issue_count: number;
  wiki_count: number;
  script_count: number;
  created_at: string;
  updated_at: string;
}

interface NewProject {
  name: string;
  description: string;
}

export default function ProjectList() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [newProject, setNewProject] = useState<NewProject>({ name: '', description: '' });
  const [createdToken, setCreatedToken] = useState<string | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch('/api/projects')
      .then(r => r.json())
      .then(setProjects)
      .catch(() => setError('Failed to load projects'));
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      const r = await fetch('/api/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newProject),
      });
      if (!r.ok) {
        const err = await r.json();
        setError(err.detail || 'Failed to create project');
        return;
      }
      const project = await r.json();
      if (project.token) {
        setCreatedToken(project.token);
      }
      setProjects(prev => [project, ...prev]);
      setNewProject({ name: '', description: '' });
    } catch {
      setError('Network error');
    }
  };

  return (
    <div style={{ padding: '24px', maxWidth: '900px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h2>Projects</h2>
        <button
          onClick={() => setShowCreate(!showCreate)}
          style={{ padding: '8px 16px', cursor: 'pointer' }}
        >
          {showCreate ? 'Cancel' : 'New Project'}
        </button>
      </div>

      {createdToken && (
        <div style={{
          padding: '16px', marginBottom: '16px',
          background: '#fff3cd', border: '1px solid #ffc107', borderRadius: '4px',
        }}>
          <strong>Auth token created. Save it now — it won't be shown again:</strong>
          <div style={{
            marginTop: '8px', padding: '8px', background: '#fff',
            fontFamily: 'monospace', wordBreak: 'break-all',
          }}>
            {createdToken}
          </div>
          <button onClick={() => { navigator.clipboard.writeText(createdToken); }} style={{ marginTop: '8px' }}>
            Copy to clipboard
          </button>
          <button onClick={() => setCreatedToken(null)} style={{ marginLeft: '8px' }}>
            Dismiss
          </button>
        </div>
      )}

      {error && <div style={{ color: 'red', marginBottom: '16px' }}>{error}</div>}

      {showCreate && (
        <form onSubmit={handleCreate} style={{
          marginBottom: '24px', padding: '16px',
          border: '1px solid #ddd', borderRadius: '4px', background: '#fafafa',
        }}>
          <div style={{ marginBottom: '12px' }}>
            <label style={{ display: 'block', marginBottom: '4px' }}>Project Name</label>
            <input
              value={newProject.name}
              onChange={e => setNewProject(p => ({ ...p, name: e.target.value }))}
              style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
              required
            />
          </div>
          <div style={{ marginBottom: '12px' }}>
            <label style={{ display: 'block', marginBottom: '4px' }}>Description</label>
            <textarea
              value={newProject.description}
              onChange={e => setNewProject(p => ({ ...p, description: e.target.value }))}
              style={{ width: '100%', padding: '8px', boxSizing: 'border-box', minHeight: '60px' }}
            />
          </div>
          <button type="submit" style={{ padding: '8px 16px', cursor: 'pointer' }}>
            Create Project
          </button>
        </form>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px' }}>
        {projects.map(project => (
          <Link
            key={project.id}
            to={`/projects/${project.id}`}
            style={{
              display: 'block', padding: '16px',
              border: '1px solid #e0e0e0', borderRadius: '8px',
              textDecoration: 'none', color: '#333',
              background: '#fff',
            }}
          >
            <h3 style={{ margin: '0 0 8px 0' }}>{project.name}</h3>
            {project.description && (
              <p style={{ margin: '0 0 12px 0', color: '#666', fontSize: '14px' }}>
                {project.description}
              </p>
            )}
            <div style={{ display: 'flex', gap: '16px', fontSize: '13px', color: '#888' }}>
              <span>{project.issue_count} issues</span>
              <span>{project.wiki_count} wiki</span>
              <span>{project.script_count} scripts</span>
            </div>
          </Link>
        ))}
      </div>

      {projects.length === 0 && !showCreate && (
        <p style={{ textAlign: 'center', color: '#888', marginTop: '48px' }}>
          No projects yet. Create one to get started.
        </p>
      )}
    </div>
  );
}
