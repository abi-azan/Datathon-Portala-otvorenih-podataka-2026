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

/** The unit's grade in every year as a row of squares, the shown year outlined. The number is in the
 *  square and the word in its title, so colour is never the only carrier; a year without a grade
 *  shows a dash. */
export function GradeHistory({ years, current, className = '' }: { years: [string, number | null | undefined][]; current: string; className?: string }) {
  if (years.length < 2) return null
  return (
    <div className={className}>
      <div className="text-xs text-muted">Ocjena po godinama</div>
      <ol className="mt-2 flex gap-1.5">
        {years.map(([y, g]) => {
          const m = grade(g)
          return (
            <li key={y} className="text-center" title={`${y}.: ${m ? `${m.value} (${m.word})` : 'nema ocjene'}`}>
              <span
                className={`tabular grid h-10 w-10 place-items-center rounded-lg text-base font-semibold ${
                  m ? '' : 'border border-hairline text-muted'
                } ${y === current ? 'ring-2 ring-ink ring-offset-2 ring-offset-page' : ''}`}
                style={m ? { background: m.color, color: m.ink } : undefined}
              >
                {m ? m.value : '–'}
              </span>
              <span className="sr-only">{m ? m.word : 'nema ocjene'}, </span>
              <span className="tabular mt-1.5 block text-[11px] text-muted">{y}.</span>
            </li>
          )
        })}
      </ol>
    </div>
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
