import * as maplibregl from 'maplibre-gl'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url'
import 'maplibre-gl/dist/maplibre-gl.css'
import { LoaderCircle } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { feature, merge } from 'topojson-client'
import type { GeometryCollection, MultiPolygon, Polygon, Topology } from 'topojson-specification'
import type { Feature, FeatureCollection, MultiPolygon as GeoMultiPolygon, Polygon as GeoPolygon, Position } from 'geojson'
import { ZAGREB_SIFRA as ZAGREB, topoUrl, type ReformUnit } from '../lib/data'
import { gradeRows, num } from '../lib/format'
import { GradeChip, MapLegend } from './Grade'
import { BASEMAP, BLANK, CROATIA, MIN_ZOOM, addOutsideVeil, fitPadding, gradeFill, quietBasemap, reducedMotion } from './mapStyle'

maplibregl.setWorkerUrl(workerUrl)

const reformKey = (u: ReformUnit) => u.clanice.join('-')
/** Croatian plural after a number: 1 jedinica, 2–4 jedinice, 5 jedinica (11–14 take the last form). */
const unitCount = (n: number) => {
  const [d, h] = [n % 10, n % 100]
  return `${n} ${d >= 2 && d <= 4 && (h < 12 || h > 14) ? 'jedinice' : 'jedinica'}`
}

interface Props {
  units: ReformUnit[]
  /** The threshold of `units`, which can lag the slider while the next file loads. */
  prag: number
  selected?: string
  onSelect?: (key: string) => void
  /** While set (the next threshold is loading or failed to load), the fill is faded and this line shown. */
  notice?: { text: string; loading: boolean }
}

interface Hover {
  left: number
  top: number
  key: string
}

const TOOLTIP_W = 260
const TOOLTIP_H = 120
const FULL = 0.94
const FADED = 0.45
// "only merged": the units that stay alone under the background colour, so they show as if filled at 0.15
const ALONE_VEIL = 0.84
// the units that changed with the threshold light up, then fade to their grade colour
const FLASH = '#ffc21a'
const FLASH_FILL = 0.5
const FLASH_IN_MS = 250
const FLASH_HOLD_MS = 450
const FLASH_OUT_MS = 1300
// a merged unit's outline, thicker when zoomed in, and thinner around a part that is small on screen
// (an islet would otherwise be all outline): at most an eighth of the part's width, at least 0.35 px.
// Each polygon of a merged unit is its own outline feature with s = √(area in km²); per zoom stop
// [zoom, full width in px, screen px per km at 44° N].
const MERGED_LINE = '#1d1c1a'
const MERGED_STOPS: [number, number, number][] = [
  [5.5, 1, 0.4],
  [7, 1.4, 1.14],
  [9, 2.2, 4.55],
  [11, 3, 18.2],
]
const mergedWidth = [
  'interpolate',
  ['linear'],
  ['zoom'],
  ...MERGED_STOPS.flatMap(([z, full, pxPerKm]) => [z, ['max', 0.35, ['min', full, ['*', ['get', 's'], pxPerKm / 8]]]]),
] as unknown as maplibregl.ExpressionSpecification

/** √ of a polygon's outer ring area in km² (equirectangular, good enough for a line width). */
function sideKm(ring: Position[]) {
  let a = 0
  let lat = 0
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    a += (ring[j][0] + ring[i][0]) * (ring[j][1] - ring[i][1])
    lat += ring[i][1]
  }
  const k = 111.32 // km per degree
  return Math.sqrt((Math.abs(a / 2) * k * k * Math.cos(((lat / ring.length) * Math.PI) / 180)))
}

function fillOpacity(m: maplibregl.Map, value: number, duration: number) {
  m.setPaintProperty('reform-fill', 'fill-opacity-transition', { duration, delay: 0 })
  m.setPaintProperty('reform-fill', 'fill-opacity', value)
}

function flash(m: maplibregl.Map, on: boolean, duration: number) {
  for (const [id, prop, value] of [
    ['reform-flash-fill', 'fill-opacity', FLASH_FILL],
    ['reform-flash-line', 'line-opacity', 1],
  ] as const) {
    m.setPaintProperty(id, `${prop}-transition`, { duration, delay: 0 })
    m.setPaintProperty(id, prop, on ? value : 0)
  }
}

/** Karta reforme: the units after the scenario, members' polygons dissolved into one per group
 *  on the client (topojson-client merge over geo/jls.topo.json), coloured by the grade after.
 *  It stays mounted across threshold changes, so the view (zoom, position) is kept. */
export function ReformMap({ units, prag, selected, onSelect, notice }: Props) {
  const box = useRef<HTMLDivElement>(null)
  const caption = useRef<HTMLDivElement>(null)
  const map = useRef<maplibregl.Map | null>(null)
  const topo = useRef<Topology | null>(null)
  const [ready, setReady] = useState(false)
  const [failed, setFailed] = useState(false)
  const [hover, setHover] = useState<Hover | null>(null)
  const [onlyMerged, setOnlyMerged] = useState(false)
  const byKey = useMemo(() => new Map(units.map((u) => [reformKey(u), u])), [units])
  const onSelectRef = useRef(onSelect)
  useEffect(() => {
    onSelectRef.current = onSelect
  }, [onSelect])
  // re-reads what is under the resting pointer, after new data is drawn (set by the map effect);
  // false while the map still draws the previous threshold's groups
  const rehover = useRef<() => boolean>(() => true)
  const keys = useRef(byKey)
  useEffect(() => {
    keys.current = byKey
  }, [byKey])
  const dim = !!notice
  const dimRef = useRef(dim)

  useEffect(() => {
    if (!box.current) return
    const m = new maplibregl.Map({
      container: box.current,
      style: BASEMAP,
      bounds: CROATIA,
      fitBoundsOptions: { padding: fitPadding(caption.current) },
      minZoom: MIN_ZOOM,
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
      addOutsideVeil(m, t, firstLabel)
      m.addSource('reform', { type: 'geojson', data: { type: 'FeatureCollection', features: [] }, promoteId: 'key' })
      m.addSource('reform-outline', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } })
      m.addSource('jls', { type: 'geojson', data: feature(t, t.objects.jls) as FeatureCollection })
      m.addSource('zup', { type: 'geojson', data: feature(t, t.objects.zupanije) as FeatureCollection })
      const none = ['==', ['get', 'key'], ''] as maplibregl.FilterSpecification
      m.addLayer({ id: 'reform-fill', type: 'fill', source: 'reform', paint: { 'fill-color': gradeFill(['get', 'g']), 'fill-opacity': FULL } }, firstLabel)
      m.addLayer(
        {
          id: 'reform-alone',
          type: 'fill',
          source: 'reform',
          filter: ['==', ['get', 'n'], 1],
          paint: { 'fill-color': '#fdfdfc', 'fill-antialias': false, 'fill-opacity': 0 },
        },
        firstLabel,
      )
      m.addLayer({ id: 'reform-flash-fill', type: 'fill', source: 'reform', filter: none, paint: { 'fill-color': FLASH, 'fill-opacity': 0 } }, firstLabel)
      // the old borders inside a merged unit, faint, so the members stay visible
      m.addLayer({ id: 'jls-line', type: 'line', source: 'jls', paint: { 'line-color': '#ffffff', 'line-width': 0.3, 'line-opacity': 0.5 } }, firstLabel)
      m.addLayer({ id: 'reform-line', type: 'line', source: 'reform', paint: { 'line-color': '#ffffff', 'line-width': 0.8 } }, firstLabel)
      m.addLayer({ id: 'zup-line', type: 'line', source: 'zup', paint: { 'line-color': '#52514e', 'line-width': 1, 'line-opacity': 0.7 } }, firstLabel)
      // the new borders: a dark outline around each merged unit, over the county lines
      m.addLayer(
        {
          id: 'reform-merged-line',
          type: 'line',
          source: 'reform-outline',
          layout: { 'line-join': 'round' },
          paint: { 'line-color': MERGED_LINE, 'line-width': mergedWidth, 'line-opacity': 0.9 },
        },
        firstLabel,
      )
      m.addLayer(
        {
          id: 'reform-flash-line',
          type: 'line',
          source: 'reform',
          filter: none,
          layout: { 'line-join': 'round' },
          paint: { 'line-color': FLASH, 'line-width': 3, 'line-opacity': 0 },
        },
        firstLabel,
      )
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
    let pointer: maplibregl.Point | null = null
    const show = (point: maplibregl.Point, key: string) => {
      if (hovered !== key) {
        if (hovered) m.setFeatureState({ source: 'reform', id: hovered }, { hover: false })
        hovered = key
        m.setFeatureState({ source: 'reform', id: key }, { hover: true })
      }
      m.getCanvas().style.cursor = key === ZAGREB ? '' : 'pointer'
      const { clientWidth: width, clientHeight: height } = m.getContainer()
      const left = point.x + 16 + TOOLTIP_W > width - 8 ? point.x - 16 - TOOLTIP_W : point.x + 16
      const top = point.y + TOOLTIP_H > height - 8 ? point.y - TOOLTIP_H - 12 : point.y - 12
      setHover({ left: Math.max(8, left), top: Math.max(8, top), key })
    }
    const hide = () => {
      if (hovered) m.setFeatureState({ source: 'reform', id: hovered }, { hover: false })
      hovered = null
      m.getCanvas().style.cursor = ''
      setHover(null)
    }
    m.on('mousemove', 'reform-fill', (e: maplibregl.MapLayerMouseEvent) => {
      const key = e.features?.[0]?.properties?.key as string | undefined
      if (key) show(e.point, key)
    })
    m.on('mouseleave', 'reform-fill', hide)
    // where the pointer rests on the map, also over the sea or while the groups are being redrawn
    m.on('mousemove', (e: maplibregl.MapMouseEvent) => {
      pointer = e.point
    })
    m.on('mouseout', () => {
      pointer = null
    })
    // the groups change under a pointer that has not moved (threshold changed by keyboard)
    rehover.current = () => {
      if (removed || !pointer || !m.getLayer('reform-fill')) return true
      const key = m.queryRenderedFeatures(pointer, { layers: ['reform-fill'] })[0]?.properties?.key as string | undefined
      if (key && key !== ZAGREB && !keys.current.has(key)) return false
      if (key) show(pointer, key)
      else hide()
      return true
    }
    m.on('click', 'reform-fill', (e: maplibregl.MapLayerMouseEvent) => {
      const key = e.features?.[0]?.properties?.key as string | undefined
      if (key && key !== ZAGREB) onSelectRef.current?.(key)
    })
    return () => {
      removed = true
      m.remove()
    }
  }, [])

  // fade the fill while the next threshold loads (declared before the data effect, which runs after it)
  useEffect(() => {
    dimRef.current = dim
    const m = map.current
    if (!ready || !m) return
    fillOpacity(m, dim ? FADED : FULL, reducedMotion() ? 0 : 250)
  }, [ready, dim])

  // dissolve each group's members into one shape whenever the threshold changes
  const drawn = useRef(false)
  const shownKeys = useRef(new Set<string>())
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
      features.push({ type: 'Feature', properties: { key: reformKey(u), g: u.ocjena ?? 0, n: u.clanice.length }, geometry: merge(t, parts) })
    }
    const zg = bySifra.get(ZAGREB)
    if (zg) features.push({ type: 'Feature', properties: { key: ZAGREB, g: 0, n: 1 }, geometry: merge(t, [zg]) })
    // a new threshold: drop the old colours to faded at once, then fade the new ones in once drawn
    const fade = drawn.current && !reducedMotion()
    // the units that did not exist at the previous threshold (new mergers, and members that split off)
    const keysNow = features.map((f) => f.properties!.key as string)
    const fresh = fade ? keysNow.filter((k) => k !== ZAGREB && !shownKeys.current.has(k)) : []
    shownKeys.current = new Set(keysNow)
    drawn.current = true
    if (fade) fillOpacity(m, FADED, 0)
    flash(m, false, 0)
    const freshFilter = ['in', ['get', 'key'], ['literal', fresh]] as maplibregl.FilterSpecification
    m.setFilter('reform-flash-fill', freshFilter)
    m.setFilter('reform-flash-line', freshFilter)
    let done = false
    let fadedIn = false
    let retry: ReturnType<typeof setTimeout> | undefined
    let flashOut: ReturnType<typeof setTimeout> | undefined
    const giveUp = Date.now() + 5000 // slow machines take seconds to redraw the tiles
    const settle = () => {
      if (done) return
      if (fade && !fadedIn) {
        fadedIn = true
        fillOpacity(m, dimRef.current ? FADED : FULL, 450)
        if (fresh.length) {
          flash(m, true, FLASH_IN_MS)
          flashOut = setTimeout(() => flash(m, false, FLASH_OUT_MS), FLASH_IN_MS + FLASH_HOLD_MS)
        }
      }
      clearTimeout(retry)
      // until the new groups are drawn under the pointer, the tooltip waits (a stale key shows none)
      if (!rehover.current() && Date.now() < giveUp) retry = setTimeout(settle, 150)
      else done = true
    }
    // the worker has the new groups ('content'), then their tiles are drawn ('idle')
    const onData = (e: maplibregl.MapSourceDataEvent) => {
      if (e.sourceId !== 'reform' || e.sourceDataType !== 'content') return
      m.off('sourcedata', onData)
      m.once('idle', settle)
    }
    m.on('sourcedata', onData)
    ;(m.getSource('reform') as maplibregl.GeoJSONSource).setData({ type: 'FeatureCollection', features })
    // the merged units' outlines, one feature per polygon, each with its own size
    const outlines: Feature[] = []
    for (const f of features) {
      if ((f.properties!.n as number) < 2) continue
      const g = f.geometry as GeoPolygon | GeoMultiPolygon
      for (const poly of g.type === 'Polygon' ? [g.coordinates] : g.coordinates)
        outlines.push({ type: 'Feature', properties: { s: sideKm(poly[0]) }, geometry: { type: 'Polygon', coordinates: poly } })
    }
    ;(m.getSource('reform-outline') as maplibregl.GeoJSONSource).setData({ type: 'FeatureCollection', features: outlines })
    const timer = setTimeout(settle, 1500) // in case no 'idle' follows
    return () => {
      done = true
      m.off('sourcedata', onData)
      m.off('idle', settle)
      clearTimeout(timer)
      clearTimeout(retry)
      clearTimeout(flashOut)
    }
  }, [ready, units])

  // "only merged": veil the units that stay alone
  useEffect(() => {
    const m = map.current
    if (!ready || !m) return
    m.setPaintProperty('reform-alone', 'fill-opacity-transition', { duration: reducedMotion() ? 0 : 300, delay: 0 })
    m.setPaintProperty('reform-alone', 'fill-opacity', onlyMerged ? ALONE_VEIL : 0)
  }, [ready, onlyMerged])

  useEffect(() => {
    const m = map.current
    if (!ready || !m) return
    m.setFilter('reform-selected', ['==', ['get', 'key'], selected ?? ''])
  }, [ready, selected])

  // a key from the previous threshold (until the pointer is re-read) shows no tooltip
  const h = hover ? byKey.get(hover.key) : undefined
  const tip = hover && (h || hover.key === ZAGREB) ? hover : null
  // no counts here: the panel next to the map shows them before and after
  const legend = gradeRows()
  return (
    <div className="flex h-full w-full flex-col overflow-hidden rounded-2xl border border-hairline bg-surface">
      <div className="relative min-h-0 flex-1">
        {/* the wrapper is absolute, not the map box: maplibre-gl.css sets the box to position: relative */}
        <div className="absolute inset-0">
          <div ref={box} className="h-full w-full" aria-label={`Karta reforme za prag od ${num(prag)} stanovnika`} role="region" />
        </div>
        {/* top left on phones (the fit leaves room under it), bottom left over the Italian coast from lg */}
        <div
          ref={caption}
          className="pointer-events-none absolute top-4 left-4 max-w-[calc(100%-5.5rem)] rounded-lg bg-card/90 px-3 py-2 shadow-sm backdrop-blur lg:top-auto lg:bottom-12"
        >
          <div className="text-sm font-semibold">Ocjena poslije reforme, prag {num(prag)} stanovnika</div>
          <div className="mt-2 mb-1.5 hidden lg:block">
            <MapLegend rows={legend} layout="list" label="Legenda ocjena poslije reforme" />
          </div>
          <div className="text-xs text-muted">tamni obrub: spojena jedinica · klikni za pojedinosti</div>
          <button
            type="button"
            role="switch"
            aria-checked={onlyMerged}
            disabled={!ready}
            onClick={() => setOnlyMerged((v) => !v)}
            className="pointer-events-auto mt-1.5 -ml-1 flex items-center gap-2 rounded-md px-1 py-0.5 text-xs font-medium text-ink-2 hover:text-ink disabled:opacity-50"
          >
            <span
              aria-hidden
              className={`relative h-3.5 w-6 shrink-0 rounded-full transition-colors motion-reduce:transition-none ${onlyMerged ? 'bg-ink' : 'bg-axis'}`}
            >
              <span
                className={`absolute top-0.5 left-0.5 h-2.5 w-2.5 rounded-full bg-card shadow-sm transition-transform motion-reduce:transition-none ${onlyMerged ? 'translate-x-2.5' : ''}`}
              />
            </span>
            Prikaži samo spojene
          </button>
          {notice && (
            <div className="mt-1 flex items-center gap-1.5 text-xs font-medium text-ink-2">
              {notice.loading && <LoaderCircle className="h-3.5 w-3.5 animate-spin" aria-hidden />}
              {notice.text}
            </div>
          )}
        </div>
        {!ready && (
          <div className="absolute inset-0 grid place-items-center text-sm text-muted">
            {failed ? 'Karta se nije učitala. Osvježi stranicu.' : 'Učitavam kartu…'}
          </div>
        )}
        {tip && (
          <div
            className="pointer-events-none absolute z-10 rounded-xl border border-hairline bg-card/95 p-3 shadow-lg backdrop-blur"
            style={{ left: tip.left, top: tip.top, width: TOOLTIP_W }}
          >
            {h ? (
              <>
                <div className="font-serif text-lg leading-tight font-semibold">{h.naziv}</div>
                <div className="mt-0.5 text-xs text-muted">
                  {h.clanice.length > 1 ? `${unitCount(h.clanice.length)} · ` : 'bez spajanja · '}
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
      <div className="border-t border-hairline bg-card px-3 py-2 lg:hidden">
        <MapLegend rows={legend} layout="strip" label="Legenda ocjena poslije reforme" />
      </div>
    </div>
  )
}
