import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import CommentThread from '../../components/CommentThread';

interface WikiPage {
  id: number;
  title: string;
  slug: string;
  body: string;
  category: string;
  tags: string[];
  version: number;
  updated_at: string;
}

interface WikiListEntry {
  id: number;
  title: string;
  slug: string;
  category: string;
  tags: string[];
  version: number;
  updated_at: string;
}

function WikiPanel() {
  const { slug } = useParams<{ slug: string }>();
  const [pages, setPages] = useState<WikiListEntry[]>([]);
  const [page, setPage] = useState<WikiPage | null>(null);
  const [commentBody, setCommentBody] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [showNewForm, setShowNewForm] = useState(false);

  useEffect(() => {
    const url = categoryFilter
      ? `/api/wiki?category=${encodeURIComponent(categoryFilter)}`
      : '/api/wiki';
    fetch(url).then(r => r.json()).then(setPages);
  }, [categoryFilter]);

  useEffect(() => {
    if (slug) {
      fetch(`/api/wiki/${slug}`)
        .then(r => r.json())
        .then(setPage)
        .catch(() => setPage(null));
    } else {
      setPage(null);
    }
  }, [slug]);

  async function handleCreatePage(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const res = await fetch('/api/wiki', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: form.get('title'),
        slug: form.get('slug'),
        body: form.get('body'),
        category: form.get('category') || 'general',
        tags: (form.get('tags') as string || '').split(',').map(t => t.trim()).filter(Boolean),
      }),
    });
    if (res.ok) {
      const newPage = await res.json();
      setPages(prev => [newPage, ...prev]);
      setShowNewForm(false);
      (e.target as HTMLFormElement).reset();
    }
  }

  async function handleAddComment() {
    if (!slug || !page || !commentBody.trim()) return;
    const res = await fetch('/api/comments', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        target_type: 'wiki',
        target_id: page.id,
        body: commentBody,
      }),
    });
    if (res.ok) {
      setCommentBody('');
    }
  }

  const categories = [...new Set(pages.map(p => p.category))];

  if (slug && page) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        <div style={{ padding: '16px', borderBottom: '1px solid #e0e0e0' }}>
          <Link to="/wiki" style={{ fontSize: '13px', color: '#666' }}>&larr; Back to wiki</Link>
          <h2 style={{ marginTop: '8px' }}>{page.title}</h2>
          <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
            <span style={{ fontSize: '12px', color: '#666' }}>v{page.version}</span>
            <span style={{ fontSize: '12px', color: '#666' }}>
              Updated: {page.updated_at ? new Date(page.updated_at).toLocaleString() : ''}
            </span>
            {page.tags.map(tag => (
              <span key={tag} style={{
                padding: '2px 6px', borderRadius: '4px', fontSize: '11px', background: '#e0e0e0',
              }}>{tag}</span>
            ))}
          </div>
        </div>
        <div style={{ flex: 1, overflow: 'auto', padding: '16px' }}>
          <div style={{
            background: '#fff', border: '1px solid #e0e0e0',
            borderRadius: '8px', padding: '16px', marginBottom: '16px',
            whiteSpace: 'pre-wrap', fontSize: '14px', lineHeight: 1.7,
          }}>
            {page.body}
          </div>
          <CommentThread
            comments={[]}
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
          <button
            onClick={() => setCategoryFilter('')}
            style={{
              padding: '4px 12px', border: '1px solid #ccc', borderRadius: '16px',
              fontSize: '12px', cursor: 'pointer',
              background: categoryFilter === '' ? '#1976D2' : '#fff',
              color: categoryFilter === '' ? '#fff' : '#333',
            }}
          >
            All
          </button>
          {categories.map(cat => (
            <button
              key={cat}
              onClick={() => setCategoryFilter(cat)}
              style={{
                padding: '4px 12px', border: '1px solid #ccc', borderRadius: '16px',
                fontSize: '12px', cursor: 'pointer',
                background: categoryFilter === cat ? '#1976D2' : '#fff',
                color: categoryFilter === cat ? '#fff' : '#333',
              }}
            >
              {cat}
            </button>
          ))}
          <button
            onClick={() => setShowNewForm(!showNewForm)}
            style={{
              padding: '4px 12px', border: '1px solid #1976D2', borderRadius: '16px',
              fontSize: '12px', cursor: 'pointer', background: '#fff', color: '#1976D2',
              marginLeft: 'auto',
            }}
          >
            + New Page
          </button>
        </div>

        {showNewForm && (
          <form onSubmit={handleCreatePage} style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <input name="title" placeholder="Page title" required
              style={{ padding: '8px', border: '1px solid #ccc', borderRadius: '4px', fontSize: '14px' }} />
            <input name="slug" placeholder="page-slug" required
              style={{ padding: '8px', border: '1px solid #ccc', borderRadius: '4px', fontSize: '14px' }} />
            <textarea name="body" placeholder="Page content (markdown)" rows={4}
              style={{ padding: '8px', border: '1px solid #ccc', borderRadius: '4px', fontSize: '14px' }} />
            <div style={{ display: 'flex', gap: '8px' }}>
              <input name="category" placeholder="category" defaultValue="general"
                style={{ flex: 1, padding: '8px', border: '1px solid #ccc', borderRadius: '4px', fontSize: '14px' }} />
              <input name="tags" placeholder="tags (comma-separated)"
                style={{ flex: 2, padding: '8px', border: '1px solid #ccc', borderRadius: '4px', fontSize: '14px' }} />
            </div>
            <button type="submit" style={{
              padding: '8px 16px', background: '#1976D2', color: '#fff',
              border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '14px', alignSelf: 'flex-start',
            }}>
              Create Wiki Page
            </button>
          </form>
        )}
      </div>

      <div style={{ flex: 1, overflow: 'auto' }}>
        {pages.map(p => (
          <Link
            key={p.id}
            to={`/wiki/${p.slug}`}
            style={{ textDecoration: 'none', color: 'inherit' }}
          >
            <div style={{
              padding: '12px 16px', borderBottom: '1px solid #f0f0f0',
              display: 'flex', alignItems: 'center', gap: '12px',
            }}>
              <span style={{ flex: 1, fontSize: '14px', fontWeight: 500 }}>{p.title}</span>
              <span style={{
                fontSize: '11px', padding: '2px 8px', borderRadius: '12px',
                background: '#e3f2fd', color: '#1565C0',
              }}>
                {p.category}
              </span>
              <span style={{ fontSize: '11px', color: '#999' }}>v{p.version}</span>
              <span style={{ fontSize: '11px', color: '#999' }}>
                {p.updated_at ? new Date(p.updated_at).toLocaleDateString() : ''}
              </span>
            </div>
          </Link>
        ))}
        {pages.length === 0 && (
          <p style={{ textAlign: 'center', color: '#999', marginTop: '32px' }}>
            No wiki pages yet
          </p>
        )}
      </div>
    </div>
  );
}

export default WikiPanel;
