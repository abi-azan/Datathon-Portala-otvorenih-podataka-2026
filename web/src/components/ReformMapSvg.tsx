import { LoaderCircle } from 'lucide-react'
import { useMemo, useState } from 'react'
import { merge, mesh } from 'topojson-client'
import type { GeometryCollection, MultiPolygon, Polygon } from 'topojson-specification'
import { ZAGREB_SIFRA as ZAGREB, type ReformUnit } from '../lib/data'
import { grade, gradeRows, num } from '../lib/format'
import { pathOf } from '../lib/geo'
import { useTopology } from '../lib/topology'
import { GradeChip, MapLegend } from './Grade'
import { SVG_MAP_NOTE } from './GradeMapSvg'
import type { ReformMapProps } from './ReformMap'
import { SvgMap, type SvgArea, type SvgLine } from './SvgMap'

const reformKey = (u: ReformUnit) => u.clanice.join('-')
/** Croatian plural after a number: 1 jedinica, 2–4 jedinice, 5 jedinica (11–14 take the last form). */
const unitCount = (n: number) => {
  const [d, h] = [n % 10, n % 100]
  return `${n} ${d >= 2 && d <= 4 && (h < 12 || h > 14) ? 'jedinice' : 'jedinica'}`
}

const FADED = 0.45 // while the next threshold loads
const ALONE = 0.15 // "only merged": the units that stay alone
const NO_DATA = '#ffffff'

/** ReformMap without WebGL: the same props, the groups dissolved with topojson merge and drawn as SVG
 *  (components/SvgMap). The flash of newly merged units is left out. */
export function ReformMapSvg({ units, prag, selected, onSelect, notice }: ReformMapProps) {
  const { topo, failed } = useTopology()
  const [onlyMerged, setOnlyMerged] = useState(false)
  const byKey = useMemo(() => new Map(units.map((u) => [reformKey(u), u])), [units])

  // borders that do not change with the threshold
  const base = useMemo(() => {
    if (!topo) return null
    return {
      old: pathOf(mesh(topo, topo.objects.jls as GeometryCollection)),
      counties: pathOf(mesh(topo, topo.objects.zupanije as GeometryCollection)),
    }
  }, [topo])

  // each group's members dissolved into one shape
  const groups = useMemo(() => {
    if (!topo) return []
    const geoms = (topo.objects.jls as GeometryCollection<{ sifra: string }>).geometries
    const bySifra = new Map(geoms.map((g) => [(g.properties as { sifra: string }).sifra, g as Polygon | MultiPolygon]))
    const out: { key: string; d: string; n: number; g: number | null }[] = []
    for (const u of units) {
      const parts = u.clanice.map((s) => bySifra.get(s)).filter((g): g is Polygon | MultiPolygon => !!g)
      if (parts.length) out.push({ key: reformKey(u), d: pathOf(merge(topo, parts)), n: u.clanice.length, g: u.ocjena })
    }
    const zg = bySifra.get(ZAGREB)
    if (zg) out.push({ key: ZAGREB, d: pathOf(merge(topo, [zg])), n: 1, g: null })
    return out
  }, [topo, units])

  const dim = !!notice
  const areas = useMemo<SvgArea[]>(
    () =>
      groups.map((x) => ({
        key: x.key,
        d: x.d,
        fill: grade(x.g)?.color ?? NO_DATA,
        opacity: dim ? FADED : onlyMerged && x.n === 1 ? ALONE : 1,
      })),
    [groups, dim, onlyMerged],
  )
  const lines = useMemo<SvgLine[]>(() => {
    if (!base) return []
    const open = groups.find((x) => x.key === selected)
    return [
      // the old borders inside a merged unit, faint, so the members stay visible
      { key: 'stare-granice', d: base.old, stroke: '#ffffff', width: 0.4, opacity: 0.5 },
      { key: 'zupanije', d: base.counties, stroke: '#52514e', width: 1, opacity: 0.7 },
      // the new borders: a dark outline around each merged unit
      ...groups.filter((x) => x.n > 1).map((x) => ({ key: `spojena-${x.key}`, d: x.d, stroke: '#1d1c1a', width: 1.4, opacity: 0.9 })),
      // the open group: a black line on a white one, so it also stands out on the dark green of grade 5
      ...(open
        ? [
            { key: 'odabrana-podloga', d: open.d, stroke: '#ffffff', width: 7 },
            { key: 'odabrana', d: open.d, stroke: '#0b0b0b', width: 3.5 },
          ]
        : []),
    ]
  }, [base, groups, selected])

  const tooltip = (key: string) => {
    if (key === ZAGREB) return <div className="text-sm">Grad Zagreb nije uključen u scenarij.</div>
    const h = byKey.get(key)
    if (!h) return null
    return (
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
    )
  }

  const legend = gradeRows()
  return (
    <div className="flex h-full w-full flex-col overflow-hidden rounded-2xl border border-hairline bg-surface">
      <div className="border-b border-hairline bg-card px-3 py-2">
        <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1">
          <div className="text-sm font-semibold">Ocjena poslije reforme, prag {num(prag)} stanovnika</div>
          <button
            type="button"
            role="switch"
            aria-checked={onlyMerged}
            disabled={!topo}
            onClick={() => setOnlyMerged((v) => !v)}
            className="-ml-1 flex items-center gap-2 rounded-md px-1 py-0.5 text-xs font-medium text-ink-2 hover:text-ink disabled:opacity-50"
          >
            <span aria-hidden className={`relative h-3.5 w-6 shrink-0 rounded-full transition-colors motion-reduce:transition-none ${onlyMerged ? 'bg-ink' : 'bg-axis'}`}>
              <span
                className={`absolute top-0.5 left-0.5 h-2.5 w-2.5 rounded-full bg-card shadow-sm transition-transform motion-reduce:transition-none ${onlyMerged ? 'translate-x-2.5' : ''}`}
              />
            </span>
            Prikaži samo spojene
          </button>
        </div>
        <div className="text-xs text-muted">tamni obrub: spojena jedinica · klikni za pojedinosti</div>
        <div className="mt-0.5 text-xs text-muted">{SVG_MAP_NOTE}</div>
        {notice && (
          <div className="mt-1 flex items-center gap-1.5 text-xs font-medium text-ink-2">
            {notice.loading && <LoaderCircle className="h-3.5 w-3.5 animate-spin" aria-hidden />}
            {notice.text}
          </div>
        )}
      </div>
      <div className="relative min-h-0 flex-1">
        {topo ? (
          <SvgMap
            areas={areas}
            lines={lines}
            label={`Karta reforme za prag od ${num(prag)} stanovnika`}
            tooltip={tooltip}
            clickable={(key) => key !== ZAGREB}
            onClick={(key) => onSelect?.(key)}
            tooltipWidth={260}
            tooltipHeight={120}
          />
        ) : (
          <div className="absolute inset-0 grid place-items-center px-6 text-center text-sm text-muted">
            {failed ? 'Karta se nije učitala. Osvježi stranicu.' : 'Učitavam kartu…'}
          </div>
        )}
      </div>
      <div className="border-t border-hairline bg-card px-3 py-2">
        <MapLegend rows={legend} layout="strip" label="Legenda ocjena poslije reforme" />
      </div>
    </div>
  )
}
