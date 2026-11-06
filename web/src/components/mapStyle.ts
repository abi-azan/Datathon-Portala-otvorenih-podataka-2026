import * as maplibregl from 'maplibre-gl'
import type { Feature, Polygon } from 'geojson'
import { merge } from 'topojson-client'
import type { GeometryObject, Topology } from 'topojson-specification'
import { CROATIA, mercY } from '../lib/geo'
import { GRADES } from '../lib/format'
import { SEQUENTIAL } from '../lib/views'

// OpenFreeMap: free vector tiles from OpenStreetMap data, no key (openfreemap.org).
export const BASEMAP = 'https://tiles.openfreemap.org/styles/positron'
export { CROATIA }
/** Lowest zoom of the maps: low enough that fitBounds can show all of Croatia in a 325 px wide map on a
 *  phone (about zoom 4.9 with the caption above it); on a desktop the first view is above 5.5 anyway. */
export const MIN_ZOOM = 4.5

// The westmost land of Croatia from Istria south, [lon, lat]: Savudrija, the west coast of Istria,
// Kamenjak, Unije, Susak, Lošinj, Premuda, Dugi otok, Kornati, Žirje, Biševo and Lastovo. A caption in
// the bottom left corner has to stay left of these (open-sea islets such as Svetac are left out).
const WEST_EDGE: [number, number][] = [
  [13.49, 45.5],
  [13.6, 45.1],
  [13.9, 44.77],
  [14.24, 44.62],
  [14.29, 44.51],
  [14.45, 44.47],
  [14.57, 44.33],
  [14.82, 44.15],
  [15.0, 43.95],
  [15.2, 43.8],
  [15.63, 43.65],
  [16.0, 42.97],
  [16.8, 42.75],
]

/** The left padding with which fitBounds(CROATIA) puts all land right of a caption that sits in the
 *  bottom left corner of the map. On a short map (a 1280×720 laptop) the caption with the legend is
 *  almost half the map's height and would cover the islands off Zadar and Šibenik. The padding grows
 *  only as far as Croatia stays within 10 % of its size at the smallest padding. */
function leftClear(caption: HTMLElement, base: number): number {
  const floor = base + 64
  const box = caption.offsetParent as HTMLElement | null
  const W = box?.clientWidth ?? 0
  const H = box?.clientHeight ?? 0
  if (!W || !H) return floor
  const [w, s, e, n] = CROATIA
  const cw = e - w
  const top = mercY(n)
  const ch = top - mercY(s)
  const scaleAt = (left: number) => Math.min((W - left - base) / cw, (H - 2 * base) / ch)
  const right = caption.offsetLeft + caption.offsetWidth + 10
  const above = caption.offsetTop - 10
  let best = floor
  for (let left = floor; left <= W - base - 200; left += 8) {
    const scale = scaleAt(left)
    if (scale < 0.9 * scaleAt(floor)) break
    best = left
    // fitBounds centres the bounds in the padded box
    const x0 = left + (W - left - base - cw * scale) / 2
    const y0 = base + (H - 2 * base - ch * scale) / 2
    if (WEST_EDGE.every(([lon, lat]) => y0 + (top - mercY(lat)) * scale < above || x0 + (lon - w) * scale >= right)) break
  }
  return best
}

/** Fit padding that keeps Croatia clear of the map's caption. Below lg the caption sits in the top
 *  corner and the map is wide rather than tall, so a deeper top padding costs no zoom; from lg it sits
 *  bottom left, over the Italian coast, and a wider left padding moves the islands to the right of it
 *  (the map is tall rather than wide there, so this too costs almost no zoom). */
export function fitPadding(caption: HTMLElement | null, base = 24) {
  const atTop = caption != null && caption.offsetTop < 40
  return atTop
    ? { top: Math.max(base, caption.offsetTop + caption.offsetHeight + 8), bottom: base, left: base, right: base }
    : { top: base, bottom: base, left: caption ? leftClear(caption, base) : base, right: base }
}

/** Land colour of the quiet basemap (and of BLANK). */
export const LAND = '#fdfdfc'

// Fallback when the OpenFreeMap style cannot be loaded: the choropleth still works on a plain background.
export const BLANK: maplibregl.StyleSpecification = {
  version: 8,
  sources: {},
  layers: [{ id: 'background', type: 'background', paint: { 'background-color': LAND } }],
}

/** `share` of colour `hex` over the land colour, as one opaque colour: what a fill of `hex` at
 *  opacity `share` looks like on the basemap. */
export function overLand(hex: string, share: number) {
  const ch = (h: string, i: number) => parseInt(h.slice(1 + 2 * i, 3 + 2 * i), 16)
  const mix = [0, 1, 2].map((i) => Math.round(share * ch(hex, i) + (1 - share) * ch(LAND, i)))
  return `#${mix.map((v) => v.toString(16).padStart(2, '0')).join('')}`
}

/** Fill colour of a grade read from an expression (feature-state or property); white when missing. */
export const gradeFill = (value: maplibregl.ExpressionSpecification) =>
  ['match', ['coalesce', value, 0], ...GRADES.flatMap((g) => [g.value, g.color]), '#ffffff'] as unknown as maplibregl.ExpressionSpecification

/** Class of a context view's quintile 1-5 in `classFill`, kept apart from the grades 1-5. */
export const SEQUENTIAL_CLASS = 10

/** Fill colour of a class read from feature-state `key`: a grade 1-5, a quintile 11-15 on the
 *  sequential ramp, white when missing. One expression for all views, so a switch of view is a
 *  feature-state change like a change of year. `share` < 1 mixes every colour with the land colour
 *  beforehand, so an opaque layer looks like the colour at that opacity. */
export const classFill = (key: string, share = 1) =>
  [
    'match',
    ['coalesce', ['feature-state', key], 0],
    ...GRADES.flatMap((g) => [g.value, overLand(g.color, share)]),
    ...SEQUENTIAL.flatMap((c, i) => [SEQUENTIAL_CLASS + i + 1, overLand(c, share)]),
    overLand('#ffffff', share),
  ] as unknown as maplibregl.ExpressionSpecification

/** How much the area outside Croatia is washed out: neighbouring countries stay recognisable
 *  (their names and borders are drawn above the veil), but the eye goes to the grades. */
const VEIL = 0.72

/** A land-coloured veil over everything outside Croatia: a world-sized polygon with every land part
 *  of Croatia (the merged counties: mainland, exclave, islands) cut out as a hole. Added below
 *  `beforeId` (the first label layer), so all place and country names stay on top. */
export function addOutsideVeil(m: maplibregl.Map, topo: Topology, beforeId?: string) {
  const counties = (topo.objects.zupanije as { geometries: GeometryObject[] }).geometries
  const croatia = merge(topo, counties as Parameters<typeof merge>[1])
  const holes = croatia.coordinates.map((poly) => poly[0])
  const veil: Feature<Polygon> = {
    type: 'Feature',
    properties: {},
    geometry: { type: 'Polygon', coordinates: [[[-180, -85], [180, -85], [180, 85], [-180, 85], [-180, -85]], ...holes] },
  }
  m.addSource('outside', { type: 'geojson', data: veil })
  m.addLayer({ id: 'outside-veil', type: 'fill', source: 'outside', paint: { 'fill-color': LAND, 'fill-opacity': VEIL, 'fill-antialias': false } }, beforeId)
}

export const reducedMotion = () => window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false

/** Make the basemap recede: white land, pale sea, Croatian place names where OSM has them,
 *  and no land-use fills that could be mistaken for the neutral grade colour. */
export function quietBasemap(m: maplibregl.Map) {
  for (const l of m.getStyle().layers) {
    if (l.type === 'background') m.setPaintProperty(l.id, 'background-color', LAND)
    else if (l.type === 'fill' && /water|ocean|sea/.test(l.id)) m.setPaintProperty(l.id, 'fill-color', '#dbe5ee')
    else if (l.type === 'fill' && /land|park|wood|grass|forest|residential|industrial|aeroway|building/.test(l.id))
      m.setLayoutProperty(l.id, 'visibility', 'none')
    else if (l.type === 'symbol' && m.getLayoutProperty(l.id, 'text-field'))
      m.setLayoutProperty(l.id, 'text-field', ['coalesce', ['get', 'name:hr'], ['get', 'name:latin'], ['get', 'name']])
  }
}
