import { GRADES, grade, type LegendRow } from '../lib/format'

/** Grade as number + word, never colour alone. */
export function GradeChip({ g, size = 'sm' }: { g: number | null | undefined; size?: 'sm' | 'lg' }) {
  const m = grade(g)
  if (!m) return <span className="text-sm text-muted">nema ocjene</span>
  const big = size === 'lg'
  return (
    <span
      className={`inline-flex items-center rounded-full font-medium ${big ? 'gap-2.5 py-1.5 pr-4 pl-1.5 text-base' : 'gap-1.5 py-0.5 pr-2.5 pl-0.5 text-sm'}`}
      style={{ background: m.color, color: m.ink }}
    >
      <span
        className={`tabular grid place-items-center rounded-full bg-white/90 font-semibold text-ink ${big ? 'h-9 w-9 text-xl' : 'h-6 w-6 text-sm'}`}
      >
        {m.value}
      </span>
      {m.word}
    </span>
  )
}

/** Legend drawn on a map: a list inside the map's caption (from lg), or a wrapped strip under the
 *  map on phones, where a list over the map would cover half of Croatia. */
export function MapLegend({ rows, layout, label }: { rows: LegendRow[]; layout: 'list' | 'strip'; label: string }) {
  const label_ = (r: LegendRow) =>
    r.value != null ? (
      <>
        <span className="tabular font-semibold text-ink">{r.value}</span> {r.label}
      </>
    ) : (
      r.label
    )
  const swatch = (color: string) => (
    <span className="h-3 w-5 shrink-0 rounded-sm" style={{ background: color, boxShadow: 'inset 0 0 0 1px rgb(0 0 0 / 0.12)' }} aria-hidden />
  )
  if (layout === 'strip')
    return (
      <ul className="flex flex-wrap gap-x-3.5 gap-y-1 text-xs text-ink-2" aria-label={label}>
        {rows.map((r) => (
          <li key={r.key} className="flex items-center gap-1.5">
            {swatch(r.color)}
            <span>{label_(r)}</span>
            {r.n != null && <span className="tabular text-muted">{r.n}</span>}
          </li>
        ))}
      </ul>
    )
  return (
    <ul className="space-y-0.5 text-[13px] leading-5" aria-label={label}>
      {rows.map((r) => (
        <li key={r.key} className="flex items-center gap-2">
          {swatch(r.color)}
          <span className="flex-1 text-ink-2">{label_(r)}</span>
          {r.n != null && <span className="tabular pl-3 text-muted">{r.n}</span>}
        </li>
      ))}
    </ul>
  )
}

export { GRADES }
