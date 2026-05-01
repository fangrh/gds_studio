interface Layer {
  name: string;
  visible: boolean;
  color: string;
}

interface Props {
  layers: Layer[];
  onToggle: (name: string) => void;
}

function LayerSelector({ layers, onToggle }: Props) {
  return (
    <div style={{
      width: '200px', borderRight: '1px solid #e0e0e0',
      padding: '12px', overflowY: 'auto', background: '#f5f5f5',
    }}>
      <h3 style={{ marginBottom: '12px', fontSize: '14px', fontWeight: 600 }}>
        Layers
      </h3>
      {layers.length === 0 && (
        <p style={{ color: '#999', fontSize: '13px' }}>No layers loaded</p>
      )}
      {layers.map(layer => (
        <label
          key={layer.name}
          style={{
            display: 'flex', alignItems: 'center', gap: '8px',
            padding: '4px 0', cursor: 'pointer', fontSize: '13px',
          }}
        >
          <input
            type="checkbox"
            checked={layer.visible}
            onChange={() => onToggle(layer.name)}
          />
          <span style={{
            display: 'inline-block', width: '12px', height: '12px',
            background: layer.color, borderRadius: '2px',
          }} />
          {layer.name}
        </label>
      ))}
    </div>
  );
}

export default LayerSelector;
