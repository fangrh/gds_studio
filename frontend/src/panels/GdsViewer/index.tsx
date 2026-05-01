import { useEffect, useRef, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import Map from 'ol/Map';
import View from 'ol/View';
import VectorLayer from 'ol/layer/Vector';
import VectorSource from 'ol/source/Vector';
import { Style, Fill, Stroke } from 'ol/style';
import { Polygon } from 'ol/geom';
import Feature from 'ol/Feature';

interface LayerInfo {
  layer: number;
  datatype: number;
}

interface GeometryData {
  name: string;
  bbox: { left: number; bottom: number; right: number; top: number };
  layers: Record<string, LayerInfo>;
  elements: { type: string; layer: string; vertices: number[][] }[];
}

interface GdsFile {
  name: string;
  size: number;
}

const LAYER_COLORS: Record<string, string> = {
  '1/0': '#4488ff',
  '2/0': '#ff4488',
  '3/0': '#44ff88',
  '66/0': '#cccc44',
  '10/0': '#ff8844',
};

function getStyle(layer: string): Style {
  const color = LAYER_COLORS[layer] || '#44ff88';
  return new Style({
    fill: new Fill({ color: color + '80' }),
    stroke: new Stroke({ color, width: 0.5 }),
  });
}

const HIDDEN_STYLE = new Style({});

function GdsViewer() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const mapRef = useRef<HTMLDivElement>(null);
  const mapObjRef = useRef<Map | null>(null);
  const [layers, setLayers] = useState<{ name: string; visible: boolean; color: string; count: number }[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [files, setFiles] = useState<GdsFile[]>([]);

  const gds = searchParams.get('gds') || '';

  // Load GDS file list
  useEffect(() => {
    fetch('/api/gds/files')
      .then((r) => r.json())
      .then(setFiles)
      .catch(() => {});
  }, []);

  // Initialize OpenLayers map
  useEffect(() => {
    if (!mapRef.current || mapObjRef.current) return;

    const map = new Map({
      target: mapRef.current,
      view: new View({ center: [0, 0], zoom: 1 }),
      layers: [],
    });

    mapObjRef.current = map;

    map.on('pointermove', (evt) => {
      const feature = map.forEachFeatureAtPixel(evt.pixel, (f) => f);
      if (feature) {
        const layer = feature.get('layer');
        setInfo(`Layer: ${layer}`);
        mapRef.current!.style.cursor = 'crosshair';
      } else {
        setInfo(null);
        mapRef.current!.style.cursor = 'default';
      }
    });

    return () => {
      map.setTarget(undefined);
      mapObjRef.current = null;
    };
  }, []);

  // Load and render GDS geometry
  useEffect(() => {
    if (!gds || !mapObjRef.current) return;

    const loadGeometry = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`/api/gds/geometry/${gds}`);
        if (!res.ok) throw new Error(`Failed to load: ${res.status}`);
        const data: GeometryData = await res.json();

        const source = new VectorSource();
        data.elements.forEach((el, i) => {
          if (el.vertices.length < 3) return;
          const coords = [...el.vertices, el.vertices[0]];
          const polygon = new Polygon([coords]);
          const feature = new Feature({ geometry: polygon });
          feature.set('layer', el.layer);
          feature.set('index', i);
          feature.setStyle(getStyle(el.layer));
          source.addFeature(feature);
        });

        const layerCounts: Record<string, number> = {};
        data.elements.forEach((el) => {
          layerCounts[el.layer] = (layerCounts[el.layer] || 0) + 1;
        });

        const vectorLayer = new VectorLayer({ source });
        const map = mapObjRef.current!;
        map.getLayers().clear();
        map.addLayer(vectorLayer);

        const { left, bottom, right, top } = data.bbox;
        const extent: [number, number, number, number] = [left, bottom, right, top];
        map.getView().fit(extent, { padding: [40, 40, 40, 40], size: map.getSize() });

        setLayers(
          Object.entries(data.layers).map(([name]) => ({
            name,
            visible: true,
            color: LAYER_COLORS[name] || '#44ff88',
            count: layerCounts[name] || 0,
          }))
        );
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };

    loadGeometry();
  }, [gds]);

  function handleLayerToggle(layerName: string) {
    const newLayers = layers.map((l) =>
      l.name === layerName ? { ...l, visible: !l.visible } : l
    );
    setLayers(newLayers);
    if (!mapObjRef.current) return;
    mapObjRef.current.getLayers().forEach((layer) => {
      if (layer instanceof VectorLayer) {
        const source = layer.getSource();
        if (source) {
          source.forEachFeature((f) => {
            const fLayer = f.get('layer');
            const layerState = newLayers.find((l) => l.name === fLayer);
            if (layerState) {
              f.setStyle(layerState.visible ? getStyle(fLayer) : HIDDEN_STYLE);
            }
          });
        }
      }
    });
  }

  return (
    <div style={{ display: 'flex', height: '100%' }}>
      <div style={{ width: 200, borderRight: '1px solid #e0e0e0', padding: 8, overflowY: 'auto', background: '#fafafa' }}>
        <h4 style={{ margin: '0 0 8px 0', fontSize: 12, textTransform: 'uppercase', color: '#666' }}>
          GDS Files
        </h4>
        {files.map((f) => (
          <div
            key={f.name}
            onClick={() => navigate(`/viewer?gds=${f.name}`)}
            style={{
              padding: '4px 6px',
              cursor: 'pointer',
              borderRadius: 3,
              marginBottom: 2,
              fontSize: 12,
              background: gds === f.name ? '#e0e0ff' : 'transparent',
              fontWeight: gds === f.name ? 'bold' : 'normal',
            }}
          >
            {f.name}
          </div>
        ))}
        {files.length === 0 && (
          <p style={{ fontSize: 12, color: '#999' }}>No GDS files found</p>
        )}

        {layers.length > 0 && (
          <>
            <h4 style={{ margin: '12px 0 8px 0', fontSize: 12, textTransform: 'uppercase', color: '#666' }}>
              Layers
            </h4>
            {layers.map((l) => (
              <label key={l.name} style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4, cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={l.visible}
                  onChange={() => handleLayerToggle(l.name)}
                />
                <span style={{
                  display: 'inline-block', width: 12, height: 12,
                  backgroundColor: l.color, border: '1px solid #333',
                }} />
                <span style={{ fontSize: 12 }}>{l.name} ({l.count})</span>
              </label>
            ))}
          </>
        )}
      </div>
      <div style={{ flex: 1, position: 'relative' }}>
        <div
          ref={mapRef}
          style={{ width: '100%', height: '100%', background: '#1a1a2e' }}
        />
        {loading && (
          <div style={{
            position: 'absolute', top: 10, left: '50%', transform: 'translateX(-50%)',
            background: '#333', color: '#fff', padding: '4px 12px', borderRadius: 4, fontSize: 12,
          }}>
            Loading...
          </div>
        )}
        {error && (
          <div style={{
            position: 'absolute', top: 10, left: '50%', transform: 'translateX(-50%)',
            background: '#c00', color: '#fff', padding: '4px 12px', borderRadius: 4, fontSize: 12,
          }}>
            {error}
          </div>
        )}
        {info && (
          <div style={{
            position: 'absolute', bottom: 10, left: 10,
            background: 'rgba(0,0,0,0.7)', color: '#fff', padding: '4px 8px', borderRadius: 4, fontSize: 11,
          }}>
            {info}
          </div>
        )}
        {!gds && !loading && (
          <div style={{
            position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
            color: '#888', textAlign: 'center',
          }}>
            <p>Select a GDS file to view</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default GdsViewer;
