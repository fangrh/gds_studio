import { useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import LayerSelector from '../../components/LayerSelector';
import DeepLink from '../../components/DeepLink';

interface Layer {
  name: string;
  visible: boolean;
  color: string;
}

function GdsViewer() {
  const [searchParams] = useSearchParams();
  const mapRef = useRef<HTMLDivElement>(null);
  const [layers, setLayers] = useState<Layer[]>([]);
  const [hoveredElement, setHoveredElement] = useState<{
    cell: string; elementId: number; layer: string; bbox: string;
  } | null>(null);

  const gds = searchParams.get('gds') || '';
  const cell = searchParams.get('cell') || '';
  const elem = searchParams.get('elem') || '';
  const layer = searchParams.get('layer') || '';
  const bbox = searchParams.get('bbox') || '';

  useEffect(() => {
    // In production: load tile pyramid from /api/gds/tiles/{gds}/{z}/{x}/{y}
    // and render with OpenLayers WebGL tile layer.
  }, [gds, cell, elem, layer, bbox]);

  function handleLayerToggle(layerName: string) {
    setLayers(prev =>
      prev.map(l => l.name === layerName ? { ...l, visible: !l.visible } : l)
    );
  }

  return (
    <div style={{ display: 'flex', height: '100%' }}>
      <LayerSelector layers={layers} onToggle={handleLayerToggle} />
      <div style={{ flex: 1, position: 'relative' }}>
        <div
          ref={mapRef}
          style={{
            width: '100%', height: '100%', background: '#1a1a2e',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#888',
          }}
        >
          {gds ? (
            <div style={{ textAlign: 'center' }}>
              <p>GDS: <strong>{gds}</strong></p>
              {cell && <p>Cell: <strong>{cell}</strong></p>}
              {elem && <p>Element: <strong>{elem}</strong></p>}
              {layer && <p>Layer: <strong>{layer}</strong></p>}
              {bbox && <p>BBox: <strong>{bbox}</strong></p>}
            </div>
          ) : (
            <p>Select a GDS file to view</p>
          )}
        </div>
        {hoveredElement && (
          <DeepLink
            gds={gds}
            cell={hoveredElement.cell}
            elementId={hoveredElement.elementId}
            layer={hoveredElement.layer}
            bbox={hoveredElement.bbox}
          />
        )}
      </div>
    </div>
  );
}

export default GdsViewer;
