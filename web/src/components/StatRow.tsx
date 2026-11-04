import type { ReactNode } from 'react'

/** One line of a profile card: label (with an optional hint), the value and the peer-group median. */
export function StatRow({ label, value, median, hint }: { label: string; value: ReactNode; median?: string; hint?: ReactNode }) {
  return (
    <div className="flex items-baseline justify-between gap-4 border-b border-hairline pb-2 last:border-0 last:pb-0">
      <dt className="text-ink-2">
        {label}
        {hint && <span className="mt-0.5 block text-xs text-muted">{hint}</span>}
      </dt>
      <dd className="tabular shrink-0 text-right">
        <span className="font-medium whitespace-nowrap">{value}</span>
        {median && (
          <div className="text-xs whitespace-nowrap text-muted">
            medijan <span className="hidden sm:inline">usporedne skupine </span>
            {median}
          </div>
        )}
      </dd>
    </div>
  )
}
