import { useState, useEffect } from 'react';
import { useParams, Link, Outlet, useLocation } from 'react-router-dom';

interface Project {
  id: number;
  name: string;
  description: string;
  issue_count: number;
  wiki_count: number;
  script_count: number;
}

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const [project, setProject] = useState<Project | null>(null);

  useEffect(() => {
    fetch(`/api/projects/${id}`)
      .then(r => r.json())
      .then(setProject)
      .catch(() => setProject(null));
  }, [id]);

  if (!project) {
    return <div style={{ padding: '24px' }}>Loading project...</div>;
  }

  const projectId = parseInt(id!);
  const basePath = `/projects/${id}`;
  const isActive = (path: string) => location.pathname.startsWith(path);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{
        padding: '8px 16px',
        borderBottom: '1px solid #e0e0e0',
        background: '#f5f5f5',
        display: 'flex',
        alignItems: 'center',
        gap: '16px',
      }}>
        <Link to="/projects" style={{ textDecoration: 'none', color: '#666', fontSize: '14px' }}>
          &larr; Projects
        </Link>
        <span style={{ fontWeight: 'bold' }}>{project.name}</span>
        {project.description && (
          <span style={{ color: '#888', fontSize: '13px' }}>- {project.description}</span>
        )}
        <div style={{ marginLeft: 'auto', display: 'flex', gap: '12px' }}>
          <Link
            to={`${basePath}/viewer`}
            style={{
              fontWeight: isActive(`${basePath}/viewer`) ? 'bold' : 'normal',
              textDecoration: 'none', color: '#333', fontSize: '14px',
            }}
          >
            Viewer
          </Link>
          <Link
            to={`${basePath}/issues`}
            style={{
              fontWeight: isActive(`${basePath}/issues`) ? 'bold' : 'normal',
              textDecoration: 'none', color: '#333', fontSize: '14px',
            }}
          >
            Issues ({project.issue_count})
          </Link>
          <Link
            to={`${basePath}/wiki`}
            style={{
              fontWeight: isActive(`${basePath}/wiki`) ? 'bold' : 'normal',
              textDecoration: 'none', color: '#333', fontSize: '14px',
            }}
          >
            Wiki
          </Link>
        </div>
      </div>

      <div style={{ flex: 1, overflow: 'hidden' }}>
        <Outlet context={{ projectId }} />
      </div>
    </div>
  );
}
