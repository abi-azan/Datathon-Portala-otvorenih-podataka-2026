import { useMemo } from 'react'
import { feature, mesh } from 'topojson-client'
import type { GeometryCollection } from 'topojson-specification'
import type { FeatureCollection, MultiPolygon, Polygon } from 'geojson'
import { boxOf, pathOf, union, type Box } from '../lib/geo'
import { grade, num } from '../lib/format'
import { go, unitHref } from '../lib/router'
import { useTopology } from '../lib/topology'
import { SEQUENTIAL, classOf, contextView, legendRows, quintiles } from '../lib/views'
import { GradeChip, MapLegend } from './Grade'
import type { GradeMapProps } from './GradeMap'
import { SvgMap, type SvgArea, type SvgLine } from './SvgMap'

const DIM = 0.22
const NO_DATA = '#ffffff'

/** What the SVG maps say about themselves, so a visitor knows why there is no basemap. */
export const SVG_MAP_NOTE = 'Pojednostavljeni prikaz karte, jer ovaj preglednik ne podržava WebGL.'

/** GradeMap without WebGL: the same props and the same colours, drawn as SVG (components/SvgMap).
 *  Used where the browser gives no WebGL 2 context, and when the MapLibre map fails while drawing. */
export function GradeMapSvg({ units, year, colorBy = 'ocjena', selectable = false, selected, onSelect, dimmed, hint, focus, legendCounts = true }: GradeMapProps) {
  const { topo, failed } = useTopology()
  const shapes = useMemo(() => {
    if (!topo) return null
    const jls = feature(topo, topo.objects.jls) as FeatureCollection<Polygon | MultiPolygon, { sifra: string; slug: string }>
    return {
      units: jls.features.map((f) => ({ sifra: f.properties.sifra, slug: f.properties.slug, d: pathOf(f.geometry), box: boxOf(f.geometry) })),
      counties: pathOf(mesh(topo, topo.objects.zupanije as GeometryCollection)),
    }
  }, [topo])
  const bySifra = useMemo(() => new Map(units.map((u) => [u.sifra, u])), [units])
  const view = contextView(colorBy)

  const areas = useMemo<SvgArea[]>(() => {
    if (!shapes) return []
    const cuts = view ? quintiles(units, view, year) : []
    const faded = new Set(dimmed ?? [])
    return shapes.units.map((s) => {
      const u = bySifra.get(s.sifra)
      const fill = !u
        ? NO_DATA
        : view
          ? (SEQUENTIAL[classOf(view.value(u, year), cuts) - 1] ?? NO_DATA)
          : (grade(u.ocjena[year])?.color ?? NO_DATA)
      return { key: s.sifra, d: s.d, fill, opacity: faded.has(s.sifra) ? DIM : 1 }
    })
  }, [shapes, units, bySifra, view, year, dimmed])

  const lines = useMemo<SvgLine[]>(() => {
    if (!shapes) return []
    const picked = new Set(selected ?? [])
    return [
      { key: 'zupanije', d: shapes.counties, stroke: '#52514e', width: 1, opacity: 0.7 },
      ...shapes.units.filter((s) => picked.has(s.sifra)).map((s) => ({ key: `odabrana-${s.sifra}`, d: s.d, stroke: '#0b0b0b', width: 3.5 })),
    ]
  }, [shapes, selected])

  // the box of the focus units (the county of the selection in the simulator)
  const focusKey = (focus ?? []).join(',')
  const focusBox = useMemo<Box | null>(() => {
    if (!shapes || !focusKey) return null
    const want = new Set(focusKey.split(','))
    return union(shapes.units.filter((s) => want.has(s.sifra)).map((s) => s.box))
  }, [shapes, focusKey])

  const legend = useMemo(() => legendRows(units, year, colorBy, legendCounts), [units, year, colorBy, legendCounts])
  const slugOf = useMemo(() => new Map((shapes?.units ?? []).map((s) => [s.sifra, s.slug])), [shapes])

  const tooltip = (sifra: string) => {
    const u = bySifra.get(sifra)
    if (!u) return null
    const g = grade(u.ocjena[year])
    const isSelected = (selected ?? []).includes(sifra)
    return (
      <>
        <div className="font-serif text-lg leading-tight font-semibold">{u.naziv}</div>
        <div className="mt-0.5 text-xs text-muted">
          {u.zupanija} · {num(u.stanovnici)} stanovnika
        </div>
        <div className="mt-2 flex items-center gap-2">
          {g ? <GradeChip g={g.value} /> : <span className="text-sm text-muted">nema podataka</span>}
          <span className="tabular text-sm text-ink-2">{num(u.bodovi[year], 1)} / 100 bodova</span>
        </div>
        {view && (
          <div className="mt-1.5 text-sm">
            <span className="text-muted">{view.short}: </span>
            <span className="tabular font-medium">{view.format(view.value(u, year))}</span>
          </div>
        )}
        <div className="mt-2 text-xs text-muted">
          {hint?.(sifra) ?? (!selectable ? 'Klikni za pregled jedinice' : isSelected ? 'Klikni za uklanjanje iz odabira' : 'Klikni za odabir jedinice')}
        </div>
      </>
    )
  }
  const onClick = (sifra: string) => {
    if (selectable) return onSelect?.(sifra)
    const slug = slugOf.get(sifra)
    if (slug) go(unitHref(slug))
  }

  const title = view ? view.label : 'Ocjena financijske održivosti proračuna'
  return (
    <div className="flex h-full w-full flex-col overflow-hidden rounded-2xl border border-hairline bg-surface">
      <div className="border-b border-hairline bg-card px-3 py-2">
        <div className="text-sm font-semibold">
          {title}, {year}.
        </div>
        <div className="text-xs text-muted">
          {view ? 'Ne ulazi u ocjenu · tamnije = veća vrijednost' : '556 općina i gradova'} · klikni jedinicu za {selectable ? 'odabir' : 'pregled'}
        </div>
        <div className="mt-0.5 text-xs text-muted">{SVG_MAP_NOTE}</div>
      </div>
      <div className="relative min-h-0 flex-1">
        {shapes ? (
          <SvgMap
            areas={areas}
            lines={lines}
            focus={focusBox}
            label={`Karta općina i gradova: ${title.toLowerCase()}, ${year}.`}
            tooltip={tooltip}
            onClick={onClick}
          />
        ) : (
          <div className="absolute inset-0 grid place-items-center px-6 text-center text-sm text-muted">
            {failed ? 'Karta se nije učitala. Osvježi stranicu ili koristi pretragu.' : 'Učitavam kartu…'}
          </div>
        )}
      </div>
      {legend.length > 0 && (
        <div className="border-t border-hairline bg-card px-3 py-2">
          <MapLegend rows={legend} layout="strip" label={view ? `Legenda: ${view.label}, ${year}.` : `Legenda ocjena, ${year}.`} />
        </div>
      )}
    </div>
  )
}
