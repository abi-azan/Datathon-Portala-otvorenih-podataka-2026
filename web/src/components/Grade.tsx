import { GRADES, grade } from '../lib/format'

/** Grade as number + word, never colour alone. */
export function GradeChip({ g, size = 'sm' }: { g: number | null | undefined; size?: 'sm' | 'lg' }) {
  const m = grade(g)
  if (!m) return <span className="text-sm text-muted">nema ocjene</span>
  const big = size === 'lg'
  return (
    <span
      className={`inline-flex items-center rounded-full font-medium ${big ? 'gap-2.5 py-1.5 pr-4 pl-1.5 text-base' : 'gap-1.5 py-0.5 pr-2.5 pl-0.5 text-sm'}`}
      style={{ background: m.color, color: m.ink, boxShadow: m.value === 3 ? 'inset 0 0 0 1px #c3c2b7' : undefined }}
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

/** Legend for the map: every grade with its word and how many units have it. */
export function GradeLegend({ counts }: { counts: Record<number, number> }) {
  const total = Object.values(counts).reduce((a, b) => a + b, 0)
  return (
    <ul className="space-y-1" aria-label="Legenda ocjena">
      {GRADES.map((g) => (
        <li key={g.value} className="flex items-center gap-3 text-sm">
          <span
            className="h-3.5 w-7 shrink-0 rounded"
            style={{ background: g.color, boxShadow: 'inset 0 0 0 1px rgb(0 0 0 / 0.12)' }}
            aria-hidden
          />
          <span className="tabular w-3 font-semibold">{g.value}</span>
          <span className="flex-1 text-ink-2">{g.word}</span>
          <span className="tabular text-muted">{counts[g.value] ?? 0}</span>
          <span className="relative h-1.5 w-16 overflow-hidden rounded-full bg-hairline" aria-hidden>
            <span
              className="absolute inset-y-0 left-0 rounded-full bg-ink-2"
              style={{ width: `${total ? ((counts[g.value] ?? 0) / total) * 100 : 0}%` }}
            />
          </span>
        </li>
      ))}
    </ul>
  )
}

export { GRADES }
