import { useCallback } from 'react';

export interface DeepLinkParams {
  gds: string;
  build?: number;
  cell?: string;
  layers?: string[];
  elem?: number;
  elems?: number[];
  layer?: string;
  bbox?: string;
}

export function buildDeepLink(params: DeepLinkParams): string {
  const parts: string[] = [];
  parts.push(`gds=${encodeURIComponent(params.gds)}`);
  if (params.build !== undefined) parts.push(`build=${params.build}`);
  if (params.cell) parts.push(`cell=${encodeURIComponent(params.cell)}`);
  if (params.layers) parts.push(`layers=${params.layers.join(',')}`);
  if (params.elem !== undefined) parts.push(`elem=${params.elem}`);
  if (params.elems) parts.push(`elems=${params.elems.join(',')}`);
  if (params.layer) parts.push(`layer=${encodeURIComponent(params.layer)}`);
  if (params.bbox) parts.push(`bbox=${encodeURIComponent(params.bbox)}`);
  return `/viewer?${parts.join('&')}`;
}

export function parseDeepLink(url: string): DeepLinkParams {
  const params = new URLSearchParams(url.includes('?') ? url.split('?')[1] : url);
  const result: DeepLinkParams = { gds: params.get('gds') || '' };

  const build = params.get('build');
  if (build) result.build = parseInt(build, 10);

  const cell = params.get('cell');
  if (cell) result.cell = cell;

  const layers = params.get('layers');
  if (layers) result.layers = layers.split(',');

  const elem = params.get('elem');
  if (elem) result.elem = parseInt(elem, 10);

  const elems = params.get('elems');
  if (elems) result.elems = elems.split(',').map(Number);

  const layer = params.get('layer');
  if (layer) result.layer = layer;

  const bbox = params.get('bbox');
  if (bbox) result.bbox = bbox;

  return result;
}

export function useDeepLink() {
  const buildLink = useCallback((params: DeepLinkParams) => buildDeepLink(params), []);
  const parseLink = useCallback((url: string) => parseDeepLink(url), []);
  return { buildLink, parseLink };
}
