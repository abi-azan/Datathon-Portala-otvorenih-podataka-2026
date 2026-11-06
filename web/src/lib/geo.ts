// Geometry shared by the WebGL maps (MapLibre) and the SVG maps that replace them where WebGL 2 is
// missing. Nothing here imports MapLibre, so the SVG maps stay out of its 1 MB chunk.
import type { MultiLineString, MultiPolygon, Polygon, Position } from 'geojson'

/** Croatia's bounding box: west, south, east, north. */
export const CROATIA: [number, number, number, number] = [13.45, 42.35, 19.45, 46.56]

/** Web Mercator y of a latitude, in degrees, so it shares a scale with longitude. */
export const mercY = (lat: number) => (Math.log(Math.tan(Math.PI / 4 + (lat * Math.PI) / 360)) * 180) / Math.PI

/** Width of the SVG maps' coordinate space; the height follows from Croatia's shape in Mercator. */
export const VIEW_W = 1000
const K = VIEW_W / (CROATIA[2] - CROATIA[0])
const TOP = mercY(CROATIA[3])
export const VIEW_H = Math.round((TOP - mercY(CROATIA[1])) * K)

/** A box in the SVG maps' coordinates: x, y, width, height. */
export type Box = [number, number, number, number]

/** [lon, lat] to SVG coordinates (Mercator, the same shape as the MapLibre maps). */
export const project = (p: Position): [number, number] => [(p[0] - CROATIA[0]) * K, (TOP - mercY(p[1])) * K]

/** One ring or line as path commands; points that round to the same tenth are dropped. */
function trace(points: Position[], close: boolean) {
  let d = ''
  let last = ''
  for (const p of points) {
    const [x, y] = project(p)
    const s = `${x.toFixed(1)},${y.toFixed(1)}`
    if (s === last) continue
    d += (d ? 'L' : 'M') + s
    last = s
  }
  return d && close ? d + 'Z' : d
}

/** SVG path data of a polygon, a multipolygon or a mesh of lines. */
export function pathOf(g: Polygon | MultiPolygon | MultiLineString): string {
  if (g.type === 'MultiLineString') return g.coordinates.map((l) => trace(l, false)).join('')
  const polys = g.type === 'Polygon' ? [g.coordinates] : g.coordinates
  return polys.map((rings) => rings.map((r) => trace(r, true)).join('')).join('')
}

/** Bounding box of a polygon or multipolygon in SVG coordinates. */
export function boxOf(g: Polygon | MultiPolygon): Box {
  let [x0, y0, x1, y1] = [Infinity, Infinity, -Infinity, -Infinity]
  const polys = g.type === 'Polygon' ? [g.coordinates] : g.coordinates
  for (const rings of polys)
    for (const p of rings[0]) {
      const [x, y] = project(p)
      x0 = Math.min(x0, x)
      y0 = Math.min(y0, y)
      x1 = Math.max(x1, x)
      y1 = Math.max(y1, y)
    }
  return [x0, y0, x1 - x0, y1 - y0]
}

/** The smallest box around several boxes; null when there are none. */
export function union(boxes: Box[]): Box | null {
  if (!boxes.length) return null
  const x0 = Math.min(...boxes.map((b) => b[0]))
  const y0 = Math.min(...boxes.map((b) => b[1]))
  const x1 = Math.max(...boxes.map((b) => b[0] + b[2]))
  const y1 = Math.max(...boxes.map((b) => b[1] + b[3]))
  return [x0, y0, x1 - x0, y1 - y0]
}
