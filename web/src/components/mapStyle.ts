import * as maplibregl from 'maplibre-gl'
import { GRADES } from '../lib/format'
import { SEQUENTIAL } from '../lib/views'

// OpenFreeMap: free vector tiles from OpenStreetMap data, no key (openfreemap.org).
export const BASEMAP = 'https://tiles.openfreemap.org/styles/positron'
export const CROATIA: [number, number, number, number] = [13.45, 42.35, 19.45, 46.56]

/** Fit padding that keeps Croatia clear of the map's caption. Below lg the caption sits in the top
 *  corner and the map is wide rather than tall, so a deeper top padding costs no zoom; from lg it sits
 *  bottom left, over the Italian coast, and needs none. */
export function fitPadding(caption: HTMLElement | null, base = 24) {
  const atTop = caption != null && caption.offsetTop < 40
  return { top: atTop ? Math.max(base, caption.offsetTop + caption.offsetHeight + 8) : base, bottom: base, left: base, right: base }
}

// Fallback when the OpenFreeMap style cannot be loaded: the choropleth still works on a plain background.
export const BLANK: maplibregl.StyleSpecification = {
  version: 8,
  sources: {},
  layers: [{ id: 'background', type: 'background', paint: { 'background-color': '#fdfdfc' } }],
}

/** Fill colour of a grade read from an expression (feature-state or property); white when missing. */
export const gradeFill = (value: maplibregl.ExpressionSpecification) =>
  ['match', ['coalesce', value, 0], ...GRADES.flatMap((g) => [g.value, g.color]), '#ffffff'] as unknown as maplibregl.ExpressionSpecification

/** Class of a context view's quintile 1-5 in `classFill`, kept apart from the grades 1-5. */
export const SEQUENTIAL_CLASS = 10

/** Fill colour of a class read from feature-state `key`: a grade 1-5, a quintile 11-15 on the
 *  sequential ramp, white when missing. One expression for all views, so a switch of view is a
 *  feature-state change like a change of year. */
export const classFill = (key: string) =>
  [
    'match',
    ['coalesce', ['feature-state', key], 0],
    ...GRADES.flatMap((g) => [g.value, g.color]),
    ...SEQUENTIAL.flatMap((c, i) => [SEQUENTIAL_CLASS + i + 1, c]),
    '#ffffff',
  ] as unknown as maplibregl.ExpressionSpecification

export const reducedMotion = () => window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false

/** Make the basemap recede: white land, pale sea, Croatian place names where OSM has them,
 *  and no land-use fills that could be mistaken for the neutral grade colour. */
export function quietBasemap(m: maplibregl.Map) {
  for (const l of m.getStyle().layers) {
    if (l.type === 'background') m.setPaintProperty(l.id, 'background-color', '#fdfdfc')
    else if (l.type === 'fill' && /water|ocean|sea/.test(l.id)) m.setPaintProperty(l.id, 'fill-color', '#dbe5ee')
    else if (l.type === 'fill' && /land|park|wood|grass|forest|residential|industrial|aeroway|building/.test(l.id))
      m.setLayoutProperty(l.id, 'visibility', 'none')
    else if (l.type === 'symbol' && m.getLayoutProperty(l.id, 'text-field'))
      m.setLayoutProperty(l.id, 'text-field', ['coalesce', ['get', 'name:hr'], ['get', 'name:latin'], ['get', 'name']])
  }
}
