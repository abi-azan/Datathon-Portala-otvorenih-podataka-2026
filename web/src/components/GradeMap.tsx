import * as maplibregl from 'maplibre-gl'
// The worker is self-contained; point MapLibre at it explicitly, because Vite's dependency
// pre-bundling (dev) and chunking (build) break the default URL next to maplibre-gl.mjs.
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url'
import { useEffect, useRef, useState } from 'react'
import { feature } from 'topojson-client'
import type { Topology } from 'topojson-specification'
import type { FeatureCollection } from 'geojson'
import { topoUrl, type UnitIndex } from '../lib/data'
import { GRADES, grade, num } from '../lib/format'
import { go, unitHref } from '../lib/router'
import { GradeChip } from './Grade'

// OpenFreeMap: free vector tiles from OpenStreetMap data, no key (openfreemap.org).
const BASEMAP = 'https://tiles.openfreemap.org/styles/positron'
const CROATIA: [number, number, number, number] = [13.45, 42.35, 19.45, 46.56]
maplibregl.setWorkerUrl(workerUrl)

const fillColor = [
  'match',
  ['coalesce', ['feature-state', 'g'], 0],
  ...GRADES.flatMap((g) => [g.value, g.color]),
  '#ffffff',
] as unknown as maplibregl.ExpressionSpecification

/** Make the basemap recede: white land, pale sea, Croatian place names where OSM has them,
 *  and no land-use fills that could be mistaken for the neutral grade colour. */
function quietBasemap(m: maplibregl.Map) {
  for (const l of m.getStyle().layers) {
    if (l.type === 'background') m.setPaintProperty(l.id, 'background-color', '#fdfdfc')
    else if (l.type === 'fill' && /water|ocean|sea/.test(l.id)) m.setPaintProperty(l.id, 'fill-color', '#dbe5ee')
    else if (l.type === 'fill' && /land|park|wood|grass|forest|residential|industrial|aeroway|building/.test(l.id))
      m.setLayoutProperty(l.id, 'visibility', 'none')
    else if (l.type === 'symbol' && m.getLayoutProperty(l.id, 'text-field'))
      m.setLayoutProperty(l.id, 'text-field', ['coalesce', ['get', 'name:hr'], ['get', 'name:latin'], ['get', 'name']])
  }
}

interface Props {
  units: UnitIndex[]
  year: string
}

interface Hover {
  x: number
  y: number
  unit: UnitIndex
}

export function GradeMap({ units, year }: Props) {
  const box = useRef<HTMLDivElement>(null)
  const map = useRef<maplibregl.Map | null>(null)
  const [ready, setReady] = useState(false)
  const [hover, setHover] = useState<Hover | null>(null)
  const bySifra = useRef(new Map<string, UnitIndex>())
  bySifra.current = new Map(units.map((u) => [u.sifra, u]))

  useEffect(() => {
    if (!box.current) return
    const m = new maplibregl.Map({
      container: box.current,
      style: BASEMAP,
      bounds: CROATIA,
      fitBoundsOptions: { padding: 24 },
      minZoom: 5.5,
      maxZoom: 11,
      attributionControl: { compact: true },
      dragRotate: false,
      pitchWithRotate: false,
    })
    m.touchZoomRotate.disableRotation()
    m.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right')
    map.current = m

    m.on('load', async () => {
      quietBasemap(m)
      const topo = (await fetch(topoUrl()).then((r) => r.json())) as Topology
      const jls = feature(topo, topo.objects.jls) as FeatureCollection
      const zup = feature(topo, topo.objects.zupanije) as FeatureCollection
      const firstLabel = m.getStyle().layers.find((l: maplibregl.LayerSpecification) => l.type === 'symbol')?.id
      m.addSource('jls', { type: 'geojson', data: jls, promoteId: 'sifra' })
      m.addSource('zup', { type: 'geojson', data: zup })
      m.addLayer({ id: 'jls-fill', type: 'fill', source: 'jls', paint: { 'fill-color': fillColor, 'fill-opacity': 0.94 } }, firstLabel)
      m.addLayer({ id: 'jls-line', type: 'line', source: 'jls', paint: { 'line-color': '#ffffff', 'line-width': 0.5, 'line-opacity': 0.9 } }, firstLabel)
      m.addLayer({ id: 'zup-line', type: 'line', source: 'zup', paint: { 'line-color': '#52514e', 'line-width': 1, 'line-opacity': 0.7 } }, firstLabel)
      m.addLayer({
        id: 'jls-hover',
        type: 'line',
        source: 'jls',
        paint: {
          'line-color': '#0b0b0b',
          'line-width': ['case', ['boolean', ['feature-state', 'hover'], false], 2.2, 0],
        },
      })
      setReady(true)
    })

    let hovered: string | null = null
    m.on('mousemove', 'jls-fill', (e: maplibregl.MapLayerMouseEvent) => {
      const f = e.features?.[0]
      const sifra = f?.properties?.sifra as string | undefined
      if (!sifra) return
      if (hovered !== sifra) {
        if (hovered) m.setFeatureState({ source: 'jls', id: hovered }, { hover: false })
        hovered = sifra
        m.setFeatureState({ source: 'jls', id: sifra }, { hover: true })
      }
      m.getCanvas().style.cursor = 'pointer'
      const unit = bySifra.current.get(sifra)
      if (unit) setHover({ x: e.point.x, y: e.point.y, unit })
    })
    m.on('mouseleave', 'jls-fill', () => {
      if (hovered) m.setFeatureState({ source: 'jls', id: hovered }, { hover: false })
      hovered = null
      m.getCanvas().style.cursor = ''
      setHover(null)
    })
    m.on('click', 'jls-fill', (e: maplibregl.MapLayerMouseEvent) => {
      const slug = e.features?.[0]?.properties?.slug as string | undefined
      if (slug) go(unitHref(slug))
    })
    return () => m.remove()
  }, [])

  // recolour when the year changes
  useEffect(() => {
    const m = map.current
    if (!ready || !m) return
    for (const u of units) {
      if (u.vrsta === 'zupanija') continue
      m.setFeatureState({ source: 'jls', id: u.sifra }, { g: u.ocjena[year] ?? 0 })
    }
  }, [ready, units, year])

  const h = hover && grade(hover.unit.ocjena[year])
  return (
    <div className="relative h-full w-full overflow-hidden rounded-2xl border border-hairline bg-surface">
      <div ref={box} className="h-full w-full" aria-label="Karta ocjena općina i gradova" role="region" />
      <div className="pointer-events-none absolute top-4 left-4 rounded-lg bg-card/90 px-3 py-2 shadow-sm backdrop-blur">
        <div className="text-sm font-semibold">Ocjena financijske stabilnosti, {year}.</div>
        <div className="text-xs text-muted">556 općina i gradova · prijeđi mišem, klikni za svjedodžbu</div>
      </div>
      {!ready && (
        <div className="absolute inset-0 grid place-items-center text-sm text-muted">Učitavam kartu…</div>
      )}
      {hover && (
        <div
          className="pointer-events-none absolute z-10 w-64 rounded-xl border border-hairline bg-card/95 p-3 shadow-lg backdrop-blur"
          style={{
            left: Math.min(hover.x + 16, (box.current?.clientWidth ?? 0) - 272),
            top: Math.max(hover.y - 12, 8),
          }}
        >
          <div className="font-serif text-lg leading-tight font-semibold">{hover.unit.naziv}</div>
          <div className="mt-0.5 text-xs text-muted">
            {hover.unit.zupanija} · {num(hover.unit.stanovnici)} stanovnika
          </div>
          <div className="mt-2 flex items-center gap-2">
            {h ? <GradeChip g={h.value} /> : <span className="text-sm text-muted">nema podataka</span>}
            <span className="tabular text-sm text-ink-2">{num(hover.unit.bodovi[year], 1)} / 100 bodova</span>
          </div>
          <div className="mt-2 text-xs text-muted">Klikni za svjedodžbu jedinice</div>
        </div>
      )}
    </div>
  )
}
