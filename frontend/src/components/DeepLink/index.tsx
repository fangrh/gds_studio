import { useState } from 'react';

interface Props {
  gds: string;
  cell: string;
  elementId: number;
  layer: string;
  bbox: string;
}

function DeepLink({ gds, cell, elementId, layer, bbox }: Props) {
  const [copied, setCopied] = useState(false);

  const url = `/viewer?gds=${gds}&cell=${cell}&elem=${elementId}&layer=${layer}&bbox=${bbox}`;

  function handleCopy() {
    navigator.clipboard.writeText(window.location.origin + url).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <div style={{
      position: 'absolute', bottom: '16px', left: '16px',
      background: '#fff', border: '1px solid #ccc', borderRadius: '6px',
      padding: '8px 12px', fontSize: '12px', fontFamily: 'monospace',
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
    }}>
      <div style={{ marginBottom: '4px' }}>
        {cell} / elem:{elementId} ({layer})
      </div>
      <button
        onClick={handleCopy}
        style={{
          padding: '4px 8px', fontSize: '11px', cursor: 'pointer',
          border: '1px solid #ccc', borderRadius: '4px', background: copied ? '#e8f5e9' : '#fff',
        }}
      >
        {copied ? 'Copied!' : 'Copy Deep Link'}
      </button>
    </div>
  );
}

export default DeepLink;
