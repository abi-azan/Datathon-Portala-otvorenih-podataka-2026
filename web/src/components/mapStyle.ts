import * as maplibregl from 'maplibre-gl'
import { GRADES } from '../lib/format'

// OpenFreeMap: free vector tiles from OpenStreetMap data, no key (openfreemap.org).
export const BASEMAP = 'https://tiles.openfreemap.org/styles/positron'
export const CROATIA: [number, number, number, number] = [13.45, 42.35, 19.45, 46.56]

// Fallback when the OpenFreeMap style cannot be loaded: the choropleth still works on a plain background.
export const BLANK: maplibregl.StyleSpecification = {
  version: 8,
  sources: {},
  layers: [{ id: 'background', type: 'background', paint: { 'background-color': '#fdfdfc' } }],
}

/** Fill colour of a grade read from an expression (feature-state or property); white when missing. */
export const gradeFill = (value: maplibregl.ExpressionSpecification) =>
  ['match', ['coalesce', value, 0], ...GRADES.flatMap((g) => [g.value, g.color]), '#ffffff'] as unknown as maplibregl.ExpressionSpecification

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
