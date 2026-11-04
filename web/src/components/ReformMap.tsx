import * as maplibregl from 'maplibre-gl'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url'
import 'maplibre-gl/dist/maplibre-gl.css'
import { useEffect, useMemo, useRef, useState } from 'react'
import { feature, merge } from 'topojson-client'
import type { GeometryCollection, MultiPolygon, Polygon, Topology } from 'topojson-specification'
import type { Feature, FeatureCollection } from 'geojson'
import { topoUrl, type ReformUnit } from '../lib/data'
import { num } from '../lib/format'
import { GradeChip } from './Grade'
import { BASEMAP, BLANK, CROATIA, gradeFill, quietBasemap } from './mapStyle'

maplibregl.setWorkerUrl(workerUrl)

const reformKey = (u: ReformUnit) => u.clanice.join('-')
const ZAGREB = '01333'

interface Props {
  units: ReformUnit[]
  prag: number
  selected?: string
  onSelect?: (key: string) => void
}

interface Hover {
  left: number
  top: number
  key: string
}

const TOOLTIP_W = 260
const TOOLTIP_H = 120

/** Karta reforme: the units after the scenario, members' polygons dissolved into one per group
 *  on the client (topojson-client merge over geo/jls.topo.json), coloured by the grade after. */
export function ReformMap({ units, prag, selected, onSelect }: Props) {
  const box = useRef<HTMLDivElement>(null)
  const map = useRef<maplibregl.Map | null>(null)
  const topo = useRef<Topology | null>(null)
  const [ready, setReady] = useState(false)
  const [failed, setFailed] = useState(false)
  const [hover, setHover] = useState<Hover | null>(null)
  const byKey = useMemo(() => new Map(units.map((u) => [reformKey(u), u])), [units])
  const onSelectRef = useRef(onSelect)
  useEffect(() => {
    onSelectRef.current = onSelect
  }, [onSelect])

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
    let removed = false
    let styleOk = false
    m.on('style.load', () => {
      styleOk = true
    })
    m.on('error', (e) => {
      if (!styleOk && !removed) {
        console.warn('Basemap unavailable, using a plain background', e.error)
        styleOk = true
        m.setStyle(BLANK)
      }
    })
    m.once('load', async () => {
      quietBasemap(m)
      try {
        topo.current = (await fetch(topoUrl()).then((r) => {
          if (!r.ok) throw new Error(`HTTP ${r.status}`)
          return r.json()
        })) as Topology
      } catch {
        if (!removed) setFailed(true)
        return
      }
      if (removed) return
      const t = topo.current
      const firstLabel = m.getStyle().layers.find((l: maplibregl.LayerSpecification) => l.type === 'symbol')?.id
      m.addSource('reform', { type: 'geojson', data: { type: 'FeatureCollection', features: [] }, promoteId: 'key' })
      m.addSource('jls', { type: 'geojson', data: feature(t, t.objects.jls) as FeatureCollection })
      m.addSource('zup', { type: 'geojson', data: feature(t, t.objects.zupanije) as FeatureCollection })
      m.addLayer({ id: 'reform-fill', type: 'fill', source: 'reform', paint: { 'fill-color': gradeFill(['get', 'g']), 'fill-opacity': 0.94 } }, firstLabel)
      // the old borders inside a merged unit, faint, so the members stay visible
      m.addLayer({ id: 'jls-line', type: 'line', source: 'jls', paint: { 'line-color': '#ffffff', 'line-width': 0.4, 'line-opacity': 0.45 } }, firstLabel)
      m.addLayer({ id: 'reform-line', type: 'line', source: 'reform', paint: { 'line-color': '#ffffff', 'line-width': 1.4 } }, firstLabel)
      m.addLayer({ id: 'zup-line', type: 'line', source: 'zup', paint: { 'line-color': '#52514e', 'line-width': 1, 'line-opacity': 0.7 } }, firstLabel)
      m.addLayer({
        id: 'reform-hover',
        type: 'line',
        source: 'reform',
        paint: { 'line-color': '#0b0b0b', 'line-width': ['case', ['boolean', ['feature-state', 'hover'], false], 2.2, 0] },
      })
      m.addLayer({ id: 'reform-selected', type: 'line', source: 'reform', filter: ['==', ['get', 'key'], ''], paint: { 'line-color': '#0b0b0b', 'line-width': 3.5 } })
      setReady(true)
    })

    let hovered: string | null = null
    m.on('mousemove', 'reform-fill', (e: maplibregl.MapLayerMouseEvent) => {
      const key = e.features?.[0]?.properties?.key as string | undefined
      if (!key) return
      if (hovered !== key) {
        if (hovered) m.setFeatureState({ source: 'reform', id: hovered }, { hover: false })
        hovered = key
        m.setFeatureState({ source: 'reform', id: key }, { hover: true })
      }
      m.getCanvas().style.cursor = key === ZAGREB ? '' : 'pointer'
      const { clientWidth: width, clientHeight: height } = m.getContainer()
      const left = e.point.x + 16 + TOOLTIP_W > width - 8 ? e.point.x - 16 - TOOLTIP_W : e.point.x + 16
      const top = e.point.y + TOOLTIP_H > height - 8 ? e.point.y - TOOLTIP_H - 12 : e.point.y - 12
      setHover({ left: Math.max(8, left), top: Math.max(8, top), key })
    })
    m.on('mouseleave', 'reform-fill', () => {
      if (hovered) m.setFeatureState({ source: 'reform', id: hovered }, { hover: false })
      hovered = null
      m.getCanvas().style.cursor = ''
      setHover(null)
    })
    m.on('click', 'reform-fill', (e: maplibregl.MapLayerMouseEvent) => {
      const key = e.features?.[0]?.properties?.key as string | undefined
      if (key && key !== ZAGREB) onSelectRef.current?.(key)
    })
    return () => {
      removed = true
      m.remove()
    }
  }, [])

  // dissolve each group's members into one shape whenever the threshold changes
  useEffect(() => {
    const m = map.current
    const t = topo.current
    if (!ready || !m || !t) return
    const geoms = (t.objects.jls as GeometryCollection<{ sifra: string }>).geometries
    const bySifra = new Map(geoms.map((g) => [(g.properties as { sifra: string }).sifra, g as Polygon | MultiPolygon]))
    const features: Feature[] = []
    for (const u of units) {
      const parts = u.clanice.map((s) => bySifra.get(s)).filter((g): g is Polygon | MultiPolygon => !!g)
      if (!parts.length) continue
      features.push({ type: 'Feature', properties: { key: reformKey(u), g: u.ocjena ?? 0 }, geometry: merge(t, parts) })
    }
    const zg = bySifra.get(ZAGREB)
    if (zg) features.push({ type: 'Feature', properties: { key: ZAGREB, g: 0 }, geometry: merge(t, [zg]) })
    ;(m.getSource('reform') as maplibregl.GeoJSONSource).setData({ type: 'FeatureCollection', features })
  }, [ready, units])

  useEffect(() => {
    const m = map.current
    if (!ready || !m) return
    m.setFilter('reform-selected', ['==', ['get', 'key'], selected ?? ''])
  }, [ready, selected])

  const h = hover ? byKey.get(hover.key) : undefined
  return (
    <div className="relative h-full w-full overflow-hidden rounded-2xl border border-hairline bg-surface">
      <div ref={box} className="h-full w-full" aria-label={`Karta reforme za prag od ${num(prag)} stanovnika`} role="region" />
      <div className="pointer-events-none absolute top-4 left-4 max-w-[calc(100%-5.5rem)] rounded-lg bg-card/90 px-3 py-2 shadow-sm backdrop-blur">
        <div className="text-sm font-semibold">Ocjena poslije reforme, prag {num(prag)} stanovnika</div>
        <div className="text-xs text-muted">bijele crte su stare granice · klikni za pojedinosti</div>
      </div>
      {!ready && (
        <div className="absolute inset-0 grid place-items-center text-sm text-muted">
          {failed ? 'Karta se nije učitala. Osvježi stranicu.' : 'Učitavam kartu…'}
        </div>
      )}
      {hover && (
        <div
          className="pointer-events-none absolute z-10 rounded-xl border border-hairline bg-card/95 p-3 shadow-lg backdrop-blur"
          style={{ left: hover.left, top: hover.top, width: TOOLTIP_W }}
        >
          {h ? (
            <>
              <div className="font-serif text-lg leading-tight font-semibold">{h.naziv}</div>
              <div className="mt-0.5 text-xs text-muted">
                {h.clanice.length > 1 ? `${h.clanice.length} jedinice · ` : 'bez spajanja · '}
                {num(h.stanovnici)} stanovnika
              </div>
              <div className="mt-2 flex items-center gap-2">
                <GradeChip g={h.ocjena} />
                <span className="tabular text-sm text-ink-2">{num(h.bodovi, 1)} / 100</span>
              </div>
            </>
          ) : (
            <div className="text-sm">Grad Zagreb nije uključen u scenarij.</div>
          )}
        </div>
      )}
    </div>
  )
}
