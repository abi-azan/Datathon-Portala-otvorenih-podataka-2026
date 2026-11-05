// The map's three views (PLAN §6 MUST 2): the grade, and two context measures that are shown but
// not scored (PLAN §3.4). The context views use quintiles over the 556 towns and municipalities of
// the selected year, on one sequential hue that is not the grade palette, so "more" never reads as
// "better" or "worse".
import type { UnitIndex } from './data'
import { eur, num, pct } from './format'

export type ViewKey = 'ocjena' | 'uprava_pc' | 'udio_tekucih_pomoci'

// Violet, light -> dark; checked with the dataviz validator (ordinal mode, light surface): monotone
// lightness, visible step gaps, light end 2.15:1 against the map surface.
export const SEQUENTIAL = ['#b0a6ec', '#8f82e1', '#6f5fd8', '#4f3fbd', '#30227a']

export interface ContextView {
  key: Exclude<ViewKey, 'ocjena'>
  label: string
  short: string
  value: (u: UnitIndex, year: string) => number | null
  format: (v: number | null) => string
  /** Legend label of a class, with the unit written once. */
  range: (from: number, to: number) => string
}

export const CONTEXT_VIEWS: ContextView[] = [
  {
    key: 'uprava_pc',
    label: 'Trošak opće uprave po stanovniku',
    short: 'Trošak uprave',
    value: (u, y) => u.uprava_pc_po_godini?.[y] ?? null,
    format: (v) => (v == null ? '–' : `${eur(v)} po stanovniku`),
    range: (a, b) => `${num(a)} – ${num(b)} € po stanovniku`,
  },
  {
    key: 'udio_tekucih_pomoci',
    label: 'Pomoći u tekućim prihodima',
    short: 'Pomoći u prihodima',
    value: (u, y) => u.udio_tekucih_pomoci_po_godini?.[y] ?? null,
    format: (v) => pct(v),
    range: (a, b) => `${num(a * 100, 1)} – ${num(b * 100, 1)} %`,
  },
]

export const contextView = (key: ViewKey) => CONTEXT_VIEWS.find((v) => v.key === key)

/** Four cut points (quintiles) of a view over the towns and municipalities in a year. */
export function quintiles(units: UnitIndex[], view: ContextView, year: string): number[] {
  const xs = units
    .filter((u) => u.vrsta !== 'zupanija')
    .map((u) => view.value(u, year))
    .filter((v): v is number => v != null && Number.isFinite(v))
    .sort((a, b) => a - b)
  if (!xs.length) return []
  return [0.2, 0.4, 0.6, 0.8].map((q) => xs[Math.min(xs.length - 1, Math.floor(q * xs.length))])
}

/** Class 1-5 of a value against the cut points; 0 when there is no value. */
export function classOf(v: number | null, cuts: number[]): number {
  if (v == null || !Number.isFinite(v) || !cuts.length) return 0
  return 1 + cuts.filter((c) => v >= c).length
}
