import { useState } from 'react'
import { GRADES, num } from '../lib/format'

interface Point {
  year: string
  value: number | null
  median: number | null
  grade: number | null
}

const W = 640
const H = 240
const PAD = { l: 36, r: 128, t: 14, b: 28 } // r: room for the longest band label, "3 · umjereno stabilno"
// grade bands on the 0-100 points scale (PLAN §3.2)
const BANDS = [
  { g: 5, lo: 80, hi: 100 },
  { g: 4, lo: 60, hi: 80 },
  { g: 3, lo: 40, hi: 60 },
  { g: 2, lo: 20, hi: 40 },
  { g: 1, lo: 0, hi: 20 },
]

/** Points 2019-2025 for the unit (solid) and the median of similar units (dashed). */
export function TrendChart({ points, groupName }: { points: Point[]; groupName: string }) {
  const [hover, setHover] = useState<number | null>(null)
  const x = (i: number) => PAD.l + (i * (W - PAD.l - PAD.r)) / Math.max(points.length - 1, 1)
  const y = (v: number) => PAD.t + ((100 - v) * (H - PAD.t - PAD.b)) / 100
  const path = (key: 'value' | 'median') =>
    points
      .map((p, i) => (p[key] == null ? null : `${x(i)},${y(p[key] as number)}`))
      .filter(Boolean)
      .join(' L ')
  const hp = hover != null ? points[hover] : null

  return (
    <div className="relative">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full overflow-visible" role="img" aria-label={`Bodovi po godinama i medijan usporedne skupine ${groupName}`}>
        {BANDS.map((b) => {
          const meta = GRADES.find((g) => g.value === b.g)!
          return (
            <g key={b.g}>
              <rect x={PAD.l} y={y(b.hi)} width={W - PAD.l - PAD.r} height={y(b.lo) - y(b.hi)} fill={meta.color} opacity={0.13} />
              <text x={W - PAD.r + 8} y={(y(b.hi) + y(b.lo)) / 2 + 3.5} textAnchor="start" className="fill-[#6f6d68] text-[10px]">
                {b.g} · {meta.word}
              </text>
            </g>
          )
        })}
        {[0, 20, 40, 60, 80, 100].map((v) => (
          <g key={v}>
            <line x1={PAD.l} x2={W - PAD.r} y1={y(v)} y2={y(v)} stroke="#e1e0d9" strokeWidth={1} />
            <text x={PAD.l - 8} y={y(v) + 3.5} textAnchor="end" className="tabular fill-[#6f6d68] text-[10px]">
              {v}
            </text>
          </g>
        ))}
        {points.map((p, i) => (
          <text key={p.year} x={x(i)} y={H - 8} textAnchor="middle" className="tabular fill-[#6f6d68] text-[10px]">
            {p.year}
          </text>
        ))}
        <path d={`M ${path('median')}`} fill="none" stroke="#898781" strokeWidth={2} strokeDasharray="5 4" />
        <path d={`M ${path('value')}`} fill="none" stroke="#0b0b0b" strokeWidth={2} />
        {points.map((p, i) =>
          p.value == null ? null : (
            <circle key={p.year} cx={x(i)} cy={y(p.value)} r={hover === i ? 6 : 4.5} fill="#0b0b0b" stroke="#fcfcfb" strokeWidth={2} />
          ),
        )}
        {/* each year's points written on the chart, so reading them does not need a hover */}
        {points.map((p, i) =>
          p.value == null ? null : (
            <text
              key={p.year}
              x={x(i)}
              y={y(p.value) < PAD.t + 16 ? y(p.value) + 19 : y(p.value) - 10}
              textAnchor="middle"
              stroke="#fcfcfb"
              strokeWidth={3}
              style={{ paintOrder: 'stroke' }}
              className="tabular fill-[#0b0b0b] text-[11px] font-semibold"
            >
              {num(p.value, 0)}
            </text>
          ),
        )}
        {hover != null && <line x1={x(hover)} x2={x(hover)} y1={PAD.t} y2={H - PAD.b} stroke="#0b0b0b" strokeOpacity={0.25} />}
        {points.map((p, i) => (
          <rect
            key={p.year}
            x={x(i) - (W - PAD.l - PAD.r) / (2 * Math.max(points.length - 1, 1))}
            y={0}
            width={(W - PAD.l - PAD.r) / Math.max(points.length - 1, 1)}
            height={H}
            fill="transparent"
            onMouseEnter={() => setHover(i)}
            onMouseLeave={() => setHover(null)}
            // touch screens have no hover: a tap shows the year's details, a second tap hides them
            onClick={() => setHover((h) => (h === i ? null : i))}
          />
        ))}
      </svg>
      {hp && hover != null && (
        <div
          className="pointer-events-none absolute top-2 rounded-lg border border-hairline bg-card px-3 py-2 text-xs shadow-md"
          style={{ left: `calc(${(x(hover) / W) * 100}% ${hover > points.length / 2 ? '- 170px' : '+ 12px'})` }}
        >
          <div className="font-semibold">{hp.year}.</div>
          <div className="tabular">
            Bodovi: <strong>{num(hp.value, 1)}</strong> {hp.grade ? `(ocjena ${hp.grade})` : ''}
          </div>
          <div className="tabular text-muted">Medijan usporedne skupine: {num(hp.median, 1)}</div>
        </div>
      )}
      <div className="mt-2 flex flex-wrap gap-5 text-xs text-ink-2">
        <span className="flex items-center gap-2">
          <svg width="22" height="8" aria-hidden>
            <line x1="0" x2="22" y1="4" y2="4" stroke="#0b0b0b" strokeWidth="2" />
          </svg>
          Ova jedinica
        </span>
        <span className="flex items-center gap-2">
          <svg width="22" height="8" aria-hidden>
            <line x1="0" x2="22" y1="4" y2="4" stroke="#898781" strokeWidth="2" strokeDasharray="5 4" />
          </svg>
          Medijan usporedne skupine „{groupName}”
        </span>
      </div>
    </div>
  )
}
