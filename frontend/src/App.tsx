import { Routes, Route, Link, useLocation } from 'react-router-dom';
import GdsViewer from './panels/GdsViewer';
import IssuePanel from './panels/IssuePanel';
import WikiPanel from './panels/WikiPanel';
import ProjectList from './panels/ProjectList';
import ProjectDetail from './panels/ProjectDetail';

function App() {
  const location = useLocation();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <nav style={{
        display: 'flex', gap: '16px', padding: '8px 16px',
        borderBottom: '1px solid #e0e0e0', background: '#fafafa'
      }}>
        <Link to="/projects" style={{
          fontWeight: location.pathname.startsWith('/projects') ? 'bold' : 'normal',
          textDecoration: 'none', color: '#333',
        }}>
          Projects
        </Link>
        <Link to="/viewer" style={{
          fontWeight: location.pathname.startsWith('/viewer') ? 'bold' : 'normal',
          textDecoration: 'none', color: '#333',
        }}>
          GDS Viewer
        </Link>
        <Link to="/issues" style={{
          fontWeight: location.pathname.startsWith('/issues') ? 'bold' : 'normal',
          textDecoration: 'none', color: '#333',
        }}>
          Issues
        </Link>
        <Link to="/wiki" style={{
          fontWeight: location.pathname.startsWith('/wiki') ? 'bold' : 'normal',
          textDecoration: 'none', color: '#333',
        }}>
          Wiki
        </Link>
      </nav>

      <main style={{ flex: 1, overflow: 'hidden' }}>
        <Routes>
          {/* Project routes */}
          <Route path="/projects" element={<ProjectList />} />
          <Route path="/projects/:id" element={<ProjectDetail />}>
            <Route path="viewer" element={<GdsViewer />} />
            <Route path="issues" element={<IssuePanel />} />
            <Route path="issues/:id" element={<IssuePanel />} />
            <Route path="wiki" element={<WikiPanel />} />
            <Route path="wiki/:slug" element={<WikiPanel />} />
          </Route>

          {/* Global routes (backward compat) */}
          <Route path="/viewer" element={<GdsViewer />} />
          <Route path="/viewer/:params" element={<GdsViewer />} />
          <Route path="/issues" element={<IssuePanel />} />
          <Route path="/issues/:id" element={<IssuePanel />} />
          <Route path="/wiki" element={<WikiPanel />} />
          <Route path="/wiki/:slug" element={<WikiPanel />} />
          <Route path="/" element={<ProjectList />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
