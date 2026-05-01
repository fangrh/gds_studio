interface Comment {
  id: number;
  author_type: string;
  body: string;
  agent_model?: string;
  created_at: string;
}

interface Props {
  comments: Comment[];
  onAddComment: () => void;
  commentBody: string;
  onCommentChange: (body: string) => void;
}

function CommentThread({ comments, onAddComment, commentBody, onCommentChange }: Props) {
  return (
    <div>
      <h3 style={{ fontSize: '14px', marginBottom: '12px' }}>Comments</h3>
      {comments.map(c => (
        <div key={c.id} style={{
          marginBottom: '12px', padding: '12px',
          border: c.author_type === 'agent' ? '1px solid #e3f2fd' : '1px solid #e0e0e0',
          borderRadius: '8px',
          background: c.author_type === 'agent' ? '#f5f9ff' : '#fff',
        }}>
          <div style={{ display: 'flex', gap: '8px', marginBottom: '4px' }}>
            <span style={{
              fontSize: '11px', fontWeight: 600,
              color: c.author_type === 'agent' ? '#1565C0' : '#333',
            }}>
              {c.author_type === 'agent' ? 'Agent' : 'User'}
            </span>
            {c.agent_model && (
              <span style={{ fontSize: '11px', color: '#999' }}>{c.agent_model}</span>
            )}
            <span style={{ fontSize: '11px', color: '#999' }}>
              {c.created_at ? new Date(c.created_at).toLocaleString() : ''}
            </span>
          </div>
          <p style={{ fontSize: '14px', whiteSpace: 'pre-wrap', lineHeight: 1.5 }}>
            {c.body}
          </p>
        </div>
      ))}
      <div style={{ marginTop: '12px' }}>
        <textarea
          value={commentBody}
          onChange={e => onCommentChange(e.target.value)}
          placeholder="Add a comment..."
          rows={3}
          style={{
            width: '100%', padding: '8px', border: '1px solid #ccc',
            borderRadius: '4px', fontSize: '14px', resize: 'vertical',
          }}
        />
        <button
          onClick={onAddComment}
          disabled={!commentBody.trim()}
          style={{
            marginTop: '8px', padding: '6px 16px',
            background: commentBody.trim() ? '#1976D2' : '#ccc',
            color: '#fff', border: 'none', borderRadius: '4px',
            cursor: commentBody.trim() ? 'pointer' : 'default', fontSize: '14px',
          }}
        >
          Comment
        </button>
      </div>
    </div>
  );
}

export default CommentThread;
