// Live call to the DZS PxWeb API for a unit's population series (SP31_2, json-stat2).
//
// The profile JSON carries the exact request (pipeline/kontekst.py live_query): POST the query to the
// table URL. DZS sends Access-Control-Allow-Origin: *, and Content-Type text/plain keeps it a simple
// request without a preflight. DZS answers HTTP 429 after about ten quick calls, so every answer is
// kept in sessionStorage, a 429 pauses live calls for a while, and a call that takes longer than
// TIMEOUT_MS is dropped. In every failing case the caller keeps the static copy from the profile JSON.
import type { LiveQuery } from './data'

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

const key = (q: LiveQuery) => `dzs:${q.tablica}:${q.kod}`
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

/** Values by year from a json-stat2 answer for one unit; null when the answer is not that series. */
export function parseSeries(js: JsonStat, q: LiveQuery): Record<string, number | null> | null {
  if (!js || !Array.isArray(js.id) || !Array.isArray(js.size) || !js.dimension) return null
  const yearAt = js.id.indexOf(YEAR)
  if (yearAt < 0) return null
  // every dimension except the year must hold a single value, and the area must be the unit asked for
  if (js.size.some((n, i) => i !== yearAt && n !== 1)) return null
  const area = js.dimension[js.id.find((d) => d !== YEAR && positions(js.dimension[d].category).some(([c]) => c === q.kod)) ?? '']
  if (!area) return null
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
