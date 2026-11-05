import { useEffect, useState } from 'react'
import { feature } from 'topojson-client'
import type { GeometryCollection, Topology } from 'topojson-specification'
import type { Feature, MultiPolygon, Polygon, Position } from 'geojson'
import { topoUrl } from '../lib/data'
import { grade } from '../lib/format'

const W = 260
const H = 120
const PAD = 4
/** Neighbours' fill: a neutral grey, so the unit stands out by its grade colour and not only by its
 *  outline; light enough that grades 1-5 all read against it. */
const NEIGHBOUR = '#d3d2ca'

interface Props {
  /** jedinica: the unit's slug and its neighbours' slugs; zupanija: the county's id among all counties */
  kind: 'jedinica' | 'zupanija'
  slug: string
  neighbours: string[]
  zupId: number
  ocjena: number | null
  naziv: string
}

interface Shape {
  d: string
  own: boolean
}

/** The unit's outline among its neighbours in grey, drawn as SVG from geo/jls.topo.json
 *  (equirectangular, scaled by cos of the mean latitude). Loaded as its own chunk, after the page. */
export default function UnitOutline({ kind, slug, neighbours, zupId, ocjena, naziv }: Props) {
  const [shapes, setShapes] = useState<Shape[] | null>(null)
  const nb = neighbours.join(',')

  useEffect(() => {
    let off = false
    fetch(topoUrl())
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json() as Promise<Topology>
      })
      .then((t) => {
        if (off) return
        const layer = (kind === 'zupanija' ? t.objects.zupanije : t.objects.jls) as GeometryCollection
        const props = (g: { properties?: unknown }) => (g.properties ?? {}) as { slug?: string; zup_id?: number }
        const near = new Set(nb.split(','))
        const picked = layer.geometries.filter((g) =>
          kind === 'zupanija' ? true : props(g).slug === slug || near.has(props(g).slug ?? ''),
        )
        const feats = picked.map((g) => ({
          own: kind === 'zupanija' ? props(g).zup_id === zupId : props(g).slug === slug,
          f: feature(t, g) as Feature<Polygon | MultiPolygon>,
        }))
        const rings = (f: Feature<Polygon | MultiPolygon>): Position[][] =>
          f.geometry.type === 'Polygon' ? f.geometry.coordinates : f.geometry.coordinates.flat()
        const all = feats.flatMap(({ f }) => rings(f).flat())
        if (!all.length) return setShapes([])
        const lat0 = (Math.min(...all.map((p) => p[1])) + Math.max(...all.map((p) => p[1]))) / 2
        const kx = Math.cos((lat0 * Math.PI) / 180)
        const xs = all.map((p) => p[0] * kx)
        const ys = all.map((p) => -p[1])
        const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)]
        const s = Math.min((W - 2 * PAD) / (x1 - x0 || 1), (H - 2 * PAD) / (y1 - y0 || 1))
        // left-aligned with the text above, centred vertically
        const ox = PAD
        const oy = PAD + (H - 2 * PAD - (y1 - y0) * s) / 2
        const pt = (p: Position) => `${(ox + (p[0] * kx - x0) * s).toFixed(1)},${(oy + (-p[1] - y0) * s).toFixed(1)}`
        const path = (f: Feature<Polygon | MultiPolygon>) => rings(f).map((r) => `M${r.map(pt).join('L')}Z`).join('')
        // own shape last, so its outline is on top
        setShapes(feats.map(({ f, own }) => ({ d: path(f), own })).sort((a, b) => Number(a.own) - Number(b.own)))
      })
      .catch(() => !off && setShapes([]))
    return () => {
      off = true
    }
  }, [kind, slug, nb, zupId])

  if (!shapes?.length) return <div style={{ height: H }} aria-hidden />
  const fill = grade(ocjena)?.color ?? '#ffffff'
  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      width={W}
      height={H}
      role="img"
      aria-label={kind === 'zupanija' ? `${naziv} na karti Hrvatske` : `${naziv} sa susjednim jedinicama`}
      className="max-w-full"
    >
      {shapes.map((sh, i) => (
        <path
          key={i}
          d={sh.d}
          fill={sh.own ? fill : NEIGHBOUR}
          stroke={sh.own ? '#0b0b0b' : '#ffffff'}
          strokeWidth={sh.own ? 1.2 : 0.8}
          strokeLinejoin="round"
          fillRule="evenodd"
        />
      ))}
    </svg>
  )
}
