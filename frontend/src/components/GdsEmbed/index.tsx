interface Props {
  deepLinkUrl?: string;
}

function GdsEmbed({ deepLinkUrl }: Props) {
  if (!deepLinkUrl) return null;

  return (
    <div style={{
      marginTop: '4px', padding: '4px 8px',
      background: '#fafafa', border: '1px dashed #ddd',
      borderRadius: '4px', fontSize: '11px', color: '#999',
    }}>
      [GDS Preview: {deepLinkUrl}]
    </div>
  );
}

export default GdsEmbed;
