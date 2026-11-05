// Live call to the DZS PxWeb API for a unit's population series (SP31_2, json-stat2).
//
// The profile JSON carries the exact request (pipeline/kontekst.py live_query): POST the query to the
// table URL. DZS sends Access-Control-Allow-Origin: *, and Content-Type text/plain keeps it a simple
// request without a preflight. DZS answers HTTP 429 after about ten quick calls, so every answer is
// kept in sessionStorage, a 429 pauses live calls for a while, and a call that takes longer than
// TIMEOUT_MS is dropped. In every failing case the caller keeps the static copy from the profile JSON.
//
// The static copy may hold years PxWeb does not have yet (pipeline/dzs_xlsx.py: 2025 from the DZS
// publication "Gradovi i općine u statistici" until PxWeb gets it on 30.11.2026). mergeSeries() joins the
// two per year, so a live answer that ends earlier never hides those years, and a live year always wins.
import type { DzsSource, LiveQuery } from './data'

export const PUBLICATION = 'Gradovi i općine u statistici'

export interface LiveSeries {
  /** value by year, e.g. {"2021": 3156, ...}; null where DZS has no number */
  values: Record<string, number | null>
  /** when DZS answered (ISO time) */
  fetched: string
}

const TIMEOUT_MS = 3000
const PAUSE_AFTER_429_MS = 60_000
const PAUSE_KEY = 'dzs:pauza'
const YEAR = 'Godina'

// v2: answers are kept only after the unit's name in them was checked (parseSeries)
const key = (q: LiveQuery) => `dzs:v2:${q.tablica}:${q.kod}`
const inFlight = new Map<string, Promise<LiveSeries | null>>()

function read<T>(k: string): T | null {
  try {
    const s = sessionStorage.getItem(k)
    return s ? (JSON.parse(s) as T) : null
  } catch {
    return null
  }
}

function write(k: string, v: unknown) {
  try {
    sessionStorage.setItem(k, JSON.stringify(v))
  } catch {
    // private mode or full storage: the series is just fetched again next time
  }
}

interface JsonStatCategory {
  index: Record<string, number> | string[]
  label?: Record<string, string>
}
interface JsonStat {
  id: string[]
  size: number[]
  dimension: Record<string, { category: JsonStatCategory }>
  value: (number | null)[] | Record<string, number | null>
}

const positions = (c: JsonStatCategory): [string, number][] =>
  Array.isArray(c.index) ? c.index.map((code, i) => [code, i]) : Object.entries(c.index)

const plain = (s: string) => s.normalize('NFC').replace(/\s+/g, ' ').trim().toLocaleUpperCase('hr')

/** The query variable that selects the unit (its selection is exactly [q.kod]). */
const areaVariable = (q: LiveQuery) =>
  (q.upit.query as { code?: string; selection?: { values?: unknown[] } }[]).find(
    (x) => x.selection?.values?.length === 1 && x.selection.values[0] === q.kod,
  )?.code

/** Values by year from a json-stat2 answer for one unit; null when the answer is not that series.
 * The area dimension must hold only the unit's code, and DZS's label for that code must be the name
 * the profile expects (q.naziv, from the table's metadata at build time): if DZS renumbers its rows,
 * the code would point to another unit, and its numbers must not be shown under this one's name. */
export function parseSeries(js: JsonStat, q: LiveQuery): Record<string, number | null> | null {
  if (!js || !Array.isArray(js.id) || !Array.isArray(js.size) || !js.dimension) return null
  const yearAt = js.id.indexOf(YEAR)
  if (yearAt < 0 || !js.dimension[YEAR]) return null
  // every dimension except the year must hold a single value, and the area must be the unit asked for
  if (js.size.some((n, i) => i !== yearAt && n !== 1)) return null
  const areaId = areaVariable(q)
  const area = areaId ? js.dimension[areaId] : undefined
  if (!area || js.id.indexOf(areaId as string) < 0) return null
  const codes = positions(area.category)
  if (codes.length !== 1 || codes[0][0] !== q.kod) return null
  if (q.naziv != null) {
    const label = area.category.label?.[q.kod]
    if (label == null || plain(label) !== plain(q.naziv)) return null
  }
  const cat = js.dimension[YEAR].category
  const out: Record<string, number | null> = {}
  for (const [code, pos] of positions(cat)) {
    const year = cat.label?.[code] ?? code
    const v = Array.isArray(js.value) ? js.value[pos] : js.value?.[String(pos)]
    if (/^\d{4}$/.test(year)) out[year] = typeof v === 'number' ? v : null
  }
  return Object.keys(out).length ? out : null
}

async function call(q: LiveQuery): Promise<LiveSeries | null> {
  const pausedUntil = read<number>(PAUSE_KEY)
  if (pausedUntil && Date.now() < pausedUntil) return null
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), TIMEOUT_MS)
  try {
    const r = await fetch(q.url, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain' },
      body: JSON.stringify(q.upit),
      signal: ctrl.signal,
    })
    if (r.status === 429) write(PAUSE_KEY, Date.now() + PAUSE_AFTER_429_MS)
    if (!r.ok) return null
    const values = parseSeries((await r.json()) as JsonStat, q)
    if (!values) return null
    const series = { values, fetched: new Date().toISOString() }
    write(key(q), series)
    return series
  } catch {
    return null // timeout, network, CORS or a malformed answer: the static copy stays
  } finally {
    clearTimeout(timer)
  }
}

/** The unit's series straight from DZS, from this tab's cache when it was asked for already; null on any failure. */
export function liveSeries(q: LiveQuery): Promise<LiveSeries | null> {
  const k = key(q)
  const cached = read<LiveSeries>(k)
  if (cached?.values) return Promise.resolve(cached)
  let p = inFlight.get(k)
  if (!p) {
    p = call(q).finally(() => inFlight.delete(k))
    inFlight.set(k, p)
  }
  return p
}

export interface MergedSeries {
  /** [year, value] in year order, from the first year on */
  points: [string, number][]
  /** years whose value came from the live answer */
  live: string[]
  /** years whose value came from the profile JSON */
  stored: string[]
}

/** The population series shown on the card: per year the live value where the live answer has a number
 * for that year, else the stored one (pipeline build: PxWeb, or the DZS publication for the years PxWeb
 * does not have yet). Years before `first` are dropped. Pure, so it can be tested without a browser. */
export function mergeSeries(
  stored: Record<string, number | null>,
  live: Record<string, number | null> | null,
  first: number,
): MergedSeries {
  const years = new Set([...Object.keys(stored), ...Object.keys(live ?? {})].filter((y) => /^\d{4}$/.test(y) && Number(y) >= first))
  const out: MergedSeries = { points: [], live: [], stored: [] }
  for (const y of [...years].sort((a, b) => Number(a) - Number(b))) {
    const l = live?.[y]
    const s = stored[y]
    if (typeof l === 'number') {
      out.points.push([y, l])
      out.live.push(y)
    } else if (typeof s === 'number') {
      out.points.push([y, s])
      out.stored.push(y)
    }
  }
  return out
}

/** "2021.–2024." for consecutive years, "2025." for one, "2021., 2023." otherwise. */
export function yearSpan(years: (string | number)[]): string {
  const ys = [...new Set(years.map(Number))].sort((a, b) => a - b)
  if (!ys.length) return ''
  if (ys.length > 1 && ys[ys.length - 1] - ys[0] === ys.length - 1) return `${ys[0]}.–${ys[ys.length - 1]}.`
  return ys.map((y) => `${y}.`).join(', ')
}

/** Years by source from izvor_po_godini, e.g. {pxweb: ["2021", …, "2024"], xlsx: ["2025"]}. */
export function yearsBySource(bySource: Record<string, DzsSource> | null | undefined) {
  const out: Record<DzsSource, string[]> = { pxweb: [], xlsx: [] }
  for (const [y, s] of Object.entries(bySource ?? {})) (out[s] ?? out.pxweb).push(y)
  return out
}

/** Source line for the demography of the simulator and Karta reforme. */
export function demographySource(bySource: Record<string, DzsSource> | null | undefined): string {
  const { pxweb, xlsx } = yearsBySource(bySource)
  const what = 'stanovništvo 31. prosinca, rođeni, umrli i migracije po općinama i gradovima'
  if (!xlsx.length) return `Izvor: Državni zavod za statistiku, PxWeb API: ${what}.`
  return `Izvor: Državni zavod za statistiku, ${what}: ${pxweb.length ? `PxWeb API (${yearSpan(pxweb)}) i ` : ''}publikacija „${PUBLICATION}” (${yearSpan(xlsx)}).`
}
