import * as maplibregl from 'maplibre-gl'
// The worker is self-contained; point MapLibre at it explicitly, because Vite's dependency
// pre-bundling (dev) and chunking (build) break the default URL next to maplibre-gl.mjs.
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url'
// Imported here, not in index.css, so the stylesheet ships in the lazy map chunk.
import 'maplibre-gl/dist/maplibre-gl.css'
import { useEffect, useRef, useState } from 'react'
import { feature } from 'topojson-client'
import type { Topology } from 'topojson-specification'
import type { FeatureCollection } from 'geojson'
import { topoUrl, type UnitIndex } from '../lib/data'
import { grade, num } from '../lib/format'
import { go, unitHref } from '../lib/router'
import { GradeChip } from './Grade'
import { BASEMAP, BLANK, CROATIA, gradeFill, quietBasemap } from './mapStyle'
import { SEQUENTIAL, classOf, contextView, quintiles, type ViewKey } from '../lib/views'

maplibregl.setWorkerUrl(workerUrl)

const fillColor = gradeFill(['feature-state', 'g'])

/** What the fill encodes: the grade, or one of the two context views (lib/views.ts). */
export type MapColorBy = ViewKey

// The context views colour their quintile class 1-5 (feature-state `g`) on the sequential ramp.
const sequentialFill = [
  'match',
  ['coalesce', ['feature-state', 'g'], 0],
  ...SEQUENTIAL.flatMap((c, i) => [i + 1, c]),
  '#ffffff',
] as unknown as maplibregl.ExpressionSpecification

interface Props {
  units: UnitIndex[]
  year: string
  colorBy?: MapColorBy
  /** Click picks a unit (onSelect) instead of opening its profile. */
  selectable?: boolean
  /** Šifre of units drawn with a thick outline. */
  selected?: string[]
  onSelect?: (sifra: string) => void
  /** Šifre of units drawn faded (e.g. not allowed as the next pick in the simulator). */
  dimmed?: string[]
  /** Tooltip footer for a unit, instead of the default click hint (e.g. why it cannot be picked). */
  hint?: (sifra: string) => string | undefined
  /** Šifre of units to fit the view to whenever this list changes (e.g. the county of the selection). */
  focus?: string[]
}

interface Hover {
  left: number
  top: number
  unit: UnitIndex
}

const TOOLTIP_W = 256
const TOOLTIP_H = 132 // approximate height, to keep the tooltip inside the map

export function GradeMap({ units, year, colorBy = 'ocjena', selectable = false, selected, onSelect, dimmed, hint, focus }: Props) {
  const box = useRef<HTMLDivElement>(null)
  const map = useRef<maplibregl.Map | null>(null)
  const [ready, setReady] = useState(false)
  const [hover, setHover] = useState<Hover | null>(null)
  const [failed, setFailed] = useState(false)
  const bySifra = useRef(new Map<string, UnitIndex>())
  useEffect(() => {
    bySifra.current = new Map(units.map((u) => [u.sifra, u]))
  }, [units])
  // the map's click handler is registered once, so it reads the latest props from here
  const clickProps = useRef({ selectable, onSelect })
  useEffect(() => {
    clickProps.current = { selectable, onSelect }
  }, [selectable, onSelect])
  const outlined = useRef(new Set<string>())
  const faded = useRef(new Set<string>())
  const geo = useRef<FeatureCollection | null>(null)

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
    outlined.current = new Set()
    faded.current = new Set()
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
      let topo: Topology
      try {
        topo = (await fetch(topoUrl()).then((r) => {
          if (!r.ok) throw new Error(`HTTP ${r.status}`)
          return r.json()
        })) as Topology
      } catch {
        if (!removed) setFailed(true)
        return
      }
      if (removed) return
      const jls = feature(topo, topo.objects.jls) as FeatureCollection
      const zup = feature(topo, topo.objects.zupanije) as FeatureCollection
      geo.current = jls
      const firstLabel = m.getStyle().layers.find((l: maplibregl.LayerSpecification) => l.type === 'symbol')?.id
      m.addSource('jls', { type: 'geojson', data: jls, promoteId: 'sifra' })
      m.addSource('zup', { type: 'geojson', data: zup })
      m.addLayer(
        {
          id: 'jls-fill',
          type: 'fill',
          source: 'jls',
          paint: {
            'fill-color': fillColor,
            'fill-opacity': ['case', ['boolean', ['feature-state', 'dim'], false], 0.22, 0.94],
          },
        },
        firstLabel,
      )
      m.addLayer({ id: 'jls-line', type: 'line', source: 'jls', paint: { 'line-color': '#ffffff', 'line-width': 0.5, 'line-opacity': 0.9 } }, firstLabel)
      m.addLayer({ id: 'zup-line', type: 'line', source: 'zup', paint: { 'line-color': '#52514e', 'line-width': 1, 'line-opacity': 0.7 } }, firstLabel)
      m.addLayer({
        id: 'jls-selected',
        type: 'line',
        source: 'jls',
        paint: {
          'line-color': '#0b0b0b',
          'line-width': ['case', ['boolean', ['feature-state', 'selected'], false], 3.5, 0],
        },
      })
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
      const { clientWidth: width, clientHeight: height } = m.getContainer()
      // right of the cursor, or left of it near the right edge; above it near the bottom edge
      const left = e.point.x + 16 + TOOLTIP_W > width - 8 ? e.point.x - 16 - TOOLTIP_W : e.point.x + 16
      const top = e.point.y + TOOLTIP_H > height - 8 ? e.point.y - TOOLTIP_H - 12 : e.point.y - 12
      if (unit) setHover({ left: Math.max(8, left), top: Math.max(8, top), unit })
    })
    m.on('mouseleave', 'jls-fill', () => {
      if (hovered) m.setFeatureState({ source: 'jls', id: hovered }, { hover: false })
      hovered = null
      m.getCanvas().style.cursor = ''
      setHover(null)
    })
    m.on('click', 'jls-fill', (e: maplibregl.MapLayerMouseEvent) => {
      const props = e.features?.[0]?.properties
      const { selectable, onSelect } = clickProps.current
      if (selectable) {
        const sifra = props?.sifra as string | undefined
        if (sifra) onSelect?.(sifra)
        return
      }
      const slug = props?.slug as string | undefined
      if (slug) go(unitHref(slug))
    })
    return () => {
      removed = true
      m.remove()
    }
  }, [])

  // recolour when the year or the colouring changes
  useEffect(() => {
    const m = map.current
    if (!ready || !m) return
    const view = contextView(colorBy)
    const cuts = view ? quintiles(units, view, year) : []
    m.setPaintProperty('jls-fill', 'fill-color', view ? sequentialFill : fillColor)
    for (const u of units) {
      if (u.vrsta === 'zupanija') continue
      const g = view ? classOf(view.value(u, year), cuts) : (u.ocjena[year] ?? 0)
      m.setFeatureState({ source: 'jls', id: u.sifra }, { g })
    }
  }, [ready, units, year, colorBy])

  // outline the selected units; only the difference to the last call touches the map
  useEffect(() => {
    const m = map.current
    if (!ready || !m) return
    const next = new Set(selected ?? [])
    for (const s of outlined.current) if (!next.has(s)) m.setFeatureState({ source: 'jls', id: s }, { selected: false })
    for (const s of next) if (!outlined.current.has(s)) m.setFeatureState({ source: 'jls', id: s }, { selected: true })
    outlined.current = next
  }, [ready, selected])

  // fade the units that cannot be picked; same diffing as the outline
  useEffect(() => {
    const m = map.current
    if (!ready || !m) return
    const next = new Set(dimmed ?? [])
    for (const s of faded.current) if (!next.has(s)) m.setFeatureState({ source: 'jls', id: s }, { dim: false })
    for (const s of next) if (!faded.current.has(s)) m.setFeatureState({ source: 'jls', id: s }, { dim: true })
    faded.current = next
  }, [ready, dimmed])

  // fit the view to the focus units when their list changes; back to the whole country when it empties
  const focusKey = (focus ?? []).join(',')
  const fitted = useRef(false)
  useEffect(() => {
    const m = map.current
    if (!ready || !m || !geo.current) return
    if (!focusKey) {
      if (fitted.current) m.fitBounds(CROATIA, { padding: 24, duration: 600 })
      fitted.current = false
      return
    }
    fitted.current = true
    const want = new Set(focusKey.split(','))
    let [w, s, e, n] = [180, 90, -180, -90]
    const visit = (c: unknown): void => {
      if (Array.isArray(c) && typeof c[0] === 'number') {
        const [x, y] = c as number[]
        w = Math.min(w, x)
        e = Math.max(e, x)
        s = Math.min(s, y)
        n = Math.max(n, y)
      } else if (Array.isArray(c)) c.forEach(visit)
    }
    for (const f of geo.current.features) {
      if (want.has(f.properties?.sifra) && f.geometry.type !== 'GeometryCollection') visit(f.geometry.coordinates)
    }
    if (w < e) m.fitBounds([w, s, e, n], { padding: 48, maxZoom: 9.5, duration: 600 })
  }, [ready, focusKey])

  const h = hover && grade(hover.unit.ocjena[year])
  const view = contextView(colorBy)
  const hoverSelected = hover != null && (selected ?? []).includes(hover.unit.sifra)
  return (
    <div className="relative h-full w-full overflow-hidden rounded-2xl border border-hairline bg-surface">
      <div ref={box} className="h-full w-full" aria-label="Karta ocjena općina i gradova" role="region" />
      {/* max width keeps the caption clear of the zoom buttons on narrow screens */}
      <div className="pointer-events-none absolute top-4 left-4 max-w-[calc(100%-5.5rem)] rounded-lg bg-card/90 px-3 py-2 shadow-sm backdrop-blur">
        <div className="text-sm font-semibold">{view ? view.label : 'Ocjena financijske održivosti proračuna'}, {year}.</div>
        <div className="text-xs text-muted">
          556 općina i gradova · prijeđi mišem, klikni za {selectable ? 'odabir' : 'pregled'}
        </div>
      </div>
      {!ready && (
        <div className="absolute inset-0 grid place-items-center text-sm text-muted">
          {failed ? 'Karta se nije učitala. Osvježi stranicu ili koristi pretragu.' : 'Učitavam kartu…'}
        </div>
      )}
      {hover && (
        <div
          className="pointer-events-none absolute z-10 rounded-xl border border-hairline bg-card/95 p-3 shadow-lg backdrop-blur"
          style={{ left: hover.left, top: hover.top, width: TOOLTIP_W }}
        >
          <div className="font-serif text-lg leading-tight font-semibold">{hover.unit.naziv}</div>
          <div className="mt-0.5 text-xs text-muted">
            {hover.unit.zupanija} · {num(hover.unit.stanovnici)} stanovnika
          </div>
          <div className="mt-2 flex items-center gap-2">
            {h ? <GradeChip g={h.value} /> : <span className="text-sm text-muted">nema podataka</span>}
            <span className="tabular text-sm text-ink-2">{num(hover.unit.bodovi[year], 1)} / 100 bodova</span>
          </div>
          {view && (
            <div className="mt-1.5 text-sm">
              <span className="text-muted">{view.short}: </span>
              <span className="tabular font-medium">{view.format(view.value(hover.unit, year))}</span>
            </div>
          )}
          <div className="mt-2 text-xs text-muted">
            {hint?.(hover.unit.sifra) ??
              (!selectable ? 'Klikni za pregled jedinice' : hoverSelected ? 'Klikni za uklanjanje iz odabira' : 'Klikni za odabir jedinice')}
          </div>
        </div>
      )}
    </div>
  )
}
