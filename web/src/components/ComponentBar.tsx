import { grade, gradeOfPoints, num } from '../lib/format'

/** A component's 0-100 points as a bar in the colour of the grade those points fall in, with the
 *  peer-group median as a dark mark across it. The median is also written next to the points, so
 *  the comparison never depends on hovering. */
export function ComponentBar({ name, score, peer, thin = false }: { name: string; score: number | null; peer?: number | null; thin?: boolean }) {
  const band = score == null ? undefined : grade(gradeOfPoints(score))
  return (
    <div
      className={`relative ${thin ? 'mt-1.5' : 'mt-2'}`}
      role="img"
      aria-label={`${name}: ${num(score, 0)} od 100 bodova${peer != null ? `, medijan usporedne skupine ${num(peer, 0)}` : ''}`}
    >
      <div className={`${thin ? 'h-2' : 'h-2.5'} overflow-hidden rounded-full bg-hairline/70`}>
        <div
          className="h-full rounded-full"
          style={{
            width: `${score ?? 0}%`,
            background: band?.color,
          }}
        />
      </div>
      {peer != null && (
        <span
          className="absolute -top-1 -bottom-1 w-0.5 rounded-full bg-ink"
          style={{ left: `calc(${Math.min(100, Math.max(0, peer))}% - 1px)` }}
          aria-hidden
        />
      )}
    </div>
  )
}

/** Points with the peer median after them, for the right end of a component's heading. */
export function ComponentPoints({ score, peer }: { score: number | null; peer?: number | null }) {
  return (
    <span className="shrink-0 text-sm">
      <span className="tabular font-semibold">{num(score, 0)}</span>
      {peer != null && <span className="tabular text-xs text-muted"> · medijan {num(peer, 0)}</span>}
    </span>
  )
}

/** The key for the median mark, under a card's heading. */
export function MedianKey() {
  return (
    <p className="mt-2 flex items-center gap-1.5 text-xs text-muted">
      <span className="h-3.5 w-0.5 rounded-full bg-ink" aria-hidden />
      crtica: medijan usporedne skupine
    </p>
  )
}
